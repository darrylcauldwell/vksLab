---
title: "VKS Lab"
subtitle: "Physical Design"
author: "dreamfold"
date: "March 2026"
---

# Physical Design

## 1. VLAN & Subnet Table

> Implements NET-03 (six-VLAN segmentation) and NET-04 (jumbo frames for overlay/storage). See [Logical Design](logical-design.md) Section 3.

| VLAN ID | Name | Subnet | Purpose | MTU |
|---------|------|--------|---------|-----|
| 10 | Management | 10.0.10.0/24 | ESXi management, vCenter, SDDC Manager, NSX Manager | 1500 |
| 20 | vMotion | 10.0.20.0/24 | vMotion traffic | 9000 |
| 30 | vSAN | 10.0.30.0/24 | vSAN storage traffic | 9000 |
| 40 | Host Overlay (TEP) | 10.0.40.0/24 | NSX host transport endpoint tunnels | 9000 |
| 50 | Edge Overlay | 10.0.50.0/24 | NSX Edge TEP tunnels | 9000 |
| 60 | Edge Uplink | 10.0.60.0/24 | NSX Tier-0 ↔ Arista vEOS BGP peering | 1500 |

## 2. IP Addressing Scheme

### Infrastructure Services (VLAN 10 — Management)

| IP Address | Hostname | Role |
|------------|----------|------|
| 10.0.10.1 | gateway | Arista vEOS SVI (default gateway) |
| 10.0.10.2 | jumpbox | Ubuntu jumpbox (NIC2) |
| 10.0.10.3 | vcf-installer | VCF Installer appliance |
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
| 10.0.60.1 | Arista vEOS (BGP neighbor) |
| 10.0.60.2 | NSX Tier-0 uplink interface |

## 3. Ubuntu Jumpbox Specification

> Implements NET-01 (dual-homed single entry point), SVC-01 through SVC-06 (co-located infrastructure services). See [Logical Design](logical-design.md) Sections 3–4.

| Resource | Value |
|----------|-------|
| OS | Ubuntu 24.04 LTS |
| Desktop | XFCE + xrdp (remote desktop access) |
| vCPU | 2 |
| RAM | 10 GB |
| Disk | 60 GB |
| NIC1 | vCD public network (DHCP or static from vCD) |
| NIC2 | vCD private network — VLAN 10 (management), IP 10.0.10.2 |

### Network Configuration

See [Delivery Guide](deliver.md) for netplan configuration. Key parameters:

- NIC1 (ens160): vCD public network, DHCP
- NIC2 (ens192): vCD private network, static 10.0.10.2/24, gateway 10.0.10.1
- IP forwarding disabled — jumpbox is not a router

### Services Configuration

| Service | Package | Config |
|---------|---------|--------|
| DNS | dnsmasq | Zone: `lab.dreamfold.dev`, upstream forwarder via NIC1 |
| DHCP | dnsmasq | Static MAC→IP reservations for ESXi hosts on VLAN 10 |
| NTP | chrony | `allow 10.0.0.0/16`, servers: public NTP pools |
| CA | step-ca | Root CA for `lab.dreamfold.dev`, ACME enabled |
| OIDC | Keycloak (Docker) | Port 8443, centralised identity provider for vCenter and NSX |
| Secrets | OpenBao (Docker) | Port 8200, KV secret store for lab credentials |
| Remote access | xrdp | Listening on port 3389 (NIC1) |
| Web browser | Firefox | Access vCenter, NSX Manager, SDDC Manager UIs |

All VCF components point to 10.0.10.2 for DNS and NTP. The CA root certificate is distributed to ESXi hosts and management appliances during deployment.

### DHCP Reservations (VLAN 10)

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

## 4. Arista vEOS Router Specification

> Implements NET-02 (vEOS inter-VLAN routing and BGP peering) and SVC-05 (secondary NTP). See [Logical Design](logical-design.md) Section 3.

| Resource | Value |
|----------|-------|
| Image | Arista vEOS 4.32.x |
| vCPU | 2 |
| RAM | 4 GB |
| Disk | 8 GB |
| NIC | vCD private network (trunk, all VLANs) |

See [Delivery Guide](deliver.md) for complete vEOS startup-config including interface, NTP, and BGP configuration.

| Parameter | Value |
|-----------|-------|
| vEOS ASN | 65000 |
| NSX Tier-0 ASN | 65001 |
| Peering subnet | 10.0.60.0/24 |
| NTP server | Secondary NTP source (10.0.10.1) for VCF validation |

BGP advertises all connected subnets to NSX, and receives VPC/overlay prefixes from the Tier-0. This gives VKS workloads a routed path out through the vEOS to the jumpbox and beyond.

vEOS also serves as a secondary NTP source. VCF validation requires two NTP servers — jumpbox chrony (10.0.10.2) is primary and vEOS (10.0.10.1) is secondary.

## 5. Nested ESXi Host Specification

> Implements ESX-01 (nested VMs on vCD), ESX-02 (4+3 host split), ESX-03 (vSAN ESA), ESX-04 (two-vNIC model). See [Logical Design](logical-design.md) Section 5.

### Management Domain Hosts (4x)

| Resource | Per Host | Total (4 hosts) |
|----------|----------|-----------------|
| vCPU | 8 | 32 |
| RAM | 72 GB | 288 GB |
| Disk (vSAN NVMe) | 200 GB | 800 GB |
| NICs | 2 (management + trunk) | — |
| ESXi Version | 9.0 | — |

### Workload Domain Hosts (3x)

