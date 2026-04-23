#!/bin/bash
# Debug: check certificate authority and CSR state in SDDC Manager
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Certificate Authorities ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/certificate-authorities" \
  | python3 -m json.tool

echo ""
echo "=== Domains ==="
DOMAINS=$(curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/domains" \
  | python3 -c "import sys,json; [print(d['id'], d['name'], d['status']) for d in json.load(sys.stdin).get('elements',[])]")
echo "$DOMAINS"

echo ""
echo "=== Domain Certificates ==="
while read -r ID NAME STATUS; do
  echo "--- ${NAME} (${STATUS}) ---"
  curl -sk --proxy "${PROXY}" \
    -H "Authorization: Bearer ${TOKEN}" \
    "https://${SDDC_HOST}/v1/domains/${ID}/certificates" \
    | python3 -c "
import sys,json
data = json.load(sys.stdin)
for elem in data.get('elements', []):
  for cert in elem.get('certificates', []):
    print(f\"  {cert.get('issuedBy','?')} -> {cert.get('issuedTo','?')} expires {cert.get('expirationDate','?')}\")
" 2>/dev/null || echo "  (no certificates)"
done <<< "$DOMAINS"
