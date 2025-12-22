#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Annotated, Any

import pytest

from meatie import api_ref, endpoint
from meatie_aiohttp import Client


@dataclass
class Todo:
    user_id: int
    id: int
    title: str
    completed: bool


@dataclass
class DateRange:
    start: str
    end: str


def bool_formatter(value: bool) -> str:
    return str(value).lower()


def todo_formatter(value: Todo) -> dict[str, Any]:
    """Convert Todo to dict with userId alias."""
    data = asdict(value)
    data["userId"] = data.pop("user_id")
    return data


def date_formatter(value: str) -> str:
    """Format date string to ISO format."""
    return value.replace("/", "-")


def date_range_marshaller(value: DateRange) -> dict[str, str]:
    """Unwrap DateRange into multiple query params."""
    return {"start_date": value.start, "end_date": value.end}


@pytest.mark.asyncio()
async def test_query_param_formatted_with_future_annotations(mock_tools) -> None:
    """Test that query parameter formatter is applied when using future annotations."""
    # GIVEN
    session = mock_tools.session_with_json_response(json=[])

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/users/{user_id}/todos")
        async def get_todos_by_user(
            self, user_id: int, completed: Annotated[bool, api_ref(fmt=bool_formatter)]
        ) -> list[Any]: ...

    # WHEN
    async with TestClient() as client:
        await client.get_todos_by_user(1, completed=True)

    # THEN - formatter should convert True -> "true"
    session.request.assert_awaited_once_with("GET", "/users/1/todos", params={"completed": "true"})


@pytest.mark.asyncio()
async def test_body_param_formatted_with_future_annotations(mock_tools) -> None:
    """Test that body parameter formatter is applied when using future annotations."""
    # GIVEN
    todo = Todo(user_id=1, id=201, title="test", completed=False)
    session = mock_tools.session_with_json_response(json={"userId": 1, "id": 201, "title": "test", "completed": False})

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/todos")
        async def post_todo(self, todo: Annotated[Todo, api_ref("body", fmt=todo_formatter)]) -> Any: ...

    # WHEN
    async with TestClient() as client:
        await client.post_todo(todo)

    # THEN - formatter should convert Todo -> dict with aliases
    session.request.assert_awaited_once_with(
        "POST",
        "/todos",
        json={"userId": 1, "id": 201, "title": "test", "completed": False},
    )


@pytest.mark.asyncio()
async def test_path_param_formatted_with_future_annotations(mock_tools) -> None:
    """Test that path parameter formatter is applied when using future annotations."""
    # GIVEN
    session = mock_tools.session_with_json_response(json=[])

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/reports/{date}/summary")
        async def get_report(self, date: Annotated[str, api_ref(fmt=date_formatter)]) -> list[Any]: ...

    # WHEN
    async with TestClient() as client:
        await client.get_report("2024/12/22")

    # THEN - formatter should convert 2024/12/22 -> 2024-12-22
    session.request.assert_awaited_once_with("GET", "/reports/2024-12-22/summary")


@pytest.mark.asyncio()
async def test_unwrap_param_with_future_annotations(mock_tools) -> None:
    """Test that unwrap parameter (marshaller) is applied when using future annotations."""
    # GIVEN
    session = mock_tools.session_with_json_response(json=[])

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/events")
        async def get_events(
            self, date_range: Annotated[DateRange, api_ref(unwrap=date_range_marshaller)]
        ) -> list[Any]: ...

    # WHEN
    async with TestClient() as client:
        await client.get_events(DateRange(start="2024-01-01", end="2024-12-31"))

    # THEN - marshaller should unwrap DateRange into two params
    session.request.assert_awaited_once_with(
        "GET", "/events", params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
    )


@pytest.mark.asyncio()
async def test_simple_param_rename_with_future_annotations(mock_tools) -> None:
    """Test that simple parameter renaming works with future annotations (no fmt/unwrap)."""
    # GIVEN
    session = mock_tools.session_with_json_response(json=[])

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/users")
        async def get_users(
            self, sort_by: Annotated[str, api_ref("orderBy")], limit: Annotated[int, api_ref("maxResults")]
        ) -> list[Any]: ...

    # WHEN
    async with TestClient() as client:
        await client.get_users(sort_by="name", limit=10)

    # THEN - params should be renamed
    session.request.assert_awaited_once_with("GET", "/users", params={"orderBy": "name", "maxResults": 10})


@pytest.mark.asyncio()
async def test_multiple_formatted_params_with_future_annotations(mock_tools) -> None:
    """Test that multiple annotated params with formatters work together with future annotations."""
    # GIVEN
    session = mock_tools.session_with_json_response(json=[])

    class TestClient(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/data/{id}/records")
        async def get_records(
            self,
            id: Annotated[int, api_ref(fmt=hex)],
            active: Annotated[bool, api_ref(fmt=bool_formatter)],
            page: Annotated[int, api_ref("pageNumber")],
        ) -> list[Any]: ...

    # WHEN
    async with TestClient() as client:
        await client.get_records(id=255, active=True, page=2)

    # THEN - all formatters/renames should be applied
    session.request.assert_awaited_once_with("GET", "/data/0xff/records", params={"active": "true", "pageNumber": 2})
