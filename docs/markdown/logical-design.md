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
       │            │  │ Gateway   │         │              │                  │       │
       ▼            │  │DNS/DHCP/CA│         │              │                  │       │
  vCD Public Net    │  │          ─┼─────────┤              │                  │       │
  ──────────────────┼──┼─ NIC1     │         │              │                  │       │
                    │  │  NIC2 ────┼─────┐   │              │                  │       │
                    │  └──────────┘     │   │              │                  │       │
                    │                    │   │              │                  │       │
                    │              ┌─────┼───┼──────────────┼──────────┐       │       │
                    │              │     ▼   ▼              ▼          │       │       │
                    │              │  ┌──────────┐                    │       │       │
                    │              │  │  Ubuntu   │                    │       │       │
                    │              │  │  Gateway  │◄─── BGP ───┐      │       │       │
                    │              │  │  (FRR) │            │      │       │       │
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
                    │              │  │  vCenter  SDDC Mgr       │  │   │       │       │
                    │              │  │  NSX Mgr  VCF Operations │  │   │       │       │
                    │              │  │  VCF Automation           │  │   │       │       │
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
| Ubuntu Gateway | 1 | External access, inter-Virtual LAN (VLAN) routing, Border Gateway Protocol (BGP) via Free Range Routing (FRR), Certificate Authority (CA), Domain Name System (DNS), Dynamic Host Configuration Protocol (DHCP), Network Time Protocol (NTP), identity (Keycloak) |
| Nested ESXi (Management) | 4 | VMware Cloud Foundation (VCF) management domain hosts |
| Nested ESXi (Workload) | 3 | VCF workload domain hosts |
| VCF Installer | 1 | Drives VCF bringup (temporary; formerly Cloud Builder) |
| vCenter Server | 2 | Management + workload domain |
| Software-Defined Data Center (SDDC) Manager | 1 | VCF lifecycle management |
| VCF Networking (NSX) Manager | 2 | Management + workload domain |
| NSX Edge VMs | 2 | North-south routing, Virtual Private Cloud (VPC) |
| VCF Operations | 1 | Monitoring and analytics |
| VCF Automation | 1 | Infrastructure automation |

## 2. vCloud Director Layer

### vApp Model

All lab VMs run inside a single vCloud Director vApp:

- 1x Ubuntu gateway
- 7x nested ESXi hosts
- VCF management appliances (deployed during bringup onto nested ESXi)

### Two-Network Strategy

| Network | Type | Purpose |
|---------|------|---------|
| vCD Public | Org VDC external/routed | Gateway external access (RDP, SSH) |
| vCD Private | Org VDC internal (isolated) | All inter-VM communication, carries VCF VLANs as trunk |

The vCD public network provides external reachability. The vCD private network is an isolated org VDC network that carries all internal lab traffic as a trunk — VLAN tagging is handled by the nested ESXi vSwitches and the gateway VLAN sub-interfaces.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-001 | VCD-01 | All lab components run inside a single vCloud Director vApp | Simplifies lifecycle management — entire lab can be snapshot, powered off, or redeployed as a unit | Risk: Single vApp failure affects entire lab. Mitigation: Acceptable for lab use; snapshot before changes |
| R-001 | VCD-02 | Two-network model: one public, one private (trunk) | Minimises vCD network objects while supporting full VLAN segmentation via trunk | Risk: Trunk misconfiguration breaks all internal traffic. Mitigation: Verify trunk MTU and VLAN pass-through during foundation phase |
| R-010 | VCD-03 | vApp snapshot as primary backup and recovery mechanism | Single-operation capture of entire lab state (all VM disks and memory); restore path is revert + power-on sequence; RTO ≤ 30 minutes | Risk: Snapshot size grows with lab data; vCD snapshot storage limits may apply. Mitigation: Lab is disposable — full rebuild via delivery guide provides fallback (RTO ≤ 4h) |

## 3. Network Topology

### Dual-Homed Gateway Pattern

The Ubuntu gateway is dual-homed:

- **NIC1** (vCD public network): externally reachable via RDP/SSH
- **NIC2** (vCD private network): connects to the internal lab fabric on the management VLAN

All other lab VMs have a single NIC on the vCD private network. The gateway performs IP forwarding and inter-VLAN routing via VLAN sub-interfaces on ens34.

### Gateway Routing (FRR)

The gateway has a trunk interface (ens34, Maximum Transmission Unit (MTU) 9000) on the vCD private network carrying all VCF VLANs via 802.1Q sub-interfaces. It provides:

- **Inter-VLAN routing** between management, vMotion, and other VCF networks via VLAN sub-interfaces
- **BGP peering** with the NSX Tier-0 gateway for north-south routing from VPC workloads (via FRR)
- **Default gateway** for nested ESXi management interfaces
- **NAT** for outbound internet access via iptables masquerade on ens33

### VLAN Segmentation Strategy

Six VLANs segment traffic by function, each on its own /24 subnet:

| VLAN ID | Name | Purpose | MTU |
|---------|------|---------|-----|
| 10 | Management | ESXi management, vCenter, SDDC Manager, NSX Manager | Standard |
| 20 | vMotion | vMotion traffic | Jumbo |
| 30 | vSAN | vSAN storage traffic | Jumbo |
| 40 | Host Overlay | NSX host Tunnel Endpoint (TEP) tunnels | Jumbo |
| 50 | Edge Overlay | NSX Edge TEP tunnels | Jumbo |
| 60 | Edge Uplink | NSX Tier-0 ↔ Gateway BGP peering | Standard |

### MTU Strategy

- **Jumbo frames (9000)** for overlay and storage VLANs — vMotion, vSAN, Host TEP, Edge TEP. Required for encapsulation overhead.
- **Standard frames (1500)** for management and edge uplink VLANs — no encapsulation overhead.
- The vCD private network portgroup must allow jumbo frames (MTU ≥ 9000).

### DNS Resolution Chain

The gateway runs dnsmasq, authoritative for the `lab.dreamfold.dev` zone. Unknown queries are forwarded upstream via the gateway's external NIC. All nested VMs point to the gateway for DNS — they must not query external DNS directly.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-002 | NET-01 | Dual-homed gateway provides the only external entry point | Single ingress point simplifies security and avoids exposing VCF management interfaces directly | Risk: Gateway outage removes all external access. Mitigation: Acceptable for lab; vCD console access remains available |
| R-006 | NET-02 | Gateway provides inter-VLAN routing (VLAN sub-interfaces) and BGP peering (FRR) | Consolidates routing onto the gateway — eliminates a separate router VM, saves 2 vCPU / 4 GB RAM, removes Arista licence dependency | Risk: FRR is less feature-rich than a dedicated network OS. Mitigation: Only basic L3 routing and BGP needed for lab |
| R-004 | NET-03 | Six VLANs segment traffic by function | Matches VCF reference architecture VLAN model — management, vMotion, vSAN, host TEP, edge TEP, edge uplink | Risk: Over-segmentation for a lab. Mitigation: Required by VCF — cannot reduce without breaking bringup |
| R-004 | NET-04 | Jumbo frames (MTU 9000) for overlay and storage VLANs | Required for NSX Geneve encapsulation overhead and optimal vSAN performance | Risk: vCD private network must support MTU 9000. Mitigation: Verify provider portgroup MTU before deployment |
| R-003 | NET-05 | dnsmasq on gateway provides authoritative DNS for lab.dreamfold.dev | Lightweight, simple configuration, dual-homed gateway can forward to upstream DNS | Risk: Single DNS server — no redundancy. Mitigation: Acceptable for lab; dnsmasq restarts quickly |

