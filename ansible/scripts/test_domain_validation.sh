#!/bin/bash
# Test domain validation directly via curl + SOCKS proxy
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>
# No set -e — we want to see all output even on failure

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
echo "=== POST /v1/domains/validations ==="
curl -sk -X POST "https://${SDDC_HOST}/v1/domains/validations" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -d '{
  "domainName": "workload-domain",
  "deployWithoutLicenseKeys": true,
  "ssoDomainSpec": {
    "ssoDomainName": "workload",
    "ssoDomainPassword": "VMware1!VMware1!"
  },
  "vcenterSpec": {
    "name": "vcenter-wld",
    "networkDetailsSpec": {
      "dnsName": "vcenter-wld.lab.dreamfold.dev",
      "ipAddress": "10.0.10.9",
      "gateway": "10.0.10.1",
      "subnetMask": "255.255.255.0"
    },
    "rootPassword": "VMware1!VMware1!",
    "datacenterName": "workload-dc",
    "vmSize": "MEDIUM",
    "storageSize": "lstorage"
  },
  "computeSpec": {
    "clusterSpecs": [{
      "name": "workload-cluster",
      "clusterImageId": "877a4083-cc40-4313-8bb7-fc6673cbf106",
      "hostSpecs": [
        {"id": "1f02375b-8f98-4feb-910a-6cdedad0e8c2", "hostNetworkSpec": {"vmNics": [{"id": "vmnic0", "vdsName": "workload-cluster-vds01", "uplink": "uplink1"}]}},
        {"id": "ad9c3f19-4664-4f4a-99a0-3806b7c231cc", "hostNetworkSpec": {"vmNics": [{"id": "vmnic0", "vdsName": "workload-cluster-vds01", "uplink": "uplink1"}]}},
        {"id": "abad8d54-27a7-4f5c-88fe-29105ecaf3a8", "hostNetworkSpec": {"vmNics": [{"id": "vmnic0", "vdsName": "workload-cluster-vds01", "uplink": "uplink1"}]}}
      ],
      "datastoreSpec": {
        "vsanDatastoreSpec": {
          "datastoreName": "workload-vsan-ds",
          "esaConfig": {"enabled": true}
        }
      },
      "networkSpec": {
        "vdsSpecs": [{
          "name": "workload-cluster-vds01",
          "isUsedByNsxt": true,
          "portGroupSpecs": [
            {"name": "workload-cluster-vds01-pg-mgmt", "transportType": "MANAGEMENT", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standByUplinks": []},
            {"name": "workload-cluster-vds01-pg-vmotion", "transportType": "VMOTION", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standByUplinks": []},
            {"name": "workload-cluster-vds01-pg-vsan", "transportType": "VSAN", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standByUplinks": []}
          ]
        }],
        "nsxClusterSpec": {
          "nsxTClusterSpec": {
            "geneveVlanId": 40,
            "ipAddressPoolSpec": {
              "name": "workload-tep-pool",
              "subnets": [{
                "cidr": "10.0.40.0/24",
                "gateway": "10.0.40.1",
                "ipAddressPoolRanges": [{"start": "10.0.40.15", "end": "10.0.40.17"}]
              }]
            }
          }
        }
      }
    }]
  },
  "nsxTSpec": {
    "vipFqdn": "nsx-vip-wld.lab.dreamfold.dev",
    "nsxManagerSpecs": [{
      "name": "nsx-mgr-wld",
      "networkDetailsSpec": {
        "dnsName": "nsx-mgr-wld.lab.dreamfold.dev",
        "ipAddress": "10.0.10.10",
        "gateway": "10.0.10.1",
        "subnetMask": "255.255.255.0"
      }
    }],
    "nsxManagerAdminPassword": "VMware1!VMware1!",
    "formFactor": "medium"
  }
}' -o /tmp/domain_validation_response.json

echo ""
echo "=== Response ==="
cat /tmp/domain_validation_response.json
echo ""
echo ""
python3 -m json.tool /tmp/domain_validation_response.json 2>/dev/null || true
