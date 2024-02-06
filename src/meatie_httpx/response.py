#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from json import JSONDecodeError
from typing import Any

from httpx import Response
from meatie.error import ParseResponseError, ResponseError


class HttpxResponse:
    def __init__(self, response: Response) -> None:
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status_code

    def read(self) -> bytes:
        return self.response.content

    def text(self) -> str:
        try:
            return self.response.text
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    def json(self) -> dict[str, Any]:
        try:
            return self.response.json()
        except JSONDecodeError as exc:
            try:
                text = self.response.text
            except Exception as inner_exc:
                raise ResponseError(self, inner_exc) from inner_exc
            raise ParseResponseError(text, self, exc) from exc
