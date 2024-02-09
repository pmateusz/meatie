#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import time

from . import BaseCondition, Condition, RetryContext

__all__ = ["after", "after_attempt", "never"]

from meatie import Duration


class StopAfterAttempt(BaseCondition):
    def __init__(self, attempts: int) -> None:
        self.attempts = attempts

    def __call__(self, ctx: RetryContext) -> bool:
        return ctx.attempt_number > self.attempts


class StopAfter(BaseCondition):
    def __init__(self, max_delay: Duration) -> None:
        self.max_delay = max_delay

    def __call__(self, ctx: RetryContext) -> bool:
        elapsed_time = time.monotonic() - ctx.started_at
        return elapsed_time > self.max_delay


class StopNever(BaseCondition):
    def __call__(self, ctx: RetryContext) -> bool:
        return False


never: Condition = StopNever()
after_attempt = StopAfterAttempt
after = StopAfter
