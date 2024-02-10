#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from unittest.mock import Mock

import pytest
from aiohttp import ClientResponse
from meatie.internal.adapter import ClientResponseAdapter


def test_to_json() -> None:
    # GIVEN
    response = Mock(spec=ClientResponse)

    # WHEN
    with pytest.raises(RuntimeError) as exc_info:
        ClientResponseAdapter.to_content(response)

    # THEN
    exc = exc_info.value
    assert exc.args == ("JSON serialization is not supported",)
