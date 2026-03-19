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
| 3.1.1 | Create new vApp in vCloud Director | An empty vApp is created in the target VDC |
| 3.1.2 | Add routed network (public) to vApp | External connectivity is available via the public network |
| 3.1.3 | Add isolated network: name `lab-trunk`, gateway CIDR `192.168.254.1/24`, tick **Allow Guest VLAN** | A trunk-capable internal network is available for VLAN traffic |

### 3.2 Deploy Gateway VM (Manual in vCD)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.2.1 | Create Ubuntu 24.04 VM from Content Hub ISO (2 vCPU, 10 GB RAM, 60 GB disk) with NIC1 on Public network, NIC2 on lab-trunk | The gateway VM is created with the specified configuration | The VM is visible in the vApp inventory |
| 3.2.2 | Power on and complete Ubuntu installer via vCD console — set server name `gateway`, username `ubuntu`, password from 1Password "Lab Bootstrap" item | Ubuntu 24.04 is installed on the gateway VM | A login prompt appears on the vCD console |
| 3.2.3 | Run `apt update && apt upgrade -y` to bring the OS up to date | All packages are updated to the latest versions | `apt list --upgradable` shows no pending updates |

### 3.3 Stage SDDC Manager OVA on Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.3.1 | Download `VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova` (2.03 GB) from support.broadcom.com to operator laptop | The OVA file is saved to the operator laptop | The file exists on the operator laptop |
| 3.3.2 | Note public IP assigned by DHCP to NIC1 (ens160): `ip addr show ens160` | The public IP address is obtained | — |
| 3.3.3 | SCP OVA from laptop to gateway: `scp VCF-SDDC-Manager-Appliance-9.0.2.0.25151285.ova ubuntu@<gateway-ip>:~/vcf-installer.ova` | The OVA file is transferred to the gateway | `ls -lh ~/vcf-installer.ova` shows 2.03 GB |

### 3.4 Clone ESXi VMs (Manual in vCD)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.4.1 | Clone esxi-01 through esxi-04 from vApp template `[baked]esxi-9.0.2-2514807` (48 vCPU, 128 GB RAM, 40 GB boot Non-Volatile Memory Express (NVMe) + 200 GB vSAN NVMe), both NICs on `lab-trunk` | The four management ESXi VMs are cloning from the template |
| 3.4.2 | Clone esxi-05 through esxi-07 (same spec), both NICs on `lab-trunk` | The three workload ESXi VMs are cloning from the template |

### 3.5 Power Off and Save to Catalog

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.5.1 | Power off all 8 VMs (gateway + 7 ESXi) | All 8 VMs are stopped | The vApp shows all VMs powered off |
| 3.5.2 | In vCD, right-click vApp → Add to Catalog. Name: `[baseline]vcf-lab-8vm`, storage policy: `ProvisioningStoragePolicy-provider01` | The vApp template is created in the catalog | The catalog shows the new template |
| 3.5.3 | Verify template is visible in catalog and contains 8 VMs | The template is valid and contains all expected VMs | Opening template details confirms 8 VMs are listed |

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
| 4.2.1 | In vCD catalog, deploy vApp from template `[baseline]vcf-lab-8vm` | A vApp is created containing all 8 VMs | The vApp is visible with all VMs listed |
| 4.2.2 | Read back MAC addresses from vCD for all 7 ESXi VMs (vmnic0), update `esxi_mac` in `ansible/inventory/hosts.yml` | MAC addresses are recorded for all 7 ESXi VMs | The inventory file is updated with the new MAC addresses |
| 4.2.3 | Power on all 8 VMs | All 8 VMs are running | The gateway obtains a public IP via Dynamic Host Configuration Protocol (DHCP) |
| 4.2.4 | Note gateway public IP: `ip addr show ens160` via vCD console | The public IP address is obtained | — |
| 4.2.5 | Store gateway IP in 1Password: `op item edit "Lab Bootstrap" ip_address=<gateway-ip>` | The gateway IP is stored in 1Password | `op item get "Lab Bootstrap" --fields ip_address` returns the IP |
| 4.2.6 | If no SSH key exists, generate one: `ssh-keygen -t ed25519` | An ed25519 key pair is created | `~/.ssh/id_ed25519.pub` exists |
| 4.2.7 | Copy SSH key to gateway: `ssh-copy-id ubuntu@<gateway-ip>` | The SSH public key is deployed to the gateway | `ssh ubuntu@<gateway-ip>` connects without a password prompt |

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
| Gateway external access | RDP to gateway public IP | The XFCE desktop is accessible via RDP |
| Gateway DNS | `dig @10.0.10.1 gateway.lab.dreamfold.dev` | The query returns 10.0.10.1 |
| Gateway NTP | `chronyc sources` | Chrony shows upstream NTP servers synchronised |
| Gateway CA | `step ca health` | The health check returns "ok" |
| Management IP | `ip addr show ens192` on gateway | The interface shows 10.0.10.1/24 on the native (untagged) VLAN |
| VLAN sub-interfaces | `ip addr show ens192.20` on gateway | The sub-interface shows 10.0.20.1/24 (vMotion) |
| Inter-VLAN routing | `ping 10.0.20.1` from a host on VLAN 10 | The ping succeeds |
| FRR BGP | `vtysh -c 'show ip bgp summary'` on gateway | The FRR BGP process is running and shows neighbour status |

