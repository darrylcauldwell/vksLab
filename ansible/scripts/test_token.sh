#!/bin/bash
# Test VCF Installer token endpoint
SECRETS="$(cd "$(dirname "$0")/.." && pwd)/inventory/group_vars/all/secrets.yml"
PASS=$(grep sddc_admin_password "$SECRETS" | awk '{print $2}')

echo "Testing token endpoint..."
curl -vsk -x socks5h://localhost:1080 \
  https://vcf-installer.lab.dreamfold.dev/v1/tokens \
  -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin@local\",\"password\":\"$PASS\"}" \
  2>&1 | head -40
