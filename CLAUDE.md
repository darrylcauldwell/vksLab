# DDA-VCF — Project Instructions

Documentation Driven Architecture (DDA) for VMware Cloud Foundation (VCF) 9.0 — a nested lab where the physical design document is both human-readable documentation and machine-readable configuration. Hosted in a vCloud Director vApp.

## Change Review Process (MANDATORY)

**Every change to automation or documentation must achieve two goals:**
1. **Do the desired thing** — the change achieves what was intended
2. **Cause no unintended consequences** — the change does not break anything else

**There is no urgency.** Speed of delivery is not a priority. Correctness is. If a change requires discussion, assumptions need validating, or uncertainty exists — stop, discuss with the user, and reach sufficient certainty before writing any code.

### Scope

This process applies to ALL changes in this project — Ansible playbooks, roles, templates, inventory, bringup specs, and documentation.

### Before proposing a change

1. **State the change** — what exactly will be modified and why
2. **State assumptions and uncertainty** — what assumptions are being made? What has not been verified? Be explicit. "I believe X but I have not confirmed it" is always better than presenting X as fact
3. **Trace the impact** — for each changed value, trace its consequences:
   - What other files reference this value or depend on it?
   - What downstream systems validate or consume it (e.g., VCF validation, dnsmasq, netplan)?
   - Could this change break connectivity, service startup, or bringup at any phase?
4. **Verify against documentation** — check VCF behaviour via the `localexpert` MCP tool before proposing changes to bringup specs, VDS configuration, or networking. If localexpert is unavailable, state "UNVERIFIED — could not check VCF docs" and discuss with the user before proceeding
5. **One logical change per commit** — do not bundle speculative or unrelated fixes together
6. **Flag destructive operations** — any ESXi network reset, VDS reconfiguration, or vSwitch modification must include an explicit warning about what will break if it fails and whether it is reversible

### Handling uncertainty

When uncertain about any aspect of a change:
- **Say so explicitly** — "I'm not sure this is correct because..."
- **Do not guess and present the guess as a solution** — a wrong change that wastes a 3-hour rebuild is far worse than pausing to discuss
- **Discuss until certainty is reached** — work through assumptions with the user. Ask questions. Research. There is no rush
- **If certainty cannot be reached**, state the remaining risk clearly and let the user decide whether to proceed

## Documentation Set

The five design documents in `docs/markdown/` form a cohesive set. Each document stands alone (a reader may open any single document), but they must remain consistent with each other.

| Document | TOGAF ADM Phase | Content |
|----------|----------------|---------|
| `conceptual-design.md` | Phase A — Architecture Vision | Requirements, constraints, assumptions, conceptual architecture, traceability matrix |
| `logical-design.md` | Phases B/C — Business & Information Systems Architecture | Logical components, design decisions with rationale, traceability to requirements |
| `physical-design.md` | Phase D — Technology Architecture | IP addressing, host specs, resource sizing, technology selections |
| `deliver.md` | Phases E/F — Opportunities, Solutions & Migration Planning | Phased deployment procedures, verification steps |
| `operate.md` | Phase H — Architecture Change Management | SOPs, lifecycle management, health checks, capacity management |

When adding new content, place it in the document that matches its TOGAF ADM phase. Design decisions belong in logical design (with Decision ID, justification, and risk/mitigation). Physical specs belong in physical design. Procedures belong in the delivery or operations guide.

### Cross-Document Consistency

When modifying any document in the set:

1. **Check if the change affects design requirements or decisions.** If it does, trace the impact across all five documents using the Requirements Traceability Matrix in `conceptual-design.md` Section 12.
2. **If the change is terminology, naming, or formatting** (not a design change), apply it consistently across all five documents in the same commit or commit series.
3. **Never leave documents out of sync.** A terminology change in one document without the corresponding change in others creates confusion for readers who cross-reference.

### Requirements Traceability

Every design decision must reference a requirement ID (e.g., R-005, C-002). Every requirement in `conceptual-design.md` must be traceable through the chain:

```
Requirement → Design Decision (logical-design.md) → Implementation (deliver.md) → Verification (deliver.md / operate.md)
```

The Requirements Traceability Matrix in `conceptual-design.md` Section 12 is the master index. When adding a new requirement, design decision, or procedure:
- Add the requirement to the matrix
- Assign a Decision ID (format: `XXX-NN`, e.g., `VKS-05`, `NET-06`)
- Reference the Decision ID in the logical/physical design
- Add implementation steps to the delivery guide
- Add verification steps to either the delivery guide or operations guide

### Design Decision Table Format

All design decision tables must include these columns:

| Column | Purpose |
|--------|---------|
| Req. | Requirement ID being addressed |
| Decision ID | Unique identifier (format: `XXX-NN`) |
| Design Decision | What was decided |
| Design Justification | Why this approach was chosen |
| Risk / Mitigation | What could go wrong and how to handle it |

