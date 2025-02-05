#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import pytest
from http_test import HTTPTestServer

from meatie import ProxyError, Request
from meatie.internal.types import Client


class ProxyErrorSuite:
    @staticmethod
    def test_can_handle_proxy_error(client: Client, http_server: HTTPTestServer) -> None:
        # GIVEN
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        with pytest.raises(ProxyError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None
