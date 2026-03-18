---
title: "VKS Lab"
subtitle: "Operations Guide"
author: "dreamfold"
date: "March 2026"
---

# Operations Guide

## 1. Standard Operating Procedures

### 1.1 Lab Power On Sequence (R-010, VCD-03)

The lab must be powered on in a specific order to ensure service dependencies are met.

| Order | Component | Action | Wait For |
|-------|-----------|--------|----------|
| 1 | Jumpbox | Power on VM | SSH/RDP accessible |
| 2 | Arista vEOS | Power on VM | SVIs up (`show ip interface brief`) |
| 3 | Management ESXi hosts (esxi-01 to esxi-04) | Power on VMs | ESXi DCUI shows management IP |
| 4 | Wait for vSAN cluster | Automatic | vSAN health green in vCenter |
| 5 | Management appliances auto-start | Automatic (HA/DRS) | vCenter, SDDC Manager, NSX Manager accessible |
| 6 | Workload ESXi hosts (esxi-05 to esxi-07) | Power on VMs | ESXi DCUI shows management IP |
| 7 | Wait for workload vSAN | Automatic | vSAN health green |
| 8 | Workload appliances auto-start | Automatic | Workload vCenter, NSX Manager accessible |
| 9 | NSX Edge VMs | Verify running | BGP adjacency re-established |
| 10 | Supervisor & VKS | Verify running | `kubectl get nodes` shows Ready |

### 1.2 Lab Power Off Sequence (Safe Shutdown)

**IMPORTANT**: vSAN clusters must be shut down gracefully to avoid data loss.

| Order | Component | Action | Verification |
|-------|-----------|--------|-------------|
| 1 | VKS workloads | Scale deployments to 0 or cordon/drain nodes | `kubectl get pods` shows no running pods |
| 2 | VKS cluster | (Optional) Delete VKS cluster or leave powered off | Cluster nodes powered off |
| 3 | Workload appliances | Shut down workload vCenter and NSX Manager | VMs powered off |
| 4 | Workload ESXi hosts | Put in maintenance mode (evacuate VMs first), then shut down | Hosts in maintenance, then powered off |
| 5 | Management appliances | Shut down VCF Ops, VCF Auto, NSX Manager, SDDC Manager, then vCenter (last) | All management VMs powered off |
| 6 | Management ESXi hosts | Put in maintenance mode, then shut down | Hosts powered off |
| 7 | Arista vEOS | Power off | VM stopped |
| 8 | Jumpbox | Power off (last) | VM stopped |

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
| 1 | Deploy new nested ESXi VM with standard spec (8 vCPU, 72 GB RAM, 200 GB + 10 GB disk) | VM powered on |
| 2 | Configure networking (management access + trunk) | Management IP pingable |
| 3 | Set hostname, DNS (10.0.10.2), NTP (10.0.10.2) | Services configured |
| 4 | Add DNS record to jumpbox dnsmasq | `dig` resolves new hostname |
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

### 1.7 Certificate Renewal SOP (R-009, SVC-02)

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
| 1 | Check if `step ca renew` cron/timer is active on the jumpbox | `systemctl status step-ca-renew.timer` |
| 2 | If expired, manually renew | `step ca renew /path/to/cert.pem /path/to/key.pem --force` |
| 3 | Restart the affected service | Service responds with valid TLS |

#### Manual Certificate Renewal (VCF Components)

For VCF components (vCenter, NSX Manager, SDDC Manager) that use certificates issued by step-ca but do not auto-renew:

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Generate a new certificate from step-ca | `step ca certificate <fqdn> cert.pem key.pem` |
| 2 | Upload to the component via its management UI or API | Certificate updated |
| 3 | Restart the component's web service if required | UI accessible with new certificate |

#### Root CA Certificate Rotation

If the step-ca root CA certificate approaches expiry or needs rotation:

| Step | Action | Notes |
|------|--------|-------|
| 1 | Generate new root CA on jumpbox | `step ca init` or use `step certificate create` for a new root |
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
| 8 | Verify BGP adjacency after Edge upgrade | `show ip bgp summary` on vEOS |
| 9 | Verify VPC and VKS connectivity | Test workload accessible |

### 2.4 VKS Kubernetes Version Upgrades

| Step | Action | Notes |
|------|--------|-------|
| 1 | Sync content library | New VKr images appear |
| 2 | Check available Kubernetes versions | `kubectl get tkr` (TanzuKubernetesRelease) |
| 3 | Update cluster manifest with new version | Change `spec.topology.version` |
| 4 | Apply updated manifest | `kubectl apply -f vks-cluster.yaml` |
| 5 | Wait for rolling upgrade | Control plane nodes upgraded first, then workers |
| 6 | Verify cluster health | `kubectl get nodes` — all nodes Ready, new version |
| 7 | Verify workloads | `kubectl get pods` — all pods Running |

