#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import NoReturn

from meatie import AsyncResponse, Response


class _ClientResponseAdapter:
    @staticmethod
    def from_response(response: Response) -> Response:
        return response

    @staticmethod
    def from_async_response(response: AsyncResponse) -> AsyncResponse:
        return response

    @staticmethod
    def to_content(value: Response) -> NoReturn:
        raise RuntimeError("JSON serialization is not supported")


ClientResponseAdapter = _ClientResponseAdapter()
