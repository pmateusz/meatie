# Meatie: Generate methods for calling REST APIs using type hints

[![GitHub Test Badge][1]][2] [![codecov.io][3]][4] [![pypi.org][5]][6] [![versions][7]][8]
[![downloads][9]][10] [![License][11]][12]

[1]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml/badge.svg "GitHub CI Badge"

[2]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml "GitHub Actions Page"

[3]: https://codecov.io/gh/pmateusz/meatie/branch/master/graph/badge.svg?branch=master "Coverage Badge"

[4]: https://codecov.io/gh/pmateusz/meatie?branch=master "Codecov site"

[5]: https://img.shields.io/pypi/v/meatie.svg "Pypi Latest Version Badge"

[6]: https://pypi.python.org/pypi/meatie "Pypi site"

[7]:https://img.shields.io/pypi/pyversions/meatie.svg

[8]: https://github.com/pmateusz/meatie

[9]: https://static.pepy.tech/badge/meatie

[10]: https://pepy.tech/project/meatie

[11]: https://img.shields.io/github/license/pmateusz/meatie "License Badge"

[12]: https://opensource.org/license/bsd-3-clause "License"

Meatie is a Python metaprogramming library that eliminates the need for boilerplate code when integrating with REST
APIs. The library generates code for calling a REST API based on method signatures annotated with type hints. Meatie
abstracts away mechanics related to HTTP communication, such as building URLs, encoding query parameters, parsing, and
dumping Pydantic models. With some modest additional configuration effort, generated HTTP clients offer rate limiting,
retries, and caching. Meatie is compatible with Pydantic V1 and V2. Python 3.9 is the minimum officially supported
version.

## TL;DR

Generate HTTP clients using type annotations.

```python
from typing import Annotated
from aiohttp import ClientSession
from meatie.aio import ApiRef, Client, endpoint
from meatie_example.store import Product, Basket, BasketQuote  # Pydantic models


class OnlineStore(Client):
    def __init__(self, session: ClientSession) -> None:
        super().__init__(session)

    @endpoint("/api/v1/products")
    async def get_products(self) -> list[Product]:
        # Sends an HTTP GET request and parses response's body using Pydantic to list[Product]
        ...

    @endpoint("/api/v1/quote/request")
    async def post_request_quote(self, basket: Annotated[Basket, ApiRef("body")]) -> BasketQuote:
        # Dumps a Pydantic model :basket to JSON and sends it as payload of an HTTP POST request.
        ...

    @endpoint("/api/v1/quote/{quote_id}/accept")
    async def post_accept_quote(self, quote_id: int) -> None:
        # URLs can reference method parameters. Parameters not referenced in the URL are sent as HTTP query params.
        ...
```

### Cache

Cache result for given TTL.

```python
from aiohttp import ClientSession
from meatie.aio import Client, endpoint, Cache, HOUR
from meatie_example.store import Product


class OnlineStore(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://test.store.com"))

    @endpoint("/api/v1/products", Cache(ttl=4 * HOUR))
    async def get_products(self) -> list[Product]:
        ...
```

A cache key is built based on the URL path and query parameters. It does not include the scheme and the network
location.

By default, every instance of an HTTP client uses an independent cache. The behavior can be changed in the endpoint
definition to share cached results across all instances of the same HTTP client class.

```python
@endpoint("/api/v1/products", Cache(ttl=4 * HOUR, shared=True))
async def get_products(self) -> list[Product]:
    ...
```

### Rate Limiting

Commercial-grade publicly available REST APIs enforce rate limit policies (a.k.a. throttling) to slow down fast
consumers. Consequently, a system can maintain a fair allocation of computational resources across all consumers. Rate
limit policies define the cost of calling an endpoint using credits (or tokens). Every consumer has some credit
allowance and replenishment rate. For instance, 300 credits constitute the initial budget, and one new credit unit
becomes available every second. The server rejects API calls that exceed the rate limit. Disobedient clients who
constantly violate rate limits are punished via a temporary lockout.

Meatie supports a rate limit policy definition in the endpoint description. Meatie delays the HTTP requests that exceed
the rate limit. Triggering the rate limit by the server has much more severe consequences than delaying a call on the
client that otherwise is very likely to be rejected anyway.

```python
from aiohttp import ClientSession
from meatie.aio import Client, endpoint, Limit, Limiter, Rate
from meatie_example.store import Product


class OnlineStore(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://test.store.com"),
                         limiter=Limiter(rate=Rate(tokens_per_sec=1), capacity=300))

    @endpoint("/api/v1/products", Limit(tokens=30))
    async def get_products(self) -> list[Product]:
        ...
```

### Retry

The retry mechanism is an inevitable part of a robust error-handling strategy for dealing with intermittent errors. In
the scope of HTTP integrations, reasonable candidates for a retry are HTTP response errors status 429 (Too Many
Requests) and network connectivity issues (i.e., timeout, connection reset).

Meatie enables a retry strategy in the endpoint definition and allows further customization of the strategy by plugging
in third-party functions. They control whether to make a retry attempt, for how long to wait between retries, which
sleep function to use for waiting, and whether to abort further retries.

