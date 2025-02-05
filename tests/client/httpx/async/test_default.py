#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from typing import Generator

import httpx
import pytest
from http_test import ClientAdapter
from suite.client import DefaultSuite

from meatie_httpx import AsyncClient


class TestAsyncHttpxDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(
        self,
        event_loop: asyncio.AbstractEventLoop,
    ) -> Generator[ClientAdapter, None, None]:
        with ClientAdapter(event_loop, AsyncClient(httpx.AsyncClient())) as client:
            yield client