## 4. Infrastructure Services Design

All infrastructure services (DNS, NTP, CA, secrets, identity) run on the Ubuntu gateway.

**Rationale**: The gateway sits on the management VLAN (10.0.10.1), reachable by all internal VMs. Running all services on one VM minimises resource consumption and component count.

| Service | Technology | Role |
|---------|------------|------|
| DNS | dnsmasq | Authoritative for `lab.dreamfold.dev`, forwards unknown queries upstream |
| DHCP | dnsmasq | Static MAC→IP reservations for ESXi hosts on VLAN 10 |
| NTP | chrony | Stratum 2 server, syncs to public pools externally, serves lab internally |
| CA | step-ca | ACME-capable CA for TLS certs across VCF components |
| Secrets | 1Password (operator laptop) | Credentials retrieved via `community.general.onepassword` lookup plugin |
| OpenID Connect (OIDC) | Keycloak (Docker) | External identity provider; VCF Identity Broker federates SSO across all VCF components (HTTPS, port 8443) |

The CA root certificate must be distributed to ESXi hosts and management appliances during deployment.

### Credential Management

Lab credentials follow a two-tier model: **bootstrap** (simple, typed manually) and **runtime** (complex, injected by Ansible).

- **Bootstrap password**: A single, simple password stored in 1Password as "Lab Bootstrap". The operator types this into the vCD console during Ubuntu gateway install and into the ESXi Direct Console User Interface (DCUI) to set the initial root password. Ansible connects to hosts using this password.
- **Runtime passwords**: Complex, auto-generated passwords stored as separate 1Password items. Ansible injects these into VCF components during deployment. The `esxi_prepare` role (Phase 2) changes ESXi root passwords from bootstrap to runtime credentials so that VCF bringup specs reference the correct values.
- **Derived credentials**: Service passwords that do not need to be stored in 1Password are derived deterministically from the bootstrap password via salted SHA-256 hash (e.g., `(bootstrap_password + 'step-ca') | hash('sha256')`). This ensures playbook idempotency — reruns produce the same password rather than generating a new random value that would desynchronise with previously initialised services.

### 1Password Secret Store

Lab credentials are stored in the operator's 1Password vault ("Employee"). Ansible retrieves them at runtime using the `community.general.onepassword` lookup plugin, which calls the 1Password CLI (`op`).

| Item Title | Fields | Purpose |
|------------|--------|---------|
| Lab Bootstrap | `password`, `ip_address` | Simple password for console/DCUI entry; gateway public IP |
| ESXi Root | `password` | Runtime root password for all ESXi hosts |
| vCenter SSO | `password` | vCenter SSO administrator password |
| SDDC Manager | `password` | SDDC Manager admin password |
| NSX Manager | `password` | NSX Manager admin password |
| Keycloak Admin | `password` | Keycloak admin password |

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-003 | SVC-01 | All infrastructure services (DNS, NTP, CA, DHCP, secrets) co-located on the gateway | Minimises VM count; gateway on management VLAN is reachable by all internal VMs; upstream access via iptables masquerade on public NIC | Risk: Gateway overloaded or single point of failure. Mitigation: Services are lightweight; lab-grade availability is acceptable |
| R-009 | SVC-02 | step-ca provides ACME-capable CA for TLS certificates | Automated certificate issuance via ACME protocol; avoids manual certificate management | Risk: Root CA compromise affects all lab TLS. Mitigation: Lab-only CA — no production trust chain |
| R-003 | SVC-03 | chrony as NTP server syncing to public pools | Provides accurate time source for VCF components; stratum 2 sufficient for lab | Risk: Upstream NTP unreachable from nested environment. Mitigation: chrony maintains local time accuracy during short outages |
| R-003 | SVC-04 | dnsmasq DHCP with static MAC→IP reservations for ESXi hosts | Eliminates manual IP configuration during ESXi deployment; hosts receive correct IP on first boot | Risk: MAC address mismatch prevents DHCP lease. Mitigation: Verify MAC assignments in vCD before first boot |
| R-003 | SVC-05 | Single NTP server on gateway (10.0.10.1) | Gateway chrony syncs to ntp.broadcom.net upstream and serves time to all lab VMs; VCF validation may require a second NTP entry — use ntp.broadcom.net as fallback if needed | Risk: Single NTP server — no local redundancy. Mitigation: chrony maintains local time accuracy during short upstream outages |
| R-002 | SVC-06 | 1Password as centralised secret store for lab credentials | Leverages existing 1Password subscription on operator laptop; `community.general.onepassword` Ansible lookup plugin; no in-lab infrastructure required | Risk: Requires 1Password CLI and active session on operator laptop. Mitigation: `op signin` before running playbooks |

### Identity and Access Management

Keycloak runs as a Docker container on the gateway (port 8443, HTTPS) and provides centralised identity for VCF management components. It replaces per-component local authentication with a single sign-on (SSO) experience via OIDC.

