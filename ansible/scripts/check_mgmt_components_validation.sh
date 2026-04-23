#!/bin/bash
# Check VCF Management Components validation result
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Management Components Validation Status ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/vcf-management-components/validations" \
  | python3 -m json.tool
