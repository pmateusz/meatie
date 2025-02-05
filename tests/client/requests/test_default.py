#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Generator

import pytest
import requests
from suite.client import DefaultSuite

from meatie_requests.client import Client


class TestRequestsDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[Client, None, None]:
        with Client(requests.Session()) as client:
            yield client
