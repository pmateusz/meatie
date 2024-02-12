#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import requests.exceptions
from meatie import BaseClient, Cache, Request
from meatie.error import (
    MeatieError,
    ProxyError,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)
from requests import Session
from typing_extensions import Self

from . import Response


class Client(BaseClient):
    def __init__(
        self,
        session: Session,
        session_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Any] = None,
    ) -> None:
        super().__init__(local_cache, limiter)

        self.session = session
        self.session_params = session_params if session_params else {}

    def send(self, request: Request) -> Response:
        kwargs: dict[str, Any] = self.session_params.copy()

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.params:
            kwargs["params"] = request.params

        try:
            response = self.session.request(request.method, request.path, **kwargs)
        except (
            requests.exceptions.URLRequired,
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.InvalidURL,
            requests.exceptions.InvalidHeader,
            requests.exceptions.InvalidHeader,
        ) as exc:
            raise RequestError(exc) from exc
        except (requests.exceptions.TooManyRedirects, requests.exceptions.HTTPError) as exc:
            raise TransportError(exc) from exc
        except requests.exceptions.ProxyError as exc:
            raise ProxyError(exc) from exc
        except requests.exceptions.Timeout as exc:
            raise Timeout(exc) from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError) as exc:
            raise ServerError(exc) from exc
        except requests.exceptions.RequestException as exc:
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
        self.close()

    def close(self) -> None:
        self.session.close()
