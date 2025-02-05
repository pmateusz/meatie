#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any

from typing_extensions import override

from meatie import BaseClient, Request


def test_can_influence_cache_size() -> None:
    # GIVEN
    class CustomClient(BaseClient):
        SHARED_CACHE_MAX_SIZE = 10

        @override
        def send(self, request: Request) -> Any:
            pass

    # WHEN
    client = CustomClient()

    # THEN
    assert client.shared_cache.max_size == 10
