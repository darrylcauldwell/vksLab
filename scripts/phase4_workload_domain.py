#!/usr/bin/env python3
"""Phase 4: Create VCF Workload Domain using VCF SDK.

This script replaces the Ansible playbook approach with direct SDK calls,
providing better error visibility and spec validation.

Usage:
    python3 phase4_workload_domain.py \
      --sddc-hostname sddc-manager.lab.dreamfold.dev \
      --username admin@local \
      --password <password>
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "vcf-sdk"))

from vcf_sdk import SDDCManager
from vcf_sdk.exceptions import ValidationError, TaskFailedError, TimeoutError

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)


def build_domain_spec(
    cluster_image_id: str,
    nsx_manager_host_id: str,
    vcenter_host_id: str,
    esxi_05_host_id: str,
    esxi_06_host_id: str,
    esxi_07_host_id: str,
    lab_mgmt_prefix: str = "10.0.10",
    lab_gateway: str = "10.0.10.1",
    lab_domain: str = "lab.dreamfold.dev",
    lab_overlay_prefix: str = "10.0.40",
    lab_vlan_id_host_overlay: int = 40,
    lab_vlan_host_overlay_subnet: str = "10.0.40.0/24",
    lab_vlan_host_overlay_gateway: str = "10.0.40.1",
) -> dict:
    """Build workload domain specification."""

    return {
        "domainName": "workload-domain",
        "deployWithoutLicenseKeys": True,
        "ssoSpec": {
            "ssoDomain": "vsphere.local"
        },
        "vcenterSpec": {
            "name": "vcenter-wld",
            "networkDetailsSpec": {
                "ipAddress": f"{lab_mgmt_prefix}.9",
                "dnsName": f"vcenter-wld.{lab_domain}",
                "gateway": lab_gateway,
                "subnetMask": "255.255.255.0"
            },
            "rootPassword": "VMware1!VMware1!",
            "datacenterName": "workload-dc",
            "vmSize": "medium",
            "storageSize": "lstorage"
        },
        "computeSpec": {
            "clusterSpecs": [
                {
                    "name": "workload-cluster",
                    "clusterImageId": cluster_image_id,
                    "hostSpecs": [
                        {
                            "id": esxi_05_host_id,
                            "hostname": f"esxi-05.{lab_domain}",
                            "username": "root",
                            "storageType": "VSAN_ESA",
                            "hostNetworkSpec": {
                                "vmNics": [
                                    {
                                        "id": "vmnic0",
                                        "vdsName": "workload-cluster-vds01",
                                        "uplink": "uplink1"
                                    }
                                ]
                            }
                        },
                        {
                            "id": esxi_06_host_id,
                            "hostname": f"esxi-06.{lab_domain}",
                            "username": "root",
                            "storageType": "VSAN_ESA",
                            "hostNetworkSpec": {
                                "vmNics": [
                                    {
                                        "id": "vmnic0",
                                        "vdsName": "workload-cluster-vds01",
                                        "uplink": "uplink1"
                                    }
                                ]
                            }
                        },
                        {
                            "id": esxi_07_host_id,
                            "hostname": f"esxi-07.{lab_domain}",
                            "username": "root",
                            "storageType": "VSAN_ESA",
                            "hostNetworkSpec": {
                                "vmNics": [
                                    {
                                        "id": "vmnic0",
                                        "vdsName": "workload-cluster-vds01",
                                        "uplink": "uplink1"
                                    }
                                ]
                            }
                        }
                    ],
                    "datastoreSpec": {
                        "vsanDatastoreSpec": {
                            "datastoreName": "workload-vsan-ds",
                            "failuresToTolerate": 1,
                            "esaEnabled": True
                        }
                    },
                    "networkSpec": {
                        "vdsSpecs": [
                            {
                                "name": "workload-cluster-vds01",
                                "portGroupSpecs": [
                                    {
                                        "name": "workload-cluster-vds01-pg-mgmt",
                                        "transportType": "MANAGEMENT",
                                        "teamingPolicy": "loadbalance_loadbased",
                                        "activeUplinks": ["uplink1"],
                                        "standbyUplinks": []
                                    },
                                    {
                                        "name": "workload-cluster-vds01-pg-vmotion",
                                        "transportType": "VMOTION",
                                        "teamingPolicy": "loadbalance_loadbased",
                                        "activeUplinks": ["uplink1"],
                                        "standbyUplinks": []
                                    },
                                    {
                                        "name": "workload-cluster-vds01-pg-vsan",
                                        "transportType": "VSAN",
                                        "teamingPolicy": "loadbalance_loadbased",
                                        "activeUplinks": ["uplink1"],
                                        "standbyUplinks": []
                                    }
                                ],
                                "isUsedByNsxt": True,
                                "vmnics": ["vmnic0"],
                                "vmnicsToUplinks": [
                                    {
                                        "id": "vmnic0",
                                        "uplink": "uplink1"
                                    }
                                ]
                            }
                        ],
                        "nsxClusterSpec": {
                            "nsxTClusterSpec": {
                                "geneveVlanId": lab_vlan_id_host_overlay,
                                "ipAddressPoolSpec": {
                                    "name": "workload-tep-pool",
                                    "subnets": [
                                        {
                                            "ipAddressPoolRanges": [
                                                {
                                                    "start": f"{lab_overlay_prefix}.15",
                                                    "end": f"{lab_overlay_prefix}.17"
                                                }
                                            ],
                                            "cidr": lab_vlan_host_overlay_subnet,
                                            "gateway": lab_vlan_host_overlay_gateway
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            ]
        },
        "nsxTSpec": {
            "nsxManagerSpecs": [
                {
                    "name": "nsx-mgr-wld",
                    "hostname": f"nsx-mgr-wld.{lab_domain}",
                    "networkDetailsSpec": {
                        "ipAddress": f"{lab_mgmt_prefix}.10",
                        "dnsName": f"nsx-mgr-wld.{lab_domain}",
                        "gateway": lab_gateway,
                        "subnetMask": "255.255.255.0"
                    }
                }
            ],
            "nsxManagerAdminPassword": "VMware1!VMware1!",
            "formFactor": "medium"
        }
    }


def main():
    """Run Phase 4 workload domain creation."""
    parser = argparse.ArgumentParser(
        description="Create VCF workload domain using SDK"
    )
    parser.add_argument(
        "--sddc-hostname",
        default="sddc-manager.lab.dreamfold.dev",
        help="SDDC Manager hostname"
    )
    parser.add_argument(
        "--username",
        default="admin@local",
        help="SDDC Manager username"
    )
    parser.add_argument(
        "--password",
        required=True,
        help="SDDC Manager password"
    )
    parser.add_argument(
        "--skip-commission",
        action="store_true",
        help="Skip host commissioning (assume already commissioned)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate spec without creating domain"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Phase 4: VCF Workload Domain Creation (SDK)")
    logger.info("=" * 70)

    try:
        with SDDCManager(
            hostname=args.sddc_hostname,
            username=args.username,
            password=args.password,
            verify_ssl=False
        ) as sddc:

            # Step 1: Get network pool
            logger.info("\n[1/4] Looking up network pool...")
            mgmt_pool = sddc.networks.find_pool("mgmt-network-pool")
            if not mgmt_pool:
                logger.error("Network pool 'mgmt-network-pool' not found!")
                return 1
            logger.info(f"✓ Found network pool: {mgmt_pool.name}")
            logger.info(f"  ID: {mgmt_pool.id}")
            logger.info(f"  Hosts in pool: {mgmt_pool.hosts_count}")

            # Step 2: Get vLCM image
            logger.info("\n[2/4] Looking up vLCM images...")
            images = sddc.images.list()
            if not images:
                logger.error("No vLCM images found!")
                return 1
            primary_image = images[0]
            logger.info(f"✓ Found {len(images)} vLCM image(s)")
            logger.info(f"  Using: {primary_image.personality_name}")
            logger.info(f"  ID: {primary_image.personality_id}")

            # Step 3: Commission hosts (if needed)
            if not args.skip_commission:
                logger.info("\n[3/4] Commissioning workload hosts...")
                all_hosts = sddc.hosts.list()
                commissioned_fqdns = {h.fqdn for h in all_hosts}

                hosts_to_commission = [
                    {
                        "fqdn": "esxi-05.lab.dreamfold.dev",
                        "username": "root",
                        "password": "VMware1!VMware1!",
                        "storageType": "VSAN_ESA",
                        "networkPoolId": mgmt_pool.id
                    },
                    {
                        "fqdn": "esxi-06.lab.dreamfold.dev",
                        "username": "root",
                        "password": "VMware1!VMware1!",
                        "storageType": "VSAN_ESA",
                        "networkPoolId": mgmt_pool.id
                    },
                    {
                        "fqdn": "esxi-07.lab.dreamfold.dev",
                        "username": "root",
                        "password": "VMware1!VMware1!",
                        "storageType": "VSAN_ESA",
                        "networkPoolId": mgmt_pool.id
                    }
                ]

                to_commission = [
                    h for h in hosts_to_commission
                    if h["fqdn"] not in commissioned_fqdns
                ]

                if to_commission:
                    logger.info(f"✓ Commissioning {len(to_commission)} host(s)...")
                    commission_task = sddc.hosts.commission(to_commission)
                    logger.info(f"  Task ID: {commission_task.id}")
                    final_task = sddc.tasks.wait_for_completion(
                        commission_task.id,
                        timeout=3600,
                        poll_interval=30
                    )
                    logger.info(f"✓ Commission complete!")
                else:
                    logger.info("✓ All hosts already commissioned")

                # Refresh host list for spec
                all_hosts = sddc.hosts.list()
            else:
                logger.info("\n[3/4] Skipping host commissioning (--skip-commission)")
                all_hosts = sddc.hosts.list()

            # Step 4: Build domain spec
            logger.info("\n[4/4] Building domain specification...")
            host_map = {h.fqdn: h.id for h in all_hosts}

            domain_spec = build_domain_spec(
                cluster_image_id=primary_image.personality_id,
                nsx_manager_host_id=host_map.get("nsx-mgr-wld.lab.dreamfold.dev", ""),
                vcenter_host_id=host_map.get("vcenter-wld.lab.dreamfold.dev", ""),
                esxi_05_host_id=host_map.get("esxi-05.lab.dreamfold.dev", ""),
                esxi_06_host_id=host_map.get("esxi-06.lab.dreamfold.dev", ""),
                esxi_07_host_id=host_map.get("esxi-07.lab.dreamfold.dev", "")
            )

            # Step 5: Validate spec
            logger.info("\n[5/5] Validating domain specification...")
            logger.info("Sending spec to SDDC Manager for validation...")

            try:
                validation = sddc.domains.validate(domain_spec)
                logger.info("✓ Domain spec validation passed!")
                logger.info(f"  Validation ID: {validation.id}")

                if args.validate_only:
                    logger.info("\n✓ Validation complete (--validate-only, skipping creation)")
                    return 0

                # Step 6: Create domain
                logger.info("\n[6/6] Creating workload domain...")
                create_task = sddc.domains.create(domain_spec, validate=False)
                logger.info(f"✓ Domain creation task started!")
                logger.info(f"  Task ID: {create_task.id}")

                logger.info("\nWaiting for domain creation to complete...")
                final_task = sddc.tasks.wait_for_completion(
                    create_task.id,
                    timeout=5400,
                    poll_interval=60
                )

                logger.info("\n" + "=" * 70)
                logger.info("✓ Phase 4 Complete!")
                logger.info("=" * 70)
                logger.info(f"Domain created successfully!")
                logger.info(f"Task status: {final_task.status}")

                return 0

            except ValidationError as e:
                logger.error("\n✗ Domain spec validation failed!")
                logger.error(f"Error: {e}")
                if hasattr(e, 'response_body') and e.response_body:
                    logger.error("\nValidation details:")
                    try:
                        errors = json.loads(e.response_body)
                        logger.error(json.dumps(errors, indent=2))
                    except:
                        logger.error(e.response_body)
                return 1

    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
