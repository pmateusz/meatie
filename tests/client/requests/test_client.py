from http import HTTPStatus

from http_test import Handler, HTTPTestServer
from requests import Session

from meatie import endpoint
from meatie_requests import Client


def test_use_prefix(http_server: HTTPTestServer) -> None:
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
        def get_status(self) -> str: ...

    # WHEN
    with PrefixClient(Session(), prefix=http_server.base_url + "/api/v1/") as client:
        status = client.get_status()

    # THEN
    assert status == "ok"
