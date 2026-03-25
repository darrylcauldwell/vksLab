---
title: "VKS Lab"
subtitle: "Operations Guide"
author: "dreamfold"
date: "March 2026"
---

# Operations Guide

## 1. Standard Operating Procedures

### 1.1 Lab Power On Sequence (R-010, VCD-03)

The VMware Cloud Foundation (VCF) lab must be powered on in a specific order to ensure service dependencies are met.

| Order | Component | Action | Wait For |
|-------|-----------|--------|----------|
| 1 | Gateway | Power on VM | SSH/RDP accessible |
| 2 | Management ESXi hosts (esxi-01 to esxi-04) | Power on VMs | ESXi Direct Console User Interface (DCUI) shows management IP |
| 3 | Wait for vSAN cluster | Automatic | vSAN health green in vCenter |
| 4 | Management appliances auto-start | Automatic (HA/DRS) | vCenter, Software-Defined Data Center (SDDC) Manager, VCF Networking (NSX) Manager accessible |
| 5 | Workload ESXi hosts (esxi-05 to esxi-07) | Power on VMs | ESXi DCUI shows management IP |
| 6 | Wait for workload vSAN | Automatic | vSAN health green |
| 7 | Workload appliances auto-start | Automatic | Workload vCenter, NSX Manager accessible |
| 8 | NSX Edge VMs | Verify running | Border Gateway Protocol (BGP) adjacency re-established |
| 9 | vSphere Supervisor & vSphere Kubernetes Services (VKS) | Verify running | `kubectl get nodes` shows Ready on both clusters |
| 10 | Platform services (vks-services-01) | Verify pods running | Contour, Harbor, Velero, ArgoCD pods all Running |

### 1.2 Lab Power Off Sequence (Safe Shutdown)

**IMPORTANT**: vSAN clusters must be shut down gracefully to avoid data loss.

| Order | Component | Action | Verification |
|-------|-----------|--------|-------------|
| 1 | Platform services (vks-services-01) | Scale down ArgoCD, Velero schedule, Harbor | Platform service pods terminated |
| 2 | VKS workloads (vks-cluster-01) | Scale deployments to 0 or cordon/drain nodes | `kubectl get pods` shows no running pods |
| 3 | VKS clusters | (Optional) Delete VKS clusters or leave powered off | Cluster nodes powered off |
| 4 | Workload appliances | Shut down workload vCenter and NSX Manager | VMs powered off |
| 5 | Workload ESXi hosts | Put in maintenance mode (evacuate VMs first), then shut down | Hosts in maintenance, then powered off |
| 6 | Management appliances | Shut down VCF Operations, VCF Automation, NSX Manager, SDDC Manager, then vCenter (last) | All management VMs powered off |
| 7 | Management ESXi hosts | Put in maintenance mode, then shut down | Hosts powered off |
| 8 | Gateway | Power off (last) | VM stopped |

**vCenter must be the last management appliance shut down and the first to start up.**

### 1.3 Snapshot and Restore the Lab (R-010, VCD-03)

#### Taking a Snapshot

| Step | Action | Notes |
|------|--------|-------|
| 1 | Perform safe shutdown (Section 1.2) | All VMs powered off |
| 2 | In vCloud Director, select the vApp | — |
| 3 | Take vApp snapshot | Captures all VM states and disks |
| 4 | Label snapshot with date and description | e.g., "2026-03-17 — Post-VKS-deployment baseline" |
| 5 | Power on lab (Section 1.1) | Verify all services healthy |

#### Restoring from Snapshot

| Step | Action | Notes |
|------|--------|-------|
| 1 | Perform safe shutdown (Section 1.2) | All VMs powered off |
| 2 | In vCloud Director, revert vApp to snapshot | All VMs restored to snapshot state |
| 3 | Power on lab (Section 1.1) | Follow full startup sequence |
| 4 | Verify all services healthy | Use Ready for Operations checklist from Delivery Guide |

