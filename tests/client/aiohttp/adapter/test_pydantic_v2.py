#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Annotated, Any, Optional

import pytest
from aiohttp import ClientSession
from http_test import HTTPTestServer
from meatie import AsyncResponse, api_ref, endpoint
from meatie_aiohttp import Client

pydantic = pytest.importorskip("pydantic", minversion="2.0.0")
BaseModel: type = pydantic.BaseModel


@pytest.mark.asyncio()
async def test_post_request_body_with_fmt(http_server: HTTPTestServer) -> None:
    # GIVEN
    class Request(pydantic.BaseModel):
        data: Optional[dict[str, Any]]

    def handler(request: BaseHTTPRequestHandler) -> None:
        content_length = request.headers.get("Content-Length", "0")
        raw_body = request.rfile.read(int(content_length))
        body = json.loads(raw_body.decode("utf-8"))

        if body.get("data") is not None:
            request.send_response(HTTPStatus.BAD_REQUEST)
        else:
            request.send_response(HTTPStatus.OK)
        request.end_headers()

    http_server.handler = handler

    def dump_body(model: pydantic.BaseModel) -> str:
        return model.model_dump_json(by_alias=True, exclude_none=True)

    class TestClient(Client):
        @endpoint("/")
        async def post_request(self, body: Annotated[Request, api_ref(fmt=dump_body)]) -> AsyncResponse:
            ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.post_request(Request(data=None))

    # THEN
    assert response.status == HTTPStatus.OK