### 2.5 vEOS Software Update

| Step | Action | Notes |
|------|--------|-------|
| 1 | Download new vEOS image | From Arista support portal |
| 2 | Upload to vEOS flash | `copy scp: flash:` or via vCD datastore |
| 3 | Set boot image | `boot system flash:<new-image>.swi` |
| 4 | Take lab snapshot | — |
| 5 | Reload vEOS | `reload` |
| 6 | Verify SVIs and routing | `show ip interface brief`, `show ip route` |
| 7 | Verify BGP adjacency | `show ip bgp summary` — should re-establish |

### 2.6 Jumpbox OS Patching

| Step | Action | Notes |
|------|--------|-------|
| 1 | SSH to jumpbox | — |
| 2 | `sudo apt update && sudo apt upgrade` | Review packages before confirming |
| 3 | Verify dnsmasq still running | `systemctl status dnsmasq` |
| 4 | Verify chrony still running | `systemctl status chronyd` |
| 5 | Verify step-ca still running | `step ca health` |
| 6 | Reboot if kernel update | `sudo reboot` |
| 7 | Verify all lab services post-reboot | DNS, NTP, CA, RDP all functional |

### 2.7 OpenBao Secret Store

#### Seal/Unseal

OpenBao automatically seals on container restart. Unseal after any Docker restart or jumpbox reboot:

```bash
export BAO_ADDR=http://127.0.0.1:8200
bao operator unseal <unseal-key>
```

#### Password Rotation

When VCF rotates a password (e.g., ESXi root password via SDDC Manager), update OpenBao to keep secrets in sync:

```bash
bao kv put secret/esxi/root-password value='<new-password>'
```

#### Backup

```bash
# Export all secrets (for disaster recovery)
for path in esxi/root-password vcenter/sso-password sddc-manager/admin-password nsx/admin-password; do
  bao kv get -format=json "secret/$path" > ~/backups/openbao/$path.json
done
```

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

### 3.2 Weekly Checks

| # | Check | Method | Expected Result |
|---|-------|--------|-----------------|
| 1 | BGP adjacency | `show ip bgp summary` on vEOS | Established |
| 2 | BGP routes received | `show ip bgp` on vEOS | VPC prefixes present |
| 3 | DNS resolution | `dig @10.0.10.2 vcenter-mgmt.lab.dreamfold.dev` | Correct response |
| 4 | NTP synchronisation | `chronyc tracking` on jumpbox | System clock synchronised |
| 5 | ESXi NTP sync | `esxcli system ntp get` on each host | Server reachable |
| 6 | Certificate expiry (R-009) | `step ca certificate list` or check expiry dates | No certs expiring within 30 days |
| 7 | NSX Edge status | NSX Manager → Edge Clusters | Both Edges Up |

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

## 4. Troubleshooting

### 4.1 Common Issues

#### Nested ESXi Performance Degradation

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Slow VM operations | CPU contention on physical host | Check vCD host resource utilisation; reduce concurrent workloads |
| High vSAN latency | Nested disk I/O overhead | Expected for nested vSAN; reduce FTT if capacity allows |
| vMotion timeouts | Network contention on trunk | Verify jumbo frame MTU end-to-end; check for frame drops |

#### vSAN Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| vSAN health warnings | Disk group degraded | Check `esxcli vsan health cluster list`; rebuild disk group if needed |
| Objects inaccessible | Insufficient hosts for FTT=1 | Ensure minimum 3 hosts (workload) or 4 hosts (management) are available |
| Resync stuck | Insufficient bandwidth or capacity | Wait for resync; check vSAN capacity; consider reducing object count |
| Network partition | VLAN 30 misconfigured | Verify vmk2 on VLAN 30 across all hosts; check vEOS SVI |

#### BGP Flapping

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| BGP session down | NSX Edge rebooted or network disruption | Check Edge VM status; verify VLAN 60 connectivity |
| Routes withdrawn | Tier-0 uplink interface down | Check NSX Tier-0 uplink status; verify Edge TEP connectivity |
| Frequent flaps | Hold/keepalive timers too aggressive | Increase BGP timers (hold: 180s, keepalive: 60s) |

#### VKS Node Not Ready

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Node shows NotReady | kubelet not running | SSH to node, check `systemctl status kubelet` |
| Node unreachable | NSX VPC connectivity issue | Check VPC status, verify Tier-0/Tier-1 routing |
| Pods stuck Pending | Insufficient node resources | Check `kubectl describe node`; consider scaling VM class |
| Image pull failures | No internet access from VPC | Verify NAT rule on Tier-0; check route to internet via vEOS/jumpbox |

