#!/bin/bash
# Submit VCF Management Components validation and poll via location header
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Submitting validation ==="
# Capture both headers and body
curl -sk -X POST "https://${SDDC_HOST}/v1/vcf-management-components/validations?redo=true" \
  --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -D /tmp/mgmt_val_headers.txt \
  -o /tmp/mgmt_val_body.json \
  -d '{
  "vcfOperationsSpec": {
    "nodes": [
      {
        "hostname": "vcf-ops.lab.dreamfold.dev",
        "type": "master",
        "rootUserPassword": "VMware1!VMware1!"
      }
    ],
    "adminUserPassword": "VMware1!VMware1!",
    "applianceSize": "xsmall"
  },
  "vcfOperationsCollectorSpec": {
    "hostname": "vcf-ops-collector.lab.dreamfold.dev",
    "rootUserPassword": "VMware1!VMware1!",
    "applianceSize": "small"
  },
  "vcfOperationsFleetManagementSpec": {
    "hostname": "vcf-ops-fleet.lab.dreamfold.dev",
    "rootUserPassword": "VMware1!VMware1!",
    "adminUserPassword": "VMware1!VMware1!"
  },
  "vcfMangementComponentsInfrastructureSpec": {
    "localRegionNetwork": {
      "networkName": "vcf-m01-cl01-vds01-pg-vm-mgmt",
      "subnetMask": "255.255.255.0",
      "gateway": "10.0.10.1"
    },
    "xRegionNetwork": {
      "networkName": "vcf-m01-cl01-vds01-pg-vm-mgmt",
      "subnetMask": "255.255.255.0",
      "gateway": "10.0.10.1"
    }
  }
}'

echo "Response body:"
python3 -m json.tool /tmp/mgmt_val_body.json 2>/dev/null || cat /tmp/mgmt_val_body.json

echo ""
echo "Response headers:"
cat /tmp/mgmt_val_headers.txt

# Extract location header for polling
LOCATION=$(grep -i "^location:" /tmp/mgmt_val_headers.txt | tr -d '\r' | awk '{print $2}')

if [ -z "$LOCATION" ]; then
  echo ""
  echo "No location header found — validation may have completed immediately"
  exit 0
fi

echo ""
echo "=== Polling: ${LOCATION} ==="
for i in $(seq 1 60); do
  sleep 5

  RESULT=$(curl -sk --proxy "${PROXY}" \
    -H "Authorization: Bearer ${TOKEN}" \
    "https://${SDDC_HOST}${LOCATION}")

  STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('executionStatus','UNKNOWN'))" 2>/dev/null)
  echo "  Poll ${i}: ${STATUS}"

  if [ "$STATUS" != "IN_PROGRESS" ] && [ "$STATUS" != "UNKNOWN" ]; then
    echo ""
    echo "=== Final Result ==="
    echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
    exit 0
  fi
done

echo "Timed out after 5 minutes"
