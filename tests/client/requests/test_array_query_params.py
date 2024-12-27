from dataclasses import dataclass
from typing import Annotated, Optional

import requests
from http_test import HTTPTestServer
from http_test.handlers import companies_filter_by_sector
from meatie import api_ref, endpoint
from meatie_requests import Client


def test_send_array_query_params(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = companies_filter_by_sector

    @dataclass(slots=True)
    class Company:
        name: str
        sector: str

    class TestClient(Client):
        @endpoint(http_server.base_url + "/")
        def get_companies(
            self, sectors: Annotated[Optional[list[str]], api_ref(name="sector")] = None
        ) -> list[Company]:
            ...

    # WHEN
    with TestClient(requests.Session()) as client:
        companies = client.get_companies(sectors=["Information Technology", "Financials"])

    # THEN
    assert companies == [
        Company(name="Apple", sector="Information Technology"),
        Company(name="Berkshire Hathaway", sector="Financials"),
    ]