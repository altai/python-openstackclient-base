# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 Nebula, Inc.
"""
Exception definitions.
"""


class ClientException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    pass


class CommandError(ClientException):
    pass


class AuthorizationFailure(ClientException):
    pass


class NoTokenLookupException(ClientException):
    """This form of authentication does not support looking up
       endpoints from an existing token."""
    pass


class EndpointNotFound(ClientException):
    """Could not find Service or Region in Service Catalog."""
    pass


class ClientConnectionError(ClientException):
    pass


class HttpException(ClientException):
    """
    The base exception class for all exceptions this library raises.
    """
    def __init__(self, code, message=None, details=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details

    def __str__(self):
        return "%s (HTTP %s)" % (self.message, self.code)


class BadRequest(HttpException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(HttpException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(HttpException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(HttpException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class Conflict(HttpException):
    """
    HTTP 409 - Conflict
    """
    http_status = 409
    message = "Conflict"


class OverLimit(HttpException):
    """
    HTTP 413 - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(HttpException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in HttpException.__subclasses__())
#
# Instead, we have to hardcode it:
_code_map = dict((c.http_status, c) for c in [BadRequest,
                                              Unauthorized,
                                              Forbidden,
                                              NotFound,
                                              OverLimit,
                                              HTTPNotImplemented])


def from_response(response, body):
    """
    Return an instance of an HttpException or subclass
    based on an httplib2 response.

    Usage::

        resp, body = http.request(...)
        if resp.status != 200:
            raise exception_from_response(resp, body)
    """
    cls = _code_map.get(response.status, HttpException)
    if body:
        if isinstance(body, dict):
            error = body.itervalues().next() if body else {}
            if not isinstance(error, dict):
                error = body
            message = error.get("message", None)
            details = error.get("details", None)
        else:
            message = "Unable to communicate with server: %s." % body
            details = None
        return cls(code=response.status, message=message, details=details)
    else:
        return cls(code=response.status)
