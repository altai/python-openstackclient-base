# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.
# Copyright 2012 Grid Dynamics.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""


import errno
import logging
import re
import os

import httplib
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

try:
    import sendfile
except ImportError:
    sendfile = None

# Python 2.5 compat fix
if not hasattr(urlparse, "parse_qsl"):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from openstackclient_base import exceptions


LOG = logging.getLogger(__name__)
CHUNKSIZE = 65536
VERSION_REGEX = re.compile(r"v\d+\.?\d*")


def seekable(body):
    # pipes are not seekable, avoids sendfile() failure on e.g.
    #   cat /path/to/image | glance add ...
    # or where add command is launched via popen
    try:
        os.lseek(body.fileno(), 0, os.SEEK_SET)
        return True
    except OSError as e:
        return (e.errno != errno.ESPIPE)


def sendable(body):
    return (sendfile is not None and
            hasattr(body, "fileno") and
            seekable(body))


def body_iterator(connection, body):
    if sendable(body) and isinstance(connection, httplib.HTTPConnection):
        return SendFileIterator(connection, body)
    elif hasattr(body, "read"):
        return FileReaderIterator(body)
    elif isinstance(body, collections.Iterable):
        return body
    else:
        return None


class FileReaderIterator(object):

    """
    A class that acts as an iterator over an image file's
    chunks of data.
    """

    def __init__(self, source):
        """
        Constructs the object from a readable image source
        (such as an HTTPResponse or file-like object)
        """
        self.source = source

    def __iter__(self):
        """
        Exposes an iterator over the chunks of data in the
        image file.
        """
        while True:
            chunk = self.source.read(CHUNKSIZE)
            if chunk:
                yield chunk
            else:
                break


class SendFileIterator(object):
    """
    Emulate iterator pattern over sendfile, in order to allow
    send progress be followed by wrapping the iteration.
    """
    def __init__(self, connection, body):
        self.connection = connection
        self.body = body
        self.offset = 0
        self.sending = True

    def __iter__(self):
        class OfLength:
            def __init__(self, len):
                self.len = len

            def __len__(self):
                return self.len

        while self.sending:
            try:
                sent = sendfile.sendfile(self.connection.sock.fileno(),
                                         self.body.fileno(),
                                         self.offset,
                                         CHUNKSIZE)
            except OSError as e:
                # suprisingly, sendfile may fail transiently instead of
                # blocking, in which case we select on the socket in order
                # to wait on its return to a writeable state before resuming
                # the send loop
                if e.errno in (errno.EAGAIN, errno.EBUSY):
                    wlist = [self.connection.sock.fileno()]
                    rfds, wfds, efds = select.select([], wlist, [])
                    if wfds:
                        continue
                raise

            self.sending = (sent != 0)
            self.offset += sent
            yield OfLength(sent)


class HTTPSClientAuthConnection(httplib.HTTPSConnection):
    """
    Class to make a HTTPS connection, with support for
    full client-based SSL Authentication

    :see http://code.activestate.com/recipes/
            577548-https-httplib-client-connection-with-certificate-v/
    """

    def __init__(self, host, port, key_file, cert_file,
                 ca_file, timeout=None, insecure=False):
        httplib.HTTPSConnection.__init__(self, host, port, key_file=key_file,
                                         cert_file=cert_file)
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_file = ca_file
        self.timeout = timeout
        self.insecure = insecure

    def connect(self):
        """
        Connect to a host on a given (SSL) port.
        If ca_file is pointing somewhere, use it to check Server Certificate.

        Redefined/copied and extended from httplib.py:1105 (Python 2.6.x).
        This is needed to pass cert_reqs=ssl.CERT_REQUIRED as parameter to
        ssl.wrap_socket(), which forces SSL to check server certificate against
        our client certificate.
        """
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        # Check CA file unless 'insecure' is specificed
        if self.insecure is True:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        cert_reqs=ssl.CERT_NONE)
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        ca_certs=self.ca_file,
                                        cert_reqs=ssl.CERT_REQUIRED)


