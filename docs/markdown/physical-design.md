---
title: "VKS Lab"
subtitle: "Physical Design"
author: "dreamfold"
date: "March 2026"
---

# Physical Design

## 1. VLAN & Subnet Table

> Implements NET-03 (six-Virtual LAN (VLAN) segmentation) and NET-04 (jumbo frames for overlay/storage). See [Logical Design](logical-design.md) Section 3.

| VLAN ID | Name | Subnet | Purpose | Maximum Transmission Unit (MTU) |
|---------|------|--------|---------|-----|
| 10 | Management | 10.0.10.0/24 | ESXi management, vCenter, Software-Defined Data Center (SDDC) Manager, VMware Cloud Foundation (VCF) Networking (NSX) Manager | 1500 |
| 20 | vMotion | 10.0.20.0/24 | vMotion traffic | 9000 |
| 30 | vSAN | 10.0.30.0/24 | vSAN storage traffic | 9000 |
| 40 | Host Overlay (TEP) | 10.0.40.0/24 | NSX host Tunnel Endpoint (TEP) tunnels | 9000 |
| 50 | Edge Overlay | 10.0.50.0/24 | NSX Edge TEP tunnels | 9000 |
| 60 | Edge Uplink | 10.0.60.0/24 | NSX Tier-0 Gateway ↔ Gateway Border Gateway Protocol (BGP) peering | 1500 |

## 2. IP Addressing Scheme

### Infrastructure Services (VLAN 10 — Management)

| IP Address | Hostname | Role |
|------------|----------|------|
| 10.0.10.1 | gateway | Gateway VLAN 10 sub-interface (default gateway) |
| 10.0.10.3 | vcf-installer | VMware Cloud Foundation (VCF) Installer appliance |
| 10.0.10.4 | vcenter-mgmt | vCenter Server (management) |
| 10.0.10.5 | sddc-manager | SDDC Manager |
| 10.0.10.6 | nsx-mgr-mgmt | NSX Manager (management) |
| 10.0.10.7 | vcf-ops | VCF Operations |
| 10.0.10.8 | vcf-auto | VCF Automation |
| 10.0.10.9 | vcenter-wld | vCenter Server (workload) |
| 10.0.10.10 | nsx-mgr-wld | NSX Manager (workload) |
| 10.0.10.11 | esxi-01 | Management domain ESXi host |
| 10.0.10.12 | esxi-02 | Management domain ESXi host |
| 10.0.10.13 | esxi-03 | Management domain ESXi host |
| 10.0.10.14 | esxi-04 | Management domain ESXi host |
| 10.0.10.15 | esxi-05 | Workload domain ESXi host |
| 10.0.10.16 | esxi-06 | Workload domain ESXi host |
| 10.0.10.17 | esxi-07 | Workload domain ESXi host |
| 10.0.10.20 | edge-01 | NSX Edge VM (management interface) |
| 10.0.10.21 | edge-02 | NSX Edge VM (management interface) |

### vMotion (VLAN 20)

| IP Range | Purpose |
|----------|---------|
| 10.0.20.11–14 | Management domain ESXi hosts |
| 10.0.20.15–17 | Workload domain ESXi hosts |

### vSAN (VLAN 30)

| IP Range | Purpose |
|----------|---------|
| 10.0.30.11–14 | Management domain ESXi hosts |
| 10.0.30.15–17 | Workload domain ESXi hosts |

### Host Overlay TEP (VLAN 40)

| IP Range | Purpose |
|----------|---------|
| 10.0.40.11–17 | ESXi host TEP interfaces (pool) |

### Edge Overlay TEP (VLAN 50)

| IP Range | Purpose |
|----------|---------|
| 10.0.50.20–21 | NSX Edge TEP interfaces |

### Edge Uplink / BGP (VLAN 60)

| IP Address | Role |
|------------|------|
| 10.0.60.1 | Gateway ens34.60 (BGP neighbor) |
| 10.0.60.2 | NSX Tier-0 uplink interface |

## 3. Ubuntu Gateway Specification

> Implements NET-01 (dual-homed single entry point), SVC-01 through SVC-06 (co-located infrastructure services). See [Logical Design](logical-design.md) Sections 3–4.

