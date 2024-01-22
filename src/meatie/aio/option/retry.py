#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import abc
import asyncio
import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import Awaitable, Callable, Optional

import aiohttp

from meatie.aio import (
    Client,
    Context,
    Duration,
    RateLimitExceeded,
    Response,
)
from meatie.aio.internal import EndpointDescriptor
from meatie.internal.types import PT, T


@dataclass()
class RetryContext:
    attempt_number: int
    started_at: float
    error: Optional[Exception]
    response: Optional[Response]


class _BaseCondition:
    @abc.abstractmethod
    def __call__(self, ctx: RetryContext) -> bool:
        pass

    def __and__(self, other: "_BaseCondition") -> "_BaseCondition":
        return _AndCondition(self, other)

    def __or__(self, other: "_BaseCondition") -> "_BaseCondition":
        return _OrCondition(self, other)


class _AndCondition(_BaseCondition):
    def __init__(self, left: _BaseCondition, right: _BaseCondition) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: RetryContext) -> bool:
        return self._left(ctx) and self._right(ctx)


class _OrCondition(_BaseCondition):
    def __init__(self, left: _BaseCondition, right: _BaseCondition) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: RetryContext) -> bool:
        return self._left(ctx) or self._right(ctx)


def _no_wait(_: RetryContext) -> float:
    return 0.0


class RetryOnStatusCode(_BaseCondition):
    def __init__(self, status: int) -> None:
        self.status = status

    def __call__(self, ctx: RetryContext) -> bool:
        if ctx.response is not None:
            return ctx.response.status == self.status

        if isinstance(ctx.error, aiohttp.ClientResponseError):
            return ctx.error.status == self.status

        return False


class RetryOnExceptionType(_BaseCondition):
    def __init__(self, exc_type: type[BaseException]) -> None:
        self.exc_type = exc_type

    def __call__(self, ctx: RetryContext) -> bool:
        return isinstance(ctx.error, self.exc_type)


RetryOnServerConnectionError = RetryOnExceptionType(aiohttp.ServerConnectionError)
RetryOnTooManyRequestsStatus = RetryOnStatusCode(HTTPStatus.TOO_MANY_REQUESTS)
NoWait = _no_wait


class WaitExponential(_BaseCondition):
    def __init__(self, multiplier: int = 2, lower_bound: int = 1, upper_bound: int = 3600) -> None:
        self._multiplier = multiplier
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def __call__(self, ctx: RetryContext) -> bool:
        return max(min(self._multiplier**ctx.attempt_number, self._upper_bound), self._lower_bound)


def _never_stop(ctx: RetryContext) -> bool:
    return False


class StopAfter:
    def __init__(self, attempts: int) -> None:
        self.attempts = attempts

    def __call__(self, ctx: RetryContext) -> bool:
        return ctx.attempt_number > self.attempts


NeverStop = _never_stop

StopCondition = Callable[[RetryContext], bool]
RetryCondition = Callable[[RetryContext], bool]
WaitFunc = Callable[[RetryContext], float]


class RetryOption:
    __PRIORITY = 75

    def __init__(
        self,
        retry: RetryCondition = (RetryOnTooManyRequestsStatus | RetryOnServerConnectionError),
        wait: WaitFunc = NoWait,
        stop: StopCondition = NeverStop,
        sleep_func: Callable[[Duration], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.__retry = retry
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(RetryOption.__PRIORITY, self.__operator)

    async def __operator(self, operation_ctx: Context[Client, T]) -> T:
        retry_ctx = RetryContext(
            attempt_number=1, started_at=time.monotonic(), error=None, response=None
        )
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
        raise RateLimitExceeded()
