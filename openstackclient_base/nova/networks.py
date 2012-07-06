# Copyright 2012 Alessio Ababilov
# Copyright 2012 Grid Dynamics
"""
Network interface.
"""

from openstackclient_base import base


class Network(base.Resource):
    """
    A network.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Network: %s>" % self.label


class NetworkManager(base.ManagerWithFind):
    """
    Manage :class:`Network` resources.
    """
    resource_class = Network

    def list(self):
        """
        Get a list of all networks.

        :rtype: list of :class:`Network`.
        """
        return self._list("/gd-networks", "networks")

    def get(self, network):
        """
        Get a specific network.

        :param network: The ID of the :class:`Network` to get.
        :rtype: :class:`Network`
        """
        return self._get("/gd-networks/%s" % base.getid(network), "network")

    def delete(self, network):
        """
        Delete a specific network.

        :param network: The ID of the :class:`Network` to get.
        """
        self._delete("/gd-networks/%s" % base.getid(network))

    def create(self, **kwargs):
        """
        Create (allocate) a  floating ip for a tenant

        :param bridge:
        :param bridge_interface:
        :param cidr:
        :param cidr_v6:
        :param dns1:
        :param dns2:
        :param fixed_cidr:
        :param gateway:
        :param gateway_v6:
        :param label:
        :param multi_host:
        :param priority:
        :param project_id:
        :param network_size: int
        :param num_networks: int
        :param vlan_start: int
        :param vpn_start: int

        :rtype: list of :class:`Network`
        """
        body = {
            "network": kwargs
        }
        resp, body = self.api.post("/gd-networks", body=body)
        return [self.resource_class(self, item) for item in body["networks"]]

    def disassociate(self, network):
        """
        Disassociate a specific network from project.

        :param network: The ID of the :class:`Network` to get.
        """
        self.api.post("/gd-networks/%s/action" % base.getid(network),
                      body={"disassociate": 1})

    def associate(self, network, project):
        """
        Associates a network with project.

        :param project: The ID of the :class:`Network` to get.
        """
        self.api.post("/gd-networks/%s/action" % base.getid(network),
                      body={"associate": base.getid(project)})


manager_class = NetworkManager
name = "networks"
