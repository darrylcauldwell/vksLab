---
title: "VKS Lab"
subtitle: "Delivery Guide"
author: "dreamfold"
date: "March 2026"
---

# Delivery Guide

## 1. Deployment Overview

The lab is built in six sequential phases. Each phase depends on the successful completion of the previous one. The entire deployment can be completed in one to two days, depending on VCF bringup duration and resource availability.

| Phase | Name | Depends On | Duration Estimate |
|-------|------|------------|-------------------|
| 1 | Foundation | — | 2-3 hours |
| 2 | Nested ESXi | Phase 1 | 1-2 hours |
| 3 | VCF Management Domain | Phase 2 | 3-4 hours |
| 4 | VCF Workload Domain | Phase 3 | 2-3 hours |
| 5 | NSX Networking | Phase 4 | 1-2 hours |
| 6 | VKS | Phase 5 | 1-2 hours |

**Phase 1** establishes the vApp, jumpbox (DNS, NTP, CA, inter-VLAN routing, Quagga BGP). **Phase 2** deploys all seven nested ESXi hosts. **Phase 3** runs the VCF Installer to bring up the management domain (vCenter, SDDC Manager, NSX Manager, VCF Operations, VCF Automation). **Phase 4** commissions workload hosts and creates the workload domain. **Phase 5** deploys the NSX Edge cluster, configures Tier-0/Tier-1 gateways, establishes BGP peering, and creates the NSX VPC. **Phase 6** enables the Supervisor, creates a vSphere Namespace, and deploys a VKS cluster with a test workload.

## 2. Prerequisites

> Before starting deployment, verify that all assumptions from [Conceptual Design](conceptual-design.md) Section 7 hold true. See Section 2.2 below for the verification checklist.

The following must be in place before starting Phase 1.

| # | Prerequisite | Status |
|---|-------------|--------|
| 1 | vCD resources approved (60 vCPU, 512 GB RAM, 1.5 TB storage) | ☐ |
| 2 | Ubuntu ISO available in vCD Content Hub (`ubuntu-24.04.2-live-server-amd64.iso`), ESXi vApp template available (`[baked]esxi-9.0.2-2514807`) | ☐ |
| 3 | VCF Installer OVA (`VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova`, 2.03 GB) — download from support.broadcom.com to operator laptop, SCP to jumpbox per §5.2 | ☐ |
| 4 | DNS zone `lab.dreamfold.dev` prepared (internal use only or delegated) | ☐ |
| 5 | VLAN trunk configuration confirmed on vCD private network (MTU 9000 support) | ☐ |
| 6 | Licences: not required — VCF 9.0 License Later provides 90-day grace (lab lease is 14 days) | ☐ |
| 7 | 1Password credentials created in "VKS Lab" vault (see §2.1 and §3.2c) | ☐ |
| 8 | VCF offline depot reachable (`depot.vcf-gcp.broadcom.net`) | ☐ |
| 9 | vCD org administrator credentials available | ☐ |
| 10 | RDP client installed on operator workstation | ☐ |

### 2.1 Credentials Checklist

The following credentials must be prepared before deployment. All are stored in the 1Password **VKS Lab** vault and retrieved by Ansible at runtime. VCF enforces password complexity: minimum 12 characters, with uppercase, lowercase, digit, and special character.

| # | 1Password Item | Username | Used By | Notes |
|---|---------------|----------|---------|-------|
| 1 | ESXi Root | `root` | All 7 ESXi hosts | Must be identical across all hosts for VCF bringup |
| 2 | vCenter SSO | `administrator@vsphere.local` | vcenter-mgmt, vcenter-wld | vSphere SSO administrator |
| 3 | SDDC Manager | `admin@local` | sddc-manager | SDDC Manager local admin |
| 4 | NSX Manager | `admin` | nsx-mgr-mgmt, nsx-mgr-wld | NSX Manager admin |
| 5 | Keycloak Admin | `admin` | jumpbox (Keycloak container) | Keycloak admin console |

### 2.2 Assumptions Verification

Verify each assumption before proceeding to Phase 1. Cross-reference: [Conceptual Design](conceptual-design.md) Section 7.

| ID | Assumption | Verification Method | Verified |
|----|-----------|-------------------|----------|
| A-001 | vCD supports nested virtualisation and jumbo frames (MTU 9000) | Deploy test VM; enable nested virt flag; ping with `-s 8972` across vCD private network | ☐ |
| A-002 | Sufficient vCD resources (60 vCPU, 512 GB RAM, 1.5 TB storage) | Check vCD tenant portal → Organisation → Allocation | ☐ |
| A-004 | VCF offline depot reachable | `curl -s https://depot.vcf-gcp.broadcom.net` from jumpbox returns a response | ☐ |
| A-005 | lab.dreamfold.dev DNS zone delegated or internal-only | Confirm zone delegation record exists or document internal-only usage | ☐ |

## 3. Phase 1 — Foundation

> Phase 1 implements R-001, R-002, R-003, R-009 via VCD-01, VCD-02, NET-01, NET-05, SVC-01 through SVC-08.

### 3.1 Create vCD vApp

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1.1 | Create new vApp in vCloud Director | Empty vApp created |
| 3.1.2 | Add routed network (public) to vApp | External connectivity available |
| 3.1.3 | Add isolated network (private, MTU 9000) to vApp | Trunk-capable internal network available |

### 3.2 Deploy and Configure Jumpbox

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.2.1 | Deploy Ubuntu 24.04 VM (2 vCPU, 10 GB RAM, 60 GB disk) | VM powered on | VM accessible via vCD console |
| 3.2.2 | Configure NIC1 (ens160) on public network | DHCP address obtained | `ip addr show ens160` shows IP |
| 3.2.3 | Configure NIC2 (ens192) on private network as VLAN trunk (MTU 9000) | Static IP configured | `ping 10.0.10.1` from local |
| 3.2.4 | Install XFCE desktop and xrdp | Remote desktop available | RDP connection on port 3389 |
| 3.2.5 | Install and configure dnsmasq for lab.dreamfold.dev | DNS server running | `dig @10.0.10.1 jumpbox.lab.dreamfold.dev` |
| 3.2.6 | Install and configure chrony | NTP server running | `chronyc sources` shows upstream |
| 3.2.7 | Install and configure step-ca | CA running with ACME | `step ca health` returns ok |
| 3.2.8 | Install Firefox for web management UIs | Browser available | Launch Firefox via RDP |

