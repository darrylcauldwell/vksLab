---
title: "VKS Lab"
subtitle: "Delivery Guide"
author: "dreamfold"
date: "March 2026"
---

# Delivery Guide

## 1. Deployment Overview

The lab is built in two tiers. **Phase 0** is a one-time operation that creates a reusable vApp template containing 8 VMs (1 gateway + 7 ESXi). This template is stored in the vCD catalog where it is exempt from lease expiry, so it survives the 14-day runtime and 30-day storage leases. **Phases 1–6** run on each rebuild by deploying from that template — dramatically faster than building from scratch.

| Phase | Name | Frequency |
|-------|------|-----------|
| 0 | vApp Template | One-time |
| 1 | Foundation | Each rebuild |
| 2 | Nested ESXi | Each rebuild |
| 3 | VCF Management Domain | Each rebuild |
| 4 | VCF Workload Domain | Each rebuild |
| 5 | NSX Networking | Each rebuild |
| 6 | VKS | Each rebuild |

**Phase 0** creates the baseline vApp with a gateway VM (Ubuntu, Open Virtual Appliance (OVA) pre-staged) and 7 ESXi VMs, then saves it as a catalog template. **Phase 1** deploys the template, configures the gateway (Domain Name System (DNS), Network Time Protocol (NTP), Certificate Authority (CA), inter-Virtual LAN (VLAN) routing, Free Range Routing (FRR) Border Gateway Protocol (BGP)). **Phase 2** configures all seven nested ESXi hosts. **Phase 3** runs the VMware Cloud Foundation (VCF) Installer to bring up the management domain (vCenter, Software-Defined Data Center (SDDC) Manager, VCF Networking (NSX) Manager, VCF Operations, VCF Automation). **Phase 4** commissions workload hosts and creates the workload domain. **Phase 5** deploys the NSX Edge cluster, configures NSX Tier-0 Gateway / NSX Tier-1 Gateway, establishes BGP peering, and creates the NSX Virtual Private Cloud (VPC). **Phase 6** enables the vSphere Supervisor, creates a vSphere Namespace, and deploys a vSphere Kubernetes Services (VKS) cluster with a test workload.

## 2. Prerequisites

> Before starting deployment, verify that all assumptions from [Conceptual Design](conceptual-design.md) Section 7 hold true. See Section 2.2 below for the verification checklist.

The following must be in place before starting Phase 1.

