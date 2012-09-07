# Copyright 2012 Alessio Ababilov
# Copyright 2012 Grid Dynamics
"""
Fping interface.
"""

from openstackclient_base import base


class Fping(base.Resource):
    """
    A server for fping.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Fping: %s>" % self.id


class FpingManager(base.ManagerWithFind):
    """
    Manage :class:`Fping` resources.
    """
    resource_class = Fping

    def list(self, all_tenants=False, include=[], exclude=[]):
        """
        Fping all servers.

        :rtype: list of :class:`Fping`.
        """
        params = []
        if all_tenants:
            params.append("all_tenants=1")
        if include:
            params.append("include=%s" % ",".join(include))
        elif exclude:
            params.append("exclude=%s" % ",".join(exclude))
        uri = "/os-fping"
        if params:
            uri = "%s?%s" % (uri, "&".join(params))
        return self._list(uri, "servers", iterate=False)

    def get(self, server):
        """
        Fping a specific server.

        :param network: The ID of the server to get.
        :rtype: :class:`Fping`
        """
        return self._get("/os-fping/%s" % base.getid(server), "server")


manager_class = FpingManager
name = "fping"
