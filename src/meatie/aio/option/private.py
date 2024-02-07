#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.types import PT, ResponseBodyType


class PrivateOption:
    __PRIORITY = 50

    def __call__(self, descriptor: AsyncEndpointDescriptor[PT, ResponseBodyType]) -> None:
        descriptor.register_operator(PrivateOption.__PRIORITY, PrivateOption.__operator)

    @staticmethod
    async def __operator(ctx: AsyncContext[ResponseBodyType]) -> ResponseBodyType:
        await ctx.client.authenticate(ctx.request)
        return await ctx.proceed()


Instance = PrivateOption()
