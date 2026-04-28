#!/bin/bash
# Run an Ansible playbook with 1Password secrets pre-loaded.
#
# Fetches all secrets ONCE before Ansible starts, writes them to
# inventory/group_vars/secrets.yml so Ansible auto-loads them.
# Single biometric prompt. Cached for 1 hour.
#
# Usage:
#   ./run.sh playbooks/phase1_foundation.yml
#   ./run.sh playbooks/phase1_foundation.yml --start-at-task="Deploy dnsmasq"
#   ./run.sh playbooks/sop/sync.yml

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate venv if healthy, otherwise use system Python
if [ -z "$VIRTUAL_ENV" ] && [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    # Verify venv has a working ansible-playbook before activating
    if [ -x "$REPO_ROOT/.venv/bin/ansible-playbook" ] && "$REPO_ROOT/.venv/bin/python3" -c "import ansible" 2>/dev/null; then
        source "$REPO_ROOT/.venv/bin/activate"
    else
        echo "WARNING: .venv is broken (missing ansible). Using system Python."
        echo "  To fix: rm -rf $REPO_ROOT/.venv && python3 -m venv .venv && pip install ansible vmware-vcf"
        rm -rf "$REPO_ROOT/.venv"
    fi
fi
mkdir -p "$SCRIPT_DIR/inventory/group_vars/all"
SECRETS_FILE="$SCRIPT_DIR/inventory/group_vars/all/secrets.yml"
VAULT="Employee"

if [ -z "$1" ]; then
    echo "Usage: ./run.sh <playbook> [ansible-playbook args...]"
    exit 1
fi

# Check if secrets file exists and is less than 1 hour old
if [ -f "$SECRETS_FILE" ]; then
    AGE=$(( $(date +%s) - $(stat -f %m "$SECRETS_FILE" 2>/dev/null || stat -c %Y "$SECRETS_FILE" 2>/dev/null) ))
    if [ "$AGE" -lt 3600 ]; then
        echo "Using cached secrets ($(( AGE / 60 ))m old)"
        exec ansible-playbook "$@"
    fi
fi

echo "Fetching secrets from 1Password (single biometric prompt)..."
cat > "$SECRETS_FILE" <<EOF
---
gateway_public_ip: "$(op read "op://$VAULT/Jumpbox Ubuntu/ip_address")"
gateway_password: "$(op read "op://$VAULT/Jumpbox Ubuntu/password")"
bootstrap_password: "$(op read "op://$VAULT/Jumpbox Ubuntu/password")"
esxi_root_password: "$(op read "op://$VAULT/ESXi Root/password")"
vcenter_sso_password: "$(op read "op://$VAULT/vCenter SSO/password")"
sddc_admin_password: "$(op read "op://$VAULT/SDDC Manager/password")"
nsx_admin_password: "$(op read "op://$VAULT/NSX Manager/password")"
keycloak_admin_password: "$(op read "op://$VAULT/Keycloak Admin/password")"
depot_username: "$(op read "op://$VAULT/Offline Depot/username")"
depot_password: "$(op read "op://$VAULT/Offline Depot/password")"
EOF
chmod 600 "$SECRETS_FILE"

echo "Secrets cached. Running playbook..."
exec ansible-playbook "$@"
