#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from typing import Union

from ... import ResponseError
from . import BaseCondition, RetryContext

__all__ = ["always", "has_status", "has_exception_type", "has_exception_cause_type"]


class RetryAlways(BaseCondition):
    def __call__(self, ctx: RetryContext) -> bool:
        return True


class RetryOnStatus(BaseCondition):
    def __init__(self, status: int) -> None:
        self.status = status

    def __call__(self, ctx: RetryContext) -> bool:
        if ctx.response is not None:
            return ctx.response.status == self.status

        if isinstance(ctx.error, ResponseError):
            return ctx.error.response.status == self.status

        return False


class RetryOnExceptionType(BaseCondition):
    def __init__(
        self, exc_types: Union[type[BaseException], tuple[type[BaseException], ...]]
    ) -> None:
        self.exc_types = exc_types

    def __call__(self, ctx: RetryContext) -> bool:
        return isinstance(ctx.error, self.exc_types)


class RetryOnExceptionCauseType(BaseCondition):
    def __init__(
        self, exc_types: Union[type[BaseException], tuple[type[BaseException], ...]]
    ) -> None:
        self.exc_types = exc_types

    def __call__(self, ctx: RetryContext) -> bool:
        exc = ctx.error
        while exc is not None:
            if isinstance(exc, self.exc_types):
                return True
            exc = exc.__cause__
        return False


always = RetryAlways()
has_status = RetryOnStatus
has_exception_type = RetryOnExceptionType
has_exception_cause_type = RetryOnExceptionCauseType
