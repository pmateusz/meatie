#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Optional,
    Union,
    overload,
)

from typing_extensions import Self

from meatie import BaseClient, Request, Response
from meatie.internal.adapter import TypeAdapter
from meatie.internal.template import RequestTemplate, get_method
from meatie.internal.types import PT, ResponseBodyType

Operator = Callable[["Context[ResponseBodyType]"], ResponseBodyType]


class EndpointDescriptor(Generic[PT, ResponseBodyType]):
    """Class descriptor for calling HTTP endpoints."""

    def __init__(
        self,
        template: RequestTemplate[Any],
        response_decoder: TypeAdapter[ResponseBodyType],
    ) -> None:
        """Creates an endpoint descriptor.

        Args:
            template: the template for building HTTP requests to send to the given endpoint.
            response_decoder: the adapter for decoding the HTTP responses returned from the endpoint.
        """
        self.template = template
        self.response_decoder = response_decoder
        self.get_json: Optional[Callable[[Any], Any]] = None
        self.get_text: Optional[Callable[[Any], str]] = None
        self.get_error: Optional[Callable[[Response], Optional[Exception]]] = None
        self.__operator_by_priority: dict[int, Operator[ResponseBodyType]] = {}

    def __set_name__(self, owner: type[object], name: str) -> None:
        if self.template.method is not None:
            return

        self.template.method = get_method(name)

    def register_operator(self, priority: int, operator: Operator[ResponseBodyType]) -> None:
        """Registers an operator to apply on an HTTP request or response.

        Meatie uses the following priorities for the built-in operators:
         * 20 - caching
         * 40 - retry
         * 60 - rate limiting
         * 80 - authentication

        Args:
            priority: the priority of the operator, operators are applied in ascending order of priority.
            operator: the operator to apply.
        """
        self.__operator_by_priority[priority] = operator

    @overload
    def __get__(self, instance: None, owner: None) -> Self:
        ...

    @overload
    def __get__(self, instance: BaseClient, owner: type[object]) -> Callable[PT, Awaitable[ResponseBodyType]]:
        ...

    def __get__(
        self, instance: Optional[BaseClient], owner: Optional[type[object]] = None
    ) -> Union[Self, Callable[PT, Awaitable[ResponseBodyType]]]:
        if instance is None or owner is None:
            return self

        priority_operator_pair = list(self.__operator_by_priority.items())
        priority_operator_pair.sort()
        operators = [operator for _, operator in priority_operator_pair]

        return BoundEndpointDescriptor(  # type: ignore[return-value]
            instance,
            operators,
            self.template,
            self.response_decoder,
            self.get_json,
            self.get_text,
            self.get_error,
        )


class Context(Generic[ResponseBodyType]):
    """Stores context for processing an HTTP request."""

    def __init__(
        self,
        client: BaseClient,
        operators: list[Operator[ResponseBodyType]],
        request: Request,
    ) -> None:
        """Initializes the context.

        Args:
            client: HTTP client instance used for sending the HTTP request.
            operators: list of operators that should be applied on the HTTP request and its response.
            request: the HTTP request to be sent.
        """
        self.client = client
        self.__operators = operators
        self.__next_step = 0

        self.request = request
        self.response: Optional[Response] = None

    def proceed(self) -> ResponseBodyType:
        """One method call will apply one operator on the HTTP request.

        Operators are applied on HTTP requests according to order defined in the context object. HTTP responses are processed in the opposite order.
        """
        if self.__next_step >= len(self.__operators):
            raise RuntimeError("No more step to process request")

        current_step = self.__next_step
        self.__next_step += 1
        current_operator = self.__operators[current_step]
        try:
            result = current_operator(self)
            return result
        finally:
            self.__next_step = current_step


class BoundEndpointDescriptor(Generic[PT, ResponseBodyType]):
    """Class descriptor for calling HTTP endpoints  bound to the HTTP client instance."""

    def __init__(
        self,
        instance: BaseClient,
        operators: Iterable[Operator[ResponseBodyType]],
        template: RequestTemplate[Any],
        response_decoder: TypeAdapter[ResponseBodyType],
        get_json: Optional[Callable[[Any], Any]],
        get_text: Optional[Callable[[Any], str]],
        get_error: Optional[Callable[[Response], Optional[Exception]]],
    ) -> None:
        """Initializes the bound descriptor.

        Args:
            instance: HTTP client instance.
            operators: the list of operators to apply on HTTP requests and responses.
            template: the template for building HTTP requests to call the endpoint.
            response_decoder: the adapter for decoding the HTTP responses returned from the endpoint.
            get_json: the function to get JSON from the HTTP response.
            get_text: the function to get text from the HTTP response.
            get_error: the function to get an error from the HTTP response.
        """
        self.__instance = instance
        self.__operators = list(operators)
        self.__operators.append(self.__send_request)
        self.__template = template
        self.__response_decoder = response_decoder
        self.__get_json = get_json
        self.__get_text = get_text
        self.__get_error = get_error

    def __call__(self, *args: PT.args, **kwargs: PT.kwargs) -> ResponseBodyType:
        """Sends an HTTP request.

        Args:
            *args: positional arguments for the endpoint.
            **kwargs: keyword arguments for the endpoint.

        Returns:
            HTTP response body parsed to the expected Python return type used in the method signature.
        """
        request = self.__template.build_request(*args, **kwargs)
        context = Context[ResponseBodyType](self.__instance, self.__operators, request)
        return context.proceed()

    def __send_request(self, context: Context[ResponseBodyType]) -> ResponseBodyType:
        response = self.__instance.send(context.request)
        if self.__get_json is not None:
            response.get_json = self.__get_json
        if self.__get_text is not None:
            response.get_text = self.__get_text
        context.response = response

        if self.__get_error is not None:
            error = self.__get_error(response)
            if error is not None:
                raise error

        return self.__response_decoder.from_response(response)