## 5. Phase 2 — Nested ESXi

> Phase 2 implements R-004, R-007 via ESX-01 through ESX-04 and NET-03, NET-04.

### 5.1 Configure ESXi Hosts (Manual)

ESXi hosts receive their management IP via DHCP from the gateway dnsmasq (configured in Phase 1). MAC addresses were recorded during Phase 1 template deployment (§4.2.2).

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.1.1 | On each host via Direct Console User Interface (DCUI): Troubleshooting Options → Enable SSH | SSH is enabled on the host | `ssh root@<ip>` connects successfully |
| 5.1.2 | On each host via DCUI: set root password to match 1Password "Lab Bootstrap" item | The root password is set | SSH login with the bootstrap password succeeds |

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
| All hosts reachable | `ping 10.0.10.{11..17}` from gateway | All seven hosts respond to ping |
| DNS resolution | `nslookup esxi-01.lab.dreamfold.dev 10.0.10.1` | The query returns the correct IP for each host |
| Reverse DNS | `nslookup 10.0.10.11 10.0.10.1` | The query returns esxi-01.lab.dreamfold.dev |
| NTP sync | `esxcli system ntp get` on each host | NTP is configured with server 10.0.10.1 |
| Time sync | Compare time across all hosts | Time across all hosts is within 1 second |
| vSAN ESA ready | `esxcli vsan storage list` on each host | The NVMe device is marked as SSD |
| Host status | `cd ansible && ansible-playbook playbooks/phase2_esxi.yml --check` | All tasks report ok with no changes required |

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
| 6.2.1 | Upload OVA from gateway to esxi-01 datastore: `scp ~/vcf-installer.ova root@esxi-01:…` or ESXi Host Client | The OVA is available on the esxi-01 datastore | The datastore browser shows the OVA file |
| 6.2.2 | Deploy VCF Installer OVA with IP 10.0.10.3, GW 10.0.10.1, DNS 10.0.10.1 | The VCF Installer appliance is deployed and powered on | The VM is powered on in the ESXi Host Client |
| 6.2.3 | Wait for installer services to start (5-10 minutes) | All installer services are ready | `https://vcf-installer.lab.dreamfold.dev` is accessible |

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
| 6.3.1 | Access VCF Installer UI at `https://vcf-installer.lab.dreamfold.dev` | The VCF Installer login page is displayed | The browser loads the login page |
| 6.3.2 | The `vcf_bringup` Ansible role validates and submits the deployment specification to the VCF Installer API | The deployment parameters are validated without errors | No validation errors are reported |
| 6.3.3 | Start bringup workflow | The bringup deployment begins | The progress bar is advancing |
| 6.3.4 | Wait for vCenter deployment | The vCenter Server is deployed successfully | `https://vcenter-mgmt.lab.dreamfold.dev` is accessible |
| 6.3.5 | Wait for VDS and vSAN configuration | Networking and storage are configured | vSAN health shows green in vCenter |
| 6.3.6 | Wait for SDDC Manager deployment | SDDC Manager is deployed successfully | `https://sddc-manager.lab.dreamfold.dev` is accessible |
| 6.3.7 | Wait for NSX Manager deployment | NSX Manager is deployed successfully | `https://nsx-mgr-mgmt.lab.dreamfold.dev` is accessible |
| 6.3.8 | Bringup completes | The management domain is operational | SDDC Manager shows the management domain as healthy |

