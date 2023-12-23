#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import asyncio
import time as sys_time
from typing import Awaitable, Callable

from meatie.aio import Client, Context
from meatie.aio.internal import EndpointDescriptor
from meatie.internal.limit import Tokens
from meatie.internal.types import PT, T


class LimitOption:
    __PRIORITY = 80

    def __init__(
        self, tokens: Tokens, sleep_func: Callable[[Tokens], Awaitable[None]] = asyncio.sleep
    ) -> None:
        self.tokens = tokens
        self.sleep_func = sleep_func

    def __call__(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        if self.tokens > 0.0:
            descriptor.register_operator(LimitOption.__PRIORITY, self.__operator)

    async def __operator(self, ctx: Context[Client, T]) -> T:
        current_time = sys_time.monotonic()
        reservation = ctx.client.limiter.reserve_at(current_time, self.tokens)
        delay = reservation.ready_at - current_time
        if delay > 0:
            await self.sleep_func(delay)

        return await ctx.proceed()
