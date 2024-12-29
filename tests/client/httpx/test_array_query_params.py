from dataclasses import dataclass
from typing import Annotated, Optional

import httpx
from http_test import HTTPTestServer
from http_test.handlers import companies_filter_by_sector
from meatie import api_ref, endpoint
from meatie_httpx import Client


def test_handles_array_query_params(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = companies_filter_by_sector

    @dataclass(slots=True)
    class Company:
        name: str
        sector: str

    class TestClient(Client):
        @endpoint("/")
        def get_companies(
            self, sectors: Annotated[Optional[list[str]], api_ref(name="sector")] = None
        ) -> list[Company]:
            ...

    # WHEN
    with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
        companies = client.get_companies(sectors=["Information Technology", "Financials"])

    # THEN
    assert len(companies) > 0
    assert all(company.sector in ["Information Technology", "Financials"] for company in companies)
