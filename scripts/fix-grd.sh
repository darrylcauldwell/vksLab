#!/bin/bash
# Fix GRD RDP on a gateway where the playbook failed mid-run.
# Run as the ubuntu user on the gateway.
set -e

RDP_PASSWORD="${1:?Usage: $0 <rdp-password>}"

sudo pkill grdctl 2>/dev/null || true

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

# Ensure keyring is unlocked
rm -f ~/.local/share/keyrings/*.keyring
mkdir -p ~/.local/share/keyrings
echo "login" > ~/.local/share/keyrings/default
echo -n "" | gnome-keyring-daemon --unlock

# Generate TLS certificate
mkdir -p ~/.local/share/gnome-remote-desktop
openssl req -x509 -newkey rsa:2048 \
  -keyout ~/.local/share/gnome-remote-desktop/grd-tls.key \
  -out ~/.local/share/gnome-remote-desktop/grd-tls.crt \
  -days 365 -nodes -subj "/CN=gateway"

# Configure GRD
grdctl rdp set-tls-cert ~/.local/share/gnome-remote-desktop/grd-tls.crt
grdctl rdp set-tls-key ~/.local/share/gnome-remote-desktop/grd-tls.key
grdctl rdp set-credentials ubuntu "$RDP_PASSWORD"
grdctl rdp enable
grdctl rdp disable-view-only
systemctl --user restart gnome-remote-desktop

echo "GRD RDP configured — try connecting now."
