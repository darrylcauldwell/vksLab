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
| R-007 | Lab SHOULD use vSAN ESA with FTT=1 for all clusters |
| R-008 | Lab SHOULD use NSX VPC with centralised Edge connectivity |
| R-009 | All TLS certificates SHOULD be issued by the internal step-ca CA |
| R-010 | Lab MAY be powered off, snapshot, and redeployed as a single vApp |

## 5. Service Level Objectives

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Availability** | Best-effort (no SLA) | Lab environment — acceptable to be offline during maintenance or experimentation |
| **RTO (full rebuild)** | ≤ 4 hours | Redeploy from scratch using delivery guide procedures |
| **RTO (snapshot restore)** | ≤ 30 minutes | Revert vApp snapshot and power-on sequence (R-010) |
| **RPO** | N/A | No persistent production data — lab state is disposable and reproducible |
| **Backup method** | vApp snapshot (R-010) | Single-operation backup of entire lab state including all VM disks and memory |

The lab is designed to be **disposable and reproducible**. The delivery guide enables a full rebuild from scratch; vApp snapshots provide a faster restore path for iterative experimentation. No traditional backup/replication infrastructure is required.

## 6. Constraints

| ID    | Constraint |
|-------|------------|
| C-001 | All resources provisioned from vCloud Director — no bare-metal infrastructure |
| C-002 | Nested virtualisation — ESXi hosts run as VMs with accepted performance degradation |
| C-003 | Single-site topology — one management domain and one workload domain |
| C-004 | Lab-grade only — not intended for production workloads or performance benchmarking |
| C-005 | Internet access required for VKS content library sync and VCF depot access |

## 7. Assumptions

| ID    | Assumption |
|-------|------------|
| A-001 | The vCloud Director provider supports nested virtualisation and jumbo frames (MTU 9000) |
| A-002 | Sufficient vCD resources are available (60 vCPU, 512 GB RAM, 1.5 TB storage) |
| A-003 | Arista vEOS lab/evaluation licence is available for router use |
| A-004 | VCF depot access is available (online or via offline bundles) |
| A-005 | The lab.dreamfold.dev DNS zone is delegated or used internally only |

## 8. Functional Overview

### Remote Access

A dual-homed jumpbox provides external access to the lab environment. It serves as the single entry point — all other lab components are on an isolated internal network.

### Infrastructure Services

The lab requires DNS, NTP, and a certificate authority (CA). These services run on the jumpbox to minimise component count and because the jumpbox is dual-homed (reachable from both external and internal networks).

- **DNS** — authoritative for the `lab.dreamfold.dev` domain, forwards unknown queries upstream
- **NTP** — syncs to public time sources externally, serves time to all lab components internally
- **CA** — lightweight ACME-capable CA (step-ca) for issuing TLS certificates to VCF components

### Layer 3 Routing

A virtual router provides inter-VLAN routing across all VCF network segments. It also participates in BGP peering with the NSX Tier-0 gateway, enabling north-south connectivity from VPC workloads out through the lab to external networks.

### VCF Domains

Two VCF domains provide separation of concerns:

- **Management domain** — hosts VCF management components (vCenter, SDDC Manager, NSX Manager, VCF Operations, VCF Automation)
- **Workload domain** — hosts the NSX Edge cluster, Supervisor, and VKS workloads

### VKS Cluster

A VKS cluster deployed via the Supervisor demonstrates Kubernetes lifecycle management on VCF. The cluster uses NSX VPC for pod networking with centralised Edge connectivity.

## 9. Conceptual Architecture

