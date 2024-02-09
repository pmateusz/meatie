#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from abc import abstractmethod
from typing import Any, Optional, TypeVar

from typing_extensions import Self

from meatie import INF, Cache, Limiter, Rate, Request


class BaseAsyncClient:
    shared_cache: Cache

    def __init__(
        self,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Limiter] = None,
    ):
        self.local_cache = local_cache if local_cache is not None else Cache()
        self.limiter = limiter if limiter is not None else Limiter(Rate.max, INF)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls.shared_cache = Cache()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException], exc_tb: Any
    ) -> None:
        return None

    async def authenticate(self, request: Request) -> None:
        pass

    @abstractmethod
    async def send(self, request: Request) -> Any:
        ...


AsyncClientType = TypeVar("AsyncClientType", bound=BaseAsyncClient)
