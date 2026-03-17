# VKS Lab Design Document

Nested VCF 9 environment running as a vApp on vCloud Director, showcasing VMware Kubernetes Service (VKS) with NSX VPC centralised connectivity.

## 1. Overview & Objectives

### Purpose

Demonstrate VKS on VCF 9 with NSX VPC in a fully nested lab environment hosted on vCloud Director. The lab provides a self-contained platform for exploring Supervisor clusters, VKS cluster lifecycle, and NSX VPC networking — all within a single vApp.

### Target Audience

- VMware platform engineers evaluating VCF 9 + VKS
- Network engineers exploring NSX VPC and BGP integration
- Anyone needing a portable nested VCF environment for testing

### Key Capabilities

- End-to-end VCF 9 deployment (management + workload domains)
- VKS cluster provisioning via Supervisor and Cluster v1beta1 API
- NSX VPC with centralised Edge connectivity
- BGP peering between NSX Tier-0 and Arista vEOS for north-south routing
- Remote access via RDP to Ubuntu jumpbox

## 2. Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                     vCloud Director vApp                        │
                    │                                                                 │
   Internet         │  ┌──────────┐    vCD Private Network (Trunk)                    │
       │            │  │  Ubuntu   │◄──────────────────────────────────────────┐       │
       │            │  │ Jumpbox   │         │              │                  │       │
       ▼            │  │ CA/DNS/NTP│         │              │                  │       │
  vCD Public Net    │  │          ─┼─────────┤              │                  │       │
  ──────────────────┼──┼─ NIC1     │         │              │                  │       │
                    │  │  NIC2 ────┼─────┐   │              │                  │       │
                    │  └──────────┘     │   │              │                  │       │
                    │                    │   │              │                  │       │
                    │              ┌─────┼───┼──────────────┼──────────┐       │       │
                    │              │     ▼   ▼              ▼          │       │       │
                    │              │  ┌──────────┐                    │       │       │
                    │              │  │  Arista   │                    │       │       │
                    │              │  │  vEOS     │◄─── BGP ───┐      │       │       │
                    │              │  │  Router   │            │      │       │       │
                    │              │  └──────────┘            │      │       │       │
                    │              │       │                    │      │       │       │
                    │              │       │ Inter-VLAN         │      │       │       │
                    │              │       │ Routing            │      │       │       │
                    │              │       ▼                    │      │       │       │
                    │              │  ┌─────────────────────────┼──┐   │       │       │
                    │              │  │    VCF Management Domain│  │   │       │       │
                    │              │  │                         │  │   │       │       │
                    │              │  │  ESXi-01  ESXi-02      │  │   │       │       │
                    │              │  │  ESXi-03  ESXi-04      │  │   │       │       │
                    │              │  │                         │  │   │       │       │
                    │              │  │  vCenter  SDDC Mgr      │  │   │       │       │
                    │              │  │  NSX Mgr  VCF Ops       │  │   │       │       │
                    │              │  │  VCF Automation          │  │   │       │       │
                    │              │  └─────────────────────────┘  │   │       │       │
                    │              │                                │   │       │       │
                    │              │  ┌─────────────────────────┐  │   │       │       │
                    │              │  │   VCF Workload Domain    │  │   │       │       │
                    │              │  │                          │  │   │       │       │
                    │              │  │  ESXi-05  ESXi-06       │  │   │       │       │
                    │              │  │  ESXi-07                │  │   │       │       │
                    │              │  │                          │  │   │       │       │
                    │              │  │  vCenter   NSX Mgr      │  │   │       │       │
                    │              │  │                          │  │   │       │       │
                    │              │  │  ┌──────────────────┐   │  │   │       │       │
                    │              │  │  │  NSX Edge Cluster │   │  │   │       │       │
                    │              │  │  │  Edge-01  Edge-02 │───┼──┼───┘       │       │
                    │              │  │  │  Tier-0 ► Tier-1  │   │  │           │       │
                    │              │  │  │  NSX VPC           │   │  │           │       │
                    │              │  │  └──────────────────┘   │  │           │       │
                    │              │  │                          │  │           │       │
                    │              │  │  ┌──────────────────┐   │  │           │       │
                    │              │  │  │  VKS Cluster      │   │  │           │       │
                    │              │  │  │  (Supervisor)      │   │  │           │       │
                    │              │  │  │  Control Plane     │   │  │           │       │
                    │              │  │  │  Worker Nodes      │   │  │           │       │
                    │              │  │  └──────────────────┘   │  │           │       │
                    │              │  └──────────────────────────┘  │           │       │
                    │              └────────────────────────────────┘           │       │
                    │                                                           │       │
                    └───────────────────────────────────────────────────────────┘       │