Do not omit the justification or risk columns. A decision without rationale is not traceable; a decision without risk analysis is not complete.

### Diagrams

Diagrams use draw.io with the `.drawio.svg` dual-purpose format. Files are stored in `docs/diagrams/`:

| File type | Purpose |
|-----------|---------|
| `*.drawio.svg` | Single file — editable by draw.io AND renderable by GitHub/browsers as SVG |

**Export command**: `drawio --export --format svg --embed-diagram -o output.drawio.svg input.drawio`

**Rules**:
- Always use `.drawio.svg` format (not separate `.drawio` + `.svg` files)
- Embed in markdown using relative paths: `![Description](diagrams/filename.drawio.svg)`
- Diagram labels and component names must match the terminology used in the surrounding prose — when renaming a component or term, update every diagram that references it
- When replacing an ASCII diagram with a draw.io equivalent, remove the ASCII version in the same commit

### Cross-Document Link Integrity

Cross-references between documents must use relative paths (e.g., `[Logical Design](logical-design.md)`) and point to real section headings. When renaming or restructuring a section, search all five documents for references to the old heading and update them.

### Version-Specific References

When a procedure or configuration is version-dependent, specify the exact version (e.g., "VCF 9.0.1+", "ESXi 9.0"). Do not write version-generic instructions for version-specific behaviour. If a workaround applies only to certain versions, state the version range and note when it is no longer needed.

## Terminology

### VCF 9.0 Product Names

These terms have specific official names that must always be used in prose. Hostnames, CLI commands, config paths, and API endpoints are excluded — they reflect what the software actually uses.

| Short Form | Always Write | Notes |
|------------|-------------|-------|
| Cloud Builder | VCF Installer | Say "formerly Cloud Builder" only in historical context |
| VCF Ops | VCF Operations | Never abbreviate |
| VCF Auto | VCF Automation | Never abbreviate |
| VMware Kubernetes releases | VMware Kubernetes Runtime (VKr) | The old name is incorrect |

### Acronym Expansion Rules

Every acronym is expanded on **first use per document** (each document stands alone). After the first expansion, use the short form.

| Acronym | First Use Expansion |
|---------|-------------------|
| DDA | Documentation Driven Architecture (DDA) |
| VCF | VMware Cloud Foundation (VCF) |
| NSX | VCF Networking (NSX) |
| VKS | vSphere Kubernetes Services (VKS) |
| VKr | VMware Kubernetes Runtime (VKr) |
| SDDC | Software-Defined Data Center (SDDC) |
| VPC | Virtual Private Cloud (VPC) |
| BGP | Border Gateway Protocol (BGP) |
| FRR | Free Range Routing (FRR) |
| TEP | Tunnel Endpoint (TEP) |
| VLAN | Virtual LAN (VLAN) |
| MTU | Maximum Transmission Unit (MTU) |
| NVMe | Non-Volatile Memory Express (NVMe) |
| HCL | Hardware Compatibility List (HCL) |
| VIB | vSphere Installation Bundle (VIB) |
| OVA | Open Virtual Appliance (OVA) |
| DCUI | Direct Console User Interface (DCUI) |
| OIDC | OpenID Connect (OIDC) |
| SNAT | Source Network Address Translation (SNAT) |
| CSI | Container Storage Interface (CSI) |
| FCD | First Class Disk (FCD) |
| FTT | Failures to Tolerate (FTT) |
| DFW | Distributed Firewall (DFW) |
| VDS | vSphere Distributed Switch (VDS) |
| ESA | Express Storage Architecture (ESA) |
| NTP | Network Time Protocol (NTP) |
| CA | Certificate Authority (CA) |
| DNS | Domain Name System (DNS) |
| DHCP | Dynamic Host Configuration Protocol (DHCP) |

### Qualified Names on First Use

These component names require qualification on first use per document:

| Component | First Use | Subsequent |
|-----------|----------|------------|
| Supervisor | vSphere Supervisor | Supervisor |
| Tier-0 | NSX Tier-0 Gateway | Tier-0 |
| Tier-1 | NSX Tier-1 Gateway | Tier-1 |
| Identity Broker | VCF Identity Broker | Identity Broker |

### Vendor Terminology Verification

When introducing or changing VMware/Broadcom product terminology, verify against the official VCF documentation using the `localexpert` MCP tool (`query_knowledge`). Product names, feature names, and acronym expansions change between VCF releases — always check the ingested docs for the version this lab targets (VCF 9.0). If the localexpert Docker Compose stack is not running, start it first:

```bash
cd /Users/darrylcauldwell/Development/localExpert && docker compose up -d
```
