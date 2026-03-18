---
title: "VKS Lab"
subtitle: "Logical Design"
author: "dreamfold"
date: "March 2026"
---

# Logical Design

## 1. Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                     vCloud Director vApp                        │
                    │                                                                 │
   Internet         │  ┌──────────┐    vCD Private Network (Trunk)                    │
       │            │  │  Ubuntu   │◄──────────────────────────────────────────┐       │
       │            │  │ Jumpbox   │         │              │                  │       │
       ▼            │  │DNS/DHCP/CA│         │              │                  │       │
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

See [Delivery Guide](deliver.md) for step-by-step deployment procedures with exact dependencies.

### Component Inventory

| Component | Quantity | Role |
|-----------|----------|------|
| Ubuntu Jumpbox | 1 | External access, CA, DNS, DHCP, NTP, secrets (OpenBao) |
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

## 2. vCloud Director Layer

### vApp Model

All lab VMs run inside a single vCloud Director vApp:

- 1x Ubuntu jumpbox
- 1x Arista vEOS router
- 7x nested ESXi hosts
- VCF management appliances (deployed during bringup onto nested ESXi)

### Two-Network Strategy

| Network | Type | Purpose |
|---------|------|---------|
| vCD Public | Org VDC external/routed | Jumpbox external access (RDP, SSH) |
| vCD Private | Org VDC internal (isolated) | All inter-VM communication, carries VCF VLANs as trunk |

The vCD public network provides external reachability. The vCD private network is an isolated org VDC network that carries all internal lab traffic as a trunk — VLAN tagging is handled by the nested ESXi vSwitches and the Arista vEOS router.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-001 | VCD-01 | All lab components run inside a single vCloud Director vApp | Simplifies lifecycle management — entire lab can be snapshot, powered off, or redeployed as a unit | Risk: Single vApp failure affects entire lab. Mitigation: Acceptable for lab use; snapshot before changes |
| R-001 | VCD-02 | Two-network model: one public, one private (trunk) | Minimises vCD network objects while supporting full VLAN segmentation via trunk | Risk: Trunk misconfiguration breaks all internal traffic. Mitigation: Verify trunk MTU and VLAN pass-through during foundation phase |
| R-010 | VCD-03 | vApp snapshot as primary backup and recovery mechanism | Single-operation capture of entire lab state (all VM disks and memory); restore path is revert + power-on sequence; RTO ≤ 30 minutes | Risk: Snapshot size grows with lab data; vCD snapshot storage limits may apply. Mitigation: Lab is disposable — full rebuild via delivery guide provides fallback (RTO ≤ 4h) |

## 3. Network Topology

### Dual-Homed Jumpbox Pattern

The Ubuntu jumpbox is dual-homed:

- **NIC1** (vCD public network): externally reachable via RDP/SSH
- **NIC2** (vCD private network): connects to the internal lab fabric on the management VLAN

All other lab VMs have a single NIC on the vCD private network. The jumpbox does not perform IP forwarding — it is not a router.

### Arista vEOS Router

The vEOS router sits on the vCD private network with a trunk port carrying all VCF VLANs. It provides:

- **Inter-VLAN routing** between management, vMotion, and other VCF networks via SVIs
- **BGP peering** with the NSX Tier-0 gateway for north-south routing from VPC workloads
- **Default gateway** for nested ESXi management interfaces

### VLAN Segmentation Strategy

Six VLANs segment traffic by function, each on its own /24 subnet:

| VLAN ID | Name | Purpose | MTU |
|---------|------|---------|-----|
| 10 | Management | ESXi management, vCenter, SDDC Manager, NSX Manager | Standard |
| 20 | vMotion | vMotion traffic | Jumbo |
| 30 | vSAN | vSAN storage traffic | Jumbo |
| 40 | Host Overlay | NSX host transport endpoint tunnels | Jumbo |
| 50 | Edge Overlay | NSX Edge TEP tunnels | Jumbo |
| 60 | Edge Uplink | NSX Tier-0 ↔ Arista vEOS BGP peering | Standard |

