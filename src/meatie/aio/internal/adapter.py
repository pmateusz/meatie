#  Copyright 2023 The Meatie Authors. All rights reserved.
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

from aiohttp import ClientResponse

from meatie.aio import Response
from meatie.internal.types import T


class TypeAdapter(Protocol[T]):
    async def from_response(self, response: Response) -> T:
        ...

    def to_json(self, value: T) -> Any:
        ...


class _NoneAdapter:
    @staticmethod
    async def from_response(_: Response) -> None:
        return None

    @staticmethod
    def to_json(_: None) -> None:
        return None


class _BytesAdapter:
    @staticmethod
    async def from_response(response: Response) -> bytes:
        return await response.read()

    @staticmethod
    def to_json(value: bytes) -> bytes:
        return value


class _StringAdapter:
    @staticmethod
    async def from_response(response: Response) -> str:
        return await response.text()

    @staticmethod
    def to_json(value: str) -> str:
        return value


class _JsonAdapter:
    @staticmethod
    async def from_response(response: Response) -> Any:
        return await response.json()

    @staticmethod
    def to_json(value: Any) -> Any:
        return value


class _ClientResponseAdapter:
    @staticmethod
    async def from_response(response: Response) -> Response:
        return response

    @staticmethod
    def to_json(value: Any) -> Any:
        raise RuntimeError(f"Serialization to json is not available for {ClientResponse} adapter")


NoneAdapter = _NoneAdapter()
BytesAdapter: TypeAdapter[bytes] = _BytesAdapter()
StringAdapter: TypeAdapter[str] = _StringAdapter()
JsonAdapter = _JsonAdapter()
ClientResponseAdapter = _ClientResponseAdapter()


def _is_model_type_no_pydantic(value: type[Any]) -> bool:
    return False


_is_model_type = _is_model_type_no_pydantic
_PydanticTypeAdapterFactory: Optional[Callable[[type[T]], TypeAdapter[T]]] = None


def _resolve_pydantic_type_adapter() -> None:
    global _is_model_type, _PydanticTypeAdapterFactory
    module_spec = importlib.util.find_spec("pydantic")

    if module_spec is None:
        return

    try:
        from .pydantic_v2 import PydanticV2TypeAdapter, is_model_type

        _PydanticTypeAdapterFactory = PydanticV2TypeAdapter
    except ImportError:
        from .pydantic_v1 import PydanticV1TypeAdapter, is_model_type

        _PydanticTypeAdapterFactory = PydanticV1TypeAdapter

    _is_model_type = is_model_type


_resolve_pydantic_type_adapter()


def get_adapter(value_type: Union[type[T], GenericAlias]) -> TypeAdapter[T]:
    if value_type is None:
        return NoneAdapter  # type: ignore[unreachable]

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
    elif _is_model_type(value_type):
        if _PydanticTypeAdapterFactory is None:
            return JsonAdapter
        return _PydanticTypeAdapterFactory(value_type)

    if isclass(value_type) and issubclass(value_type, ClientResponse):
        return ClientResponseAdapter  # type: ignore[return-value]

    return JsonAdapter
