#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any

import requests
from meatie.error import ParseResponseError, ResponseError


class Response:
    def __init__(self, response: requests.Response) -> None:
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status_code

    def read(self) -> bytes:
        try:
            return self.response.content
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    def text(self) -> str:
        try:
            return self.response.text
        except Exception as exc:
            raise ResponseError(self, exc) from exc

    def json(self) -> dict[str, Any]:
        try:
            return self.response.json()
        except requests.JSONDecodeError as exc:
            text = self.response.text
            raise ParseResponseError(text, self, exc) from exc
        except Exception as exc:
            raise ResponseError(self, exc) from exc
