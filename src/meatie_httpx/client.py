#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import httpx
from typing_extensions import Self

from meatie import (
    BaseClient,
    Cache,
    MeatieError,
    ProxyError,
    Request,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)

from .response import Response


class Client(BaseClient):
    """The sync client implementation using httpx."""

    def __init__(
        self,
        client: httpx.Client,
        client_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Any] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__(local_cache, limiter)

        self.client = client
        self.client_params = client_params if client_params else {}
        self.prefix = prefix

    def send(self, request: Request) -> Response:
        kwargs = build_kwargs(request, self.client_params)

        path = request.path
        if self.prefix is not None:
            path = self.prefix + path

        try:
            response = self.client.request(request.method, path, **kwargs)
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


def build_kwargs(request: Request, client_params: dict[str, Any]) -> dict[str, Any]:
    kwargs = client_params.copy()

    if request.data is not None:
        kwargs["content"] = request.data

    if request.json is not None:
        kwargs["json"] = request.json

    if request.headers:
        kwargs["headers"] = request.headers

    if request.params:
        kwargs["params"] = request.params

    return kwargs