### 1.4 Add an ESXi Host to a Domain

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Deploy new nested ESXi VM with standard spec (24 vCPU, 128 GB RAM, 64 GB boot Non-Volatile Memory Express (NVMe) + 256 GB local NVMe + 2,048 GB vSAN NVMe) | VM powered on |
| 2 | Configure networking (management access + trunk) | Management IP pingable |
| 3 | Set hostname, Domain Name System (DNS) (10.0.10.1), Network Time Protocol (NTP) (10.0.10.1) | Services configured |
| 4 | Add DNS record to gateway dnsmasq | `dig` resolves new hostname |
| 5 | Commission host in SDDC Manager | Host appears in free pool |
| 6 | Expand the target domain cluster | Host added to cluster |
| 7 | Verify vSAN rebalance | vSAN health shows rebalancing, then green |

### 1.5 Remove an ESXi Host from a Domain

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Put host in maintenance mode (evacuate all VMs) | No VMs running on host |
| 2 | Wait for vSAN data evacuation | vSAN rebalance complete |
| 3 | Remove host from cluster via SDDC Manager | Host decommissioned |
| 4 | Remove DNS record from dnsmasq | Record removed |
| 5 | Power off and delete ESXi VM | Resources reclaimed |

### 1.6 Rebuild VKS Cluster (R-005, VKS-01 through VKS-04)

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Connect to Supervisor API | `kubectl vsphere login` succeeds |
| 2 | Delete existing VKS cluster | `kubectl delete cluster vks-cluster-01` |
| 3 | Wait for cluster deletion | All VKS VMs removed from vCenter |
| 4 | Apply VKS cluster manifest | `kubectl apply -f vks-cluster.yaml` |
| 5 | Wait for control plane (3 nodes) | `kubectl get machines` shows 3 Running |
| 6 | Wait for workers (3 nodes) | `kubectl get machines` shows 6 Running |
| 7 | Obtain new kubeconfig and verify | `kubectl get nodes` shows 6 Ready |
| 8 | Deploy test workload with AppArmor | `kubectl apply -f` test manifest | Pods running with RuntimeDefault profile |

### 1.7 NSX Edge Failover Verification (NSX-01, NSX-02)

Use this procedure to verify Active-Standby failover behaviour or to test resilience after changes.

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Identify active Edge | NSX Manager → System → Fabric → Edge Clusters → click cluster → note which Edge shows "Active" for NSX Tier-0 Gateway |
| 2 | Verify BGP adjacency before test | `sudo vtysh -c 'show ip bgp summary'` on gateway → Established with 10.0.60.2 |
| 3 | Start continuous ping from gateway | `ping -i 1 <VKS-LB-VIP>` (or any pod-reachable IP via Source Network Address Translation (SNAT)) |
| 4 | Power off the active Edge VM | vCenter → right-click active Edge VM → Power Off |
| 5 | Observe failover | NSX Manager → Edge Clusters → standby Edge promotes to Active (expect 2-4s) |
| 6 | Monitor BGP re-establishment | `sudo vtysh -c 'show ip bgp summary'` on gateway → watch for Established (expect 30-60s) |
| 7 | Verify traffic restoration | Continuous ping resumes; count lost packets (expect 30-60 lost at 1/sec) |
| 8 | Power on the failed Edge VM | vCenter → Power On; Edge rejoins cluster as Standby |
| 9 | Verify cluster health | NSX Manager → Edge Clusters → both Edges show Up |

> **Caution**: This test causes a brief north-south traffic outage. Perform during a maintenance window. Take a vApp snapshot first (Section 1.3).

### 1.8 Certificate Renewal SOP (R-009, SVC-02)

Certificates issued by the internal step-ca have a default lifetime. Renew before expiry to avoid service disruption.

#### Check Certificate Expiry

```bash
# List all active certificates and their expiry dates
step ca certificate list --expired=false

# Check a specific component's certificate
echo | openssl s_client -connect vcenter-mgmt.lab.dreamfold.dev:443 2>/dev/null | openssl x509 -noout -dates
```

#### Renew via ACME

For components that obtained certificates via ACME (step-ca automatic renewal):

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Check if `step ca renew` cron/timer is active on the gateway | `systemctl status step-ca-renew.timer` |
| 2 | If expired, manually renew | `step ca renew /path/to/cert.pem /path/to/key.pem --force` |
| 3 | Restart the affected service | Service responds with valid TLS |

#### Manual Certificate Renewal (VCF Components)

For VCF components (vCenter, NSX Manager, SDDC Manager) that use certificates issued by step-ca but do not auto-renew:

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Generate a new certificate from step-ca | `step ca certificate <fqdn> cert.pem key.pem` |
| 2 | Upload to the component via its management UI or API | Certificate updated |
| 3 | Restart the component's web service if required | UI accessible with new certificate |