```

### Component Inventory

| Component | Quantity | Role |
|-----------|----------|------|
| Ubuntu Jumpbox | 1 | External access, CA, DNS, NTP |
| Arista vEOS | 1 | Inter-VLAN routing, BGP peer |
| Nested ESXi (Management) | 4 | VCF management domain hosts |
| Nested ESXi (Workload) | 3 | VCF workload domain hosts |
| VCF Installer | 1 | Drives VCF bringup (temporary) |
| vCenter Server | 2 | Management + workload domain |
| SDDC Manager | 1 | VCF lifecycle management |
| NSX Manager | 2 | Management + workload domain |
| NSX Edge VMs | 2 | North-south routing, VPC |
| VCF Operations | 1 | Monitoring and analytics |
| VCF Automation | 1 | Infrastructure automation |

## 3. vCloud Director Layer

### vApp Composition

All lab VMs run inside a single vCloud Director vApp. The vApp contains:

- 1x Ubuntu jumpbox
- 1x Arista vEOS router
- 7x nested ESXi hosts
- VCF management appliances (deployed during bringup onto nested ESXi)

### Networks

| Network | Type | Purpose |
|---------|------|---------|
| vCD Public | Org VDC external/routed | Jumpbox external access (RDP, SSH) |
| vCD Private | Org VDC internal (isolated) | All inter-VM communication, carries VCF VLANs |

The vCD public network provides external reachability. The vCD private network is an isolated org VDC network that carries all internal lab traffic as a trunk — VLAN tagging is handled by the nested ESXi vSwitches and the Arista vEOS router.

## 4. Network Design

### External Access

The Ubuntu jumpbox is dual-homed:

- **NIC1** (vCD public network): receives an IP from vCD, reachable externally via RDP/SSH
- **NIC2** (vCD private network): connects to the internal lab fabric on the management VLAN

All other lab VMs have a single NIC on the vCD private network.

### Arista vEOS Router

The vEOS router sits on the vCD private network with a trunk port carrying all VCF VLANs. It provides:

- **Inter-VLAN routing** between management, vMotion, and other VCF networks
- **BGP peering** with the NSX Tier-0 gateway for north-south routing from VPC workloads
- **Default gateway** for nested ESXi management interfaces

### VLAN Allocation

| VLAN ID | Name | Subnet | Purpose | MTU |
|---------|------|--------|---------|-----|
| 10 | Management | 10.0.10.0/24 | ESXi management, vCenter, SDDC Manager, NSX Manager | 1500 |
| 20 | vMotion | 10.0.20.0/24 | vMotion traffic | 9000 |
| 30 | vSAN | 10.0.30.0/24 | vSAN storage traffic | 9000 |
| 40 | Host Overlay (TEP) | 10.0.40.0/24 | NSX host transport endpoint tunnels | 9000 |
| 50 | Edge Overlay | 10.0.50.0/24 | NSX Edge TEP tunnels | 9000 |
| 60 | Edge Uplink | 10.0.60.0/24 | NSX Tier-0 ↔ Arista vEOS BGP peering | 1500 |

### IP Addressing Scheme

#### Infrastructure Services (VLAN 10 — Management)

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
| 10.0.10.11–14 | esxi-01 to 04 | Management domain ESXi hosts |
| 10.0.10.15–17 | esxi-05 to 07 | Workload domain ESXi hosts |
| 10.0.10.20–21 | edge-01 to 02 | NSX Edge VMs (management interface) |

#### vMotion (VLAN 20)

| IP Range | Purpose |
|----------|---------|
| 10.0.20.11–14 | Management domain ESXi hosts |
| 10.0.20.15–17 | Workload domain ESXi hosts |

#### vSAN (VLAN 30)

| IP Range | Purpose |
|----------|---------|
| 10.0.30.11–14 | Management domain ESXi hosts |
| 10.0.30.15–17 | Workload domain ESXi hosts |

#### Host Overlay TEP (VLAN 40)

| IP Range | Purpose |
|----------|---------|
| 10.0.40.11–17 | ESXi host TEP interfaces (pool) |

#### Edge Overlay TEP (VLAN 50)

| IP Range | Purpose |
|----------|---------|
| 10.0.50.20–21 | NSX Edge TEP interfaces |

#### Edge Uplink / BGP (VLAN 60)

| IP Address | Role |
|------------|------|
| 10.0.60.1 | Arista vEOS (BGP neighbor) |
| 10.0.60.2 | NSX Tier-0 uplink interface |

### MTU

- VLANs 20 (vMotion), 30 (vSAN), 40 (Host Overlay), 50 (Edge Overlay): MTU 9000
- VLANs 10 (Management), 60 (Edge Uplink): MTU 1500
- The vCD private network portgroup must allow jumbo frames (MTU ≥ 9000)

### DNS, NTP, and Certificate Authority

All three infrastructure services run on the Ubuntu jumpbox:

| Service | Software | Details |
|---------|----------|---------|
| DNS | dnsmasq | Authoritative for `lab.local` zone, forwards unknown queries upstream |
| NTP | chrony | Stratum 2 server, syncs to public NTP pools via jumpbox external NIC |
| CA | step-ca | Lightweight ACME-capable CA for issuing TLS certs to VCF components |

All VCF components point to 10.0.10.2 for DNS and NTP. The CA root certificate is distributed to ESXi hosts and management appliances during deployment.

## 5. Ubuntu Jumpbox

### Purpose

The jumpbox is the single point of entry into the lab and hosts shared infrastructure services (DNS, NTP, CA).

### Specification

| Resource | Value |
|----------|-------|
| OS | Ubuntu 24.04 LTS |
| Desktop | XFCE + xrdp (remote desktop access) |
| vCPU | 2 |
| RAM | 4 GB |
| Disk | 60 GB |
| NIC1 | vCD public network (DHCP or static from vCD) |
| NIC2 | vCD private network — VLAN 10 (management), IP 10.0.10.2 |

### Services

| Service | Package | Config |
|---------|---------|--------|
| DNS | dnsmasq | Zone: `lab.local`, upstream forwarder via NIC1 |
| NTP | chrony | `allow 10.0.0.0/16`, servers: public NTP pools |
| CA | step-ca | Root CA for `lab.local`, ACME enabled |
| Remote access | xrdp | Listening on port 3389 (NIC1) |
| Web browser | Firefox | Access vCenter, NSX Manager, SDDC Manager UIs |

### Network Configuration

```
# NIC1 (ens160) — vCD public network
auto ens160
iface ens160 inet dhcp

