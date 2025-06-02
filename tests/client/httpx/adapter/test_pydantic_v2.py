#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Annotated

import pytest
from http_test import HTTPTestServer
from http_test.handlers import echo_json_handler
from httpx import Client as HttpxClient

from meatie import api_ref, endpoint
from meatie_httpx import Client

pydantic = pytest.importorskip("pydantic", minversion="2.0.0")


class Todo(pydantic.BaseModel):
    user_id: int = pydantic.Field(alias="userId")
    id: int
    title: str
    completed: bool


class Params:
    @staticmethod
    def todo(value: Todo) -> dict:
        return value.model_dump(by_alias=True)


class JsonPlaceholderClient(Client):
    def __init__(self, base_url: str) -> None:
        super().__init__(HttpxClient(base_url=base_url))

    @endpoint("/todos")
    def post_todo_as_dict(
        self, todo: Annotated[Todo, api_ref("body", fmt=lambda data: data.model_dump(by_alias=True))]
    ) -> Todo: ...


def test_post_request_body_with_fmt_as_dict(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = echo_json_handler

    # WHEN
    with JsonPlaceholderClient(http_server.base_url) as client:
        todo = client.post_todo_as_dict(Todo(userId=123, id=456, title="abc", completed=True))

    # THEN
    assert todo.user_id == 123
