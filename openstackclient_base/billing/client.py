import datetime

from openstackclient_base.client import BaseClient


class Manager(object):
    def __init__(self, client, base_uri, method_list):
        self.client = client
        self.base_uri = base_uri
        method_map = {"GET": "list", "POST": "create",
                      "PUT": "update", "DELETE": "delete"}
        for method in method_list:
            setattr(self, method_map[method],
                lambda obj=self, _method=method, **kwargs:
                    obj.cs_request(_method, **kwargs))

    def cs_request(self, method, body=None, **kwargs):
        query = ["%s=%s" % (key, value)
                 for key, value in kwargs.iteritems()
                 if value]
        if query:
            query = "%s?%s" % (self.base_uri, "&".join(query))
        else:
            query = self.base_uri
        return self.client.cs_request(query, method, body=body)[1]


class Tariff(object):
    def __init__(self, client):
        self.client = client

    def list(self):
        return self.client.get("/tariff")[1]

    def update(self, name, price, migrate):
        request_data = {
            "datetime": "%sZ" % datetime.datetime.utcnow().isoformat(),
            "migrate": migrate,
            "values": {
                name: float(price),
            }
        }
        return self.client.post("/tariff", body=request_data)[1]


class BillingClient(BaseClient):
    """
    Client for the Nova Billing v2.0 API.
    """
    service_type = "nova-billing"

    def __init__(self, http_client, extensions=None):
        super(BillingClient, self).__init__(http_client, extensions)
        calls = {
            "account": ("GET", "POST", "PUT"),
            "cost_center": ("DELETE", "GET", "POST", "PUT"),
            "event": ("POST",),
            "resource": ("GET", "PUT"),
            "report": ("GET",),
        }
        for call, methods in calls.iteritems():
            setattr(self, call, Manager(self, call, methods))
        self.tariff = Tariff(self)