#### Jumpbox netplan configuration

```yaml
# /etc/netplan/01-lab.yaml
network:
  version: 2
  ethernets:
    ens160:
      dhcp4: true
    ens192:
      mtu: 9000
  vlans:
    ens192.10:
      id: 10
      link: ens192
      addresses: [10.0.10.1/24]
      mtu: 1500
      nameservers:
        addresses: [127.0.0.1]
    ens192.20:
      id: 20
      link: ens192
      addresses: [10.0.20.1/24]
      mtu: 9000
    ens192.30:
      id: 30
      link: ens192
      addresses: [10.0.30.1/24]
      mtu: 9000
    ens192.40:
      id: 40
      link: ens192
      addresses: [10.0.40.1/24]
      mtu: 9000
    ens192.50:
      id: 50
      link: ens192
      addresses: [10.0.50.1/24]
      mtu: 9000
    ens192.60:
      id: 60
      link: ens192
      addresses: [10.0.60.1/24]
      mtu: 1500
```

Apply with `sudo netplan apply`.

#### dnsmasq configuration (DNS + DHCP)

```ini
# /etc/dnsmasq.d/lab.conf
domain=lab.dreamfold.dev
local=/lab.dreamfold.dev/
server=192.19.189.20
server=192.19.189.10
server=192.19.189.30

# --- DNS Records ---
# Infrastructure
address=/jumpbox.lab.dreamfold.dev/10.0.10.1
address=/vcf-installer.lab.dreamfold.dev/10.0.10.3
address=/vcenter-mgmt.lab.dreamfold.dev/10.0.10.4
address=/sddc-manager.lab.dreamfold.dev/10.0.10.5
address=/nsx-mgr-mgmt.lab.dreamfold.dev/10.0.10.6
address=/vcf-ops.lab.dreamfold.dev/10.0.10.7
address=/vcf-auto.lab.dreamfold.dev/10.0.10.8
address=/vcenter-wld.lab.dreamfold.dev/10.0.10.9
address=/nsx-mgr-wld.lab.dreamfold.dev/10.0.10.10
# ESXi hosts
address=/esxi-01.lab.dreamfold.dev/10.0.10.11
address=/esxi-02.lab.dreamfold.dev/10.0.10.12
address=/esxi-03.lab.dreamfold.dev/10.0.10.13
address=/esxi-04.lab.dreamfold.dev/10.0.10.14
address=/esxi-05.lab.dreamfold.dev/10.0.10.15
address=/esxi-06.lab.dreamfold.dev/10.0.10.16
address=/esxi-07.lab.dreamfold.dev/10.0.10.17
# NSX Edges
address=/edge-01.lab.dreamfold.dev/10.0.10.20
address=/edge-02.lab.dreamfold.dev/10.0.10.21

# --- DHCP on VLAN 10 (management) ---
dhcp-range=10.0.10.100,10.0.10.199,255.255.255.0,12h
dhcp-option=option:router,10.0.10.1
dhcp-option=option:dns-server,10.0.10.1
dhcp-option=option:ntp-server,10.0.10.1

# Static MAC→IP reservations (replace xx:xx with actual MACs from vCD)
dhcp-host=00:50:56:xx:xx:01,esxi-01,10.0.10.11
dhcp-host=00:50:56:xx:xx:02,esxi-02,10.0.10.12
dhcp-host=00:50:56:xx:xx:03,esxi-03,10.0.10.13
dhcp-host=00:50:56:xx:xx:04,esxi-04,10.0.10.14
dhcp-host=00:50:56:xx:xx:05,esxi-05,10.0.10.15
dhcp-host=00:50:56:xx:xx:06,esxi-06,10.0.10.16
dhcp-host=00:50:56:xx:xx:07,esxi-07,10.0.10.17
```

#### chrony configuration

```ini
# /etc/chrony/chrony.conf
pool ntp.broadcom.net iburst
allow 10.0.0.0/16
```

### 3.2a Certificate Distribution (R-009, SVC-02)

After step-ca is running, the root CA certificate must be distributed to all components that will validate TLS certificates. This is done progressively as components are deployed.

| Phase | Target | Method |
|-------|--------|--------|
| Phase 2 | ESXi hosts | **Automated by `esxi_prepare` role** — copies root cert and runs `esxcli security cert import` via `phase2_esxi.yml` |
| Phase 3 | VCF Installer | Provide root cert during OVA deployment parameters |
| Phase 3 | vCenter, SDDC Manager, NSX Manager | Deployed by VCF Installer — configure trusted root in bringup workbook |
| Phase 4 | Workload vCenter, NSX Manager | Deployed by SDDC Manager — inherits trust from management domain |

Export the root CA certificate from step-ca:

```bash
step ca root /tmp/lab-root-ca.crt
```

For reference — the following manual steps are automated by `phase2_esxi.yml` and do not need to be run separately:

```bash
# Automated by esxi_prepare role — shown for reference only
scp /tmp/lab-root-ca.crt root@esxi-XX:/tmp/
ssh root@esxi-XX 'esxcli security cert import --cert-file /tmp/lab-root-ca.crt'
```

### 3.2b Internet Access from Nested Environment

VCF depot sync (via `depot.vcf-gcp.broadcom.net`), content library updates, and VKS image pulls require outbound internet access from the nested environment. Components on the management VLAN (10.0.10.x) must be able to reach external URLs.

The jumpbox is dual-homed (public NIC + management VLAN) and provides outbound internet for the entire lab. IP masquerading on the jumpbox allows all hosts on the management VLAN (and other VLANs) to reach external URLs via the jumpbox's public NIC:

```bash
# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.d/99-lab-forwarding.conf

# Add masquerade rule for traffic from the lab network exiting via the public NIC
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/16 -o ens160 -j MASQUERADE

# Persist iptables rules
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

| Verification | Command | Expected Result |
|-------------|---------|-----------------|
| Jumpbox forwarding | `cat /proc/sys/net/ipv4/ip_forward` | 1 |
| Masquerade rule | `sudo iptables -t nat -L POSTROUTING` | MASQUERADE rule present |
| ESXi internet access | `ssh root@esxi-01 'vmkping -I vmk0 8.8.8.8'` | Success |

### 3.2c 1Password Secret Store

Ansible runs from the operator's laptop and retrieves all lab credentials from 1Password using the `community.general.onepassword` lookup plugin. This requires the 1Password CLI (`op`) and a vault named **VKS Lab**.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.2c.1 | Install 1Password CLI (`op`) on operator laptop | CLI available | `op --version` |
| 3.2c.2 | Sign in to 1Password CLI | Authenticated | `op vault list` shows vaults |
| 3.2c.3 | Create "VKS Lab" vault | Vault exists | `op vault get "VKS Lab"` |
| 3.2c.4 | Create credential items in the vault | All items stored | `op item list --vault "VKS Lab"` |

```bash
# Install 1Password CLI (macOS)
brew install --cask 1password-cli

# Sign in (interactive — opens 1Password desktop app or prompts for credentials)
eval $(op signin)

# Create the lab vault
op vault create "VKS Lab"

# Store credentials with auto-generated VCF-compliant passwords
# (20 chars, letters + digits + symbols meets VCF 12-char minimum with complexity)
op item create --vault "VKS Lab" --category login --title "ESXi Root" \
  --generate-password='20,letters,digits,symbols' username=root
op item create --vault "VKS Lab" --category login --title "vCenter SSO" \
  --generate-password='20,letters,digits,symbols' username='administrator@vsphere.local'
op item create --vault "VKS Lab" --category login --title "SDDC Manager" \
  --generate-password='20,letters,digits,symbols' username='admin@local'
op item create --vault "VKS Lab" --category login --title "NSX Manager" \
  --generate-password='20,letters,digits,symbols' username=admin
op item create --vault "VKS Lab" --category login --title "Keycloak Admin" \
  --generate-password='20,letters,digits,symbols' username=admin
```

Ansible retrieves these credentials at runtime via lookups in `group_vars/all.yml`:

```yaml
esxi_root_password: "{{ lookup('community.general.onepassword', 'ESXi Root', field='password', vault='VKS Lab') }}"
```

### 3.3 Ansible Setup on Operator Laptop

Ansible runs from the operator's laptop (not the jumpbox) and connects to lab hosts via SSH ProxyJump through the jumpbox. Install it in a Python virtual environment to avoid conflicts with system packages.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.3.1 | Create Python virtual environment | venv created | `.venv/` directory exists |
| 3.3.2 | Install ansible-core | Ansible available | `ansible --version` |
| 3.3.3 | Install required Ansible collections | Collections installed | `ansible-galaxy collection list` shows community.general |
| 3.3.4 | Validate inventory resolves | All IPs derived correctly | No errors in output |

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Ansible
pip install ansible-core

# Install required collections (1Password lookups, VMware modules)
ansible-galaxy collection install -r ansible/collections/requirements.yml

# Validate inventory (variables won't fully resolve without 1Password,
# but Jinja2 syntax errors will surface here)
ansible-playbook -i ansible/inventory/hosts.yml --check ansible/playbooks/phase2_esxi.yml 2>&1 | head -5
```

> **Note**: Activate the virtual environment (`source .venv/bin/activate`) before running any `ansible-playbook` commands. The `.venv/` directory is already in `.gitignore`.

### 3.4 Keycloak Identity Provider (R-002, SVC-07, SVC-08)

Deploy Keycloak as a Docker container on the jumpbox for centralised OIDC identity. Keycloak provides SSO for vCenter and NSX Manager, replacing per-component local authentication.

**Prerequisites**: Docker Engine running on jumpbox. Keycloak admin password stored in 1Password (step 3.2c.4).

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.4.1 | Retrieve Keycloak admin password from 1Password | Password available | `op item get "Keycloak Admin" --vault "VKS Lab" --fields password` |
| 3.4.2 | Run Keycloak container (port 8443, HTTPS) | Container running | `docker ps` shows keycloak |
| 3.4.3 | Wait for Keycloak to start (1-2 minutes) | Admin console accessible | `https://jumpbox.lab.dreamfold.dev:8443` loads |
| 3.4.4 | Create "lab" realm | Realm created | Realm visible in admin console |
| 3.4.5 | Create "admin" user with admin role | User created | User appears in realm user list |
| 3.4.6 | Create "operator" user with view-only role | User created | User appears in realm user list |
| 3.4.7 | Create OIDC client for vCenter | Client created | Client ID `vcenter` visible in realm |
| 3.4.8 | Create OIDC client for NSX Manager | Client created | Client ID `nsx-manager` visible in realm |