| Resource | Value |
|----------|-------|
| OS | Ubuntu 24.04 LTS |
| Desktop | GNOME + gnome-remote-desktop (Wayland-native RDP) |
| vCPU | 2 |
| RAM | 10 GB |
| Disk | 60 GB |
| NIC1 | vCD public network (Dynamic Host Configuration Protocol (DHCP) or static from vCD) |
| NIC2 | vCD private network — 802.1Q trunk (MTU 9000), VLAN sub-interfaces |

### Network Configuration

See [Delivery Guide](deliver.md) for netplan configuration. Key parameters:

- NIC1 (ens33): vCD public network, DHCP
- NIC2 (ens34): vCD private network, 802.1Q trunk (MTU 9000)
  - ens34: 10.0.10.1/24 (Management, native/untagged — ESXi DHCP works without VLAN config)
  - ens34.20: 10.0.20.1/24 (vMotion, MTU 9000)
  - ens34.30: 10.0.30.1/24 (vSAN, MTU 9000)
  - ens34.40: 10.0.40.1/24 (Host Overlay, MTU 9000)
  - ens34.50: 10.0.50.1/24 (Edge Overlay, MTU 9000)
  - ens34.60: 10.0.60.1/24 (Edge Uplink / BGP, MTU 1500)
- IP forwarding enabled — gateway is the inter-VLAN router
- FRR provides BGP peering with NSX Tier-0

### Services Configuration

| Service | Package | Config |
|---------|---------|--------|
| Domain Name System (DNS) | dnsmasq | Zone: `lab.dreamfold.dev`, upstream forwarder via NIC1 |
| DHCP | dnsmasq | Static MAC→IP reservations for ESXi hosts on VLAN 10 |
| Network Time Protocol (NTP) | chrony | `allow 10.0.0.0/16`, servers: public NTP pools |
| Certificate Authority (CA) | step-ca | Root CA for `lab.dreamfold.dev`, ACME enabled, max cert duration 8760h (1 year), listens on 127.0.0.1:443 |
| OpenID Connect (OIDC) | Keycloak (Docker) | Port 8443, external IdP; VCF Identity Broker federates SSO to all VCF components |
| Secrets | 1Password (operator laptop) | `community.general.onepassword` lookup plugin via 1Password CLI |
| Routing | Free Range Routing (FRR) (zebra + bgpd) | Inter-VLAN routing, BGP peering with NSX Tier-0 (ASN 65000) |
| Remote access | gnome-remote-desktop | Wayland-native RDP on port 3389; GDM3 auto-login |
| Web browser | Firefox | Access vCenter, NSX Manager, SDDC Manager UIs |

All VCF components point to 10.0.10.1 for DNS and NTP. systemd-resolved is disabled on the gateway to free port 53 for dnsmasq.

**CA certificate distribution**: The step-ca root certificate is fetched from the gateway to the Ansible controller during Phase 1, then pushed to each ESXi host during Phase 2 via `ansible.builtin.copy` and imported with `esxcli security cert import`. See [Logical Design](logical-design.md) SVC-10 and "Certificate Distribution" for details.

**DNS configuration**: dnsmasq listens on ens34 (management VLAN 10, native/untagged) for lab DNS/DHCP. The gateway's own `/etc/resolv.conf` points to upstream DNS (192.19.189.20) — not through its own dnsmasq — so that package installation and external resolution work independently of dnsmasq state.

### Dynamic Host Configuration Protocol (DHCP) Reservations (VLAN 10)

ESXi hosts receive their management IP via DHCP with static MAC→IP reservations. MAC addresses are assigned when creating the ESXi VMs in vCloud Director.

| MAC Address | Hostname | IP Address |
|-------------|----------|------------|
| 00:50:56:xx:xx:01 | esxi-01 | 10.0.10.11 |
| 00:50:56:xx:xx:02 | esxi-02 | 10.0.10.12 |
| 00:50:56:xx:xx:03 | esxi-03 | 10.0.10.13 |
| 00:50:56:xx:xx:04 | esxi-04 | 10.0.10.14 |
| 00:50:56:xx:xx:05 | esxi-05 | 10.0.10.15 |
| 00:50:56:xx:xx:06 | esxi-06 | 10.0.10.16 |
| 00:50:56:xx:xx:07 | esxi-07 | 10.0.10.17 |

