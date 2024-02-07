#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from meatie import AsyncContext
from meatie.aio import AsyncEndpointDescriptor
from meatie.internal.types import PT, T


class PrivateOption:
    __PRIORITY = 50

    def __call__(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(PrivateOption.__PRIORITY, PrivateOption.__operator)

    @staticmethod
    async def __operator(ctx: AsyncContext[T]) -> T:
        await ctx.client.authenticate(ctx.request)
        return await ctx.proceed()


Instance = PrivateOption()