```bash
# Retrieve admin password from 1Password
export KC_ADMIN_PASS=$(op item get "Keycloak Admin" --vault "VKS Lab" --fields password)

# Run Keycloak container with HTTPS on port 8443
docker run -d --name keycloak \
  -p 8443:8443 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD="${KC_ADMIN_PASS}" \
  -e KC_HOSTNAME=jumpbox.lab.dreamfold.dev \
  -e KC_HTTPS_CERTIFICATE_FILE=/opt/keycloak/conf/server.crt \
  -e KC_HTTPS_CERTIFICATE_KEY_FILE=/opt/keycloak/conf/server.key \
  -v /etc/step-ca/certs/keycloak.crt:/opt/keycloak/conf/server.crt:ro \
  -v /etc/step-ca/certs/keycloak.key:/opt/keycloak/conf/server.key:ro \
  -v keycloak-data:/opt/keycloak/data \
  --restart unless-stopped \
  quay.io/keycloak/keycloak:latest start

# Wait for Keycloak to become ready
sleep 60

# Obtain admin access token
KC_TOKEN=$(curl -s -X POST \
  "https://jumpbox.lab.dreamfold.dev:8443/realms/master/protocol/openid-connect/token" \
  -d "grant_type=client_credentials&client_id=admin-cli" \
  -d "grant_type=password&username=admin&password=${KC_ADMIN_PASS}&client_id=admin-cli" \
  --cacert /tmp/lab-root-ca.crt | jq -r '.access_token')

# Create "lab" realm
curl -s -X POST "https://jumpbox.lab.dreamfold.dev:8443/admin/realms" \
  -H "Authorization: Bearer ${KC_TOKEN}" \
  -H "Content-Type: application/json" \
  --cacert /tmp/lab-root-ca.crt \
  -d '{"realm": "lab", "enabled": true, "displayName": "VKS Lab"}'

# Create admin user
curl -s -X POST "https://jumpbox.lab.dreamfold.dev:8443/admin/realms/lab/users" \
  -H "Authorization: Bearer ${KC_TOKEN}" \
  -H "Content-Type: application/json" \
  --cacert /tmp/lab-root-ca.crt \
  -d '{"username": "lab-admin", "enabled": true, "credentials": [{"type": "password", "value": "CHANGE-ME", "temporary": false}]}'

# Create operator user
curl -s -X POST "https://jumpbox.lab.dreamfold.dev:8443/admin/realms/lab/users" \
  -H "Authorization: Bearer ${KC_TOKEN}" \
  -H "Content-Type: application/json" \
  --cacert /tmp/lab-root-ca.crt \
  -d '{"username": "lab-operator", "enabled": true, "credentials": [{"type": "password", "value": "CHANGE-ME", "temporary": false}]}'
```

**TLS certificate**: Before starting Keycloak, issue a TLS certificate from step-ca for the Keycloak HTTPS endpoint:

```bash
step ca certificate jumpbox.lab.dreamfold.dev \
  /etc/step-ca/certs/keycloak.crt /etc/step-ca/certs/keycloak.key \
  --san jumpbox.lab.dreamfold.dev \
  --not-after 8760h
```

#### Configure vCenter OIDC Identity Source

After VCF bringup (Phase 3), configure each vCenter to use Keycloak as an external identity provider.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.4.9 | In vCenter, navigate to Administration → Single Sign-On → Configuration → Identity Provider | Identity provider settings page | — |
| 3.4.10 | Add OIDC identity provider with Keycloak discovery URL | Provider configured | Discovery URL validated |
| 3.4.11 | Set Client ID to `vcenter`, provide client secret | Client credentials accepted | — |
| 3.4.12 | Map Keycloak groups to vCenter roles (Administrators, ReadOnly) | Role mappings created | Keycloak users can login |
| 3.4.13 | Test SSO login with `lab-admin` user | Login succeeds | vCenter dashboard loads |

vCenter OIDC configuration parameters:

| Parameter | Value |
|-----------|-------|
| Provider Name | Keycloak Lab |
| Discovery Endpoint | `https://jumpbox.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration` |
| Client ID | `vcenter` |
| Client Secret | (generated in Keycloak admin console) |

#### Configure NSX Manager OIDC Identity Source

Configure each NSX Manager to use Keycloak as an external identity provider.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.4.14 | In NSX Manager, navigate to System → Settings → User Management → OIDC | OIDC configuration page | — |
| 3.4.15 | Add OIDC provider with Keycloak discovery URL | Provider configured | Metadata fetched |
| 3.4.16 | Set Client ID to `nsx-manager`, provide client secret | Client credentials accepted | — |
| 3.4.17 | Map Keycloak roles to NSX RBAC roles | Role mappings created | Keycloak users can login |
| 3.4.18 | Test SSO login with `lab-admin` user | Login succeeds | NSX dashboard loads |

NSX Manager OIDC configuration parameters:

| Parameter | Value |
|-----------|-------|
| Provider Name | Keycloak Lab |
| Discovery Endpoint | `https://jumpbox.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration` |
| Client ID | `nsx-manager` |
| Client Secret | (generated in Keycloak admin console) |

**Note**: Steps 3.4.9 through 3.4.18 cannot be completed until after VCF bringup (Phase 3) and workload domain creation (Phase 4), because vCenter and NSX Manager must be deployed first. Return to these steps after Phase 4 is complete.

#### Keycloak Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Keycloak admin console | Browse `https://jumpbox.lab.dreamfold.dev:8443` | Login page loads |
| Lab realm exists | Admin console → Realms | "lab" realm listed |
| Users created | Admin console → lab realm → Users | lab-admin and lab-operator listed |
| OIDC discovery | `curl https://jumpbox.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration` | JSON with issuer, token, and auth endpoints |
| vCenter SSO login | Login to vCenter with Keycloak user | Dashboard loads |
| NSX SSO login | Login to NSX Manager with Keycloak user | Dashboard loads |

### 3.5 Foundation Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| Jumpbox external access | RDP to jumpbox public IP | Desktop accessible |
| Jumpbox DNS | `dig @10.0.10.1 jumpbox.lab.dreamfold.dev` | Returns 10.0.10.1 |
| Jumpbox NTP | `chronyc sources` | Shows upstream servers |
| Jumpbox CA | `step ca health` | Returns "ok" |
| VLAN sub-interfaces | `ip addr show ens192.10` on jumpbox | Shows 10.0.10.1 |
| Inter-VLAN routing | `ping 10.0.20.1` from a host on VLAN 10 | Success |
| Quagga BGP | `vtysh -c 'show ip bgp summary'` on jumpbox | Quagga running |

## 4. Phase 2 — Nested ESXi

> Phase 2 implements R-004, R-007 via ESX-01 through ESX-04 and NET-03, NET-04.

### 4.1 Deploy Management Domain Hosts

