#!/bin/bash
# Test VCF bringup validation directly via curl + SOCKS proxy
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>
# Note: VCF Installer must be deployed and API accessible
# No set -e — we want to see all output even on failure

INSTALLER_HOST="vcf-installer.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"

echo "=== Getting bearer token ==="
TOKEN=$(curl -sk -X POST "https://${INSTALLER_HOST}/v1/tokens" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@local","password":"VMware1!VMware1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

echo "Token acquired (${#TOKEN} chars)"

echo ""
echo "=== POST /v1/sddcs/validations ==="
curl -sk -X POST "https://${INSTALLER_HOST}/v1/sddcs/validations" \
  --proxy "${PROXY}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -d '{
  "sddcId": "vcf-m01",
  "workflowType": "VCF",
  "ceipEnabled": false,
  "skipEsxThumbprintValidation": true,
  "managementPoolName": "mgmt-network-pool",
  "dnsSpec": {
    "nameservers": ["10.0.10.1"],
    "subdomain": "lab.dreamfold.dev"
  },
  "ntpServers": ["10.0.10.1"],
  "vcenterSpec": {
    "vcenterHostname": "vcenter-mgmt.lab.dreamfold.dev",
    "rootVcenterPassword": "VMware1!VMware1!",
    "adminUserSsoPassword": "VMware1!VMware1!",
    "vmSize": "small",
    "storageSize": "lstorage",
    "ssoDomain": "vsphere.local"
  },
  "clusterSpec": {
    "clusterName": "vcf-m01-cl01",
    "datacenterName": "vcf-m01-dc01"
  },
  "datastoreSpec": {
    "vsanSpec": {
      "datastoreName": "vcf-m01-cl01-ds-vsan01",
      "esaConfig": {"enabled": true}
    }
  },
  "sddcManagerSpec": {
    "hostname": "sddc-manager.lab.dreamfold.dev",
    "rootPassword": "VMware1!VMware1!",
    "sshPassword": "VMware1!VMware1!",
    "localUserPassword": "VMware1!VMware1!"
  },
  "nsxtSpec": {
    "nsxtManagerSize": "medium",
    "rootNsxtManagerPassword": "VMware1!VMware1!",
    "nsxtAdminPassword": "VMware1!VMware1!",
    "nsxtAuditPassword": "VMware1!VMware1!",
    "skipNsxOverlayOverManagementNetwork": true,
    "nsxtManagers": [
      {"hostname": "nsx-mgr-mgmt-01.lab.dreamfold.dev"}
    ],
    "vipFqdn": "nsx-mgr-mgmt.lab.dreamfold.dev",
    "transportVlanId": 40,
    "ipAddressPoolSpec": {
      "name": "tep-ip-pool",
      "description": "ESXi Host Overlay TEP IP Pool",
      "subnets": [{
        "cidr": "10.0.40.0/24",
        "gateway": "10.0.40.1",
        "ipAddressPoolRanges": [{"start": "10.0.40.11", "end": "10.0.40.20"}]
      }]
    }
  },
  "hostSpecs": [
    {"hostname": "esxi-01", "credentials": {"username": "root", "password": "VMware1!VMware1!"}},
    {"hostname": "esxi-02", "credentials": {"username": "root", "password": "VMware1!VMware1!"}},
    {"hostname": "esxi-03", "credentials": {"username": "root", "password": "VMware1!VMware1!"}},
    {"hostname": "esxi-04", "credentials": {"username": "root", "password": "VMware1!VMware1!"}}
  ],
  "networkSpecs": [
    {"networkType": "MANAGEMENT", "subnet": "10.0.10.0/24", "gateway": "10.0.10.1", "vlanId": 10, "mtu": 1500, "portGroupKey": "vcf-m01-cl01-vds01-pg-mgmt", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standbyUplinks": []},
    {"networkType": "VM_MANAGEMENT", "subnet": "10.0.10.0/24", "gateway": "10.0.10.1", "vlanId": 10, "mtu": 1500, "portGroupKey": "vcf-m01-cl01-vds01-pg-vm-mgmt", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standbyUplinks": []},
    {"networkType": "VMOTION", "subnet": "10.0.20.0/24", "gateway": "10.0.20.1", "vlanId": 20, "mtu": 8900, "portGroupKey": "vcf-m01-cl01-vds01-pg-vmotion", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standbyUplinks": [], "includeIpAddressRanges": [{"startIpAddress": "10.0.20.11", "endIpAddress": "10.0.20.20"}]},
    {"networkType": "VSAN", "subnet": "10.0.30.0/24", "gateway": "10.0.30.1", "vlanId": 30, "mtu": 8900, "portGroupKey": "vcf-m01-cl01-vds01-pg-vsan", "teamingPolicy": "loadbalance_loadbased", "activeUplinks": ["uplink1"], "standbyUplinks": [], "includeIpAddressRanges": [{"startIpAddress": "10.0.30.11", "endIpAddress": "10.0.30.20"}]}
  ],
  "dvsSpecs": [{
    "dvsName": "vcf-m01-cl01-vds01",
    "networks": ["MANAGEMENT", "VM_MANAGEMENT", "VMOTION", "VSAN"],
    "mtu": 8900,
    "nsxtSwitchConfig": {
      "hostSwitchOperationalMode": "STANDARD",
      "transportZones": [
        {"name": "nsx-vlan-transportzone", "transportType": "VLAN"},
        {"name": "overlay-tz-vcf-m01", "transportType": "OVERLAY"}
      ]
    },
    "vmnicsToUplinks": [{"id": "vmnic0", "uplink": "uplink1"}],
    "nsxTeamings": [{"policy": "LOADBALANCE_SRCID", "standByUplinks": [], "activeUplinks": ["uplink1"]}]
  }]
}' -o /tmp/bringup_validation_response.json

echo ""
echo "=== Response ==="
cat /tmp/bringup_validation_response.json
echo ""
echo ""
python3 -m json.tool /tmp/bringup_validation_response.json 2>/dev/null || true
