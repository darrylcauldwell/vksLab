#!/bin/bash
# Debug: trace the exact vcf_sdk import failure on the gateway
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Full import traceback ==="
ansible gateways -m command -a "python3 -c \"
import traceback
try:
    from vcf_sdk.sddc_manager import SDDCManager
    print('SDDCManager OK')
except Exception as e:
    traceback.print_exc()
\"" 2>&1

echo ""
echo "=== Test individual dependencies ==="
for mod in requests pydantic urllib3; do
    echo -n "$mod: "
    ansible gateways -m command -a "python3 -c \"import $mod; print($mod.__version__)\"" 2>&1 | grep -E "SUCCESS|FAILED|Error|version"
done

echo ""
echo "=== Test vcf_sdk sub-imports ==="
for mod in vcf_sdk.exceptions vcf_sdk.auth vcf_sdk.base vcf_sdk.version_check vcf_sdk.versions vcf_sdk.managers vcf_sdk.sddc_manager; do
    echo -n "$mod: "
    ansible gateways -m command -a "python3 -c \"import $mod; print('OK')\"" 2>&1 | grep -E "OK|Error|FAILED"
done

echo ""
echo "=== vcf_sdk location ==="
ansible gateways -m command -a "python3 -c \"import vcf_sdk; print(vcf_sdk.__file__)\"" 2>&1