#### Root Certificate Authority (CA) Certificate Rotation

If the step-ca root CA certificate approaches expiry or needs rotation:

| Step | Action | Notes |
|------|--------|-------|
| 1 | Generate new root CA on gateway | `step ca init` or use `step certificate create` for a new root |
| 2 | Export new root certificate | `step ca root /tmp/new-root-ca.crt` |
| 3 | Distribute to all ESXi hosts | `esxcli security cert import` on each host |
| 4 | Update VCF component trust stores | Via vCenter and NSX Manager certificate management |
| 5 | Re-issue all leaf certificates | Signed by the new root CA |
| 6 | Verify TLS connectivity across all components | Browse all management UIs; check for certificate warnings |

## 2. Lifecycle Management

> **Before any lifecycle operation**, take a vApp snapshot (R-010, VCD-03) as a rollback point. See Section 1.3.

### 2.1 ESXi Patching (vLCM)

VCF uses vSphere Lifecycle Manager (vLCM) for ESXi host updates.

| Step | Action | Notes |
|------|--------|-------|
| 1 | Check SDDC Manager for available updates | SDDC Manager → Lifecycle Management |
| 2 | Download update bundle | May require depot access or offline bundle |
| 3 | Review release notes and compatibility | Check VMware Interop Matrix |
| 4 | Take lab snapshot (Section 1.3) | Rollback point |
| 5 | Apply update to management domain first | SDDC Manager orchestrates host-by-host rolling update |
| 6 | Verify management domain health | vSAN health, all hosts connected |
| 7 | Apply update to workload domain | Same rolling update process |
| 8 | Verify workload domain health | vSAN health, VKS cluster healthy |

### 2.2 VCF Component Updates (SDDC Manager Lifecycle)

SDDC Manager coordinates updates to vCenter, NSX Manager, SDDC Manager itself, and other VCF components.

| Step | Action | Notes |
|------|--------|-------|
| 1 | Check SDDC Manager → Lifecycle Management → Updates | Available bundles listed |
| 2 | Download applicable bundles | — |
| 3 | Review update prerequisites | Check compatibility and order |
| 4 | Take lab snapshot | Rollback point |
| 5 | Apply updates in SDDC Manager-recommended order | Typically: SDDC Manager → NSX → vCenter → ESXi |
| 6 | Verify each component after update | Login and check version |

### 2.3 NSX Upgrade Path

| Step | Action | Notes |
|------|--------|-------|
| 1 | Check NSX upgrade coordinator | NSX Manager → System → Upgrade |
| 2 | Upload upgrade bundle | — |
| 3 | Run pre-checks | Coordinator validates environment |
| 4 | Take lab snapshot | — |
| 5 | Upgrade NSX Manager cluster | Coordinator handles rolling upgrade |
| 6 | Upgrade host transport nodes | Rolling upgrade, one host at a time |
| 7 | Upgrade Edge cluster | Rolling upgrade, one Edge at a time |
| 8 | Verify BGP adjacency after Edge upgrade | `sudo vtysh -c 'show ip bgp summary'` on gateway |
| 9 | Verify Virtual Private Cloud (VPC) and VKS connectivity | Test workload accessible |

### 2.4 VKS Kubernetes Version Upgrades

| Step | Action | Notes |
|------|--------|-------|
| 1 | Sync content library | New VMware Kubernetes Runtime (VKr) images appear |
| 2 | Check available Kubernetes versions | `kubectl get tkr` (TanzuKubernetesRelease) |
| 3 | Update cluster manifest with new version | Change `spec.topology.version` |
| 4 | Apply updated manifest | `kubectl apply -f vks-cluster.yaml` |
| 5 | Wait for rolling upgrade | Control plane nodes upgraded first, then workers |
| 6 | Verify cluster health | `kubectl get nodes` — all nodes Ready, new version |
| 7 | Verify workloads | `kubectl get pods` — all pods Running |

### 2.5 Gateway OS Patching

