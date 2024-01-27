#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from meatie.aio import ParseResponseError, Response

from .types import TypeAdapter


class _StringAdapter:
    @staticmethod
    async def from_response(response: Response) -> str:
        try:
            return await response.text()
        except ValueError as exc:
            raise ParseResponseError(response.status, None) from exc

    @staticmethod
    def to_json(value: str) -> str:  # pragma: no cover
        return value


StringAdapter: TypeAdapter[str] = _StringAdapter()
