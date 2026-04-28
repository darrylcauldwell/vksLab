#!/bin/bash
# Check VCF Installer validation or bringup status by ID.
# Usage: ./scripts/check_vcf_status.sh
set -e

INSTALLER="vcf-installer.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

read -p "Task ID: " TASK_ID
read -p "Type (validation/bringup) [validation]: " TASK_TYPE
TASK_TYPE=${TASK_TYPE:-validation}

echo ""
echo "Getting token..."
SECRETS="$(cd "$(dirname "$0")/.." && pwd)/inventory/group_vars/all/secrets.yml"
if [ -f "$SECRETS" ]; then
    PASS=$(grep sddc_admin_password "$SECRETS" | awk '{print $2}')
else
    read -sp "VCF Installer password: " PASS
    echo ""
fi

# Use python to build JSON body — avoids shell escaping issues with ! in password
TMPFILE=$(mktemp)
python3 -c "import json; print(json.dumps({'username': 'admin@local', 'password': '$PASS'}))" > "$TMPFILE"

TOKEN=$(curl -sk -x "$PROXY" -X POST \
  -H 'Content-Type: application/json' \
  -d @"$TMPFILE" \
  "https://$INSTALLER/v1/tokens" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])" 2>/dev/null)

rm -f "$TMPFILE"

if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get token. Check SOCKS tunnel and credentials."
    exit 1
fi

if [ "$TASK_TYPE" = "validation" ]; then
    URL="https://$INSTALLER/v1/sddcs/validations/$TASK_ID"
elif [ "$TASK_TYPE" = "bringup" ]; then
    URL="https://$INSTALLER/v1/sddcs/$TASK_ID"
else
    echo "Unknown type: $TASK_TYPE"
    exit 1
fi

echo "Fetching status..."
echo ""

RESPONSE=$(curl -sk -x "$PROXY" -H "Authorization: Bearer $TOKEN" "$URL")

if [ "$TASK_TYPE" = "validation" ]; then
    echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Execution Status: {data.get('executionStatus', 'UNKNOWN')}\")
print(f\"Result Status:    {data.get('resultStatus', 'N/A')}\")
print()
checks = data.get('validationChecks', [])
if checks:
    print(f'Validation Checks ({len(checks)}):')
    for c in checks:
        status = c.get('resultStatus', 'UNKNOWN')
        desc = c.get('description', 'No description')
        icon = '✓' if status == 'SUCCEEDED' else '✗' if status == 'FAILED' else '…'
        print(f'  {icon} [{status}] {desc}')
        if status == 'FAILED':
            err = c.get('errorResponse', {})
            if err.get('message'):
                print(f'    Error: {err[\"message\"]}')
"
else
    echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Status: {data.get('status', 'UNKNOWN')}\")
print(f\"Type:   {data.get('type', 'N/A')}\")
print()
subtasks = data.get('subTasks', [])
if subtasks:
    print(f'Sub-tasks ({len(subtasks)}):')
    for t in subtasks:
        status = t.get('status', 'UNKNOWN')
        name = t.get('name', 'Unknown')
        icon = '✓' if status == 'SUCCESSFUL' else '✗' if status == 'FAILED' else '…'
        print(f'  {icon} [{status}] {name}')
"
fi
