#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from typing import Callable, Generator

import aiohttp
import pytest
from http_test import ClientAdapter
from suite.client import DefaultSuite

from meatie_aiohttp import Client as AiohttpClient


class TestAiohttpDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(
        self,
        event_loop: asyncio.AbstractEventLoop,
        create_client_session: Callable[..., aiohttp.ClientSession],
    ) -> Generator[ClientAdapter, None, None]:
        with ClientAdapter(event_loop, AiohttpClient(create_client_session())) as client:
            yield client
