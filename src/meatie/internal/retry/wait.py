#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import abc
import random
from abc import abstractmethod
from typing import Callable

from meatie.types import HOUR, Duration

from .context import RetryContext

__all__ = ["zero", "uniform", "jit", "exponential", "fixed", "WaitFunc"]

WaitFunc = Callable[[RetryContext], Duration]


class BaseWait(abc.ABC):
    @abstractmethod
    def __call__(self, ctx: RetryContext) -> Duration:
        raise NotImplementedError()

    def __add__(self, other: WaitFunc) -> "BaseWait":
        return WaitSum(self, other)


class WaitSum(BaseWait):
    def __init__(self, *waits: WaitFunc) -> None:
        self.waits = waits

    def __call__(self, ctx: RetryContext) -> Duration:
        return sum(wait(ctx) for wait in self.waits)


class WaitZero(BaseWait):
    def __call__(self, ctx: RetryContext) -> Duration:
        return 0.0


class WaitExponential(BaseWait):
    def __init__(
        self,
        exp_base: float = 2.0,
        multiplier: float = 2.0,
        lb: float = 0.0,
        ub: float = HOUR,
    ) -> None:
        self.exp_base = exp_base
        self.multiplier = multiplier
        self.lb = max(lb, 0.0)
        self.ub = ub

    def __call__(self, ctx: RetryContext) -> Duration:
        try:
            result = self.multiplier * self.exp_base ** (ctx.attempt_number - 1)
        except OverflowError:
            return self.ub
        return max(self.lb, min(result, self.ub))


class WaitFixed(BaseWait):
    def __init__(self, delay: Duration, *other_delays: Duration) -> None:
        self.__delays: list[Duration] = [delay]
        self.__delays.extend(other_delays)

    def __call__(self, ctx: RetryContext) -> Duration:
        step = min(ctx.attempt_number, len(self.__delays)) - 1
        return self.__delays[step]


class WaitUniform(BaseWait):
    def __init__(self, lb: Duration, ub: Duration) -> None:
        self.lb = lb
        self.ub = ub

    def __call__(self, ctx: RetryContext) -> Duration:
        return random.uniform(self.lb, self.ub)


class WaitJit(WaitUniform):
    def __init__(self, ub: Duration) -> None:
        super().__init__(0.0, ub)


zero: WaitFunc = WaitZero()
uniform = WaitUniform
jit = WaitJit
exponential = WaitExponential
fixed = WaitFixed
