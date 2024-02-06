#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import httpx
from meatie.error import (
    MeatieError,
    ProxyError,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)
from meatie.types import Request
from typing_extensions import Self

from . import HttpxResponse


class HttpxClient:
    def __init__(
        self, session: httpx.Client, session_params: Optional[dict[str, Any]] = None
    ) -> None:
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
            kwargs["params"] = request.query_params

        try:
            response = self.session.request(request.method, request.path, **kwargs)
        except (httpx.InvalidURL, httpx.UnsupportedProtocol) as exc:
            raise RequestError(exc) from exc
        except httpx.ProxyError as exc:
            raise ProxyError(exc) from exc
        except httpx.TimeoutException as exc:
            raise Timeout(exc) from exc
        except (httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            raise ServerError(exc) from exc
        except (httpx.TooManyRedirects, httpx.ProtocolError) as exc:
            raise TransportError(exc) from exc
        except httpx.HTTPError as exc:
            raise MeatieError(exc) from exc
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
