#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from abc import abstractmethod
from asyncio import AbstractEventLoop
from contextlib import AbstractAsyncContextManager
from typing import Any, Optional

from typing_extensions import Self

from meatie import Request, INF, CacheStore, Limiter, Rate, AsyncResponse
from meatie.types import AsyncClientType


class BaseAsyncClient(AbstractAsyncContextManager):  # type: ignore[type-arg]
    shared_cache: CacheStore

    def __init__(
        self,
        local_cache: Optional[CacheStore] = None,
        limiter: Optional[Limiter] = None,
    ):
        self.local_cache = local_cache if local_cache is not None else CacheStore()
        self.limiter = limiter if limiter is not None else Limiter(Rate.max, INF)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls.shared_cache = CacheStore()

    async def authenticate(self, request: Request) -> None:
        pass

    @abstractmethod
    async def send(self, request: Request) -> Any:
        ...


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
