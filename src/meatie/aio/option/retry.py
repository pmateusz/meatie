#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import asyncio
import time
from http import HTTPStatus
from typing import Awaitable, Callable, Optional

from meatie import (
    Condition,
    Duration,
    RetryContext,
    RetryError,
    has_status,
    never,
    zero,
)
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.retry import WaitFunc
from meatie.internal.types import PT, T


class RetryOption:
    __PRIORITY = 75

    def __init__(
        self,
        retry: Condition = has_status(HTTPStatus.TOO_MANY_REQUESTS),
        wait: WaitFunc = zero,
        stop: Condition = never,
        sleep_func: Callable[[Duration], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.__retry = retry
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(RetryOption.__PRIORITY, self.__operator)

    async def __operator(self, operation_ctx: AsyncContext[T]) -> T:
        retry_ctx = RetryContext(attempt_number=1, started_at=time.monotonic())
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    await self.__sleep_func(wait_time)

            try:
                last_result = await operation_ctx.proceed()
                retry_ctx.response = operation_ctx.response
            except Exception as exc:
                retry_ctx.error = exc

            if not self.__retry(retry_ctx):
                break

            retry_ctx.attempt_number += 1
            stopped = self.__stop(retry_ctx)

        if not stopped and last_result is not None:
            return last_result

        if retry_ctx.error is not None:
            raise retry_ctx.error
        raise RetryError()