- **Realm**: A single `lab` realm contains all user accounts. There is no external LDAP or Active Directory — the lab has no domain controller.
- **Users**: Local Keycloak users are created for `admin` (full administrator) and `operator` (read-only / day-2 operations).
- **Integration**: The VCF Identity Broker (embedded in SDDC Manager) is configured with Keycloak as an external OIDC identity source. The Identity Broker federates SSO across all VCF components (vCenter, NSX Manager, SDDC Manager). A single OIDC client (`vcf-identity-broker`) in the `lab` realm handles the integration. Users authenticate via the Keycloak login page and receive an OIDC token validated against the discovery endpoint (`https://gateway.lab.dreamfold.dev:8443/realms/lab/.well-known/openid-configuration`).
- **Fallback**: Local administrator accounts (administrator@vsphere.local, NSX admin) remain available as a fallback if Keycloak is unavailable.

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-002 | SVC-07 | Keycloak as external OIDC identity provider, federated via VCF Identity Broker | Single sign-on reduces credential sprawl; Identity Broker (in SDDC Manager) provides a single integration point for all VCF components rather than per-component OIDC configuration | Risk: Keycloak container outage blocks SSO login. Mitigation: Local administrator accounts remain functional as fallback; Keycloak container configured with restart policy |
| C-004 | SVC-08 | Local Keycloak realm with local users (no AD/LDAP) | Lab has no domain controller; local users in a single realm provide the simplest identity model | Risk: No directory sync — user management is manual. Mitigation: Acceptable for lab with a small number of operators |
| R-009 | SVC-09 | step-ca max certificate duration set to 1 year (8760h) | Default step-ca provisioner limits certificates to 24 hours, which is too short for lab services like Keycloak that need stable TLS. 1-year duration avoids frequent renewal while remaining shorter than the 10-year root CA lifetime | Risk: Long-lived certificates are not rotated. Mitigation: Lab environment — acceptable; see [Operations Guide](operate.md) for renewal SOP |
| R-009 | SVC-10 | step-ca binds to 127.0.0.1 only | Avoids dependency on VLAN sub-interface readiness during startup; all certificate operations originate from the gateway itself | Risk: Remote ACME clients cannot reach step-ca directly. Mitigation: All cert issuance is performed by Ansible from the gateway; no remote ACME clients are needed |
| R-009 | SVC-11 | Keycloak container managed via Docker CLI (not community.docker Ansible module) | Avoids requiring the Python `docker` library on the gateway; reduces gateway package dependencies | Risk: Slightly less declarative than Ansible module. Mitigation: Idempotency achieved via `docker inspect` check before `docker run` |
| R-002 | SVC-12 | Bootstrap-to-runtime password rotation during ESXi preparation | ESXi hosts start with a simple bootstrap password (typed via DCUI) and are rotated to complex runtime credentials by the `esxi_prepare` role. VCF bringup specs then reference the runtime passwords | Risk: Phase 2 playbook cannot be rerun after password change without DCUI reset. Mitigation: Lab deployment is a one-pass process; DCUI reset is documented as fallback |
| R-002 | SVC-13 | Deterministic password derivation for service credentials | Service passwords (e.g., step-ca) are derived from the bootstrap password via salted SHA-256 hash rather than random generation. This ensures Ansible playbooks are idempotent — reruns produce the same password | Risk: Derived password security depends on bootstrap password entropy. Mitigation: Bootstrap password stored in 1Password; SHA-256 output provides sufficient complexity for lab services |
| R-002 | SVC-14 | GNOME + gnome-remote-desktop for Wayland-native RDP | Replaces X11-only XFCE + xrdp; gnome-remote-desktop is built into Ubuntu 24.04 GNOME; Wayland provides correct keyboard mapping and is the modern display protocol | Risk: gnome-remote-desktop is newer than xrdp. Mitigation: Ubuntu 24.04 ships it as default; fallback to xrdp is straightforward |

### Certificate Distribution

The step-ca root CA certificate must be trusted by ESXi hosts and VCF management appliances for TLS validation. The distribution mechanism spans two Ansible phases:

1. **Phase 1** (gateway role): step-ca generates the root CA during initialisation. The certificate is exported to a local path on the gateway and then fetched to the Ansible controller using `ansible.builtin.fetch`.
2. **Phase 2** (esxi_prepare role): The controller pushes the root CA certificate to each ESXi host via `ansible.builtin.copy`, then imports it into the ESXi trust store with `esxcli security cert import`.

This two-step fetch-then-push pattern is necessary because the Ansible `copy` module sources files from the controller, not from intermediate hosts.

## 5. Compute Design

### Nested ESXi Approach

All ESXi hosts run as VMs on vCloud Director. This enables the entire VCF stack to run without dedicated hardware. Nested virtualisation adds performance overhead that is acceptable for lab purposes.

### Management Domain (4 Hosts)

Four nested ESXi hosts form the management domain cluster. This is the minimum for vSAN with Failures to Tolerate (FTT)=1 (RAID-1) while leaving headroom for management appliances.

Each host is sized to accommodate VCF management appliances:

- vCenter Server
- SDDC Manager
- NSX Manager (single node — lab-scale)
- VCF Operations
- VCF Automation

### Workload Domain (3 Hosts)

Three nested ESXi hosts form the workload domain cluster. This is the minimum for vSAN with FTT=1. These hosts run:

- NSX Edge cluster (2x Edge VMs, large-sized for vSphere Kubernetes Services (VKS))
- vSphere Supervisor control plane VMs
- VKS worker nodes

### vSAN Design

- **Mode**: vSAN Express Storage Architecture (ESA) — single storage pool, NVMe-based, simplified management
- **Storage policy**: Failures to Tolerate = 1 (RAID-1 mirroring)
- Each host contributes one Non-Volatile Memory Express (NVMe) storage device to a single storage pool (no separate cache/capacity tiers)
- Nested environments require a mock Hardware Compatibility List (HCL) vSphere Installation Bundle (VIB) and NVMe devices marked as SSD

#### Storage Policy: "vSAN Default"

The default vSAN storage policy is applied to all VM home objects, VMDKs, and VKS PersistentVolumes unless overridden.

| Setting | Value | Rationale |
|---------|-------|-----------|
| Failures to Tolerate (FTT) | 1 | Minimum for data protection; RAID-1 mirror across 2 hosts |
| Failure Tolerance Method | RAID-1 (Mirroring) | Required at minimum host counts (3-4 hosts); RAID-5/6 requires ≥4 hosts and reduces write performance |
| Stripe Width | 1 | Default; no performance benefit from wider stripes in nested environment |
| Object Space Reservation | 0% (thin provisioning) | Maximises usable capacity in resource-constrained lab |
| Deduplication and Compression | Enabled (ESA default) | ESA performs inline dedup and compression at the storage pool level; reduces consumed capacity |
| Encryption at Rest | Disabled | Not required for lab; avoids KMS dependency and reduces CPU overhead |

#### ESA vs OSA

vSAN ESA (Express Storage Architecture) differs from the legacy OSA (Original Storage Architecture):

| Aspect | ESA | OSA |
|--------|-----|-----|
| Storage tiers | Single pool (no cache/capacity split) | Separate cache and capacity tiers |
| Dedup/compression | Always-on, inline, at pool level | Optional, per disk group |
| Device type | NVMe only | SAS/SATA/NVMe with dedicated cache device |
| Rebalancing | Operates on single pool — faster rebalance | Rebalances within disk groups, then across |
| Snapshots | Native efficient snapshots (no chain limits) | Legacy redo-log chain (depth limits) |
| Minimum vSAN version | vSAN 8+ / ESXi 8+ | All versions |

ESA was chosen (ESX-03) because it is the VMware-recommended architecture for new vSAN deployments on vSAN 8+ and eliminates the complexity of cache/capacity tier management.

#### vSAN Object Model and Data Placement

vSAN stores VM data as **objects**. Each VMDK, VM home namespace, and swap file is a separate vSAN object. With FTT=1 RAID-1, each object is stored as two mirrored **components** placed on different hosts, plus a **witness** on a third host.

```
Object (e.g., VM disk.vmdk)
  ├── Component (data replica) → Host A
  ├── Component (data mirror) → Host B
  └── Witness (metadata)      → Host C
```

