#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import NoReturn

from meatie.aio import AsyncResponse


class _ClientResponseAdapter:
    @staticmethod
    async def from_response(response: AsyncResponse) -> AsyncResponse:
        return response

    @staticmethod
    def to_json(value: AsyncResponse) -> NoReturn:
        raise RuntimeError("JSON serialization is not supported")


ClientResponseAdapter = _ClientResponseAdapter()
