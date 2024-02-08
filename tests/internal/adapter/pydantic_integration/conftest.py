#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Callable

import pytest


@pytest.fixture(name="dump_model")
def dump_model_fixture() -> Callable[[Any], Any]:
    try:
        import pydantic
    except ImportError:
        pytest.skip("no pydantic installed")

    try:
        from pydantic import TypeAdapter

        def dump_model_v2(model: Any) -> Any:
            adapter = TypeAdapter(type(model))
            return adapter.dump_python(model, mode="json", by_alias=True)

        return dump_model_v2

    except ImportError:
        import json

        import pydantic.json

        def dump_model_v1(model: Any) -> Any:
            json_string = json.dumps(model, default=pydantic.json.pydantic_encoder)
            return json.loads(json_string)

        return dump_model_v1
