#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import abc
import urllib.parse
from typing import Generic, Union

from meatie import Cache, Context, Duration, EndpointDescriptor, Request
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.types import PT, T

__all__ = ["cache"]


class CacheOption:
    __PRIORITY = 25

    def __init__(self, ttl: Duration, shared: bool = False) -> None:
        self.ttl = ttl
        self.shared = shared

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        operator: Operator[T]
        if self.shared:
            operator = SharedOperator[T](self.ttl)
        else:
            operator = LocalOperator[T](self.ttl)
        descriptor.register_operator(CacheOption.__PRIORITY, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        operator: AsyncOperator[T]
        if self.shared:
            operator = SharedAsyncOperator[T](self.ttl)
        else:
            operator = LocalAsyncOperator[T](self.ttl)
        descriptor.register_operator(CacheOption.__PRIORITY, operator)


cache = CacheOption


def get_key(request: Request) -> str:
    key = request.path
    if request.params:
        key += "?" + urllib.parse.urlencode(request.params)
    return key


class _Operator(Generic[T]):
    def __init__(self, ttl: Duration) -> None:
        self.ttl = ttl

    @abc.abstractmethod
    def _storage(self, ctx: Context[T]) -> Cache:
        ...


class Operator(Generic[T]):
    def __init__(self, ttl: Duration) -> None:
        self.ttl = ttl

    def __call__(self, ctx: Context[T]) -> T:
        storage = self._storage(ctx)
        key = get_key(ctx.request)
        value_opt = storage.load(key)
        if value_opt is not None:
            return value_opt

        value = ctx.proceed()
        storage.store(key, value, self.ttl)
        return value

    @abc.abstractmethod
    def _storage(self, ctx: Context[T]) -> Cache:
        ...


class LocalOperator(Operator[T]):
    def _storage(self, ctx: Context[T]) -> Cache:
        return ctx.client.local_cache


class SharedOperator(Operator[T]):
    def _storage(self, ctx: Context[T]) -> Cache:
        return ctx.client.shared_cache


class AsyncOperator(Generic[T]):
    def __init__(self, ttl: Duration) -> None:
        self.ttl = ttl

    async def __call__(self, ctx: AsyncContext[T]) -> T:
        storage = self._storage(ctx)
        key = get_key(ctx.request)
        value_opt = storage.load(key)
        if value_opt is not None:
            return value_opt

        value = await ctx.proceed()
        storage.store(key, value, self.ttl)
        return value

    @abc.abstractmethod
    def _storage(self, ctx: AsyncContext[T]) -> Cache:
        ...


class LocalAsyncOperator(AsyncOperator[T]):
    def _storage(self, ctx: AsyncContext[T]) -> Cache:
        return ctx.client.local_cache


class SharedAsyncOperator(AsyncOperator[T]):
    def _storage(self, ctx: AsyncContext[T]) -> Cache:
        return ctx.client.shared_cache