```
                         ┌──────────────────────────────────┐
                         │          vCloud Director          │
                         │            (vApp)                 │
                         │                                   │
    External Access ────►│  ┌──────────┐                     │
                         │  │ Jumpbox  │                     │
                         │  │ DNS/NTP  │                     │
                         │  │ CA       │                     │
                         │  └────┬─────┘                     │
                         │       │                           │
                         │  ┌────┴─────┐                     │
                         │  │ Virtual  │                     │
                         │  │ Router   │◄─── BGP ──┐         │
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

## 10. Deployment Approach

Deployment proceeds in six phases, each building on the previous:

1. **Foundation** — vApp creation, jumpbox, virtual router, infrastructure services
2. **Nested Compute** — ESXi host deployment and network preparation
3. **VCF Management Domain** — VCF Installer bringup of management components
4. **VCF Workload Domain** — host commissioning and workload domain creation
5. **NSX Networking** — Edge cluster, Tier-0/Tier-1 gateways, BGP, VPC
6. **VKS** — Supervisor enablement, namespace creation, VKS cluster deployment

See [Logical Design](logical-design.md) for phase details and [Delivery Guide](deliver.md) for step-by-step procedures.

## 11. Open Questions & Risks

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | Virtual router licensing for lab use | Open | May require a licence key — check if lab/eval licence is available |
| 2 | vCD resource allocation approval | Open | Substantial resource request — needs org approval |
| 3 | Internet access from nested environment | Open | VKS content library and VCF depot sync require outbound internet — routing path through jumpbox may need NAT/masquerade |
| 4 | VCF depot access | Open | VCF Installer and SDDC Manager need access to VMware depot — may need offline bundles if internet is restricted |
| 5 | Nested ESXi performance | Risk | Nested virtualisation adds overhead — vSAN and overlay performance degraded. Acceptable for lab only |
| 6 | Certificate distribution | Open | Need automation to distribute root CA cert to ESXi hosts and appliances during deployment |

## 12. Requirements Traceability Matrix

### Requirements → Design → Implementation → Verification

| Req. | Description | Design Decisions | Implementation (Deliver Guide) | Verification |
|------|-------------|-----------------|-------------------------------|-------------|
| R-001 | Lab hosted in single vCD vApp | VCD-01, VCD-02 | Phase 1 — vApp creation (§3.1) | vApp visible in vCD console |
| R-002 | Remote access via RDP jumpbox | NET-01, SVC-06 | Phase 1 — jumpbox deploy (§3.2) | RDP connection on port 3389 |
| R-003 | DNS, NTP, CA on jumpbox | NET-05, SVC-01, SVC-03, SVC-04, SVC-05 | Phase 1 — jumpbox services (§3.2.5–3.2.7) | `dig`, `chronyc sources`, `step ca health` |
| R-004 | Two VCF domains (mgmt + wld) | NET-03, NET-04, ESX-02, VCF-01, VCF-02, VCF-03, VCF-04 | Phase 3 (§5) + Phase 4 (§6) | SDDC Manager shows both domains Active |
| R-005 | VKS cluster via Supervisor with NSX VPC | VKS-01, VKS-02, VKS-03, VKS-04 | Phase 6 — Supervisor + VKS (§8) | `kubectl get nodes` shows 6 Ready |
| R-006 | BGP peering between NSX and vEOS | NET-02, NSX-01, NSX-02 | Phase 5 — BGP config (§7.2–7.3) | `show ip bgp summary` — Established |
| R-007 | vSAN ESA with FTT=1 | ESX-03 | Phase 2 — ESXi prep (§4.3) | `esxcli vsan health cluster list` green |
| R-008 | NSX VPC centralised Edge | NSX-03, NSX-04 | Phase 5 — VPC config (§7.5) | VPC shows Realised in NSX Manager |
| R-009 | TLS certs from internal step-ca | SVC-02 | Phase 1 — CA setup (§3.2.7) + cert distribution (§3.2a) | `step ca health`; certs valid on components |
| R-010 | vApp snapshot/redeploy | VCD-03 | Operate Guide — snapshot SOP (§1.3) | Snapshot restore + power-on completes successfully |

### Constraint Traceability

| Constraint | Description | Design Decisions |
|------------|-------------|-----------------|
| C-001 | All resources from vCD — no bare-metal | VCD-01, ESX-01, ESX-04 |
| C-002 | Nested virtualisation accepted | ESX-01, ESX-03 |
| C-003 | Single-site topology | VCF-01 |
| C-004 | Lab-grade only — not production | VCF-02, VKS-04 |
| C-005 | Internet access for VKS/VCF sync | Deliver Guide §3.2b (jumpbox NAT/masquerade) |

### Assumption Verification

| Assumption | Description | Verification Method | Where Verified |
|------------|-------------|-------------------|----------------|
| A-001 | vCD supports nested virtualisation and jumbo frames | Deploy test VM, enable nested virt flag, ping with MTU 9000 | Deliver Guide §3.1 (vApp network creation) |
| A-002 | Sufficient vCD resources (60 vCPU, 512 GB RAM, 1.5 TB) | Check vCD tenant quota before deployment | Deliver Guide §2 prerequisites checklist |
| A-003 | Arista vEOS lab/eval licence available | Obtain licence from Arista portal before deployment | Deliver Guide §2 prerequisites #6 |
| A-004 | VCF depot access available | Confirm online depot reachable or stage offline bundles | Deliver Guide §2 prerequisites #8 |
| A-005 | lab.dreamfold.dev DNS zone delegated or internal-only | Verify zone delegation or confirm internal-only use | Deliver Guide §2 prerequisites #4 |
