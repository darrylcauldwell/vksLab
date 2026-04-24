---
title: "VKS Lab"
subtitle: "Delivery Guide"
author: "dreamfold"
date: "March 2026"
---

# Delivery Guide

## 1. Deployment Overview

The lab is built in two tiers. **Phase 0** is a one-time operation that creates a reusable vApp template containing 8 VMs (1 gateway + 7 ESXi). This template is stored in the vCD catalog where it is exempt from lease expiry, so it survives the 14-day runtime and 30-day storage leases. **Phases 1–8** run on each rebuild by deploying from that template — dramatically faster than building from scratch.

| Phase | Name | Frequency |
|-------|------|-----------|
| 0 | vApp Template | One-time |
| 1 | Foundation | Each rebuild |
| 2 | MAC Discovery | Each rebuild |
| 3 | Nested ESXi | Each rebuild |
| 4 | VCF Management Domain | Each rebuild |
| 5 | VCF Platform Services | Each rebuild |
| 6 | VCF Workload Domain | Each rebuild |
| 7 | VCF Workload NSX Networking | Each rebuild |
| 8 | VCF Workload VKS | Each rebuild |

**Phase 0** creates the baseline vApp with a gateway VM (Ubuntu, Open Virtual Appliance (OVA) pre-staged) and 7 ESXi VMs, then saves it as a catalog template. **Phase 1** deploys the template, configures the gateway (Domain Name System (DNS), Network Time Protocol (NTP), Certificate Authority (CA), inter-Virtual LAN (VLAN) routing, Free Range Routing (FRR) Border Gateway Protocol (BGP), Keycloak OIDC). **Phase 2** discovers ESXi MAC addresses and assigns static DHCP reservations. **Phase 3** configures all seven nested ESXi hosts. **Phase 4** runs the VMware Cloud Foundation (VCF) Installer to bring up the management domain (vCenter, Software-Defined Data Center (SDDC) Manager, VCF Networking (NSX) Manager). **Phase 5** deploys VCF Management Components (VCF Operations, Collector, Fleet Management), configures VCF Identity Broker OIDC with Keycloak, replaces self-signed certificates with step-ca issued certificates, and configures SDDC Manager backups. **Phase 6** commissions workload hosts and creates the workload domain. **Phase 7** deploys the NSX Edge cluster, configures NSX Tier-0 Gateway / NSX Tier-1 Gateway, establishes BGP peering, and creates the NSX Virtual Private Cloud (VPC). **Phase 8** enables the vSphere Supervisor, creates a vSphere Namespace, deploys a vSphere Kubernetes Services (VKS) cluster with a test workload, and installs platform services.

> **Execution model**: Phases 1–3 run from the operator's laptop targeting the gateway and ESXi hosts via SSH. Phases 4–8 run from localhost via SOCKS proxy (`ssh -D 1080 -N ubuntu@<gateway-ip>`), routing all VCF API calls through the gateway using the `vmware_vcf.ansible` collection modules. Each phase includes DNS quality gates that ensure and verify required DNS records on the gateway before proceeding. A single 1Password prompt per phase provides authentication credentials.

## 2. Prerequisites

> Before starting deployment, verify that all assumptions from [Conceptual Design](conceptual-design.md) Section 7 hold true.

The following must be in place before starting Phase 0.

