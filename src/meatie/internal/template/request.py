#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import inspect
from types import GenericAlias
from typing import (
    Any,
    Generic,
    Iterable,
    Optional,
)

from typing_extensions import Callable, Self, Union, get_type_hints

from meatie.api_reference import ApiReference
from meatie.internal.adapter import JsonAdapter, StringAdapter, TypeAdapter, get_adapter
from meatie.internal.types import PT, RequestBodyType, T
from meatie.types import Method, Request

from . import Kind, Parameter, PathTemplate
from .unwrap import Unwrappable


class RequestTemplate(Generic[RequestBodyType]):
    """Represents a template for making HTTP requests."""

    __slots__ = (
        "method",
        "template",
        "params",
        "request_encoder",
        "__param_by_name",
    )

    def __init__(
        self,
        template: PathTemplate,
        params: list[Parameter],
        request_encoder: TypeAdapter[RequestBodyType],
        method: Optional[Method],
    ) -> None:
        """Creates a RequestTemplate.

        Args:
            template: URL path template.
            params: parameters for the HTTP request, such as path, query, and body parameters.
            request_encoder: request body encoder.
            method: HTTP method.
        """
        self.method = method
        self.template = template
        self.params = params
        self.request_encoder = request_encoder

        self.__param_by_name: dict[str, Parameter] = {}
        for param in self.params:
            self.__param_by_name[param.name] = param

    def build_request(self, *args: Any, **kwargs: Any) -> Request:
        """Create Request given *args and **kwargs.

        :return: Request instance
        """
        if self.method is None:
            raise RuntimeError("'method' is None")

        if len(args) > len(self.params):
            raise RuntimeError("Too many arguments passed to the function.")

        value_by_param = {}

        # set arguments passed as args to corresponding values
        for index, value in enumerate(args):
            param = self.params[index]
            value_by_param[param] = value

        # set arguments to default parameter values if arguments were not passed already as args
        for param in self.params:
            if param.default_value is None or param in value_by_param:
                continue
            value_by_param[param] = param.default_value

        # override default values by actual values passed in kwargs
        for name, value in kwargs.items():
            param_opt = self.__param_by_name.get(name)
            if param_opt is None:
                raise ValueError(f"Parameter '{name}' is not mentioned in the endpoint definition.")
            value_by_param[param_opt] = value

        path_kwargs = {}
        query_kwargs = {}
        body_json: Any = None
        body_data: Any = None
        for param, value in value_by_param.items():
            if param.kind == Kind.PATH:
                if param.formatter is not None:
                    value = param.formatter(value)
                path_kwargs[param.api_ref] = value
                continue

            if param.kind == Kind.QUERY:
                # emit query parameters only if underlying value is not None
                if value is None:
                    continue

                if param.marshaller is not None:
                    values = param.marshaller(value)
                    query_kwargs.update(values)
                    continue

                if param.formatter is not None:
                    value = param.formatter(value)
                    query_kwargs[param.api_ref] = value
                    continue

                if isinstance(value, Unwrappable):
                    values = value.unwrap()
                    query_kwargs.update(values)
                    continue

                query_kwargs[param.api_ref] = value
                continue

            if param.kind == Kind.BODY:
                if param.formatter is not None:
                    raw_value = param.formatter(value)
                    if isinstance(raw_value, (str, bytes)):
                        body_data = raw_value
                    else:
                        body_json = raw_value
                else:
                    body_json = self.request_encoder.to_content(value)
                continue

            raise NotImplementedError(f"Kind {param.kind} is not supported")  # pragma: no cover

        path = self.template.format(**path_kwargs)
        return Request(
            method=self.method,
            path=path,
            params=query_kwargs,
            headers={},
            json=body_json,
            data=body_data,
        )

    @classmethod
    def from_callable(cls, func: Callable[PT, T], template: PathTemplate, method: Optional[Method]) -> Self:
        """Create RequestTemplate from a callable.

        Args:
            func: Callable.
            template: URL path template.
            method: HTTP method.

        Returns:
            RequestTemplate instance.

        Raises:
            ValueError: if arguments are found invalid.
        """
        signature = inspect.signature(func)
        type_hints = get_type_hints(func, include_extras=True)
        return cls.from_signature(signature, type_hints, template, method)

    @classmethod
    def from_signature(
        cls,
        signature: inspect.Signature,
        type_hints: dict[str, Union[type, GenericAlias, None]],
        template: PathTemplate,
        method: Optional[Method],
    ) -> Self:
        """Create RequestTemplate from a Python method signature.

        Args:
            signature: Python function signature.
            type_hints: type hints for Python method parameters.
            template: URL path template.
            method: HTTP method.

        Returns:
            RequestTemplate instance.

        Raises:
            ValueError: if arguments are found invalid.
        """
        parameters = []
        request_encoder: TypeAdapter[Any] = JsonAdapter
        for param_name in type_hints:
            if param_name == "return":
                continue

            param_type = type_hints[param_name]
            sig_param = signature.parameters[param_name]
            api_ref = ApiReference.from_signature(sig_param, param_type)
            assert api_ref.name is not None

            kind = Kind.QUERY
            if api_ref.name == "body":
                kind = Kind.BODY
                if api_ref.fmt is None:
                    request_encoder = get_adapter(param_type)
                else:
                    request_encoder = StringAdapter

            elif api_ref.name in template:
                kind = Kind.PATH

            default_value = None
            if sig_param.default is not inspect.Parameter.empty:
                default_value = sig_param.default

            parameter = Parameter(
                kind,
                param_name,
                api_ref.name,
                default_value,
                api_ref.fmt,
                api_ref.unwrap,
            )
            parameters.append(parameter)

        return cls.validate_object(template, parameters, signature, request_encoder, method)

    @classmethod
    def validate_object(
        cls,
        template: PathTemplate,
        params: Iterable[Parameter],
        signature: inspect.Signature,
        request_encoder: TypeAdapter[RequestBodyType],
        method: Optional[Method],
    ) -> Self:
        """Create RequestTemplate given the URL path template, HTTP request parameters, Python function signature, request body encoder, and HTTP method.

        Args:
            template: URL path template.
            params: list of HTTP parameters.
            signature: Python function signature.
            request_encoder: request body encoder.
            method: HTTP method.

        Returns:
            RequestTemplate instance.

        Raises:
            ValueError: if arguments are found invalid, for instance, a parameter mentioned in the URL path template is not present in the method signature.
        """
        template_str = str(template)
        if template_str == "":
            raise ValueError("'path' is empty")

        visited_api_refs = set()
        for param in params:
            if param.name == "self":
                raise ValueError("Parameter 'self' is forbidden")

            if param.api_ref in visited_api_refs:
                raise ValueError(f"Multiple parameters have name '{param.api_ref}'")

            if param.kind == Kind.PATH and param.api_ref not in template:
                raise ValueError(f"Parameter '{param.api_ref}' is not present in the path '{template}'")

            visited_api_refs.add(param.api_ref)

        missing_api_refs = set(template.parameters) - visited_api_refs
        for api_ref in missing_api_refs:
            raise ValueError(f"Parameter '{api_ref}' is not present in the method signature '{signature}'")

        return cls(template, list(params), request_encoder, method)