**Quorum**: An object requires >50% of its votes to be accessible. With FTT=1 RAID-1 (2 data components + 1 witness = 3 votes), losing one host still leaves 2/3 votes — the object remains accessible. Losing two hosts drops below quorum and the object becomes inaccessible.

**3-host workload domain impact**: With exactly 3 hosts and FTT=1, losing a single host means:
- All objects remain accessible (2/3 quorum maintained)
- vSAN enters a **degraded** state — objects are not fully protected (only one data copy remains)
- vSAN cannot rebuild the missing components until the host returns or a new host is added
- A second host failure before rebuild completes would cause data loss

This is acceptable for a lab environment (C-004) where data is disposable and reproducible.

#### Nested vSAN Performance Expectations

Nested vSAN operates on virtual NVMe devices backed by the vCD provider's physical storage. Performance is fundamentally limited by:

1. **Double virtualisation overhead** — I/O passes through the nested ESXi storage stack, then the outer ESXi/vCD stack
2. **vCD provider storage backend** — IOPS and latency depend on the physical storage behind vCD (SAN, NFS, vSAN)
3. **Shared trunk NIC** — vSAN traffic (VLAN 30) shares the single trunk vNIC with vMotion, TEP, and Edge traffic

**Expected performance ranges** (highly variable by vCD provider):

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Read latency | 2-10 ms | vs <1 ms on bare-metal vSAN |
| Write latency | 5-20 ms | Higher due to FTT=1 synchronous mirror write |
| Random 4K IOPS | 500-2,000 | vs 50,000+ on bare-metal NVMe vSAN |
| Sequential throughput | 200-500 MB/s | Limited by trunk NIC bandwidth |

**This is not suitable for performance benchmarking** (C-002, C-004). Nested vSAN provides functional storage for VCF operations and VKS workloads but performance metrics are not representative of production environments.

#### Data Protection Boundary

The lab's data protection model is deliberately simple:

| Protection Layer | Method | Scope | Limitation |
|-----------------|--------|-------|------------|
| Entire lab state | vApp snapshot (VCD-03, R-010) | All VM disks + memory across entire vApp | All-or-nothing; cannot restore individual VMs or PVs |
| vSAN object level | FTT=1 RAID-1 mirroring | Protects against single host failure | Does not protect against vSAN cluster-wide failure or logical corruption |
| VKS PersistentVolume level | Velero + MinIO (VKS-12) | Namespace / label selector | CSI snapshot data movement; requires Velero schedule configuration |
| Application data level | Velero (application-consistent) | Per-namespace | Backs up Kubernetes resources + PV data; restore to same or different cluster |