| Step | Action | Notes |
|------|--------|-------|
| 1 | SSH to gateway | — |
| 2 | `sudo apt update && sudo apt upgrade` | Review packages before confirming |
| 3 | Verify dnsmasq still running | `systemctl status dnsmasq` |
| 4 | Verify chrony still running | `systemctl status chronyd` |
| 5 | Verify step-ca still running | `step ca health` |
| 6 | Reboot if kernel update | `sudo reboot` |
| 7 | Verify all lab services post-reboot | DNS, NTP, CA, RDP all functional |

### 2.6 1Password Secret Store

Lab credentials are stored in the operator's 1Password vault ("Employee"). Ansible retrieves them at runtime via the `community.general.onepassword` lookup plugin.

#### Password Rotation

When VCF rotates a password (e.g., ESXi root password via SDDC Manager), update the corresponding 1Password item to keep secrets in sync:

```bash
op item edit "ESXi Root" --vault Employee password='<new-password>'
```

#### Verify Access

```bash
# Confirm 1Password CLI can read lab secrets
op item list --vault Employee
```

### 2.7 Platform Services Lifecycle

#### Harbor Garbage Collection

Harbor accumulates unused image layers over time. Run garbage collection periodically to reclaim storage.

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Login to Harbor UI at `https://harbor.lab.dreamfold.dev` | Dashboard loads |
| 2 | Navigate to **Administration** > **Garbage Collection** > **GC Now** | GC job starts |
| 3 | Wait for completion | Job status shows Success; freed space reported |

#### Velero Backup Schedule and Restore Testing

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Verify schedule is active: `velero schedule get` | `daily-backup` shows next run time |
| 2 | Check recent backups: `velero backup get` | At least one Completed backup within 24h |
| 3 | Test restore (dry run): `velero restore create test-restore --from-backup <latest> --dry-run` | Restore plan is generated without errors |
| 4 | Clean up: `velero restore delete test-restore` | Restore removed |

#### ArgoCD Cluster Registration

To register an additional VKS cluster with ArgoCD:

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Obtain kubeconfig for the target cluster | `kubectl get nodes` works against target |
| 2 | Register cluster: `argocd cluster add <context-name> --name <display-name>` | `argocd cluster list` shows the new cluster |
| 3 | Verify connectivity: `argocd cluster get <display-name>` | Status shows Successful |

#### VKS Standard Package Updates

VKS Standard Packages (cert-manager, Contour, Harbor, Velero) are updated via the `vcf package` CLI when new versions are available in the VMware Kubernetes Runtime (VKr) content library.

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Check available package versions: `vcf package available list` | New versions listed |
| 2 | Take a vApp snapshot (Section 1.3) | Rollback point |
| 3 | Update package: `vcf package install <package> --version <new-version>` | Package pods restart with new version |
| 4 | Verify service health after update | Service-specific health check passes |

## 3. Health Checks

### 3.1 Daily Checks

| # | Check | Method | Expected Result |
|---|-------|--------|-----------------|
| 1 | vSAN health (management) | vCenter → Cluster → Monitor → vSAN → Health | All green |
| 2 | vSAN health (workload) | vCenter → Cluster → Monitor → vSAN → Health | All green |
| 3 | ESXi host status | Both vCenters → Hosts and Clusters | All hosts Connected |
| 4 | VKS cluster status | `kubectl get nodes` | All nodes Ready |
| 5 | VKS system pods | `kubectl get pods -n kube-system` | All pods Running |
| 6 | SDDC Manager alerts | SDDC Manager → Dashboard | No critical alerts |
| 7 | Shared-services cluster status | `kubectl get nodes` on vks-services-01 | All nodes Ready |
| 8 | Contour pods | `kubectl get pods -n projectcontour` on vks-services-01 | All Running |
| 9 | Harbor health | `curl https://harbor.lab.dreamfold.dev/api/v2.0/health` | `{"status":"healthy"}` |

### 3.2 Weekly Checks

| # | Check | Method | Expected Result |
|---|-------|--------|-----------------|
| 1 | BGP adjacency | `sudo vtysh -c 'show ip bgp summary'` on gateway | Established |
| 2 | BGP routes received | `sudo vtysh -c 'show ip bgp'` on gateway | VPC prefixes present |
| 3 | DNS resolution | `dig @10.0.10.1 vcenter-mgmt.lab.dreamfold.dev` | Correct response |
| 4 | NTP synchronisation | `chronyc tracking` on gateway | System clock synchronised |
| 5 | ESXi NTP sync | `esxcli system ntp get` on each host | Server reachable |
| 6 | Certificate expiry (R-009) | `step ca certificate list` or check expiry dates | No certs expiring within 30 days |
| 7 | NSX Edge status | NSX Manager → Edge Clusters | Both Edges Up |
| 8 | Velero backup | `velero backup get` on vks-services-01 | Recent backup shows Completed |
| 9 | ArgoCD sync status | `argocd app list` | All apps Synced/Healthy |
| 10 | MinIO health | `mc admin info minio` | Connected, no errors |

