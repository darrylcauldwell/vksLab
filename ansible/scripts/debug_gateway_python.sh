#!/bin/bash
# Debug: verify vcf_sdk is importable on the gateway
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Gateway Python interpreter ==="
ansible gateways -m setup -a "filter=ansible_python" 2>&1 | grep executable

echo ""
echo "=== Direct import test ==="
ansible gateways -m command -a "python3 -c 'from vcf_sdk import SDDCManager; print(\"OK\")'" 2>&1

echo ""
echo "=== Check vcf_sdk location ==="
ansible gateways -m command -a "ls -la /usr/lib/python3/dist-packages/vcf_sdk/__init__.py" 2>&1

echo ""
echo "=== Python3.12 sys.path ==="
ansible gateways -m command -a "python3.12 -c 'import sys; print(chr(10).join(sys.path))'" 2>&1

echo ""
echo "=== Python3.12 import test ==="
ansible gateways -m command -a "python3.12 -c 'from vcf_sdk import SDDCManager; print(\"OK\")'" 2>&1
