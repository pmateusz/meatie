#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from unittest.mock import Mock

from aiohttp import ClientResponse
from meatie.adapter import TypeAdapter, get_adapter
from meatie.types import Response


def test_bytes_decoder() -> None:
    # GIVEN
    value = b"123"
    response = Mock(spec=Response, read=Mock(return_value=value))
    adapter: TypeAdapter[bytes] = get_adapter(type(value))

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert value == result


def test_string_decoder() -> None:
    # GIVEN
    value = "123"
    response = Mock(spec=Response, text=Mock(return_value=value))
    adapter = get_adapter(type(value))

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert value == result


def test_response_decoder() -> None:
    # GIVEN
    response = Mock(spec=Response)
    adapter = get_adapter(ClientResponse)

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert result is response


def test_json_decoder() -> None:
    # GIVEN
    value = {"key": "123"}
    response = Mock(spec=Response, json=Mock(return_value=value))
    adapter = get_adapter(dict)

    # WHEN
    result = adapter.from_response(response)

    # THEN
    assert value == result
