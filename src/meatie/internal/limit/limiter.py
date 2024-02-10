#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


import time as sys_time
from typing import Optional

from meatie import Time

from . import Rate, Reservation, Tokens


class Limiter:
    __slots__ = ("rate", "capacity", "__last_tokens", "__last_time")

    def __init__(
        self,
        rate: Rate,
        capacity: Tokens,
        init_tokens: Optional[Tokens] = None,
        init_time: Optional[Time] = None,
    ) -> None:
        self.rate = rate
        self.capacity = capacity
        self.__last_tokens = init_tokens if init_tokens is not None else capacity
        self.__last_time = init_time if init_time is not None else sys_time.monotonic()

    def reserve_now(self, tokens: Tokens) -> Reservation:
        return self.reserve_at(sys_time.monotonic(), tokens)

    def reserve_at(self, time: Time, tokens: Tokens) -> Reservation:
        if tokens > self.capacity:
            raise ValueError(
                f"amount of requested tokens ({tokens}) exceed the limit ({self.capacity})"
            )

        available = self.__advance_until(time)
        remaining = available - tokens

        if remaining < 0:
            wait_duration = self.rate.duration_from_tokens(-remaining)
        else:
            wait_duration = 0.0

        result = Reservation(ready_at=time + wait_duration, tokens=tokens)
        self.__last_time = time
        self.__last_tokens = remaining
        return result

    def __advance_until(self, time: Time) -> Time:
        last_time = self.__last_time
        if time < last_time:
            last_time = time

        duration = time - last_time
        delta = self.rate.tokens_from_duration(duration)
        tokens = self.__last_tokens + delta
        if tokens > self.capacity:
            return self.capacity
        return tokens