# NIC2 (ens192) — vCD private network, management VLAN
auto ens192
iface ens192 inet static
    address 10.0.10.2/24
    gateway 10.0.10.1
    mtu 1500
```

IP forwarding is **not** enabled on the jumpbox — it is not a router. The Arista vEOS handles all inter-VLAN routing.

## 6. Arista vEOS Router

### Purpose

The vEOS provides Layer-3 routing across all VCF VLANs and BGP peering with NSX Tier-0 for north-south connectivity from VPC workloads.

### Specification

| Resource | Value |
|----------|-------|
| Image | Arista vEOS 4.32.x |
| vCPU | 2 |
| RAM | 4 GB |
| Disk | 8 GB |
| NIC | vCD private network (trunk, all VLANs) |

### Interface Configuration

```
! Trunk interface on vCD private network
interface Ethernet1
   no switchport
   mtu 9000

! Management VLAN SVI
interface Vlan10
   ip address 10.0.10.1/24
   mtu 1500

! vMotion VLAN SVI
interface Vlan20
   ip address 10.0.20.1/24
   mtu 9000

! vSAN VLAN SVI
interface Vlan30
   ip address 10.0.30.1/24
   mtu 9000

! Host Overlay TEP VLAN SVI
interface Vlan40
   ip address 10.0.40.1/24
   mtu 9000

! Edge Overlay TEP VLAN SVI
interface Vlan50
   ip address 10.0.50.1/24
   mtu 9000

! Edge Uplink VLAN SVI (BGP peering)
interface Vlan60
   ip address 10.0.60.1/24
   mtu 1500
```

### BGP Configuration

```
router bgp 65000
   router-id 10.0.60.1
   neighbor 10.0.60.2 remote-as 65001
   neighbor 10.0.60.2 description NSX-Tier0
   !
   address-family ipv4
      neighbor 10.0.60.2 activate
      redistribute connected
