#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from meatie import INF, Duration

from . import Tokens


class Rate:
    max: "Rate"
    __slots__ = ("__tokens_per_sec",)

    def __init__(self, tokens_per_sec: float) -> None:
        if tokens_per_sec <= 0:
            raise ValueError("'tokens_per_sec' must be positive")

        self.__tokens_per_sec = tokens_per_sec

    def duration_from_tokens(self, tokens: Tokens) -> Duration:
        return tokens / self.__tokens_per_sec

    def tokens_from_duration(self, duration: Duration) -> Tokens:
        return self.__tokens_per_sec * duration


Rate.max = Rate(INF)
