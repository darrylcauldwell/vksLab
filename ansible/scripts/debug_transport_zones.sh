#!/bin/bash
# Debug: show transport zone details from workload NSX Manager
# Requires: ssh -D 1080 -N ubuntu@<gateway-public-ip>

curl -sk -u admin:'VMware1!VMware1!' \
  --proxy socks5h://localhost:1080 \
  "https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/sites/default/enforcement-points/default/transport-zones" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for tz in data.get('results', []):
    print(json.dumps({
        'id': tz.get('id'),
        'display_name': tz.get('display_name'),
        'tz_type': tz.get('tz_type'),
        'is_default': tz.get('is_default'),
        'path': tz.get('path'),
    }, indent=2))
    print()
"
