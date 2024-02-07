#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from meatie import Response


class _NoneAdapter:
    @staticmethod
    async def from_response(_: Response) -> None:  # pragma: no cover
        return None

    @staticmethod
    def to_json(_: None) -> None:  # pragma: no cover
        return None


AsyncNoneAdapter = _NoneAdapter()
