#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.types import PT, ResponseBodyType

__all__ = ["private"]


class PrivateOption:
    __PRIORITY = 50

    def __call__(self, descriptor: EndpointDescriptor[PT, ResponseBodyType]) -> None:
        descriptor.register_operator(PrivateOption.__PRIORITY, PrivateOption.__operator)

    @staticmethod
    def __operator(ctx: Context[ResponseBodyType]) -> ResponseBodyType:
        ctx.client.authenticate(ctx.request)
        return ctx.proceed()


private = PrivateOption()