```

| Parameter | Value |
|-----------|-------|
| vEOS ASN | 65000 |
| NSX Tier-0 ASN | 65001 |
| Peering subnet | 10.0.60.0/24 |

BGP advertises all connected subnets to NSX, and receives VPC/overlay prefixes from the Tier-0. This gives VKS workloads a routed path out through the vEOS to the jumpbox and beyond.

> **Note**: Detailed vEOS configuration will be finalised after vEOS image ingestion into the lab.

## 7. Nested ESXi Hosts

### Management Domain Hosts (4x)

| Resource | Per Host | Total (4 hosts) |
|----------|----------|-----------------|
| vCPU | 8 | 32 |
| RAM | 72 GB | 288 GB |
| Disk (vSAN) | 200 GB | 800 GB |
| NICs | 2 (management + trunk) | — |
| ESXi Version | 9.0 | — |

### Workload Domain Hosts (3x)

| Resource | Per Host | Total (3 hosts) |
|----------|----------|-----------------|
| vCPU | 8 | 24 |
| RAM | 72 GB | 216 GB |
| Disk (vSAN) | 200 GB | 600 GB |
| NICs | 2 (management + trunk) | — |
| ESXi Version | 9.0 | — |

### vSAN Configuration

- **Mode**: vSAN OSA (Original Storage Architecture) — simpler for nested environments, well-proven
- **Storage policy**: Failures to Tolerate = 1 (RAID-1 mirroring)
- Each host contributes one capacity disk (200 GB virtual disk)
- Cache tier: 10 GB virtual disk per host (flash-simulated)

### Host Networking

Each nested ESXi host has two virtual NICs:

| vNIC | Connected To | Carries |
|------|-------------|---------|
| vmnic0 | vCD private network (access, VLAN 10) | Management traffic |
| vmnic1 | vCD private network (trunk) | vMotion, vSAN, TEP, Edge VLANs |

Inside each ESXi host, a VDS (created during VCF bringup) maps VLANs to VMkernel ports:

| VMkernel | VLAN | Service |
|----------|------|---------|
| vmk0 | 10 | Management |
| vmk1 | 20 | vMotion |
| vmk2 | 30 | vSAN |
| vmk3 | 40 | Host Overlay (TEP) |

## 8. VCF 9 Management Domain

### Deployment Method

The VCF Installer appliance drives the initial bringup. It is deployed onto one of the management domain ESXi hosts and orchestrates the deployment of all management components.

### Management Domain Components

| Component | Hostname | IP (VLAN 10) | Role |
|-----------|----------|-------------|------|
| VCF Installer | vcf-installer | 10.0.10.3 | Orchestrates initial deployment |
| vCenter Server | vcenter-mgmt | 10.0.10.4 | Management domain vCenter |
| SDDC Manager | sddc-manager | 10.0.10.5 | VCF lifecycle and domain management |
| NSX Manager | nsx-mgr-mgmt | 10.0.10.6 | Management domain NSX (single node for lab) |
| VCF Operations | vcf-ops | 10.0.10.7 | Monitoring, capacity, and analytics |
| VCF Automation | vcf-auto | 10.0.10.8 | Infrastructure-as-code and self-service |

### Deployment Prerequisites

Before running the VCF Installer:

1. All 4 management ESXi hosts are accessible on the management network
2. DNS forward and reverse records exist for all components (configured in jumpbox dnsmasq)
3. NTP is reachable from all hosts (jumpbox chrony)
4. ESXi hosts have matching passwords and are in maintenance mode

### VCF Installer Bringup Workflow

1. Deploy VCF Installer OVA to esxi-01
2. Access the installer UI at `https://10.0.10.3`
3. Provide the deployment parameter workbook (JSON)
4. Installer deploys vCenter, configures vDS, creates vSAN cluster
5. Installer deploys SDDC Manager
6. Installer deploys NSX Manager
7. Post-bringup: deploy VCF Operations and VCF Automation from SDDC Manager

## 9. VCF 9 Workload Domain

### Purpose

The workload domain hosts the NSX Edge cluster, Supervisor, and VKS workloads — keeping them separate from management infrastructure.

### Components

| Component | Hostname | IP (VLAN 10) | Role |
|-----------|----------|-------------|------|
| vCenter Server | vcenter-wld | 10.0.10.9 | Workload domain vCenter |
| NSX Manager | nsx-mgr-wld | 10.0.10.10 | Workload domain NSX (single node for lab) |

