#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock

import pytest

from meatie import AsyncResponse, HttpStatusError, endpoint


class Client:
    @endpoint("/v1/multisig-transactions/{tx_hash}")
    async def delete_multisig_transaction(self, tx_hash: str) -> AsyncResponse: ...


class Controller:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def delete_transaction(self, tx_hash: str) -> bool:
        response = await self._client.delete_multisig_transaction(tx_hash)
        if response.status == HTTPStatus.NO_CONTENT:
            return True

        if response.status == HTTPStatus.NOT_FOUND:
            return False

        raise HttpStatusError(response)


@pytest.mark.asyncio()
async def test_handles_not_found() -> None:
    # GIVEN
    client = Mock(spec=Client)
    client.delete_multisig_transaction = AsyncMock(return_value=Mock(status=HTTPStatus.NOT_FOUND))
    controller = Controller(client)

    # WHEN
    is_deleted = await controller.delete_transaction("OxDEAD")

    # THEN
    assert not is_deleted


@pytest.mark.asyncio()
async def test_handles_no_content() -> None:
    # GIVEN
    client = Mock(spec=Client)
    client.delete_multisig_transaction = AsyncMock(return_value=Mock(status=HTTPStatus.NO_CONTENT))
    controller = Controller(client)

    # WHEN
    is_deleted = await controller.delete_transaction("Ox1234567")

    # THEN
    assert is_deleted


@pytest.mark.asyncio()
async def test_handles_other_status() -> None:
    # GIVEN
    client = Mock(spec=Client)
    client.delete_multisig_transaction = AsyncMock(return_value=Mock(status=HTTPStatus.INTERNAL_SERVER_ERROR))
    controller = Controller(client)

    # WHEN
    with pytest.raises(HttpStatusError) as exc_info:
        await controller.delete_transaction("Ox1234567")

    # THEN
    assert isinstance(exc_info.value, HttpStatusError)
    assert exc_info.value.response.status == HTTPStatus.INTERNAL_SERVER_ERROR
