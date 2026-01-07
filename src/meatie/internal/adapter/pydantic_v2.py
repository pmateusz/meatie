#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Generic, get_args, get_origin

import pydantic
from typing_extensions import Annotated, Union, is_typeddict

from meatie.error import ParseResponseError
from meatie.internal.types import T
from meatie.types import AsyncResponse, Response

from . import JsonAdapter, TypeAdapter


class PydanticV2TypeAdapter(Generic[T]):
    def __init__(self, adapter: pydantic.TypeAdapter[T]) -> None:
        self.adapter = adapter

    def from_response(self, response: Response) -> T:
        json_model = JsonAdapter.from_response(response)
        try:
            return self.adapter.validate_python(json_model)
        except pydantic.ValidationError as exc:
            text = response.text()
            raise ParseResponseError(text, response) from exc

    async def from_async_response(self, response: AsyncResponse) -> T:
        json_model = await JsonAdapter.from_async_response(response)
        try:
            return self.adapter.validate_python(json_model)
        except pydantic.ValidationError as exc:
            text = await response.text()
            raise ParseResponseError(text, response) from exc

    def to_content(self, value: T) -> Any:
        return self.adapter.dump_python(value, mode="json", by_alias=True)


class PydanticV2TypeAdapterFactory:
    @staticmethod
    def __call__(model_cls: Union[type[T], pydantic.TypeAdapter[T]]) -> TypeAdapter[T]:
        if isinstance(model_cls, pydantic.TypeAdapter):
            return PydanticV2TypeAdapter(model_cls)
        adapter = pydantic.TypeAdapter(model_cls)
        return PydanticV2TypeAdapter(adapter)

    @classmethod
    def is_model_type(cls, value: Any) -> bool:
        if isclass(value):
            return issubclass(value, pydantic.BaseModel) or is_dataclass(value) or is_typeddict(value)

        origin = get_origin(value)
        if origin is Annotated:
            base_type = get_args(value)[0]
            return cls.is_model_type(base_type)

        if origin is Union:
            for arg in get_args(value):
                if not cls.is_model_type(arg):
                    return False
            return True

        return isinstance(value, pydantic.TypeAdapter)
