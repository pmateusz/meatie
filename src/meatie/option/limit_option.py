#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import time
from typing import Awaitable, Callable, Generic, Union

from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.limit import Tokens
from meatie.internal.types import PT, T
from meatie.types import Duration

__all__ = ["limit"]


class LimitOption:
    """Configure the rate limit for the endpoint calls."""

    def __init__(
        self,
        tokens: Tokens,
        sleep_func: Union[Callable[[float], Union[None, Awaitable[None]]], None] = None,
    ) -> None:
        """Creates a new rate limit option.

        The number of available tokens at a given time are controlled by the rate limiter instance used by the client.
        Meatie provides leaky bucket rate limiter implementation with constant replenishment rate and burst size. See meatie.Limiter.

        Parameters:
            tokens: number of tokens consumed by the endpoint call
            sleep_func: the sleep function to use. Default behaviour is to rely on the Python standard library functions: time.sleep and asyncio.sleep for async functions.
        """
        self.tokens = tokens
        self.sleep_func = sleep_func

    def __call__(
        self,
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]],
    ) -> None:
        """Apply the rate limit option to the endpoint descriptor."""
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    @property
    def priority(self) -> int:
        """Returns: the priority of the limit operator."""
        return 60

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        if self.tokens <= 0.0:
            return

        sleep_func: Callable[[float], None] = time.sleep
        if self.sleep_func is not None:
            sleep_func = self.sleep_func  # type: ignore[assignment]
        operator = LimitOperator[T](self.tokens, sleep_func)
        descriptor.register_operator(self.priority, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        if self.tokens <= 0.0:
            return

        sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep
        if self.sleep_func is not None:
            sleep_func = self.sleep_func  # type: ignore[assignment]
        operator = AsyncLimitOperator[T](self.tokens, sleep_func)
        descriptor.register_operator(self.priority, operator)


limit = LimitOption


class LimitOperator(Generic[T]):
    """Delays the endpoint calls that exceed the rate limit."""

    def __init__(self, tokens: Tokens, sleep_func: Callable[[Duration], None]) -> None:
        """Creates a new limit operator.

        Args:
            tokens: number of tokens consumed by the endpoint call
            sleep_func: the sleep function to use (default: time.sleep).
        """
        self.tokens = tokens
        self.sleep_func = sleep_func

    def __call__(self, ctx: Context[T]) -> T:
        current_time = time.monotonic()
        reservation = ctx.client.limiter.reserve_at(current_time, self.tokens)
        delay = reservation.ready_at - current_time
        if delay > 0:
            self.sleep_func(delay)

        return ctx.proceed()


class AsyncLimitOperator(Generic[T]):
    """Delays the endpoint calls that exceed the rate limit."""

    def __init__(self, tokens: Tokens, sleep_func: Callable[[Duration], Awaitable[None]]) -> None:
        """Creates a new limit operator.

        Args:
            tokens: number of tokens consumed by the endpoint call
            sleep_func: the sleep function to use (default: asyncio.sleep).
        """
        self.tokens = tokens
        self.sleep_func = sleep_func

    async def __call__(self, ctx: AsyncContext[T]) -> T:
        current_time = time.monotonic()
        reservation = ctx.client.limiter.reserve_at(current_time, self.tokens)
        delay = reservation.ready_at - current_time
        if delay > 0:
            await self.sleep_func(delay)

        return await ctx.proceed()