### 6.4 Post-Bringup Deployments

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.4.1 | Deploy VCF Operations from SDDC Manager | VCF Operations is deployed successfully | `https://vcf-ops.lab.dreamfold.dev` is accessible |
| 6.4.2 | Deploy VCF Automation from SDDC Manager | VCF Automation is deployed successfully | `https://vcf-auto.lab.dreamfold.dev` is accessible |
| 6.4.3 | Remove VCF Installer VM (no longer needed) | Resources are reclaimed from the VCF Installer VM | The VM is deleted from the inventory |

### 6.5 Management Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| vCenter health | Login to `https://vcenter-mgmt.lab.dreamfold.dev` | The cluster shows 4 hosts, all in a connected state |
| vSAN health | vCenter → Cluster → Monitor → vSAN → Health | All vSAN health checks are green |
| SDDC Manager | Login to `https://sddc-manager.lab.dreamfold.dev` | The management domain shows Active status |
| NSX Manager | Login to `https://nsx-mgr-mgmt.lab.dreamfold.dev` | The dashboard is accessible and all transport nodes are connected |
| VCF Operations | Login to `https://vcf-ops.lab.dreamfold.dev` | The dashboard shows the management domain |
| VCF Automation | Login to `https://vcf-auto.lab.dreamfold.dev` | The console is accessible |

## 7. Phase 4 — VCF Workload Domain

> Phase 4 implements R-004 via VCF-01, VCF-02. Workload hosts are commissioned into the free pool and a VI workload domain is created.

### 7.1 Commission Hosts

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.1.1 | In SDDC Manager, navigate to Hosts → Commission | The host commission wizard opens | — |
| 7.1.2 | Add esxi-05, esxi-06, esxi-07 to free pool | The three hosts begin commissioning | Task progress is visible in the SDDC Manager UI |
| 7.1.3 | Wait for host validation and commissioning | All three hosts are in the free pool | SDDC Manager shows 3 hosts available in the free pool |

### 7.2 Create Workload Domain

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7.2.1 | In SDDC Manager, navigate to Domains → Add Domain | The create domain wizard opens | — |
| 7.2.2 | Configure workload domain with 3 hosts, vSAN storage | The domain configuration is accepted | Validation passes without errors |
| 7.2.3 | Specify vcenter-wld (10.0.10.9) and nsx-mgr-wld (10.0.10.10) | The appliance configuration is accepted | — |
| 7.2.4 | Start domain creation | The domain deployment begins | Task progress is visible in the SDDC Manager UI |
| 7.2.5 | Wait for workload domain deployment (60-90 minutes) | The workload domain is created | SDDC Manager shows the domain as Active |

### 7.3 Workload Domain Verification

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Workload vCenter | Login to `https://vcenter-wld.lab.dreamfold.dev` | The cluster shows 3 hosts, all in a connected state |
| Workload vSAN | vCenter → Cluster → Monitor → vSAN → Health | All vSAN health checks are green |
| Workload NSX | Login to `https://nsx-mgr-wld.lab.dreamfold.dev` | The NSX Manager dashboard is accessible |
| Transport nodes | NSX Manager → System → Fabric → Nodes | Three host transport nodes are configured and connected |
| SDDC Manager | Domains overview | Both management and workload domains show Active status |

### 7.4 Configure Keycloak OpenID Connect (OIDC) via VCF Identity Broker

Keycloak was deployed in Phase 1 by the `docker_services` role with the lab realm, users, and OIDC clients already configured. Now that the workload domain exists, register Keycloak as the external identity provider with the **VCF Identity Broker**. The Identity Broker federates authentication across all VCF products (vCenter, NSX Manager, SDDC Manager) — you configure the OIDC provider once in the broker, and it propagates to the integrated products.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.4.1 | In SDDC Manager → Administration → Identity Providers, register Keycloak as an OIDC provider | The OIDC provider is configured in the Identity Broker |
| 7.4.2 | Set Discovery Endpoint to `https://gateway.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration` | The OIDC metadata is fetched from Keycloak |
| 7.4.3 | Set Client ID and provide client secret from Keycloak admin console | The client credentials are accepted |
| 7.4.4 | Map Keycloak groups to VCF roles (admin, read-only, etc.) | The role mappings are created |
| 7.4.5 | Test SSO login with `lab-admin` user via management vCenter | The vCenter dashboard loads after SSO login |
| 7.4.6 | Test SSO login with `lab-admin` user via NSX Manager | The NSX Manager dashboard loads after SSO login |
| 7.4.7 | Verify Identity Broker shows both management and workload domains federated | All federated products are listed in the Identity Broker |

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
| 8.1.1 | In workload NSX Manager, navigate to System → Fabric → Edge Clusters | The Edge management page is displayed | — |
| 8.1.2 | Deploy edge-01 (Large, 8 vCPU, 32 GB RAM) with management IP 10.0.10.20 | The edge-01 VM is deployed and powered on | `ping 10.0.10.20` succeeds |
| 8.1.3 | Deploy edge-02 (Large) with management IP 10.0.10.21 | The edge-02 VM is deployed and powered on | `ping 10.0.10.21` succeeds |
| 8.1.4 | Configure Edge Tunnel Endpoint (TEP) interfaces on VLAN 50 (10.0.50.20, 10.0.50.21) | TEP connectivity is established between the Edge nodes | The Edge transport node status shows Up |
| 8.1.5 | Create Edge cluster with both Edge VMs | The Edge cluster is created with both Edge VMs | NSX Manager shows the Edge cluster as healthy |

