#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json.decoder import JSONDecodeError
from typing import Any, Awaitable, Callable, Optional

from aiohttp import ClientResponse, ContentTypeError
from meatie.error import ParseResponseError, ResponseError


class Response:
    def __init__(
        self,
        response: ClientResponse,
        get_json: Optional[Callable[[ClientResponse], Awaitable[dict[str, Any]]]] = None,
        get_text: Optional[Callable[[ClientResponse], Awaitable[str]]] = None,
    ) -> None:
        self.response = response
        if get_json is not None:
            self.get_json = get_json  # type: ignore[assignment]
        if get_text is not None:
            self.get_text = get_text  # type: ignore[assignment]

    @property
    def status(self) -> int:
        return self.response.status

    async def read(self) -> bytes:
        try:
            return await self.response.content.read()
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    async def text(self) -> str:
        try:
            return await self.get_text(self.response)
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    async def json(self) -> dict[str, Any]:
        try:
            return await self.get_json(self.response)
        except JSONDecodeError as exc:
            text = await self.text()
            raise ParseResponseError(text, self, exc) from exc
        except ContentTypeError as exc:
            text = await self.text()
            raise ParseResponseError(text, self, exc) from exc

    @classmethod
    def get_json(cls, response: ClientResponse) -> Awaitable[dict[str, Any]]:
        return response.json()

    @classmethod
    def get_text(cls, response: ClientResponse) -> Awaitable[str]:
        return response.text(errors="replace")