> Replace `xx:xx` placeholders with actual MAC addresses from vCD after VM creation.

## 5. Nested ESXi Host Specification

> Implements ESX-01 (nested VMs on vCD), ESX-02 (4+3 host split), ESX-03 (vSAN ESA), ESX-04 (two-vNIC model). See [Logical Design](logical-design.md) Section 5.

### Management Domain Hosts (4x)

| Resource | Per Host | Total (4 hosts) |
|----------|----------|-----------------|
| vCPU | 48 | 192 |
| RAM | 128 GB | 512 GB |
| Disk (vSAN Non-Volatile Memory Express (NVMe)) | 200 GB | 800 GB |
| NICs | 2 (management + trunk) | — |
| ESXi Version | 9.0 | — |

### Workload Domain Hosts (3x)

| Resource | Per Host | Total (3 hosts) |
|----------|----------|-----------------|
| vCPU | 48 | 144 |
| RAM | 128 GB | 384 GB |
| Disk (vSAN NVMe) | 200 GB | 600 GB |
| NICs | 2 (management + trunk) | — |
| ESXi Version | 9.0 | — |

### vNIC Mappings

| vNIC | Connected To | Carries |
|------|-------------|---------|
| vmnic0 | vCD private network (access, VLAN 10) | Management traffic |
| vmnic1 | vCD private network (trunk) | vMotion, vSAN, TEP, Edge VLANs |

### VMkernel Assignments

| VMkernel | VLAN | Service |
|----------|------|---------|
| vmk0 | 10 | Management |
| vmk1 | 20 | vMotion |
| vmk2 | 30 | vSAN |
| vmk3 | 40 | Host Overlay (TEP) |

### vSAN Disk Layout

- **Mode**: vSAN Express Storage Architecture (ESA)
- **Storage policy**: Failures to Tolerate (FTT) = 1 (RAID-1 mirroring)
- Each host: 1x 200 GB NVMe storage device in a single storage pool (no separate cache tier)
- Nested ESXi preparation: NVMe devices marked as SSD, mock Hardware Compatibility List (HCL) vSphere Installation Bundle (VIB) installed, FakeSCSIReservations enabled

### vSAN Usable Capacity

With FTT=1 RAID-1, each object is mirrored — raw capacity is halved for data protection. vSAN ESA also requires operational reserve for rebalancing and component rebuilds.

> **Note on ESA slack space**: vSAN ESA does not require the 30% slack space reservation that OSA recommended. ESA's single-pool architecture with inline dedup/compression handles space management more efficiently. VMware recommends maintaining **~25% free space** for operational headroom — primarily for component rebuilds after host failure and temporary space during lifecycle operations. The 70% utilisation threshold in the scaling guidance (Section 10.1) reflects this.

#### Management Domain Storage

| Metric | Value | Calculation |
|--------|-------|-------------|
| Raw capacity | 800 GB | 4 hosts × 200 GB |
| FTT=1 RAID-1 overhead | 50% | Mirror = 2× data |
| Usable after RAID | ~400 GB | 800 GB ÷ 2 |
| Operational reserve (25%) | ~100 GB | Rebalancing, rebuilds, lifecycle headroom |
| Available for VM data | ~300 GB | After reserve |
| Appliance allocation | ~1,100 GB (thin) | See Section 6 + resource table (thin-provisioned — actual consumption is 30-50% of allocated) |

> Appliance disks are thin-provisioned. The allocated total far exceeds raw capacity, but actual vSAN consumption is much lower due to thin provisioning plus ESA inline dedup/compression. Monitor via vCenter → vSAN → Capacity.

#### Workload Domain Storage

