#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie import AsyncResponse, Response
from meatie.error import ResponseError


class _StringAdapter:
    @staticmethod
    def from_response(response: Response) -> str:
        try:
            return response.text()
        except ValueError as exc:
            raise ResponseError(response, exc) from exc

    @staticmethod
    async def from_async_response(response: AsyncResponse) -> str:
        try:
            return await response.text()
        except ValueError as exc:
            raise ResponseError(response, exc) from exc

    @staticmethod
    def to_content(value: str) -> str:  # pragma: no cover
        return value


StringAdapter = _StringAdapter()