### MTU Strategy

- **Jumbo frames (9000)** for overlay and storage VLANs — vMotion, vSAN, Host TEP, Edge TEP. Required for encapsulation overhead.
- **Standard frames (1500)** for management and edge uplink VLANs — no encapsulation overhead.
- The vCD private network portgroup must allow jumbo frames (MTU ≥ 9000).

### DNS Resolution Chain

The jumpbox runs dnsmasq, authoritative for the `lab.dreamfold.dev` zone. Unknown queries are forwarded upstream via the jumpbox's external NIC. All nested VMs point to the jumpbox for DNS — they must not query external DNS directly.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-002 | NET-01 | Dual-homed jumpbox provides the only external entry point | Single ingress point simplifies security and avoids exposing VCF management interfaces directly | Risk: Jumpbox outage removes all external access. Mitigation: Acceptable for lab; vCD console access remains available |
| R-006 | NET-02 | Arista vEOS provides inter-VLAN routing and BGP peering | Purpose-built network OS provides production-grade routing features (BGP, SVIs, ACLs) in a VM form factor | Risk: vEOS licensing may be required. Mitigation: Lab/evaluation licence available from Arista |
| R-004 | NET-03 | Six VLANs segment traffic by function | Matches VCF reference architecture VLAN model — management, vMotion, vSAN, host TEP, edge TEP, edge uplink | Risk: Over-segmentation for a lab. Mitigation: Required by VCF — cannot reduce without breaking bringup |
| R-004 | NET-04 | Jumbo frames (MTU 9000) for overlay and storage VLANs | Required for NSX Geneve encapsulation overhead and optimal vSAN performance | Risk: vCD private network must support MTU 9000. Mitigation: Verify provider portgroup MTU before deployment |
| R-003 | NET-05 | dnsmasq on jumpbox provides authoritative DNS for lab.dreamfold.dev | Lightweight, simple configuration, dual-homed jumpbox can forward to upstream DNS | Risk: Single DNS server — no redundancy. Mitigation: Acceptable for lab; dnsmasq restarts quickly |

## 4. Infrastructure Services Design

All three infrastructure services (DNS, NTP, CA) run on the Ubuntu jumpbox.

**Rationale**: The jumpbox sits on the management VLAN (10.0.10.2), reachable by all internal VMs. It uses the vEOS router (10.0.10.1) as its default gateway for upstream DNS forwarding and NTP synchronisation. Running all services on one VM minimises resource consumption and component count.

| Service | Technology | Role |
|---------|------------|------|
| DNS | dnsmasq | Authoritative for `lab.dreamfold.dev`, forwards unknown queries upstream |
| DHCP | dnsmasq | Static MAC→IP reservations for ESXi hosts on VLAN 10 |
| NTP | chrony | Stratum 2 server, syncs to public pools externally, serves lab internally |
| CA | step-ca | ACME-capable CA for TLS certs across VCF components |
| Secrets | OpenBao (Docker) | KV secret store for passwords and credentials (REST API, port 8200) |

The Arista vEOS router (10.0.10.1) also serves as a secondary NTP source. VCF validation requires two NTP servers — the jumpbox chrony (primary) and vEOS NTP (secondary) satisfy this requirement.

The CA root certificate must be distributed to ESXi hosts and management appliances during deployment.

### OpenBao Secret Store

OpenBao (an open-source fork of HashiCorp Vault, licensed under MPL 2.0) runs as a Docker container on the jumpbox. It provides a centralised KV secret store for all lab credentials, accessible via REST API and the Python `hvac` library.

Secret paths:

| Path | Content |
|------|---------|
| `secret/esxi/root-password` | Shared root password for all ESXi hosts |
| `secret/vcenter/sso-password` | vCenter SSO administrator password |
| `secret/sddc-manager/admin-password` | SDDC Manager admin password |
| `secret/nsx/admin-password` | NSX Manager admin password |
| `secret/keycloak/admin-password` | Keycloak admin password |

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-003 | SVC-01 | All infrastructure services (DNS, NTP, CA, DHCP, secrets) co-located on the jumpbox | Minimises VM count; jumpbox on management VLAN is reachable by all internal VMs; upstream access via vEOS NAT | Risk: Jumpbox overloaded or single point of failure. Mitigation: Services are lightweight; lab-grade availability is acceptable |
| R-009 | SVC-02 | step-ca provides ACME-capable CA for TLS certificates | Automated certificate issuance via ACME protocol; avoids manual certificate management | Risk: Root CA compromise affects all lab TLS. Mitigation: Lab-only CA — no production trust chain |
| R-003 | SVC-03 | chrony as NTP server syncing to public pools | Provides accurate time source for VCF components; stratum 2 sufficient for lab | Risk: Upstream NTP unreachable from nested environment. Mitigation: chrony maintains local time accuracy during short outages |
| R-003 | SVC-04 | dnsmasq DHCP with static MAC→IP reservations for ESXi hosts | Eliminates manual IP configuration during ESXi deployment; hosts receive correct IP on first boot | Risk: MAC address mismatch prevents DHCP lease. Mitigation: Verify MAC assignments in vCD before first boot |
| R-003 | SVC-05 | vEOS as secondary NTP server (10.0.10.1) alongside jumpbox chrony (10.0.10.2) | VCF validation requires two NTP sources; vEOS provides a second time source with minimal additional configuration | Risk: vEOS NTP accuracy depends on upstream sync via Ethernet2. Mitigation: vEOS syncs to public NTP pools directly |
| R-002 | SVC-06 | OpenBao as centralised secret store for lab credentials | Provides secure, API-accessible password management; Python `hvac` library enables automation; open-source MPL 2.0 licence | Risk: Additional resource consumption (~200-500 MB RAM). Mitigation: Lightweight; jumpbox sized to accommodate |

## 5. Compute Design

### Nested ESXi Approach

All ESXi hosts run as VMs on vCloud Director. This enables the entire VCF stack to run without dedicated hardware. Nested virtualisation adds performance overhead that is acceptable for lab purposes.

### Management Domain (4 Hosts)

Four nested ESXi hosts form the management domain cluster. This is the minimum for vSAN with FTT=1 (RAID-1) while leaving headroom for management appliances.

Each host is sized to accommodate VCF management appliances:

- vCenter Server
- SDDC Manager
- NSX Manager (single node — lab-scale)
- VCF Operations
- VCF Automation

### Workload Domain (3 Hosts)

Three nested ESXi hosts form the workload domain cluster. This is the minimum for vSAN with FTT=1. These hosts run:

- NSX Edge cluster (2x Edge VMs, large-sized for VKS)
- Supervisor control plane VMs
- VKS worker nodes

### vSAN Design

- **Mode**: vSAN ESA (Express Storage Architecture) — single storage pool, NVMe-based, simplified management
- **Storage policy**: Failures to Tolerate = 1 (RAID-1 mirroring)
- Each host contributes one NVMe storage device to a single storage pool (no separate cache/capacity tiers)
- Nested environments require a mock HCL VIB and NVMe devices marked as SSD

### Host Networking Model

Each nested ESXi host has two virtual NICs:

| vNIC | Connected To | Carries |
|------|-------------|---------|
| vmnic0 | vCD private network (access mode) | Management traffic only |
| vmnic1 | vCD private network (trunk mode) | vMotion, vSAN, TEP, Edge VLANs |

Inside each ESXi host, a VDS (created during VCF bringup) maps VLANs to VMkernel ports:

| VMkernel | VLAN | Service |
|----------|------|---------|
| vmk0 | Management | Management |
| vmk1 | vMotion | vMotion |
| vmk2 | vSAN | vSAN |
| vmk3 | Host Overlay | Host TEP |

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| C-001 | ESX-01 | All ESXi hosts run as nested VMs on vCloud Director | Enables full VCF stack without dedicated hardware | Risk: Significant performance overhead from nested virtualisation. Mitigation: Acceptable for lab; not for benchmarking |
| R-004 | ESX-02 | 4 hosts for management domain, 3 hosts for workload domain | Minimum for vSAN FTT=1; 4 management hosts provide headroom for management appliances | Risk: No N+1 redundancy. Mitigation: Lab-grade — host failure tolerated via vSAN RAID-1 |
| R-007 | ESX-03 | vSAN ESA (Express Storage Architecture) with FTT=1 | Single storage pool eliminates cache/capacity tier management; NVMe-based; ESA is the VMware-recommended architecture for vSAN 8+ | Risk: Nested NVMe requires mock HCL VIB and SSD marking. Mitigation: Automated via esxi-prep tool; FakeSCSIReservations setting handles nested SCSI |
| C-001 | ESX-04 | Two vNICs per host — access (management) and trunk (all other VLANs) | Separates management from data traffic while minimising vNIC count | Risk: Single trunk NIC is a bandwidth bottleneck. Mitigation: Acceptable for lab traffic volumes |

## 6. VCF Domain Architecture

### Management vs Workload Domain Separation

VCF best practice separates management infrastructure from tenant workloads:

- **Management domain**: lifecycle management components. Created by the VCF Installer during initial bringup.
- **Workload domain**: application workloads, NSX Edges, Supervisor, and VKS. Created via SDDC Manager after the management domain is operational.

### Management Domain Components

| Component | Role |
|-----------|------|
| VCF Installer | Orchestrates initial deployment (temporary — removed after bringup) |
| vCenter Server | Management domain compute management |
| SDDC Manager | VCF lifecycle and domain management |
| NSX Manager | Management domain NSX (single node for lab) |
| VCF Operations | Monitoring, capacity, and analytics |
| VCF Automation | Infrastructure-as-code and self-service |

### Workload Domain Components

| Component | Role |
|-----------|------|
| vCenter Server | Workload domain compute management |
| NSX Manager | Workload domain NSX (single node for lab) |

### Deployment Method

The VCF Installer appliance drives the initial management domain bringup. It is deployed onto one of the management ESXi hosts and orchestrates vCenter, vDS, vSAN, SDDC Manager, and NSX Manager deployment.

The workload domain is created via SDDC Manager by commissioning the workload ESXi hosts into the free pool, then creating a new VI workload domain.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-004 | VCF-01 | Separate management and workload domains | VCF best practice — isolates lifecycle management from tenant workloads | Risk: Doubles resource consumption for vCenter and NSX Manager. Mitigation: Sized ESXi hosts to accommodate both |
| C-004 | VCF-02 | Single-node NSX Manager in each domain | Minimum viable deployment — reduces resource consumption | Risk: No NSX Manager HA. Mitigation: Acceptable for lab; can redeploy NSX Manager from SDDC Manager if needed |
| R-004 | VCF-03 | VCF Operations and VCF Automation deployed in management domain | Provides monitoring, capacity analytics, and IaC capabilities for the lab | Risk: Additional resource consumption. Mitigation: Optional components — can be removed if resources are constrained |
| R-004 | VCF-04 | VCF Installer drives initial bringup then is decommissioned | Standard VCF deployment method — installer is temporary | Risk: Installer VM consumes resources during bringup. Mitigation: Remove after bringup to reclaim resources |

## 7. NSX Networking Architecture

### Edge Cluster Model

Two NSX Edge VMs deployed on the workload domain cluster provide north-south routing capacity. Edges are sized Large to support VKS workload traffic.

### Gateway Hierarchy

```
NSX Tier-0 Gateway (Active-Standby)
    │
    ├── BGP peering with Arista vEOS
    │   (external connectivity)
    │
    └── NSX Tier-1 Gateway
            │
            ├── Route advertisement: connected subnets, NAT IPs, LB VIPs
            │
            └── NSX VPC
                    │
                    └── VKS pod and service networks
```

- **Tier-0**: Active-Standby HA mode, BGP uplink to vEOS, source NAT for outbound traffic
- **Tier-1**: Linked to Tier-0, advertises connected subnets, hosts NSX LB for Kubernetes services
- **VPC**: Centralised connectivity model — all north-south traffic traverses the Edge cluster