ESXi hosts receive their management IP via DHCP from the jumpbox dnsmasq (configured in Phase 1). Note the MAC address assigned by vCD for each VM and update the `dhcp-host` entries in `/etc/dnsmasq.d/lab.conf` before first boot.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 4.1.1 | Clone esxi-01 from vApp template `[baked]esxi-9.0.2-2514807` in vCD (8 vCPU, 72 GB RAM, 200 GB NVMe disk) | VM powered on | ESXi DCUI accessible |
| 4.1.2 | Note vmnic0 MAC address assigned by vCD, update `esxi_mac` in `ansible/inventory/hosts.yml` | MAC recorded | Inventory updated |
| 4.1.3 | Configure vmnic0 on VLAN 10 (access), vmnic1 on trunk | Networking connected | Host receives IP via DHCP |
| 4.1.4 | Repeat steps 4.1.1-4.1.3 for esxi-02 through esxi-04 | All 4 hosts deployed | All pingable from jumpbox |

### 4.2 Deploy Workload Domain Hosts

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 4.2.1 | Clone esxi-05 through esxi-07 from vApp template `[baked]esxi-9.0.2-2514807` (same spec as management hosts) | VMs powered on | ESXi DCUI accessible |
| 4.2.2 | Note MAC addresses assigned by vCD, update `esxi_mac` in `ansible/inventory/hosts.yml` | MACs recorded | Inventory updated |
| 4.2.3 | Configure vmnic0 on VLAN 10 (access), vmnic1 on trunk | Networking connected | All pingable from jumpbox |

### 4.3 Prepare Hosts (Automated)

Use the Ansible `esxi_prepare` role to configure all hosts. This sets hostname, DNS, NTP, root password, and prepares vSAN ESA in a single operation.

```bash
# From the jumpbox
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/phase2_esxi.yml

# Or prepare a single host
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/phase2_esxi.yml --limit esxi-01
```

The `prepare` command performs these steps on each host via SSH:

1. Set hostname (`esxcli system hostname set`)
2. Configure DNS server (`esxcli network ip dns server add`)
3. Configure NTP server — 10.0.10.1
4. Set root password
5. **vSAN ESA preparation**:
   - Enable FakeSCSIReservations advanced setting (required for nested SCSI reservations)
   - Mark NVMe storage devices as SSD (nested NVMe appears as non-SSD)
   - Enable vSAN firewall rules (vsan-transport, vsanEncryption)
6. Import CA root certificate
7. Verify network connectivity (`vmkping` to gateway)

> **Note**: VCF 9.0.1+ includes a built-in vSAN ESA HCL bypass for nested environments. The mock HCL VIB (used in earlier VCF versions) is no longer required.

### 4.4 ESXi Host Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| All hosts reachable | `ping 10.0.10.{11..17}` from jumpbox | All respond |
| DNS resolution | `nslookup esxi-01.lab.dreamfold.dev 10.0.10.1` | Returns correct IP for all hosts |
| Reverse DNS | `nslookup 10.0.10.11 10.0.10.1` | Returns esxi-01.lab.dreamfold.dev |
| NTP sync | `esxcli system ntp get` on each host | NTP server configured (10.0.10.1) |
| Time sync | Compare time across all hosts | Within 1 second |
| vSAN ESA ready | `esxcli vsan storage list` on each host | NVMe device marked as SSD |
| Host status | `ansible-playbook ansible/playbooks/phase2_esxi.yml --check` | All tasks show ok |

## 5. Phase 3 — VCF Management Domain

> Phase 3 implements R-004 via VCF-01, VCF-03, VCF-04. VCF Installer drives initial bringup of vCenter, SDDC Manager, and NSX Manager.

### 5.1 Pre-Bringup DNS Records

Verify all DNS records are configured in dnsmasq (done in Phase 1). Forward and reverse records must exist for:

| Hostname | IP | Purpose |
|----------|-----|---------|
| vcf-installer.lab.dreamfold.dev | 10.0.10.3 | VCF Installer |
| vcenter-mgmt.lab.dreamfold.dev | 10.0.10.4 | Management vCenter |
| sddc-manager.lab.dreamfold.dev | 10.0.10.5 | SDDC Manager |
| nsx-mgr-mgmt.lab.dreamfold.dev | 10.0.10.6 | Management NSX Manager |

### 5.2 Download and Deploy VCF Installer

In VCF 9.0, the SDDC Manager appliance doubles as the VCF Installer (Cloud Builder functionality is consolidated into it). The OVA is downloaded once to the operator's laptop and SCP'd to the jumpbox for each deployment — this avoids re-downloading 2+ GB on every lab rebuild.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.2.1 | Download `VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova` (2.03 GB) from support.broadcom.com to operator laptop | OVA saved locally | File exists on laptop |
| 5.2.2 | SCP OVA from laptop to jumpbox: `scp VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova <jumpbox-public-ip>:~/vcf-installer.ova` | OVA on jumpbox | `ls -lh ~/vcf-installer.ova` |
| 5.2.3 | Upload OVA from jumpbox to esxi-01 datastore via `scp` or ESXi Host Client | OVA available on datastore | Datastore browser shows file |
| 5.2.4 | Deploy VCF Installer OVA with IP 10.0.10.3, GW 10.0.10.1, DNS 10.0.10.1 | Appliance deployed | VM powered on |
| 5.2.5 | Wait for installer services to start (5-10 minutes) | Services ready | `https://vcf-installer.lab.dreamfold.dev` accessible |

#### VCF Deployment Parameter Workbook

The bringup spec is defined as a YAML dict in `ansible/roles/vcf_bringup/defaults/main.yml`. All IPs are derived from `lab_network_prefix` and credentials are injected from 1Password at runtime — no manual JSON editing required. The Ansible `vcf_bringup` role validates and submits the spec to the Cloud Builder API.

No licence keys are required at bringup — VCF 9.0 "License Later" mode provides a 90-day grace period. Licences are applied via SDDC Manager after bringup.

#### Troubleshooting: vSAN HCL Timestamp Validation

The VCF Installer validates that its embedded vSAN HCL file (`all.json`) is less than 90 days old. If the installer OVA was built more than 90 days ago, bringup fails with an HCL validation error. To work around this, SSH to the VCF Installer and patch the timestamp:

```bash
ssh vcf@vcf-installer.lab.dreamfold.dev
sudo sed -i 's/"timestamp":"[^"]*"/"timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"/' \
  /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json
sudo sed -i 's/"jsonUpdatedTime":"[^"]*"/"jsonUpdatedTime":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"/' \
  /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json
```

