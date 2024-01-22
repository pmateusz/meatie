#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import inspect
import re
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ApiRef:
    name: str

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter) -> Self:
        for arg in get_args(parameter.annotation):
            if isinstance(arg, cls):
                return arg
        return cls(name=parameter.name)


class Kind(Enum):
    UNKNOWN = 0
    PATH = 1
    QUERY = 2
    BODY = 3


@dataclass(unsafe_hash=True)
class Parameter:
    kind: Kind
    name: str
    api_ref: str


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
        "parameters",
        "request_encoder",
        "response_decoder",
        "__parameter_by_name",
    )

    def __init__(
        self,
        template: PathTemplate,
        parameters: Iterable[Parameter],
        request_encoder: TypeAdapter[RequestBodyT],
        response_decoder: TypeAdapter[ResponseBodyT],
        method: Optional[Method],
    ) -> None:
        self.method = method
        self.template = template
        self.parameters = parameters
        self.request_encoder = request_encoder
        self.response_decoder = response_decoder

        self.__parameter_by_name: dict[str, Parameter] = {}
        for parameter in self.parameters:
            self.__parameter_by_name[parameter.name] = parameter

    def build_request(self, *args: Any, **kwargs: Any) -> Request:
        if self.method is None:
            raise RuntimeError("'method' is None")

        bound_parameter_names = set()

        value_by_parameter = {}
        for name, value in kwargs.items():
            parameter_opt = self.__parameter_by_name.get(name)
            if parameter_opt is None:
                raise ValueError(f"Parameter '{name}' is not mentioned in the endpoint definition")

            value_by_parameter[parameter_opt] = value
            bound_parameter_names.add(name)

        unbound_parameters = [
            parameter
            for parameter in self.parameters
            if parameter.name not in bound_parameter_names
        ]
        num_unbound_params = len(unbound_parameters)
        num_args = len(args)
        if num_args > num_unbound_params:
            raise ValueError(
                "Too many arguments passed to the function."
                f" Value '{args[num_unbound_params]}' is not bound to any parameter."
            )
        if num_args < num_unbound_params:
            raise ValueError(
                f"Too few arguments passed to the function. Parameter '{unbound_parameters[num_args]}' is unbound."
            )

        for parameter, value in zip(unbound_parameters, args):
            value_by_parameter[parameter] = value

        path_kwargs = {}
        query_kwargs = {}
        body_value: Any = None
        for parameter, value in value_by_parameter.items():
            if parameter.kind == Kind.PATH:
                path_kwargs[parameter.api_ref] = value
                continue

            if parameter.kind == Kind.QUERY:
                query_kwargs[parameter.api_ref] = value
                continue

            if parameter.kind == Kind.BODY:
                body_value = value
                continue

            raise NotImplementedError(f"Kind {parameter.kind} is not supported")

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

            parameter = Parameter(kind, param_name, api_ref.name)
            parameters.append(parameter)

        return cls.validate_object(
            template, parameters, signature, request_encoder, response_decoder, method
        )

    @classmethod
    def validate_object(
        cls,
        template: PathTemplate,
        parameters: Iterable[Parameter],
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
        for parameter in parameters:
            if parameter.name == "self":
                raise ValueError("Parameter 'self' is forbidden")

            if parameter.api_ref in visited_api_refs:
                raise ValueError(f"Multiple parameters have name '{parameter.api_ref}'")

            if parameter.kind == Kind.PATH and parameter.api_ref not in template:
                raise ValueError(
                    f"Parameter '{parameter.api_ref}' is not present in the path '{template}'"
                )

            visited_api_refs.add(parameter.api_ref)

        missing_api_refs = set(template.parameters) - visited_api_refs
        for api_ref in missing_api_refs:
            raise ValueError(
                f"Parameter '{api_ref}' is not present in the method signature '{signature}'"
            )

        return cls(template, parameters, request_encoder, response_decoder, method)
