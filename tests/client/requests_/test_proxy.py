#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from typing import Generator

import pytest
import requests
from meatie_requests.client import RequestsClient
from suite.client import ProxyErrorSuite


class TestRequestsProxyErrorSuite(ProxyErrorSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(
            requests.Session(),
            session_params={
                "proxies": {
                    "http": "http://localhost:3128",
                }
            },
        ) as client:
            yield client
