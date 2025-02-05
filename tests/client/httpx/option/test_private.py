#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any
from unittest.mock import patch

from meatie import endpoint, private
from meatie_httpx import Client


def test_calls_authenticate_on_private_endpoint(mock_tools) -> None:
    # GIVEN
    products = [{"name": "pencil"}, {"name": "headphones"}]
    client = mock_tools.client_with_json_response(json=products)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(client)

        @endpoint("/api/v1/products", private)
        def get_products(self) -> list[Any]: ...

    # WHEN
    with Store() as api:
        with patch.object(api, "authenticate") as method_mock:
            results = api.get_products()

    # THEN
    assert products == results
    method_mock.assert_called_once()
    client.request.assert_called_once()
