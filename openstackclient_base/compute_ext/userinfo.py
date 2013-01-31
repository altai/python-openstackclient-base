# Copyright 2013 Grid Dynamics Inc.


from openstackclient_base import base
from novaclient.v1_1.keypairs import Keypair


class UserKeypairManager(base.Manager):
    """
    Extend KeypairManager with functions provided by nova-userinfo.
    """
    resource_class = Keypair

    def create(self, user, name, public_key):
        """
        Create a keypair for a user

        :param user: user to create keypair for
        :param name: name for the keypair to create
        :param public_key: existing public key to import
        """
        body = {'keypair': {
            'name': name,
            'public_key': public_key
        }}
        return self._create('/gd-userinfo/%s/keypairs' % base.getid(user),
                            body, 'keypair')

    def delete(self, user, key):
        """
        Delete a keypair for a user

        :param user: user to delete keypair for
        :param key: The :class:`Keypair` (or its ID) to delete.
        """
        self._delete('/gd-userinfo/%s/keypairs/%s'
                     % (base.getid(user), base.getid(key)))

    def list(self, user):
        """
        Get a list of keypairs.
        """
        return self._list('/gd-userinfo/%s/keypairs' % base.getid(user),
                          'keypairs')

    def get(self, user, key):
        """
        Get specific keypair for a user

        :param user: user who owns the keypair
        :param key: The :class:`Keypair` (or its ID) to get
        """
        return self._get('/gd-userinfo/%s/keypairs/%s'
                         % (base.getid(user), base.getid(key)),
                         'keypair')
