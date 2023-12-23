#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, Callable
from unittest.mock import AsyncMock, Mock

import pytest
from meatie.aio import Response
from meatie.aio.internal import TypeAdapter, get_adapter

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel


@pytest.mark.asyncio()
async def test_pydantic_model(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class Product(BaseModel):
        name: str

    value = Product(name="glasses")
    response = Mock(spec=Response, json=AsyncMock(return_value=dump_model(value)))
    adapter: TypeAdapter[str] = get_adapter(type(value))

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert value == result


@pytest.mark.asyncio()
async def test_pydantic_model_sequence(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class ListElement(BaseModel):
        name: str

    value = ListElement(name="123")
    response = Mock(spec=Response)
    response.json = AsyncMock(return_value=[dump_model(value)])
    adapter: TypeAdapter[list[ListElement]] = get_adapter(list[ListElement])

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert [value] == result


@pytest.mark.asyncio()
async def test_pydantic_model_dict(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class DictValue(BaseModel):
        name: str

    value = DictValue(name="123")
    response = Mock(spec=Response)
    response.json = AsyncMock(return_value={"key": dump_model(value)})
    adapter: TypeAdapter[dict[str, DictValue]] = get_adapter(dict[str, DictValue])

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert {"key": value} == result
