import logging
import uuid
import unittest
import sys

from openstackclient_base.base import monkey_patch
monkey_patch()


LOG = logging.getLogger()
ch = logging.StreamHandler()
LOG.setLevel(logging.DEBUG)
LOG.addHandler(ch)

http_client = None


def test_nova():
    from openstackclient_base.nova.client import ComputeClient
    print ComputeClient(http_client).servers.list()


def test_keystone():
    from openstackclient_base.keystone.client import IdentityPublicClient
    print IdentityPublicClient(http_client).tenants.list()


def test_glance(filename):
    from openstackclient_base.glance.v1.client import ImageClient
    ic = ImageClient(http_client)

    print ic.images.list()

    create_params = {'name': "test-img-%s" % uuid.uuid4(),
                     'disk_format': "raw",
                     'container_format': "ovf"}
    if filename == "-":
        f = sys.stdin
    else:
        f = open(filename, "rb")
    img_desc = ic.images.create(data=f, **create_params)
    f.close()
    print img_desc
    img_id = img_desc.id

    img = ic.images.get(img_id, True)
    with open(img_id, "wb") as f:
        for chunk in img.data:
            f.write(chunk)


def test_unbound_token(auth):
    from openstackclient_base.client import HttpClient
    from openstackclient_base.keystone.client import IdentityPublicClient
    unbound = HttpClient(username=auth[0],
                         password=auth[1],
                         auth_uri=auth[3])
    print IdentityPublicClient(unbound).tenants.list()


def main():
    from openstackclient_base.client import HttpClient
    global http_client
    auth = sys.argv[2:]
    http_client = HttpClient(username=auth[0],
                             password=auth[1],
                             tenant_name=auth[2],
                             auth_uri=auth[3])
    cmd = sys.argv[1]
    if cmd == "keystone":
        test_keystone()
    elif cmd == "nova":
        test_nova()
    elif cmd == "unbound":
        test_unbound_token(auth)
    else:
        test_glance(sys.argv[6])


class NeoTests(unittest.TestCase):
    def test_empty_url(self):
        import socket
        from openstackclient_base.client import HttpClient
        c = HttpClient()
        self.assertRaises(socket.gaierror, lambda: c.request('', '/users'))


if __name__ == "__main__":
    main()
    # unittest.main()
    # NOTE(apugachev) we can not jsut use unittest.main here.
    # Use "python -m unittest discover" instead.
