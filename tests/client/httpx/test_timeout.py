#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import platform
from typing import Generator

import httpx
import pytest
from suite.client import TimeoutSuite

from meatie_httpx import Client


class TestHttpxTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[Client, None, None]:
        with Client(httpx.Client(), client_params={"timeout": 0.005}) as client:
            yield client

    @pytest.mark.xfail(platform.system() == "Windows", reason="The test seems to rely on Unix-specific behavior.")
    def test_can_handle_timeout(self, http_server, client):
        TimeoutSuite.test_can_handle_timeout(http_server, client)
