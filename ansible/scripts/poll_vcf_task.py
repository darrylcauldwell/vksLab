#!/usr/bin/env python3
"""Poll a VCF Installer validation or bringup task with live status output.

Usage:
    poll_vcf_task.py <hostname> <username> <password> <type> <task_id> [delay] [timeout]

    type: validation | bringup
    delay: seconds between polls (default: 10 for validation, 60 for bringup)
    timeout: max seconds (default: 3600 for validation, 14400 for bringup)
"""

import json
import os
import sys
import time

import requests
import urllib3

urllib3.disable_warnings()

PROXY = os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", ""))


def get_token(hostname, username, password):
    url = f"https://{hostname}/v1/tokens"
    resp = requests.post(
        url,
        json={"username": username, "password": password},
        verify=False,
        proxies={"https": PROXY} if PROXY else None,
    )
    resp.raise_for_status()
    return resp.json()["accessToken"]


def poll_validation(hostname, token, task_id):
    url = f"https://{hostname}/v1/sddcs/validations/{task_id}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
        proxies={"https": PROXY} if PROXY else None,
    )
    resp.raise_for_status()
    return resp.json()


def poll_bringup(hostname, token, task_id):
    url = f"https://{hostname}/v1/sddcs/{task_id}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
        proxies={"https": PROXY} if PROXY else None,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 6:
        print(__doc__)
        sys.exit(1)

    hostname = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    task_type = sys.argv[4]
    task_id = sys.argv[5]
    delay = int(sys.argv[6]) if len(sys.argv) > 6 else (10 if task_type == "validation" else 60)
    timeout = int(sys.argv[7]) if len(sys.argv) > 7 else (3600 if task_type == "validation" else 14400)

    print(f"Polling {task_type} {task_id[:8]}... (delay={delay}s, timeout={timeout}s)")
    sys.stdout.flush()

    token = get_token(hostname, username, password)
    start = time.time()

    while True:
        elapsed = int(time.time() - start)

        try:
            if task_type == "validation":
                data = poll_validation(hostname, token, task_id)
                status = data.get("executionStatus", "UNKNOWN")
                result = data.get("resultStatus", "")
                checks = data.get("validationChecks", [])
                passed = len([c for c in checks if c.get("resultStatus") == "SUCCEEDED"])
                failed = len([c for c in checks if c.get("resultStatus") == "FAILED"])
                total = len(checks)
                print(f"  [{elapsed}s] {status} — {passed}/{total} passed, {failed} failed {f'({result})' if result else ''}")
                sys.stdout.flush()

                if status == "COMPLETED":
                    if failed > 0:
                        print("\nFailed checks:")
                        for c in checks:
                            if c.get("resultStatus") == "FAILED":
                                desc = c.get("description", "Unknown")
                                err = c.get("errorResponse", {}).get("message", "No message")
                                code = c.get("errorResponse", {}).get("errorCode", "")
                                print(f"  ✗ {desc}: {err} [{code}]")
                    print(f"\nValidation {result}")
                    # Output JSON for Ansible to parse
                    print(f"\nRESULT_JSON:{json.dumps({'execution_status': status, 'result_status': result, 'failed_checks': failed})}")
                    sys.exit(0 if result == "SUCCEEDED" or failed == 0 else 2)

            else:  # bringup
                data = poll_bringup(hostname, token, task_id)
                status = data.get("status", "UNKNOWN")
                print(f"  [{elapsed}s] {status}")
                sys.stdout.flush()

                if status in ("COMPLETED_WITH_SUCCESS", "COMPLETED_WITH_FAILURE"):
                    print(f"\nBringup {status}")
                    print(f"\nRESULT_JSON:{json.dumps({'status': status})}")
                    sys.exit(0 if "SUCCESS" in status else 2)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, refresh
                print(f"  [{elapsed}s] Token expired, refreshing...")
                token = get_token(hostname, username, password)
                continue
            raise

        if elapsed > timeout:
            print(f"\nTIMEOUT after {timeout}s")
            sys.exit(1)

        time.sleep(delay)


if __name__ == "__main__":
    main()