| Metric | Value | Calculation |
|--------|-------|-------------|
| Raw capacity | 600 GB | 3 hosts × 200 GB |
| FTT=1 RAID-1 overhead | 50% | Mirror = 2× data |
| Usable after RAID | ~300 GB | 600 GB ÷ 2 |
| Operational reserve (25%) | ~75 GB | Rebalancing, rebuilds |
| Available for VM data | ~225 GB | After reserve |
| Infrastructure allocation | ~800 GB (thin) | vCenter + NSX Mgr + 2× Edge + vSphere Supervisor CPs (thin-provisioned) |
| Available for vSphere Kubernetes Services (VKS) PVs | ~50-100 GB | Depends on actual consumption after thin + dedup |

> The workload domain is the tighter storage constraint. VKS PersistentVolumes compete with NSX Edge VMs and the Supervisor control plane for vSAN capacity. Monitor vSAN capacity utilisation closely — see [Operations Guide](operate.md) Section 5.

## 6. VCF Management Domain

> Implements VCF-01 (domain separation), VCF-03 (VCF Operations/Automation in mgmt domain), VCF-04 (installer-driven bringup). See [Logical Design](logical-design.md) Section 6.

### Component Table

| Component | Hostname | IP (VLAN 10) | Role |
|-----------|----------|-------------|------|
| VCF Installer | vcf-installer | 10.0.10.3 | Orchestrates initial deployment |
| vCenter Server | vcenter-mgmt | 10.0.10.4 | Management domain vCenter |
| SDDC Manager | sddc-manager | 10.0.10.5 | VCF lifecycle and domain management |
| NSX Manager | nsx-mgr-mgmt | 10.0.10.6 | Management domain NSX (single node) |
| VCF Operations | vcf-ops | 10.0.10.7 | Monitoring, capacity, and analytics |
| VCF Automation | vcf-auto | 10.0.10.8 | Infrastructure automation |

### Installer Prerequisites

Before running the VCF Installer:

1. All 4 management ESXi hosts are accessible on the management network
2. DNS forward and reverse records exist for all components (configured in gateway dnsmasq)
3. NTP is reachable from all hosts (gateway chrony)
4. ESXi hosts have matching passwords and are in maintenance mode

See [Delivery Guide](deliver.md) Phase 3 for the step-by-step bringup procedure.

## 7. VCF Workload Domain

> Implements VCF-01 (domain separation) and VCF-02 (single-node NSX Manager). See [Logical Design](logical-design.md) Section 6.

### Component Table

| Component | Hostname | IP (VLAN 10) | Role |
|-----------|----------|-------------|------|
| vCenter Server | vcenter-wld | 10.0.10.9 | Workload domain vCenter |
| NSX Manager | nsx-mgr-wld | 10.0.10.10 | Workload domain NSX (single node) |

See [Delivery Guide](deliver.md) Phase 4 for the host commissioning and domain creation procedure.

## 8. NSX Edge Cluster

> Implements NSX-01 (two-node Large Edge cluster), NSX-02 (Active-Standby Tier-0 with BGP), NSX-03 (centralised Virtual Private Cloud (VPC)), NSX-04 (source NAT). See [Logical Design](logical-design.md) Section 7.

### Edge VM Specifications

| Edge VM | Hostname | Management IP | TEP IP (VLAN 50) | Uplink IP (VLAN 60) |
|---------|----------|--------------|-------------------|---------------------|
| Edge-01 | edge-01 | 10.0.10.20 | 10.0.50.20 | — |
| Edge-02 | edge-02 | 10.0.10.21 | 10.0.50.21 | — |

Edge VMs are sized as **Large** (8 vCPU, 32 GB RAM) to support VKS workloads.

### Tier-0 Gateway Settings

| Setting | Value |
|---------|-------|
| Name | tier0-gateway |
| HA Mode | Active-Standby |
| Edge Cluster | workload-edge-cluster |
| Uplink Interface | 10.0.60.2/24 on VLAN 60 |
| BGP ASN | 65001 |
| BGP Neighbor | 10.0.60.1 (Gateway FRR, ASN 65000) |

### NSX Tier-1 Gateway Settings

| Setting | Value |
|---------|-------|
| Name | tier1-gateway |
| Linked to | tier0-gateway |
| Route Advertisement | Connected subnets, NAT IPs, LB VIPs |

### NSX VPC Settings

