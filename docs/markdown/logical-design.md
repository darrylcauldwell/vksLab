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
   Internet         │                  vCD Private Network (Trunk)                    │
       │            │                        │              │                  │       │
       │            │              ┌─────────┼──────────────┼──────────┐       │       │
       ▼            │              │         │              │          │       │       │
  vCD Public Net    │              │  ┌──────────┐                    │       │       │
  ──────────────────┼──────────────┼──┤  Arista   │                    │       │       │
                    │              │  │  vEOS     │◄─── BGP ───┐      │       │       │
                    │              │  │  Router   │            │      │       │       │
                    │              │  │  ETH1+ETH2│            │      │       │       │
                    │              │  └──────────┘            │      │       │       │
                    │              │       │ NAT/Gateway       │      │       │       │
                    │              │       │ Inter-VLAN        │      │       │       │
                    │              │       │ Routing           │      │       │       │
                    │              │       ▼                    │      │       │       │
                    │              │  ┌──────────┐            │      │       │       │
                    │              │  │  Ubuntu   │            │      │       │       │
                    │              │  │  Jumpbox  │            │      │       │       │
                    │              │  │ CA/DNS/NTP│            │      │       │       │
                    │              │  └──────────┘            │      │       │       │
                    │              │       │                    │      │       │       │
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
| Ubuntu Jumpbox | 1 | CA, DNS, NTP, management desktop (internal only) |
| Arista vEOS | 1 | Internet gateway, NAT, port-forward, inter-VLAN routing, BGP peer |
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
| vCD Public | Org VDC external/routed | vEOS external interface (internet gateway, RDP port-forward) |
| vCD Private | Org VDC internal (isolated) | All inter-VM communication, carries VCF VLANs as trunk |

The vCD public network provides external reachability — only the vEOS router connects to it. The vCD private network is an isolated org VDC network that carries all internal lab traffic as a trunk — VLAN tagging is handled by the nested ESXi vSwitches and the Arista vEOS router.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-001 | VKS-VCD-RCMD-001 | All lab components run inside a single vCloud Director vApp | Simplifies lifecycle management — entire lab can be snapshot, powered off, or redeployed as a unit | Risk: Single vApp failure affects entire lab. Mitigation: Acceptable for lab use; snapshot before changes |
| R-001 | VKS-VCD-RCMD-002 | Two-network model: one public, one private (trunk) | Minimises vCD network objects while supporting full VLAN segmentation via trunk | Risk: Trunk misconfiguration breaks all internal traffic. Mitigation: Verify trunk MTU and VLAN pass-through during foundation phase |

## 3. Network Topology

### vEOS Internet Gateway

The Arista vEOS router is the only multi-homed device in the lab:

- **Ethernet1** (vCD private network, trunk): carries all VCF VLANs for inter-VLAN routing
- **Ethernet2** (vCD public network, DHCP): provides internet connectivity and external access

vEOS performs source NAT (masquerade) for all outbound traffic from internal VLANs via Ethernet2. Inbound RDP (TCP 3389) is port-forwarded from the vEOS public IP to the jumpbox at 10.0.10.2.

The Ubuntu jumpbox has a single NIC on the management VLAN (10.0.10.2). It does not perform IP forwarding — it is not a router. Its default gateway is vEOS (10.0.10.1).

### Arista vEOS Router

The vEOS router provides:

- **Internet gateway** — NAT/masquerade for outbound traffic via Ethernet2
- **Port-forwarding** — RDP (TCP 3389) from public IP to jumpbox 10.0.10.2
- **Inter-VLAN routing** between management, vMotion, and other VCF networks via SVIs
- **BGP peering** with the NSX Tier-0 gateway for north-south routing from VPC workloads
- **Default gateway** for all internal VMs including nested ESXi management interfaces

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