### Deployment via SDDC Manager

1. **Commission hosts**: Add esxi-05, esxi-06, esxi-07 to SDDC Manager's free pool
2. **Create workload domain**: Use SDDC Manager to create a new VI workload domain with:
   - 3x ESXi hosts
   - vSAN storage
   - New vCenter instance (vcenter-wld)
   - New NSX Manager instance (nsx-mgr-wld) — or share the management NSX if preferred
3. **Validate**: Confirm cluster health, vSAN status, and NSX transport node status

## 10. NSX Edge Cluster & VPC (Centralised)

### NSX Edge Deployment

Deploy two NSX Edge VMs onto the workload domain cluster:

| Edge VM | Hostname | Management IP | TEP IP (VLAN 50) | Uplink IP (VLAN 60) |
|---------|----------|--------------|-------------------|---------------------|
| Edge-01 | edge-01 | 10.0.10.20 | 10.0.50.20 | — |
| Edge-02 | edge-02 | 10.0.10.21 | 10.0.50.21 | — |

Edge VMs are sized as **Large** (8 vCPU, 32 GB RAM) to support VKS workloads.

### Tier-0 Gateway

| Setting | Value |
|---------|-------|
| Name | tier0-gateway |
| HA Mode | Active-Standby |
| Edge Cluster | workload-edge-cluster |
| Uplink Interface | 10.0.60.2/24 on VLAN 60 |
| BGP ASN | 65001 |
| BGP Neighbor | 10.0.60.1 (Arista vEOS, ASN 65000) |

### Tier-1 Gateway

| Setting | Value |
|---------|-------|
| Name | tier1-gateway |
| Linked to | tier0-gateway |
| Route Advertisement | Connected subnets, NAT IPs, LB VIPs |

### NSX VPC Configuration

NSX VPC provides project-level network isolation for VKS workloads:

| Setting | Value |
|---------|-------|
| VPC Name | vks-vpc |
| Connectivity | Centralised (via Edge cluster) |
| External Connectivity | Via Tier-0 BGP to vEOS |
| Subnets | Created dynamically by VKS for pod and service networks |
| NAT | Source NAT on Tier-0 for outbound traffic |
| Load Balancing | NSX LB via Tier-1 for Kubernetes services |

The centralised model means all north-south traffic from VKS pods traverses the NSX Edge cluster → Tier-0 → BGP → Arista vEOS → jumpbox (or beyond).

## 11. VKS / Supervisor

### Supervisor Enablement

Enable the Supervisor on the workload domain cluster via vCenter:

| Setting | Value |
|---------|-------|
| Cluster | Workload domain cluster |
| Networking | NSX |
| Control Plane Network | VPC subnet (auto-provisioned) |
| Storage Policy | vSAN Default |
| Content Library | VKS Kubernetes releases |

### Content Library

A subscribed content library provides Kubernetes release images (VKr — VMware Kubernetes releases). The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via vEOS → jumpbox → vCD public network).

### VKS Cluster Deployment

Deploy a VKS cluster using the Cluster v1beta1 API:

| Setting | Value |
|---------|-------|
| Cluster Name | vks-cluster-01 |
| Kubernetes Version | Latest available VKr |
| Control Plane Nodes | 3 |
| Worker Nodes | 3 |
| VM Class | best-effort-medium (2 vCPU, 8 GB RAM) |
| Storage Class | vSAN Default |
| Network | NSX VPC subnet |

### vSphere Namespace

A vSphere Namespace provides the tenancy boundary for VKS:

| Setting | Value |
|---------|-------|
| Namespace | vks-workloads |
| VM Classes | best-effort-small, best-effort-medium |
| Storage Policies | vSAN Default |
| Content Library | VKS Kubernetes releases |

## 12. Resource Summary

### vCD Resource Requirements

| Component | vCPU | RAM (GB) | Storage (GB) |
|-----------|------|----------|-------------|
| Ubuntu Jumpbox | 2 | 4 | 60 |
| Arista vEOS | 2 | 4 | 8 |
| ESXi (Management, 4x) | 32 | 288 | 800 |
| ESXi (Workload, 3x) | 24 | 216 | 600 |
| **vCD Total** | **60** | **512** | **1,468** |

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

## 13. Deployment Sequence

### Phase 1 — Foundation

