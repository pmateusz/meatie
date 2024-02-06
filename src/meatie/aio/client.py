#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from abc import abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Any, Optional, TypeVar

from meatie import Request
from meatie.internal import INF, CacheStore, Limiter, Rate


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


AsyncClientType = TypeVar("AsyncClientType", bound=BaseAsyncClient)
