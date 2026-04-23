#!/usr/bin/env python3
"""
Validate a VCF API spec against the SDDC Manager or VCF Installer OpenAPI schema.

Usage:
    # Validate a domain creation spec
    python validate_spec.py --schema sddc-manager --type DomainCreationSpec spec.json

    # Validate from stdin (e.g., pipe from ansible)
    cat spec.json | python validate_spec.py --schema sddc-manager --type DomainCreationSpec

    # Download OpenAPI specs first (one-time setup)
    python validate_spec.py --download

Common spec types:
    DomainCreationSpec      POST /v1/domains
    ClusterSpec             POST /v1/clusters
    HostCommissionSpec      POST /v1/hosts (array of these)
    EdgeClusterSpec         POST /v1/edge-clusters
    SddcSpec                POST /v1/sddc (VCF Installer bringup)

Requires: pip install jsonschema
"""

import argparse
import json
import sys
import os
from pathlib import Path
from urllib.request import urlopen

SPEC_DIR = Path(__file__).parent / "openapi"

SPEC_URLS = {
    "sddc-manager": "https://raw.githubusercontent.com/vmware/vcf-api-specs/main/specifications/sddc-manager/sddc-manager-openapi.json",
    "vcf-installer": "https://raw.githubusercontent.com/vmware/vcf-api-specs/main/specifications/vcf-installer/vcf-installer-openapi.json",
}


def download_specs():
    """Download OpenAPI specs from GitHub."""
    SPEC_DIR.mkdir(exist_ok=True)
    for name, url in SPEC_URLS.items():
        dest = SPEC_DIR / f"{name}-openapi.json"
        print(f"Downloading {name} -> {dest}")
        with urlopen(url) as resp:
            dest.write_bytes(resp.read())
        print(f"  OK ({dest.stat().st_size:,} bytes)")


def load_openapi(schema_name: str) -> dict:
    """Load an OpenAPI spec file."""
    path = SPEC_DIR / f"{schema_name}-openapi.json"
    if not path.exists():
        print(f"OpenAPI spec not found at {path}")
        print(f"Run: python {sys.argv[0]} --download")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def resolve_ref(openapi: dict, ref: str) -> dict:
    """Resolve a $ref pointer in the OpenAPI spec."""
    parts = ref.lstrip("#/").split("/")
    node = openapi
    for part in parts:
        node = node[part]
    return node


def resolve_schema(openapi: dict, schema: dict) -> dict:
    """Recursively resolve $ref in a schema."""
    if "$ref" in schema:
        return resolve_schema(openapi, resolve_ref(openapi, schema["$ref"]))
    return schema


def validate_value(openapi: dict, schema: dict, value, path: str, errors: list):
    """Validate a value against an OpenAPI schema, collecting all errors."""
    schema = resolve_schema(openapi, schema)
    schema_type = schema.get("type")

    # Type check
    if schema_type == "string" and not isinstance(value, str):
        errors.append(f"{path}: expected string, got {type(value).__name__}")
        return
    elif schema_type == "integer" and not isinstance(value, int):
        errors.append(f"{path}: expected integer, got {type(value).__name__}")
        return
    elif schema_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{path}: expected boolean, got {type(value).__name__}")
        return
    elif schema_type == "array" and not isinstance(value, list):
        errors.append(f"{path}: expected array, got {type(value).__name__}")
        return
    elif schema_type == "object" and not isinstance(value, dict):
        errors.append(f"{path}: expected object, got {type(value).__name__}")
        return

    # String pattern check
    if schema_type == "string" and "pattern" in schema:
        import re
        pattern = schema["pattern"]
        if not re.match(pattern, value):
            errors.append(f"{path}: value '{value}' does not match pattern {pattern}")

    # String length checks
    if schema_type == "string":
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string too short ({len(value)} < {schema['minLength']})")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string too long ({len(value)} > {schema['maxLength']})")

    # Integer range checks
    if schema_type == "integer":
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value {value} above maximum {schema['maximum']}")

    # Array item validation
    if schema_type == "array" and "items" in schema:
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array too short ({len(value)} < {schema['minItems']})")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: array too long ({len(value)} > {schema['maxItems']})")
        item_schema = schema["items"]
        for i, item in enumerate(value):
            validate_value(openapi, item_schema, item, f"{path}[{i}]", errors)

    # Object property validation
    if schema_type == "object" and isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for req_field in required:
            if req_field not in value:
                errors.append(f"{path}.{req_field}: MISSING (required)")

        # Check for unknown fields
        for field in value:
            if field not in properties:
                errors.append(f"{path}.{field}: UNKNOWN field (not in schema)")

        # Validate each provided field
        for field, field_value in value.items():
            if field in properties:
                validate_value(openapi, properties[field], field_value, f"{path}.{field}", errors)

        # Flag deprecated fields
        for field in value:
            if field in properties:
                field_schema = resolve_schema(openapi, properties[field])
                if field_schema.get("deprecated"):
                    desc = field_schema.get("description", "")
                    errors.append(f"{path}.{field}: DEPRECATED — {desc}")


def validate_spec(openapi: dict, spec_type: str, spec: dict) -> list:
    """Validate a spec dict against an OpenAPI schema type."""
    schemas = openapi.get("components", {}).get("schemas", {})
    if spec_type not in schemas:
        available = [k for k in schemas if "Spec" in k or "spec" in k]
        return [f"Schema '{spec_type}' not found. Available spec schemas: {', '.join(sorted(available)[:20])}..."]

    schema = schemas[spec_type]
    errors = []
    validate_value(openapi, schema, spec, spec_type, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate VCF API specs against OpenAPI schema")
    parser.add_argument("spec_file", nargs="?", help="JSON spec file (or - for stdin)")
    parser.add_argument("--schema", choices=["sddc-manager", "vcf-installer"], default="sddc-manager",
                        help="Which OpenAPI schema to validate against")
    parser.add_argument("--type", dest="spec_type", help="Schema type name (e.g., DomainCreationSpec)")
    parser.add_argument("--download", action="store_true", help="Download OpenAPI specs from GitHub")
    parser.add_argument("--list-types", action="store_true", help="List available spec types")
    args = parser.parse_args()

    if args.download:
        download_specs()
        return

    openapi = load_openapi(args.schema)

    if args.list_types:
        schemas = openapi.get("components", {}).get("schemas", {})
        spec_schemas = sorted(k for k in schemas if "Spec" in k or "spec" in k)
        print(f"Available spec types in {args.schema}:")
        for s in spec_schemas:
            desc = schemas[s].get("description", "")
            required = schemas[s].get("required", [])
            print(f"  {s}")
            if required:
                print(f"    Required: {', '.join(required)}")
        return

    if not args.spec_type:
        parser.error("--type is required (e.g., --type DomainCreationSpec)")

    # Load spec
    if args.spec_file and args.spec_file != "-":
        with open(args.spec_file) as f:
            spec = json.load(f)
    else:
        spec = json.load(sys.stdin)

    # Validate
    errors = validate_spec(openapi, args.spec_type, spec)

    # Report
    warnings = [e for e in errors if "DEPRECATED" in e]
    failures = [e for e in errors if "DEPRECATED" not in e]

    if failures:
        print(f"\n VALIDATION FAILED — {len(failures)} error(s):\n")
        for err in failures:
            print(f"  - {err}")
    else:
        print(f"\n VALIDATION PASSED")

    if warnings:
        print(f"\n  {len(warnings)} deprecation warning(s):\n")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
