# Caching

In this tutorial, you will learn how to cache HTTP responses. This feature allows Meatie to skip querying HTTP endpoints and instead return cached data when available.

You will build upon the Python script developed in the [Rate Limiting](./rate_limiter.md) tutorial.

## Steps

1. Copy the following code sample and save it as a `tutorial.py` Python script.
    ```py
    from typing import Annotated, override
    from time import time
    import httpx
    from meatie import Limiter, Rate, Request, api_ref, endpoint, limit, private
    from meatie_httpx import Client
    from pydantic import BaseModel

    class User(BaseModel):
        username: str

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"),
                limiter=Limiter(Rate(tokens_per_sec=2), capacity=2))

        @endpoint("/users", private, limit(1))
        def get_users(self, username: str = None) -> list[User]:
            ...

        @endpoint("/users", private, limit(1), method="POST")
        def create_user(self, user: Annotated[User, api_ref("body")]) -> User:
            ...

        @endpoint("/users/{id}", limit(1), private)
        def delete_user(self, id: str) -> None:
            ...

        @override
        def authenticate(self, request: Request) -> None:
            request.headers["Authorization"] = "Bearer bWVhdGll"


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            for _ in range(5):
                print(time(), client.get_users(username="Bret"))


        print("ok")
    ```

2. Add caching functionality to the `get_users` endpoint. Set `ttl` to 5 minutes.

    ```py hl_lines="4 17 19"
    from typing import Annotated, override
    from time import time
    import httpx
    from meatie import Cache, Limiter, MINUTE, Rate, Request, api_ref, cache, endpoint, limit, private
    from meatie_httpx import Client
    from pydantic import BaseModel

    class User(BaseModel):
        username: str

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"),
                limiter=Limiter(Rate(tokens_per_sec=2), capacity=2),
                local_cache=Cache(max_size=100))

        @endpoint("/users", private, limit(1), cache(ttl=5 * MINUTE))
        def get_users(self, username: str = None) -> list[User]:
            ...

        @endpoint("/users", private, limit(1), method="POST")
        def create_user(self, user: Annotated[User, api_ref("body")]) -> User:
            ...

        @endpoint("/users/{id}", limit(1), private)
        def delete_user(self, id: str) -> None:
            ...

        @override
        def authenticate(self, request: Request) -> None:
            request.headers["Authorization"] = "Bearer bWVhdGll"


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            for _ in range(5):
                print(time(), client.get_users(username="Bret"))


        print("ok")
    ```

The cached responses are stored within the client instance. In this example, the cache is configured to store the 100 most recently used responses. Each cached response remains valid for 5 minutes.

## Next Steps

This concludes our tutorial series on Meatie's core features. We plan to add a tutorial on implementing retry mechanisms in the near future. Stay tuned for updates!