#### DNS Resolution Failures

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot resolve lab hostnames | dnsmasq not running | `sudo systemctl restart dnsmasq` on jumpbox |
| Upstream DNS fails | Jumpbox external NIC issue | Check ens160 connectivity; verify upstream DNS servers |
| Stale records | dnsmasq config not reloaded | Edit config, then `sudo systemctl restart dnsmasq` |

#### DHCP Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| ESXi host not getting IP | MAC address mismatch | Verify MAC in vCD matches `dhcp-host` entry in `/etc/dnsmasq.d/lab.conf`; restart dnsmasq |
| Host gets wrong IP | Duplicate DHCP reservation | Check for duplicate MAC entries in dnsmasq config |
| DHCP lease expired | Host powered off too long | Restart dnsmasq; host will get new lease on next boot |
| No DHCP offers | dnsmasq not listening on VLAN 10 | Verify dnsmasq is bound to ens192 (management VLAN interface); check `dhcp-range` config |

#### OpenBao Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot read secrets | Vault sealed | `bao operator unseal <key>` on jumpbox |
| Container not running | Docker restart or OOM | `docker start openbao`; check `docker logs openbao` |
| Authentication failed | Token expired | Re-authenticate: `bao login <root-token>` |
| Connection refused on 8200 | Container port not mapped | Verify `docker ps` shows port 8200 mapping |

#### Keycloak Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Cannot login via SSO | Keycloak container not running | `docker start keycloak`; check `docker logs keycloak` |
| OIDC token validation failed | Clock skew between jumpbox and VCF components | Verify NTP sync on jumpbox (`chronyc tracking`) and VCF appliances; ensure time delta is under 5 seconds |
| OIDC token validation failed | TLS certificate expired on Keycloak | Renew certificate: `step ca renew /etc/step-ca/certs/keycloak.crt /etc/step-ca/certs/keycloak.key --force`; restart Keycloak container |
| Users cannot authenticate | Realm misconfiguration or user disabled | Check Keycloak admin console → lab realm → Users; verify user is enabled and credentials are set |
| vCenter rejects OIDC provider | Discovery endpoint unreachable from vCenter | Verify vCenter can resolve `jumpbox.lab.dreamfold.dev` and reach port 8443; check firewall/routing |
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
| Jumpbox dnsmasq | `/var/log/syslog` (filter: dnsmasq) | `journalctl -u dnsmasq` |
| Jumpbox chrony | `/var/log/syslog` (filter: chronyd) | `journalctl -u chronyd` |
| Jumpbox step-ca | `journalctl -u step-ca` | systemd journal |
| vEOS | `show logging` | vEOS CLI |
| OpenBao | Container stdout | `docker logs openbao` |
| Keycloak | Container stdout | `docker logs keycloak` |

### 4.3 Useful Diagnostic Commands

#### ESXi

```bash
# Check host health
esxcli system health status get

# Check vSAN status
esxcli vsan health cluster list

# Check network connectivity
vmkping -I vmk0 10.0.10.1    # Management gateway
vmkping -I vmk2 10.0.30.1 -s 8972  # vSAN with jumbo frames

# Check NTP
esxcli system ntp get

# Check DNS
nslookup vcenter-mgmt.lab.dreamfold.dev 10.0.10.2
```

#### vEOS

```text
! Check all interfaces
show ip interface brief

! Check BGP
show ip bgp summary
show ip bgp

! Check routing table
show ip route

! Check logs
show logging last 50
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

Refer to [Physical Design](physical-design.md) Section 10 for the canonical vCD resource requirements and nested appliance resource tables. Use those tables as the baseline when assessing capacity.

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
| Add ESXi host to workload domain | More compute/storage for VKS | +8 vCPU, +72 GB RAM, +210 GB disk |
| Increase VKS worker count | More pod capacity | Uses existing ESXi resources |
| Scale VKS VM class (medium → large) | More per-node resources | Uses existing ESXi resources |
| Add ESXi host to management domain | More headroom for appliances | +8 vCPU, +72 GB RAM, +210 GB disk |

### 5.3 Resource Monitoring

| What to Monitor | Where | Tool |
|----------------|-------|------|
| vCD resource allocation | vCloud Director tenant portal | Provider quota vs used |
| ESXi host utilisation | vCenter Performance charts | CPU, RAM, network, storage |
| vSAN capacity | vCenter → vSAN → Capacity | Used vs free, dedup/compression ratio |
| VKS node resources | `kubectl top nodes` | CPU and memory usage per node |
| VKS pod resources | `kubectl top pods` | Per-pod resource consumption |
| NSX Edge throughput | NSX Manager → Edge dashboard | Data plane throughput |
| BGP route count | `show ip bgp summary` on vEOS | Prefixes received/advertised |
