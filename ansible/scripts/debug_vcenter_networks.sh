#!/bin/bash
# Debug: list portgroups/networks on management vCenter
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

VCENTER="vcenter-mgmt.lab.dreamfold.dev"
PROXY="socks5h://localhost:1080"
USERNAME="administrator@vsphere.local"
PASSWORD="VMware1!VMware1!"

echo "=== Getting vCenter session ==="
SESSION=$(curl -sk -X POST "https://${VCENTER}/api/session" \
  --proxy "${PROXY}" \
  -u "${USERNAME}:${PASSWORD}" \
  | tr -d '"')

echo "Session: ${SESSION:0:20}..."

echo ""
echo "=== Networks / Portgroups ==="
curl -sk --proxy "${PROXY}" \
  -H "vmware-api-session-id: ${SESSION}" \
  "https://${VCENTER}/api/vcenter/network" \
  | python3 -c "
import sys, json
networks = json.load(sys.stdin)
for n in networks:
    print(f\"{n.get('name', '?'):50s} type={n.get('type', '?'):20s} network={n.get('network', '?')}\")
"
