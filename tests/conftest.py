#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any
from unittest.mock import Mock

import pytest
from requests import Response, Session
from requests.exceptions import JSONDecodeError


class MockTools:
    @staticmethod
    def json_response(json: Any, status: int = HTTPStatus.OK) -> Mock:
        return Mock(spec=Response, status_code=status, json=Mock(return_value=json))

    @staticmethod
    def json_client_response_error(status: int) -> Mock:
        json = Mock(side_effect=JSONDecodeError("mock error", "mock json document", 0))
        return Mock(spec=Response, status_code=status, json=json)

    @staticmethod
    def session_with_json_response(json: Any, status: int = HTTPStatus.OK) -> Mock:
        response = MockTools.json_response(json, status)
        return MockTools.session_wrap_response(response)

    @staticmethod
    def session_with_json_client_response_error(status: int) -> Mock:
        response = MockTools.json_client_response_error(status)
        return MockTools.session_wrap_response(response)

    @staticmethod
    def session_wrap_response(response: Mock) -> Mock:
        return Mock(spec=Session, request=Mock(return_value=response))


@pytest.fixture(name="mock_tools", scope="session")
def mock_tools_fixture() -> MockTools:
    return MockTools()