### 8.2 Configure Tier-0 Gateway

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.2.1 | Create Tier-0 gateway (Active-Standby, linked to Edge cluster) | The NSX Tier-0 Gateway is created | The gateway status shows Realised in NSX Manager |
| 8.2.2 | Add uplink interface on VLAN 60, IP 10.0.60.2/24 | The uplink interface is configured | The interface status shows Up |
| 8.2.3 | Configure BGP: ASN 65001, neighbor 10.0.60.1 (ASN 65000), keepalive 60s, hold 180s | BGP peering is configured on the Tier-0 Gateway | — |
| 8.2.4 | Enable route redistribution (connected subnets, NAT) | Connected and NAT routes are advertised | — |

### 8.3 Configure BGP on Gateway (FRR)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.3.1 | SSH to gateway | CLI access to the gateway is established | — |
| 8.3.2 | Verify FRR BGP configuration deployed by Ansible | The FRR BGP configuration is in place | `vtysh -c 'show ip bgp summary'` shows the configuration |
| 8.3.3 | Verify BGP adjacency established | The BGP session state is Established | `vtysh -c 'show ip bgp summary'` shows Established |
| 8.3.4 | Verify route exchange | Routes are received from the NSX Tier-0 Gateway | `vtysh -c 'show ip bgp'` shows VPC prefixes |

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
| 8.4.1 | Create Tier-1 gateway linked to Tier-0 | The NSX Tier-1 Gateway is created and linked to the Tier-0 | The gateway status shows Realised in NSX Manager |
| 8.4.2 | Configure route advertisement (connected subnets, NAT IPs, LB VIPs) | Route advertisements are enabled | — |

### 8.5 Configure NSX VPC

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 8.5.1 | Create VPC project in NSX Manager | The VPC project is created in NSX Manager | — |
| 8.5.2 | Create VPC (vks-vpc) with centralised connectivity | The VPC is created with centralised connectivity | The VPC status shows Realised |
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
| BGP adjacency | `vtysh -c 'show ip bgp summary'` on gateway | The BGP session is Established with 10.0.60.2 |
| Routes from NSX | `vtysh -c 'show ip bgp'` on gateway | VPC and overlay prefixes are received |
| Routes from gateway | NSX Manager → Networking → Tier-0 → Routing Table | Infrastructure subnets are received from the gateway |
| Edge cluster health | NSX Manager → System → Fabric → Edge Clusters | Both Edge nodes show Up status |
| Tier-0 status | NSX Manager → Networking → Tier-0 Gateways | The Tier-0 status is Realised with all interfaces Up |
| VPC status | NSX Manager → VPC overview | The vks-vpc status shows Realised |

## 9. Phase 6 — VKS

> Phase 6 implements R-005 via VKS-01 through VKS-04. Supervisor enablement, namespace creation, and VKS cluster deployment.

### 9.1 Create Content Library

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.1.1 | In workload vCenter, navigate to Content Libraries | The content library management page is displayed | — |
| 9.1.2 | Create subscribed library pointing to VMware Kubernetes Runtime (VKr) endpoint | The subscribed content library is created | The sync status shows Active |
| 9.1.3 | Wait for initial sync to complete | VKr images are available in the library | At least one Kubernetes version is listed |