**There is no NFS server or file-level backup infrastructure.** Kubernetes PersistentVolume backup is provided by Velero on the shared-services cluster (VKS-12) — see [Platform Services](#platform-services) in Section 8. The lab is designed to be disposable (C-004), but Velero provides namespace-level backup and restore for workloads with persistent data.

### Host Networking Model

Each nested ESXi host has two virtual NICs:

| vNIC | Connected To | Carries |
|------|-------------|---------|
| vmnic0 | vCD private network (access mode) | Management traffic only |
| vmnic1 | vCD private network (trunk mode) | vMotion, vSAN, TEP, Edge VLANs |

Inside each ESXi host, a vSphere Distributed Switch (VDS), created during VCF bringup, maps VLANs to VMkernel ports:

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
| R-007 | ESX-03 | vSAN ESA (Express Storage Architecture) with FTT=1 | Single storage pool eliminates cache/capacity tier management; NVMe-based; ESA is the VMware-recommended architecture for vSAN 8+ | Risk: Nested NVMe requires mock HCL VIB and SSD marking. Mitigation: Automated via Ansible esxi_prepare role; FakeSCSIReservations setting handles nested SCSI |
| C-001 | ESX-04 | Two vNICs per host — access (management) and trunk (all other VLANs) | Separates management from data traffic while minimising vNIC count | Risk: Single trunk NIC is a bandwidth bottleneck. Mitigation: Acceptable for lab traffic volumes |

## 6. VCF Domain Architecture

### Management vs Workload Domain Separation

VCF best practice separates management infrastructure from tenant workloads:

- **Management domain**: lifecycle management components. Created by the VCF Installer during initial bringup.
- **Workload domain**: application workloads, NSX Edges, vSphere Supervisor, and vSphere Kubernetes Services (VKS). Created via SDDC Manager after the management domain is operational.

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

### Edge HA Failover Behaviour

The NSX Tier-0 Gateway operates in **Active-Standby** mode across the two Edge VMs. Only the active Edge processes north-south traffic; the standby monitors and takes over on failure.

**Detection mechanism**: The NSX data plane uses BFD (Bidirectional Forwarding Detection) between the Active and Standby Edge VMs to detect failures. BFD operates at sub-second intervals (default: 500ms detect time). When BFD detects the active Edge is unreachable, the standby promotes itself to active.

**BGP session behaviour during failover**:

1. Active Edge fails → BFD detects failure (~500ms)
2. Standby Edge promotes to active (~2-4s)
3. New active Edge re-establishes the BGP session with the gateway (FRR) on VLAN 60
4. BGP hold timer (180s) on the gateway determines when stale routes are withdrawn
5. New BGP session establishes, routes are re-exchanged

**Expected convergence time**: In a nested lab environment, expect 30-60 seconds for full north-south traffic restoration. This includes BFD detection (~0.5s), Edge promotion (~2-4s), and BGP session re-establishment (variable, up to the hold timer). The BGP hold timer (180s) is the worst case for route withdrawal if the session never re-establishes.

**Graceful restart**: NSX supports BGP graceful restart, which allows the new active Edge to signal the peer (gateway FRR) that it is restarting BGP. FRR retains stale routes during the restart window rather than immediately withdrawing them, reducing traffic disruption.

### Gateway Hierarchy

```
NSX Tier-0 Gateway (Active-Standby)
    │
    ├── BGP peering with gateway (FRR)
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

- **Tier-0**: Active-Standby HA mode, BGP uplink to gateway (FRR), source NAT for outbound traffic
- **Tier-1**: Linked to Tier-0, advertises connected subnets, hosts NSX LB for Kubernetes services
- **VPC**: Centralised connectivity model — all north-south traffic traverses the Edge cluster

### BGP Design

| Parameter | Gateway (FRR) | NSX Tier-0 |
|-----------|------|------------|
| ASN | 65000 | 65001 |
| Router ID | 10.0.60.1 | 10.0.60.2 |
| Role | External peer (FRR) | Internal peer |
| Keepalive / Hold | 60s / 180s | 60s / 180s |
| Advertisements | Connected subnets (all VLANs) | VPC/overlay prefixes |

BGP provides dynamic route exchange: the gateway advertises lab infrastructure subnets to NSX, and NSX advertises VPC/overlay prefixes back. This gives VKS workloads a routed path out through the Edge cluster → Tier-0 → gateway.

**Timer selection**: Keepalive 60s / hold 180s (3× keepalive) are conservative values suited to a nested lab. Default BGP timers (60/180) provide tolerance for momentary delays caused by nested virtualisation overhead, vSAN latency spikes, or Edge VM resource contention. More aggressive timers (e.g., 10/30) would detect failures faster but risk false positives in a resource-constrained nested environment.

### Centralised VPC Model

NSX VPC provides project-level network isolation for VKS workloads:

- **Connectivity**: Centralised (via Edge cluster) — not distributed
- **External connectivity**: Via Tier-0 BGP to gateway
- **Subnets**: Created dynamically by VKS for pod and service networks
- **NAT**: Source NAT on Tier-0 for outbound traffic
- **Load balancing**: NSX LB via Tier-1 for Kubernetes services

### Source Network Address Translation (SNAT) Design

SNAT on the Tier-0 gateway translates outbound VPC traffic so that external networks (infrastructure VLANs, gateway, internet) see a single routable source IP — the Tier-0 uplink address.

| Parameter | Value |
|-----------|-------|
| SNAT source ranges | 192.168.0.0/16 (VKS pod CIDR), 10.96.0.0/12 (VKS service CIDR) |
| Translated IP | 10.0.60.2 (Tier-0 uplink interface on VLAN 60) |
| Applied on | Tier-0 gateway |
| Direction | Outbound (egress from VPC to external) |

**Why SNAT is required**: VPC pod and service CIDRs (192.168.0.0/16, 10.96.0.0/12) are internal overlay addresses. External networks (gateway, internet) cannot route return traffic to these addresses directly. SNAT translates the source to 10.0.60.2, which the gateway knows how to reach via the directly connected VLAN 60 sub-interface. Return traffic is reverse-NATted by the Tier-0 back to the original pod/service IP.

**Inbound traffic** to Kubernetes services uses NSX Load Balancer VIPs on the Tier-1 gateway. The LB VIP is a routable address advertised via Tier-1 → Tier-0 → BGP to the gateway, so inbound traffic does not require DNAT rules on the Tier-0.

### Route Redistribution Chain

VPC subnets must propagate from the overlay network through the gateway hierarchy to the physical network for end-to-end connectivity. The route redistribution chain is:

```
VPC Subnet (overlay)
  │
  ▼
Tier-1 Gateway
  │  Route advertisement: connected subnets, NAT IPs, LB VIPs
  ▼
Tier-0 Gateway
  │  Route redistribution: connected, static, NAT
  │  BGP advertisement to gateway
  ▼
Gateway / FRR (ASN 65000)
  │  Receives VPC prefixes via BGP
  │  Redistributes connected subnets back to NSX
  ▼
Infrastructure VLANs (10.0.10–60.0/24)
```

**Tier-1 route advertisement settings** (required):

| Setting | Value | Purpose |
|---------|-------|---------|
| Connected Subnets & Segment | Enabled | Advertises VPC subnets to Tier-0 |
| NAT IPs | Enabled | Advertises Tier-1 NAT addresses |
| LB VIPs | Enabled | Advertises Kubernetes LoadBalancer VIPs |

**Tier-0 route redistribution settings** (required):

| Setting | Value | Purpose |
|---------|-------|---------|
| Connected Subnets | Enabled | Redistributes Tier-0 connected interfaces into BGP |
| Static Routes | Enabled | Redistributes default route and any static routes |
| NAT IPs | Enabled | Redistributes SNAT translated IPs |
| Tier-1 Connected | Enabled | Redistributes Tier-1 advertised routes into BGP |

**Gateway route redistribution**: The FRR BGP configuration uses `redistribute connected` to advertise all VLAN sub-interface subnets (VLANs 10–60) to the NSX Tier-0. This gives the Tier-0 reachability to the infrastructure VLANs without requiring static routes.

### End-to-End Traffic Flow

#### North-South: Pod → Internet (Egress)

```
1. Pod (192.168.x.x) sends packet to external IP (e.g., 8.8.8.8)
   │
   ▼ Geneve encapsulation (overlay)
2. ESXi host TEP (VLAN 40) tunnels packet to Edge TEP (VLAN 50)
   │
   ▼ Geneve decapsulation at Edge VM
3. Tier-1 gateway routes to Tier-0 (connected subnet → parent gateway)
   │
   ▼ SNAT: source 192.168.x.x → 10.0.60.2
4. Tier-0 gateway forwards via uplink on VLAN 60 to next-hop 10.0.60.1 (gateway)
   │
   ▼ NAT: source 10.0.x.x → gateway public IP (iptables masquerade)
5. Gateway masquerades source IP via iptables and forwards via ens33 (public NIC) → internet
```

#### North-South: Internet → Pod (Ingress via LoadBalancer)

```
1. External client connects to Kubernetes LoadBalancer VIP (routable address)
   │
   ▼ Traffic arrives at gateway public NIC (if from internet)
2. Gateway routes to VIP via gateway (connected route for 10.0.60.0/24)
   │
   ▼ Gateway has BGP route (FRR) for VIP → next-hop 10.0.60.2
3. Gateway forwards to Tier-0 uplink (10.0.60.2) on VLAN 60
   │
   ▼ Standard L3 routing
4. Tier-0 forwards to Tier-1 (VIP is Tier-1 LB address)
   │
   ▼ NSX Load Balancer on Tier-1
5. Tier-1 LB distributes to backend pods
   │
   ▼ Geneve encapsulation (overlay)
6. Edge TEP (VLAN 50) tunnels to host TEP (VLAN 40) → pod receives packet
```

#### Encapsulation Transitions

| Segment | Encapsulation | Notes |
|---------|---------------|-------|
| Pod → ESXi host | Container networking (VPC overlay) | Pod-to-pod within same host is local |
| ESXi host → Edge VM | Geneve tunnel (VLAN 40 → VLAN 50) | NSX overlay, MTU 9000 required |
| Edge VM → Tier-0 uplink | Standard Ethernet (VLAN 60) | Geneve decapsulated at Edge; MTU 1500 |
| Tier-0 uplink → Gateway | Standard Ethernet (VLAN 60) | Routed L3, no encapsulation |
| Gateway ens34.60 → ens33 | IP forwarding + iptables masquerade | NAT for internet-bound |

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-006 | NSX-01 | Two-node NSX Edge cluster sized Large | Minimum for Active-Standby HA; Large sizing required for VKS workloads | Risk: Large Edges consume significant resources (8 vCPU, 32 GB each). Mitigation: Workload domain hosts sized accordingly |
| R-006 | NSX-02 | Active-Standby Tier-0 with BGP uplink to gateway (FRR) (keepalive 60s, hold 180s) | Provides dynamic route exchange; gateway advertises infrastructure subnets, NSX advertises VPC prefixes; conservative timers tolerate nested virtualisation overhead | Risk: BGP misconfiguration breaks north-south routing. Mitigation: Verify adjacency and route tables in Phase 5 |
| R-008 | NSX-03 | Centralised VPC connectivity model (via Edge cluster) | All north-south traffic traverses Edge — simpler than distributed model for lab | Risk: Edge cluster becomes throughput bottleneck. Mitigation: Acceptable for lab traffic volumes |
| R-008 | NSX-04 | Source NAT on Tier-0 for outbound VPC traffic | Simplifies return routing — external networks see traffic from Tier-0 uplink IP | Risk: NAT hides source IPs. Mitigation: Acceptable for lab; can add specific SNAT rules if needed |

## 8. VKS Architecture

### vSphere Supervisor

The vSphere Supervisor is enabled on the workload domain cluster via vCenter. It uses NSX for networking and vSAN for storage.

#### Supervisor Networking Stack

VCF 9 supports three networking stacks for the vSphere Supervisor. The choice determines available features, load balancer options, and network isolation capabilities.

| Capability | NSX with VPC | NSX (legacy) | vSphere Distributed Switch |
|------------|-------------|--------------|---------------------------|
| VKS cluster support | Yes | Yes | Yes |
| vSphere Pods | Yes | Yes | No |
| Network isolation model | VPC per project | Segment-based | VLAN / port group |
| Microsegmentation (DFW) | Yes | Yes | No |
| Routable pods | Yes | Yes | No |
| Multi-tenancy | VPC self-service | Manual | None |
| Load balancer options | NSX embedded, Avi | NSX embedded, Avi | Foundation, Avi |
| Edge cluster required | Yes | Yes | No |
| VCF Automation integration | Full | Limited | None |

The lab uses **NSX with VPC** — the recommended default for VCF 9. This provides VPC-based network isolation, microsegmentation via Distributed Firewall (DFW), and the NSX embedded load balancer for Kubernetes services. The NSX Edge cluster and Tier-0/Tier-1 gateways deployed in Phase 5 are prerequisites.

VDS was not selected because it lacks vSphere Pods support, microsegmentation, and requires a separate load balancer appliance. NSX (legacy) was not selected because NSX with VPC is the recommended architecture for new VCF 9 deployments and provides superior multi-tenancy and VCF Automation integration.

#### Load Balancer

The Supervisor networking stack determines which load balancers are available for Kubernetes Service type LoadBalancer. The choice is made at the Supervisor level and applies to all VKS clusters in the Supervisor.

| Capability | NSX Embedded | Avi (NSX Advanced LB) | Foundation LB |
|------------|-------------|----------------------|---------------|
| Networking stacks | NSX VPC, NSX | NSX VPC, NSX, VDS | VDS |
| Layer | L4 | L4 + L7 | L4 |
| Deployment model | Embedded in Tier-1 | Separate controller + SEs | 1–2 VMs on Supervisor |
| HA | Active-Standby (Tier-1) | Controller cluster (3-node) | Active-Passive (2 VMs) |
| Additional infrastructure | None (uses existing Edge) | Avi Controller VMs | Foundation LB VMs |
| Analytics | Basic (NSX Manager) | Advanced (Avi dashboard) | None |
| VCF entitlement | Included | Separate licence | Included |
| WAF / L7 policies | No | Yes | No |

The lab uses the **NSX embedded load balancer** — it is included with the VCF entitlement, requires no additional infrastructure beyond the existing NSX Edge cluster, and provides the L4 load balancing needed for Kubernetes services. Avi was not selected because it requires separate controller VMs and a licence — unnecessary overhead for a lab. Foundation LB is not available with the NSX VPC networking stack.

HAProxy is deprecated and not considered.

#### VKS Guest Cluster CNI

VKS clusters support three CNI options for pod networking inside guest clusters. The CNI operates independently of the Supervisor networking stack — all three options work with NSX VPC.

| Capability | Antrea | Calico | Antrea NSX Routed CNI |
|------------|--------|--------|----------------------|
| Data plane | Open vSwitch (OVS) | Linux iptables / eBPF | Open vSwitch (OVS) |
| Kubernetes NetworkPolicy | Yes | Yes | Yes |
| Cluster-wide policy (ACNP) | Yes | No | Yes |
| Tiered security policies | Yes | No | Yes |
| NSX Manager integration | Via Antrea-NSX Adapter | No | Via Antrea-NSX Adapter |
| Routable pod IPs | No (overlay) | No (overlay) | Yes (pods get IPs from NSX) |
| Windows node pools | Yes | No | No |
| Default | Yes (system-defined) | No (must specify) | No (must specify) |
| vDefend integration | Yes (with adapter) | No | Yes (with adapter) |

The lab uses **Antrea** — the system-defined default CNI. It provides Kubernetes NetworkPolicy support, advanced cluster-wide policies (ACNP), and optional NSX Manager integration via the Antrea-NSX Adapter. Calico was not selected because it lacks NSX integration and advanced policy tiers. The Antrea NSX Routed CNI was not selected because routable pod IPs are unnecessary for this lab — SNAT on the Tier-0 provides adequate outbound connectivity, and the LoadBalancer VIP provides inbound access.

### vSphere Namespace

A vSphere Namespace provides the tenancy boundary for VKS. It defines the allowed VM classes, storage policies, and content library for Kubernetes clusters within that namespace.

### Content Library

A subscribed content library provides Kubernetes release images — VMware Kubernetes Runtime (VKr). The library syncs from VMware's public endpoint. Internet access from the nested environment is required (routed via gateway → vCD public network).

### VKS Cluster Topology

The VKS cluster is deployed using the Cluster v1beta1 API:

- **Control plane**: 3 nodes (HA)
- **Workers**: 3 nodes
- **VM class**: Medium (balances resource use against lab constraints)
- **Storage**: vSAN Default policy
- **Networking**: NSX VPC subnet

### Persistent Storage (vSphere CSI)

VKS clusters use the **vSphere Container Storage Interface (CSI) driver** to provision PersistentVolumes from vSAN. The CSI driver is automatically installed when the Supervisor is enabled.

**How it works**: When a pod requests a PersistentVolumeClaim (PVC), the CSI driver creates a First Class Disk (FCD) — an independent VMDK on the vSAN datastore — and attaches it to the worker node VM as a virtual disk. The Kubernetes kubelet then mounts the formatted volume into the pod.

```
PVC (Kubernetes)
  │
  ▼ CSI CreateVolume
vSphere CSI Driver
  │
  ▼ CreateVolume → FCD (First Class Disk)
vSAN Datastore
  │
  ▼ AttachVolume → vSCSI device on worker VM
Worker Node → Pod mount
```

**StorageClass configuration**:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| provisioner | `csi.vsphere.vmware.com` | vSphere CSI driver |
| storagePolicyName | `vsan-default-storage-policy` | Maps to vSAN Default policy (FTT=1 RAID-1) |
| reclaimPolicy | `Delete` | PV is deleted when PVC is deleted (lab — no need to retain) |
| volumeBindingMode | `WaitForFirstConsumer` | Delays volume creation until pod is scheduled (ensures correct host placement) |
| allowVolumeExpansion | `true` | Permits online PV resize via PVC edit |

**PersistentVolume lifecycle**:

| Phase | Action | vSAN Impact |
|-------|--------|-------------|
| Provision | PVC created → CSI driver creates FCD on vSAN | New vSAN object (VMDK) with FTT=1 RAID-1 components |
| Attach | Pod scheduled → FCD attached to worker node VM | vSCSI hot-add; vSAN serves I/O from local or remote component |
| Use | Pod reads/writes the mounted volume | I/O traverses nested storage stack (pod → guest OS → nested ESXi → vCD) |
| Detach | Pod deleted or rescheduled → FCD detached from VM | vSCSI hot-remove; FCD remains on vSAN |
| Delete | PVC deleted with `reclaimPolicy: Delete` → FCD deleted | vSAN object removed; space reclaimed after dedup/compression cleanup |

> **Note**: PersistentVolumes inherit vSAN data protection (FTT=1) but have **no backup or snapshot mechanism** beyond vApp snapshots. Deleting a PVC permanently removes the data. See [Data Protection Boundary](#data-protection-boundary) in Section 5.

### Workload Security (AppArmor)

VKS worker nodes run Ubuntu with AppArmor enabled by default. AppArmor confines container processes to a mandatory access control profile that restricts file access, mount operations, network capabilities, and signal handling.

The lab enforces the **RuntimeDefault** AppArmor profile — the containerd default profile that:

- Blocks writing to `/proc` and `/sys` (except allowed paths)
- Prevents raw network socket creation
- Denies mount operations inside containers
- Restricts `ptrace` to same-container processes
- Allows normal file I/O, network connections, and process execution

This is set via the Kubernetes `securityContext.appArmorProfile` field (Kubernetes 1.30+, GA). VKS clusters on Ubuntu nodes inherit AppArmor support from the host OS — no additional installation is required.

### Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-005 | VKS-01 | Supervisor enabled on workload domain cluster with NSX networking | Required for VKS; Supervisor uses NSX VPC for namespace networking and load balancing (VKS-06, VKS-07); guest cluster pod networking uses Antrea CNI (VKS-08) | Risk: Supervisor enablement requires stable NSX and vSAN. Mitigation: Validate both before enabling Supervisor |
| R-005 | VKS-02 | 3 control plane + 3 worker nodes for VKS cluster | HA control plane with 3 workers provides realistic cluster topology | Risk: 6 VMs consume significant workload domain resources. Mitigation: Use best-effort-medium VM class (2 vCPU, 8 GB) |
| R-005 | VKS-03 | Subscribed content library for VKr images | Automatic sync of Kubernetes release images from VMware | Risk: Requires internet access from nested environment. Mitigation: Route via gateway → vCD public network |
| C-004 | VKS-04 | best-effort-medium VM class for VKS nodes | Balances resource use against lab constraints | Risk: Insufficient resources for complex workloads. Mitigation: Scale VM class up if needed; monitor resource utilisation |
| R-011 | VKS-05 | AppArmor RuntimeDefault profile enforced on all VKS workloads | Ubuntu VKS nodes ship with AppArmor enabled; RuntimeDefault provides baseline container confinement without custom profile management | Risk: RuntimeDefault may block workloads that require elevated privileges (e.g., privileged containers, raw sockets). Mitigation: Lab workloads are standard (nginx); privileged workloads can use `Unconfined` with explicit annotation |
| R-005 | VKS-06 | Supervisor networking stack: NSX with VPC | NSX VPC is the recommended default for VCF 9; provides VPC-based isolation, DFW microsegmentation, and NSX embedded LB without additional appliances | Risk: NSX VPC adds complexity vs. VDS. Mitigation: Lab already deploys NSX for Edge/Tier-0/Tier-1; VPC adds minimal incremental complexity |
| R-005 | VKS-07 | Load balancer: NSX embedded LB via Tier-1 | Included in VCF entitlement; no additional infrastructure beyond existing Edge cluster; L4 sufficient for lab Kubernetes services | Risk: NSX embedded LB is L4 only — no L7 routing, WAF, or advanced traffic management. Mitigation: Lab workloads require only L4; ingress controller can be added later if L7 is needed |
| R-005 | VKS-08 | VKS guest cluster CNI: Antrea (default) | System-defined default; provides NetworkPolicy, cluster-wide policies (ACNP), and optional NSX Manager integration via Antrea-NSX Adapter | Risk: Antrea is the only CNI choice if Windows node pools are needed later. Mitigation: Lab uses Linux only; Antrea is the most feature-rich option regardless |

### Platform Services

The lab deploys a set of platform services to support production-style workloads. These services run on a dedicated shared-services VKS cluster, separate from the application workload cluster.

#### Two-Cluster Topology

| Cluster | Purpose | Workloads |
|---------|---------|-----------|
| `vks-cluster-01` | Application workloads | planespotter, test deployments |
| `vks-services-01` | Platform infrastructure | Contour, Harbor, MinIO, Velero, ArgoCD |

Separating platform services from application workloads provides independent lifecycle management — platform services can be upgraded without disrupting applications. ArgoCD runs on the shared-services cluster as a hub and manages both clusters in a hub-and-spoke model.

#### Delivery Mechanism

Platform services are installed using two mechanisms:

| Mechanism | Services | Rationale |
|-----------|----------|-----------|
| VKS Standard Packages (`vcf package install`) | cert-manager, Contour, Harbor, Velero | VMware-supported, versioned, integrated with VKS lifecycle |
| Upstream Helm charts | ArgoCD, MinIO | Not available as VKS Standard Packages |

This keeps the lab aligned with VMware's supported ecosystem while using community charts only where necessary.

#### Ingress Controller

VKS clusters use the NSX embedded load balancer for L4 (Service type LoadBalancer). For L7 routing (host/path-based), an ingress controller is required. Contour sits **behind** the NSX embedded load balancer — NSX provisions an L4 VIP for the Envoy DaemonSet, and Envoy then routes L7 traffic by hostname/path. They complement each other.

| Capability | Contour + Envoy | Istio Gateway | NSX LB only (no ingress) |
|------------|----------------|---------------|--------------------------|
| L7 routing (host/path) | Yes (HTTPProxy CRD) | Yes (Gateway API) | No (L4 only) |
| TLS termination | Yes | Yes | Yes |
| Multi-service single VIP | Yes (hostname routing) | Yes | No (1 VIP per service) |
| gRPC support | Yes (h2c protocol) | Yes | No |
| VKS Standard Package | Yes (v1.33.1) | Yes (v1.28.2) | N/A (built-in) |
| Resource footprint | Light (~0.2 CPU, 0.3 Gi) | Heavy (~2 CPU, 2 Gi) | None |
| Complexity | Low | High (full service mesh) | None |

**Selection**: Contour (VKS Standard Package v1.33.1). L7 ingress with minimal footprint; HTTPProxy CRD enables multi-service routing through a single NSX LB VIP. Istio is overkill for a lab; NSX LB alone cannot do L7 routing.

#### Container Registry

Pulling container images directly from external registries (GHCR, Docker Hub) over the internet adds latency and is subject to rate limits. A local proxy cache accelerates pulls and provides vulnerability scanning.

| Capability | Harbor (proxy cache) | Direct pull from GHCR | Docker Registry (mirror) |
|------------|---------------------|----------------------|--------------------------|
| Local image cache | Yes | No | Yes |
| Vulnerability scanning | Yes (Trivy) | No | No |
| GHCR proxy cache | Yes (native provider) | N/A | Manual mirror config |
| Web UI | Yes (Portal) | N/A | No |
| Multi-registry support | Yes (Docker Hub, GHCR, Quay, etc.) | N/A | Single upstream |
| VKS Standard Package | Yes (v2.14.2) | N/A | No |
| Storage requirement | ~62 Gi PVC | None | ~50 Gi PVC |

**Selection**: Harbor (VKS Standard Package v2.14.2) with a `ghcr-proxy` project configured as a proxy cache for `ghcr.io`. Provides local caching, vulnerability scanning, and a single pull-through endpoint for all workload images (`harbor.lab.dreamfold.dev/ghcr-proxy/...`). Exposed via Contour HTTPProxy (shares the Envoy LB VIP).

#### Kubernetes Backup

The lab's data protection model (VCD-03) uses vApp snapshots for the entire lab state, but provides no PersistentVolume-level backup. Velero fills this gap for Kubernetes workloads by backing up both Kubernetes resources and PersistentVolume data.

| Capability | Velero + MinIO | vSAN snapshots only | VKSM Data Protection |
|------------|---------------|--------------------|--------------------|
| Kubernetes resource backup | Yes | No | Yes (wraps Velero) |
| PersistentVolume backup | Yes (CSI snapshot data movement) | Yes (vSAN object level) | Yes |
| Cross-cluster restore | Yes | No | Yes |
| S3-compatible storage | MinIO (in-cluster) | N/A | Required |
| Scheduled backups | Yes (cron) | Manual | Yes (policy-based) |
| VKS Standard Package | Yes (Velero v1.17.2) | N/A | Requires VCF Automation |
| Granularity | Namespace / label selector | Entire VM | Namespace |

**Selection**: Velero (VKS Standard Package v1.17.2) with MinIO (Helm chart) as in-cluster S3-compatible backup target. Container Storage Interface (CSI) snapshot support is pre-installed in VKS clusters. Velero backs up both Kubernetes resources and PV data. VKSM Data Protection wraps Velero but requires VCF Automation — unnecessary indirection for a lab.

MinIO runs as a single-pod deployment with a vSAN-backed PVC (~100 Gi). Velero's node-agent DaemonSet runs on each worker node (3 pods).

#### GitOps Deployment

Manual `kubectl apply` and Helm installs do not provide drift detection, audit trails, or multi-cluster management. A GitOps controller provides declarative, version-controlled application deployment.

| Capability | ArgoCD | Flux | Manual (kubectl/Helm) |
|------------|--------|------|-----------------------|
| Multi-cluster management | Yes (hub-and-spoke) | Yes (per-cluster) | Manual context switching |
| Web UI | Yes (dashboard) | No (CLI only) | No |
| Application CRD | Yes (Application, ApplicationSet) | Yes (Kustomization, HelmRelease) | No |
| Drift detection | Yes (real-time sync) | Yes (reconciliation loop) | No |
| OpenID Connect (OIDC) integration | Yes (Dex) | No | N/A |
| VKS ecosystem support | Broadcom operator available | No official VMware support | N/A |
| Community adoption | Largest CNCF GitOps project | Strong but smaller | N/A |

**Selection**: ArgoCD (upstream Helm chart v3.3.x). Installed on the shared-services cluster as a hub; manages both the shared-services and workload clusters. Web UI exposed via Contour HTTPProxy (shares the Envoy LB VIP). The Broadcom Supervisor Service operator bundles EOL v2.14.13 — the upstream Helm chart provides current v3.3.x.

#### Platform Services Design Decisions

| Req. | Decision ID | Design Decision | Design Justification | Risk / Mitigation |
|------|-------------|-----------------|----------------------|-------------------|
| R-012 | VKS-09 | Separate shared-services VKS cluster (`vks-services-01`) for platform infrastructure | Isolates platform services from application workloads; independent upgrade lifecycle; ArgoCD hub manages both clusters from a single control point | Risk: Second cluster doubles control plane resource consumption (+6 vCPU, +24 GB RAM). Mitigation: Workload domain headroom is sufficient (~35% CPU, ~53% RAM after second cluster) |
| R-014 | VKS-10 | Contour as L7 ingress controller (VKS Standard Package v1.33.1) | L7 host/path routing with minimal footprint; HTTPProxy CRD enables multi-service routing through a single NSX LB VIP; complements NSX embedded L4 LB | Risk: Contour is L7 only — does not replace NSX LB for L4 services. Mitigation: NSX LB remains the L4 default; Contour adds L7 on top |
| R-013 | VKS-11 | Harbor as container registry proxy cache (VKS Standard Package v2.14.2) | Local image caching reduces external pull latency and rate-limit exposure; Trivy vulnerability scanning provides image security; native GHCR proxy cache support | Risk: Harbor requires ~62 Gi persistent storage on vSAN. Mitigation: Workload domain vSAN has sufficient capacity; monitor via vSAN Capacity dashboard |
| R-015 | VKS-12 | Velero with MinIO for Kubernetes backup (VKS Standard Package v1.17.2 + Helm) | Backs up Kubernetes resources and PersistentVolume data; CSI snapshot integration with vSphere CSI driver; MinIO provides in-cluster S3-compatible storage without external dependencies | Risk: MinIO is a single-pod deployment — not HA. Mitigation: Lab-grade availability acceptable; vSAN FTT=1 protects the MinIO PVC data; backup metadata is recoverable from the PVC |
| R-016 | VKS-13 | ArgoCD for GitOps deployment (upstream Helm chart v3.3.x) | Hub-and-spoke multi-cluster management; web UI for visibility; OIDC integration via Dex for Keycloak SSO; largest CNCF GitOps community | Risk: Upstream Helm chart requires manual lifecycle management (not a VKS Standard Package). Mitigation: Helm upgrade is straightforward; ArgoCD can manage its own upgrades via self-management pattern |
| R-012 | VKS-14 | VKS Standard Packages as primary delivery mechanism | cert-manager, Contour, Harbor, and Velero installed via `vcf package install`; ArgoCD and MinIO via upstream Helm charts; aligns with VMware's supported ecosystem | Risk: Helm-installed components (ArgoCD, MinIO) are outside VMware support. Mitigation: Community-supported; lab-grade availability acceptable |
