#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any

from requests import Response


class RequestsResponse:
    def __init__(self, response: Response) -> None:
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status_code

    def read(self) -> bytes:
        return self.response.content

    def text(self) -> str:
        return self.response.text

    def json(self) -> dict[str, Any]:
        return self.response.json()
