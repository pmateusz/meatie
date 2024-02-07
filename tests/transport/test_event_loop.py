#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio

import pytest
from asyncio import Runner


def test_event_loop():
    next_number = 0

    async def task() -> int:
        nonlocal next_number
        result = next_number
        next_number += 1
        return result

    with Runner() as runner:
        result_1 = runner.run(task())
        result_2 = runner.run(task())

    assert result_1 == 0
    assert result_2 == 1


@pytest.mark.asyncio()
async def test_event_loop():
    next_number = 0

    async def task() -> int:
        nonlocal next_number
        result = next_number
        next_number += 1
        return result

    with Runner() as runner:
        result_1 = runner.run(task())
        result_2 = runner.run(task())

    assert result_1 == 0
    assert result_2 == 1
