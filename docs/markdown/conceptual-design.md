---
title: "VKS Lab"
subtitle: "Conceptual Design"
author: "dreamfold"
date: "March 2026"
---

# Conceptual Design

## 1. Purpose & Objectives

Demonstrate vSphere Kubernetes Services (VKS) on VMware Cloud Foundation (VCF) 9 with VCF Networking (NSX) VPC in a fully nested lab environment hosted on vCloud Director. The lab provides a self-contained platform for exploring vSphere Supervisor clusters, VKS cluster lifecycle, and NSX VPC networking — all within a single vApp.

## 2. Target Audience

- VMware platform engineers evaluating VCF 9 + VKS
- Network engineers exploring NSX VPC and Border Gateway Protocol (BGP) integration
- Anyone needing a portable nested VCF environment for testing

## 3. Key Capabilities

- End-to-end VCF 9 deployment (management + workload domains)
- VKS cluster provisioning via Supervisor and Cluster API
- NSX VPC with centralised Edge connectivity
- BGP peering between NSX and a virtual router for north-south routing
- Remote access via RDP to a management gateway

## 4. Requirements

| ID    | Requirement |
|-------|-------------|
| R-001 | Lab MUST be hosted entirely within a single vCloud Director vApp |
| R-002 | Lab MUST provide remote access via RDP to a management gateway |
| R-003 | Lab MUST provide Domain Name System (DNS), Network Time Protocol (NTP), and Certificate Authority (CA) services on the gateway |
| R-004 | Lab MUST deploy two VCF domains — management and workload |
| R-005 | Lab MUST deploy a VKS cluster via Supervisor with NSX VPC networking |
| R-006 | Lab MUST provide BGP peering between NSX Tier-0 Gateway and a virtual router for north-south routing |
| R-007 | Lab SHOULD use vSAN Express Storage Architecture (ESA) with Failures to Tolerate (FTT)=1 for all clusters |
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

**Data protection boundary**: vApp snapshots protect the entire lab state (all VM disks and memory) as a single unit. There is no file-level backup, no PersistentVolume-level snapshot or replication, and no NFS or shared storage for application data. vSAN FTT=1 RAID-1 protects against single host failure within a domain, but does not protect against cluster-wide failure, logical corruption, or accidental deletion of Kubernetes PersistentVolumes. Any workload with persistent data requirements beyond "disposable" should be treated as at-risk in this environment.

## 6. Constraints

| ID    | Constraint |
|-------|------------|
| C-001 | All resources provisioned from vCloud Director — no bare-metal infrastructure |
| C-002 | Nested virtualisation — ESXi hosts run as VMs with accepted performance degradation |
| C-003 | Single-site topology — one management domain and one workload domain |
| C-004 | Lab-grade only — not intended for production workloads or performance benchmarking |
| C-005 | Internet access required for VKS content library sync and VCF offline depot (`depot.vcf-gcp.broadcom.net`) |

## 7. Assumptions

| ID    | Assumption |
|-------|------------|
| A-001 | The vCloud Director provider supports nested virtualisation and jumbo frames (Maximum Transmission Unit (MTU) 9000) |
| A-002 | Sufficient vCD resources are available (338 vCPU, 906 GB RAM, 1.5 TB storage) |
| A-003 | VCF offline depot is reachable at `depot.vcf-gcp.broadcom.net` |
| A-004 | The lab.dreamfold.dev DNS zone is delegated or used internally only |

## 8. Functional Overview

### Remote Access

A dual-homed gateway provides external access to the lab environment. It serves as the single entry point — all other lab components are on an isolated internal network.

### Infrastructure Services

The lab requires DNS, NTP, and a certificate authority (CA). These services run on the gateway to minimise component count and because the gateway is dual-homed (reachable from both external and internal networks).

- **DNS** — authoritative for the `lab.dreamfold.dev` domain, forwards unknown queries upstream
- **NTP** — syncs to public time sources externally, serves time to all lab components internally
- **CA** — lightweight ACME-capable CA (step-ca) for issuing TLS certificates to VCF components

### Layer 3 Routing

A virtual router provides inter-Virtual LAN (VLAN) routing across all VCF network segments. It also participates in BGP peering with the NSX Tier-0 Gateway via Free Range Routing (FRR), enabling north-south connectivity from VPC workloads out through the lab to external networks.

### VCF Domains

Two VCF domains provide separation of concerns:

- **Management domain** — hosts VCF management components (vCenter, Software-Defined Data Center (SDDC) Manager, NSX Manager, VCF Operations, VCF Automation)
- **Workload domain** — hosts the NSX Edge cluster, Supervisor, and VKS workloads

### VKS Cluster

A VKS cluster deployed via the Supervisor demonstrates Kubernetes lifecycle management on VCF. The cluster uses NSX VPC for pod networking with centralised Edge connectivity.

## 9. Conceptual Architecture

