#!/bin/bash
# One-time fix: install vcf_sdk and dependencies into the Python
# that Ansible uses for localhost module execution on macOS.
# Requires sudo.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# The Python that brew's ansible-playbook uses internally
ANSIBLE_PYTHON="/opt/homebrew/Cellar/ansible/13.6.0/libexec/bin/python"

# Fall back to detection if path doesn't exist
if [ ! -x "$ANSIBLE_PYTHON" ]; then
    ANSIBLE_PYTHON=$(ansible -m debug -a "var=ansible_playbook_python" localhost 2>/dev/null | grep -oP '(?<=": ")[^"]+' || true)
fi

if [ -z "$ANSIBLE_PYTHON" ] || [ ! -x "$ANSIBLE_PYTHON" ]; then
    echo "ERROR: Cannot find Ansible's Python interpreter"
    echo "Run: ansible -m debug -a 'var=ansible_playbook_python' localhost"
    exit 1
fi

SITE_PACKAGES=$($ANSIBLE_PYTHON -c "import site; print(site.getsitepackages()[0])")

echo "Ansible Python: $ANSIBLE_PYTHON"
echo "Site-packages: $SITE_PACKAGES"
echo ""

echo "Installing vcf_sdk..."
sudo rm -rf "$SITE_PACKAGES/vcf_sdk"
sudo cp -r "$REPO_ROOT/ansible/python/vcf_sdk" "$SITE_PACKAGES/vcf_sdk"
sudo find "$SITE_PACKAGES/vcf_sdk" -type d -exec chmod 755 {} +
sudo find "$SITE_PACKAGES/vcf_sdk" -type f -exec chmod 644 {} +

echo "Installing pydantic v2 from vendored wheels..."
sudo $ANSIBLE_PYTHON -m pip install --no-index --force-reinstall \
  --find-links "$REPO_ROOT/ansible/python/wheels" \
  pydantic pydantic_core typing_extensions annotated_types typing_inspection \
  2>/dev/null || \
sudo $ANSIBLE_PYTHON -m pip install --no-index --force-reinstall \
  --find-links "$REPO_ROOT/ansible/python/wheels" \
  pydantic pydantic_core typing_extensions annotated_types typing_inspection

echo ""
echo "Verifying..."
$ANSIBLE_PYTHON -c "from vcf_sdk import SDDCManager, CloudBuilder; print('vcf_sdk OK')"
echo "Done."
