#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""Type hint verification tests for the @endpoint decorator."""

from typing import Annotated

import pytest

from meatie import api_ref, endpoint

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel
Field = pydantic.Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class TypedAsyncClient:
    """Test client with endpoint signatures for type checking. The client is for test purposes only as it is not bind to any HTTP client library."""

    @endpoint("/todos")
    async def get_todos(self) -> list[Todo]: ...

    @endpoint("/todos")
    async def get_todos_with_query(self, user_id: Annotated[int, api_ref("userId")]) -> list[Todo]: ...

    @endpoint("/todos/{todo_id}")
    async def get_todo_by_id(self, todo_id: int) -> Todo: ...

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo: ...

    @endpoint("/todos/{todo_id}", method="DELETE")
    async def delete_todo(self, todo_id: int) -> None: ...

    @endpoint("/todos/count")
    async def get_todo_count(self) -> int: ...


class TypedSyncClient:
    """Test client with endpoint signatures for type checking. The client is for test purposes only as it is not bind to any HTTP client library."""

    @endpoint("/todos")
    def get_todos(self) -> list[Todo]: ...

    @endpoint("/todos")
    def get_todos_with_query(self, user_id: Annotated[int, api_ref("userId")]) -> list[Todo]: ...

    @endpoint("/todos/{todo_id}")
    def get_todo_by_id(self, todo_id: int) -> Todo: ...

    @endpoint("/todos")
    def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo: ...

    @endpoint("/todos/{todo_id}", method="DELETE")
    def delete_todo(self, todo_id: int) -> None: ...

    @endpoint("/todos/count")
    def get_todo_count(self) -> int: ...


def test_async_endpoint_return_types() -> None:
    """Verify async endpoints create AsyncEndpointDescriptor with correct HTTP methods."""
    from meatie.aio.descriptor import AsyncEndpointDescriptor

    assert isinstance(TypedAsyncClient.get_todos, AsyncEndpointDescriptor)
    assert isinstance(TypedAsyncClient.get_todo_by_id, AsyncEndpointDescriptor)
    assert isinstance(TypedAsyncClient.get_todo_count, AsyncEndpointDescriptor)

    assert TypedAsyncClient.get_todos.template.method == "GET"
    assert TypedAsyncClient.get_todo_by_id.template.method == "GET"
    assert TypedAsyncClient.delete_todo.template.method == "DELETE"


def test_async_endpoint_parameter_types() -> None:
    """Verify endpoints correctly register query, path, and body parameters."""
    get_todos_with_query_template = TypedAsyncClient.get_todos_with_query.template
    get_todo_by_id_template = TypedAsyncClient.get_todo_by_id.template
    post_todo_template = TypedAsyncClient.post_todo.template

    query_params = [p for p in get_todos_with_query_template.params if p.name == "user_id"]
    assert len(query_params) > 0

    path_params = [p for p in get_todo_by_id_template.params if p.name == "todo_id"]
    assert len(path_params) > 0

    body_params = [p for p in post_todo_template.params if p.name == "todo"]
    assert len(body_params) > 0

    assert "todo_id" in str(get_todo_by_id_template.template)


def test_endpoint_decorator_preserves_signatures() -> None:
    """Verify endpoint methods are accessible for IDE inspection."""
    assert hasattr(TypedAsyncClient, "get_todos")
    assert hasattr(TypedAsyncClient, "get_todo_by_id")
    assert hasattr(TypedAsyncClient, "post_todo")

    assert "get_todos" in dir(TypedAsyncClient)
    assert "get_todo_by_id" in dir(TypedAsyncClient)
    assert "post_todo" in dir(TypedAsyncClient)


def test_sync_endpoint_return_types() -> None:
    """Verify sync endpoints create EndpointDescriptor with correct HTTP methods."""
    from meatie.descriptor import EndpointDescriptor

    assert isinstance(TypedSyncClient.get_todos, EndpointDescriptor)
    assert isinstance(TypedSyncClient.get_todo_by_id, EndpointDescriptor)
    assert isinstance(TypedSyncClient.get_todo_count, EndpointDescriptor)

    assert TypedSyncClient.get_todos.template.method == "GET"
    assert TypedSyncClient.get_todo_by_id.template.method == "GET"
    assert TypedSyncClient.delete_todo.template.method == "DELETE"


def test_sync_endpoint_parameter_types() -> None:
    """Verify endpoints correctly register query, path, and body parameters."""
    get_todos_with_query_template = TypedSyncClient.get_todos_with_query.template
    get_todo_by_id_template = TypedSyncClient.get_todo_by_id.template
    post_todo_template = TypedSyncClient.post_todo.template

    query_params = [p for p in get_todos_with_query_template.params if p.name == "user_id"]
    assert len(query_params) > 0

    path_params = [p for p in get_todo_by_id_template.params if p.name == "todo_id"]
    assert len(path_params) > 0

    body_params = [p for p in post_todo_template.params if p.name == "todo"]
    assert len(body_params) > 0

    assert "todo_id" in str(get_todo_by_id_template.template)


def test_sync_endpoint_decorator_preserves_signatures() -> None:
    """Verify endpoint methods are accessible for IDE inspection."""
    assert hasattr(TypedSyncClient, "get_todos")
    assert hasattr(TypedSyncClient, "get_todo_by_id")
    assert hasattr(TypedSyncClient, "post_todo")

    assert "get_todos" in dir(TypedSyncClient)
    assert "get_todo_by_id" in dir(TypedSyncClient)
    assert "post_todo" in dir(TypedSyncClient)
