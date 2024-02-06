#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import pytest
from meatie.internal.limit import Limiter, Rate
from meatie.internal.types import INF


def test_inf_rate_limit_is_not_blocking() -> None:
    # GIVEN
    current_time = 1000
    tokens = 1_000_000
    limiter = Limiter(Rate.max, INF, current_time, 0)

    # WHEN
    reservation = limiter.reserve_at(current_time, tokens)

    # THEN
    assert reservation.ready_at == current_time
    assert reservation.tokens == tokens


def test_cannot_reserve_over_limit() -> None:
    # GIVEN
    current_time = 1000
    limiter = Limiter(Rate.max, 0, current_time, 0)

    # WHEN
    with pytest.raises(ValueError) as exc_info:
        limiter.reserve_at(current_time, 1)

    # THEN
    assert "amount of requested tokens (1) exceed the limit (0)" == str(exc_info.value)


def test_can_reserve_immediately_if_possible() -> None:
    # GIVEN
    current_time = 1000
    tokens = 10
    limit = 60
    limiter = Limiter(Rate(1), limit, current_time, limit)

    # WHEN
    reservation = limiter.reserve_at(current_time, tokens)

    # THEN
    assert reservation.ready_at == current_time
    assert reservation.tokens == tokens


def test_can_reserve_for_future() -> None:
    # GIVEN
    current_time = 1000
    tokens = 10
    limit = 60
    limiter = Limiter(Rate(1), limit, 0, current_time)

    # WHEN
    reservation = limiter.reserve_at(current_time, tokens)

    # THEN
    assert reservation.ready_at == 1010
    assert reservation.tokens == tokens
