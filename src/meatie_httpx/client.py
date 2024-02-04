#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import urllib.parse
from typing import Any, Optional

from httpx import Client
from meatie.internal.types import Request
from typing_extensions import Self

from . import HttpxResponse


class HttpxClient:
    def __init__(self, session: Client, session_params: Optional[dict[str, Any]] = None) -> None:
        self.session = session
        self.session_params = session_params if session_params else {}

    def send(self, request: Request) -> HttpxResponse:
        kwargs: dict[str, Any] = self.session_params.copy()

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.query_params:
            url = request.path + "?" + urllib.parse.urlencode(request.query_params)
        else:
            url = request.path

        response = self.session.request(request.method, url, **kwargs)
        return HttpxResponse(response)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        self.session.close()
