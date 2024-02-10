#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import (
    Any,
    Protocol,
)

from meatie import AsyncResponse, Response
from meatie.internal.types import T


class TypeAdapter(Protocol[T]):
    def from_response(self, response: Response) -> T:
        ...

    async def from_async_response(self, response: AsyncResponse) -> T:
        ...

    def to_content(self, value: T) -> Any:
        ...
