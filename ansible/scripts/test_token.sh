#!/bin/bash
# Test VCF Installer token endpoint
SECRETS="$(cd "$(dirname "$0")/.." && pwd)/inventory/group_vars/all/secrets.yml"
PASS=$(grep sddc_admin_password "$SECRETS" | awk '{print $2}')

# Write JSON body to temp file to avoid shell escaping issues with ! in password
TMPFILE=$(mktemp)
VCF_PASS="$PASS" python3 -c "import json,os; print(json.dumps({'username': 'admin', 'password': os.environ['VCF_PASS']}))" > "$TMPFILE"

echo "Testing token endpoint..."
curl -sk -x socks5h://localhost:1080 \
  https://vcf-installer.lab.dreamfold.dev/v1/tokens \
  -X POST \
  -H 'Content-Type: application/json' \
  -d @"$TMPFILE" 2>&1

rm -f "$TMPFILE"
