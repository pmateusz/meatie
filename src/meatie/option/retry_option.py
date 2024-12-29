#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import time
from http import HTTPStatus
from typing import Awaitable, Callable, Optional, Union

from meatie import (
    Condition,
    Context,
    Duration,
    EndpointDescriptor,
    RetryContext,
    RetryError,
    has_status,
    never,
    zero,
)
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.retry import WaitFunc
from meatie.internal.types import PT, T

__all__ = ["retry"]


class RetryOption:
    __PRIORITY = 40

    def __init__(
        self,
        on: Condition = has_status(HTTPStatus.TOO_MANY_REQUESTS),
        wait: WaitFunc = zero,
        stop: Condition = never,
        sleep_func: Union[
            Callable[[Duration], None], Callable[[Duration], Awaitable[None]], None
        ] = None,
    ) -> None:
        """
        :param on: function that returns True if the operation should be retried. Default behaviour is to retry on the HTTP Too Many Requests (429) status code.
        :param wait: function that returns the duration to wait before the next retry attempt. Default behaviour is to don't wait.
        :param stop: function that returns True if the operation should be aborted. Default behaviour is never to stop.
        :param sleep_func: the sleep function to use. Default behaviour is to rely on the Python standard library functions: time.sleep and asyncio.sleep for async functions.

        See also:
            meatie.has_status - retry on a specific status code
            meatie.has_exception_type - retry on a specific exception type
            meatie.has_exception_cause_type - retry if a specific exception type is present in the exception chain
            meatie.zero - don't wait
            meatie.fixed - wait a fixed amount of seconds
            meatie.uniform - wait a random amount of seconds in the given time range
            meatie.exponential - keep increasing the wait time exponentially
            meatie.jitter - add a random jitter to the wait time
            meatie.never - never stop
            meatie.after - stop after deadline in seconds
            meatie.after_attempt - stop after a number of attempts
        """

        self.__on = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        sleep_func: Union[Callable[[float], None], None] = self.__sleep_func  # type: ignore[assignment]
        if sleep_func is None:
            sleep_func = time.sleep

        operator = RetryOperator(self.__on, self.__wait, self.__stop, sleep_func)
        descriptor.register_operator(RetryOption.__PRIORITY, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        sleep_func: Union[Callable[[float], Awaitable[None]], None] = self.__sleep_func  # type: ignore[assignment]
        if sleep_func is None:
            sleep_func = asyncio.sleep

        operator = AsyncRetryOperator(self.__on, self.__wait, self.__stop, sleep_func)
        descriptor.register_operator(RetryOption.__PRIORITY, operator)


retry = RetryOption


class RetryOperator:
    def __init__(
        self,
        on: Condition,
        wait: WaitFunc,
        stop: Condition,
        sleep_func: Callable[[Duration], None],
    ) -> None:
        self.__condition = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(self, operation_ctx: Context[T]) -> T:
        retry_ctx = RetryContext(attempt_number=1, started_at=time.monotonic())
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            retry_ctx.error = None
            retry_ctx.response = None
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    self.__sleep_func(wait_time)

            try:
                last_result = operation_ctx.proceed()
                retry_ctx.response = operation_ctx.response
            except BaseException as exc:
                retry_ctx.error = exc

            if not self.__condition(retry_ctx):
                break

            retry_ctx.attempt_number += 1
            stopped = self.__stop(retry_ctx)

        if not stopped and last_result is not None:
            return last_result

        if retry_ctx.error is not None:
            raise retry_ctx.error
        raise RetryError()


class AsyncRetryOperator:
    def __init__(
        self,
        on: Condition,
        wait: WaitFunc,
        stop: Condition,
        sleep_func: Callable[[Duration], Awaitable[None]],
    ) -> None:
        self.__condition = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    async def __call__(self, operation_ctx: AsyncContext[T]) -> T:
        retry_ctx = RetryContext(attempt_number=1, started_at=time.monotonic())
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            retry_ctx.error = None
            retry_ctx.response = None
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    await self.__sleep_func(wait_time)

            try:
                last_result = await operation_ctx.proceed()
                retry_ctx.response = operation_ctx.response
            except BaseException as exc:
                retry_ctx.error = exc

            if not self.__condition(retry_ctx):
                break

            retry_ctx.attempt_number += 1
            stopped = self.__stop(retry_ctx)

        if not stopped and last_result is not None:
            return last_result

        if retry_ctx.error is not None:
            raise retry_ctx.error
        raise RetryError()
