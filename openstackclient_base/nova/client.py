# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2012 Grid Dynamics.

from openstackclient_base.client import BaseClient

from novaclient.v1_1 import certs
from novaclient.v1_1 import cloudpipe
from novaclient.v1_1 import aggregates
from novaclient.v1_1 import flavors
from novaclient.v1_1 import floating_ip_dns
from novaclient.v1_1 import floating_ips
from novaclient.v1_1 import floating_ip_pools
from novaclient.v1_1 import hosts
from novaclient.v1_1 import images
from novaclient.v1_1 import keypairs
from novaclient.v1_1 import limits
from novaclient.v1_1 import quota_classes
from novaclient.v1_1 import quotas
from novaclient.v1_1 import security_group_rules
from novaclient.v1_1 import security_groups
from novaclient.v1_1 import servers
from novaclient.v1_1 import usage
from novaclient.v1_1 import virtual_interfaces
from novaclient.v1_1 import volumes
from novaclient.v1_1 import volume_snapshots
from novaclient.v1_1 import volume_types


class ComputeClient(BaseClient):
    """
    Client for the OpenStack Compute v2.0 API.
    """
    service_type = "compute"

    def __init__(self, client, extensions=None):
        super(ComputeClient, self).__init__(client=client,
                                            extensions=extensions)
        
        self.flavors = flavors.FlavorManager(self)
        self.images = images.ImageManager(self)
        self.limits = limits.LimitsManager(self)
        self.servers = servers.ServerManager(self)

        # extensions
        self.dns_domains = floating_ip_dns.FloatingIPDNSDomainManager(self)
        self.dns_entries = floating_ip_dns.FloatingIPDNSEntryManager(self)
        self.cloudpipe = cloudpipe.CloudpipeManager(self)
        self.certs = certs.CertificateManager(self)
        self.floating_ips = floating_ips.FloatingIPManager(self)
        self.floating_ip_pools = floating_ip_pools.FloatingIPPoolManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.security_groups = security_groups.SecurityGroupManager(self)
        self.security_group_rules = \
            security_group_rules.SecurityGroupRuleManager(self)
        self.usage = usage.UsageManager(self)
        self.virtual_interfaces = \
            virtual_interfaces.VirtualInterfaceManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.hosts = hosts.HostManager(self)


class VolumeClient(BaseClient):
    """
    Client for the OpenStack Volume v2.0 API.
    """

    service_type = "volume"

    def __init__(self, client, extensions=None):
        super(VolumeClient, self).__init__(client=client,
                                           extensions=extensions)

        self.volumes = volumes.VolumeManager(self)
        self.volume_snapshots = volume_snapshots.SnapshotManager(self)
        self.volume_types = volume_types.VolumeTypeManager(self)
