# Copyright 2012 Grid Dynamics.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from openstackclient_base.client import HttpClient


class ClientSet(object):

    def __init__(self, **kwargs):
        try:
            self.http_client = kwargs["http_client"]
        except KeyError:
            self.http_client = HttpClient(**kwargs)

    @property
    def keystone(self):
        return self.identity_admin

    @property
    def nova(self):
        return self.compute

    @property
    def glance(self):
        return self.image

    @property
    def identity_admin(self):
        from openstackclient_base.keystone.client import IdentityAdminClient
        return IdentityAdminClient(self.http_client)

    @property
    def identity_public(self):
        from openstackclient_base.keystone.client import IdentityPublicClient
        return IdentityPublicClient(self.http_client)

    @property
    def compute(self):
        from openstackclient_base.nova.client import ComputeClient
        from openstackclient_base.nova import networks
        return ComputeClient(self.http_client, extensions=[networks])

    @property
    def volume(self):
        from openstackclient_base.nova.client import VolumeClient
        return VolumeClient(self.http_client)

    @property
    def image(self):
        from openstackclient_base.glance.v1.client import ImageClient
        return ImageClient(self.http_client)

    @property
    def billing(self):
        from openstackclient_base.billing.client import BillingClient
        return BillingClient(self.http_client)
