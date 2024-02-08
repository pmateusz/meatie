#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, cast
from unittest.mock import patch

import pytest
from meatie import Limit, Limiter, Rate, endpoint
from meatie_requests import RequestsClient
from requests import Session

from tests.aio.conftest import MockTools


@pytest.mark.asyncio()
async def test_waits_until_tokens_are_available(mock_tools: MockTools) -> None:
    # GIVEN
    products = [{"name": "bicycle"}]
    response = mock_tools.json_response(json=products)
    session = mock_tools.session_wrap_response(response)
    current_time = 100

    with patch("time.monotonic") as time_monotonic, patch("time.sleep") as time_sleep:
        time_monotonic.return_value = current_time

        class Store(RequestsClient):
            def __init__(self) -> None:
                super().__init__(
                    cast(Session, session),
                    limiter=Limiter(Rate(1), capacity=2, init_tokens=0, init_time=current_time),
                )

            @endpoint("/api/v1/products", Limit(tokens=2))
            def get_products(self) -> list[Any]:
                ...

        # WHEN
        with Store() as api:
            result = api.get_products()

    # THEN
    assert products == result
    time_sleep.assert_called_once_with(2)
    response.json.assert_called_once()
