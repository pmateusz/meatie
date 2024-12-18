#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import httpx
import pytest
from http_test import HTTPTestServer
from http_test.handlers import service_unavailable
from meatie import HttpStatusError, Response, ResponseError, body, endpoint
from meatie_httpx import Client


def get_error(response: Response) -> Exception | None:
    exc_type = HttpStatusError if response.status >= 300 else ResponseError

    body = response.json()
    if isinstance(body, dict):
        error = body.get("error")
        if error is not None:
            return exc_type(response, error)

    if response.status >= 300:
        return exc_type(response)

    return None


def test_raises_error(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = service_unavailable

    class TestClient(Client):
        @endpoint("/", body(error=get_error))
        def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(HttpStatusError) as exc_info:
        with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
            client.get_response()

    # THEN
    assert exc_info.value.args == ("deployment in progress",)