### BGP Design

| Parameter | vEOS | NSX Tier-0 |
|-----------|------|------------|
| Role | External peer | Internal peer |
| Advertisements | Connected subnets (all VLANs) | VPC/overlay prefixes |

BGP provides dynamic route exchange: vEOS advertises lab infrastructure subnets to NSX, and NSX advertises VPC/overlay prefixes back. This gives VKS workloads a routed path out through the Edge cluster → Tier-0 → vEOS → jumpbox.

### Centralised VPC Model

NSX VPC provides project-level network isolation for VKS workloads:

- **Connectivity**: Centralised (via Edge cluster) — not distributed
- **External connectivity**: Via Tier-0 BGP to vEOS
- **Subnets**: Created dynamically by VKS for pod and service networks
- **NAT**: Source NAT on Tier-0 for outbound traffic
- **Load balancing**: NSX LB via Tier-1 for Kubernetes services of type LoadBalancer

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-006 | NSX-01 | Two-node NSX Edge cluster sized Large | Minimum for Active-Standby HA; Large sizing required for VKS workloads | Risk: Large Edges consume significant resources (8 vCPU, 32 GB each). Mitigation: Workload domain hosts sized accordingly |
| R-006 | NSX-02 | Active-Standby Tier-0 with BGP uplink to vEOS | Provides dynamic route exchange; vEOS advertises infrastructure subnets, NSX advertises VPC prefixes | Risk: BGP misconfiguration breaks north-south routing. Mitigation: Verify adjacency and route tables in Phase 5 |
| R-008 | NSX-03 | Centralised VPC connectivity model (via Edge cluster) | All north-south traffic traverses Edge — simpler than distributed model for lab | Risk: Edge cluster becomes throughput bottleneck. Mitigation: Acceptable for lab traffic volumes |
| R-008 | NSX-04 | Source NAT on Tier-0 for outbound VPC traffic | Simplifies return routing — external networks see traffic from Tier-0 uplink IP | Risk: NAT hides source IPs. Mitigation: Acceptable for lab; can add specific SNAT rules if needed |

## 8. VKS Architecture

### Supervisor

The Supervisor is enabled on the workload domain cluster via vCenter. It uses NSX for networking and vSAN for storage.

### vSphere Namespace

A vSphere Namespace provides the tenancy boundary for VKS. It defines the allowed VM classes, storage policies, and content library for Kubernetes clusters within that namespace.

### Content Library

A subscribed content library provides Kubernetes release images (VKr — VMware Kubernetes releases). The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via vEOS → jumpbox → vCD public network).

### VKS Cluster Topology

The VKS cluster is deployed using the Cluster v1beta1 API:

- **Control plane**: 3 nodes (HA)
- **Workers**: 3 nodes
- **VM class**: Medium (balances resource use against lab constraints)
- **Storage**: vSAN Default policy
- **Networking**: NSX VPC subnet

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-005 | VKS-01 | Supervisor enabled on workload domain cluster with NSX networking | Required for VKS; NSX provides pod networking via VPC | Risk: Supervisor enablement requires stable NSX and vSAN. Mitigation: Validate both before enabling Supervisor |
| R-005 | VKS-02 | 3 control plane + 3 worker nodes for VKS cluster | HA control plane with 3 workers provides realistic cluster topology | Risk: 6 VMs consume significant workload domain resources. Mitigation: Use best-effort-medium VM class (2 vCPU, 8 GB) |
| R-005 | VKS-03 | Subscribed content library for VKr images | Automatic sync of Kubernetes release images from VMware | Risk: Requires internet access from nested environment. Mitigation: Route via vEOS → jumpbox → vCD public network |
| C-004 | VKS-04 | best-effort-medium VM class for VKS nodes | Balances resource use against lab constraints | Risk: Insufficient resources for complex workloads. Mitigation: Scale VM class up if needed; monitor resource utilisation |
