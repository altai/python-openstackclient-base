# Copyright 2012 Grid Dynamics.

import sys
from openstackclient_base import base


for mod in ("glanceclient.common",
            "novaclient",
            "novaclient.v1_1",
            "keystoneclient"):
    orig_mod = sys.modules.get("%s.base" % mod)
    if orig_mod is None:
        orig_mod =  __import__(mod, {}, {}, ["base"]).base
    for attr in ("getid",
                 "Manager",
                 "ManagerWithFind",
                 "Resource",
                 "BootingManagerWithFind"):
        setattr(orig_mod, attr, getattr(base, attr))
