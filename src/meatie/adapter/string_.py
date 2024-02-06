#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie.adapter import TypeAdapter
from meatie.error import ResponseError
from meatie.types import Response


class _StringAdapter:
    @staticmethod
    def from_response(response: Response) -> str:
        try:
            return response.text()
        except ValueError as exc:
            raise ResponseError(response, exc) from exc

    @staticmethod
    def to_json(value: str) -> str:  # pragma: no cover
        return value


StringAdapter: TypeAdapter[str] = _StringAdapter()