| Setting | Value |
|---------|-------|
| VPC Name | vks-vpc |
| Connectivity | Centralised (via Edge cluster) |
| External Connectivity | Via Tier-0 BGP to gateway |
| Subnets | Created dynamically by VKS for pod and service networks |
| NAT | Source NAT on Tier-0 for outbound traffic |
| Load Balancing | NSX LB via Tier-1 for Kubernetes services |

### Expected Route Tables (Post-Phase 5)

After NSX networking is configured and BGP is established, the following routes should be present.

#### Gateway Route Table (`ip route` / `vtysh -c 'show ip bgp'`)

```text
default via <public-gw> dev ens33              ← internet via public NIC

10.0.10.0/24 dev ens34 scope link              ← Management (native VLAN)
10.0.20.0/24 dev ens34.20 scope link           ← vMotion
10.0.30.0/24 dev ens34.30 scope link           ← vSAN
10.0.40.0/24 dev ens34.40 scope link           ← Host Overlay
10.0.50.0/24 dev ens34.50 scope link           ← Edge Overlay
10.0.60.0/24 dev ens34.60 scope link           ← Edge Uplink / BGP

# BGP routes (vtysh -c 'show ip bgp'):
B>   192.168.0.0/16 [20/0] via 10.0.60.2           ← VKS pod CIDR (from NSX Tier-0)
B>   10.96.0.0/12 [20/0] via 10.0.60.2             ← VKS service CIDR (from NSX Tier-0)
```

> **Note**: The exact VPC/overlay prefixes received via BGP depend on which subnets the Supervisor and VKS cluster create. The pod CIDR (192.168.0.0/16) and service CIDR (10.96.0.0/12) are defined in the VKS cluster manifest. Additional /24 subnets may appear as VPC segments are created.

#### NSX Tier-0 Route Table

View via NSX Manager → Networking → Tier-0 Gateways → tier0-gateway → Routing Table, or via API:

```
GET https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/routing-table
```

| Prefix | Next Hop | Type | Source |
|--------|----------|------|--------|
| 10.0.10.0/24 | 10.0.60.1 | BGP | Gateway (management) |
| 10.0.20.0/24 | 10.0.60.1 | BGP | Gateway (vMotion) |
| 10.0.30.0/24 | 10.0.60.1 | BGP | Gateway (vSAN) |
| 10.0.40.0/24 | 10.0.60.1 | BGP | Gateway (host overlay) |
| 10.0.50.0/24 | 10.0.60.1 | BGP | Gateway (edge overlay) |
| 10.0.60.0/24 | — | Connected | Tier-0 uplink |
| 192.168.x.0/24 | — | Connected | Tier-1 (VKS pod subnets) |
| 10.96.x.0/24 | — | Connected | Tier-1 (VKS service subnets) |
| 0.0.0.0/0 | 10.0.60.1 | Static | Default route to gateway |

> **Expected route count**: ~6 BGP routes from gateway (one per VLAN SVI) plus connected/redistributed routes from Tier-1. The exact count depends on how many VPC subnets are created by the Supervisor and VKS.

## 9. VKS Cluster Specification

> Implements VKS-01 (Supervisor with NSX), VKS-02 (3+3 node topology), VKS-03 (subscribed content library), VKS-04 (best-effort-medium VM class). See [Logical Design](logical-design.md) Section 8.

### Supervisor Settings

| Setting | Value |
|---------|-------|
| Cluster | Workload domain cluster |
| Networking | NSX |
| Control Plane Network | VPC subnet (auto-provisioned) |
| Storage Policy | vSAN Default |
| Content Library | VKS Kubernetes releases |

### vSphere Namespace

| Setting | Value |
|---------|-------|
| Namespace | vks-workloads |
| VM Classes | best-effort-small, best-effort-medium |
| Storage Policies | vSAN Default |
| Content Library | VKS Kubernetes releases |

### VKS Cluster Settings

| Setting | Value |
|---------|-------|
| Cluster Name | vks-cluster-01 |
| Kubernetes Version | Latest available VMware Kubernetes Runtime (VKr) |
| Control Plane Nodes | 3 |
| Worker Nodes | 3 |
| VM Class | best-effort-medium (2 vCPU, 8 GB RAM) |
| Storage Class | vSAN Default |
| Network | NSX VPC subnet |
| AppArmor Profile | RuntimeDefault (containerd default) |

