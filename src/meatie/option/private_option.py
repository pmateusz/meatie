#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Union

from meatie import Context, EndpointDescriptor
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.types import PT, T

__all__ = ["private"]


class PrivateOption:
    """
    Include additional information in the request, i.e., `Authorization` header, before calling the API endpoint.
    """

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    @property
    def priority(self) -> int:
        return 80

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(self.priority, operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(self.priority, async_operator)


def operator(ctx: Context[T]) -> T:
    ctx.client.authenticate(ctx.request)
    return ctx.proceed()


async def async_operator(ctx: AsyncContext[T]) -> T:
    await ctx.client.authenticate(ctx.request)
    return await ctx.proceed()


private = PrivateOption()
