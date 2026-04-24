#!/bin/bash
# Recreate Python venv and install dependencies.
# Run from repo root: ./setup-venv.sh
set -e
cd "$(dirname "$0")"

echo "Removing old venv..."
rm -rf .venv

echo "Creating new venv..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing ansible-core..."
pip install ansible-core

echo "Done. Now run:"
echo "  source .venv/bin/activate"
echo "  cd ansible"
echo "  ./run.sh playbooks/phase1_foundation.yml"
