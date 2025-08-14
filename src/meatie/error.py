#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Union

from typing_extensions import deprecated

from meatie.types import AsyncResponse, Response


class MeatieError(Exception):
    """Base class for all Meatie exceptions.

    Check `__cause__` for the original exception raised by the underlying HTTP client library.
    """

    ...


class RetryError(MeatieError):
    """Raised when all retry attempts have been exhausted."""

    ...


@deprecated("Use `HttpStatusError` instead.")
class RateLimitExceeded(MeatieError):
    """Deprecated: Use `HttpStatusError` instead.

    Scheduled for removal.
    """

    ...


class TransportError(MeatieError):
    """Raised in response to a transport error, i.e., too many redirects, a protocol error, a network error."""

    ...


class ProxyError(TransportError):
    """Raised when a proxy error occurs.

    Request failed due to a proxy error, i.e., the proxy server is refusing connections, the proxy server does not
     accept CONNECT requests.
    """

    ...


class ServerError(TransportError):
    """Raised when a server or a network error occurs.

    HTTP request failed because of the server-side error i.e., server violated HTTP protocol by returning a corrupted response,
    server disconnected the connection prematurely, server certificate is invalid, cannot establish a connection with the server.
    """

    ...


class Timeout(ServerError):
    """Raised when a request times out, i.e., connection timeout, read timeout, write timeout."""

    ...


class RequestError(MeatieError):
    """Raised when the request cannot be sent by the underlying HTTP client library, i.e., invalid URL, unsupported protocol.

    There is no point in retrying the operation.
    """

    ...


class ResponseError(MeatieError):
    """Raised when the response body cannot be read or decoded to a string."""

    def __init__(self, response: Union[Response, AsyncResponse]) -> None:
        """Creates a ResponseError.

        Args:
            response: HTTP response object.
        """
        self.response = response


class HttpStatusError(ResponseError):
    """Dedicated for handling HTTP status errors. Currently, it is not raised by the Meatie library."""

    ...


class ParseResponseError(ResponseError):
    """Raised when the response body cannot be parsed to a JSON object."""

    def __init__(
        self,
        text: str,
        response: Union[Response, AsyncResponse],
    ) -> None:
        """Creates a ParseResponseError.

        Args:
            text: response body in the text format.
            response: HTTP response object.
        """
        super().__init__(response)

        self.text = text