class HttpClient(object):

    USER_AGENT = "python-openstackclient-base"

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, auth_uri=None,
                 endpoint=None, token=None, region_name=None,
                 access=None,
                 use_ssl=False, insecure=False,
                 key_file=None, cert_file=None, ca_file=None,
                 timeout=None):
        self.username = username
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.password = password
        self.auth_uri = auth_uri or auth_url
        self.token = token
        self.endpoint = endpoint
        self.region_name = region_name
        self.access = access

        connect_kwargs = {} if timeout is None else {"timeout": timeout}

        self.use_ssl = use_ssl
        if use_ssl:
            if (cert_file is not None) != (key_file is None):
                raise ValueError("cert_file and key_file"
                    "should be both None or not None")

            for filename in key_file, cert_file, ca_file:
                if (filename is not None and
                    not os.path.exists(filename)):
                    msg = "File %s does not exist" % filename
                    raise exceptions.ClientConnectionError(msg)
            for arg in "key_file", "cert_file", "ca_file", "insecure":
                connect_kwargs[arg] = locals()[arg]

        self.connect_kwargs = connect_kwargs

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
            LOG.error("expected `access' key in keystone response")
            raise

    def http_log(self, uri, method, headers, body, resp, resp_body):
        if not LOG.isEnabledFor(logging.DEBUG):
            return

        string_parts = ["curl -i -X '%s' '%s'" % (method, uri)]

        for key, value in headers.iteritems():
            string_parts.append(" -H '%s: %s'" % (key, value))
        if isinstance(body, basestring):
            string_parts.append(" -d '%s'" % body)
        LOG.debug("REQ: %s\n" % "".join(string_parts))
        if resp:
            LOG.debug("RESP: %s\n" % resp.status)
        if resp_body:
            LOG.debug("RESP BODY: %s\n" % resp_body)

    def request(self, uri, method, **kwargs):
        parsed = urlparse.urlsplit(uri)
        if not parsed.netloc:
            parsed = urlparse.urlparse("http://%s" % url)
        use_ssl = parsed.scheme == "https"
        connection_class = (httplib.HTTPSConnection
                            if use_ssl
                            else httplib.HTTPConnection)
        c = connection_class(parsed.netloc, **self.connect_kwargs)
        request_uri = ("?".join([parsed.path, parsed.query])
                       if parsed.query
                       else parsed.path)

        headers = kwargs.get("headers", {})
        headers["User-Agent"] = self.USER_AGENT
        body = kwargs.get("body", None)
        if isinstance(body, (dict, list)):
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
        elif body is not None:
            headers["Content-Type"] = "application/octet-stream"

        def _pushing(method):
            return method.lower() in ("post", "put")

        def _simple(body):
            return body is None or isinstance(body, basestring)

        def _filelike(body):
            return hasattr(body, "read")

        def _sendbody(connection, iter):
            connection.endheaders()
            for sent in iter:
                # iterator has done the heavy lifting
                pass

        def _chunkbody(connection, iter):
            connection.putheader("Transfer-Encoding", "chunked")
            connection.endheaders()
            for chunk in iter:
                connection.send("%x\r\n%s\r\n" % (len(chunk), chunk))
            connection.send("0\r\n\r\n")

        # Do a simple request or a chunked request, depending
        # on whether the body param is file-like or iterable and
        # the method is PUT or POST
        #
        try:
            resp, resp_body = None, None
            if not _pushing(method) or _simple(body):
                # Simple request...
                c.request(method, request_uri, body, headers)
            else:
                iter = body_iterator(c, body)
                if iter is None:
                    raise TypeError("Unsupported body type: %s" % body.__class__)

                c.putrequest(method, request_uri)
                use_sendfile = isinstance(iter, SendFileIterator)

                # According to HTTP/1.1, Content-Length and Transfer-Encoding
                # conflict.
                for header, value in headers.iteritems():
                    if use_sendfile or header.lower() != "content-length":
                        c.putheader(header, value)

                if use_sendfile:
                    # send actual file without copying into userspace
                    _sendbody(c, iter)
                else:
                    # otherwise iterate and chunk
                    _chunkbody(c, iter)

            resp = c.getresponse()
            status_class = resp.status / 100
            if status_class != 2 or kwargs.get("read_body", True):
                resp_body = resp.read()
            else:
                resp_body = None
        finally:
            self.http_log(uri, method, headers, body, resp, resp_body)

        try:
            if resp_body:
                resp_body = json.loads(resp_body)
        except (TypeError, ValueError):
            pass

        if status_class == 3 and not _pushing(method):
            return self.request(resp["location"], method, **kwargs)
        if status_class in (4, 5):
            LOG.exception("Request returned failure status.")
            raise exceptions.from_response(resp, resp_body)

        return (resp, resp_body)

    @staticmethod
    def concat_url(endpoint, url):
        version = None
        endpoint = endpoint.rstrip("/")
        spl = endpoint.rsplit("/", 1)
        if VERSION_REGEX.match(spl[1]):
            endpoint = spl[0]
            version = spl[1]
        url = url.strip("/")
        spl = url.split("/", 1)
        if VERSION_REGEX.match(spl[0]):
            version = spl[0]
            url = spl[1]
        if version:
            return "%s/%s/%s" % (endpoint, version, url)
        else:
            return "%s/%s" % (endpoint, url)

    def cs_request(self, client, url, method, **kwargs):
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

    def __init__(self, http_client, extensions=None):
        self.http_client = http_client
        # a temporary fix for novaclient if monkey_patch is not applied
        self.client = self

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

    def cs_request(self, url, method, **kwargs):
        return self.http_client.cs_request(
            self, url, method, **kwargs)

    def head(self, url, **kwargs):
        return self.cs_request(url, "HEAD", **kwargs)

    def get(self, url, **kwargs):
        return self.cs_request(url, "GET", **kwargs)

    def post(self, url, **kwargs):
        return self.cs_request(url, "POST", **kwargs)

    def put(self, url, **kwargs):
        return self.cs_request(url, "PUT", **kwargs)

    def delete(self, url, **kwargs):
        return self.cs_request(url, "DELETE", **kwargs)
