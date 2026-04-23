#!/usr/bin/env python3
"""
Configure VCF Identity Broker with OIDC provider.

Translates William Lam's PowerShell script to Python.
Uses VCF Operations internal APIs (/suite-api/internal/vidb/).
Tested on VCF 9.0 — internal APIs may change between versions.

Reference: https://williamlam.com/2026/04/automating-vcf-9-0-single-sign-on-sso-with-oidc-based-identity-provider.html
"""

import json
import os
import sys

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    # Read config from environment (set by Ansible)
    ops_fqdn = os.environ["VCF_OPS_FQDN"]
    ops_username = os.environ["VCF_OPS_USERNAME"]
    ops_password = os.environ["VCF_OPS_PASSWORD"]
    sso_model = os.environ.get("VCF_SSO_MODEL", "EMBEDDED")
    vcf_auto_deployed = os.environ.get("VCF_AUTO_DEPLOYED", "false").lower() == "true"

    oidc_label = os.environ["OIDC_LABEL"]
    oidc_discovery_url = os.environ["OIDC_DISCOVERY_URL"]
    oidc_client_id = os.environ["OIDC_CLIENT_ID"]
    oidc_client_secret = os.environ["OIDC_CLIENT_SECRET"]
    oidc_domain = os.environ["OIDC_DOMAIN"]
    oidc_jit_group = os.environ.get("OIDC_JIT_GROUP", "vcf-admins")
    oidc_group_attr = os.environ.get("OIDC_GROUP_ATTR", "groups")
    oidc_cert_path = os.environ["OIDC_CERT_PATH"]

    base_url = f"https://{ops_fqdn}"

    # Load TLS cert chain
    with open(oidc_cert_path) as f:
        cert_pem = f.read()

    # Step 1: Authenticate to VCF Operations
    print("Acquiring VCF Operations token...", flush=True)
    resp = requests.post(
        f"{base_url}/suite-api/api/auth/token/acquire",
        json={"username": ops_username, "password": ops_password, "authSource": "local"},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        verify=False,
    )
    resp.raise_for_status()
    token = resp.json()["token"]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"OpsToken {token}",
        "X-Ops-API-use-unsupported": "true",
    }

    # Step 2: Accept terms
    print("Acknowledging SSO prerequisites...", flush=True)
    resp = requests.put(
        f"{base_url}/suite-api/internal/vidb/globalidpsettings",
        json={"key": "TERMS_AND_CONDITIONS", "value": "ACCEPTED"},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    # Step 3: Get VCF instance ID
    print("Retrieving VCF instance IDs...", flush=True)
    resp = requests.get(
        f"{base_url}/suite-api/api/resources",
        params={"adapterKindKey": "VMWARE_INFRA_MANAGEMENT", "resourceKind": "Vidb Monitoring"},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    filter_name = "Appliance" if sso_model == "EXTERNAL" else "Embedded"
    vcf_id = None
    for resource in resp.json().get("resourceList", []):
        if filter_name in resource.get("resourceKey", {}).get("name", ""):
            for ident in resource.get("resourceKey", {}).get("resourceIdentifiers", []):
                if ident.get("identifierType", {}).get("name") == "VIDB_MONITORING_VCF_IDENTIFIER":
                    vcf_id = ident["value"]
                    break

    if not vcf_id:
        print(f"ERROR: Could not find VCF instance ID (filter: {filter_name})", file=sys.stderr)
        sys.exit(1)

    print(f"VCF instance ID: {vcf_id}", flush=True)

    # Step 4: Get vIDB resource ID
    resp = requests.get(
        f"{base_url}/suite-api/internal/vidb/vidbs",
        params={"vcfId": vcf_id},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    vidb_resource_id = None
    for vidb in resp.json():
        if vidb.get("deploymentType") == sso_model and vidb.get("vidbStatus", {}).get("status") == "ELIGIBLE":
            vidb_resource_id = vidb["id"]
            break

    if not vidb_resource_id:
        print("ERROR: Could not find eligible vIDB resource", file=sys.stderr)
        sys.exit(1)

    print(f"vIDB resource ID: {vidb_resource_id}", flush=True)

    # Step 5: Set deployment model
    print(f"Setting SSO deployment model: {sso_model}...", flush=True)
    resp = requests.post(
        f"{base_url}/suite-api/internal/vidb/ssoconfigstatus",
        params={"vcfId": vcf_id},
        json={"status": "DEPLOYMENT_MODE_SELECTED", "deploymentType": sso_model},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    # Step 6: Create OIDC IdP
    print(f"Configuring OIDC identity provider: {oidc_label}...", flush=True)
    idp_body = {
        "name": oidc_label,
        "deploymentType": sso_model,
        "vidbResourceId": vidb_resource_id,
        "vcfInstanceId": vcf_id,
        "idpType": "PING",
        "idpConfigTag": "OIDC",
        "provisionType": "JIT",
        "idpConfig": {
            "oidcConfiguration": {
                "discoveryEndpoint": oidc_discovery_url,
                "clientId": oidc_client_id,
                "clientSecret": oidc_client_secret,
                "openIdUserIdentifierAttribute": "sub",
                "internalUserIdentifierAttribute": "ExternalID",
            }
        },
        "directories": [
            {
                "domains": [oidc_domain],
                "name": "Directory OIDC JIT",
            }
        ],
        "provisioningConfig": {
            "jitConfiguration": {
                "oidcJitConfiguration": {
                    "userAttributeMappings": [
                        {"directoryName": "firstName", "attrName": "given_name"},
                        {"directoryName": "lastName", "attrName": "family_name"},
                        {"directoryName": "email", "attrName": "email"},
                        {"directoryName": "userName", "attrName": "preferred_username"},
                        {"directoryName": "groups", "attrName": oidc_group_attr},
                    ]
                },
                "jitProvisioningGroups": [
                    {
                        "domain": oidc_domain,
                        "groupNames": [oidc_jit_group],
                    }
                ],
            }
        },
        "trustedCertChain": {
            "certChain": [cert_pem],
        },
    }

    resp = requests.post(
        f"{base_url}/suite-api/internal/vidb/identityproviders",
        json=idp_body,
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    # Step 7: Get vIDB hostname and configure auth sources (vCenter, NSX)
    print("Configuring SSO for vCenter & NSX...", flush=True)
    resp = requests.get(
        f"{base_url}/suite-api/internal/vidb/identityproviders",
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    vidb_hostname = None
    for idp in resp.json().get("identityProviderInfoList", []):
        if (idp.get("deploymentType") == sso_model
                and idp.get("vidbResourceId") == vidb_resource_id
                and idp.get("vcfInstanceId") == vcf_id):
            vidb_hostname = idp.get("vidbHostname")
            break

    if not vidb_hostname:
        print("ERROR: Could not find vIDB hostname", file=sys.stderr)
        sys.exit(1)

    # Get unconfigured components
    resp = requests.get(
        f"{base_url}/suite-api/internal/vidb/authsource",
        params={"vcfId": vcf_id},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    vcf_components = []
    for comp in resp.json().get("authSourceComponents", []):
        if comp.get("status") == "NOT_CONFIGURED":
            vcf_components.append({
                "componentType": comp["componentType"],
                "componentHostname": comp["componentHostname"],
                "vcfComponentId": comp["vcfComponentId"],
            })

    if vcf_components:
        resp = requests.post(
            f"{base_url}/suite-api/internal/vidb/authsource",
            json={
                "vcfInstanceId": vcf_id,
                "vidbResourceId": vidb_resource_id,
                "vidbHostname": vidb_hostname,
                "vcfComponents": vcf_components,
            },
            headers=headers,
            verify=False,
        )
        resp.raise_for_status()

    # Step 8: Configure VCF Operations
    print("Configuring SSO for VCF Operations...", flush=True)
    resp = requests.get(
        f"{base_url}/suite-api/internal/vidb/authsource/components",
        params={"componentType": "VCF_OPS"},
        headers=headers,
        verify=False,
    )
    if resp.status_code == 200:
        if len(resp.json().get("authSourceComponents", [])) == 0:
            requests.post(
                f"{base_url}/suite-api/internal/vidb/authsource",
                json={
                    "vcfInstanceId": vcf_id,
                    "vidbResourceId": vidb_resource_id,
                    "vidbHostname": vidb_hostname,
                    "vcfComponents": [{"componentType": "VCF_OPS"}],
                },
                headers=headers,
                verify=False,
            ).raise_for_status()

    # Step 9: Configure VCF Automation (if deployed)
    if vcf_auto_deployed:
        print("Configuring SSO for VCF Automation...", flush=True)
        resp = requests.get(
            f"{base_url}/suite-api/internal/vidb/authsource/components",
            params={"componentType": "VCF_AUTOMATION"},
            headers=headers,
            verify=False,
        )
        if resp.status_code == 200:
            if len(resp.json().get("authSourceComponents", [])) == 0:
                requests.post(
                    f"{base_url}/suite-api/internal/vidb/authsource",
                    json={
                        "vcfInstanceId": vcf_id,
                        "vidbResourceId": vidb_resource_id,
                        "vidbHostname": vidb_hostname,
                        "vcfComponents": [{"componentType": "VCF_AUTOMATION"}],
                    },
                    headers=headers,
                    verify=False,
                ).raise_for_status()

    # Step 10: Mark workflow complete
    print("Completing SSO workflow...", flush=True)
    resp = requests.put(
        f"{base_url}/suite-api/internal/vidb/ssoconfigstatus",
        params={"vcfId": vcf_id},
        json={"status": "FINISHED", "deploymentType": sso_model},
        headers=headers,
        verify=False,
    )
    resp.raise_for_status()

    print("VCF SSO OIDC configuration complete.", flush=True)
    print(json.dumps({"changed": True, "oidc_label": oidc_label, "domain": oidc_domain}))


if __name__ == "__main__":
    main()
