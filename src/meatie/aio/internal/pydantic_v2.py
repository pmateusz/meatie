#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Generic

from pydantic import BaseModel, TypeAdapter
from typing_extensions import is_typeddict

from meatie.aio import Response
from meatie.internal.types import T


class PydanticV2TypeAdapter(Generic[T]):
    def __init__(self, model_type: type[T]) -> None:
        self.adapter = TypeAdapter(model_type)

    async def from_response(self, response: Response) -> T:
        json_model = await response.json()
        return self.adapter.validate_python(json_model)

    def to_json(self, value: T) -> Any:
        return self.adapter.dump_python(value, mode="json", by_alias=True)


def is_model_type(value: type[Any]) -> bool:
    return isclass(value) and (
        issubclass(value, BaseModel) or is_dataclass(value) or is_typeddict(value)
    )
