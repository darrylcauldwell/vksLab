#!/bin/bash
# Debug: try CSR generation for management domain only
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Generate CSR for management domain (vcf-m01) ==="
curl -sk -X PUT "https://${SDDC_HOST}/v1/domains/vcf-m01/csrs" \
  --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -d '{
  "csrGenerationSpec": {
    "country": "GB",
    "state": "England",
    "locality": "London",
    "organization": "Lab",
    "organizationUnit": "VCF",
    "keySize": "3072",
    "keyAlgorithm": "RSA"
  }
}' | python3 -m json.tool 2>/dev/null || true

echo ""
echo "=== Generate CSR for workload domain ==="
curl -sk -X PUT "https://${SDDC_HOST}/v1/domains/workload-domain/csrs" \
  --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -d '{
  "csrGenerationSpec": {
    "country": "GB",
    "state": "England",
    "locality": "London",
    "organization": "Lab",
    "organizationUnit": "VCF",
    "keySize": "3072",
    "keyAlgorithm": "RSA"
  }
}' | python3 -m json.tool 2>/dev/null || true
