#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Generator

import httpx
import pytest

from tests.client.default_suite import DefaultSuite
from meatie_httpx import HttpxClient


class TestHttpxDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client()) as client:
            yield client
