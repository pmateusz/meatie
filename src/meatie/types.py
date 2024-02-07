#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Any, Optional, Protocol, TypeVar, Union

from typing_extensions import Literal, Self

from meatie.internal import ResponseBodyType

Method = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]


@dataclass()
class Request:
    method: Method
    path: str
    query_params: dict[str, Union[str, int]]
    headers: dict[str, Union[str, bytes]]
    data: Optional[Union[str, bytes]] = None
    json: Any = None


class Response(Protocol):
    @property
    def status(self) -> int:
        ...

    def read(self) -> bytes:
        ...

    def text(self, *args: Any, **kwargs: Any) -> str:
        ...

    def json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        ...


class Client(Protocol):
    def send(self, request: Request) -> Response:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        ...


ClientType = TypeVar("ClientType", bound=Client, covariant=True)


class Context(Protocol[ClientType, ResponseBodyType]):
    @property
    def client(self) -> ClientType:
        ...

    @property
    def request(self) -> Request:
        ...

    @property
    def response(self) -> Optional[Response]:
        ...

    def proceed(self) -> ResponseBodyType:
        ...


class AsyncResponse(Protocol):
    @property
    def status(self) -> int:
        ...

    async def read(self) -> bytes:
        ...

    async def text(self, encoding: Optional[str] = None) -> str:
        ...

    async def json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        ...


class AsyncClient(Protocol):
    async def send(self, request: Request) -> AsyncResponse:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        ...


AsyncClientType = TypeVar("AsyncClientType", bound=AsyncClient, covariant=True)


class AsyncContext(Protocol[AsyncClientType, ResponseBodyType]):
    @property
    def client(self) -> AsyncClientType:
        ...

    @property
    def request(self) -> Request:
        ...

    @property
    def response(self) -> Optional[AsyncResponse]:
        ...

    async def proceed(self) -> ResponseBodyType:
        ...
