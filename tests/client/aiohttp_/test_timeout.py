#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from typing import Callable, Generator

import aiohttp
import pytest
from http_test import ClientAdapter
from meatie_aiohttp import Client
from suite.client import TimeoutSuite


class TestAiohttpTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(
        self,
        event_loop: asyncio.AbstractEventLoop,
        create_client_session: Callable[..., aiohttp.ClientSession],
    ) -> Generator[ClientAdapter, None, None]:
        with ClientAdapter(
            event_loop,
            Client(create_client_session(timeout=aiohttp.ClientTimeout(total=0.005))),
        ) as client:
            yield client