### 3.3 Monthly Checks

| # | Check | Method | Expected Result |
|---|-------|--------|-----------------|
| 1 | vSAN capacity utilisation | vCenter → vSAN → Capacity | Below 80% used |
| 2 | ESXi host resource utilisation | vCenter → Performance → Cluster | CPU/RAM below 80% sustained |
| 3 | Datastore free space | vCenter → Storage | Adequate free space |
| 4 | VKS node resource usage | `kubectl top nodes` | No nodes at resource limits |
| 5 | VKS pod resource usage | `kubectl top pods --all-namespaces` | No runaway pods |
| 6 | SDDC Manager lifecycle updates | SDDC Manager → Lifecycle Management | Review available updates |
| 7 | VKr image updates | Sync content library, `kubectl get tkr` | Check for new Kubernetes versions |
| 8 | Snapshot cleanup | vCloud Director → vApp snapshots | Remove old snapshots to reclaim space |
| 9 | Harbor storage usage | Harbor UI → Projects → ghcr-proxy → Storage | Below 80% of PVC capacity |
| 10 | Velero backup retention | `velero backup get` | Old backups pruned per retention policy |

## 4. Troubleshooting

### 4.1 Common Issues

#### Nested ESXi Performance Degradation

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Slow VM operations | CPU contention on physical host | Check vCD host resource utilisation; reduce concurrent workloads |
| High vSAN latency | Nested disk I/O overhead | Expected for nested vSAN; reduce Failures to Tolerate (FTT) if capacity allows |
| vMotion timeouts | Network contention on trunk | Verify jumbo frame MTU end-to-end; check for frame drops |

#### vSAN Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| vSAN health warnings | Disk group degraded | Check `esxcli vsan health cluster list`; rebuild disk group if needed |
| Objects inaccessible | Insufficient hosts for FTT=1 | Ensure minimum 3 hosts (workload) or 4 hosts (management) are available |
| Resync stuck | Insufficient bandwidth or capacity | Wait for resync; check vSAN capacity; consider reducing object count |
| Network partition | Virtual LAN (VLAN) 30 misconfigured | Verify vmk2 on VLAN 30 across all hosts; check gateway VLAN sub-interface |

#### BGP Flapping

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| BGP session down | NSX Edge rebooted or network disruption | Check Edge VM status; verify VLAN 60 connectivity |
| Routes withdrawn | Tier-0 uplink interface down | Check NSX Tier-0 uplink status; verify Edge TEP connectivity |
| Frequent flaps | Hold/keepalive timers too aggressive | Increase BGP timers (hold: 180s, keepalive: 60s) |

#### NSX Fabric and VPC Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Transport node disconnected | Host Tunnel Endpoint (TEP) interface down | Check vmk3 (VLAN 40) on ESXi host; verify Maximum Transmission Unit (MTU) 9000 end-to-end |
| Transport node config not realised | NSX Manager communication failure | Restart nsx-proxy on ESXi host: `/etc/init.d/nsx-proxy restart` |
| VPC subnet not reachable | NSX Tier-1 Gateway route advertisement disabled | NSX Manager → Tier-1 → Route Advertisement: enable connected subnets |
| VPC to external connectivity broken | Tier-0 uplink down or NAT rule missing | Check Tier-0 uplink interface status; verify SNAT rule exists |
| Distributed Firewall (DFW) blocking traffic | Default DFW rule set to deny | NSX Manager → Security → Distributed Firewall: check default rule |

#### Content Library Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Content library sync failed | No internet access from vCenter | Verify NAT/masquerade on gateway; check gateway default route and iptables |
| Sync stuck at 0% | DNS resolution failure | Verify vCenter can resolve VMware CDN URLs via gateway DNS |
| VKr images not appearing | Library not subscribed or sync incomplete | Check subscription URL in vCenter → Content Libraries; trigger manual sync |
| Insufficient storage for sync | Datastore full | Check vSAN capacity; remove old/unused items from library |

