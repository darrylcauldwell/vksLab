#!/bin/bash
# Fix GRD RDP on a gateway where the playbook failed mid-run.
# Run as root on the gateway: sudo ./fix-grd.sh <rdp-password>
set -e

RDP_PASSWORD="${1:?Usage: $0 <rdp-password>}"

pkill grdctl 2>/dev/null || true

# Generate TLS certificate
mkdir -p /etc/gnome-remote-desktop
openssl req -x509 -newkey rsa:2048 \
  -keyout /etc/gnome-remote-desktop/grd-tls.key \
  -out /etc/gnome-remote-desktop/grd-tls.crt \
  -days 365 -nodes -subj "/CN=gateway"
chmod 600 /etc/gnome-remote-desktop/grd-tls.*

# Configure GRD system mode (no keyring, no D-Bus)
grdctl --system rdp set-tls-cert /etc/gnome-remote-desktop/grd-tls.crt
grdctl --system rdp set-tls-key /etc/gnome-remote-desktop/grd-tls.key
grdctl --system rdp set-credentials ubuntu "$RDP_PASSWORD"
grdctl --system rdp disable-view-only
grdctl --system rdp enable
systemctl restart gnome-remote-desktop

echo "GRD RDP configured in system mode — try connecting now."
