#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any

from aiohttp import ClientResponse


class AiohttpResponse:
    def __init__(self, response: ClientResponse) -> None:
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status

    async def read(self) -> bytes:
        return await self.response.content.read()

    async def text(self) -> str:
        return await self.response.text()

    async def json(self) -> dict[str, Any]:
        return await self.response.json()
