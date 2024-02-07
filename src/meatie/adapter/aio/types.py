#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import (
    Any,
    Protocol,
)

from meatie import AsyncResponse
from meatie.internal.types import T


class AsyncTypeAdapter(Protocol[T]):
    async def from_response(self, response: AsyncResponse) -> T:
        ...

    def to_json(self, value: T) -> Any:
        ...