### Content Library

A subscribed content library provides VKr images. The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via gateway → vCD public network).

## 10. Resource Summary Tables

### vCD Resource Requirements

| Component | vCPU | RAM (GB) | Storage (GB) |
|-----------|------|----------|-------------|
| Ubuntu Gateway | 2 | 10 | 60 |
| ESXi (Management, 4x) | 192 | 512 | 800 |
| ESXi (Workload, 3x) | 144 | 384 | 600 |
| **vCD Total** | **338** | **906** | **1,460** |

### VCF Appliances (Nested, on ESXi)

These run inside the nested environment and consume resources from the ESXi hosts above:

| Component | vCPU | RAM (GB) | Storage (GB) |
|-----------|------|----------|-------------|
| VCF Installer | 4 | 24 | 100 |
| vCenter (Management) | 4 | 21 | 100 |
| vCenter (Workload) | 4 | 21 | 100 |
| SDDC Manager | 4 | 16 | 500 |
| NSX Manager (Management) | 6 | 24 | 200 |
| NSX Manager (Workload) | 6 | 24 | 200 |
| NSX Edge (2x) | 16 | 64 | 400 |
| VCF Operations | 4 | 16 | 100 |
| VCF Automation | 4 | 24 | 100 |
| **Nested Total** | **52** | **234** | **1,800** |

> **Note**: The nested appliance resources are consumed from the 896 GB RAM and 1,400 GB storage provisioned to the ESXi VMs. The remaining ~662 GB RAM is available for VKS workloads and Supervisor VMs.

### 10.1 Capacity Headroom Analysis

#### Management Domain Headroom

The management domain hosts run all VCF infrastructure appliances. The VCF Installer is temporary and its resources are reclaimed after bringup.

| Category | vCPU | RAM (GB) |
|----------|------|----------|
| **Total provisioned (4 hosts)** | 192 | 512 |
| vCenter Server (management) | 4 | 21 |
| SDDC Manager | 4 | 16 |
| NSX Manager (management) | 6 | 24 |
| VCF Operations | 4 | 16 |
| VCF Automation | 4 | 24 |
| **Appliance subtotal** | **22** | **101** |
| VCF Installer (temporary, reclaimed after bringup) | 4 | 24 |
| **Remaining after bringup** | **170** | **411** |
| **Utilisation** | **~11%** | **~20%** |

> **Note**: Management domain hosts have substantial headroom. The surplus provides a comfortable buffer for SDDC Manager lifecycle operations (e.g., in-place upgrades that temporarily run two appliance instances).

#### Workload Domain Headroom

The workload domain hosts run the workload vCenter, NSX Manager, NSX Edge cluster, Supervisor control plane, and VKS worker nodes. This domain is the tighter constraint.

| Category | vCPU | RAM (GB) |
|----------|------|----------|
| **Total provisioned (3 hosts)** | 144 | 384 |
| vCenter Server (workload) | 4 | 21 |
| NSX Manager (workload) | 6 | 24 |
| NSX Edge cluster (2x Large) | 16 | 64 |
| Supervisor control plane (3 CP VMs) | ~6 | ~24 |
| VKS workers (3x best-effort-medium) | 6 | 24 |
| **Consumed subtotal** | **~38** | **~157** |
| **Remaining** | **~106** | **~227** |
| **Utilisation** | **~26%** | **~41%** |

> **Note**: The workload domain has comfortable headroom for VKS workloads and scaling. The surplus allows adding more VKS worker nodes or scaling existing ones to larger VM classes without resource pressure.

#### Scaling Thresholds

Monitor these indicators to determine when the lab has reached practical limits. See [Operations Guide](operate.md) Section 5 for scaling procedures and options.

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| vSAN capacity | > 70% used | Plan storage addition or object cleanup |
| Host RAM utilisation | > 90% sustained | Add ESXi host or reduce VM count |
| VKS node CPU/RAM | > 80% sustained | Scale VM class up or add worker nodes |
| Workload domain vCPU utilisation | > 80% sustained | Add ESXi host or reduce workload |