### 5.3 Run VCF Bringup

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.3.1 | Access VCF Installer UI at `https://vcf-installer.lab.dreamfold.dev` | Login page | Browser loads |
| 5.3.2 | Upload deployment parameter workbook (JSON) | Parameters validated | No validation errors |
| 5.3.3 | Start bringup workflow | Deployment begins | Progress bar advancing |
| 5.3.4 | Wait for vCenter deployment | vCenter Server deployed | `https://vcenter-mgmt.lab.dreamfold.dev` accessible |
| 5.3.5 | Wait for VDS and vSAN configuration | Networking and storage configured | vSAN health green in vCenter |
| 5.3.6 | Wait for SDDC Manager deployment | SDDC Manager deployed | `https://sddc-manager.lab.dreamfold.dev` accessible |
| 5.3.7 | Wait for NSX Manager deployment | NSX Manager deployed | `https://nsx-mgr-mgmt.lab.dreamfold.dev` accessible |
| 5.3.8 | Bringup completes | Management domain operational | SDDC Manager shows healthy domain |

### 5.4 Post-Bringup Deployments

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.4.1 | Deploy VCF Operations from SDDC Manager | VCF Ops deployed | `https://vcf-ops.lab.dreamfold.dev` accessible |
| 5.4.2 | Deploy VCF Automation from SDDC Manager | VCF Auto deployed | `https://vcf-auto.lab.dreamfold.dev` accessible |
| 5.4.3 | Remove VCF Installer VM (no longer needed) | Resources reclaimed | VM deleted |

### 5.5 Management Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| vCenter health | Login to `https://vcenter-mgmt.lab.dreamfold.dev` | Cluster shows 4 hosts, all connected |
| vSAN health | vCenter → Cluster → Monitor → vSAN → Health | All health checks green |
| SDDC Manager | Login to `https://sddc-manager.lab.dreamfold.dev` | Management domain shows Active |
| NSX Manager | Login to `https://nsx-mgr-mgmt.lab.dreamfold.dev` | Dashboard accessible, transport nodes connected |
| VCF Operations | Login to `https://vcf-ops.lab.dreamfold.dev` | Dashboard shows management domain |
| VCF Automation | Login to `https://vcf-auto.lab.dreamfold.dev` | Console accessible |

## 6. Phase 4 — VCF Workload Domain

> Phase 4 implements R-004 via VCF-01, VCF-02. Workload hosts are commissioned into the free pool and a VI workload domain is created.

### 6.1 Commission Hosts

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.1.1 | In SDDC Manager, navigate to Hosts → Commission | Commission wizard opens | — |
| 6.1.2 | Add esxi-05, esxi-06, esxi-07 to free pool | Hosts commissioning | Task progress visible |
| 6.1.3 | Wait for host validation and commissioning | Hosts in free pool | SDDC Manager shows 3 hosts available |

### 6.2 Create Workload Domain

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.2.1 | In SDDC Manager, navigate to Domains → Add Domain | Create domain wizard opens | — |
| 6.2.2 | Configure workload domain with 3 hosts, vSAN storage | Domain configuration accepted | Validation passes |
| 6.2.3 | Specify vcenter-wld (10.0.10.9) and nsx-mgr-wld (10.0.10.10) | Appliance config accepted | — |
| 6.2.4 | Start domain creation | Deployment begins | Task progress visible |
| 6.2.5 | Wait for workload domain deployment (60-90 minutes) | Domain created | SDDC Manager shows Active |

### 6.3 Workload Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Workload vCenter | Login to `https://vcenter-wld.lab.dreamfold.dev` | Cluster shows 3 hosts, all connected |
| Workload vSAN | vCenter → Cluster → Monitor → vSAN → Health | All checks green |
| Workload NSX | Login to `https://nsx-mgr-wld.lab.dreamfold.dev` | Dashboard accessible |
| Transport nodes | NSX Manager → System → Fabric → Nodes | 3 host transport nodes configured |
| SDDC Manager | Domains overview | Both domains show Active |

## 7. Phase 5 — NSX Networking

> Phase 5 implements R-006, R-008 via NET-02, NSX-01 through NSX-04. Edge cluster, gateways, BGP, and VPC are configured.

### 7.1 Deploy NSX Edge Cluster

#### Prerequisites for Nested Edge Deployment

**PDPE1GB CPU flag**: NSX Edge VMs require 1GB hugepages. In nested environments, this CPU instruction may not be exposed to the nested ESXi host. If Edge deployment fails, add this VM Advanced Setting on each nested ESXi host VM (in vCD):

```
featMask.vm.cpuid.PDPE1GB = Val:1
```

For AMD Ryzen/Threadripper physical hosts, also add: `monitor_control.enable_fullcpuid = "TRUE"`.

**NSX Edge OVF certificate expiry**: NSX Edge OVF certificates can expire, causing deployment failure with `VALIDATION_ERROR: CERTIFICATE_EXPIRED`. If you encounter this error, follow VMware KB 424034 to replace the expired OVF certificate before retrying Edge deployment.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.1.1 | In workload NSX Manager, navigate to System → Fabric → Edge Clusters | Edge management page | — |
| 7.1.2 | Deploy edge-01 (Large, 8 vCPU, 32 GB RAM) with management IP 10.0.10.20 | Edge VM deployed | `ping 10.0.10.20` |
| 7.1.3 | Deploy edge-02 (Large) with management IP 10.0.10.21 | Edge VM deployed | `ping 10.0.10.21` |
| 7.1.4 | Configure Edge TEP interfaces on VLAN 50 (10.0.50.20, 10.0.50.21) | TEP connectivity | Edge transport node status: Up |
| 7.1.5 | Create Edge cluster with both Edge VMs | Edge cluster created | NSX Manager shows cluster healthy |

### 7.2 Configure Tier-0 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.2.1 | Create Tier-0 gateway (Active-Standby, linked to Edge cluster) | Tier-0 created | Gateway shows Realised |
| 7.2.2 | Add uplink interface on VLAN 60, IP 10.0.60.2/24 | Uplink configured | Interface status: Up |
| 7.2.3 | Configure BGP: ASN 65001, neighbor 10.0.60.1 (ASN 65000), keepalive 60s, hold 180s | BGP configured | — |
| 7.2.4 | Enable route redistribution (connected subnets, NAT) | Routes advertised | — |

