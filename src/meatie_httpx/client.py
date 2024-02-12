#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import httpx
from meatie import BaseClient, Cache
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

from . import Response


class Client(BaseClient):
    def __init__(
        self,
        client: httpx.Client,
        client_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Any] = None,
    ) -> None:
        super().__init__(local_cache, limiter)

        self.client = client
        self.client_params = client_params if client_params else {}

    def send(self, request: Request) -> Response:
        kwargs: dict[str, Any] = self.client_params.copy()

        if request.data is not None:
            kwargs["content"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.params:
            kwargs["params"] = request.params

        try:
            response = self.client.request(request.method, request.path, **kwargs)
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
        return Response(response)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        self.client.close()

    def close(self) -> None:
        self.client.close()
