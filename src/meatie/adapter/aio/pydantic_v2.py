#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Generic

from pydantic import BaseModel, ValidationError
from pydantic import TypeAdapter as pydantic_TypeAdapter
from typing_extensions import is_typeddict

from meatie import ParseResponseError, AsyncResponse
from meatie.internal.types import T
from . import AsyncJsonAdapter, AsyncTypeAdapter


class PydanticV2TypeAdapter(Generic[T]):
    def __init__(self, model_type: type[T]) -> None:
        self.adapter = pydantic_TypeAdapter(model_type)

    async def from_response(self, response: AsyncResponse) -> T:
        json_model = AsyncJsonAdapter.from_response(response)
        try:
            return self.adapter.validate_python(json_model)
        except ValidationError as exc:
            text = await response.text()
            raise ParseResponseError(text, response, exc) from exc

    def to_json(self, value: T) -> Any:
        return self.adapter.dump_python(value, mode="json", by_alias=True)


class PydanticV2TypeAdapterFactory:
    @staticmethod
    def __call__(model_cls: type[T]) -> AsyncTypeAdapter[T]:
        return PydanticV2TypeAdapter(model_cls)

    @staticmethod
    def is_model_type(value: type[Any]) -> bool:
        return isclass(value) and (
            issubclass(value, BaseModel) or is_dataclass(value) or is_typeddict(value)
        )