# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.
# Copyright 2012 Grid Dynamics.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import logging
import re
import os
import urlparse

import httplib2

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, "parse_qsl"):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from openstackclient_base import exceptions


LOG = logging.getLogger(__name__)


class HttpClient(httplib2.Http):

    USER_AGENT = "python-openstackclient-base"

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, auth_uri=None,
                 endpoint=None, token=None, region_name=None,
                 timeout=None):
        super(HttpClient, self).__init__(timeout=timeout)
        self.username = username
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.password = password
        auth_uri = auth_uri or auth_url
        self.auth_uri = auth_uri.rstrip("/") if auth_uri else None
        self.token = token
        self.endpoint = endpoint
        self.region_name = region_name

        self.access = None

        # httplib2 overrides
        self.force_exception_to_status_code = True

    def url_for(self, endpoint_type, service_type, region_name=None):
        """Fetch an endpoint from the service catalog.

        Fetch the specified endpoint from the service catalog for
        a particular endpoint attribute. If no attribute is given, return
        the first endpoint of the specified type.

        See tests for a sample service catalog.
        """
        catalog = self.access.get("serviceCatalog", [])
        if not region_name:
            region_name = self.region_name
        for service in catalog:
            if service["type"] != service_type:
                continue

            endpoints = service["endpoints"]
            for endpoint in endpoints:
                if region_name and endpoint["region"] != region_name:
                    continue
                return endpoint[endpoint_type]

        raise exceptions.EndpointNotFound("Endpoint not found.")

    def get_endpoints(self, endpoint_type=None, service_type=None):
        """Fetch and filter endpoints for the specified service(s)

        Returns endpoints for the specified service (or all) and
        that contain the specified type (or all).
        """
        sc = {}
        for service in self.access.get("serviceCatalog", []):
            if service_type and service_type != service["type"]:
                continue
            sc[service["type"]] = []
            for endpoint in service["endpoints"]:
                if endpoint_type and endpoint_type not in endpoint.keys():
                    continue
                if region_name and endpoint["region"] != region_name:
                    continue
                sc[service["type"]].append(endpoint)
        return sc

    def authenticate(self):
        """ Authenticate against the keystone API v2.0.
        """
        if self.token:
            params = {"auth": {"token": {"id": self.token}}}
        elif self.username and self.password:
            params = {"auth": {"passwordCredentials":
                                   {"username": self.username,
                                    "password": self.password}}}
        else:
            raise ValueError("A username and password or token is required.")
        if self.tenant_id:
            params["auth"]["tenantId"] = self.tenant_id
        elif self.tenant_name:
            params["auth"]["tenantName"] = self.tenant_name
        resp, body = self.request(
            self.concat_url(self.auth_uri, "/v2.0/tokens"), "POST",
            body=params)
        try:
            self.access = body["access"]
        except ValueError:
            LOG.error("expected `access` key in keystone response")
            raise

    def http_log(self, args, kwargs, resp, body):
        if not LOG.isEnabledFor(logging.DEBUG):
            return

        string_parts = ["curl -i"]
        for element in args:
            if element in ("GET", "POST"):
                string_parts.append(" -X %s" % element)
            else:
                string_parts.append(" %s" % element)

        for element in kwargs["headers"]:
            header = " -H \"%s: %s\"" % (element, kwargs["headers"][element])
            string_parts.append(header)

        LOG.debug("REQ: %s\n" % "".join(string_parts))
        if "body" in kwargs:
            LOG.debug("REQ BODY: %s\n" % (kwargs["body"]))
        LOG.debug("RESP: %s\nRESP BODY: %s\n", resp, body)

    def request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib2.Http.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        request_kwargs = kwargs.copy()
        request_kwargs.setdefault("headers", kwargs.get("headers", {}))
        request_kwargs["headers"]["User-Agent"] = self.USER_AGENT
        if "body" in kwargs:
            request_kwargs["headers"]["Content-Type"] = "application/json"
            request_kwargs["body"] = json.dumps(kwargs["body"])

        resp, body = super(HttpClient, self).request(
            url, method, **request_kwargs)

        self.http_log((url, method,), request_kwargs, resp, body)

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                LOG.debug("Could not decode JSON from body: %s" % body)
        else:
            LOG.debug("No body was returned.")
            body = None

        if resp.status in (400, 401, 403, 404, 408, 409, 413, 500, 501):
            LOG.exception("Request returned failure status.")
            raise exceptions.from_response(resp, body)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self.request(resp["location"], method, **kwargs)

        return resp, body

    version_re = re.compile(r"v\d+\.?\d*")

    @staticmethod
    def concat_url(endpoint, url):
        version = None
        endpoint = endpoint.rstrip("/")
        spl = endpoint.rsplit("/", 1)
        if HttpClient.version_re.match(spl[1]):
            endpoint = spl[0]
            version = spl[1]
        url = url.strip("/")
        spl = url.split("/", 1)
        if HttpClient.version_re.match(spl[0]):
            version = spl[0]
            url = spl[1]
        if version:
            return "%s/%s/%s" % (endpoint, version, url)
        else:
            return "%s/%s" % (endpoint, url)

    def _cs_request(self,
                    client,
                    url, method, **kwargs):
        if self.endpoint:
            endpoint = self.endpoint
            token = self.token
        else:
            if not self.access:
                self.authenticate()
                client.endpoint = None
            endpoint = self.url_for(
                client.endpoint_type,
                client.service_type)
            if not client.endpoint:
                client.endpoint = endpoint
            token = self.access["token"]["id"]

        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-Auth-Token"] = token
        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            return self.request(
                self.concat_url(endpoint, url), method, **kwargs)
        except exceptions.Unauthorized:
            if self.endpoint:
                raise
            self.authenticate()
            endpoint = self.url_for(
                client.endpoint_type,
                client.service_type)
            client.endpoint = endpoint
            token = self.access["token"]["id"]
            kwargs["headers"]["X-Auth-Token"] = token
            return self.request(
                self.concat_url(endpoint, url), method, **kwargs)


class BaseClient(object):
    """
    Top-level object to access the OpenStack API.
    """

    service_type = None
    endpoint_type = "publicURL"
    endpoint = None

    def __init__(self, client, extensions=None):
        self.client = client

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

    def _cs_request(self, url, method, **kwargs):
        return self.client._cs_request(
            self, url, method, **kwargs)

    def get(self, url, **kwargs):
        return self._cs_request(url, "GET", **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, "POST", **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, "PUT", **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, "DELETE", **kwargs)
