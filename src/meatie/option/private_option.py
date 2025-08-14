#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Union

from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.types import PT, T

__all__ = ["private"]


class PrivateOption:
    """Include additional information in the HTTP request before calling the API endpoint.

    Instructs Meatie library to call the `authenticate` method of the client instance with the HTTP request as the argument.

    Popular use cases are to set the `Authorization` header or sign the HTTP request using API keys before calling the API endpoint.
    """

    def __call__(
        self,
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]],
    ) -> None:
        """Apply the private option to the endpoint descriptor."""
        if isinstance(descriptor, EndpointDescriptor):
            return self.__sync_descriptor(descriptor)
        return self.__async_descriptor(descriptor)

    @property
    def priority(self) -> int:
        """Returns: the priority of the private operator."""
        return 80

    def __sync_descriptor(self, descriptor: EndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(self.priority, _operator)

    def __async_descriptor(self, descriptor: AsyncEndpointDescriptor[PT, T]) -> None:
        descriptor.register_operator(self.priority, _async_operator)


private = PrivateOption()


def _operator(ctx: Context[T]) -> T:
    ctx.client.authenticate(ctx.request)
    return ctx.proceed()


async def _async_operator(ctx: AsyncContext[T]) -> T:
    await ctx.client.authenticate(ctx.request)
    return await ctx.proceed()