#### VKS Node Not Ready

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Node shows NotReady | kubelet not running | SSH to node, check `systemctl status kubelet` |
| Node unreachable | NSX VPC connectivity issue | Check VPC status, verify Tier-0/Tier-1 routing |
| Pods stuck Pending | Insufficient node resources | Check `kubectl describe node`; consider scaling VM class |
| Image pull failures | No internet access from VPC | Verify NAT rule on Tier-0; check route to internet via gateway |

#### DNS Resolution Failures

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot resolve lab hostnames | dnsmasq not running | `sudo systemctl restart dnsmasq` on gateway |
| Upstream DNS fails | Gateway external NIC issue | Check ens33 connectivity; verify upstream DNS servers |
| Stale records | dnsmasq config not reloaded | Edit config, then `sudo systemctl restart dnsmasq` |
| VCF bringup DNS timeouts | IPv6 AAAA query delays | Lab is IPv4-only; AAAA queries to upstream servers can cause resolution delays. If bringup fails with DNS timeouts, check `/var/log/syslog` for slow AAAA responses and consider adding `filter-AAAA` to dnsmasq config (requires dnsmasq compiled with `--enable-filter-aaaa`) |

#### Dynamic Host Configuration Protocol (DHCP) Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| ESXi host not getting IP | MAC address mismatch | Verify MAC in vCD matches `dhcp-host` entry in `/etc/dnsmasq.d/lab.conf`; restart dnsmasq |
| Host gets wrong IP | Duplicate DHCP reservation | Check for duplicate MAC entries in dnsmasq config |
| DHCP lease expired | Host powered off too long | Restart dnsmasq; host will get new lease on next boot |
| No DHCP offers | dnsmasq not listening on VLAN 10 | Verify dnsmasq is bound to ens34 (management VLAN, native/untagged); check `dhcp-range` config |

#### 1Password Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot read secrets | Not signed in to 1Password CLI | `eval $(op signin)` |
| Vault not found | Wrong vault name | `op vault list` to verify vault name matches `Employee` |
| Ansible lookup fails | 1Password CLI not installed | `brew install --cask 1password-cli` |

#### Keycloak Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot login via SSO | Keycloak container not running | `docker start keycloak`; check `docker logs keycloak` |
| OpenID Connect (OIDC) token validation failed | Clock skew between gateway and VCF components | Verify NTP sync on gateway (`chronyc tracking`) and VCF appliances; ensure time delta is under 5 seconds |
| OIDC token validation failed | TLS certificate expired on Keycloak | Renew certificate: `step ca renew /etc/step-ca/certs/keycloak.crt /etc/step-ca/certs/keycloak.key --force`; restart Keycloak container |
| Users cannot authenticate | Realm misconfiguration or user disabled | Check Keycloak admin console → lab realm → Users; verify user is enabled and credentials are set |
| vCenter rejects OIDC provider | Discovery endpoint unreachable from vCenter | Verify vCenter can resolve `gateway.lab.dreamfold.dev` and reach port 8443; check firewall/routing |
| NSX Manager rejects OIDC provider | Client ID or secret mismatch | Verify client ID and secret in NSX OIDC config match the Keycloak client configuration |
| SSO works but user has no permissions | Role mapping missing | Check vCenter/NSX role mappings for the Keycloak user or group; add appropriate RBAC assignments |

### 4.2 Log Locations

