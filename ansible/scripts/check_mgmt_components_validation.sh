#!/bin/bash
# Check VCF Management Components validation result via task ID
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"
VALIDATION_ID="bb013603-ad7a-4ac5-bc15-4bf9e4f34c06"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Check as Task ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/tasks/${VALIDATION_ID}" \
  | python3 -m json.tool 2>/dev/null || echo "(not a task)"

echo ""
echo "=== Recent Tasks (last 5) ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/tasks" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data.get('elements', [])[:5]:
    print(f\"{t.get('id','?')[:20]}  {t.get('status','?'):12s}  {t.get('name', t.get('description','?'))[:60]}\")
"
