#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Generator

import pytest
from http_test import HTTPTestServer


@pytest.fixture(name="test_server", scope="module")
def test_server_fixture() -> Generator[HTTPTestServer, None, None]:
    with HTTPTestServer() as server:
        yield server