### 7.3 Configure BGP on Jumpbox (Quagga)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.3.1 | SSH to jumpbox | CLI access | — |
| 7.3.2 | Verify Quagga BGP configuration deployed by Ansible | BGP configured | `vtysh -c 'show ip bgp summary'` |
| 7.3.3 | Verify BGP adjacency established | Session state: Established | `vtysh -c 'show ip bgp summary'` shows Established |
| 7.3.4 | Verify route exchange | Routes received from NSX | `vtysh -c 'show ip bgp'` shows VPC prefixes |

#### Jumpbox Quagga BGP configuration

```text
router bgp 65000
 bgp router-id 10.0.60.1
 timers bgp 60 180
 neighbor 10.0.60.2 remote-as 65001
 neighbor 10.0.60.2 description NSX-Tier0
 address-family ipv4 unicast
  neighbor 10.0.60.2 activate
  redistribute connected
```

> **BGP timers**: `timers bgp 60 180` sets keepalive to 60 seconds and hold time to 180 seconds (3× keepalive). These are conservative values suited to a nested lab where Edge VM reboots or vSAN latency spikes may briefly delay BGP keepalives. The NSX Tier-0 must be configured with matching timers (keepalive 60, hold 180) to avoid asymmetric dead-peer detection.

### 7.4 Configure Tier-1 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.4.1 | Create Tier-1 gateway linked to Tier-0 | Tier-1 created | Gateway shows Realised |
| 7.4.2 | Configure route advertisement (connected subnets, NAT IPs, LB VIPs) | Advertisements enabled | — |

### 7.5 Configure NSX VPC

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.5.1 | Create VPC project in NSX Manager | Project created | — |
| 7.5.2 | Create VPC (vks-vpc) with centralised connectivity | VPC created | VPC shows Realised |
| 7.5.3 | Configure external connectivity via Tier-0 | Routing configured | — |
| 7.5.4 | Configure Source NAT on Tier-0 for outbound VPC traffic | NAT rules active | See SNAT steps below |

#### Configure SNAT Rules on Tier-0

Two SNAT rules are required — one for the VKS pod CIDR and one for the service CIDR. Both translate outbound traffic to the Tier-0 uplink IP (10.0.60.2) so that external networks can route return traffic.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.5.4a | In NSX Manager, navigate to Networking → NAT → tier0-gateway | NAT rules page | — |
| 7.5.4b | Add SNAT rule: source 192.168.0.0/16 → translated IP 10.0.60.2 | Rule created | Rule shows Active |
| 7.5.4c | Add SNAT rule: source 10.96.0.0/12 → translated IP 10.0.60.2 | Rule created | Rule shows Active |
| 7.5.4d | Verify NAT rules are realised | Both rules Active | NSX Manager → NAT → tier0-gateway shows 2 SNAT rules |

SNAT rule parameters:

| Field | Pod CIDR Rule | Service CIDR Rule |
|-------|--------------|-------------------|
| Action | SNAT | SNAT |
| Source | 192.168.0.0/16 | 10.96.0.0/12 |
| Translated IP | 10.0.60.2 | 10.0.60.2 |
| Applied To | Tier-0 uplink interface | Tier-0 uplink interface |
| Logging | Disabled | Disabled |

> **Note**: These CIDRs match the VKS cluster manifest (`pods.cidrBlocks` and `services.cidrBlocks`). If you change the cluster CIDRs, update the SNAT rules to match.

### 7.6 NSX Networking Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| BGP adjacency | `vtysh -c 'show ip bgp summary'` on jumpbox | Established with 10.0.60.2 |
| Routes from NSX | `vtysh -c 'show ip bgp'` on jumpbox | VPC/overlay prefixes received |
| Routes from jumpbox | NSX Manager → Networking → Tier-0 → Routing Table | Infrastructure subnets received |
| Edge cluster health | NSX Manager → System → Fabric → Edge Clusters | Both Edges Up |
| Tier-0 status | NSX Manager → Networking → Tier-0 Gateways | Realised, interfaces Up |
| VPC status | NSX Manager → VPC overview | vks-vpc shows Realised |

## 8. Phase 6 — VKS

> Phase 6 implements R-005 via VKS-01 through VKS-04. Supervisor enablement, namespace creation, and VKS cluster deployment.

### 8.1 Create Content Library

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.1.1 | In workload vCenter, navigate to Content Libraries | Library management page | — |
| 8.1.2 | Create subscribed library pointing to VMware VKr endpoint | Library created | Sync status: Active |
| 8.1.3 | Wait for initial sync to complete | VKr images available | At least one Kubernetes version listed |

### 8.2 Enable Supervisor

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.2.1 | In workload vCenter, navigate to Workload Management | Supervisor setup wizard | — |
| 8.2.2 | Select workload domain cluster | Cluster selected | — |
| 8.2.3 | Configure networking: NSX, management network, workload network | Networking configured | — |
| 8.2.4 | Configure storage: vSAN Default policy | Storage configured | — |
| 8.2.5 | Start Supervisor enablement | Deployment begins | Task progress visible |
| 8.2.6 | Wait for Supervisor deployment (30-45 minutes) | Supervisor running | Status: Running |

### 8.3 Create vSphere Namespace

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.3.1 | In workload vCenter, navigate to Workload Management → Namespaces | Namespace management | — |
| 8.3.2 | Create namespace "vks-workloads" | Namespace created | Status: Active |
| 8.3.3 | Assign VM classes: best-effort-small, best-effort-medium | VM classes assigned | Listed under namespace |
| 8.3.4 | Assign storage policies: vSAN Default | Storage assigned | Listed under namespace |
| 8.3.5 | Assign content library: VKS Kubernetes releases | Library assigned | Listed under namespace |

