#!/usr/bin/env python3
"""
Ensure required VCF Management Components bundles are downloaded.

Checks download status for VROPS, VRSLCM, and VCF_OPS_CLOUD_PROXY
matching the current VCF version. Downloads any that are PENDING.
Polls until all downloads complete.
"""

import json
import os
import sys
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REQUIRED_TYPES = {"VROPS", "VRSLCM", "VCF_OPS_CLOUD_PROXY"}
TERMINAL_STATUSES = {"SUCCESS", "AVAILABLE", "FAILED", "CANCELLED"}


def main():
    sddc_host = os.environ["SDDC_HOSTNAME"]
    username = os.environ["SDDC_USERNAME"]
    password = os.environ["SDDC_PASSWORD"]
    base_url = f"https://{sddc_host}"

    # Authenticate
    print("Authenticating to SDDC Manager...", flush=True)
    resp = requests.post(
        f"{base_url}/v1/tokens",
        json={"username": username, "password": password},
        verify=False,
    )
    resp.raise_for_status()
    token = resp.json()["accessToken"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Get VCF version
    resp = requests.get(f"{base_url}/v1/sddc-managers", headers=headers, verify=False)
    resp.raise_for_status()
    vcf_version = resp.json()["elements"][0]["version"]
    vcf_major_minor = ".".join(vcf_version.split(".")[:3])  # e.g., "9.0.2"
    print(f"VCF version: {vcf_version} (matching {vcf_major_minor}.*)", flush=True)

    # Get download status for all bundles
    resp = requests.get(f"{base_url}/v1/bundles/download-status", headers=headers, verify=False)
    resp.raise_for_status()
    all_bundles = resp.json().get("elements", [])

    # Find required bundles matching VCF version
    required = {}
    for bundle in all_bundles:
        comp_type = bundle.get("componentType", "")
        version = bundle.get("version", "")
        if comp_type in REQUIRED_TYPES and version.startswith(vcf_major_minor):
            # Prefer INSTALL over PATCH if multiple exist
            existing = required.get(comp_type)
            if not existing or bundle.get("imageType") == "INSTALL":
                required[comp_type] = bundle

    print(f"\nRequired bundles for {vcf_major_minor}:", flush=True)
    for comp_type in REQUIRED_TYPES:
        bundle = required.get(comp_type)
        if bundle:
            print(f"  {comp_type}: {bundle['version']} [{bundle['downloadStatus']}] (bundle: {bundle['bundleId'][:20]}...)", flush=True)
        else:
            print(f"  {comp_type}: NOT FOUND in depot", file=sys.stderr, flush=True)
            sys.exit(1)

    # Download any that need it
    to_download = []
    for comp_type, bundle in required.items():
        status = bundle["downloadStatus"]
        if status in ("SUCCESS", "AVAILABLE"):
            print(f"  {comp_type}: already downloaded", flush=True)
        elif status in ("SCHEDULED", "IN_PROGRESS", "VALIDATING"):
            print(f"  {comp_type}: download in progress ({status})", flush=True)
            to_download.append(bundle)
        elif status == "PENDING":
            print(f"  {comp_type}: triggering download...", flush=True)
            dl_resp = requests.patch(
                f"{base_url}/v1/bundles/{bundle['bundleId']}",
                json={"bundleDownloadSpec": {"downloadNow": True}},
                headers=headers,
                verify=False,
            )
            if dl_resp.ok:
                print(f"  {comp_type}: download started", flush=True)
                to_download.append(bundle)
            else:
                print(f"  {comp_type}: download trigger failed: {dl_resp.text}", file=sys.stderr, flush=True)
                sys.exit(1)
        else:
            print(f"  {comp_type}: unexpected status {status}", file=sys.stderr, flush=True)
            sys.exit(1)

    if not to_download:
        print("\nAll required bundles are available.", flush=True)
        print(json.dumps({"changed": False, "msg": "All bundles already downloaded"}))
        return

    # Poll until all downloads complete
    print(f"\nWaiting for {len(to_download)} download(s) to complete...", flush=True)
    timeout = 3600
    start = time.time()

    while True:
        # Refresh token if needed (long downloads)
        elapsed = time.time() - start
        if elapsed > timeout:
            print("ERROR: Bundle download timed out", file=sys.stderr, flush=True)
            sys.exit(1)

        if elapsed > 0 and int(elapsed) % 600 == 0:
            # Re-auth every 10 minutes
            resp = requests.post(
                f"{base_url}/v1/tokens",
                json={"username": username, "password": password},
                verify=False,
            )
            if resp.ok:
                token = resp.json()["accessToken"]
                headers["Authorization"] = f"Bearer {token}"

        time.sleep(30)

        resp = requests.get(f"{base_url}/v1/bundles/download-status", headers=headers, verify=False)
        if not resp.ok:
            print(f"  Warning: status check failed ({resp.status_code}), retrying...", flush=True)
            continue

        current = resp.json().get("elements", [])
        pending_ids = {b["bundleId"] for b in to_download}

        all_done = True
        for bundle in current:
            if bundle["bundleId"] in pending_ids:
                status = bundle["downloadStatus"]
                if status not in TERMINAL_STATUSES:
                    all_done = False
                elif status in ("FAILED", "CANCELLED"):
                    print(f"ERROR: {bundle['componentType']} download {status}", file=sys.stderr, flush=True)
                    sys.exit(1)

        mins = int(elapsed / 60)
        print(f"  {mins}m elapsed — {'complete' if all_done else 'still downloading'}...", flush=True)

        if all_done:
            break

    print("\nAll required bundles downloaded successfully.", flush=True)
    print(json.dumps({"changed": True, "msg": "Bundles downloaded"}))


if __name__ == "__main__":
    main()
