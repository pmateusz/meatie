#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import asyncio
from asyncio import Task
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponse, RequestInfo
from aiohttp.helpers import TimerNoop
from meatie.aio import AsyncResponse
from meatie.aio.internal import TypeAdapter, get_adapter
from yarl import URL


@pytest.mark.asyncio()
async def test_bytes_decoder() -> None:
    # GIVEN
    value = b"123"
    response = Mock(spec=AsyncResponse, read=AsyncMock(return_value=value))
    adapter: TypeAdapter[bytes] = get_adapter(type(value))

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert value == result


@pytest.mark.asyncio()
async def test_string_decoder() -> None:
    # GIVEN
    value = "123"
    response = Mock(spec=AsyncResponse, text=AsyncMock(return_value=value))
    adapter = get_adapter(type(value))

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert value == result


@pytest.mark.asyncio()
async def test_response_decoder() -> None:
    # GIVEN
    response = ClientResponse(
        "GET",
        URL.build(),
        writer=Mock(spec=Task),
        continue100=None,
        timer=Mock(spec=TimerNoop),
        request_info=Mock(spec=RequestInfo),
        traces=[],
        loop=asyncio.get_running_loop(),
        session=None,  # type: ignore[arg-type]
    )
    adapter = get_adapter(ClientResponse)

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert result is response


@pytest.mark.asyncio()
async def test_json_decoder() -> None:
    # GIVEN
    value = {"key": "123"}
    response = Mock(spec=AsyncResponse)
    response.json = AsyncMock(return_value=value)
    adapter = get_adapter(dict)

    # WHEN
    result = await adapter.from_response(response)

    # THEN
    assert value == result
