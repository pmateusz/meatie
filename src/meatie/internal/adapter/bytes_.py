#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from meatie import AsyncResponse, Response

from .types import TypeAdapter


class _BytesAdapter:
    @staticmethod
    def from_response(response: Response) -> bytes:
        return response.read()

    @staticmethod
    async def from_async_response(response: AsyncResponse) -> bytes:
        return await response.read()

    @staticmethod
    def to_content(value: bytes) -> bytes:
        return value


BytesAdapter: TypeAdapter[bytes] = _BytesAdapter()