| # | Prerequisite | Status |
|---|-------------|--------|
| 1 | vCD resources approved (338 vCPU, 906 GB RAM, 1.5 TB storage) | ☐ |
| 2 | Ubuntu ISO available in vCD Content Hub (`ubuntu-24.04.2-live-server-amd64.iso`), ESXi vApp template available (`[baked]esxi-9.0.2-2514807`) | ☐ |
| 3 | VCF Installer OVA (`VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova`, 2.03 GB) — download from support.broadcom.com to operator laptop (formerly Cloud Builder; consolidated into SDDC Manager appliance in VCF 9.0) | ☐ |
| 4 | RDP client installed on operator Mac — [Windows App](https://apps.apple.com/app/windows-app/id1295203466) from App Store | ☐ |

## 3. Phase 0 — vApp Template (One-Time)

> This phase is performed once to create a reusable baseline. The resulting catalog template persists indefinitely (no lease) and is used as the starting point for every rebuild.

### 3.1 Create vCD vApp (Manual)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1.1 | Create new vApp in vCloud Director | Empty vApp created |
| 3.1.2 | Add routed network (public) to vApp | External connectivity available |
| 3.1.3 | Add isolated network: name `lab-trunk`, gateway CIDR `192.168.254.1/24`, tick **Allow Guest VLAN** | Trunk-capable internal network available |

### 3.2 Deploy Gateway VM (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.2.1 | Create Ubuntu 24.04 VM from Content Hub ISO (2 vCPU, 10 GB RAM, 60 GB disk) with NIC1 on Public network, NIC2 on lab-trunk | VM created | VM visible in vApp |
| 3.2.2 | Power on and complete Ubuntu installer via vCD console — set server name `gateway`, username `ubuntu`, password from 1Password "Lab Bootstrap" item | Ubuntu installed | Login prompt on console |
| 3.2.3 | Run `apt update && apt upgrade -y` to bring the OS up to date | Packages updated | No pending updates |

### 3.3 Stage SDDC Manager OVA on Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.3.1 | Download `VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova` (2.03 GB) from support.broadcom.com to operator laptop | OVA saved locally | File exists on laptop |
| 3.3.2 | Note public IP assigned by DHCP to NIC1 (ens160): `ip addr show ens160` | IP obtained | — |
| 3.3.3 | SCP OVA from laptop to gateway: `scp VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova ubuntu@<gateway-ip>:~/vcf-installer.ova` | OVA on gateway | `ls -lh ~/vcf-installer.ova` shows 2.03 GB |

### 3.4 Clone ESXi VMs (Manual in vCD)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.4.1 | Clone esxi-01 through esxi-04 from vApp template `[baked]esxi-9.0.2-2514807` (48 vCPU, 128 GB RAM, 40 GB boot Non-Volatile Memory Express (NVMe) + 200 GB vSAN NVMe), both NICs on `lab-trunk` | 4 management VMs cloning |
| 3.4.2 | Clone esxi-05 through esxi-07 (same spec), both NICs on `lab-trunk` | 3 workload VMs cloning |

### 3.5 Power Off and Save to Catalog

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.5.1 | Power off all 8 VMs (gateway + 7 ESXi) | All VMs stopped | vApp shows all VMs powered off |
| 3.5.2 | In vCD, right-click vApp → Add to Catalog. Name: `[baseline]vcf-lab-8vm`, storage policy: `ProvisioningStoragePolicy-provider01` | Template created | Catalog shows template |
| 3.5.3 | Verify template is visible in catalog and contains 8 VMs | Template valid | Open template details, confirm 8 VMs listed |

> **Note**: The original vApp can be deleted after the template is saved — it is no longer needed. All subsequent rebuilds deploy from the catalog template.

## 4. Phase 1 — Foundation

> Phase 1 implements R-001, R-002, R-003, R-009 via VCD-01, VCD-02, NET-01, NET-05, SVC-01 through SVC-08.

### 4.1 Operator Laptop Setup

#### 4.1.1 1Password Secret Store

Ansible retrieves all lab credentials from 1Password at runtime (from the "Employee" vault). Install the CLI and generate passwords:

```bash
# Install 1Password CLI (macOS)
brew install --cask 1password-cli

# Enable CLI integration in 1Password desktop app:
#   Settings → Security → enable "Unlock using system authentication"
#   Settings → Developer → enable "Integrate with 1Password CLI"
# After this, op commands authenticate via Touch ID — no manual signin needed.

# Bootstrap password — simple, typed manually into vCD console and ESXi DCUI
op item create --vault Employee --category login --title "Lab Bootstrap" \
  password='VMware1!VMware1!'

# Runtime passwords — complex, injected by Ansible (never typed manually)
op item create --vault Employee --category login --title "ESXi Root" \
  --generate-password='20,letters,digits,symbols' username=root
op item create --vault Employee --category login --title "vCenter SSO" \
  --generate-password='20,letters,digits,symbols' username='administrator@vsphere.local'
op item create --vault Employee --category login --title "SDDC Manager" \
  --generate-password='20,letters,digits,symbols' username='admin@local'
op item create --vault Employee --category login --title "NSX Manager" \
  --generate-password='20,letters,digits,symbols' username=admin
op item create --vault Employee --category login --title "Keycloak Admin" \
  --generate-password='20,letters,digits,symbols' username=admin
```

Verify: `op item list --vault Employee` shows all 6 items.

#### 4.1.2 Ansible

Ansible runs from the operator's laptop (not the gateway) and connects to lab hosts via SSH ProxyJump through the gateway.

```bash
# Create and activate virtual environment (from repo root)
python3 -m venv .venv
source .venv/bin/activate

# Install Ansible and required collections
pip install ansible-core
ansible-galaxy collection install -r ansible/collections/requirements.yml
```

> **Note**: Activate the virtual environment (`source .venv/bin/activate`) and run all `ansible-playbook` commands from the `ansible/` directory (where `ansible.cfg` lives). The `.venv/` directory is already in `.gitignore`.

### 4.2 Deploy vApp from Template (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 4.2.1 | In vCD catalog, deploy vApp from template `[baseline]vcf-lab-8vm` | vApp created with 8 VMs | vApp visible with all VMs |
| 4.2.2 | Read back MAC addresses from vCD for all 7 ESXi VMs (vmnic0), update `esxi_mac` in `ansible/inventory/hosts.yml` | MACs recorded | Inventory file updated |
| 4.2.3 | Power on all 8 VMs | VMs running | Gateway gets public IP via DHCP |
| 4.2.4 | Note gateway public IP: `ip addr show ens160` via vCD console | IP obtained | — |
| 4.2.5 | Store gateway IP in 1Password: `op item edit "Lab Bootstrap" ip_address=<gateway-ip>` | IP stored | `op item get "Lab Bootstrap" --fields ip_address` returns IP |
| 4.2.6 | If no SSH key exists, generate one: `ssh-keygen -t ed25519` | Key pair created | `~/.ssh/id_ed25519.pub` exists |
| 4.2.7 | Copy SSH key to gateway: `ssh-copy-id ubuntu@<gateway-ip>` | Key deployed | `ssh ubuntu@<gateway-ip>` connects without password |

> **Note**: vCD assigns new MAC addresses each time a vApp is deployed from a template. The MAC update in step 4.2.2 is required on every rebuild so that DHCP reservations match.

### 4.3 Configure Gateway (Automated)

All gateway configuration (VLAN sub-interfaces, dnsmasq DNS/DHCP, chrony NTP, step-ca, XFCE/xrdp, IP masquerading, FRR BGP, Firefox, Keycloak) is automated by the `gateway` and `docker_services` Ansible roles:

```bash
source .venv/bin/activate
cd ansible
ansible-playbook playbooks/phase1_foundation.yml
```

### 4.4 Foundation Verification

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| Gateway external access | RDP to gateway public IP | Desktop accessible |
| Gateway DNS | `dig @10.0.10.1 gateway.lab.dreamfold.dev` | Returns 10.0.10.1 |
| Gateway NTP | `chronyc sources` | Shows upstream servers |
| Gateway CA | `step ca health` | Returns "ok" |
| VLAN sub-interfaces | `ip addr show ens192.10` on gateway | Shows 10.0.10.1 |
| Inter-VLAN routing | `ping 10.0.20.1` from a host on VLAN 10 | Success |
| FRR BGP | `vtysh -c 'show ip bgp summary'` on gateway | FRR running |

## 5. Phase 2 — Nested ESXi

> Phase 2 implements R-004, R-007 via ESX-01 through ESX-04 and NET-03, NET-04.

### 5.1 Configure ESXi Hosts (Manual)

ESXi hosts receive their management IP via DHCP from the gateway dnsmasq (configured in Phase 1). MAC addresses were recorded during Phase 1 template deployment (§4.2.2).

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.1.1 | On each host via Direct Console User Interface (DCUI): Troubleshooting Options → Enable SSH | SSH enabled | `ssh root@<ip>` connects |
| 5.1.2 | On each host via DCUI: set root password to match 1Password "Lab Bootstrap" item | Password set | SSH login with bootstrap password works |

### 5.2 Prepare Hosts (Automated)

Use the Ansible `esxi_prepare` role to configure all hosts. This sets hostname, DNS, NTP, root password, and prepares vSAN Express Storage Architecture (ESA) in a single operation.

```bash
cd ansible
ansible-playbook playbooks/phase2_esxi.yml
# Or prepare a single host
ansible-playbook playbooks/phase2_esxi.yml --ask-become-pass --limit esxi-01
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

| Check | Command / Method | Expected Result |
|-------|------------------|-----------------|
| All hosts reachable | `ping 10.0.10.{11..17}` from gateway | All respond |
| DNS resolution | `nslookup esxi-01.lab.dreamfold.dev 10.0.10.1` | Returns correct IP for all hosts |
| Reverse DNS | `nslookup 10.0.10.11 10.0.10.1` | Returns esxi-01.lab.dreamfold.dev |
| NTP sync | `esxcli system ntp get` on each host | NTP server configured (10.0.10.1) |
| Time sync | Compare time across all hosts | Within 1 second |
| vSAN ESA ready | `esxcli vsan storage list` on each host | NVMe device marked as SSD |
| Host status | `cd ansible && ansible-playbook playbooks/phase2_esxi.yml --check` | All tasks show ok |

## 6. Phase 3 — VCF Management Domain

> Phase 3 implements R-004 via VCF-01, VCF-03, VCF-04. VCF Installer drives initial bringup of vCenter, SDDC Manager, and NSX Manager.

### 6.1 Pre-Bringup DNS Records

Verify all DNS records are configured in dnsmasq (done in Phase 1). Forward and reverse records must exist for:

| Hostname | IP | Purpose |
|----------|-----|---------|
| vcf-installer.lab.dreamfold.dev | 10.0.10.3 | VCF Installer |
| vcenter-mgmt.lab.dreamfold.dev | 10.0.10.4 | Management vCenter |
| sddc-manager.lab.dreamfold.dev | 10.0.10.5 | SDDC Manager |
| nsx-mgr-mgmt.lab.dreamfold.dev | 10.0.10.6 | Management NSX Manager |

### 6.2 Deploy VCF Installer

In VCF 9.0, the SDDC Manager appliance doubles as the VCF Installer (Cloud Builder functionality is consolidated into it). The OVA was pre-staged on the gateway in Phase 0 (`~/vcf-installer.ova`).

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.2.1 | Upload OVA from gateway to esxi-01 datastore: `scp ~/vcf-installer.ova root@esxi-01:…` or ESXi Host Client | OVA available on datastore | Datastore browser shows file |
| 6.2.2 | Deploy VCF Installer OVA with IP 10.0.10.3, GW 10.0.10.1, DNS 10.0.10.1 | Appliance deployed | VM powered on |
| 6.2.3 | Wait for installer services to start (5-10 minutes) | Services ready | `https://vcf-installer.lab.dreamfold.dev` accessible |

#### VCF Deployment Parameter Workbook

The bringup spec is defined as a YAML dict in `ansible/roles/vcf_bringup/defaults/main.yml`. All IPs are derived from `lab_network_prefix` and credentials are injected from 1Password at runtime — no manual JSON editing required. The Ansible `vcf_bringup` role validates and submits the spec to the VCF Installer API.

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

### 6.3 Run VCF Bringup

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.3.1 | Access VCF Installer UI at `https://vcf-installer.lab.dreamfold.dev` | Login page | Browser loads |
| 6.3.2 | Upload deployment parameter workbook (JSON) | Parameters validated | No validation errors |
| 6.3.3 | Start bringup workflow | Deployment begins | Progress bar advancing |
| 6.3.4 | Wait for vCenter deployment | vCenter Server deployed | `https://vcenter-mgmt.lab.dreamfold.dev` accessible |
| 6.3.5 | Wait for VDS and vSAN configuration | Networking and storage configured | vSAN health green in vCenter |
| 6.3.6 | Wait for SDDC Manager deployment | SDDC Manager deployed | `https://sddc-manager.lab.dreamfold.dev` accessible |
| 6.3.7 | Wait for NSX Manager deployment | NSX Manager deployed | `https://nsx-mgr-mgmt.lab.dreamfold.dev` accessible |
| 6.3.8 | Bringup completes | Management domain operational | SDDC Manager shows healthy domain |

### 6.4 Post-Bringup Deployments

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.4.1 | Deploy VCF Operations from SDDC Manager | VCF Operations deployed | `https://vcf-ops.lab.dreamfold.dev` accessible |
| 6.4.2 | Deploy VCF Automation from SDDC Manager | VCF Automation deployed | `https://vcf-auto.lab.dreamfold.dev` accessible |
| 6.4.3 | Remove VCF Installer VM (no longer needed) | Resources reclaimed | VM deleted |

### 6.5 Management Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| vCenter health | Login to `https://vcenter-mgmt.lab.dreamfold.dev` | Cluster shows 4 hosts, all connected |
| vSAN health | vCenter → Cluster → Monitor → vSAN → Health | All health checks green |
| SDDC Manager | Login to `https://sddc-manager.lab.dreamfold.dev` | Management domain shows Active |
| NSX Manager | Login to `https://nsx-mgr-mgmt.lab.dreamfold.dev` | Dashboard accessible, transport nodes connected |
| VCF Operations | Login to `https://vcf-ops.lab.dreamfold.dev` | Dashboard shows management domain |
| VCF Automation | Login to `https://vcf-auto.lab.dreamfold.dev` | Console accessible |

## 7. Phase 4 — VCF Workload Domain

> Phase 4 implements R-004 via VCF-01, VCF-02. Workload hosts are commissioned into the free pool and a VI workload domain is created.

### 7.1 Commission Hosts

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.1.1 | In SDDC Manager, navigate to Hosts → Commission | Commission wizard opens | — |
| 8.1.2 | Add esxi-05, esxi-06, esxi-07 to free pool | Hosts commissioning | Task progress visible |
| 8.1.3 | Wait for host validation and commissioning | Hosts in free pool | SDDC Manager shows 3 hosts available |

### 7.2 Create Workload Domain

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.2.1 | In SDDC Manager, navigate to Domains → Add Domain | Create domain wizard opens | — |
| 7.2.2 | Configure workload domain with 3 hosts, vSAN storage | Domain configuration accepted | Validation passes |
| 7.2.3 | Specify vcenter-wld (10.0.10.9) and nsx-mgr-wld (10.0.10.10) | Appliance config accepted | — |
| 7.2.4 | Start domain creation | Deployment begins | Task progress visible |
| 7.2.5 | Wait for workload domain deployment (60-90 minutes) | Domain created | SDDC Manager shows Active |

### 7.3 Workload Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Workload vCenter | Login to `https://vcenter-wld.lab.dreamfold.dev` | Cluster shows 3 hosts, all connected |
| Workload vSAN | vCenter → Cluster → Monitor → vSAN → Health | All checks green |
| Workload NSX | Login to `https://nsx-mgr-wld.lab.dreamfold.dev` | Dashboard accessible |
| Transport nodes | NSX Manager → System → Fabric → Nodes | 3 host transport nodes configured |
| SDDC Manager | Domains overview | Both domains show Active |

### 7.4 Configure Keycloak OpenID Connect (OIDC) via VCF Identity Broker

Keycloak was deployed in Phase 1 by the `docker_services` role with the lab realm, users, and OIDC clients already configured. Now that the workload domain exists, register Keycloak as the external identity provider with the **VCF Identity Broker**. The Identity Broker federates authentication across all VCF products (vCenter, NSX Manager, SDDC Manager) — you configure the OIDC provider once in the broker, and it propagates to the integrated products.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.4.1 | In SDDC Manager → Administration → Identity Providers, register Keycloak as an OIDC provider | Provider configured |
| 7.4.2 | Set Discovery Endpoint to `https://gateway.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration` | Metadata fetched |
| 7.4.3 | Set Client ID and provide client secret from Keycloak admin console | Credentials accepted |
| 7.4.4 | Map Keycloak groups to VCF roles (admin, read-only, etc.) | Role mappings created |
| 7.4.5 | Test SSO login with `lab-admin` user via management vCenter | vCenter dashboard loads |
| 7.4.6 | Test SSO login with `lab-admin` user via NSX Manager | NSX dashboard loads |
| 7.4.7 | Verify Identity Broker shows both management and workload domains federated | All products listed |

## 8. Phase 5 — NSX Networking

> Phase 5 implements R-006, R-008 via NET-02, NSX-01 through NSX-04. Edge cluster, gateways, BGP, and VPC are configured.

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
| 8.1.1 | In workload NSX Manager, navigate to System → Fabric → Edge Clusters | Edge management page | — |
| 8.1.2 | Deploy edge-01 (Large, 8 vCPU, 32 GB RAM) with management IP 10.0.10.20 | Edge VM deployed | `ping 10.0.10.20` |
| 8.1.3 | Deploy edge-02 (Large) with management IP 10.0.10.21 | Edge VM deployed | `ping 10.0.10.21` |
| 8.1.4 | Configure Edge Tunnel Endpoint (TEP) interfaces on VLAN 50 (10.0.50.20, 10.0.50.21) | TEP connectivity | Edge transport node status: Up |
| 8.1.5 | Create Edge cluster with both Edge VMs | Edge cluster created | NSX Manager shows cluster healthy |

### 8.2 Configure Tier-0 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.2.1 | Create Tier-0 gateway (Active-Standby, linked to Edge cluster) | Tier-0 created | Gateway shows Realised |
| 8.2.2 | Add uplink interface on VLAN 60, IP 10.0.60.2/24 | Uplink configured | Interface status: Up |
| 8.2.3 | Configure BGP: ASN 65001, neighbor 10.0.60.1 (ASN 65000), keepalive 60s, hold 180s | BGP configured | — |
| 8.2.4 | Enable route redistribution (connected subnets, NAT) | Routes advertised | — |

### 8.3 Configure BGP on Gateway (FRR)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.3.1 | SSH to gateway | CLI access | — |
| 8.3.2 | Verify FRR BGP configuration deployed by Ansible | BGP configured | `vtysh -c 'show ip bgp summary'` |
| 8.3.3 | Verify BGP adjacency established | Session state: Established | `vtysh -c 'show ip bgp summary'` shows Established |
| 8.3.4 | Verify route exchange | Routes received from NSX | `vtysh -c 'show ip bgp'` shows VPC prefixes |

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
| 8.4.1 | Create Tier-1 gateway linked to Tier-0 | Tier-1 created | Gateway shows Realised |
| 8.4.2 | Configure route advertisement (connected subnets, NAT IPs, LB VIPs) | Advertisements enabled | — |

### 8.5 Configure NSX VPC

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.1 | Create VPC project in NSX Manager | Project created | — |
| 8.5.2 | Create VPC (vks-vpc) with centralised connectivity | VPC created | VPC shows Realised |
| 8.5.3 | Configure external connectivity via Tier-0 | Routing configured | — |
| 8.5.4 | Configure Source Network Address Translation (SNAT) on Tier-0 for outbound VPC traffic | NAT rules active | See SNAT steps below |

#### Configure SNAT Rules on Tier-0

Two SNAT rules are required — one for the VKS pod CIDR and one for the service CIDR. Both translate outbound traffic to the Tier-0 uplink IP (10.0.60.2) so that external networks can route return traffic.

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.4a | In NSX Manager, navigate to Networking → NAT → tier0-gateway | NAT rules page | — |
| 8.5.4b | Add SNAT rule: source 192.168.0.0/16 → translated IP 10.0.60.2 | Rule created | Rule shows Active |
| 8.5.4c | Add SNAT rule: source 10.96.0.0/12 → translated IP 10.0.60.2 | Rule created | Rule shows Active |
| 8.5.4d | Verify NAT rules are realised | Both rules Active | NSX Manager → NAT → tier0-gateway shows 2 SNAT rules |

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
| BGP adjacency | `vtysh -c 'show ip bgp summary'` on gateway | Established with 10.0.60.2 |
| Routes from NSX | `vtysh -c 'show ip bgp'` on gateway | VPC/overlay prefixes received |
| Routes from gateway | NSX Manager → Networking → Tier-0 → Routing Table | Infrastructure subnets received |
| Edge cluster health | NSX Manager → System → Fabric → Edge Clusters | Both Edges Up |
| Tier-0 status | NSX Manager → Networking → Tier-0 Gateways | Realised, interfaces Up |
| VPC status | NSX Manager → VPC overview | vks-vpc shows Realised |

## 9. Phase 6 — VKS

> Phase 6 implements R-005 via VKS-01 through VKS-04. Supervisor enablement, namespace creation, and VKS cluster deployment.

### 9.1 Create Content Library

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.1.1 | In workload vCenter, navigate to Content Libraries | Library management page | — |
| 9.1.2 | Create subscribed library pointing to VMware Kubernetes Runtime (VKr) endpoint | Library created | Sync status: Active |
| 9.1.3 | Wait for initial sync to complete | VKr images available | At least one Kubernetes version listed |

### 9.2 Enable Supervisor

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.2.1 | In workload vCenter, navigate to Workload Management | Supervisor setup wizard | — |
| 9.2.2 | Select workload domain cluster | Cluster selected | — |
| 9.2.3 | Configure networking: NSX, management network, workload network | Networking configured | — |
| 9.2.4 | Configure storage: vSAN Default policy | Storage configured | — |
| 9.2.5 | Start Supervisor enablement | Deployment begins | Task progress visible |
| 9.2.6 | Wait for Supervisor deployment (30-45 minutes) | Supervisor running | Status: Running |

### 9.3 Create vSphere Namespace

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.3.1 | In workload vCenter, navigate to Workload Management → Namespaces | Namespace management | — |
| 9.3.2 | Create namespace "vks-workloads" | Namespace created | Status: Active |
| 9.3.3 | Assign VM classes: best-effort-small, best-effort-medium | VM classes assigned | Listed under namespace |
| 9.3.4 | Assign storage policies: vSAN Default | Storage assigned | Listed under namespace |
| 9.3.5 | Assign content library: VKS Kubernetes releases | Library assigned | Listed under namespace |

### 9.4 Deploy VKS Cluster

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.4.1 | Connect to Supervisor API (`kubectl vsphere login`) | Authenticated | Kubeconfig obtained |
| 9.4.2 | Switch to vks-workloads namespace | Namespace active | `kubectl get ns` |
| 9.4.3 | Apply VKS cluster manifest (Cluster v1beta1) | Cluster creation initiated | `kubectl get cluster` shows Provisioning |
| 9.4.4 | Wait for control plane nodes (3x) | Control plane ready | `kubectl get machines` shows 3 Running |
| 9.4.5 | Wait for worker nodes (3x) | Workers ready | `kubectl get machines` shows 6 Running |
| 9.4.6 | Obtain VKS cluster kubeconfig | Kubeconfig available | `kubectl get secret` |

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
| 9.4a.1 | Login to VKS cluster | Authenticated | `kubectl get nodes` shows 6 nodes |
| 9.4a.2 | Verify StorageClass exists | StorageClass listed | `kubectl get storageclass` shows `vsan-default-storage-policy` |
| 9.4a.3 | Create test PVC (1 Gi) | PVC bound | `kubectl get pvc` shows Bound |
| 9.4a.4 | Verify PV created on vSAN | FCD visible | vCenter → Datastores → vSAN → Monitor → Virtual Objects |
| 9.4a.5 | Delete test PVC | PVC and PV deleted | `kubectl get pv` shows no orphaned PVs |

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
| 9.5.1 | Login to VKS cluster using obtained kubeconfig | Authenticated | `kubectl get nodes` shows 6 nodes |
| 9.5.2 | Deploy nginx test deployment | Pods running | `kubectl get pods` shows Running |
| 9.5.3 | Expose via LoadBalancer service | External IP assigned | `kubectl get svc` shows EXTERNAL-IP |
| 9.5.4 | Access nginx from gateway | Page loads | `curl http://<EXTERNAL-IP>` returns nginx welcome |

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

## 10. Ready for Operations Testing

Final verification checklist before the lab is considered operational.

### 10.1 Infrastructure Services

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 1 | External RDP access | RDP to gateway public IP | Desktop loads | ☐ |
| 2 | DNS forward resolution | `dig @10.0.10.1 vcenter-mgmt.lab.dreamfold.dev` | Returns 10.0.10.4 | ☐ |
| 3 | DNS reverse resolution | `dig @10.0.10.1 -x 10.0.10.4` | Returns vcenter-mgmt.lab.dreamfold.dev | ☐ |
| 4 | NTP synchronisation | `chronyc sources` on gateway | Upstream servers reachable | ☐ |
| 5 | CA health | `step ca health` on gateway | Returns "ok" | ☐ |
| 6 | Inter-VLAN routing | `ping 10.0.20.1` from an ESXi host | Success | ☐ |

### 10.2 VCF Platform

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 7 | Management vCenter | Browse `https://vcenter-mgmt.lab.dreamfold.dev` | Login page loads | ☐ |
| 8 | Workload vCenter | Browse `https://vcenter-wld.lab.dreamfold.dev` | Login page loads | ☐ |
| 9 | SDDC Manager | Browse `https://sddc-manager.lab.dreamfold.dev` | Both domains Active | ☐ |
| 10 | Management vSAN health | vCenter → Cluster → vSAN Health | All green | ☐ |
| 11 | Workload vSAN health | vCenter → Cluster → vSAN Health | All green | ☐ |
| 12 | All ESXi hosts connected | Both vCenters show hosts Connected | 4 mgmt + 3 wld | ☐ |

### 10.3 NSX Networking

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 13 | BGP adjacency | `vtysh -c 'show ip bgp summary'` on gateway | Established | ☐ |
| 14 | Route exchange | `vtysh -c 'show ip bgp'` on gateway | VPC prefixes received | ☐ |
| 15 | Edge cluster health | NSX Manager → Edge Clusters | Both Edges Up | ☐ |
| 16 | Tier-0 status | NSX Manager → Tier-0 Gateways | Realised | ☐ |
| 17 | VPC status | NSX Manager → VPC | Realised | ☐ |

### 10.4 VKS

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 18 | Supervisor status | vCenter → Workload Management | Running | ☐ |
| 19 | VKS cluster health | `kubectl get cluster vks-cluster-01` | Phase: Provisioned | ☐ |
| 20 | All nodes ready | `kubectl get nodes` on VKS cluster | 6 nodes Ready | ☐ |
| 21 | Test workload | `curl http://<nginx-lb-ip>` | nginx welcome page | ☐ |
| 22 | Pod-to-external | `kubectl exec` into pod, `curl google.com` | Response received | ☐ |
