
from openstackclient_base.client import BaseClient
from openstackclient_base.compute_ext import userinfo


class ComputeExtClient(BaseClient):
    """
    Client for the Nova extentions
    """
    service_type = "compute"

    def __init__(self, http_client, extensions=None):
        super(ComputeExtClient, self).__init__(http_client,
                                               extensions=extensions)

        self.user_keypairs = userinfo.UserKeypairManager(self)
