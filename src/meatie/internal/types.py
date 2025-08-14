#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, TypeVar

from typing_extensions import Optional, ParamSpec, Protocol, Self

from meatie.types import AsyncResponse, Request, Response

__all__ = [
    "VT",
    "T",
    "T_In",
    "T_Out",
    "PT",
    "RequestBodyType",
    "ResponseBodyType",
    "Client",
    "ClientType",
    "Context",
    "AsyncClient",
    "AsyncClientType",
    "AsyncContext",
]

VT = TypeVar("VT")
T = TypeVar("T")
T_In = TypeVar("T_In", contravariant=True)
T_Out = TypeVar("T_Out", covariant=True)
PT = ParamSpec("PT")
RequestBodyType = TypeVar("RequestBodyType", contravariant=True)
ResponseBodyType = TypeVar("ResponseBodyType", covariant=True)


class Client(Protocol):
    """Interface of a synchronous HTTP client required for integration with the Meatie library."""

    def send(self, request: Request) -> Response:
        """Sends an HTTP request and returns the HTTP response.

        Args:
            request: the HTTP request to send

        Returns:
            the HTTP response
        """
        ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None: ...


ClientType = TypeVar("ClientType", bound=Client, covariant=True)


class Context(Protocol[ClientType, ResponseBodyType]):
    """Interface of a context passed by the Meatie library to operators that customize the behaviour of endpoint calls.

    See Also:
        meatie.cache - cache results from the endpoint calls
        meatie.limit - delay the endpoint calls that exceed the rate limit
        meatie.retry - implement a retry strategy for the endpoint calls that failed
        meatie.body - customize handling of HTTP response body, such as text decoding, parsing JSON and detecting errors
    """

    @property
    def client(self) -> ClientType:
        """Returns: the synchronous HTTP client."""
        ...

    @property
    def request(self) -> Request:
        """Returns: the HTTP request."""
        ...

    @property
    def response(self) -> Optional[Response]:
        """Returns: the HTTP response if available."""
        ...

    def proceed(self) -> ResponseBodyType:
        """Applies the next operator in the chain.

        Returns: the result of the endpoint call.
        """
        ...


class AsyncClient(Protocol):
    """Interface of an asynchronous HTTP client required for integration with the Meatie library."""

    async def send(self, request: Request) -> AsyncResponse:
        """Sends an HTTP request and returns the HTTP response.

        Args:
            request: the HTTP request to send

        Returns:
            the HTTP response
        """
        ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None: ...


AsyncClientType = TypeVar("AsyncClientType", bound=AsyncClient, covariant=True)


class AsyncContext(Protocol[AsyncClientType, ResponseBodyType]):
    """Interface of a context passed by the Meatie library to operators that customize the behaviour of endpoint calls.

    See Also:
        meatie.cache - cache results from the endpoint calls
        meatie.limit - delay the endpoint calls that exceed the rate limit
        meatie.retry - implement a retry strategy for the endpoint calls that failed
        meatie.body - customize handling of HTTP response body, such as text decoding, parsing JSON and detecting errors
    """

    @property
    def client(self) -> AsyncClientType:
        """Returns: the asynchronous HTTP client."""
        ...

    @property
    def request(self) -> Request:
        """Returns: the HTTP request."""
        ...

    @property
    def response(self) -> Optional[AsyncResponse]:
        """Returns: the HTTP response if available."""
        ...

    async def proceed(self) -> ResponseBodyType:
        """Applies the next operator in the chain.

        Returns: the result of the endpoint call.
        """
        ...
