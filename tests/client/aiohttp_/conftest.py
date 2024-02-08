#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from asyncio import AbstractEventLoop
from typing import Any, Callable

import aiohttp
import pytest

from tests.client.aiohttp_.mock_tools import MockTools


@pytest.fixture(name="mock_tools", scope="session")
def mock_tools_fixture() -> MockTools:
    return MockTools()


@pytest.fixture(name="create_client_session")
def create_client_session_fixture(
    event_loop: AbstractEventLoop,
) -> Callable[..., aiohttp.ClientSession]:
    def create_client_session(*args: Any, **kwargs: Any) -> aiohttp.ClientSession:
        return event_loop.run_until_complete(_create_client_session(*args, **kwargs))

    return create_client_session


async def _create_client_session(*args: Any, **kwargs: Any) -> aiohttp.ClientSession:
    return aiohttp.ClientSession(*args, **kwargs)