| Resource | Per Host | Total (3 hosts) |
|----------|----------|-----------------|
| vCPU | 8 | 24 |
| RAM | 72 GB | 216 GB |
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

- **Mode**: vSAN ESA (Express Storage Architecture)
- **Storage policy**: Failures to Tolerate = 1 (RAID-1 mirroring)
- Each host: 1x 200 GB NVMe storage device in a single storage pool (no separate cache tier)
- Nested ESXi preparation: NVMe devices marked as SSD, mock HCL VIB installed, FakeSCSIReservations enabled

## 6. VCF Management Domain

> Implements VCF-01 (domain separation), VCF-03 (VCF Ops/Auto in mgmt domain), VCF-04 (installer-driven bringup). See [Logical Design](logical-design.md) Section 6.

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
2. DNS forward and reverse records exist for all components (configured in jumpbox dnsmasq)
3. NTP is reachable from all hosts (jumpbox chrony)
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

> Implements NSX-01 (two-node Large Edge cluster), NSX-02 (Active-Standby Tier-0 with BGP), NSX-03 (centralised VPC), NSX-04 (source NAT). See [Logical Design](logical-design.md) Section 7.

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
| BGP Neighbor | 10.0.60.1 (Arista vEOS, ASN 65000) |

### Tier-1 Gateway Settings

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
| External Connectivity | Via Tier-0 BGP to vEOS |
| Subnets | Created dynamically by VKS for pod and service networks |
| NAT | Source NAT on Tier-0 for outbound traffic |
| Load Balancing | NSX LB via Tier-1 for Kubernetes services |

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
| Kubernetes Version | Latest available VKr |
| Control Plane Nodes | 3 |
| Worker Nodes | 3 |
| VM Class | best-effort-medium (2 vCPU, 8 GB RAM) |
| Storage Class | vSAN Default |
| Network | NSX VPC subnet |

### Content Library

A subscribed content library provides Kubernetes release images (VKr). The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via vEOS → jumpbox → vCD public network).

## 10. Resource Summary Tables

### vCD Resource Requirements

| Component | vCPU | RAM (GB) | Storage (GB) |
|-----------|------|----------|-------------|
| Ubuntu Jumpbox | 2 | 10 | 60 |
| Arista vEOS | 2 | 4 | 8 |
| ESXi (Management, 4x) | 32 | 288 | 800 |
| ESXi (Workload, 3x) | 24 | 216 | 600 |
| **vCD Total** | **60** | **518** | **1,468** |

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

> **Note**: The nested appliance resources are consumed from the 504 GB RAM and 1,400 GB storage provisioned to the ESXi VMs. The remaining ~270 GB RAM is available for VKS workloads and Supervisor VMs. Cross-reference with Holodeck benchmarks (~325 GB RAM for VCF 9.0 single-site with Automation).

### 10.1 Capacity Headroom Analysis

#### Management Domain Headroom

The management domain hosts run all VCF infrastructure appliances. The VCF Installer is temporary and its resources are reclaimed after bringup.

| Category | vCPU | RAM (GB) |
|----------|------|----------|
| **Total provisioned (4 hosts)** | 32 | 288 |
| vCenter Server (management) | 4 | 21 |
| SDDC Manager | 4 | 16 |
| NSX Manager (management) | 6 | 24 |
| VCF Operations | 4 | 16 |
| VCF Automation | 4 | 24 |
| **Appliance subtotal** | **22** | **101** |
| VCF Installer (temporary, reclaimed after bringup) | 4 | 24 |
| **Remaining after bringup** | **10** | **187** |
| **Utilisation** | **~69%** | **~35%** |

> **Note**: Management domain hosts are sized for appliance overhead with comfortable headroom. RAM utilisation is low because VCF appliances are CPU-bound rather than memory-bound. The surplus RAM provides a buffer for SDDC Manager lifecycle operations (e.g., in-place upgrades that temporarily run two appliance instances).

#### Workload Domain Headroom

The workload domain hosts run the workload vCenter, NSX Manager, NSX Edge cluster, Supervisor control plane, and VKS worker nodes. This domain is the tighter constraint.

| Category | vCPU | RAM (GB) |
|----------|------|----------|
| **Total provisioned (3 hosts)** | 24 | 216 |
| vCenter Server (workload) | 4 | 21 |
| NSX Manager (workload) | 6 | 24 |
| NSX Edge cluster (2x Large) | 16 | 64 |
| Supervisor control plane (3 CP VMs) | ~6 | ~24 |
| VKS workers (3x best-effort-medium) | 6 | 24 |
| **Consumed subtotal** | **~38** | **~157** |
| **Remaining** | **-14 (overcommit)** | **~59** |
| **Utilisation** | **~158% (overcommit)** | **~73%** |

> **Note**: CPU overcommit is expected and acceptable in a nested lab environment. Nested virtualisation already means no performance guarantees from the underlying vCD platform — the physical host's scheduler mediates all CPU access. Workload domain vCPU overcommit does not prevent operation but will cause contention under sustained load. RAM is the real constraint to watch: ~59 GB free provides room for modest workload growth but not additional large VMs.

#### Scaling Thresholds

Monitor these indicators to determine when the lab has reached practical limits. See [Operations Guide](operate.md) Section 5 for scaling procedures and options.

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| vSAN capacity | > 70% used | Plan storage addition or object cleanup |
| Host RAM utilisation | > 90% sustained | Add ESXi host or reduce VM count |
| VKS node CPU/RAM | > 80% sustained | Scale VM class up or add worker nodes |
| Workload domain vCPU overcommit | > 200% | Reduce Edge size or add host |
