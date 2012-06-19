from openstackclient_base.client import BaseClient


class BillingClient(BaseClient):
    """
    Client for the Nova Billing v2.0 API.
    """
    service_type = "nova-billing"

    def event(self, request):
        return self.post("/event", request)
