#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Generator

import httpx
import pytest

from meatie_httpx import HttpxClient
from tests.client.timeout_suite import TimeoutSuite


class TestHttpxTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client(), client_params={"timeout": 0.005}) as client:
            yield client