| Component | Log Location | Access Method |
|-----------|-------------|---------------|
| ESXi | `/var/log/vmkernel.log`, `/var/log/hostd.log` | SSH to ESXi host |
| vCenter | `/var/log/vmware/vpxd/vpxd.log` | SSH to vCenter appliance |
| SDDC Manager | `/var/log/vmware/vcf/` | SSH to SDDC Manager |
| NSX Manager | `/var/log/syslog`, `/var/log/proton/` | SSH to NSX Manager |
| NSX Edge | `/var/log/syslog` | SSH to Edge VM |
| vSAN | vCenter → Monitor → vSAN → Health | vSphere Client |
| VKS / Supervisor | `kubectl logs -n vmware-system-*` | Supervisor API |
| Gateway dnsmasq | `/var/log/syslog` (filter: dnsmasq) | `journalctl -u dnsmasq` |
| Gateway chrony | `/var/log/syslog` (filter: chronyd) | `journalctl -u chronyd` |
| Gateway step-ca | `journalctl -u step-ca` | systemd journal |
| Free Range Routing (FRR) | `/var/log/frr/zebra.log`, `/var/log/frr/bgpd.log` | `journalctl` or file |
| 1Password | Operator laptop | `op item list --vault Employee` |
| Keycloak | Container stdout | `docker logs keycloak` |
| Contour | `kubectl logs -n projectcontour` | kubectl on vks-services-01 |
| Envoy | `kubectl logs -n projectcontour -l app=envoy` | kubectl on vks-services-01 |
| Harbor | `kubectl logs -n harbor` | kubectl on vks-services-01 |
| Velero | `kubectl logs -n velero -l app.kubernetes.io/name=velero` | kubectl on vks-services-01 |
| MinIO | `kubectl logs -n velero -l app=minio` | kubectl on vks-services-01 |
| ArgoCD | `kubectl logs -n argocd` | kubectl on vks-services-01 |

### 4.3 Useful Diagnostic Commands

#### ESXi

```bash
# Check host health
esxcli system health status get

# Check network connectivity
vmkping -I vmk0 10.0.10.1    # Management gateway
vmkping -I vmk2 10.0.30.1 -s 8972  # vSAN with jumbo frames

# Check NTP
esxcli system ntp get

# Check DNS
nslookup vcenter-mgmt.lab.dreamfold.dev 10.0.10.1
```

#### vSAN (from ESXi host SSH)

```bash
# Cluster-wide health summary (run from any host in the cluster)
esxcli vsan health cluster list

# List vSAN storage devices and their status
esxcli vsan storage list

# Check vSAN disk group/pool status (Express Storage Architecture (ESA) uses single pool)
esxcli vsan debug disk list

# Check vSAN network connectivity (vmk2 on VLAN 30)
esxcli vsan network list

# Check resync/rebalance status
esxcli vsan debug resync summary

# Check object health and placement
esxcli vsan debug object health summary

# Check dedup/compression savings (ESA)
esxcli vsan debug disk stats get

# Check FakeSCSIReservations (nested vSAN requirement)
esxcli system settings advanced list -o /VSAN/FakeSCSIReservations
```

#### vSAN (from vCenter UI / API)

```text
# Capacity overview
vCenter → Cluster → Monitor → vSAN → Capacity
  - Used / Free / Total
  - Dedup/compression savings ratio
  - Object breakdown by type

# Health deep-dive
vCenter → Cluster → Monitor → vSAN → Health
  - Network: vmk2 connectivity, multicast, MTU
  - Storage: disk balance, component metadata health
  - Cluster: host membership, object health

# Object browser (inspect individual vSAN objects)
vCenter → Cluster → Monitor → vSAN → Virtual Objects
  - Shows FCDs (PersistentVolumes), VMDKs, VM home namespaces
  - Component placement across hosts
  - Compliance with storage policy (FTT=1)

# Performance (latency, IOPS, throughput)
vCenter → Cluster → Monitor → vSAN → Performance
  - Cluster-level and per-host IOPS, throughput, latency
  - Backend (disk) vs frontend (VM) latency split
  - Congestion indicators
```

#### Gateway Routing (FRR)

```bash
# Check all VLAN sub-interfaces
ip addr show | grep ens34

# Check routing table
ip route

# --- BGP diagnostics (via FRR vtysh) ---
# Session summary (state, prefixes received, uptime)
sudo vtysh -c 'show ip bgp summary'

# Full BGP table (all received prefixes)
sudo vtysh -c 'show ip bgp'

# Detailed neighbor state (timers, capabilities, counters)
sudo vtysh -c 'show ip bgp neighbors 10.0.60.2'

# Routes advertised TO NSX Tier-0 (should show all connected subnets)
sudo vtysh -c 'show ip bgp neighbors 10.0.60.2 advertised-routes'

# Routes received FROM NSX Tier-0 (should show VPC/overlay prefixes)
sudo vtysh -c 'show ip bgp neighbors 10.0.60.2 received-routes'

# --- NAT diagnostics ---
# Active iptables NAT rules
sudo iptables -t nat -L POSTROUTING -v -n

# --- Logs ---
tail -50 /var/log/frr/bgpd.log
tail -50 /var/log/frr/zebra.log
```

