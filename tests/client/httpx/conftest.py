#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import pytest

httpx = pytest.importorskip("httpx")

from mock_tools.httpx import MockTools  # noqa: E402


@pytest.fixture(name="mock_tools", scope="session")
def mock_tools_fixture() -> MockTools:
    return MockTools()