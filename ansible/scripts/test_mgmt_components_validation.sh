#!/bin/bash
# Test VCF Management Components deployment validation via curl + SOCKS proxy
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>
# Requires: DNS entries for vcf-ops-collector and vcf-ops-fleet

SDDC_HOST="sddc-manager.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

echo "=== Getting bearer token ==="
TOKEN=$(curl -sk -X POST "https://${SDDC_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "Token acquired (${#TOKEN} chars)"

echo ""
echo "=== GET current management components status ==="
curl -sk --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://${SDDC_HOST}/v1/vcf-management-components" \
  -o /tmp/mgmt_components_status.json \
  -w "HTTP Status: %{http_code}\n"

echo ""
cat /tmp/mgmt_components_status.json | python3 -m json.tool 2>/dev/null || cat /tmp/mgmt_components_status.json
echo ""

echo ""
echo "=== POST /v1/vcf-management-components/validations ==="
curl -sk -X POST "https://${SDDC_HOST}/v1/vcf-management-components/validations" \
  --proxy "${PROXY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\n\nHTTP Status: %{http_code}\n" \
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
}' -o /tmp/mgmt_components_validation.json

echo ""
echo "=== Validation Response ==="
cat /tmp/mgmt_components_validation.json
echo ""
echo ""
python3 -m json.tool /tmp/mgmt_components_validation.json 2>/dev/null || true
