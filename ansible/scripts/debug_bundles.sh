#!/bin/bash
# Debug: list available bundles and their download status
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== VCF Version ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/sddc-managers" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('elements', []):
    print(f\"Version: {m.get('version', '?')}\")
"

echo ""
echo "=== Depot Configuration ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/system/settings/depot" \
  | python3 -m json.tool 2>/dev/null || echo "(not configured)"

echo ""
echo "=== Bundles (VROPS, VRSLCM, VCF_OPS_CLOUD_PROXY) ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/bundles" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
target_types = {'VROPS', 'VRSLCM', 'VCF_OPS_CLOUD_PROXY'}
for bundle in data.get('elements', []):
    components = bundle.get('components', [])
    for comp in (components or []):
        if comp.get('type') in target_types:
            print(f\"Bundle: {bundle.get('id', '?')[:30]}\")
            print(f\"  Type: {comp.get('type')}\")
            print(f\"  Version: {comp.get('version')}\")
            print(f\"  Download: {bundle.get('downloadStatus', '?')}\")
            print(f\"  Image: {comp.get('imageType', '?')}\")
            print()
            break
" 2>/dev/null || echo "(no bundles found)"

echo ""
echo "=== Download Status ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/bundles/download-status" \
  | python3 -m json.tool 2>/dev/null || echo "(no status)"
