#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Generator

import pytest
import requests

from tests.client.default_suite import DefaultSuite
from meatie_requests.client import RequestsClient


class TestRequestsDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(requests.Session()) as client:
            yield client