| # | Prerequisite | Status |
|---|-------------|--------|
| 1 | vCD resources approved (170 vCPU, 906 GB RAM, 1.9 TB storage) | ☐ |
| 2 | Ubuntu ISO available in vCD Content Hub (`ubuntu-24.04.2-live-server-amd64.iso`), ESXi vApp template available (`[baked]esxi-9.0.2-2514807`) | ☐ |
| 3 | VCF Installer OVA (`VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova`, 2.03 GB) — download from support.broadcom.com to `~/Downloads/` on operator laptop (formerly Cloud Builder; consolidated into SDDC Manager appliance in VCF 9.0) | ☐ |
| 4 | RDP client installed on operator Mac — [Windows App](https://apps.apple.com/app/windows-app/id1295203466) from App Store | ☐ |
| 5 | VCF offline depot accessible: `curl -s https://depot.vcf-gcp.broadcom.net` returns a response | ☐ |
| 6 | Operator SSH key pair exists (`~/.ssh/id_ed25519.pub`), or generate one: `ssh-keygen -t ed25519` | ☐ |

### 2.1 1Password Secret Store

Ansible retrieves all lab credentials from 1Password at runtime (from the "Employee" vault). Install the CLI and create password items:

```bash
# Install 1Password CLI (macOS)
brew install --cask 1password-cli

# Enable CLI integration in 1Password desktop app:
#   Settings → Security → enable "Unlock using system authentication"
#   Settings → Developer → enable "Integrate with 1Password CLI"
# After this, op commands authenticate via Touch ID — no manual signin needed.

# Create 1Password items (first time only)
op item create --vault Employee --category login --title "Lab Bootstrap" \
  password='VMware1!VMware1!' username=ubuntu
op item create --vault Employee --category login --title "ESXi Root" \
  password='VMware1!VMware1!' username=root
op item create --vault Employee --category login --title "vCenter SSO" \
  password='VMware1!VMware1!' username='administrator@vsphere.local'
op item create --vault Employee --category login --title "SDDC Manager" \
  password='VMware1!VMware1!' username='admin@local'
op item create --vault Employee --category login --title "NSX Manager" \
  password='VMware1!VMware1!' username=admin
op item create --vault Employee --category login --title "Keycloak Admin" \
  password='VMware1!VMware1!' username=admin
op item create --vault Employee --category login --title "Offline Depot" \
  password='<depot-password>' username=depot_user

```

Verify: `op item list --vault Employee` shows all 7 items.

### 2.2 Ansible

Ansible runs from the operator's laptop (not the gateway) and connects to lab hosts via SSH ProxyJump through the gateway.

```bash
# Install sshpass (required for password-based SSH to ESXi hosts)
brew install hudochenkov/sshpass/sshpass

# Create and activate virtual environment (from repo root)
python3 -m venv .venv
source .venv/bin/activate

# Install Ansible and required collections
pip install ansible-core
ansible-galaxy collection install -r ansible/collections/requirements.yml
```

> **Note**: Activate the virtual environment (`source .venv/bin/activate`) and run all `ansible-playbook` commands from the `ansible/` directory (where `ansible.cfg` lives). The `.venv/` directory is already in `.gitignore`.

## 3. Phase 0 — vApp Template (One-Time)

> This phase is performed once to create a reusable baseline. The resulting catalog template persists indefinitely (no lease) and is used as the starting point for every rebuild. Allow **30–45 minutes** for the full phase, depending on SCP transfer speed.

### 3.1 Create vCD vApp (Manual)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1.1 | In vCloud Director, navigate to **Data Centers** > target VDC > **vApps** > **New vApp**. Name the vApp `vcf-lab` | An empty vApp is created in the target VDC |
| 3.1.2 | Add routed network (public) to vApp | External connectivity is available via the public network |
| 3.1.3 | Add isolated network: name `lab-trunk`, gateway CIDR `192.168.254.1/24`, tick **Allow Guest VLAN** | A trunk-capable internal network is available for VLAN traffic |

### 3.2 Deploy Gateway VM (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.2.1 | In the vApp, click **Add VM** > **New**. Select Ubuntu 24.04 ISO from Content Hub (2 vCPU, 10 GB RAM, 60 GB disk). Assign NIC1 to the Public network and NIC2 to `lab-trunk` | The gateway VM is created with the specified configuration | The VM is visible in the vApp inventory |
| 3.2.2 | Power on and complete Ubuntu installer via vCD console — set server name `gateway`, username `ubuntu`, set a simple temporary password (e.g. `VMware1!`). This password matches the "Lab Bootstrap" item created in §2.1 | Ubuntu 24.04 is installed on the gateway VM | A login prompt appears on the vCD console |
| 3.2.3 | Note public IP assigned by DHCP to NIC1 (ens33): `ip addr show ens33` | The public IP address is obtained | — |
| 3.2.4 | Store gateway IP in 1Password: `op item edit "Lab Bootstrap" ip_address=<gateway-ip>` | The gateway IP is stored in 1Password | `op item get "Lab Bootstrap" --fields ip_address` returns the IP |
| 3.2.5 | Copy SSH key to gateway: `ssh-copy-id ubuntu@<gateway-ip>` | The SSH public key is deployed to the gateway | `ssh ubuntu@<gateway-ip>` connects without a password prompt |

### 3.3 Pre-install Gateway Packages (Automated)

Pre-installing packages in the template avoids ~10–15 minutes of apt installs on every rebuild. The Ansible `gateway` role is idempotent — on subsequent rebuilds (Phase 1) it no-ops when packages are already present.

```bash
source .venv/bin/activate
cd ansible
ansible-playbook playbooks/phase1_foundation.yml --tags packages
```

> **Verification**: `dpkg -l | grep -c '^ii'` on the gateway shows a significantly higher package count than a base Ubuntu install.

### 3.4 Stage VCF Installer OVA on Gateway (Automated)

Download `VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova` (2.03 GB) from support.broadcom.com and place it in `~/Downloads/` on the operator laptop. The `phase0_operator.yml` playbook uploads it to the gateway:

```bash
ansible-playbook playbooks/phase0_operator.yml --tags ova
```

> **Verification**: `ssh ubuntu@<gateway-ip> 'ls -lh ~/vcf-installer.ova'` shows 2.03 GB.

### 3.5 Deploy and Prepare ESXi VMs (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.5.1 | In the vApp, click **Add VM** > **From Template**. Select `[baked]esxi-9.0.2-2514807` from the catalog. Create esxi-01 through esxi-07 (24 vCPU, 128 GB RAM, 64 GB boot Non-Volatile Memory Express (NVMe) + 256 GB local NVMe + 2,048 GB vSAN NVMe). Each ESXi VM has a single vNIC — assign it to `lab-trunk`. If the template was created with two vNICs, remove the second one before saving the template | All 7 ESXi VMs are cloning from the template | The vApp shows 7 ESXi VMs plus the gateway, each with a single NIC attached to `lab-trunk` |
| 3.5.2 | Power on all 7 ESXi VMs (allow 5–10 minutes for POST) | All ESXi VMs are running | Each VM shows the Direct Console User Interface (DCUI) |
| 3.5.3 | For each ESXi VM (esxi-01 through esxi-07), open the VM console in vCD. Press **F2** > **Reset System Configuration** > **F11** to confirm. Wait for the host to reboot (1–2 minutes per host) | Each host reboots with a clean configuration | The DCUI shows a management IP in the DHCP dynamic range |
| 3.5.4 | On each host via DCUI: press **F2** > **Configure Management Network** > **VLAN (optional)** > enter **10** > **Enter** > **Esc** > **Y** to apply and restart the management network | Management traffic is tagged with VLAN 10 | The DCUI shows the management IP after the network restart |
| 3.5.5 | On each host via DCUI: press **F2** > **Troubleshooting Options** > **Enable SSH** > **Enter**, then **Enable ESXi Shell** > **Enter** | SSH and ESXi Shell are enabled on all hosts | The DCUI shows SSH and Shell as enabled |

### 3.6 Power Off and Save to Catalog

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.6.1 | On the gateway VM, select **Actions** > **Media** > **Eject Media** to unmount the Ubuntu install ISO | The install ISO is ejected | No media is attached to the gateway VM |
| 3.6.2 | Power off all 8 VMs (gateway + 7 ESXi) | All 8 VMs are stopped | The vApp shows all VMs powered off |
| 3.6.3 | In vCD, right-click vApp → **Add to Catalog**. Select **Make identical copy**. Name: `[baseline]vcf-9.0.2-lab-8vm`, description: "VCF 9.0.2 nested lab baseline — 1 Ubuntu 24.04 gateway (packages + OVA pre-staged) + 7 ESXi 9.0.2 hosts (4 mgmt, 3 workload)", storage policy: `ProvisioningStoragePolicy-provider01` | The vApp template is created in the catalog | The catalog shows the new template |
| 3.6.4 | Verify template is visible in catalog and contains 8 VMs | The template is valid and contains all expected VMs | Opening template details confirms 8 VMs are listed |

> **Note**: The original vApp can be deleted after the template is saved — it is no longer needed. All subsequent rebuilds deploy from the catalog template.

## 4. Phase 1 — Foundation

> Phase 1 implements R-001, R-002, R-003, R-009 via VCD-01, VCD-02, NET-01, NET-05, SVC-01 through SVC-08.

### 4.1 Deploy vApp from Template (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 4.1.1 | In vCD catalog, deploy vApp from template `[baseline]vcf-9.0.2-lab-8vm` | A vApp is created containing all 8 VMs | The vApp is visible with all VMs listed |
| 4.1.2 | Power on all 8 VMs (allow 5–10 minutes for all VMs to complete POST) | All 8 VMs are running | The gateway obtains a public IP via Dynamic Host Configuration Protocol (DHCP) |
| 4.1.3 | Note gateway public IP: `ip addr show ens33` via vCD console | The public IP address is obtained | — |
| 4.1.4 | Store gateway IP in 1Password: `op item edit "Lab Bootstrap" ip_address=<gateway-ip>` | The gateway IP is stored in 1Password | `op item get "Lab Bootstrap" --fields ip_address` returns the IP |
| 4.1.5 | Copy SSH key to gateway: `ssh-copy-id ubuntu@<gateway-ip>` | The SSH public key is deployed to the gateway | `ssh ubuntu@<gateway-ip>` connects without a password prompt |

> **Note**: vCD assigns new MAC addresses each time a vApp is deployed from a template. MAC discovery is automated in §4.3 — no manual lookup is required. ESXi hosts do not need a DCUI reset on rebuild — the template was saved after Reset System Configuration (§3.5.3) with VLAN 10 on the management port group (§3.5.4) and SSH/Shell already enabled (§3.5.5).

### 4.2 Configure Gateway (Automated)

All gateway configuration (VLAN sub-interfaces, dnsmasq DNS/DHCP, chrony NTP, step-ca, GNOME/gnome-remote-desktop, IP masquerading, FRR BGP, Firefox, Ansible, 1Password CLI, Keycloak) is automated by the `gateway` and `docker_services` Ansible roles. The playbook takes approximately **10–15 minutes** to complete:

```bash
source .venv/bin/activate
cd ansible
ansible-playbook playbooks/phase1_foundation.yml
```

Phase 1 also prepares the gateway as the Ansible control node for all subsequent phases. It installs Ansible, 1Password CLI, clones the lab repo to `~/dda-vcf`, and installs required Ansible collections. After Phase 1 completes, SSH to the gateway and run all subsequent playbooks locally:

```bash
ssh ubuntu@<gateway-ip>
cd ~/dda-vcf/ansible
op signin    # authenticate 1Password CLI
ansible-playbook -i inventory/hosts-gateway.yml playbooks/phase3_esxi.yml
```

> **Note**: The gateway-local inventory (`hosts-gateway.yml`) eliminates SSH ProxyJump — the gateway connects directly to ESXi hosts on the management VLAN. This is faster and more reliable than running from the laptop over the internet. To pull latest changes before running: `cd ~/dda-vcf && git pull`.

### 4.3 Phase 2 — Discover ESXi MACs (Automated)

After the gateway is configured (§4.2), the 7 ESXi VMs will have obtained dynamic DHCP addresses in the `.100–.199` range. The `phase2_discover_macs.yml` playbook reads these leases, maps each MAC to a static reservation (esxi-01 through esxi-07), writes the reservations into the dnsmasq config, and restarts dnsmasq so the hosts pick up their static IPs (`.11–.17`).

```bash
cd ansible
ansible-playbook playbooks/phase2_discover_macs.yml
```

The playbook:

1. Reads `/var/lib/misc/dnsmasq.leases` on the gateway
2. Extracts MAC addresses from leases in the dynamic range (`.100–.199`)
3. Asserts that at least 7 MACs are present (trims to 7 most recent if more are found)
4. Writes `dhcp-host` reservations to `/etc/dnsmasq.d/lab.conf` via `blockinfile`
5. Restarts dnsmasq to apply the static reservations
6. Waits for all 7 hosts to be reachable on port 443 (ESXi management) on their static IPs

> **Note**: The order in which MACs are assigned to hosts is arbitrary — all ESXi VMs are identical spec ("cattle not pets"), so any MAC-to-host mapping is valid. The first 4 MACs are assigned to management hosts (esxi-01 through esxi-04), the remaining 3 to workload hosts (esxi-05 through esxi-07).

The playbook is idempotent: if reservations already exist and hosts are reachable on their static IPs, it skips discovery and verifies connectivity only. On rebuild, the playbook clears stale reservations and re-discovers MACs from fresh DHCP leases (vCD assigns new MACs on each deploy from template).

### 4.4 Foundation Verification

The `phase1_foundation.yml` playbook runs automated verification checks at the end of the play. All checks below except RDP are validated automatically — the playbook will fail with a clear message if any check does not pass.

| Check | Automated | Expected Result |
|-------|-----------|-----------------|
| Gateway external access | **Manual** — RDP to gateway public IP | The GNOME desktop is accessible via RDP |
| Gateway DNS | Yes | Forward lookup of `gateway.lab.dreamfold.dev` returns the gateway IP |
| Gateway NTP | Yes | Chrony shows a synchronised upstream source |
| Gateway CA | Yes | `step ca health` returns "ok" |
| VLAN sub-interfaces | Yes | All 6 VLAN sub-interfaces have their expected CIDRs (including management on ens34.10) |
| Inter-VLAN routing | Yes | Ping to vMotion gateway succeeds |
| FRR service | Yes | FRR is active |
| FRR BGP config | Yes | `router bgp 65000` block is present (BGP adjacency establishes in Phase 7 when the NSX Tier-0 is configured) |

## 5. Phase 3 — Nested ESXi

> Phase 3 implements R-004, R-007 via ESX-01 through ESX-04 and NET-03, NET-04.

### 5.1 Prepare Hosts (Automated)

The playbook first bootstraps the root password on each host. After Reset System Configuration (Phase 0 §3.5.3), the root password is blank — the bootstrap play connects with a blank password and sets it to the 1Password "Lab Bootstrap" credential. On re-runs where the password is already set, this step is skipped automatically.

The `esxi_prepare` role then configures all hosts — hostname, DNS, NTP, root password (upgraded to the runtime credential from 1Password "ESXi Root"), and vSAN Express Storage Architecture (ESA) preparation. The playbook takes approximately **5–10 minutes** to complete:

```bash
cd ansible
ansible-playbook playbooks/phase3_esxi.yml
# Or prepare a single host
ansible-playbook playbooks/phase3_esxi.yml --ask-become-pass --limit esxi-01
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

> **Note**: VCF 9.0.1+ includes a built-in vSAN ESA Hardware Compatibility List (HCL) bypass for nested environments. The mock HCL vSphere Installation Bundle (VIB), used in earlier VCF versions, is no longer required.

### 5.3 ESXi Host Verification

The Phase 3 playbook (`phase3_esxi.yml`) includes built-in validation tasks that verify gateway connectivity, DNS server reachability, SSL certificate CN matching, and system UUID uniqueness. Successful completion of the playbook confirms that all ESXi hosts are correctly configured for VCF bringup — no additional manual verification is required.

To re-validate after changes, run the playbook in check mode:

```bash
cd ansible && ansible-playbook playbooks/phase3_esxi.yml --limit esxi --check
```

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| All hosts reachable | `ping 10.0.10.{11..17}` from gateway | All seven hosts respond to ping |
| DNS resolution | `nslookup esxi-01.lab.dreamfold.dev 10.0.10.1` | The query returns the correct IP for each host |
| Reverse DNS | `nslookup 10.0.10.11 10.0.10.1` | The query returns esxi-01.lab.dreamfold.dev |
| NTP sync | `esxcli system ntp get` on each host | NTP is configured with server 10.0.10.1 |
| Time sync | Compare time across all hosts | Time across all hosts is within 1 second |
| vSAN ESA ready | `esxcli vsan storage list` on each host | The NVMe device is marked as SSD |
| Host status | `cd ansible && ansible-playbook playbooks/phase3_esxi.yml --check` | All tasks report ok with no changes required |

## 6. Phase 4 — VCF Management Domain

> Phase 4 implements R-004 via VCF-01, VCF-03, VCF-04. VCF Installer drives initial bringup of vCenter, SDDC Manager, and NSX Manager.

### 6.1 Pre-Bringup DNS Records

DNS records for all VCF appliances are statically configured in the dnsmasq template deployed by the Phase 1 playbook (`phase1_foundation.yml`). Successful completion of Phase 1 — including the DNS forward-lookup verification task — confirms that all required records are in place. The records are defined in `ansible/roles/gateway/defaults/main.yml` under `gateway_dns_records` and include:

| Hostname | IP | Purpose |
|----------|-----|---------|
| vcf-installer.lab.dreamfold.dev | 10.0.10.3 | VCF Installer |
| vcenter-mgmt.lab.dreamfold.dev | 10.0.10.4 | Management vCenter |
| sddc-manager.lab.dreamfold.dev | 10.0.10.5 | SDDC Manager |
| nsx-mgr-mgmt.lab.dreamfold.dev | 10.0.10.6 | Management NSX Manager |

### 6.2 Deploy VCF Installer

In VCF 9.0, the SDDC Manager appliance doubles as the VCF Installer (Cloud Builder functionality is consolidated into it). The OVA was pre-staged on the gateway in Phase 0 (`~/vcf-installer.ova`).

The Phase 4 playbook (`phase4_vcf_mgmt.yml`) has two plays: the first deploys the VCF Installer, and the second (§6.3) drives the bringup workflow. Run the full playbook:

```bash
cd ansible && ansible-playbook playbooks/phase4_vcf_mgmt.yml
```

The first play deploys the VCF Installer OVA to esxi-01 with the correct network properties, powers it on, and waits for the installer services to become accessible. The deployment is idempotent — if the VM already exists, it skips straight to the service readiness check.

| Step | Automated Action | Expected Result |
|------|-----------------|-----------------|
| 6.2.1 | `govc import.spec` extracts OVF properties from the OVA | Deployment spec generated with network config |
| 6.2.2 | `govc import.ova` deploys to esxi-01 with IP `10.0.10.3`, subnet `255.255.255.0`, gateway `10.0.10.1`, DNS `10.0.10.1` | VCF Installer VM deployed and powered on |
| 6.2.3 | Playbook polls `https://vcf-installer.lab.dreamfold.dev` until accessible (up to 10 minutes) | All installer services are ready |

### 6.2.1 Download VCF Installer Bundles (Manual)

The VCF Installer requires software bundles downloaded from the offline depot before bringup can proceed. This is a manual step via the VCF Installer UI.

1. Open an SSH SOCKS tunnel from the operator laptop (runs in the foreground — leave the terminal open):

   ```bash
   ssh -D 1080 -N ubuntu@<gateway-public-ip>
   ```

2. Configure Firefox to proxy through the tunnel:
   - Open **Settings** > **General** > scroll to **Network Settings** > click **Settings...**
   - Select **Manual proxy configuration**
   - Set **SOCKS Host**: `localhost`, **Port**: `1080`
   - Select **SOCKS v5**
   - Tick **Proxy DNS when using SOCKS v5** (required — lab DNS names must resolve via the gateway)
   - Click **OK**

3. Browse to `https://vcf-installer.lab.dreamfold.dev` and accept the self-signed certificate warning. Log in with username `admin@local` and the password from 1Password "SDDC Manager" item.

4. Navigate to **Binary Management** > **Downloads**

5. Filter by version **9.0.2.0** (matches the installed VCF Installer version) — this reduces the list to 7 product bundles (~56 GB total)

6. Select all 7 bundles and click **Download**

7. Wait for all downloads to complete before proceeding to bringup. Downloads run on the VCF Installer VM — the SOCKS tunnel and browser can be closed while downloads continue.

> **Verification**: All 7 bundles show download status "Completed" in the UI.

> **Note**: Remember to revert Firefox proxy settings after this step (Settings > Network Settings > **No proxy**), otherwise normal browsing will fail when the SOCKS tunnel is closed.

### 6.2.2 Apply Nested vSAN ESA Workarounds (Manual)

Nested ESXi hosts use virtual NVMe disks that are not on the vSAN Hardware Compatibility List (HCL). VMware Cloud Foundation (VCF) 9.0.1+ includes a built-in bypass via a domainmanager property. The vSAN HCL timestamp must also be current (< 90 days old).

The bypass is documented in [Broadcom KB 408300](https://knowledge.broadcom.com/external/article/408300), which also explains why the property must be set in both `application-prod.properties` and `application.properties` for the change to take effect.

SSH to the VCF Installer and switch to root (the `vcf` user does not have sudo privileges — use `su -` with the root password from 1Password "SDDC Manager" item):

```bash
ssh vcf@vcf-installer.lab.dreamfold.dev
su -

# 1. Enable vSAN ESA HCL bypass in both properties files (idempotent)
grep -q 'vsan.esa.sddc.managed.disk.claim=true' \
  /etc/vmware/vcf/domainmanager/application-prod.properties || \
  echo 'vsan.esa.sddc.managed.disk.claim=true' >> \
  /etc/vmware/vcf/domainmanager/application-prod.properties

grep -q 'vsan.esa.sddc.managed.disk.claim=true' \
  /etc/vmware/vcf/domainmanager/application.properties || \
  echo 'vsan.esa.sddc.managed.disk.claim=true' >> \
  /etc/vmware/vcf/domainmanager/application.properties

# 2. Restart domainmanager to pick up the property change
systemctl restart domainmanager

# 3. Wait for domainmanager to be ready (~30 seconds)
sleep 30 && systemctl is-active domainmanager

# 4. Patch vSAN HCL timestamp (prevents 90-day staleness check)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sed -i "s/\"timestamp\":\"[^\"]*\"/\"timestamp\":\"$NOW\"/" \
  /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json
sed -i "s/\"jsonUpdatedTime\":\"[^\"]*\"/\"jsonUpdatedTime\":\"$NOW\"/" \
  /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json

exit
```

> **Verification**: `grep vsan.esa.sddc.managed.disk.claim /etc/vmware/vcf/domainmanager/application-prod.properties` returns `true`. `systemctl is-active domainmanager` returns `active`.

#### VCF Deployment Parameter Workbook

The bringup spec is defined as a YAML dict in `ansible/roles/vcf_bringup/defaults/main.yml`. All IPs are derived from `lab_network_prefix` and credentials are injected from 1Password at runtime — no manual JSON editing required. The Ansible `vcf_bringup` role validates and submits the spec to the VCF Installer API.

No licence keys are required at bringup — VCF 9.0 "License Later" mode provides a 90-day grace period. Licences are applied via SDDC Manager after bringup.

#### Troubleshooting: vSAN HCL Timestamp Validation

The VCF Installer validates that its embedded vSAN HCL file (`all.json`) is less than 90 days old. If the installer OVA was built more than 90 days ago, bringup fails with an HCL validation error. See [Broadcom KB 412606](https://knowledge.broadcom.com/external/article/412606/vcf-9-installer-fails-to-deploy-during-t.html) for the authoritative resolution.

The fix is to replace `all.json` with a fresh download. The lab gateway is airgapped, so download on the operator laptop first and SCP through the gateway:

```bash
# On operator laptop — download fresh HCL database
curl -o ~/Downloads/all.json https://vvs.broadcom.com/service/vsan/all.json

# SCP to gateway, then to VCF Installer
scp ~/Downloads/all.json gateway.lab.dreamfold.dev:/tmp/all.json
ssh gateway.lab.dreamfold.dev \
  "scp /tmp/all.json vcf@vcf-installer.lab.dreamfold.dev:/nfs/vmware/vcf/nfs-mount/all.json"

# On the VCF Installer — move to HCL directory and fix ownership
ssh vcf@vcf-installer.lab.dreamfold.dev
su -
mv /nfs/vmware/vcf/nfs-mount/all.json /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json
chown vcf_lcm:vcf /nfs/vmware/vcf/nfs-mount/vsan-hcl/all.json
```

Then select **Re-run Validations** in the VCF Installer UI.

### 6.3 Run VCF Bringup

> The bringup workflow takes approximately **2–3 hours** to complete end-to-end. Run `caffeinate -d` in a separate terminal to prevent the operator laptop from sleeping during this process.

The second play of the Phase 4 playbook (`phase4_vcf_mgmt.yml`) drives bringup end-to-end via the `vcf_bringup` role. It configures the offline depot, validates the bringup spec against the VCF Installer API, then submits the deployment and polls until completion. If the VCF Installer was already deployed in a previous run, restart the playbook from the bringup tasks:

```bash
cd ansible && ansible-playbook playbooks/phase4_vcf_mgmt.yml --start-at-task="Get VCF Installer API token"
```

| Step | Automated Action | Expected Result | Verification |
|------|-----------------|-----------------|--------------|
| 6.3.1 | Configure offline depot credentials via VCF Installer API | Depot configured successfully | — |
| 6.3.2 | Validate bringup spec via `POST /v1/sddcs/validations` | Validation completes with status SUCCEEDED or WARNING | Warnings for vSAN ESA HCL are expected in nested environments |
| 6.3.3 | Submit bringup via `POST /v1/sddcs` | Bringup deployment begins | — |
| 6.3.4 | Poll deployment status (up to 2 hours) — vCenter deployment | vCenter Server deployed | `https://vcenter-mgmt.lab.dreamfold.dev` is accessible |
| 6.3.5 | Poll deployment status — VDS and vSAN configuration | Networking and storage configured | vSAN health shows green in vCenter |
| 6.3.6 | Poll deployment status — SDDC Manager deployment | SDDC Manager deployed | `https://sddc-manager.lab.dreamfold.dev` is accessible |
| 6.3.7 | Poll deployment status — NSX Manager deployment | NSX Manager deployed | `https://nsx-mgr-mgmt.lab.dreamfold.dev` is accessible |
| 6.3.8 | Bringup completes, playbook verifies all management endpoints | Management domain is operational | SDDC Manager shows the management domain as healthy |

### 6.4 Post-Bringup Tasks

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.4.1 | Start downloading VCF Operations bundles from SDDC Manager UI (**Lifecycle Management** > **Bundle Management**) — VROPS, VRSLCM, VCF_OPS_CLOUD_PROXY for current VCF version. This is optional but saves time — Phase 5 automation will trigger downloads if not done manually (see §7.4) | Bundles are downloading or downloaded | Bundle status shows SUCCESS |
| 6.4.2 | Remove VCF Installer VM from vCenter (manual — no SDDC Manager API for this). Right-click VM > Power Off, then Delete from Disk | Resources (4 vCPU, 24 GB RAM) are reclaimed from the management cluster | The VM is deleted from the inventory |

> **Note**: VCF Operations, Collector, and Fleet Management are deployed automatically in Phase 5 (§7.4) via the SDDC Manager API. VCF Automation is optional.

### 6.5 Management Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| vCenter health | Login to `https://vcenter-mgmt.lab.dreamfold.dev` | The cluster shows 4 hosts, all in a connected state |
| vSAN health | vCenter → Cluster → Monitor → vSAN → Health | All vSAN health checks are green |
| SDDC Manager | Login to `https://sddc-manager.lab.dreamfold.dev` | The management domain shows Active status |
| NSX Manager | Login to `https://nsx-mgr-mgmt.lab.dreamfold.dev` | The dashboard is accessible and all transport nodes are connected |

## 7. Phase 6 — VCF Workload Domain

> Phase 6 implements R-004 via VCF-01, VCF-02. Workload hosts are commissioned into the free pool and a VI workload domain is created.

### 7.0 Prerequisites — vSAN ESA SDDC Manager Host Commissioning Bypass (VCF 9.0.1+)

**For nested lab environments**, SDDC Manager host validation will fail with "Host does not have enough capacity disks" because real hardware checks reject lab storage configurations. This workaround is required before commissioning workload hosts.

> **Note**: SSH banner automation with `sshpass` is unreliable (SSH welcome message interferes with command execution). This must be applied manually, similar to the VCF Installer vSAN HCL workaround in Phase 4.

**Manual step** (run ONCE before first Phase 6 execution):

SSH to SDDC Manager as root and append properties to **both** operationsmanager and domainmanager:

```bash
# SSH to SDDC Manager
ssh root@sddc-manager.lab.dreamfold.dev

# Add vSAN ESA disk claim bypass to operationsmanager
echo "vsan.esa.sddc.managed.disk.claim=true" >> /etc/vmware/vcf/operationsmanager/application-prod.properties

# Add vSAN ESA disk claim bypass to domainmanager
echo "vsan.esa.sddc.managed.disk.claim=true" >> /etc/vmware/vcf/domainmanager/application-prod.properties

# Add NIC speed validation bypass (for lab hardware <10GbE)
echo "enable.speed.of.physical.nics.validation=false" >> /etc/vmware/vcf/operationsmanager/application.properties

# Restart all VCF services using the proper restart script
/opt/vmware/vcf/operationsmanager/scripts/cli/sddcmanager_restart_services.sh

# Wait for services to stabilize
sleep 60

# Verify services are running
systemctl status operationsmanager
systemctl status domainmanager
```

**Verify** the properties were written to both files:

```bash
grep "vsan.esa.sddc.managed.disk.claim" /etc/vmware/vcf/operationsmanager/application-prod.properties
grep "vsan.esa.sddc.managed.disk.claim" /etc/vmware/vcf/domainmanager/application-prod.properties
grep "enable.speed.of.physical.nics.validation" /etc/vmware/vcf/operationsmanager/application.properties
```

**Reference**: 
- William Lam — [Enhancement in VCF 9.0.1 to bypass vSAN ESA HCL & Host Commission 10GbE NIC Check](https://williamlam.com/2025/09/enhancement-in-vcf-9-0-1-to-bypass-vsan-esa-hcl-host-commission-10gbe-nic-check.html)
- Broadcom KB 408300 — vSAN ESA nested lab workarounds

### 7.1 Automate Host Commissioning and Domain Creation

Once the vSAN ESA workaround (Section 7.0) has been applied to SDDC Manager, run the Phase 6 Ansible playbook from the operator laptop:

```bash
cd ansible/
ansible-playbook playbooks/phase6_vcf_workload.yml
```

**What the playbook does:**
- Looks up the management network pool ID (`mgmt-network-pool`) via SDDC Manager API
- Commissions workload hosts `esxi-05`, `esxi-06`, `esxi-07` to the free pool
- Validates the workload domain specification
- Creates the workload domain with vSAN ESA enabled, 3-node cluster
- Waits for vCenter and NSX Manager to be accessible

**Progress monitoring:**
- The playbook displays polling progress every time the task status changes
- Monitor real-time progress in SDDC Manager **Inventory** > **Tasks** if desired
- Expected time: 20–40 minutes for host commissioning + 60–90 minutes for domain creation (total ~100 minutes)

**If the playbook fails:**
- Check the error message in the console output — it will include the actual SDDC Manager error response
- Verify the vSAN ESA workaround properties are present (Section 7.0)
- Verify SDDC Manager is operational (`systemctl status operationsmanager` on the SDDC Manager VM)
- Retry: `ansible-playbook playbooks/phase6_vcf_workload.yml`

### 7.2 Workload Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Workload vCenter | Login to `https://vcenter-wld.lab.dreamfold.dev` | The cluster shows 3 hosts, all in a connected state |
| Workload vSAN | vCenter → Cluster → Monitor → vSAN → Health | All vSAN health checks are green |
| Workload NSX | Login to `https://nsx-mgr-wld.lab.dreamfold.dev` | The NSX Manager dashboard is accessible |
| Transport nodes | NSX Manager → System → Fabric → Nodes | Three host transport nodes are configured and connected |
| SDDC Manager | Domains overview | Both management and workload domains show Active status |

### 7.3 Keycloak OIDC and VCF Identity Broker

Keycloak OIDC integration is automated in Phase 5 (`phase5_vcf_platform.yml`). Phase 1 creates the Keycloak realm, groups (`vcf-admins`, `vcf-operators`), users (`lab-admin`, `lab-operator`), and the `vcf-identity-broker` OIDC client with group membership mapper. Phase 5 deploys VCF Operations (required prerequisite) then configures the Identity Broker via VCF Operations internal APIs.

> **Note**: The OIDC configuration uses VCF Operations internal `/suite-api/internal/vidb/` APIs based on [William Lam's automation](https://williamlam.com/2026/04/automating-vcf-9-0-single-sign-on-sso-with-oidc-based-identity-provider.html). These are unsupported APIs that may change between VCF versions.

**Verification:**

| Check | Method | Expected Result |
|-------|--------|-----------------|
| SSO login (vCenter) | Browse to `https://vcenter-mgmt.lab.dreamfold.dev` and select Keycloak login | The vCenter dashboard loads after SSO login |
| SSO login (NSX) | Browse to `https://nsx-mgr-wld.lab.dreamfold.dev` and select Keycloak login | The NSX Manager dashboard loads after SSO login |
| Identity Broker | In VCF Operations, check Identity Broker federation status | All VCF components are federated |

## 7.4 Phase 5 — VCF Platform Services

> Phase 5 deploys VCF Management Components, configures the Identity Broker, replaces certificates, and sets up backups. Run after Phase 4.

**Prerequisites**: SOCKS tunnel running (`ssh -D 1080 -N ubuntu@<gateway-ip>`), VCF Operations bundles downloaded (automated safety net if not done manually).

```bash
ansible-playbook playbooks/phase5_vcf_platform.yml
```

The playbook runs three roles in order:

1. **vcf_mgmt_components** — Ensures DNS records (including VCF Operations for Logs and Networks), downloads required bundles (VROPS, VRSLCM, VCF_OPS_CLOUD_PROXY), deploys VCF Operations (xsmall), Collector (small), and Fleet Management via SDDC Manager API. Takes ~30–60 minutes. VCF Operations for Logs and VCF Operations for Networks are deployed separately via Fleet Management UI after automation completes.
2. **vcf_identity** — Configures VCF Identity Broker with Keycloak OIDC via VCF Operations internal APIs. Registers `vcf-identity-broker` client, maps `vcf-admins` group to administrator role, configures SSO for vCenter, NSX, and VCF Operations.
3. **vcf_platform** — Configures OpenSSL CA in SDDC Manager, generates CSRs for all domains, signs them with step-ca on the gateway, installs signed certificates. Configures SDDC Manager backups to gateway via SFTP.

> **Bundle download best practice**: Start downloading VCF Operations bundles via SDDC Manager UI immediately after Phase 4 bringup completes. The bundles are large and take time. Phase 5 automation includes a safety net that triggers downloads if not done manually, but this adds 30+ minutes of waiting.

| Verification | Method | Expected Result |
|--------------|--------|-----------------|
| VCF Operations accessible | Browse to `https://vcf-ops.lab.dreamfold.dev` | Dashboard loads |
| SSO working | Login to vCenter via Keycloak | SSO login succeeds |
| Backup configured | SDDC Manager → Backup Configuration | Shows SFTP target on gateway |

## 8. Phase 7 — VCF Workload NSX Networking

> Phase 7 implements R-006, R-008 via NET-02, NSX-01 through NSX-04. Edge cluster, gateways, BGP, and VPC are configured.

### 8.1 Deploy NSX Edge Cluster

#### Prerequisites for Nested Edge Deployment

**PDPE1GB CPU flag**: NSX Edge VMs require 1GB hugepages. In nested environments, this CPU instruction may not be exposed to the nested ESXi host. If Edge deployment fails, add this VM Advanced Setting on each nested ESXi host VM (in vCD):

```
featMask.vm.cpuid.PDPE1GB = Val:1
```

For AMD Ryzen/Threadripper physical hosts, also add: `monitor_control.enable_fullcpuid = "TRUE"`.

**NSX Edge OVF certificate expiry**: NSX Edge OVF certificates can expire, causing deployment failure with `VALIDATION_ERROR: CERTIFICATE_EXPIRED`. If you encounter this error, follow VMware KB 424034 to replace the expired OVF certificate before retrying Edge deployment.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.1.1 | In workload NSX Manager, navigate to **System** > **Fabric** > **Nodes** > **Edge Transport Nodes** > **Add Edge VM** | The Edge management page is displayed | — |
| 8.1.2 | Deploy edge-01: form factor **Large** (8 vCPU, 32 GB RAM), management IP `10.0.10.20`, host placement on workload cluster, datastore `workload-vsan-ds` | The edge-01 VM is deployed and powered on | `ping 10.0.10.20` succeeds |
| 8.1.3 | Deploy edge-02: form factor **Large**, management IP `10.0.10.21`, same host/datastore placement | The edge-02 VM is deployed and powered on | `ping 10.0.10.21` succeeds |
| 8.1.4 | Configure Edge TEP interfaces: edge-01 TEP IP `10.0.50.20`, edge-02 TEP IP `10.0.50.21`, both on VLAN 50 | TEP connectivity is established between the Edge nodes | The Edge transport node status shows Up |
| 8.1.5 | Navigate to **System** > **Fabric** > **Edge Clusters** > **Add Edge Cluster**. Name: `edge-cluster-01`, add both edge-01 and edge-02 | The Edge cluster is created with both Edge VMs | NSX Manager shows the Edge cluster as healthy |

### 8.2 Configure Tier-0 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.2.1 | Navigate to **Networking** > **Tier-0 Gateways** > **Add Tier-0 Gateway**. Name: `tier0-gateway`, HA mode: Active-Standby, linked to `edge-cluster-01` | The NSX Tier-0 Gateway is created | The gateway status shows Realised in NSX Manager |
| 8.2.2 | On the Tier-0, add an uplink interface: IP `10.0.60.2/24`, connected segment on VLAN 60 | The uplink interface is configured | The interface status shows Up |
| 8.2.3 | On the Tier-0, open the **BGP** tab. Set local ASN `65001`, add neighbor `10.0.60.1` with remote ASN `65000`, keepalive `60`, hold time `180` | BGP peering is configured on the Tier-0 Gateway | — |
| 8.2.4 | Enable route redistribution (connected subnets, NAT) | Connected and NAT routes are advertised | — |

### 8.3 Configure BGP on Gateway (FRR)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.3.1 | SSH to gateway | CLI access to the gateway is established | — |
| 8.3.2 | Verify FRR BGP configuration deployed by Ansible | The FRR BGP configuration is in place | `sudo vtysh -c 'show ip bgp summary'` shows the configuration |
| 8.3.3 | Verify BGP adjacency established | The BGP session state is Established | `sudo vtysh -c 'show ip bgp summary'` shows Established |
| 8.3.4 | Verify route exchange | Routes are received from the NSX Tier-0 Gateway | `sudo vtysh -c 'show ip bgp'` shows VPC prefixes |

#### Gateway FRR BGP configuration

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

### 8.4 Configure Tier-1 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.4.1 | Navigate to **Networking** > **Tier-1 Gateways** > **Add Tier-1 Gateway**. Name: `tier1-gateway`, linked to `tier0-gateway` | The NSX Tier-1 Gateway is created and linked to the Tier-0 | The gateway status shows Realised in NSX Manager |
| 8.4.2 | Configure route advertisement (connected subnets, NAT IPs, LB VIPs) | Route advertisements are enabled | — |

### 8.5 Configure NSX VPC

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.1 | Navigate to **Networking** > **VPC** > **Projects** > **Add Project**. Name: `vks-project` | The VPC project is created in NSX Manager | — |
| 8.5.2 | Within the project, create a VPC named `vks-vpc` with connectivity mode **Centralised** | The VPC is created with centralised connectivity | The VPC status shows Realised |
| 8.5.3 | Configure external connectivity via Tier-0 | External routing is configured via the Tier-0 Gateway | — |
| 8.5.4 | Configure Source Network Address Translation (SNAT) on Tier-0 for outbound VPC traffic | The SNAT rules are active | See SNAT steps below |

#### Configure SNAT Rules on Tier-0

Two SNAT rules are required — one for the VKS pod CIDR and one for the service CIDR. Both translate outbound traffic to the Tier-0 uplink IP (10.0.60.2) so that external networks can route return traffic.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.4a | In NSX Manager, navigate to Networking → NAT → tier0-gateway | The NAT rules page is displayed for the Tier-0 Gateway | — |
| 8.5.4b | Add SNAT rule: source 192.168.0.0/16 → translated IP 10.0.60.2 | The SNAT rule for the pod CIDR is created | The rule status shows Active |
| 8.5.4c | Add SNAT rule: source 10.96.0.0/12 → translated IP 10.0.60.2 | The SNAT rule for the service CIDR is created | The rule status shows Active |
| 8.5.4d | Verify NAT rules are realised | Both SNAT rules show Active status | NSX Manager → NAT → tier0-gateway shows 2 SNAT rules |

SNAT rule parameters:

| Field | Pod CIDR Rule | Service CIDR Rule |
|-------|--------------|-------------------|
| Action | SNAT | SNAT |
| Source | 192.168.0.0/16 | 10.96.0.0/12 |
| Translated IP | 10.0.60.2 | 10.0.60.2 |
| Applied To | Tier-0 uplink interface | Tier-0 uplink interface |
| Logging | Disabled | Disabled |

> **Note**: These CIDRs match the VKS cluster manifest (`pods.cidrBlocks` and `services.cidrBlocks`). If you change the cluster CIDRs, update the SNAT rules to match.

### 8.6 NSX Networking Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| BGP adjacency | `sudo vtysh -c 'show ip bgp summary'` on gateway | The BGP session is Established with 10.0.60.2 |
| Routes from NSX | `sudo vtysh -c 'show ip bgp'` on gateway | VPC and overlay prefixes are received |
| Routes from gateway | NSX Manager → Networking → Tier-0 → Routing Table | Infrastructure subnets are received from the gateway |
| Edge cluster health | NSX Manager → System → Fabric → Edge Clusters | Both Edge nodes show Up status |
| Tier-0 status | NSX Manager → Networking → Tier-0 Gateways | The Tier-0 status is Realised with all interfaces Up |
| VPC status | NSX Manager → VPC overview | The vks-vpc status shows Realised |

## 9. Phase 8 — VCF Workload VKS

> Phase 8 implements R-005 via VKS-01 through VKS-04. Supervisor enablement, namespace creation, and VKS cluster deployment.

### 9.1 Create Content Library

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.1.1 | In workload vCenter, navigate to Content Libraries | The content library management page is displayed | — |
| 9.1.2 | Create subscribed library: name `vkr-content-library`, subscription URL `https://wp-content.vmware.com/v2/latest/lib.json` | The subscribed content library is created | The sync status shows Active |
| 9.1.3 | Wait for initial sync to complete | VKr images are available in the library | At least one Kubernetes version is listed |

### 9.2 Enable Supervisor

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.2.1 | In workload vCenter, click the hamburger menu > **Workload Management** > **Get Started** | The Supervisor setup wizard is displayed | — |
| 9.2.2 | Select cluster `workload-cluster`, networking stack **NSX** | The workload cluster is selected | — |
| 9.2.3 | Configure management network on VLAN 10, workload network linked to `vks-vpc` | The networking stack is configured | — |
| 9.2.4 | Configure storage policy: `vsan-default-storage-policy` | The storage policy is configured | — |
| 9.2.5 | Start Supervisor enablement | The Supervisor deployment begins | Task progress is visible in the vCenter UI |
| 9.2.6 | Wait for Supervisor deployment (30-45 minutes). Ensure `caffeinate -d` is running to prevent laptop sleep | The vSphere Supervisor is running | The Supervisor status shows Running |

### 9.3 Create vSphere Namespace

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.3.1 | In workload vCenter, navigate to Workload Management → Namespaces | The namespace management page is displayed | — |
| 9.3.2 | Create namespace with name `vks-workloads` | The vks-workloads namespace is created | The namespace status shows Active |
| 9.3.3 | Assign VM classes: best-effort-small, best-effort-medium | The VM classes are assigned to the namespace | The assigned classes are listed under the namespace |
| 9.3.4 | Assign storage policies: vSAN Default | The storage policy is assigned to the namespace | The assigned policy is listed under the namespace |
| 9.3.5 | Assign content library: `vkr-content-library` | The content library is assigned to the namespace | The assigned library is listed under the namespace |

### 9.4 Deploy VKS Cluster

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.4.1 | Connect to Supervisor API: `kubectl vsphere login --server=<supervisor-ip> --vsphere-username administrator@vsphere.local --insecure-skip-tls-verify` | Authentication to the Supervisor API succeeds | A kubeconfig file is obtained |
| 9.4.2 | Switch to the vks-workloads namespace: `kubectl config use-context vks-workloads` | The vks-workloads namespace context is active | `kubectl get ns` shows the namespace |
| 9.4.3 | Apply VKS cluster manifest (Cluster v1beta1) | VKS cluster creation is initiated | `kubectl get cluster` shows Provisioning |
| 9.4.4 | Wait for control plane nodes (3x) | The control plane is ready with 3 nodes | `kubectl get machines` shows 3 Running |
| 9.4.5 | Wait for worker nodes (3x) | All 3 worker nodes are ready | `kubectl get machines` shows 6 Running |
| 9.4.6 | Obtain VKS cluster kubeconfig | The VKS cluster kubeconfig is available | `kubectl get secret` shows the kubeconfig secret |

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

### 9.4a Verify StorageClass and PersistentVolume Provisioning

The vSphere Container Storage Interface (CSI) driver is automatically installed when the Supervisor is enabled. Verify that the StorageClass is available and can provision PersistentVolumes from vSAN.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.4a.1 | Login to VKS cluster | Authentication to the VKS cluster succeeds | `kubectl get nodes` shows 6 nodes |
| 9.4a.2 | Verify StorageClass exists | The StorageClass is listed | `kubectl get storageclass` shows `vsan-default-storage-policy` |
| 9.4a.3 | Create test PVC (1 Gi) | The test PVC is bound to a PersistentVolume | `kubectl get pvc` shows Bound |
| 9.4a.4 | Verify PV created on vSAN | The First Class Disk is visible in vCenter | vCenter → Datastores → vSAN → Monitor → Virtual Objects |
| 9.4a.5 | Delete test PVC | The test PVC and PV are deleted | `kubectl get pv` shows no orphaned PVs |

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

> **StorageClass parameters**: The `vsan-default-storage-policy` StorageClass uses `csi.vsphere.vmware.com` as the provisioner, `reclaimPolicy: Delete`, and `volumeBindingMode: WaitForFirstConsumer`. PVs are backed by vSAN First Class Disks (FCDs) with Failures to Tolerate (FTT)=1 RAID-1 data protection. See [Logical Design](logical-design.md) Section 8 for full CSI/PV architecture.

### 9.5 Deploy Test Workload

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.5.1 | Login to VKS cluster using obtained kubeconfig | Authentication to the VKS cluster succeeds | `kubectl get nodes` shows 6 nodes |
| 9.5.2 | Deploy nginx test deployment | The nginx pods are running | `kubectl get pods` shows Running |
| 9.5.3 | Expose via LoadBalancer service | An external IP is assigned to the LoadBalancer service | `kubectl get svc` shows EXTERNAL-IP |
| 9.5.4 | Access nginx from gateway | The nginx welcome page loads | `curl http://<EXTERNAL-IP>` returns the nginx welcome page |
| 9.5.5 | Verify AppArmor enforcement | AppArmor profile is active on the nginx pods | `kubectl get pod -l app=nginx-test -o jsonpath='{.items[0].spec.containers[0].securityContext.appArmorProfile.type}'` returns `RuntimeDefault` |

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
          securityContext:
            appArmorProfile:
              type: RuntimeDefault
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

## 10. Platform Services (VKS)

> Implements R-012 through R-016 via VKS-09 through VKS-14. A shared-services VKS cluster is deployed within Phase 8, then platform services are installed in dependency order.

### 10.1 Deploy Shared-Services VKS Cluster

Create a new vSphere Namespace and VKS cluster for platform services, following the same process as Phase 8.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.1.1 | In workload vCenter → Workload Management → Namespaces, create namespace `vks-services` | The vks-services namespace is created | Namespace status shows Active |
| 10.1.2 | Assign VM classes (best-effort-small, best-effort-medium), storage policy (vSAN Default), and content library (`vkr-content-library`) to the namespace | Resources are assigned | Classes and policies listed under namespace |
| 10.1.3 | Connect to Supervisor API: `kubectl vsphere login --server=<supervisor-ip> --vsphere-username administrator@vsphere.local --insecure-skip-tls-verify` | Authentication succeeds | kubeconfig obtained |
| 10.1.4 | Switch context: `kubectl config use-context vks-services` | Context active | `kubectl get ns` shows namespace |
| 10.1.5 | Apply VKS cluster manifest for `vks-services-01` (same spec as `vks-cluster-01` but with name `vks-services-01` and namespace `vks-services`) | Cluster creation initiated | `kubectl get cluster` shows Provisioning |
| 10.1.6 | Wait for control plane (3 nodes) and workers (3 nodes) | All 6 nodes Ready | `kubectl get nodes` on vks-services-01 shows 6 Ready |

#### Shared-services cluster manifest

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: vks-services-01
  namespace: vks-services
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

### 10.2 Install cert-manager (VKS Standard Package)

cert-manager is a prerequisite for Contour TLS certificate management. After installation, a ClusterIssuer is configured to use the lab step-ca ACME endpoint so all ingress TLS certificates are signed by the same CA as VCF components (Phase 5).

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.2.1 | Login to VKS shared-services cluster | Authentication succeeds | `kubectl get nodes` shows 6 Ready |
| 10.2.2 | Install cert-manager: `vcf package install cert-manager` | cert-manager pods are deployed | `kubectl get pods -n cert-manager` shows all Running |
| 10.2.3 | Verify cert-manager webhook is ready | Webhook is operational | `kubectl get apiservice v1.cert-manager.io` shows Available=True |
| 10.2.4 | Create `lab-ca` ClusterIssuer pointing at step-ca ACME endpoint | ClusterIssuer registered | `kubectl get clusterissuer lab-ca` shows Ready=True |
| 10.2.5 | Verify ACME account registration | cert-manager can reach step-ca | ClusterIssuer conditions show `ACMEAccountRegistered` |

> **Note**: The `lab-ca` ClusterIssuer uses HTTP-01 challenge validation via the Contour ingress class. Contour must be installed (§10.3) before certificates can actually be issued, but the ClusterIssuer can be created first — cert-manager will retry until the solver is available.

### 10.3 Install Contour (VKS Standard Package)

Contour provides L7 ingress routing. The Envoy DaemonSet receives an NSX LB VIP for its Service type LoadBalancer.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.3.1 | Install Contour: `vcf package install contour` | Contour and Envoy pods are deployed | `kubectl get pods -n projectcontour` shows all Running |
| 10.3.2 | Verify Envoy LoadBalancer service has an external IP | NSX LB provisions a VIP | `kubectl get svc -n projectcontour envoy` shows EXTERNAL-IP |
| 10.3.3 | Add DNS record for the Envoy VIP | Wildcard or per-service records resolve to the VIP | `dig @10.0.10.1 *.services.lab.dreamfold.dev` returns the VIP |

> **Note**: The Envoy VIP is the single L4 entry point for all L7 services (Harbor, ArgoCD). Contour routes traffic by hostname/path using HTTPProxy CRDs.

### 10.4 Install Harbor (VKS Standard Package)

Harbor provides a container registry proxy cache for GHCR.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.4.1 | Install Harbor: `vcf package install harbor` with configuration values specifying Contour HTTPProxy ingress and the `harbor.lab.dreamfold.dev` hostname | Harbor pods are deployed | `kubectl get pods -n harbor` shows all Running |
| 10.4.2 | Verify Harbor health endpoint | Harbor API is accessible | `curl https://harbor.lab.dreamfold.dev/api/v2.0/health` returns `{"status":"healthy"}` |
| 10.4.3 | Login to Harbor web UI and create a proxy cache project named `ghcr-proxy` with endpoint `https://ghcr.io` | The proxy cache project is created | The `ghcr-proxy` project is listed in Harbor |
| 10.4.4 | Test image pull through proxy cache: `docker pull harbor.lab.dreamfold.dev/ghcr-proxy/library/nginx:latest` | The image is cached locally in Harbor | Harbor UI shows the image in the `ghcr-proxy` project |

### 10.5 Install MinIO (Helm)

MinIO provides S3-compatible storage for Velero backups.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.5.1 | Add MinIO Helm repo: `helm repo add minio https://charts.min.io/` | Repo added | `helm repo list` shows minio |
| 10.5.2 | Install MinIO with a 100 Gi PVC: `helm install minio minio/minio --namespace velero --create-namespace --set persistence.size=100Gi --set resources.requests.memory=1Gi` | MinIO pod is deployed | `kubectl get pods -n velero` shows minio Running |
| 10.5.3 | Create a `velero` bucket in MinIO | The bucket is available | `mc alias set minio http://minio.velero.svc:9000 <access-key> <secret-key> && mc mb minio/velero` succeeds |

### 10.6 Install Velero (VKS Standard Package)

Velero provides Kubernetes resource and PersistentVolume backup.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.6.1 | Install Velero: `vcf package install velero` with BackupStorageLocation pointing to MinIO (`http://minio.velero.svc:9000`, bucket `velero`) | Velero server and node-agent pods are deployed | `kubectl get pods -n velero` shows velero and node-agent Running |
| 10.6.2 | Enable CSI snapshot support | VolumeSnapshot CRDs are available | `kubectl get crd volumesnapshots.snapshot.storage.k8s.io` exists |
| 10.6.3 | Create a test backup: `velero backup create test-backup --include-namespaces default` | The backup completes | `velero backup get test-backup` shows Completed |
| 10.6.4 | Create a daily backup schedule: `velero schedule create daily-backup --schedule="0 2 * * *" --include-namespaces default,harbor` | The schedule is created | `velero schedule get` shows daily-backup |

### 10.7 Install ArgoCD (Helm)

ArgoCD provides GitOps-based deployment across both VKS clusters.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 10.7.1 | Add ArgoCD Helm repo: `helm repo add argo https://argoproj.github.io/argo-helm` | Repo added | `helm repo list` shows argo |
| 10.7.2 | Install ArgoCD: `helm install argocd argo/argo-cd --namespace argocd --create-namespace` | ArgoCD pods are deployed | `kubectl get pods -n argocd` shows all Running |
| 10.7.3 | Configure Contour HTTPProxy for ArgoCD UI: create HTTPProxy resource for `argocd.lab.dreamfold.dev` pointing to `argocd-server` service | ArgoCD UI is accessible via Contour | `curl https://argocd.lab.dreamfold.dev` loads the login page |
| 10.7.4 | Retrieve initial admin password: `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' \| base64 -d` | The admin password is obtained | Login to ArgoCD UI succeeds |
| 10.7.5 | Register workload cluster as a spoke: `argocd cluster add vks-cluster-01 --name workload` | The workload cluster is registered | `argocd cluster list` shows both clusters |

### 10.8 Platform Services Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| Shared-services cluster health | `kubectl get nodes` on vks-services-01 | All 6 nodes Ready |
| Contour | `kubectl get pods -n projectcontour` | All Running |
| Envoy LB VIP | `kubectl get svc -n projectcontour envoy` | EXTERNAL-IP assigned |
| Harbor health | `curl https://harbor.lab.dreamfold.dev/api/v2.0/health` | `{"status":"healthy"}` |
| Harbor proxy cache | Pull image via `harbor.lab.dreamfold.dev/ghcr-proxy/...` | Image cached successfully |
| MinIO | `mc admin info minio` | Connected, bucket `velero` exists |
| Velero | `velero backup get` | Recent backup shows Completed |
| ArgoCD UI | Browse `https://argocd.lab.dreamfold.dev` | Login page loads |
| ArgoCD clusters | `argocd cluster list` | Both clusters listed, healthy |

## 11. Ready for Operations Testing

Final verification checklist before the lab is considered operational.

### 11.1 Infrastructure Services

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 1 | External RDP access | RDP to gateway public IP | The GNOME desktop loads via RDP | ☐ |
| 2 | DNS forward resolution | `dig @10.0.10.1 vcenter-mgmt.lab.dreamfold.dev` | The query returns 10.0.10.4 | ☐ |
| 3 | DNS reverse resolution | `dig @10.0.10.1 -x 10.0.10.4` | The query returns vcenter-mgmt.lab.dreamfold.dev | ☐ |
| 4 | NTP synchronisation | `chronyc sources` on gateway | Upstream NTP servers are reachable | ☐ |
| 5 | CA health | `step ca health` on gateway | The health check returns "ok" | ☐ |
| 6 | Inter-VLAN routing | `ping 10.0.20.1` from an ESXi host | The ping succeeds | ☐ |

### 11.2 VCF Platform

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 7 | Management vCenter | Browse `https://vcenter-mgmt.lab.dreamfold.dev` | The login page loads | ☐ |
| 8 | Workload vCenter | Browse `https://vcenter-wld.lab.dreamfold.dev` | The login page loads | ☐ |
| 9 | SDDC Manager | Browse `https://sddc-manager.lab.dreamfold.dev` | Both domains show Active status | ☐ |
| 10 | Management vSAN health | vCenter → Cluster → vSAN Health | All vSAN health checks are green | ☐ |
| 11 | Workload vSAN health | vCenter → Cluster → vSAN Health | All vSAN health checks are green | ☐ |
| 12 | All ESXi hosts connected | Both vCenters show hosts Connected | All hosts are connected (4 management + 3 workload) | ☐ |

### 11.3 NSX Networking

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 13 | BGP adjacency | `sudo vtysh -c 'show ip bgp summary'` on gateway | The BGP session is Established | ☐ |
| 14 | Route exchange | `sudo vtysh -c 'show ip bgp'` on gateway | VPC prefixes are received from the NSX Tier-0 | ☐ |
| 15 | Edge cluster health | NSX Manager → Edge Clusters | Both Edge nodes show Up status | ☐ |
| 16 | Tier-0 status | NSX Manager → Tier-0 Gateways | The Tier-0 status is Realised | ☐ |
| 17 | VPC status | NSX Manager → VPC | The VPC status is Realised | ☐ |

### 11.4 VKS

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 18 | Supervisor status | vCenter → Workload Management | The Supervisor status shows Running | ☐ |
| 19 | VKS cluster health | `kubectl get cluster vks-cluster-01` | The cluster phase shows Provisioned | ☐ |
| 20 | All nodes ready | `kubectl get nodes` on VKS cluster | All 6 nodes show Ready status | ☐ |
| 21 | Test workload | `curl http://<nginx-lb-ip>` | The nginx welcome page is returned | ☐ |
| 22 | Pod-to-external | `kubectl exec` into pod, `curl google.com` | A response is received from the external site | ☐ |
| 23 | AppArmor enforcement | `kubectl get pod -o jsonpath='{.items[0].spec.containers[0].securityContext.appArmorProfile.type}'` on VKS cluster | RuntimeDefault is reported | ☐ |

### 11.5 Platform Services

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 24 | Shared-services cluster | `kubectl get nodes` on vks-services-01 | All 6 nodes show Ready status | ☐ |
| 25 | Contour ingress | `kubectl get pods -n projectcontour` on vks-services-01 | All pods Running | ☐ |
| 26 | Harbor health | `curl https://harbor.lab.dreamfold.dev/api/v2.0/health` | Returns `{"status":"healthy"}` | ☐ |
| 27 | Harbor proxy cache | Pull image via `harbor.lab.dreamfold.dev/ghcr-proxy/...` | Image cached successfully | ☐ |
| 28 | Velero backup | `velero backup get` | Recent backup shows Completed | ☐ |
| 29 | ArgoCD UI | Browse `https://argocd.lab.dreamfold.dev` | Login page loads | ☐ |
| 30 | ArgoCD clusters | `argocd cluster list` | Both clusters listed and healthy | ☐ |

## 12. Per-Phase Troubleshooting

This section covers the most common failures encountered during each deployment phase. For ongoing operational troubleshooting procedures, see [Operations Guide](operate.md) Section 4.

### 12.1 Phase 0 — vApp Template

| Symptom | Cause | Resolution |
|---------|-------|------------|
| vApp creation fails with storage quota error | The VDC storage policy quota is insufficient for the 8-VM vApp | Request a storage quota increase from the vCD provider administrator |
| SCP transfer of the OVA stalls or times out | The vCD public network has bandwidth limits or the gateway VM is not fully booted | Verify the gateway has a public IP (`ip addr show ens33`), retry with `scp -C` for compression, or use `rsync --partial` for resumable transfers |
| "Add to Catalog" fails or times out | The target storage policy does not have enough free capacity, or the catalog has a permissions issue | Verify the storage policy `ProvisioningStoragePolicy-provider01` has sufficient free space in the vCD provider portal |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.2 Phase 1 — Foundation

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Ansible SSH connection to gateway fails with "Permission denied" | The SSH key was not copied, or the gateway IP changed after reboot | Re-run `ssh-copy-id ubuntu@<gateway-ip>` and verify the IP matches the 1Password "Lab Bootstrap" item |
| dnsmasq fails to start — port 53 already in use | `systemd-resolved` is binding port 53 on the gateway | The Ansible `gateway` role disables `systemd-resolved`; if running manually, stop it first: `sudo systemctl disable --now systemd-resolved` |
| FRR service fails to start | The FRR configuration file has a syntax error, or the FRR package is not installed | Check FRR status with `sudo systemctl status frr` and review `/etc/frr/frr.conf` for syntax errors |
| Keycloak container fails to start | The TLS certificates from step-ca have not been generated, or Docker is not running | Verify Docker is running (`sudo systemctl status docker`) and that certificates exist at `/etc/step-ca/certs/keycloak.crt` |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.3 Phase 3 — Nested ESXi

| Symptom | Cause | Resolution |
|---------|-------|------------|
| DHCP does not assign a static IP to an ESXi host | The Phase 2 MAC discovery playbook did not run, or the host had no dynamic lease when discovery ran | Re-run `ansible-playbook playbooks/phase2_discover_macs.yml` from the `ansible/` directory. If the host has no dynamic lease, verify it is powered on and connected to the `lab-trunk` network, then check `cat /var/lib/misc/dnsmasq.leases` on the gateway |
| SSH to ESXi host is refused | SSH was not enabled via DCUI, or the ESXi firewall is blocking connections | Re-enable SSH via DCUI (**F2** > **Troubleshooting Options** > **Enable SSH**) |
| NVMe device is not marked as SSD after running the playbook | The `esxi_prepare` role did not execute the SSD marking step, or the ESXi host was rebooted after preparation | Re-run `ansible-playbook playbooks/phase3_esxi.yml --limit <host>` and verify with `esxcli vsan storage list` |
| vSAN ESA health check shows "disk not claimed" | The NVMe device was not tagged for vSAN use | Run `esxcli vsan storage tag add -d <device-id> -t capacityFlash` on the affected host |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.4 Phase 4 — VCF Management Domain

| Symptom | Cause | Resolution |
|---------|-------|------------|
| VCF Installer UI is not accessible at `https://vcf-installer.lab.dreamfold.dev` | The installer services are still starting (can take 5–10 minutes after power-on) | Wait for services to finish initialising. SSH to the installer and check: `systemctl status vmware-bringup` |
| Bringup fails with HCL timestamp validation error | The embedded vSAN HCL file (`all.json`) is more than 90 days old | Patch the timestamp as described in Section 6.2 (Troubleshooting: vSAN HCL Timestamp Validation) |
| Bringup stalls on DNS resolution — "AAAA record delay" | dnsmasq is returning AAAA (IPv6) records that cause lookup delays in the bringup workflow | Add `dns-option:no-aaaa` to the dnsmasq configuration on the gateway, then restart dnsmasq |
| vSAN cluster creation fails with "FakeSCSIReservations not enabled" | The `Disk.FakeSCSIReservations` advanced setting was not applied on one or more management hosts | SSH to the affected host and run: `esxcli system settings advanced set -o /Disk/FakeSCSIReservations -i 1`, then reboot the host |
| Bringup times out waiting for SDDC Manager deployment | The VCF Installer VM has insufficient resources or network connectivity issues | Verify the installer VM can ping all management hosts and the DNS server. Check `/var/log/vmware/vcf/bringup/` logs on the installer for specific errors |
| Bringup fails at *Migrate ESXi Host Management vmknic(s) to vSphere Distributed Switch* with "Network configuration change disconnected the host from vCenter Server and has been rolled back" on remote hosts | ESXi VMs have more than one vNIC, causing the VDS to use load-based teaming. The atomic VSS-to-VDS migration of vmnic + vmk0 introduces a brief connectivity blip on remote hosts that triggers vCenter's network rollback safety mechanism | Confirm each ESXi VM has only a single vNIC attached to `lab-trunk` (see Logical Design [NET-06](logical-design.md) and [ESX-04](logical-design.md)). If a second vNIC is present, power off the VM and remove it in vCD, then redeploy from a corrected template |
| Bringup spec validation fails with `VMNIC_IN_USE_MISSING_FROM_SPEC` | A vmnic (e.g. `vmnic1`) is currently attached to vSwitch0 on an ESXi host but is not declared in the bringup spec's `vmnicsToUplinks` array | Either remove the unwanted vNIC from the ESXi VM in vCD, or add it to the bringup spec. The single-vNIC design (NET-06) is the cleaner option |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.5 Phase 6 — VCF Workload Domain

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Host commission validation fails — "host does not have enough capacity disks" (all hosts) | Nested lab storage does not meet real hardware validation requirements. SDDC Manager validation must be bypassed for lab environments (VCF 9.0.1+) | Apply the vSAN ESA workaround as described in Section 7.0 **before** commissioning hosts. The property must be added to **both** `/etc/vmware/vcf/operationsmanager/application-prod.properties` **and** `/etc/vmware/vcf/domainmanager/application-prod.properties`, then restart using `/opt/vmware/vcf/operationsmanager/scripts/cli/sddcmanager_restart_services.sh` |
| Host commission validation fails — "host not reachable" | DNS or network connectivity issues between SDDC Manager and the workload hosts | Verify forward and reverse DNS records for esxi-05 through esxi-07, and confirm `ping` succeeds from the SDDC Manager appliance |
| Domain creation fails — "insufficient hosts" | Fewer than 3 hosts are in the free pool, or one host failed commissioning | Check the SDDC Manager **Inventory** > **Hosts** page for failed hosts, resolve the issue, and re-commission |
| Domain creation fails with IP conflict | The vCenter or NSX Manager IP (10.0.10.9 or 10.0.10.10) is already in use | Verify no other VM is using these IPs with `ping` from the gateway. Check dnsmasq DHCP leases for conflicts |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.6 Phase 7 — VCF Workload NSX Networking

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Edge VM deployment fails with "PDPE1GB CPU instruction not available" | The nested ESXi host VM does not expose 1GB hugepage support | Add the VM Advanced Setting `featMask.vm.cpuid.PDPE1GB = Val:1` to each ESXi host VM in vCD, then power-cycle the host |
| Edge OVF deployment fails with `VALIDATION_ERROR: CERTIFICATE_EXPIRED` | The NSX Edge OVF certificate has expired | Follow VMware KB 424034 to replace the expired OVF certificate, then retry Edge deployment |
| BGP session is stuck in Active state (not Established) | Timer mismatch between FRR and NSX Tier-0, or the uplink VLAN segment is misconfigured | Verify both sides use keepalive `60` / hold `180`. Check that the Tier-0 uplink interface IP (`10.0.60.2`) and the FRR neighbor IP (`10.0.60.1`) are on the same VLAN 60 segment. Confirm with `sudo vtysh -c 'show ip bgp summary'` on the gateway |
| SNAT rules are not working — pods cannot reach external networks | The SNAT rules are not applied to the correct Tier-0 uplink interface, or the source CIDR does not match the VKS cluster CIDRs | Verify the SNAT rules in NSX Manager > **Networking** > **NAT** > `tier0-gateway`. Ensure the source CIDRs match `192.168.0.0/16` (pods) and `10.96.0.0/12` (services), and "Applied To" is set to the Tier-0 uplink interface |
| Edge transport node status shows "Degraded" | TEP connectivity issue — the Edge TEP VLAN or IP is misconfigured | Verify Edge TEP IPs (`10.0.50.20`/`10.0.50.21`) are on VLAN 50, and that the gateway can ping both TEP addresses |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.7 Phase 8 — VCF Workload VKS

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Content library sync fails — "unable to connect to subscription URL" | The gateway cannot reach `https://wp-content.vmware.com` due to DNS or firewall issues | Verify external DNS resolution from the gateway: `dig wp-content.vmware.com`. Ensure NAT/masquerading is active: `sudo iptables -t nat -L POSTROUTING` |
| Supervisor enablement stalls at "Configuring" for more than 45 minutes | The NSX VPC or Edge cluster is unhealthy, preventing the Supervisor from creating its networking stack | Check NSX Manager for VPC and Edge cluster health. Verify the Tier-0 and Tier-1 gateways show Realised status. Review vCenter > **Workload Management** > **Supervisor** > **Events** for specific errors |
| VKS cluster is stuck in "Provisioning" state | The VM class is not assigned to the namespace, or the content library does not contain a compatible Kubernetes version | Verify VM classes (best-effort-small, best-effort-medium) and the content library (`vkr-content-library`) are assigned to the `vks-workloads` namespace. Check `kubectl describe cluster vks-cluster-01` for event details |
| LoadBalancer service has no EXTERNAL-IP (shows `<pending>`) | The NSX VPC load balancer is not provisioned, or SNAT rules prevent return traffic | Verify the VPC has an active load balancer. Check SNAT rules on the Tier-0 Gateway. Review `kubectl describe svc nginx-test` for events indicating the failure reason |
| Pods are running but cannot reach external networks | SNAT rules are missing or the BGP route exchange is not working | Verify SNAT rules are Active in NSX Manager. Check BGP adjacency on the gateway (`sudo vtysh -c 'show ip bgp summary'`). Test from inside a pod: `kubectl exec -it <pod> -- curl -v http://10.0.10.1` to confirm gateway reachability |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.

### 12.8 Platform Services (VKS)

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `vcf package install` fails — "package not found" | The VKS Standard Package repository is not synced or the cluster does not have internet access | Verify content library sync is current; confirm pods can reach external registries via SNAT |
| Contour Envoy service stuck at `<pending>` EXTERNAL-IP | The NSX VPC load balancer is not provisioning a VIP for the Envoy service | Check NSX Manager → VPC → Load Balancer status; verify the Tier-1 gateway is healthy and LB VIP pool has available IPs |
| Harbor pods in CrashLoopBackOff | PVC not bound or insufficient storage | Check `kubectl get pvc -n harbor` — all PVCs should be Bound. Verify vSAN capacity in vCenter → vSAN → Capacity |
| Harbor proxy cache returns 502 for GHCR images | The proxy cache endpoint is misconfigured or GHCR is unreachable from Harbor | Verify the `ghcr-proxy` project endpoint is `https://ghcr.io` in Harbor UI; test outbound connectivity from a Harbor pod |
| Velero backup fails with "BackupStorageLocation unavailable" | MinIO is not running or the bucket does not exist | Check `kubectl get pods -n velero` for MinIO status; verify bucket with `mc ls minio/velero` |
| ArgoCD cannot register workload cluster | kubeconfig or RBAC issue on the target cluster | Verify the kubeconfig for vks-cluster-01 is valid; ensure the ArgoCD service account has cluster-admin on the target |

For additional troubleshooting, see [Operations Guide](operate.md) Section 4.