### 9.2 Enable Supervisor

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.2.1 | In workload vCenter, navigate to Workload Management | The Supervisor setup wizard is displayed | — |
| 9.2.2 | Select workload domain cluster | The workload cluster is selected | — |
| 9.2.3 | Configure networking: NSX, management network, workload network | The networking stack is configured | — |
| 9.2.4 | Configure storage: vSAN Default policy | The storage policy is configured | — |
| 9.2.5 | Start Supervisor enablement | The Supervisor deployment begins | Task progress is visible in the vCenter UI |
| 9.2.6 | Wait for Supervisor deployment (30-45 minutes) | The vSphere Supervisor is running | The Supervisor status shows Running |

### 9.3 Create vSphere Namespace

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.3.1 | In workload vCenter, navigate to Workload Management → Namespaces | The namespace management page is displayed | — |
| 9.3.2 | Create namespace "vks-workloads" | The vks-workloads namespace is created | The namespace status shows Active |
| 9.3.3 | Assign VM classes: best-effort-small, best-effort-medium | The VM classes are assigned to the namespace | The assigned classes are listed under the namespace |
| 9.3.4 | Assign storage policies: vSAN Default | The storage policy is assigned to the namespace | The assigned policy is listed under the namespace |
| 9.3.5 | Assign content library: VKS Kubernetes releases | The content library is assigned to the namespace | The assigned library is listed under the namespace |

### 9.4 Deploy VKS Cluster

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 9.4.1 | Connect to Supervisor API (`kubectl vsphere login`) | Authentication to the Supervisor API succeeds | A kubeconfig file is obtained |
| 9.4.2 | Switch to vks-workloads namespace | The vks-workloads namespace context is active | `kubectl get ns` shows the namespace |
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
| 1 | External RDP access | RDP to gateway public IP | The XFCE desktop loads via RDP | ☐ |
| 2 | DNS forward resolution | `dig @10.0.10.1 vcenter-mgmt.lab.dreamfold.dev` | The query returns 10.0.10.4 | ☐ |
| 3 | DNS reverse resolution | `dig @10.0.10.1 -x 10.0.10.4` | The query returns vcenter-mgmt.lab.dreamfold.dev | ☐ |
| 4 | NTP synchronisation | `chronyc sources` on gateway | Upstream NTP servers are reachable | ☐ |
| 5 | CA health | `step ca health` on gateway | The health check returns "ok" | ☐ |
| 6 | Inter-VLAN routing | `ping 10.0.20.1` from an ESXi host | The ping succeeds | ☐ |

### 10.2 VCF Platform

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 7 | Management vCenter | Browse `https://vcenter-mgmt.lab.dreamfold.dev` | The login page loads | ☐ |
| 8 | Workload vCenter | Browse `https://vcenter-wld.lab.dreamfold.dev` | The login page loads | ☐ |
| 9 | SDDC Manager | Browse `https://sddc-manager.lab.dreamfold.dev` | Both domains show Active status | ☐ |
| 10 | Management vSAN health | vCenter → Cluster → vSAN Health | All vSAN health checks are green | ☐ |
| 11 | Workload vSAN health | vCenter → Cluster → vSAN Health | All vSAN health checks are green | ☐ |
| 12 | All ESXi hosts connected | Both vCenters show hosts Connected | All hosts are connected (4 management + 3 workload) | ☐ |

### 10.3 NSX Networking

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 13 | BGP adjacency | `vtysh -c 'show ip bgp summary'` on gateway | The BGP session is Established | ☐ |
| 14 | Route exchange | `vtysh -c 'show ip bgp'` on gateway | VPC prefixes are received from the NSX Tier-0 | ☐ |
| 15 | Edge cluster health | NSX Manager → Edge Clusters | Both Edge nodes show Up status | ☐ |
| 16 | Tier-0 status | NSX Manager → Tier-0 Gateways | The Tier-0 status is Realised | ☐ |
| 17 | VPC status | NSX Manager → VPC | The VPC status is Realised | ☐ |

### 10.4 VKS

| # | Check | Method | Expected Result | Pass |
|---|-------|--------|-----------------|------|
| 18 | Supervisor status | vCenter → Workload Management | The Supervisor status shows Running | ☐ |
| 19 | VKS cluster health | `kubectl get cluster vks-cluster-01` | The cluster phase shows Provisioned | ☐ |
| 20 | All nodes ready | `kubectl get nodes` on VKS cluster | All 6 nodes show Ready status | ☐ |
| 21 | Test workload | `curl http://<nginx-lb-ip>` | The nginx welcome page is returned | ☐ |
| 22 | Pod-to-external | `kubectl exec` into pod, `curl google.com` | A response is received from the external site | ☐ |
