#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie.aio import AsyncResponse
from meatie.error import ResponseError


class _StringAdapter:
    @staticmethod
    async def from_response(response: AsyncResponse) -> str:
        try:
            return await response.text()
        except ValueError as exc:
            raise ResponseError(response, exc) from exc

    @staticmethod
    def to_json(value: str) -> str:  # pragma: no cover
        return value


AsyncStringAdapter = _StringAdapter()
