# Copyright 2012 OpenStack LLC.
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

from openstackclient_base.client import BaseClient

from glanceclient.v1 import images
from glanceclient.v1 import image_members



class ImageClient(BaseClient):
    """
    Client for the OpenStack Images v1 API.
    """

    service_type = "image"
    
    def __init__(self, client):
        """ Initialize a new client for the Images v1 API. """
        super(ImageClient, self).__init__(client=client)

        self.images = images.ImageManager(self)
        self.image_members = image_members.ImageMemberManager(self)
