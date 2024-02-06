#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import NoReturn

from meatie.types import Response


class _ClientResponseAdapter:
    @staticmethod
    async def from_response(response: Response) -> Response:
        return response

    @staticmethod
    def to_json(value: Response) -> NoReturn:
        raise RuntimeError("JSON serialization is not supported")


AsyncClientResponseAdapter = _ClientResponseAdapter()
