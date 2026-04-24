# DDA-VCF

Documentation Driven Architecture (DDA) for VMware Cloud Foundation (VCF) 9.0 — a nested lab where the design documents are the configuration source.

## What is DDA?

The physical design document (`docs/markdown/physical-design.md`) is both human-readable documentation and machine-readable configuration. A custom Ansible vars plugin parses marked markdown tables at runtime, so there is no separate inventory or CMDB. Change a value in the design doc and Ansible picks it up — documentation and configuration can never diverge because they are the same artefact.

## Documentation Set

Five TOGAF-aligned design documents form a cohesive set. Each document stands alone; together they trace every decision from requirement through implementation to verification.

| Document | TOGAF Phase | PDF |
|----------|------------|-----|
| [Conceptual Design](docs/markdown/conceptual-design.md) | A — Architecture Vision | [PDF](docs/pdf/conceptual-design.pdf) |
| [Logical Design](docs/markdown/logical-design.md) | B/C — Business & Information Systems | [PDF](docs/pdf/logical-design.pdf) |
| [Physical Design](docs/markdown/physical-design.md) | D — Technology Architecture | [PDF](docs/pdf/physical-design.pdf) |
| [Delivery Guide](docs/markdown/deliver.md) | E/F — Solutions & Migration Planning | [PDF](docs/pdf/deliver.pdf) |
| [Operations Guide](docs/markdown/operate.md) | H — Architecture Change Management | [PDF](docs/pdf/operate.pdf) |

PDFs are regenerated automatically by CI on every push to `main`.

## Deployment Phases

Ansible playbooks automate the full deployment across 9 phases. Phases 0-3 run from the operator's laptop; phases 4-8 run via SOCKS proxy through the gateway.

| Phase | Playbook | What it does |
|-------|----------|-------------|
| 0 | `phase0_operator.yml` | Operator workstation setup |
| 1 | `phase1_foundation.yml` | Gateway services (DNS, NTP, CA, Keycloak, BGP) |
| 2 | `phase2_discover_macs.yml` | Discover ESXi MAC addresses from DHCP leases |
| 3 | `phase3_esxi.yml` | ESXi host identity, networking, storage |
| 4 | `phase4_vcf_mgmt.yml` | VCF Management Domain (VCF Installer bringup) |
| 5 | `phase5_vcf_platform.yml` | VCF Platform Services (VCF Ops, Identity, CA certs) |
| 6 | `phase6_vcf_workload.yml` | VCF Workload Domain (host commission, domain create) |
| 7 | `phase7_vcf_workload_nsx.yml` | VCF Workload NSX Networking (Edge, Tier-0/1, BGP, VPC) |
| 8 | `phase8_vcf_workload_vks.yml` | VCF Workload VKS (Supervisor, namespace, cluster) |

```bash
# Run a single phase
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/phase3_esxi.yml

# Run full deployment
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml
```

## Getting Started

1. Read the [Conceptual Design](docs/markdown/conceptual-design.md) for the architecture vision
2. Follow the [Delivery Guide](docs/markdown/deliver.md) for step-by-step deployment
3. See [`ansible/`](ansible/) for roles, the DDA vars plugin, and inventory configuration
