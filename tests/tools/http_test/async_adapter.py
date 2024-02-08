#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from asyncio import AbstractEventLoop
from typing import Any, Optional

from meatie import Request
from meatie.types import AsyncClient, AsyncResponse
from typing_extensions import Self


class ResponseAdapter:
    def __init__(self, loop: AbstractEventLoop, response: AsyncResponse) -> None:
        self.loop = loop
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status

    def read(self) -> bytes:
        return self.loop.run_until_complete(self.response.read())

    def text(self) -> str:
        return self.loop.run_until_complete(self.response.text())

    def json(self) -> dict[str, Any]:
        return self.loop.run_until_complete(self.response.json())


class ClientAdapter:
    def __init__(self, loop: AbstractEventLoop, client: AsyncClient) -> None:
        self.loop = loop
        self.client = client

    def send(self, request: Request) -> ResponseAdapter:
        async_response = self.loop.run_until_complete(self.client.send(request))
        return ResponseAdapter(self.loop, async_response)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException], exc_val: Optional[BaseException], exc_tb: Any
    ) -> None:
        self.loop.run_until_complete(self.client.__aexit__(exc_type, exc_val, exc_tb))
