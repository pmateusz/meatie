#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Annotated, Union

import pytest
from typing_extensions import TypedDict

pydantic = pytest.importorskip("pydantic")

try:
    from meatie.internal.adapter.pydantic_v2 import PydanticV2TypeAdapterFactory as AdapterFactory
except ImportError:
    from meatie.internal.adapter.pydantic_v1 import PydanticV1TypeAdapterFactory as AdapterFactory


class SimpleModel(pydantic.BaseModel):
    name: str


class ModelA(pydantic.BaseModel):
    value: int


class ModelB(pydantic.BaseModel):
    value: str


@dataclass
class SimpleDataclass:
    name: str


class SimpleTypedDict(TypedDict):
    name: str


def test_is_model_type_annotated_base_model() -> None:
    annotated_type = Annotated[SimpleModel, "some metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is True


def test_is_model_type_annotated_dataclass() -> None:
    annotated_type = Annotated[SimpleDataclass, "some metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is True


def test_is_model_type_annotated_typed_dict() -> None:
    annotated_type = Annotated[SimpleTypedDict, "some metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is True


def test_is_model_type_annotated_union_of_models() -> None:
    annotated_type = Annotated[Union[ModelA, ModelB], "discriminator metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is True


def test_is_model_type_nested_annotated() -> None:
    inner = Annotated[SimpleModel, "inner"]
    outer = Annotated[inner, "outer"]
    assert AdapterFactory.is_model_type(outer) is True


def test_is_model_type_annotated_primitive_not_model() -> None:
    annotated_type = Annotated[str, "some metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is False


def test_is_model_type_annotated_union_with_primitive_not_model() -> None:
    annotated_type = Annotated[Union[SimpleModel, str], "metadata"]
    assert AdapterFactory.is_model_type(annotated_type) is False
