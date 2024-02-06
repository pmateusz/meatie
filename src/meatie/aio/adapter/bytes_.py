#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from meatie.aio import AsyncResponse


class _BytesAdapter:
    @staticmethod
    async def from_response(response: AsyncResponse) -> bytes:
        return await response.read()

    @staticmethod
    def to_json(value: bytes) -> bytes:
        return value


AsyncBytesAdapter = _BytesAdapter()
