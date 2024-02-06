#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from asyncio import AbstractEventLoop
from typing import Any, Awaitable, Callable, Optional, Protocol

from typing_extensions import Self

from meatie import Request
from meatie.internal import ResponseBodyType

from .client import AsyncClientType, BaseAsyncClient


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


class AsyncContext(Protocol[ResponseBodyType]):
    @property
    def client(self) -> BaseAsyncClient:
        ...

    @property
    def request(self) -> Request:
        ...

    @property
    def response(self) -> Optional[AsyncResponse]:
        ...

    async def proceed(self) -> ResponseBodyType:
        ...


AsyncOperator = Callable[[AsyncContext[ResponseBodyType]], Awaitable[ResponseBodyType]]


class ResponseAdapter:
    def __init__(self, loop: AbstractEventLoop, response: AsyncResponse) -> None:
        self.loop = loop
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status

    def read(self) -> bytes:
        return self.loop.run_until_complete(self.response.read())

    def text(self) -> str:
        return self.loop.run_until_complete(self.response.text())

    def json(self) -> dict[str, Any]:
        return self.loop.run_until_complete(self.response.json())


class ClientAdapter:
    def __init__(self, loop: AbstractEventLoop, client: AsyncClientType) -> None:
        self.loop = loop
        self.client = client

    def send(self, request: Request) -> ResponseAdapter:
        async_response = self.loop.run_until_complete(self.client.send(request))
        return ResponseAdapter(self.loop, async_response)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException], exc_val: Optional[BaseException], exc_tb: Any
    ) -> None:
        self.loop.run_until_complete(self.client.__aexit__(exc_type, exc_val, exc_tb))
