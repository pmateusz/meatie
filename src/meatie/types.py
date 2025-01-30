#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Union, runtime_checkable

from typing_extensions import Literal

Method = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]

Duration = float
Time = float

MINUTE = 60
HOUR = 3600
DAY = 86400

INF = float("inf")


@dataclass()
class Request:
    """Specification of an HTTP request.

    Value types used for headers and query parameters must be supported by the underlying HTTP client library.
    """

    method: Method
    path: str
    params: dict[str, Any]
    headers: dict[str, Any]
    data: Optional[Union[str, bytes]] = None
    json: Any = None


@runtime_checkable
class AsyncResponse(Protocol):
    """Interface for an asynchronous HTTP response."""

    @property
    def status(self) -> int:
        """Get HTTP status code.

        Returns:
            HTTP status code.
        """
        ...

    async def read(self) -> bytes:
        """Reads the response body and returns it as bytes without decoding.

        Returns:
            Response body as bytes.

        Raises:
            ResponseError: If an error occurs while reading the response body.
        """
        ...

    async def text(self) -> str:
        """Reads the response body and decodes it to a string using encoding declared in the Content-Type response header.

        Returns:
            Response body as string.

        Raises:
            ResponseError: If an error occurs while reading the response body.
        """
        ...

    async def json(self) -> Any:
        """Reads the response body and decodes it to JSON.

        Returns:
            Response body as JSON.

        Raises:
            ResponseError: If an error occurs while reading the response body.
            ParseResponseError: If an error occurs while parsing the response body.
        """
        ...


@runtime_checkable
class Response(Protocol):
    """Interface for an HTTP response."""

    @property
    def status(self) -> int:
        """Get HTTP status code.

        Returns:
            HTTP status code.
        """
        ...

    def read(self) -> bytes:
        """Reads the response body and returns it as bytes without decoding.

        Returns:
            Response body as bytes.

        Raises:
            ResponseError: If an error occurs while reading the response body.
        """
        ...

    def text(self) -> str:
        """Reads the response body and decodes it to a string using encoding declared in the Content-Type response header.

        Returns:
            Response body as string.

        Raises:
            ResponseError: If an error occurs while reading the response body.
        """
        ...

    def json(self) -> Any:
        """Reads the response body and decodes it to JSON.

        Returns:
            Response body as JSON.

        Raises:
            ResponseError: If an error occurs while reading the response body.
            ParseResponseError: If an error occurs while parsing the response body.
        """
        ...
