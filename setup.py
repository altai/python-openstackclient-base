# Copyright 2012 OpenStack LLC.
# Copyright 2012 Grid Dynamics.
# All Rights Reserved
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
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

import setuptools


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setuptools.setup(
    name="python-openstackclient-base",
    version="0.1",
    description="OpenStack API client base",
    long_description=read('README.rst'),
    url='https://github.com/openstack/python-openstackclient-base',
    license="Apache License, Version 2.0",
    author='OpenStack Client Contributors',
    author_email='openstack@lists.launchpad.net',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
       'Development Status :: 2 - Pre-Alpha',
       'Intended Audience :: Developers',
       'Intended Audience :: Information Technology',
       'License :: OSI Approved :: Apache Software License',
       'Operating System :: OS Independent',
       'Programming Language :: Python',
    ]
)
