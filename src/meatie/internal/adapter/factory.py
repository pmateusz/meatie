#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from importlib.metadata import PackageNotFoundError, version
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

from typing_extensions import Annotated

from meatie.internal.types import T
from meatie.types import AsyncResponse, Response

from .bytes_ import BytesAdapter
from .client_response import ClientResponseAdapter
from .json_ import JsonAdapter
from .none_ import NoneAdapter
from .string_ import StringAdapter
from .types import TypeAdapter


def _is_model_type_no_pydantic(value: type[Any]) -> bool:  # pragma: no cover
    return False


class PydanticTypeAdapterFactory(Protocol):
    def __call__(self, model_cls: type[T]) -> TypeAdapter[T]: ...

    @staticmethod
    def is_model_type(model_cls: type[Any]) -> bool: ...


def _resolve_pydantic_type_adapter_factory() -> Optional[PydanticTypeAdapterFactory]:  # pragma: no cover
    try:
        pydantic_version = version("pydantic")
    except PackageNotFoundError:
        return None

    if pydantic_version.startswith("2."):
        from .pydantic_v2 import PydanticV2TypeAdapterFactory

        return PydanticV2TypeAdapterFactory()
    else:
        from .pydantic_v1 import PydanticV1TypeAdapterFactory

        return PydanticV1TypeAdapterFactory()


_PydanticTypeAdapterFactory: Optional[PydanticTypeAdapterFactory] = _resolve_pydantic_type_adapter_factory()


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

    # Handle Annotated types: check base type but pass full Annotated type to pydantic
    origin = get_origin(value_type)
    if origin is Annotated:
        base_type = get_args(value_type)[0]
        # Check if base type is a pydantic model
        if _is_model_type(base_type):
            if _PydanticTypeAdapterFactory is None:
                return JsonAdapter
            # Pass the full Annotated type to preserve metadata (discriminators, etc.)
            return _PydanticTypeAdapterFactory(value_type)  # type: ignore[arg-type]
        # For non-pydantic Annotated types, use base type for further processing
        value_type = base_type
        origin = get_origin(value_type)

    if isinstance(value_type, GenericAlias):
        if _PydanticTypeAdapterFactory is None:
            return JsonAdapter

        if origin is None:
            return JsonAdapter

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
