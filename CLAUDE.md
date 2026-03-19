# VKS Lab — Project Instructions

## Documentation Set

The five design documents in `docs/markdown/` form a cohesive set. Each document stands alone (a reader may open any single document), but they must remain consistent with each other.

| Document | Purpose |
|----------|---------|
| `conceptual-design.md` | Requirements, constraints, conceptual architecture |
| `logical-design.md` | Detailed logical architecture and design decisions |
| `physical-design.md` | IP addressing, host specs, resource tables |
| `deliver.md` | Step-by-step deployment procedures |
| `operate.md` | SOPs, health checks, troubleshooting, lifecycle |

### Cross-Document Consistency Rule

When modifying any document in the set:

1. **Check if the change affects design requirements or decisions.** If it does, trace the impact across all five documents using the Requirements Traceability Matrix in `conceptual-design.md`.
2. **If the change is terminology, naming, or formatting** (not a design change), apply it consistently across all five documents in the same commit or commit series.
3. **Never leave documents out of sync.** A terminology change in one document without the corresponding change in others creates confusion for readers who cross-reference.

### VCF 9.0 Terminology Rules

Every acronym is expanded on **first use per document** (each document stands alone). After the first expansion, use the short form.

| Term | First Use Form | Subsequent |
|------|---------------|------------|
| VCF | VMware Cloud Foundation (VCF) | VCF |
| NSX | VCF Networking (NSX) | NSX |
| VKS | vSphere Kubernetes Services (VKS) | VKS |
| VKr | VMware Kubernetes Runtime (VKr) | VKr |
| Supervisor | vSphere Supervisor | Supervisor |
| Tier-0 | NSX Tier-0 Gateway | Tier-0 |
| Tier-1 | NSX Tier-1 Gateway | Tier-1 |
| Identity Broker | VCF Identity Broker | Identity Broker |
| Cloud Builder | VCF Installer | VCF Installer |
| VCF Operations | VCF Operations | VCF Operations |
| VCF Automation | VCF Automation | VCF Automation |
| SDDC | Software-Defined Data Center (SDDC) | SDDC |
| VPC | Virtual Private Cloud (VPC) | VPC |
| BGP | Border Gateway Protocol (BGP) | BGP |
| FRR | Free Range Routing (FRR) | FRR |
| TEP | Tunnel Endpoint (TEP) | TEP |
| VLAN | Virtual LAN (VLAN) | VLAN |
| MTU | Maximum Transmission Unit (MTU) | MTU |
| NVMe | Non-Volatile Memory Express (NVMe) | NVMe |
| HCL | Hardware Compatibility List (HCL) | HCL |
| VIB | vSphere Installation Bundle (VIB) | VIB |
| OVA | Open Virtual Appliance (OVA) | OVA |
| DCUI | Direct Console User Interface (DCUI) | DCUI |
| OIDC | OpenID Connect (OIDC) | OIDC |
| SNAT | Source Network Address Translation (SNAT) | SNAT |
| CSI | Container Storage Interface (CSI) | CSI |
| FCD | First Class Disk (FCD) | FCD |
| FTT | Failures to Tolerate (FTT) | FTT |
| DFW | Distributed Firewall (DFW) | DFW |
| VDS | vSphere Distributed Switch (VDS) | VDS |
| ESA | Express Storage Architecture (ESA) | ESA |
| NTP | Network Time Protocol (NTP) | NTP |
| CA | Certificate Authority (CA) | CA |
| DNS | Domain Name System (DNS) | DNS |
| DHCP | Dynamic Host Configuration Protocol (DHCP) | DHCP |

**Prohibited short forms:**
- Never use "VCF Ops" — always "VCF Operations"
- Never use "VCF Auto" — always "VCF Automation"
- Never use "Cloud Builder" except in historical context (e.g., "formerly Cloud Builder")
- Never use "VMware Kubernetes releases" — the correct name is "VMware Kubernetes Runtime"

### Vendor Terminology Verification

When introducing or changing VMware/Broadcom product terminology, verify against the official VCF documentation at `https://docs.vmware.com/en/VMware-Cloud-Foundation/`. Product names, feature names, and acronym expansions change between VCF releases — always check the docs for the version this lab targets (VCF 9.0). Do not rely on memory or older documentation.

### TOGAF Architecture Framework Alignment

The document set follows TOGAF Architecture Development Method (ADM) structure:

| TOGAF Phase | Lab Document | Content |
|-------------|-------------|---------|
| Preliminary / Architecture Vision | `conceptual-design.md` | Purpose, requirements, constraints, stakeholders, conceptual architecture |
| Architecture Definition (B/C/D) | `logical-design.md` | Logical components, design decisions with rationale, traceability to requirements |
| Technology Architecture | `physical-design.md` | Physical specs, IP addressing, resource sizing, technology selections |
| Migration Planning / Implementation | `deliver.md` | Phased deployment procedures, verification steps |
| Architecture Change Management | `operate.md` | SOPs, lifecycle management, health checks, capacity management |

When adding new content, place it in the document that matches its TOGAF phase. Design decisions belong in logical design (with Decision ID, justification, and risk/mitigation). Physical specs belong in physical design. Procedures belong in the delivery or operations guide.

### Hostnames and CLI Output

Hostnames (e.g., `nsx-mgr-wld`, `vcf-ops`), CLI commands, config file paths, and API endpoints are **not renamed** — they reflect what the software actually uses. Only human-readable prose and labels follow the terminology rules above.
