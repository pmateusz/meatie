#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock

from aiohttp import ClientResponse, ClientResponseError, ClientSession, RequestInfo


class AiohttpMockTools:
    @staticmethod
    def json_response(json: Any, status: int = HTTPStatus.OK) -> Mock:
        return Mock(spec=ClientResponse, status=status, json=AsyncMock(return_value=json))

    @staticmethod
    def json_client_response_error(status: int) -> Mock:
        json = AsyncMock(side_effect=ClientResponseError(Mock(spec=RequestInfo), (), status=status))
        return Mock(spec=ClientResponse, status=status, json=json)

    @staticmethod
    def session_with_json_response(json: Any, status: int = HTTPStatus.OK) -> Mock:
        response = AiohttpMockTools.json_response(json, status)
        return AiohttpMockTools.session_wrap_response(response)

    @staticmethod
    def session_with_json_client_response_error(status: int) -> Mock:
        response = AiohttpMockTools.json_client_response_error(status)
        return AiohttpMockTools.session_wrap_response(response)

    @staticmethod
    def session_wrap_response(response: Mock) -> Mock:
        return Mock(spec=ClientSession, request=AsyncMock(return_value=response))