### 8.4 Deploy VKS Cluster

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.4.1 | Connect to Supervisor API (`kubectl vsphere login`) | Authenticated | Kubeconfig obtained |
| 8.4.2 | Switch to vks-workloads namespace | Namespace active | `kubectl get ns` |
| 8.4.3 | Apply VKS cluster manifest (Cluster v1beta1) | Cluster creation initiated | `kubectl get cluster` shows Provisioning |
| 8.4.4 | Wait for control plane nodes (3x) | Control plane ready | `kubectl get machines` shows 3 Running |
| 8.4.5 | Wait for worker nodes (3x) | Workers ready | `kubectl get machines` shows 6 Running |
| 8.4.6 | Obtain VKS cluster kubeconfig | Kubeconfig available | `kubectl get secret` |

#### VKS cluster manifest

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: vks-cluster-01
  namespace: vks-workloads
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["192.168.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  topology:
    class: tanzukubernetescluster
    version: # Latest available VKr
    controlPlane:
      replicas: 3
      metadata: {}
    workers:
      machineDeployments:
        - class: node-pool
          name: worker-pool
          replicas: 3
          metadata: {}
    variables:
      - name: vmClass
        value: best-effort-medium
      - name: storageClass
        value: vsan-default-storage-policy
```

### 8.4a Verify StorageClass and PersistentVolume Provisioning

The vSphere CSI driver is automatically installed when the Supervisor is enabled. Verify that the StorageClass is available and can provision PersistentVolumes from vSAN.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.4a.1 | Login to VKS cluster | Authenticated | `kubectl get nodes` shows 6 nodes |
| 8.4a.2 | Verify StorageClass exists | StorageClass listed | `kubectl get storageclass` shows `vsan-default-storage-policy` |
| 8.4a.3 | Create test PVC (1 Gi) | PVC bound | `kubectl get pvc` shows Bound |
| 8.4a.4 | Verify PV created on vSAN | FCD visible | vCenter → Datastores → vSAN → Monitor → Virtual Objects |
| 8.4a.5 | Delete test PVC | PVC and PV deleted | `kubectl get pv` shows no orphaned PVs |

```yaml
# Test PVC — apply, verify Bound, then delete
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: vsan-default-storage-policy
  resources:
    requests:
      storage: 1Gi
```

> **StorageClass parameters**: The `vsan-default-storage-policy` StorageClass uses `csi.vsphere.vmware.com` as the provisioner, `reclaimPolicy: Delete`, and `volumeBindingMode: WaitForFirstConsumer`. PVs are backed by vSAN First Class Disks (FCDs) with FTT=1 RAID-1 data protection. See [Logical Design](logical-design.md) Section 8 for full CSI/PV architecture.

### 8.5 Deploy Test Workload

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.1 | Login to VKS cluster using obtained kubeconfig | Authenticated | `kubectl get nodes` shows 6 nodes |
| 8.5.2 | Deploy nginx test deployment | Pods running | `kubectl get pods` shows Running |
| 8.5.3 | Expose via LoadBalancer service | External IP assigned | `kubectl get svc` shows EXTERNAL-IP |
| 8.5.4 | Access nginx from jumpbox | Page loads | `curl http://<EXTERNAL-IP>` returns nginx welcome |

#### Test workload manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-test
  template:
    metadata:
      labels:
        app: nginx-test
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-test
spec:
  type: LoadBalancer
  selector:
    app: nginx-test
  ports:
    - port: 80
      targetPort: 80
```

## 9. Ready for Operations Testing

Final verification checklist before the lab is considered operational.

### 9.1 Infrastructure Services

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 1 | External RDP access | RDP to jumpbox public IP | Desktop loads | ☐ |
| 2 | DNS forward resolution | `dig @10.0.10.1 vcenter-mgmt.lab.dreamfold.dev` | Returns 10.0.10.4 | ☐ |
| 3 | DNS reverse resolution | `dig @10.0.10.1 -x 10.0.10.4` | Returns vcenter-mgmt.lab.dreamfold.dev | ☐ |
| 4 | NTP synchronisation | `chronyc sources` on jumpbox | Upstream servers reachable | ☐ |
| 5 | CA health | `step ca health` on jumpbox | Returns "ok" | ☐ |
| 6 | Inter-VLAN routing | `ping 10.0.20.1` from an ESXi host | Success | ☐ |

### 9.2 VCF Platform

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 7 | Management vCenter | Browse `https://vcenter-mgmt.lab.dreamfold.dev` | Login page loads | ☐ |
| 8 | Workload vCenter | Browse `https://vcenter-wld.lab.dreamfold.dev` | Login page loads | ☐ |
| 9 | SDDC Manager | Browse `https://sddc-manager.lab.dreamfold.dev` | Both domains Active | ☐ |
| 10 | Management vSAN health | vCenter → Cluster → vSAN Health | All green | ☐ |
| 11 | Workload vSAN health | vCenter → Cluster → vSAN Health | All green | ☐ |
| 12 | All ESXi hosts connected | Both vCenters show hosts Connected | 4 mgmt + 3 wld | ☐ |

### 9.3 NSX Networking

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 13 | BGP adjacency | `vtysh -c 'show ip bgp summary'` on jumpbox | Established | ☐ |
| 14 | Route exchange | `vtysh -c 'show ip bgp'` on jumpbox | VPC prefixes received | ☐ |
| 15 | Edge cluster health | NSX Manager → Edge Clusters | Both Edges Up | ☐ |
| 16 | Tier-0 status | NSX Manager → Tier-0 Gateways | Realised | ☐ |
| 17 | VPC status | NSX Manager → VPC | Realised | ☐ |

### 9.4 VKS

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 18 | Supervisor status | vCenter → Workload Management | Running | ☐ |
| 19 | VKS cluster health | `kubectl get cluster vks-cluster-01` | Phase: Provisioned | ☐ |
| 20 | All nodes ready | `kubectl get nodes` on VKS cluster | 6 nodes Ready | ☐ |
| 21 | Test workload | `curl http://<nginx-lb-ip>` | nginx welcome page | ☐ |
| 22 | Pod-to-external | `kubectl exec` into pod, `curl google.com` | Response received | ☐ |
