#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from functools import singledispatchmethod

from meatie import Context, EndpointDescriptor
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.types import PT, ResponseBodyType

__all__ = ["private"]


class PrivateOption:
    __PRIORITY = 50

    @singledispatchmethod
    def __call__(self, descriptor: EndpointDescriptor[PT, ResponseBodyType]) -> None:
        raise NotImplementedError()

    @__call__.register
    def __sync_call(self, descriptor: EndpointDescriptor[PT, ResponseBodyType]) -> None:
        descriptor.register_operator(PrivateOption.__PRIORITY, operator)

    @__call__.register
    def __async_call(self, descriptor: AsyncEndpointDescriptor[PT, ResponseBodyType]) -> None:
        descriptor.register_operator(PrivateOption.__PRIORITY, async_operator)


def operator(ctx: Context[ResponseBodyType]) -> ResponseBodyType:
    ctx.client.authenticate(ctx.request)
    return ctx.proceed()


async def async_operator(ctx: AsyncContext[ResponseBodyType]) -> ResponseBodyType:
    await ctx.client.authenticate(ctx.request)
    return await ctx.proceed()


private = PrivateOption()
