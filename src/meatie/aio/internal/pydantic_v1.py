#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Generic

import pydantic.json
from pydantic import BaseModel
from typing_extensions import is_typeddict

from meatie.aio import Response
from meatie.internal.types import T


class PydanticV1TypeAdapter(Generic[T]):
    def __init__(self, model_type: type[T]) -> None:
        self.model_type = model_type

    async def from_response(self, response: Response) -> T:
        raw_model = await response.json()
        return pydantic.parse_obj_as(self.model_type, raw_model)

    @staticmethod
    def to_json(value: T) -> Any:
        json_string = json.dumps(value, default=pydantic.json.pydantic_encoder)
        return json.loads(json_string)


def is_model_type(value: type[Any]) -> bool:
    return isclass(value) and (
        issubclass(value, BaseModel) or is_dataclass(value) or is_typeddict(value)
    )
