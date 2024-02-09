#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import abc
from typing import Callable

from .context import RetryContext

Condition = Callable[[RetryContext], bool]


class BaseCondition:
    @abc.abstractmethod
    def __call__(self, ctx: RetryContext) -> bool:
        pass

    def __and__(self, other: Condition) -> Condition:
        return AndCondition(self, other)

    def __or__(self, other: Condition) -> Condition:
        return OrCondition(self, other)


class AndCondition(BaseCondition):
    def __init__(self, left: Condition, right: Condition) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: RetryContext) -> bool:
        return self._left(ctx) and self._right(ctx)


class OrCondition(BaseCondition):
    def __init__(self, left: Condition, right: Condition) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: RetryContext) -> bool:
        return self._left(ctx) or self._right(ctx)
