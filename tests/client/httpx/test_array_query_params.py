#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Annotated, Optional

import httpx
import pytest
from http_test import HTTPTestServer
from http_test.handlers import companies_filter_by_sector

from meatie import api_ref, endpoint
from meatie_httpx import Client

pytest.importorskip("pydantic")


def test_handles_array_query_params(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = companies_filter_by_sector

    @dataclass
    class Company:
        name: str
        sector: str

    class TestClient(Client):
        @endpoint("/")
        def get_companies(
            self, sectors: Annotated[Optional[list[str]], api_ref(name="sector")] = None
        ) -> list[Company]: ...

    # WHEN
    with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
        companies = client.get_companies(sectors=["Information Technology", "Financials"])

    # THEN
    assert companies == [
        Company(name="Apple", sector="Information Technology"),
        Company(name="Berkshire Hathaway", sector="Financials"),
    ]
