"""Deploy NixOS VMs to vSphere."""

import pulumi
import pulumi_vsphere as vsphere

# Configuration
config = pulumi.Config()
vsphere_config = pulumi.Config("vsphere")

datacenter_name = config.require("datacenter")
cluster_name = config.require("cluster")
datastore_name = config.require("datastore")
network_name = config.require("network")
template_name = config.get("template") or "nixos-vsphere"

num_cpus = config.get_int("cpus") or 2
memory_mb = config.get_int("memory") or 2048
disk_size_gb = config.get_int("diskSize") or 20
vm_name = config.get("vmName") or "nixos-vm"

# Look up vSphere resources
datacenter = vsphere.get_datacenter(name=datacenter_name)

datastore = vsphere.get_datastore(
    name=datastore_name,
    datacenter_id=datacenter.id,
)

cluster = vsphere.get_compute_cluster(
    name=cluster_name,
    datacenter_id=datacenter.id,
)

network = vsphere.get_network(
    name=network_name,
    datacenter_id=datacenter.id,
)

template = vsphere.get_virtual_machine(
    name=template_name,
    datacenter_id=datacenter.id,
)

# Create VM from template
vm = vsphere.VirtualMachine(
    vm_name,
    name=vm_name,
    resource_pool_id=cluster.resource_pool_id,
    datastore_id=datastore.id,
    num_cpus=num_cpus,
    memory=memory_mb,
    guest_id=template.guest_id,
    network_interfaces=[
        vsphere.VirtualMachineNetworkInterfaceArgs(
            network_id=network.id,
            adapter_type=template.network_interface_types[0],
        ),
    ],
    disks=[
        vsphere.VirtualMachineDiskArgs(
            label="disk0",
            size=disk_size_gb,
            thin_provisioned=True,
        ),
    ],
    clone=vsphere.VirtualMachineCloneArgs(
        template_uuid=template.id,
    ),
)

pulumi.export("vm_name", vm.name)
pulumi.export("vm_id", vm.id)
