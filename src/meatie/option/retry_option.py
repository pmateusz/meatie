#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import time
from http import HTTPStatus
from typing import Optional

from meatie import (
    Condition,
    Context,
    EndpointDescriptor,
    RateLimitExceeded,
    RetryContext,
    has_status,
    never,
    zero,
)
from meatie.internal.retry import WaitFunc
from meatie.internal.types import PT, T

__all__ = ["retry"]


class RetryOption:
    __PRIORITY = 75

    def __init__(
        self,
        on: Condition = has_status(HTTPStatus.TOO_MANY_REQUESTS),
        wait: WaitFunc = zero,
        stop: Condition = never,
    ) -> None:
        self.__on = on
        self.__wait = wait
        self.__stop = stop

    def __call__(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(RetryOption.__PRIORITY, self.__operator)

    def __operator(self, operation_ctx: Context[T]) -> T:
        retry_ctx = RetryContext(
            attempt_number=1, started_at=time.monotonic(), error=None, response=None
        )
        last_result: Optional[T] = None
        stopped = False
        while not stopped:
            if retry_ctx.attempt_number > 1:
                wait_time = self.__wait(retry_ctx)
                if wait_time > 0.0:
                    time.sleep(wait_time)

            try:
                last_result = operation_ctx.proceed()
                retry_ctx.response = operation_ctx.response
            except BaseException as exc:
                retry_ctx.error = exc

            if not self.__on(retry_ctx):
                break

            retry_ctx.attempt_number += 1
            stopped = self.__stop(retry_ctx)

        if not stopped and last_result is not None:
            return last_result

        if retry_ctx.error is not None:
            raise retry_ctx.error
        raise RateLimitExceeded()


retry = RetryOption
