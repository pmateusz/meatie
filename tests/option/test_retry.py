#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from unittest.mock import Mock

from meatie import Context, has_exception_type, never, zero
from meatie.option.retry_option import RetryOperator


def test_exception_is_reset() -> None:
    # GIVEN
    successful_response = Mock()
    operator = RetryOperator(
        on=has_exception_type(RuntimeError), wait=zero, stop=never, sleep_func=Mock()
    )
    ctx = Mock(spec=Context)
    call_count = 0

    def on_proceed() -> Mock:
        nonlocal call_count

        call_count += 1
        if call_count == 1:
            raise RuntimeError()

        ctx.response = successful_response
        return ctx.response

    ctx.proceed = Mock(side_effect=on_proceed)

    # WHEN
    response = operator(ctx)

    # THEN
    assert ctx.proceed.call_count == 2
    assert response is successful_response
