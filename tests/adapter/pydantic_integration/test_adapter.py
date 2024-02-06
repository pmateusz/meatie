#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, Callable
from unittest.mock import Mock

import pytest
from meatie.adapter import TypeAdapter, get_adapter
from meatie.types import Response

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel


def test_pydantic_model(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class Product(BaseModel):
        name: str

    value = Product(name="glasses")
    response = Mock(spec=Response, json=Mock(return_value=dump_model(value)))
    adapter: TypeAdapter[str] = get_adapter(type(value))

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert value == result


def test_pydantic_model_sequence(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class ListElement(BaseModel):
        name: str

    value = ListElement(name="123")
    response = Mock(spec=Response, json=Mock(return_value=[dump_model(value)]))
    adapter: TypeAdapter[list[ListElement]] = get_adapter(list[ListElement])

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert [value] == result


def test_pydantic_model_dict(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class DictValue(BaseModel):
        name: str

    value = DictValue(name="123")
    response = Mock(spec=Response, json=Mock(return_value={"key": dump_model(value)}))
    adapter: TypeAdapter[dict[str, DictValue]] = get_adapter(dict[str, DictValue])

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert {"key": value} == result
