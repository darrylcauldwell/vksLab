#!/bin/bash
# Fix GRD RDP on a gateway where the playbook failed mid-run.
# Run as the ubuntu user on the gateway.
set -e

sudo pkill grdctl 2>/dev/null || true

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

mkdir -p ~/.local/share/gnome-remote-desktop

openssl req -x509 -newkey rsa:2048 \
  -keyout ~/.local/share/gnome-remote-desktop/grd-tls.key \
  -out ~/.local/share/gnome-remote-desktop/grd-tls.crt \
  -days 365 -nodes -subj "/CN=gateway"

grdctl rdp set-tls-cert ~/.local/share/gnome-remote-desktop/grd-tls.crt
grdctl rdp set-tls-key ~/.local/share/gnome-remote-desktop/grd-tls.key
grdctl rdp set-credentials ubuntu VMware1!
grdctl rdp enable
grdctl rdp disable-view-only
systemctl --user restart gnome-remote-desktop

echo "GRD RDP configured — try connecting now."
