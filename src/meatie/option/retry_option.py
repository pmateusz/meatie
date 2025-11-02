#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import time
from http import HTTPStatus
from typing import Awaitable, Callable, Generic, Optional, Union

from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.descriptor import Context, EndpointDescriptor
from meatie.error import RetryError
from meatie.internal.retry import Condition, RetryContext, WaitFunc, has_status, never, zero
from meatie.internal.types import PT, T
from meatie.types import Duration

__all__ = ["RetryOption"]


class RetryOption:
    """Configure the strategy for retrying the endpoint calls that failed."""

    def __init__(
        self,
        on: Condition = has_status(HTTPStatus.TOO_MANY_REQUESTS),
        wait: WaitFunc = zero,
        stop: Condition = never,
        sleep_func: Union[Callable[[Duration], None], Callable[[Duration], Awaitable[None]], None] = None,
    ) -> None:
        """Creates a new retry option.

        Parameters:
            on: function that returns True if the operation should be retried. Default behaviour is to retry on the HTTP Too Many Requests (429) status code.
            wait: function that returns the duration to wait before the next retry attempt. Default behaviour is no to wait.
            stop: function that returns True if the operation should be aborted. Default behaviour is never to stop.
            sleep_func: the sleep function to use. Default behaviour is to rely on the Python standard library functions: time.sleep and asyncio.sleep for async functions.

        See Also:
            meatie.has_status: retry on a specific HTTP status code
            meatie.has_exception_type: retry on a specific exception type
            meatie.has_exception_cause_type: retry if a specific exception type is present in the exception chain
            meatie.zero: do not wait
            meatie.fixed: wait a fixed amount of seconds
            meatie.uniform: wait a random amount of seconds in the given time range
            meatie.exponential: keep increasing the wait time exponentially
            meatie.jitter: add a random jitter to the wait time
            meatie.never: never stop
            meatie.after: stop after deadline in seconds
            meatie.after_attempt: stop after a number of attempts
        """
        self.__on = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(
        self,
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]],
    ) -> None:
        """Apply the retry option to the endpoint descriptor."""
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    @property
    def priority(self) -> int:
        """Returns: the priority of the retry operator."""
        return 40

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        sleep_func: Union[Callable[[float], None], None] = self.__sleep_func  # type: ignore[assignment]
        if sleep_func is None:
            sleep_func = time.sleep

        operator = RetryOperator[T](self.__on, self.__wait, self.__stop, sleep_func)
        descriptor.register_operator(self.priority, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        sleep_func: Union[Callable[[float], Awaitable[None]], None] = self.__sleep_func  # type: ignore[assignment]
        if sleep_func is None:
            sleep_func = asyncio.sleep

        operator = AsyncRetryOperator[T](self.__on, self.__wait, self.__stop, sleep_func)
        descriptor.register_operator(self.priority, operator)


retry = RetryOption


class RetryOperator(Generic[T]):
    """Executes the retry strategy for synchronous endpoint calls."""

    def __init__(
        self,
        on: Condition,
        wait: WaitFunc,
        stop: Condition,
        sleep_func: Callable[[Duration], None],
    ) -> None:
        """Creates a new retry operator.

        Args:
            on: function that returns True if the operation should be retried.
            wait: function that returns the duration to wait before the next retry attempt.
            stop: function that returns True if the operation should be aborted.
            sleep_func: the sleep function to use.
        """
        self.__condition = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    def __call__(self, operation_ctx: Context[T]) -> T:
        retry_ctx = RetryContext(attempt_number=1, started_at=time.monotonic())
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    self.__sleep_func(wait_time)

            retry_ctx.error = None
            retry_ctx.response = None
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


class AsyncRetryOperator(Generic[T]):
    """Executes the retry strategy for asynchronous endpoint calls."""

    def __init__(
        self,
        on: Condition,
        wait: WaitFunc,
        stop: Condition,
        sleep_func: Callable[[Duration], Awaitable[None]],
    ) -> None:
        """Creates a new retry operator.

        Args:
            on: function that returns True if the operation should be retried.
            wait: function that returns the duration to wait before the next retry attempt.
            stop: function that returns True if the operation should be aborted.
            sleep_func: the sleep function to use.
        """
        self.__condition = on
        self.__wait = wait
        self.__stop = stop
        self.__sleep_func = sleep_func

    async def __call__(self, operation_ctx: AsyncContext[T]) -> T:
        retry_ctx = RetryContext(attempt_number=1, started_at=time.monotonic())
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    await self.__sleep_func(wait_time)

            retry_ctx.error = None
            retry_ctx.response = None
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
