#!/bin/bash
# List all VCF Installer validations and their status
SECRETS="$(cd "$(dirname "$0")/.." && pwd)/inventory/group_vars/all/secrets.yml"
PASS=$(grep sddc_admin_password "$SECRETS" | awk '{print $2}')
PROXY="socks5h://localhost:1080"
INSTALLER="vcf-installer.lab.dreamfold.dev"

TMPFILE=$(mktemp)
VCF_PASS="$PASS" python3 -c "import json,os; print(json.dumps({'username': 'admin@local', 'password': os.environ['VCF_PASS']}))" > "$TMPFILE"

TOKEN=$(curl -sk -x "$PROXY" -X POST \
  -H 'Content-Type: application/json' \
  -d @"$TMPFILE" \
  "https://$INSTALLER/v1/tokens" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])" 2>/dev/null)
rm -f "$TMPFILE"

if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get token"
    exit 1
fi

echo "=== Validations ==="
curl -sk -x "$PROXY" -H "Authorization: Bearer $TOKEN" \
  "https://$INSTALLER/v1/sddcs/validations" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('elements', data) if isinstance(data, dict) else data
if isinstance(items, list):
    for v in items:
        vid = v.get('id', 'unknown')
        status = v.get('executionStatus', 'unknown')
        result = v.get('resultStatus', '')
        print(f'  {vid[:8]}  {status}  {result}')
    print(f'\nTotal: {len(items)}')
else:
    print(json.dumps(data, indent=2))
"

echo ""
echo "=== Bringups ==="
curl -sk -x "$PROXY" -H "Authorization: Bearer $TOKEN" \
  "https://$INSTALLER/v1/sddcs" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('elements', data) if isinstance(data, dict) else data
if isinstance(items, list):
    for s in items:
        sid = s.get('id', 'unknown')
        status = s.get('status', 'unknown')
        print(f'  {sid[:8]}  {status}')
    print(f'\nTotal: {len(items)}')
else:
    print(json.dumps(data, indent=2))
"
