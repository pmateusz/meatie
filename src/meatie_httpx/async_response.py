#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json.decoder import JSONDecodeError
from typing import Any, Awaitable, Callable, Optional

import httpx

from meatie import AsyncResponse as BaseAsyncResponse
from meatie import ParseResponseError, ResponseError


class AsyncResponse(BaseAsyncResponse):
    """The async response implementation using httpx."""

    def __init__(
        self,
        response: httpx.Response,
        get_json: Optional[Callable[[httpx.Response], Awaitable[Any]]] = None,
        get_text: Optional[Callable[[httpx.Response], Awaitable[str]]] = None,
    ) -> None:
        self.response = response
        if get_json is not None:
            self.get_json = get_json  # type: ignore[assignment]
        if get_text is not None:
            self.get_text = get_text  # type: ignore[assignment]

    @property
    def status(self) -> int:
        return self.response.status_code

    async def read(self) -> bytes:
        try:
            return self.response.content
        except Exception as exc:
            raise ResponseError(self) from exc

    async def text(self) -> str:
        try:
            return await self.get_text(self.response)
        except Exception as exc:
            raise ResponseError(self) from exc

    async def json(self) -> dict[str, Any]:
        try:
            return await self.get_json(self.response)
        except JSONDecodeError as exc:
            text = await self.text()
            raise ParseResponseError(text, self) from exc
        except Exception as exc:
            raise ResponseError(self) from exc

    @classmethod
    async def get_json(cls, response: httpx.Response) -> Any:
        return response.json()

    @classmethod
    async def get_text(cls, response: httpx.Response) -> str:
        return response.text
