from typing import Generator

import pytest
from http_test import HTTPTestServer

aiohttp = pytest.importorskip("aiohttp")
pydantic = pytest.importorskip("pydantic", minversion="2.0.0")


@pytest.fixture(name="http_server", scope="module")
def http_server_fixture() -> Generator[HTTPTestServer, None, None]:
    with HTTPTestServer() as server:
        yield server
