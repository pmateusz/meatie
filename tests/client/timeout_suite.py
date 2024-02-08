#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import time
from http import HTTPStatus

import pytest
from http_test import (
    Handler,
    HTTPTestServer,
)
from meatie import (
    Request,
    Timeout,
)
from meatie.internal.types import Client


class TimeoutSuite:
    @staticmethod
    def test_can_handle_timeout(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        def timeout_handler(handler: Handler) -> None:
            time.sleep(0.01)
            handler.send_response(HTTPStatus.OK)

        http_server.handler = timeout_handler
        request = Request("GET", http_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(Timeout) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None
