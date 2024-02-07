#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import abc
import urllib.parse
from typing import Generic

from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal import (
    CacheStore,
    Duration,
)
from meatie.internal.types import PT, T


class CacheOption:
    __PRIORITY = 25

    def __init__(self, ttl: Duration, shared: bool = False) -> None:
        self.ttl = ttl
        self.shared = shared

    def __call__(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        operator: _Operator[T]
        if self.shared:
            operator = _SharedOperator[T](self.ttl)
        else:
            operator = _LocalOperator[T](self.ttl)

        descriptor.register_operator(CacheOption.__PRIORITY, operator)


class _Operator(Generic[T]):
    def __init__(self, ttl: Duration) -> None:
        self.ttl = ttl

    async def __call__(self, ctx: AsyncContext[T]) -> T:
        key = ctx.request.path
        if ctx.request.query_params:
            key += "?" + urllib.parse.urlencode(ctx.request.query_params)

        storage = self._storage(ctx)
        value_opt = storage.load(key)
        if value_opt is not None:
            return value_opt

        value = await ctx.proceed()
        storage.store(key, value, self.ttl)
        return value

    @abc.abstractmethod
    def _storage(self, ctx: AsyncContext[T]) -> CacheStore:
        ...


class _LocalOperator(_Operator[T]):
    def _storage(self, ctx: AsyncContext[T]) -> CacheStore:
        return ctx.client.local_cache


class _SharedOperator(_Operator[T]):
    def _storage(self, ctx: AsyncContext[T]) -> CacheStore:
        return ctx.client.shared_cache
