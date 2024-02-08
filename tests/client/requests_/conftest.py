#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from tests.client.requests_.mock_tools import MockTools
import pytest


@pytest.fixture(name="mock_tools", scope="session")
def mock_tools_fixture() -> MockTools:
    return MockTools()