```python
from aiohttp import ClientSession
from meatie.aio import (
    Client,
    endpoint,
    Retry,
    WaitExponential,
    StopAfter,
    RetryOnServerConnectionError,
    RetryOnTooManyRequestsStatus
)
from meatie_example.store import Product


class OnlineStore(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://test.store.com"))

    @endpoint("/api/v1/products", Retry(retry=RetryOnServerConnectionError | RetryOnTooManyRequestsStatus,
                                        wait=WaitExponential(),
                                        stop=StopAfter(attempts=5)))
    async def get_products(self) -> list[Product]:
        ...
```

Meatie provides some standard wait strategies, retry conditions, and stop conditions, such
as: `RetryOnStatusCode(status: int)` or `RetryOnExceptionType(exc_type: type[BaseException])`.

### Private Endpoints

Some REST API endpoints are private, i.e., calling them requires prior authentication to obtain a token that should be
present in the HTTP headers of a request. An alternative approach popular for backend-side integration is to sign a
request using a secret only authorized clients should know.

Meatie simplifies integration with endpoints that require authentication by marking as `Private`. Before calling such an
endpoint, the Meatie executes the `authenticate` method the HTTP client should implement. The implemementation should
obtain a token and add it to the HTTP headers of the pending request. Alternatively, the `authenticate` method should
sign the pending request using API keys.

The example below illustrates signing requests to Binance private endpoints using API keys.

```python
import hashlib
import hmac
import time
import urllib.parse
from decimal import Decimal
from typing import Optional

from aiohttp import ClientSession
from meatie.aio import (
    Client,
    Private,
    Request,
    endpoint,
)

from pydantic import BaseModel, Field, AnyHttpUrl


class AssetWalletBalance(BaseModel):
    activate: bool
    balance: Decimal
    wallet_name: str = Field(alias="walletName")


class Binance(Client):
    def __init__(
            self,
            api_key: Optional[str] = None,
            secret: Optional[str] = None,
    ) -> None:
        super().__init__(
            ClientSession(base_url="https://api.binance.com"),
        )
        self.api_key = api_key
        self.secret = secret

    async def authenticate(self, request: Request) -> None:
        if self.api_key is None:
            raise RuntimeError("'api_key' is None")

        if self.secret is None:
            raise RuntimeError("'secret' is None")

        request.headers["X-MBX-APIKEY"] = self.api_key
        request.query_params["timestamp"] = int(time.monotonic() * 1000)

        query_params = urllib.parse.urlencode(request.query_params)
        raw_signature = hmac.new(
            self.secret.encode("utf-8"), query_params.encode("utf-8"), hashlib.sha256
        )
        signature = raw_signature.hexdigest()
        request.query_params["signature"] = signature

    @endpoint("/sapi/v1/asset/wallet/balance", Private)
    async def get_asset_wallet_balance(self) -> list[AssetWalletBalance]:
        ...
```

### Endpoint Customizations

#### Pydantic integration is optional

Pydantic integration is entirely optional. Projects that don't use Pydantic might instead process the response body as
string, binary, or JSON. Pydantic integration becomes available when 1) Pydantic library is installed and 2) the return
type of a method marked with `@endpoint` decorator can be parsed to a Pydantic model. A type can be parsed to a Pydantic
if it inherits from BaseModel, is a data class, or a typed dictionary. The rule extends to container types. A container
could also be a Sequence of Pydantic convertible items or a Mapping in with Pydantic convertible type as values.

Return `aiohttp.ClientResponse` directly.

```python
from aiohttp import ClientResponse


@endpoint("/api/v1/orders")
async def get_orders(self) -> ClientResponse:
    ...
```

Return HTTP response payload as `bytes`.

```python
@endpoint("/api/v1/orders")
async def get_orders(self) -> bytes:
    ...
```

Return HTTP response payload as text.

```python
@endpoint("/api/v1/orders")
async def get_orders(self) -> str:
    ...
```

Return HTTP response as JSON.

```python
@endpoint("/api/v1/orders")
async def get_orders(self) -> list:
    ...
```

#### Rename query parameters

It might be more convenient to use a different name for a method parameter than the query parameter name defined by the
REST
API.

```python
from typing import Annotated
from meatie.aio import ApiRef


@endpoint("/api/v1/orders")
async def get_orders(self, since_ms: Annotated[int, ApiRef("since")]) -> list[dict]:
    ...
```

#### Define the HTTP method

There is no need to use HTTP methods as prefixes.

```python
@endpoint("/api/v1/orders", method="GET")
async def list_orders(self) -> list[dict]:
    ...
```

#### Preprocess HTTP requests or postprocess HTTP responses

Cache, Limit, Private, and Retry are middleware for processing HTTP requests and postprocessing HTTP responses. Meatie
internal architecture was designed to simplify extension by third-party middleware, without the need to modify the core
library. We leave this topic for self-study by an interested reader. A good starting point is a code review of
the `meatie.aio.option.limit` package.
