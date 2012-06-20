Preamble
========

This project aims to create a uniform interface to Openstack API clients.

Unfortunately, nova, keystone, and glance clients are very inconsistent. A lot
of code is copied between all these clients instead of moving it to a common library.
The code was edited without synchronization between clients, so, they have different
behaviour:

- all client constructors use different parameters (`api_key` in nova or 
  `password` in keystone and so on);
- keystoneclient authenticates immediately in __init__, while novaclient does in lazily 
  during first method call;
- {keystone,nova}client can manage service catalogs and accept keystone's auth URI while
  glanceclient allows endpoints only;
- keystoneclient can support authorization with an unscoped token but novaclient
  doesn't;
- novaclient uses class composition while keystoneclient uses inheritance.

Quickstart
==========

::

    from openstackclient_base.base import monkey_patch
    monkey_patch()
    from openstackclient_base.client import HttpClient
    http_client = HttpClient(username="...", password="...", tenant_name="...", auth_uri="...")

    from openstackclient_base.nova.client import ComputeClient
    print ComputeClient(http_client).servers.list()

    from openstackclient_base.keystone.client import IdentityPublicClient
    print IdentityPublicClient(http_client).tenants.list()



Architecture
============
The openstack-base library contains two main classes:

- HttpClient - an httplib2.Http descedant that manages authentication, endpoints, auth URI,
  service catalog, and API versioning;
- BaseClient - base class for actual clients (e.g. volume, compute, image); it uses an
  underlying HttpClient (class composition).

Several clients are implemented. They should be moved to actual packages (novaclient, 
keystoneclient etc.). Monkey patch is not necessary, but recommended. It switches 
different clients one common base library.

- ComputeClient, VolumeClient - compute and volume clients for nova;
- v1.ImageClient, v2.ImageClient - clients for glance;
- IdentityAdminClient, IdentityPublicClient - admin and public clients for keystone.

A sample class ClientSet can be used for convenience. It should be created only once
(providing auth information) and then actual client are accessible as its properties.

::

    from openstackclient_base.client_set import ClientSet
    cs = ClientSet(username="...", password="...", tenant_name="...", auth_uri="...")

    print cs.compute.servers.list()
    print cs.identity_public.tenants.list()
