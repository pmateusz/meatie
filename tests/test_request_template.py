#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import inspect
from typing import Annotated, Any, Optional
from unittest.mock import Mock

import pytest
from meatie.adapter import JsonAdapter, NoneAdapter
from meatie.request_template import (
    ApiRef,
    Kind,
    Parameter,
    PathTemplate,
    RequestTemplate,
)


def test_validate_object() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/api/order/{order_id}/position/{position_id}")
    path_params = [
        Parameter(Kind.PATH, "position_id", "position_id"),
        Parameter(Kind.PATH, "order_id", "order_id"),
    ]

    # WHEN
    template = RequestTemplate.validate_object(
        path_template,
        path_params,
        Mock(spec=inspect.Signature),
        JsonAdapter,
        "GET",
    )

    # THEN
    assert isinstance(template, RequestTemplate)


def test_path_cannot_be_empty() -> None:
    with pytest.raises(ValueError) as exc_info:
        # WHEN
        RequestTemplate.validate_object(
            PathTemplate.from_string(""),
            [],
            Mock(spec=inspect.Signature),
            JsonAdapter,
            "GET",
        )

        # THEN
    assert "'path' is empty" == str(exc_info.value)


def test_path_must_start_with_slash() -> None:
    with pytest.raises(ValueError) as exc_info:
        # WHEN
        RequestTemplate.validate_object(
            PathTemplate.from_string("abc"),
            [],
            Mock(spec=inspect.Signature),
            JsonAdapter,
            "GET",
        )

        # THEN
    assert "'path' must start with '/'" == str(exc_info.value)


def test_all_parameters_must_be_present_in_signature() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/orders/{order_ref}/position/{position_ref}")
    path_params = [Parameter(Kind.PATH, "position_id", "position_ref")]

    # WHEN
    with pytest.raises(ValueError) as exc_info:
        RequestTemplate.validate_object(
            path_template,
            path_params,
            Mock(spec=inspect.Signature, __str__=Mock(return_value="...")),
            JsonAdapter,
            "GET",
        )

    # THEN
    assert "Parameter 'order_ref' is not present in the method signature '...'" == str(
        exc_info.value
    )


def test_all_parameters_must_be_present_in_path() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/orders/{order_ref}/position/{position_ref}")
    path_params = [Parameter(Kind.PATH, "order_id", "order_ref")]

    # WHEN
    with pytest.raises(ValueError) as exc_info:
        RequestTemplate.validate_object(
            path_template,
            path_params,
            Mock(spec=inspect.Signature, __str__=Mock(return_value="...")),
            JsonAdapter,
            "GET",
        )

    # THEN
    assert "Parameter 'position_ref' is not present in the method signature '...'" == str(
        exc_info.value
    )


def test_build_template() -> None:
    # GIVEN
    template = RequestTemplate(
        PathTemplate.from_string("/api/v1/order/{order_ref}/position"),
        [
            Parameter(Kind.PATH, "order_id", "order_ref"),
            Parameter(Kind.QUERY, "sort_by", "orderBy"),
        ],
        JsonAdapter,
        "GET",
    )

    # WHEN
    request = template.build_request(order_id=1, sort_by="price")

    # THEN
    assert "/api/v1/order/1/position" == request.path
    assert {"orderBy": "price"} == request.query_params


def test_build_template_with_default_value() -> None:
    # GIVEN
    template = RequestTemplate(
        PathTemplate.from_string("/api/v1/orders"),
        [
            Parameter(Kind.QUERY, "limit", "limit", 100),
        ],
        NoneAdapter,
        "GET",
    )

    # WHEN
    request = template.build_request()

    # THEN
    assert "/api/v1/orders" == request.path
    assert {"limit": 100} == request.query_params


def test_create_template_from_signature() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/api/v1/order/{order_id}/position")

    async def get_positions_by_order_id(
        order_id: int, sort_by: Annotated[str, ApiRef("orderBy")]
    ) -> list[Any]:
        return []

    # WHEN
    request: RequestTemplate[None] = RequestTemplate.from_callable(
        get_positions_by_order_id, path_template, "GET"
    )

    # THEN
    assert "GET" == request.method
    assert path_template == request.template
    assert [
        Parameter(Kind.PATH, "order_id", "order_id"),
        Parameter(Kind.QUERY, "sort_by", "orderBy"),
    ] == request.params


def test_create_template_from_signature_with_parameter_with_default_value() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/api/v1/orders")

    async def get_orders(limit: int = 100) -> list[Any]:
        return []

    # WHEN
    request: RequestTemplate[None] = RequestTemplate.from_callable(get_orders, path_template, "GET")

    # THEN
    assert "GET" == request.method
    assert path_template == request.template
    assert [Parameter(Kind.QUERY, "limit", "limit", 100)] == request.params


def test_create_template_from_signature_with_optional_parameter() -> None:
    # GIVEN
    path_template = PathTemplate.from_string("/api/v1/orders")

    async def get_orders(offset: Optional[int] = None) -> list[Any]:
        return []

    # WHEN
    request: RequestTemplate[None] = RequestTemplate.from_callable(get_orders, path_template, "GET")

    # THEN
    assert "GET" == request.method
    assert path_template == request.template
    assert [Parameter(Kind.QUERY, "offset", "offset", None)] == request.params
