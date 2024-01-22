#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import urllib.parse
from typing import Any, Optional

from aiohttp import ClientResponse, ClientSession
from typing_extensions import Self

from . import INF, CacheStore, Limiter, Rate, Request


class Client:
    shared_cache: CacheStore

    def __init__(
        self,
        session: ClientSession,
        session_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[CacheStore] = None,
        limiter: Optional[Limiter] = None,
    ):
        self.session = session
        self.local_cache = local_cache if local_cache is not None else CacheStore()
        self.limiter = limiter if limiter is not None else Limiter(Rate.max, INF)
        self.session_params = session_params if session_params else {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls.shared_cache = CacheStore()

    async def make_request(self, request: Request) -> ClientResponse:
        kwargs: dict[str, Any] = self.session_params.copy()

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.query_params:
            path = request.path + "?" + urllib.parse.urlencode(request.query_params)
        else:
            path = request.path

        response = await self.session.request(request.method, path, **kwargs)
        return response

    async def authenticate(self, request: Request) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.close()
