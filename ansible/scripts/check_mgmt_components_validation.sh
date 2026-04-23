#!/bin/bash
# Submit and poll VCF Management Components validation until complete
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "=== Submitting validation ==="
RESPONSE=$(curl -sk -X POST "https://${SDDC_HOST}/v1/vcf-management-components/validations?redo=true" \
  --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
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
}')

VALIDATION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
echo "Validation ID: ${VALIDATION_ID}"
echo "Initial response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null

if [ -z "$VALIDATION_ID" ]; then
  echo "ERROR: No validation ID returned"
  exit 1
fi

echo ""
echo "=== Polling for completion ==="
for i in $(seq 1 60); do
  sleep 5

  # Try to get validation status - the API might use the location header
  RESULT=$(curl -sk -X POST "https://${SDDC_HOST}/v1/vcf-management-components/validations?redo=false" \
    --proxy "${PROXY}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
    "vcfOperationsSpec": {
      "nodes": [{"hostname": "vcf-ops.lab.dreamfold.dev", "type": "master", "rootUserPassword": "VMware1!VMware1!"}],
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
  }')

  STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('executionStatus','UNKNOWN'))" 2>/dev/null)
  echo "  Poll ${i}: ${STATUS}"

  if [ "$STATUS" != "IN_PROGRESS" ] && [ "$STATUS" != "UNKNOWN" ]; then
    echo ""
    echo "=== Final Result ==="
    echo "$RESULT" | python3 -m json.tool 2>/dev/null
    exit 0
  fi
done

echo "Timed out waiting for validation to complete"
