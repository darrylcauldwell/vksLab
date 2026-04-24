#!/bin/bash
# Run an Ansible playbook with 1Password session.
# Single biometric prompt — all op lookups use the cached session.
#
# Usage:
#   ./run.sh playbooks/phase1_foundation.yml
#   ./run.sh playbooks/phase1_foundation.yml --start-at-task="Deploy dnsmasq"
#   ./run.sh playbooks/sop/sync.yml

set -e

if [ -z "$1" ]; then
    echo "Usage: ./run.sh <playbook> [ansible-playbook args...]"
    exit 1
fi

exec op run -- ansible-playbook "$@"
