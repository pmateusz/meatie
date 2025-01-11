#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from typing import Generator

import httpx
import pytest
from http_test import ClientAdapter
from meatie_httpx import AsyncClient
from suite.client import TimeoutSuite


class TestHttpxTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(
        self,
        event_loop: asyncio.AbstractEventLoop,
    ) -> Generator[ClientAdapter, None, None]:
        with ClientAdapter(
            event_loop, AsyncClient(httpx.AsyncClient(), client_params={"timeout": 0.005})
        ) as client:
            yield client
