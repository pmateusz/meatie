#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json import JSONDecodeError
from typing import Any

from aiohttp import ContentTypeError

from meatie.aio import AsyncResponse
from meatie.internal.error import ParseResponseError, ResponseError


class _JsonAdapter:
    @staticmethod
    async def from_response(response: AsyncResponse) -> Any:
        try:
            return await response.json()
        except ContentTypeError as exc:
            raise ResponseError(response, exc) from exc
        except JSONDecodeError as exc:
            text = await response.text()
            raise ParseResponseError(text, response, exc) from exc

    @staticmethod
    def to_json(value: Any) -> Any:
        return value


JsonAdapter = _JsonAdapter()
