#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from meatie.aio import AsyncResponse

from .types import TypeAdapter


class _BytesAdapter:
    @staticmethod
    async def from_response(response: AsyncResponse) -> bytes:
        return await response.read()

    @staticmethod
    def to_json(value: bytes) -> bytes:
        return value


BytesAdapter: TypeAdapter[bytes] = _BytesAdapter()
