#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json import JSONDecodeError
from typing import Any

from meatie.error import ParseResponseError, ResponseError
from meatie.types import AsyncResponse, Response


class _JsonAdapter:
    @staticmethod
    def from_response(response: Response) -> Any:
        try:
            return response.json()
        except JSONDecodeError as exc:
            text = response.text()
            raise ParseResponseError(text, response) from exc
        except Exception as exc:
            raise ResponseError(response) from exc

    @staticmethod
    async def from_async_response(response: AsyncResponse) -> Any:
        try:
            return await response.json()
        except JSONDecodeError as exc:
            text = await response.text()
            raise ParseResponseError(text, response) from exc
        except (ParseResponseError, ResponseError):
            raise

    @staticmethod
    def to_content(value: Any) -> Any:
        return value


JsonAdapter = _JsonAdapter()
