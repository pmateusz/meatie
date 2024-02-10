#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import importlib.util
from inspect import isclass
from types import GenericAlias
from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Union,
    get_args,
    get_origin,
)

from meatie import AsyncResponse, Response
from meatie.internal.types import T

from . import (
    BytesAdapter,
    ClientResponseAdapter,
    JsonAdapter,
    NoneAdapter,
    StringAdapter,
    TypeAdapter,
)


def _is_model_type_no_pydantic(value: type[Any]) -> bool:  # pragma: no cover
    return False


class PydanticTypeAdapterFactory(Protocol):
    def __call__(self, model_cls: type[T]) -> TypeAdapter[T]:
        ...

    @staticmethod
    def is_model_type(model_cls: type[Any]) -> bool:
        ...


def _resolve_pydantic_type_adapter_factory() -> (
    Optional[PydanticTypeAdapterFactory]
):  # pragma: no cover
    module_spec = importlib.util.find_spec("pydantic")

    if module_spec is None:
        return None

    try:
        from .pydantic_v2 import PydanticV2TypeAdapterFactory

        return PydanticV2TypeAdapterFactory()
    except ImportError:
        from .pydantic_v1 import PydanticV1TypeAdapterFactory

        return PydanticV1TypeAdapterFactory()


_PydanticTypeAdapterFactory: Optional[
    PydanticTypeAdapterFactory
] = _resolve_pydantic_type_adapter_factory()


def _resolve_is_model_type() -> Callable[[type[Any]], bool]:
    if _PydanticTypeAdapterFactory is None:
        return _is_model_type_no_pydantic
    return _PydanticTypeAdapterFactory.is_model_type


_is_model_type = _resolve_is_model_type()


def get_adapter(value_type: Union[type[T], GenericAlias, None]) -> TypeAdapter[T]:
    if value_type is None:
        return NoneAdapter  # type: ignore[return-value]

    if value_type is bytes:
        return BytesAdapter  # type: ignore[return-value]

    if value_type is str:
        return StringAdapter  # type: ignore[return-value]

    if isinstance(value_type, GenericAlias):
        if _PydanticTypeAdapterFactory is None:
            return JsonAdapter

        origin = get_origin(value_type)
        args = get_args(value_type)
        if issubclass(origin, Sequence):
            if _is_model_type(args[0]):
                return _PydanticTypeAdapterFactory(value_type)  # type: ignore[arg-type]
            return JsonAdapter

        if issubclass(origin, Mapping):
            if _is_model_type(args[1]):
                return _PydanticTypeAdapterFactory(value_type)  # type: ignore[arg-type]
            return JsonAdapter

        return JsonAdapter

    if _is_model_type(value_type):
        if _PydanticTypeAdapterFactory is None:
            return JsonAdapter
        return _PydanticTypeAdapterFactory(value_type)

    if isclass(value_type) and (value_type is Response or value_type is AsyncResponse):
        return ClientResponseAdapter  # type: ignore[return-value]

    return JsonAdapter
