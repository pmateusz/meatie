from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Annotated, Any, Optional

import pytest
from aiohttp import ClientSession
from http_test import Handler, HTTPTestServer
from meatie import api_ref, endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel, Field, field_serializer


class MySearchFilter(BaseModel):
    execution_date__lte: Optional[datetime] = None
    limit: Optional[int] = 10
    address: str

    @field_serializer("execution_date__lte")
    def format_date(self, dt: datetime, _info) -> str:
        return dt.isoformat(timespec="seconds")


class MyTransaction(BaseModel):
    time: datetime
    symbol: str
    amount: Decimal


class MySearchResults(BaseModel):
    data: list[MyTransaction] = Field(default_factory=list)


def dump_model(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", exclude_unset=True)


class MyClient(Client):
    @endpoint("/v1/search")
    async def get_search(
        self, query_params: Annotated[MySearchFilter, api_ref(unwrap=dump_model)]
    ) -> MySearchResults:
        ...


@pytest.mark.asyncio()
async def test_send_search_query(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(h: Handler) -> None:
        if h.path == "/v1/search?limit=5&address=0x1234":
            data = [
                MyTransaction.model_construct(
                    time=datetime(2024, 10, 27), amount=Decimal("123"), symbol="BTC"
                )
            ]
        else:
            data = []

        results = MySearchResults.model_construct(data=data)
        h.send_json(HTTPStatus.OK, results.model_dump(mode="json"))

    http_server.handler = handler
    async with ClientSession(base_url=http_server.base_url) as session:
        client = MyClient(session)

        # WHEN
        result = await client.get_search(MySearchFilter(address="0x1234", limit=5))

    # THEN
    assert result.data