The jumpbox runs dnsmasq, authoritative for the `lab.dreamfold.dev` zone. Unknown queries are forwarded upstream via vEOS NAT (the jumpbox's default gateway routes to vEOS, which masquerades outbound traffic via Ethernet2). All nested VMs point to the jumpbox for DNS — they must not query external DNS directly.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-002 | VKS-NET-RCMD-001 | vEOS is the sole multi-homed device and internet gateway; RDP is port-forwarded to the jumpbox | Single ingress point simplifies security; jumpbox has no public NIC, reducing attack surface | Risk: vEOS outage removes all external and internet access. Mitigation: Acceptable for lab; vCD console access remains available |
| R-006 | VKS-NET-RCMD-002 | Arista vEOS provides inter-VLAN routing and BGP peering | Purpose-built network OS provides production-grade routing features (BGP, SVIs, ACLs) in a VM form factor | Risk: vEOS licensing may be required. Mitigation: Lab/evaluation licence available from Arista |
| R-004 | VKS-NET-REQD-003 | Six VLANs segment traffic by function | Matches VCF reference architecture VLAN model — management, vMotion, vSAN, host TEP, edge TEP, edge uplink | Risk: Over-segmentation for a lab. Mitigation: Required by VCF — cannot reduce without breaking bringup |
| R-004 | VKS-NET-REQD-004 | Jumbo frames (MTU 9000) for overlay and storage VLANs | Required for NSX Geneve encapsulation overhead and optimal vSAN performance | Risk: vCD private network must support MTU 9000. Mitigation: Verify provider portgroup MTU before deployment |
| R-003 | VKS-NET-RCMD-005 | dnsmasq on jumpbox provides authoritative DNS for lab.dreamfold.dev | Lightweight, simple configuration; upstream forwarding via vEOS NAT | Risk: Single DNS server — no redundancy. Mitigation: Acceptable for lab; dnsmasq restarts quickly |
| C-005 | VKS-NET-RCMD-006 | vEOS NAT/masquerade on Ethernet2 for all outbound internet traffic | Centralises internet access through a single device; all internal VLANs route to internet via vEOS | Risk: vEOS Ethernet2 failure removes all internet access. Mitigation: Acceptable for lab; vCD console remains available |
| R-002 | VKS-NET-RCMD-007 | vEOS port-forwards RDP (TCP 3389) to jumpbox 10.0.10.2 | Provides external remote desktop access without exposing jumpbox directly on public network | Risk: Port-forward misconfiguration blocks RDP access. Mitigation: Verify with `show ip nat translations` on vEOS |

## 4. Infrastructure Services Design

All three infrastructure services (DNS, NTP, CA) run on the Ubuntu jumpbox.

**Rationale**: The jumpbox sits on the management VLAN (10.0.10.2), reachable by all internal VMs. It uses the vEOS router (10.0.10.1) as its default gateway for upstream DNS forwarding and NTP synchronisation. Running all three services on one VM minimises resource consumption and component count.

| Service | Technology | Role |
|---------|------------|------|
| DNS | dnsmasq | Authoritative for `lab.dreamfold.dev`, forwards unknown queries upstream |
| NTP | chrony | Stratum 2 server, syncs to public pools externally, serves lab internally |
| CA | step-ca | ACME-capable CA for TLS certs across VCF components |

The CA root certificate must be distributed to ESXi hosts and management appliances during deployment.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-003 | VKS-SVC-RCMD-001 | All infrastructure services (DNS, NTP, CA) co-located on the jumpbox | Minimises VM count; jumpbox on management VLAN is reachable by all internal VMs; upstream access via vEOS NAT | Risk: Jumpbox overloaded or single point of failure. Mitigation: Services are lightweight; lab-grade availability is acceptable |
| R-009 | VKS-SVC-RCMD-002 | step-ca provides ACME-capable CA for TLS certificates | Automated certificate issuance via ACME protocol; avoids manual certificate management | Risk: Root CA compromise affects all lab TLS. Mitigation: Lab-only CA — no production trust chain |
| R-003 | VKS-SVC-RCMD-003 | chrony as NTP server syncing to public pools | Provides accurate time source for VCF components; stratum 2 sufficient for lab | Risk: Upstream NTP unreachable from nested environment. Mitigation: chrony maintains local time accuracy during short outages |

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

- **Mode**: vSAN OSA (Original Storage Architecture) — simpler for nested environments, well-proven
- **Storage policy**: Failures to Tolerate = 1 (RAID-1 mirroring)
- Each host contributes one capacity disk and one cache disk (flash-simulated)

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
| C-001 | VKS-ESX-REQD-001 | All ESXi hosts run as nested VMs on vCloud Director | Enables full VCF stack without dedicated hardware | Risk: Significant performance overhead from nested virtualisation. Mitigation: Acceptable for lab; not for benchmarking |
| R-004 | VKS-ESX-RCMD-002 | 4 hosts for management domain, 3 hosts for workload domain | Minimum for vSAN FTT=1; 4 management hosts provide headroom for management appliances | Risk: No N+1 redundancy. Mitigation: Lab-grade — host failure tolerated via vSAN RAID-1 |
| R-007 | VKS-ESX-RCMD-003 | vSAN OSA (Original Storage Architecture) with FTT=1 | Simpler than ESA for nested environments; well-proven with nested ESXi | Risk: RAID-1 doubles storage consumption. Mitigation: Sized capacity disks accordingly (200 GB each) |
| C-001 | VKS-ESX-RCMD-004 | Two vNICs per host — access (management) and trunk (all other VLANs) | Separates management from data traffic while minimising vNIC count | Risk: Single trunk NIC is a bandwidth bottleneck. Mitigation: Acceptable for lab traffic volumes |

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
| R-004 | VKS-VCF-RCMD-001 | Separate management and workload domains | VCF best practice — isolates lifecycle management from tenant workloads | Risk: Doubles resource consumption for vCenter and NSX Manager. Mitigation: Sized ESXi hosts to accommodate both |
| C-004 | VKS-VCF-RCMD-002 | Single-node NSX Manager in each domain | Minimum viable deployment — reduces resource consumption | Risk: No NSX Manager HA. Mitigation: Acceptable for lab; can redeploy NSX Manager from SDDC Manager if needed |
| R-004 | VKS-VCF-RCMD-003 | VCF Operations and VCF Automation deployed in management domain | Provides monitoring, capacity analytics, and IaC capabilities for the lab | Risk: Additional resource consumption. Mitigation: Optional components — can be removed if resources are constrained |
| R-004 | VKS-VCF-RCMD-004 | VCF Installer drives initial bringup then is decommissioned | Standard VCF deployment method — installer is temporary | Risk: Installer VM consumes resources during bringup. Mitigation: Remove after bringup to reclaim resources |

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

BGP provides dynamic route exchange: vEOS advertises lab infrastructure subnets to NSX, and NSX advertises VPC/overlay prefixes back. This gives VKS workloads a routed path out through the Edge cluster → Tier-0 → vEOS → internet (via NAT).

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
| R-006 | VKS-NSX-REQD-001 | Two-node NSX Edge cluster sized Large | Minimum for Active-Standby HA; Large sizing required for VKS workloads | Risk: Large Edges consume significant resources (8 vCPU, 32 GB each). Mitigation: Workload domain hosts sized accordingly |
| R-006 | VKS-NSX-RCMD-002 | Active-Standby Tier-0 with BGP uplink to vEOS | Provides dynamic route exchange; vEOS advertises infrastructure subnets, NSX advertises VPC prefixes | Risk: BGP misconfiguration breaks north-south routing. Mitigation: Verify adjacency and route tables in Phase 5 |
| R-008 | VKS-NSX-RCMD-003 | Centralised VPC connectivity model (via Edge cluster) | All north-south traffic traverses Edge — simpler than distributed model for lab | Risk: Edge cluster becomes throughput bottleneck. Mitigation: Acceptable for lab traffic volumes |
| R-008 | VKS-NSX-RCMD-004 | Source NAT on Tier-0 for outbound VPC traffic | Simplifies return routing — external networks see traffic from Tier-0 uplink IP | Risk: NAT hides source IPs. Mitigation: Acceptable for lab; can add specific SNAT rules if needed |

## 8. VKS Architecture

### Supervisor

The Supervisor is enabled on the workload domain cluster via vCenter. It uses NSX for networking and vSAN for storage.

### vSphere Namespace

A vSphere Namespace provides the tenancy boundary for VKS. It defines the allowed VM classes, storage policies, and content library for Kubernetes clusters within that namespace.

### Content Library

A subscribed content library provides Kubernetes release images (VKr — VMware Kubernetes releases). The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via vEOS NAT on Ethernet2).

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
| R-005 | VKS-K8S-REQD-001 | Supervisor enabled on workload domain cluster with NSX networking | Required for VKS; NSX provides pod networking via VPC | Risk: Supervisor enablement requires stable NSX and vSAN. Mitigation: Validate both before enabling Supervisor |
| R-005 | VKS-K8S-RCMD-002 | 3 control plane + 3 worker nodes for VKS cluster | HA control plane with 3 workers provides realistic cluster topology | Risk: 6 VMs consume significant workload domain resources. Mitigation: Use best-effort-medium VM class (2 vCPU, 8 GB) |
| R-005 | VKS-K8S-RCMD-003 | Subscribed content library for VKr images | Automatic sync of Kubernetes release images from VMware | Risk: Requires internet access from nested environment. Mitigation: Route via vEOS NAT on Ethernet2 |
| C-004 | VKS-K8S-RCMD-004 | best-effort-medium VM class for VKS nodes | Balances resource use against lab constraints | Risk: Insufficient resources for complex workloads. Mitigation: Scale VM class up if needed; monitor resource utilisation |
