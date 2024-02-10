#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json.decoder import JSONDecodeError
from typing import Any, Literal, Optional

from aiohttp import ClientResponse, ContentTypeError
from meatie.error import ParseResponseError, ResponseError


class Response:
    def __init__(self, response: ClientResponse) -> None:
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status

    async def read(self) -> bytes:
        try:
            return await self.response.content.read()
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    async def text(
        self,
        encoding: Optional[str] = None,
        errors: Literal[
            "strict",
            "replace",
            "ignore",
            "surrogateescape",
            "xmlcharrefreplace",
            "backslashreplace",
        ] = "replace",
    ) -> str:
        try:
            return await self.response.text(encoding, errors)
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    async def json(self) -> dict[str, Any]:
        try:
            return await self.response.json()
        except JSONDecodeError as exc:
            text = await self._text()
            raise ParseResponseError(text, self, exc) from exc
        except ContentTypeError as exc:
            text = await self._text()
            raise ParseResponseError(text, exc) from exc

    async def _text(self) -> str:
        try:
            return await self.response.text()
        except Exception as inner_exc:
            raise ResponseError(self, inner_exc) from inner_exc
