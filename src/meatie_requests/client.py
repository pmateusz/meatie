#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import requests.exceptions
from meatie.internal.error import TransportError
from meatie.internal.types import Request
from requests import Session
from typing_extensions import Self

from . import RequestsResponse


class RequestsClient:
    def __init__(self, session: Session, session_params: Optional[dict[str, Any]] = None) -> None:
        self.session = session
        self.session_params = session_params if session_params else {}

    def send(self, request: Request) -> RequestsResponse:
        kwargs: dict[str, Any] = self.session_params.copy()

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.query_params:
            kwargs["params"] = request.query_params

        try:
            response = self.session.request(request.method, request.path, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            raise TransportError(exc) from exc
        return RequestsResponse(response)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        self.session.close()
