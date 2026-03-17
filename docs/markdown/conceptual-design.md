---
title: "VKS Lab"
subtitle: "Conceptual Design"
author: "dreamfold"
date: "March 2026"
---

# Conceptual Design

## 1. Purpose & Objectives

Demonstrate VMware Kubernetes Service (VKS) on VCF 9 with NSX VPC in a fully nested lab environment hosted on vCloud Director. The lab provides a self-contained platform for exploring Supervisor clusters, VKS cluster lifecycle, and NSX VPC networking — all within a single vApp.

## 2. Target Audience

- VMware platform engineers evaluating VCF 9 + VKS
- Network engineers exploring NSX VPC and BGP integration
- Anyone needing a portable nested VCF environment for testing

## 3. Key Capabilities

- End-to-end VCF 9 deployment (management + workload domains)
- VKS cluster provisioning via Supervisor and Cluster API
- NSX VPC with centralised Edge connectivity
- BGP peering between NSX and a virtual router for north-south routing
- Remote access via RDP to a management jumpbox

## 4. Requirements

| ID    | Requirement |
|-------|-------------|
| R-001 | Lab MUST be hosted entirely within a single vCloud Director vApp |
| R-002 | Lab MUST provide remote access via RDP to a management jumpbox |
| R-003 | Lab MUST provide DNS, NTP, and CA services on the jumpbox |
| R-004 | Lab MUST deploy two VCF domains — management and workload |
| R-005 | Lab MUST deploy a VKS cluster via Supervisor with NSX VPC networking |
| R-006 | Lab MUST provide BGP peering between NSX Tier-0 and a virtual router for north-south routing |
| R-007 | Lab SHOULD use vSAN OSA with FTT=1 for all clusters |
| R-008 | Lab SHOULD use NSX VPC with centralised Edge connectivity |
| R-009 | All TLS certificates SHOULD be issued by the internal step-ca CA |
| R-010 | Lab MAY be powered off, snapshot, and redeployed as a single vApp |

## 5. Constraints

| ID    | Constraint |
|-------|------------|
| C-001 | All resources provisioned from vCloud Director — no bare-metal infrastructure |
| C-002 | Nested virtualisation — ESXi hosts run as VMs with accepted performance degradation |
| C-003 | Single-site topology — one management domain and one workload domain |
| C-004 | Lab-grade only — not intended for production workloads or performance benchmarking |
| C-005 | Internet access required for VKS content library sync and VCF depot access |

## 6. Assumptions

| ID    | Assumption |
|-------|------------|
| A-001 | The vCloud Director provider supports nested virtualisation and jumbo frames (MTU 9000) |
| A-002 | Sufficient vCD resources are available (60 vCPU, 516 GB RAM, 1.5 TB storage) |
| A-003 | Arista vEOS lab/evaluation licence is available for router use |
| A-004 | VCF depot access is available (online or via offline bundles) |
| A-005 | The lab.dreamfold.dev DNS zone is delegated or used internally only |

## 7. Functional Overview

### Remote Access

The Arista vEOS router is the only multi-homed device in the lab — it has both an internal trunk interface and a public-facing interface with a DHCP address from vCloud Director. External RDP access arrives at the vEOS public IP and is port-forwarded to the jumpbox (10.0.10.2) on the management VLAN. All other lab components are on the isolated internal network.

### Infrastructure Services

The lab requires DNS, NTP, and a certificate authority (CA). These services run on the jumpbox to minimise component count. The jumpbox sits on the management VLAN, reachable by all internal VMs.

- **DNS** — authoritative for the `lab.dreamfold.dev` domain, forwards unknown queries upstream via vEOS NAT
- **NTP** — syncs to public time sources via vEOS NAT, serves time to all lab components internally
- **CA** — lightweight ACME-capable CA (step-ca) for issuing TLS certificates to VCF components

### Layer 3 Routing

The Arista vEOS router provides inter-VLAN routing across all VCF network segments and serves as the lab's internet gateway. It performs source NAT (masquerade) for outbound traffic from all internal VLANs via its public-facing interface. It also participates in BGP peering with the NSX Tier-0 gateway, enabling north-south connectivity from VPC workloads out through the Edge cluster to external networks.

### VCF Domains

Two VCF domains provide separation of concerns:

- **Management domain** — hosts VCF management components (vCenter, SDDC Manager, NSX Manager, VCF Operations, VCF Automation)
- **Workload domain** — hosts the NSX Edge cluster, Supervisor, and VKS workloads

### VKS Cluster

A VKS cluster deployed via the Supervisor demonstrates Kubernetes lifecycle management on VCF. The cluster uses NSX VPC for pod networking with centralised Edge connectivity.

## 8. Conceptual Architecture

```
                         ┌──────────────────────────────────┐
                         │          vCloud Director          │
                         │            (vApp)                 │
                         │                                   │
    External Access ────►│  ┌──────────┐                     │
                         │  │ Virtual  │                     │
                         │  │ Router   │◄─── BGP ──┐         │
                         │  │ (gateway)│           │         │
                         │  └────┬─────┘           │         │
                         │       │                 │         │
                         │  ┌────┴─────┐           │         │
                         │  │ Jumpbox  │           │         │
                         │  │ DNS/NTP  │           │         │
                         │  │ CA       │           │         │
                         │  └────┬─────┘           │         │
                         │       │                 │         │
                         │  ┌────┴──────────┐  ┌───┴──────┐  │
                         │  │  Management   │  │ Workload │  │
                         │  │  Domain       │  │ Domain   │  │
                         │  │               │  │          │  │
                         │  │  vCenter      │  │ vCenter  │  │
                         │  │  SDDC Mgr     │  │ NSX Mgr  │  │
                         │  │  NSX Mgr      │  │ Edges    │  │
                         │  │  VCF Ops      │  │ VKS      │  │
                         │  │  VCF Auto     │  │          │  │
                         │  └───────────────┘  └──────────┘  │
                         └──────────────────────────────────┘
```

Functional blocks and relationships — no network details. See [Logical Design](logical-design.md) for topology.

## 9. Deployment Approach

Deployment proceeds in six phases, each building on the previous:

1. **Foundation** — vApp creation, jumpbox, virtual router, infrastructure services
2. **Nested Compute** — ESXi host deployment and network preparation
3. **VCF Management Domain** — VCF Installer bringup of management components
4. **VCF Workload Domain** — host commissioning and workload domain creation
5. **NSX Networking** — Edge cluster, Tier-0/Tier-1 gateways, BGP, VPC
6. **VKS** — Supervisor enablement, namespace creation, VKS cluster deployment

See [Logical Design](logical-design.md) for phase details and [Delivery Guide](deliver.md) for step-by-step procedures.

## 10. Open Questions & Risks

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | Virtual router licensing for lab use | Open | May require a licence key — check if lab/eval licence is available |
| 2 | vCD resource allocation approval | Open | Substantial resource request — needs org approval |
| 3 | Internet access from nested environment | Resolved | vEOS NAT/masquerade on Ethernet2 (public NIC) provides outbound internet for all internal VLANs |
| 4 | VCF depot access | Open | VCF Installer and SDDC Manager need access to VMware depot — may need offline bundles if internet is restricted |
| 5 | Nested ESXi performance | Risk | Nested virtualisation adds overhead — vSAN and overlay performance degraded. Acceptable for lab only |
| 6 | Certificate distribution | Open | Need automation to distribute root CA cert to ESXi hosts and appliances during deployment |
