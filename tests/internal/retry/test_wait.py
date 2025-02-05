#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Callable

import pytest

from meatie import Duration, exponential, fixed, jit, uniform, zero
from meatie.internal.retry import RetryContext


def poll(wait: Callable[[RetryContext], Duration], length: int) -> list[Duration]:
    result = []
    ctx = RetryContext(attempt_number=1, started_at=0.0)
    for _ in range(length):
        delay = wait(ctx)
        result.append(delay)
        ctx.attempt_number += 1
    return result


def test_wait_exponential() -> None:
    # GIVEN
    wait = exponential(ub=16.0)

    # WHEN
    series = poll(wait, 5)

    # THEN
    assert series == [2.0, 4.0, 8.0, 16.0, 16.0]


def test_wait_uniform() -> None:
    # GIVEN
    lb, ub = 1.0, 5.0
    wait = uniform(lb=lb, ub=ub)

    # WHEN
    series = poll(wait, 5)

    # THEN
    for delay in series:
        assert lb <= delay <= ub


@pytest.mark.parametrize("duration", [1.0, 1])
def test_wait_fixed_one(duration) -> None:
    # GIVEN
    wait = fixed(duration)

    # WHEN
    series = poll(wait, 2)

    # THEN
    assert series == [1.0, 1.0]


def test_wait_fixed_args() -> None:
    # GIVEN
    wait = fixed(1.0, 2.0)

    # WHEN
    series = poll(wait, 3)

    # THEN
    assert series == [1.0, 2.0, 2.0]


def test_sum() -> None:
    # GIVEN
    lb = 5
    delta = 5
    ub = lb + delta
    wait = fixed(lb) + jit(delta) + zero

    # WHEN
    series = poll(wait, 5)

    # THEN
    for delay in series:
        assert lb <= delay <= ub
