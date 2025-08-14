#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import abc
import urllib.parse
from typing import Generic, Union

from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.cache import Cache
from meatie.internal.types import PT, T
from meatie.types import Duration, Request

__all__ = ["cache"]


class CacheOption:
    """Configure caching of endpoint call results."""

    def __init__(self, ttl: Duration, shared: bool = False) -> None:
        """Creates a new cache option.

        Parameters:
            ttl: the time-to-live of the cache entry in seconds
            shared: if set to False (default) the cache entry will be stored in the local cache owned by the client instance. Records cached by another client instance will not be visible.
                Otherwise, if set to True, all client that are instances of the same Python class will share the same cache.
        """
        self.ttl = ttl
        self.shared = shared

    def __call__(
        self,
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]],
    ) -> None:
        """Apply the cache option to the endpoint descriptor."""
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    @property
    def priority(self) -> int:
        """Returns: the priority of the cache operator."""
        return 20

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        operator: BaseOperator[T]
        if self.shared:
            operator = SharedOperator[T](self.ttl)
        else:
            operator = LocalOperator[T](self.ttl)
        descriptor.register_operator(self.priority, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        operator: BaseAsyncOperator[T]
        if self.shared:
            operator = SharedAsyncOperator[T](self.ttl)
        else:
            operator = LocalAsyncOperator[T](self.ttl)
        descriptor.register_operator(self.priority, operator)


cache = CacheOption


def get_key(request: Request) -> str:
    key = request.path
    if request.params:
        key += "?" + urllib.parse.urlencode(request.params)
    return key


class BaseOperator(Generic[T]):
    """Base class for cache operators. Saves the value returned from the endpoint in cache."""

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
        """Returns: the cache storage to use."""
        ...


class LocalOperator(BaseOperator[T]):
    """Cache operator that stores the value returned from the endpoint in the local cache owned by the client instance."""

    def _storage(self, ctx: Context[T]) -> Cache:
        return ctx.client.local_cache


class SharedOperator(BaseOperator[T]):
    """Cache operator that stores the value returned from the endpoint in the cache shared by all client instances of the same Python class."""

    def _storage(self, ctx: Context[T]) -> Cache:
        return ctx.client.shared_cache


class BaseAsyncOperator(Generic[T]):
    """Base class for asynchronous cache operators. Saves the value returned from the endpoint in cache."""

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
        """Returns: the cache storage to use."""
        ...


class LocalAsyncOperator(BaseAsyncOperator[T]):
    """Asynchronous cache operator that stores the value returned from the endpoint in the local cache owned by the client instance."""

    def _storage(self, ctx: AsyncContext[T]) -> Cache:
        return ctx.client.local_cache


class SharedAsyncOperator(BaseAsyncOperator[T]):
    """Asynchronous cache operator that stores the value returned from the endpoint in the cache shared by all client instances of the same Python class."""

    def _storage(self, ctx: AsyncContext[T]) -> Cache:
        return ctx.client.shared_cache
