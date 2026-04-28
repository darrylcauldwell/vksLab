#!/bin/bash
# Debug: show what Python Ansible uses for localhost
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "$VIRTUAL_ENV" ] && [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
fi

echo "=== Shell Python ==="
which python3
python3 --version

echo ""
echo "=== VIRTUAL_ENV ==="
echo "${VIRTUAL_ENV:-NOT SET}"

echo ""
echo "=== which ansible ==="
which ansible-playbook 2>/dev/null || echo "NOT FOUND"

echo ""
echo "=== Ansible localhost Python ==="
cd "$SCRIPT_DIR/.."
ansible localhost -m setup -a "filter=ansible_python" 2>&1 | grep executable

echo ""
echo "=== vcf_sdk import test (via Ansible module) ==="
ansible localhost -m command -a "python3 -c 'from vcf_sdk import SDDCManager; print(\"OK\")'" 2>&1 | tail -3

echo ""
echo "=== ansible_playbook_python ==="
ansible localhost -m debug -a "var=ansible_playbook_python" 2>&1

echo ""
echo "=== ansible_python_interpreter ==="
ansible localhost -m debug -a "var=ansible_python_interpreter" 2>&1
