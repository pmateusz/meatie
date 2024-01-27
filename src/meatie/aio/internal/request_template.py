#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import inspect
import re
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    get_args,
    get_type_hints,
)

from typing_extensions import Awaitable, Self

from meatie.aio.internal import JsonAdapter, TypeAdapter, get_adapter
from meatie.internal.http import Method, Request
from meatie.internal.types import PT


class Kind(Enum):
    UNKNOWN = 0
    PATH = 1
    QUERY = 2
    BODY = 3


class ApiRef:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ApiRef):
            return self.name == other.name
        return False

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter) -> Self:
        for arg in get_args(parameter.annotation):
            if isinstance(arg, cls):
                return arg
        return cls(name=parameter.name)


class Parameter:
    __slots__ = ("kind", "name", "api_ref", "default_value")

    def __init__(self, kind: Kind, name: str, api_ref: str, default_value: Any = None) -> None:
        self.kind = kind
        self.name = name
        self.api_ref = api_ref
        self.default_value = default_value

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Parameter):
            return (
                self.name == other.name
                and self.kind == other.kind
                and self.api_ref == other.api_ref
                and self.default_value == other.default_value
            )
        return False


_param_pattern = re.compile(r"{(?P<name>[a-zA-Z_]\w*?)}")


class PathTemplate:
    __slots__ = ("template", "parameters")

    def __init__(self, template: str, parameters: list[str]) -> None:
        self.template = template
        self.parameters = parameters

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PathTemplate):
            return self.template == other.template and self.parameters == other.parameters
        if isinstance(other, str):
            return self.template == other
        return False

    def __hash__(self) -> int:
        return hash(self.template)

    def __contains__(self, item: str) -> bool:
        return item in self.parameters

    def __str__(self) -> str:
        return self.template

    def format(self, **kwargs: dict[str, Any]) -> str:
        return self.template.format(**kwargs)

    @classmethod
    def from_string(cls, template: str) -> Self:
        parameters = [match.group("name") for match in _param_pattern.finditer(template)]
        return cls(template, parameters)


RequestBodyT = TypeVar("RequestBodyT")
ResponseBodyT = TypeVar("ResponseBodyT")


class RequestTemplate(Generic[RequestBodyT, ResponseBodyT]):
    __slots__ = (
        "method",
        "template",
        "params",
        "request_encoder",
        "response_decoder",
        "__param_by_name",
    )

    def __init__(
        self,
        template: PathTemplate,
        params: list[Parameter],
        request_encoder: TypeAdapter[RequestBodyT],
        response_decoder: TypeAdapter[ResponseBodyT],
        method: Optional[Method],
    ) -> None:
        self.method = method
        self.template = template
        self.params = params
        self.request_encoder = request_encoder
        self.response_decoder = response_decoder

        self.__param_by_name: dict[str, Parameter] = {}
        for param in self.params:
            self.__param_by_name[param.name] = param

    def build_request(self, *args: Any, **kwargs: Any) -> Request:
        if self.method is None:
            raise RuntimeError("'method' is None")

        if len(args) > len(self.params):
            raise RuntimeError("Too many arguments passed to the function.")

        value_by_param = {}
        for index, value in enumerate(args):
            param = self.params[index]
            value_by_param[param] = value

        for param in self.params:
            if param.default_value is None or param in value_by_param:
                continue
            value_by_param[param] = param.default_value

        for name, value in kwargs.items():
            param_opt = self.__param_by_name.get(name)
            if param_opt is None:
                raise ValueError(f"Parameter '{name}' is not mentioned in the endpoint definition.")

            if value is None:
                if param_opt in value_by_param:
                    del value_by_param[param_opt]
            else:
                value_by_param[param_opt] = value

        path_kwargs = {}
        query_kwargs = {}
        body_value: Any = None
        for param, value in value_by_param.items():
            if param.kind == Kind.PATH:
                path_kwargs[param.api_ref] = value
                continue

            if param.kind == Kind.QUERY:
                query_kwargs[param.api_ref] = value
                continue

            if param.kind == Kind.BODY:
                body_value = value
                continue

            raise NotImplementedError(f"Kind {param.kind} is not supported")  # pragma: no cover

        if body_value is not None:
            body_json = self.request_encoder.to_json(body_value)
        else:
            body_json = None

        path = self.template.format(**path_kwargs)
        return Request(
            method=self.method, path=path, query_params=query_kwargs, headers={}, json=body_json
        )

    @classmethod
    def from_callable(
        cls,
        func: Callable[PT, Awaitable[ResponseBodyT]],
        template: PathTemplate,
        method: Optional[Method],
    ) -> Self:
        signature = inspect.signature(func)
        type_by_param_name = get_type_hints(func)

        parameters = []
        request_encoder: TypeAdapter[Any] = JsonAdapter
        response_decoder: TypeAdapter[ResponseBodyT] = JsonAdapter
        for param_name in type_by_param_name:
            param_type = type_by_param_name[param_name]
            if param_name == "return":
                response_decoder = get_adapter(param_type)
                continue

            sig_param = signature.parameters[param_name]
            api_ref = ApiRef.from_signature(sig_param)
            kind = Kind.QUERY
            if api_ref.name == "body":
                kind = Kind.BODY
                request_encoder = get_adapter(param_type)
            elif api_ref.name in template:
                kind = Kind.PATH

            default_value = None
            if sig_param.default is not inspect.Parameter.empty:
                default_value = sig_param.default
            parameter = Parameter(kind, param_name, api_ref.name, default_value)
            parameters.append(parameter)

        return cls.validate_object(
            template, parameters, signature, request_encoder, response_decoder, method
        )

    @classmethod
    def validate_object(
        cls,
        template: PathTemplate,
        params: Iterable[Parameter],
        signature: inspect.Signature,
        request_encoder: TypeAdapter[RequestBodyT],
        response_decoder: TypeAdapter[ResponseBodyT],
        method: Optional[Method],
    ) -> Self:
        template_str = str(template)
        if template_str == "":
            raise ValueError("'path' is empty")

        if not template_str.startswith("/"):
            raise ValueError("'path' must start with '/'")

        visited_api_refs = set()
        for param in params:
            if param.name == "self":
                raise ValueError("Parameter 'self' is forbidden")

            if param.api_ref in visited_api_refs:
                raise ValueError(f"Multiple parameters have name '{param.api_ref}'")

            if param.kind == Kind.PATH and param.api_ref not in template:
                raise ValueError(
                    f"Parameter '{param.api_ref}' is not present in the path '{template}'"
                )

            visited_api_refs.add(param.api_ref)

        missing_api_refs = set(template.parameters) - visited_api_refs
        for api_ref in missing_api_refs:
            raise ValueError(
                f"Parameter '{api_ref}' is not present in the method signature '{signature}'"
            )

        return cls(template, list(params), request_encoder, response_decoder, method)