| Step | Action | Depends On |
|------|--------|-----------|
| 1.1 | Create vCD vApp with public and private networks | — |
| 1.2 | Deploy Ubuntu jumpbox, configure NIC1 (public) and NIC2 (private) | 1.1 |
| 1.3 | Configure dnsmasq, chrony, and step-ca on jumpbox | 1.2 |
| 1.4 | Deploy Arista vEOS, configure SVIs and inter-VLAN routing | 1.1 |
| 1.5 | Verify connectivity: jumpbox ↔ vEOS ↔ all VLANs | 1.2, 1.4 |

### Phase 2 — Nested ESXi

| Step | Action | Depends On |
|------|--------|-----------|
| 2.1 | Deploy 4x nested ESXi hosts (management domain) | 1.5 |
| 2.2 | Deploy 3x nested ESXi hosts (workload domain) | 1.5 |
| 2.3 | Configure ESXi networking (vmk0 management, vmnic1 trunk) | 2.1, 2.2 |
| 2.4 | Set ESXi hostnames, DNS, NTP to point to jumpbox | 2.3 |
| 2.5 | Verify all 7 hosts reachable and time-synced | 2.4 |

### Phase 3 — VCF Management Domain

| Step | Action | Depends On |
|------|--------|-----------|
| 3.1 | Create DNS records for all VCF components in dnsmasq | 2.5 |
| 3.2 | Deploy VCF Installer OVA to esxi-01 | 2.5, 3.1 |
| 3.3 | Run VCF Installer bringup (vCenter, vDS, vSAN, SDDC Mgr, NSX) | 3.2 |
| 3.4 | Deploy VCF Operations from SDDC Manager | 3.3 |
| 3.5 | Deploy VCF Automation from SDDC Manager | 3.3 |

### Phase 4 — VCF Workload Domain

| Step | Action | Depends On |
|------|--------|-----------|
| 4.1 | Commission esxi-05, esxi-06, esxi-07 in SDDC Manager | 3.3 |
| 4.2 | Create workload domain via SDDC Manager | 4.1 |
| 4.3 | Validate workload domain health | 4.2 |

### Phase 5 — NSX Networking

| Step | Action | Depends On |
|------|--------|-----------|
| 5.1 | Deploy NSX Edge cluster (2x Edge VMs) on workload domain | 4.3 |
| 5.2 | Configure Tier-0 gateway with BGP uplink to vEOS | 5.1 |
| 5.3 | Configure BGP neighbor on Arista vEOS | 5.2 |
| 5.4 | Configure Tier-1 gateway linked to Tier-0 | 5.2 |
| 5.5 | Verify BGP adjacency and route exchange | 5.3 |
| 5.6 | Configure NSX VPC | 5.4, 5.5 |

### Phase 6 — VKS

| Step | Action | Depends On |
|------|--------|-----------|
| 6.1 | Create subscribed content library for VKr images | 5.6 |
| 6.2 | Enable Supervisor on workload domain cluster | 5.6 |
| 6.3 | Create vSphere Namespace with VM classes and storage policies | 6.2 |
| 6.4 | Deploy VKS cluster via Cluster v1beta1 API | 6.3, 6.1 |
| 6.5 | Verify VKS cluster health, deploy test workload | 6.4 |

## 14. Open Questions & Risks

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | Arista vEOS licensing for lab use | Open | vEOS may require a licence key — check if lab/eval licence is available |
| 2 | vCD resource allocation approval | Open | 60 vCPU / 512 GB RAM / 1.5 TB storage is substantial — needs org approval |
| 3 | Internet access from nested environment | Open | VKS content library and VCF depot sync require outbound internet — routing: nested VM → vEOS → jumpbox → vCD public network. NAT/masquerade on jumpbox may be needed |
| 4 | DNS resolution chain | Open | Jumpbox dnsmasq handles `lab.local` and forwards other queries upstream via NIC1. Nested VMs must not query external DNS directly |
| 5 | vCD private network MTU | Open | Must support jumbo frames (MTU ≥ 9000) for overlay and vSAN traffic — verify vCD portgroup settings |
| 6 | Nested ESXi performance | Risk | Nested virtualisation adds overhead — vSAN and overlay performance may be degraded. Acceptable for lab, not production-representative |
| 7 | VCF depot access | Open | VCF Installer and SDDC Manager need access to VMware depot for downloading bundles — may need offline bundle if internet access is restricted |
| 8 | step-ca certificate distribution | Open | Need automation to distribute root CA cert to ESXi hosts and appliances during deployment |
