#!/bin/bash
# One-time fix: install vcf_sdk and dependencies into the system Python
# that Ansible uses for localhost modules on macOS.
# Requires sudo.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")

echo "Installing vcf_sdk into: $SITE_PACKAGES"
echo "This requires sudo..."

sudo rm -rf "$SITE_PACKAGES/vcf_sdk"
sudo cp -r "$REPO_ROOT/ansible/python/vcf_sdk" "$SITE_PACKAGES/vcf_sdk"
sudo find "$SITE_PACKAGES/vcf_sdk" -type d -exec chmod 755 {} +
sudo find "$SITE_PACKAGES/vcf_sdk" -type f -exec chmod 644 {} +

echo "Installing Python dependencies (requests, pydantic, urllib3)..."
sudo python3 -m pip install requests pydantic urllib3 --break-system-packages 2>/dev/null || \
  sudo python3 -m pip install requests pydantic urllib3

echo ""
echo "Verifying..."
python3 -c "from vcf_sdk import SDDCManager, CloudBuilder; print('vcf_sdk OK')"
echo "Done."
