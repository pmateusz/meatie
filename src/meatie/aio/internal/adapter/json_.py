#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json import JSONDecodeError
from typing import Any

from aiohttp import ContentTypeError

from meatie.aio import ParseResponseError, Response


class _JsonAdapter:
    @staticmethod
    async def from_response(response: Response) -> Any:
        try:
            return await response.json()
        except ContentTypeError as exc:
            message = await response.text()
            raise ParseResponseError(response.status, message) from exc
        except JSONDecodeError as exc:
            message = await response.text()
            raise ParseResponseError(response.status, message) from exc

    @staticmethod
    def to_json(value: Any) -> Any:
        return value


JsonAdapter = _JsonAdapter()
