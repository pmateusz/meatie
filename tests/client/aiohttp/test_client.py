from http import HTTPStatus

import pytest
from aiohttp import ClientSession
from http_test import Handler, HTTPTestServer
from meatie import endpoint
from meatie_aiohttp import Client


@pytest.mark.asyncio()
async def test_use_prefix(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(h: Handler) -> None:
        if h.path == "/api/v1/status":
            status_code, message = HTTPStatus.OK, "ok"
        else:
            status_code, message = HTTPStatus.NOT_FOUND, "resource not found"
        h.send_json(status_code, message)

    http_server.handler = handler

    class PrefixClient(Client):
        @endpoint("status")
        async def get_status(self) -> str:
            ...

    # WHEN
    async with PrefixClient(
        ClientSession(base_url=http_server.base_url, raise_for_status=True), prefix="/api/v1/"
    ) as client:
        status = await client.get_status()

    # THEN
    assert status == "ok"