#### NSX

```bash
# Check transport node status (from NSX Manager API)
curl -k -u admin:<password> https://nsx-mgr-wld.lab.dreamfold.dev/api/v1/transport-nodes/state

# Check logical router status
curl -k -u admin:<password> https://nsx-mgr-wld.lab.dreamfold.dev/api/v1/logical-routers/status

# Check Tier-0 routing table
# NSX Manager → Networking → Tier-0 → tier0-gateway → Routing Table
# Or via API:
curl -k -u admin:<password> \
  'https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/routing-table'

# Check Tier-0 BGP session state
curl -k -u admin:<password> \
  'https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/locale-services/default/bgp/neighbors/status'

# Check Tier-0 BGP advertised/received routes
curl -k -u admin:<password> \
  'https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/locale-services/default/bgp/neighbors/status?source=realtime'

# Check NAT rules and hit counts
curl -k -u admin:<password> \
  'https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/nat/rules'

# Check NAT rule statistics (per-rule packet/byte counts)
curl -k -u admin:<password> \
  'https://nsx-mgr-wld.lab.dreamfold.dev/policy/api/v1/infra/tier-0s/tier0-gateway/nat/rules/statistics'

# Check Tier-1 route advertisements
# NSX Manager → Networking → Tier-1 → tier1-gateway → Route Advertisement

# Check VPC status
# NSX Manager → Networking → VPC → vks-vpc → Overview

# Check Edge cluster status (from Edge VM CLI)
nsxcli
> get edge-cluster status
> get bgp neighbor summary
> get route-table

# Check NAT translation table (from Edge VM CLI)
nsxcli
> get nat rules
> get nat statistics

# Check host transport node connectivity (from ESXi host)
nsxcli
> get logical-switches
> get vtep-table
```

#### VKS / Kubernetes

```bash
# Cluster health
kubectl get nodes -o wide
kubectl get cluster vks-cluster-01 -o yaml
kubectl get machines

# System pods
kubectl get pods -n kube-system
kubectl get pods -n vmware-system-csi

# Resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# Events (useful for debugging)
kubectl get events --sort-by=.lastTimestamp
```

## 5. Capacity Management

### 5.1 Current Resource Allocation

Refer to [Physical Design](physical-design.md) Section 9 for the canonical vCD resource requirements and nested appliance resource tables. Use those tables as the baseline when assessing capacity.

### 5.2 Scaling Guidance

#### When to Scale

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| vSAN capacity > 70% | Warning | Plan capacity addition or cleanup |
| vSAN capacity > 80% | Critical | Add storage or reduce objects immediately |
| Host CPU sustained > 80% | Warning | Consider adding host or reducing workloads |
| Host RAM > 90% | Critical | Add host or reduce VM count |
| VKS node CPU/RAM > 80% | Warning | Scale VM class up or add worker nodes |
| Content library sync failing | Error | Check internet connectivity and storage space |

#### Scaling Options

| Option | Impact | vCD Resources Required |
|--------|--------|----------------------|
| Add ESXi host to workload domain | More compute/storage for VKS | +24 vCPU, +128 GB RAM, +320 GB disk |
| Increase VKS worker count | More pod capacity | Uses existing ESXi resources |
| Scale VKS VM class (medium → large) | More per-node resources | Uses existing ESXi resources |
| Add ESXi host to management domain | More headroom for appliances | +24 vCPU, +128 GB RAM, +320 GB disk |

### 5.3 Resource Monitoring

| What to Monitor | Where | Tool |
|----------------|-------|------|
| vCD resource allocation | vCloud Director tenant portal | Provider quota vs used |
| ESXi host utilisation | vCenter Performance charts | CPU, RAM, network, storage |
| vSAN capacity | vCenter → vSAN → Capacity | Used vs free, dedup/compression ratio |
| VKS node resources | `kubectl top nodes` | CPU and memory usage per node |
| VKS pod resources | `kubectl top pods` | Per-pod resource consumption |
| NSX Edge throughput | NSX Manager → Edge dashboard | Data plane throughput |
| BGP route count | `sudo vtysh -c 'show ip bgp summary'` on gateway | Prefixes received/advertised |