```
                         ┌─────────────────────────────────────┐
                         │           vCloud Director            │
                         │             (vApp)                   │
                         │                                      │
    External Access ────►│  ┌──────────┐                        │
                         │  │ Gateway  │                        │
                         │  │ DNS/NTP  │                        │
                         │  │ CA       │                        │
                         │  └────┬─────┘                        │
                         │       │                              │
                         │  ┌────┴─────┐                        │
                         │  │ Virtual  │                        │
                         │  │ Router   │◄─── BGP ──┐            │
                         │  └────┬─────┘           │            │
                         │       │                 │            │
                         │  ┌────┴────────────┐  ┌─┴────────┐  │
                         │  │  Management     │  │ Workload │  │
                         │  │  Domain         │  │ Domain   │  │
                         │  │                 │  │          │  │
                         │  │  vCenter        │  │ vCenter  │  │
                         │  │  SDDC Mgr       │  │ NSX Mgr  │  │
                         │  │  NSX Mgr        │  │ Edges    │  │
                         │  │  VCF Operations │  │ VKS      │  │
                         │  │  VCF Automation │  │          │  │
                         │  └─────────────────┘  └──────────┘  │
                         └─────────────────────────────────────┘
```

Functional blocks and relationships — no network details. See [Logical Design](logical-design.md) for topology.

## 10. Deployment Approach

Deployment proceeds in six phases, each building on the previous:

1. **Foundation** — vApp creation, gateway, virtual router, infrastructure services
2. **Nested Compute** — ESXi host deployment and network preparation
3. **VCF Management Domain** — VCF Installer bringup of management components
4. **VCF Workload Domain** — host commissioning and workload domain creation
5. **NSX Networking** — Edge cluster, Tier-0/Tier-1 gateways, BGP, VPC
6. **VKS** — Supervisor enablement, namespace creation, VKS cluster deployment

See [Logical Design](logical-design.md) for phase details and [Delivery Guide](deliver.md) for step-by-step procedures.

## 11. Open Questions & Risks

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | FRR BGP compatibility with NSX Tier-0 | Open | Verify BGP session establishes correctly in nested environment |
| 2 | vCD resource allocation approval | Open | Substantial resource request — needs org approval |
| 3 | Internet access from nested environment | Resolved | Gateway IP masquerade provides outbound internet for all lab hosts via ens160 public NIC |
| 4 | VCF depot access | Resolved | Lab offline depot available at `depot.vcf-gcp.broadcom.net` |
| 5 | Nested ESXi performance | Risk | Nested virtualisation adds overhead — vSAN and overlay performance degraded. Acceptable for lab only |
| 6 | Certificate distribution | Resolved | ESXi hosts: automated by `esxi_prepare` role. VCF appliances: trust configured during bringup. Lab API calls use `validate_certs: false` |

## 12. Requirements Traceability Matrix

### Requirements → Design → Implementation → Verification

| Req. | Description | Design Decisions | Implementation (Deliver Guide) | Verification |
|------|-------------|-----------------|-------------------------------|-------------|
| R-001 | Lab hosted in single vCD vApp | VCD-01, VCD-02 | Phase 1 — vApp creation (§3.1) | vApp visible in vCD console |
| R-002 | Remote access via RDP gateway | NET-01, SVC-06 | Phase 1 — gateway deploy (§3.2) | RDP connection on port 3389 |
| R-003 | DNS, NTP, CA on gateway | NET-05, SVC-01, SVC-03, SVC-04, SVC-05 | Phase 1 — gateway services (§3.2.5–3.2.7) | `dig`, `chronyc sources`, `step ca health` |
| R-004 | Two VCF domains (mgmt + wld) | NET-03, NET-04, ESX-02, VCF-01, VCF-02, VCF-03, VCF-04 | Phase 3 (§5) + Phase 4 (§6) | SDDC Manager shows both domains Active |
| R-005 | VKS cluster via Supervisor with NSX VPC | VKS-01, VKS-02, VKS-03, VKS-04 | Phase 6 — Supervisor + VKS (§8) | `kubectl get nodes` shows 6 Ready |
| R-006 | BGP peering between NSX and gateway | NET-02, NSX-01, NSX-02 | Phase 5 — BGP config (§7.2–7.3) | `vtysh -c 'show ip bgp summary'` — Established |
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
| C-005 | Internet access for VKS/VCF sync | Deliver Guide §3.2b (gateway NAT/masquerade) |

### Assumption Verification

| Assumption | Description | Verification Method | Where Verified |
|------------|-------------|-------------------|----------------|
| A-001 | vCD supports nested virtualisation and jumbo frames | Deploy test VM, enable nested virt flag, ping with MTU 9000 | Deliver Guide §3.1 (vApp network creation) |
| A-002 | Sufficient vCD resources (338 vCPU, 906 GB RAM, 1.5 TB) | Check vCD tenant quota before deployment | Deliver Guide §2 prerequisites checklist |
| A-003 | VCF offline depot reachable | `curl -s https://depot.vcf-gcp.broadcom.net` from gateway | Deliver Guide §2 prerequisites #8 |
| A-004 | lab.dreamfold.dev DNS zone delegated or internal-only | Verify zone delegation or confirm internal-only use | Deliver Guide §2 prerequisites #4 |
