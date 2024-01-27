#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import (
    Any,
    Protocol,
)

from meatie.aio import Response
from meatie.internal.types import T


class TypeAdapter(Protocol[T]):
    async def from_response(self, response: Response) -> T:
        ...

    def to_json(self, value: T) -> Any:
        ...
