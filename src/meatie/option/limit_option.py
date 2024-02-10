#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import time
from typing import Awaitable, Callable, Union

from meatie import Duration
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.limit import Tokens
from meatie.internal.types import PT, T

__all__ = ["limit"]


class LimitOption:
    __PRIORITY = 80

    def __init__(
        self,
        tokens: Tokens,
        sleep_func: Union[Callable[[float], Union[None, Awaitable[None]]], None] = None,
    ) -> None:
        self.tokens = tokens
        self.sleep_func = sleep_func

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        if self.tokens <= 0.0:
            return

        sleep_func: Callable[[float], None] = time.sleep
        if self.sleep_func is not None:
            sleep_func = self.sleep_func  # type: ignore[assignment]
        operator = LimitOperator(self.tokens, sleep_func)
        descriptor.register_operator(LimitOption.__PRIORITY, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        if self.tokens <= 0.0:
            return

        sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep
        if self.sleep_func is not None:
            sleep_func = self.sleep_func  # type: ignore[assignment]
        operator = AsyncLimitOperator(self.tokens, sleep_func)
        descriptor.register_operator(LimitOption.__PRIORITY, operator)


limit = LimitOption


class LimitOperator:
    def __init__(self, tokens: Tokens, sleep_func: Callable[[Duration], None]) -> None:
        self.tokens = tokens
        self.sleep_func = sleep_func

    def __call__(self, ctx: Context[T]) -> T:
        current_time = time.monotonic()
        reservation = ctx.client.limiter.reserve_at(current_time, self.tokens)
        delay = reservation.ready_at - current_time
        if delay > 0:
            self.sleep_func(delay)

        return ctx.proceed()


class AsyncLimitOperator:
    def __init__(self, tokens: Tokens, sleep_func: Callable[[Duration], Awaitable[None]]) -> None:
        self.tokens = tokens
        self.sleep_func = sleep_func

    async def __call__(self, ctx: AsyncContext[T]) -> T:
        current_time = time.monotonic()
        reservation = ctx.client.limiter.reserve_at(current_time, self.tokens)
        delay = reservation.ready_at - current_time
        if delay > 0:
            await self.sleep_func(delay)

        return await ctx.proceed()
