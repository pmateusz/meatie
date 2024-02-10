#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Generic

import pydantic
import pydantic.json
from meatie import AsyncResponse, ParseResponseError, Response
from meatie.internal.types import T
from typing_extensions import is_typeddict

from . import JsonAdapter, TypeAdapter


class PydanticV1TypeAdapter(Generic[T]):
    def __init__(self, model_type: type[T]) -> None:
        self.model_type = model_type

    def from_response(self, response: Response) -> T:
        json_model = JsonAdapter.from_response(response)
        try:
            return pydantic.parse_obj_as(self.model_type, json_model)
        except pydantic.ValidationError as exc:
            text = response.text()
            raise ParseResponseError(text, response, exc) from exc

    async def from_async_response(self, response: AsyncResponse) -> T:
        json_model = await JsonAdapter.from_async_response(response)
        try:
            return pydantic.parse_obj_as(self.model_type, json_model)
        except pydantic.ValidationError as exc:
            text = await response.text()
            raise ParseResponseError(text, response, exc) from exc

    @staticmethod
    def to_content(value: T) -> Any:
        json_string = json.dumps(value, default=pydantic.json.pydantic_encoder)
        return json.loads(json_string)


class PydanticV1TypeAdapterFactory:
    @staticmethod
    def __call__(model_cls: type[T]) -> TypeAdapter[T]:
        return PydanticV1TypeAdapter(model_cls)

    @staticmethod
    def is_model_type(value: type[Any]) -> bool:
        return isclass(value) and (
            issubclass(value, pydantic.BaseModel) or is_dataclass(value) or is_typeddict(value)
        )
