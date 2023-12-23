#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import json
from typing import Any, Callable, Optional, Protocol


class Response(Protocol):
    @property
    def status(self) -> int:
        ...

    async def read(self) -> bytes:
        ...

    async def text(self, encoding: Optional[str] = None) -> str:
        ...

    async def json(
        self, *, encoding: Optional[str] = None, loads: Callable[[str], Any] = json.loads
    ) -> dict[str, Any]:
        ...
