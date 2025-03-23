# Rate Limiting

In this tutorial, you will learn how to manage HTTP requests to avoid exceeding API rate limits.

You will extend the Python script developed in the [Authentication](./authentication.md) tutorial to enforce a rate limit of 2 requests per second.

## Steps

1. Copy the following code sample and save it as a `tutorial.py` Python script.
    ```py
    from typing import Annotated, override
    from time import time
    import httpx
    from meatie import Request, api_ref, endpoint, private
    from meatie_httpx import Client
    from pydantic import BaseModel

    class User(BaseModel):
        username: str

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/users", private)
        def get_users(self, username: str = None) -> list[User]:
            ...

        @endpoint("/users", private, method="POST")
        def create_user(self, user: Annotated[User, api_ref("body")]) -> User:
            ...

        @endpoint("/users/{id}", private)
        def delete_user(self, id: str) -> None:
            ...

        @override
        def authenticate(self, request: Request) -> None:
            request.headers["Authorization"] = "Bearer bWVhdGll"


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users(username="Bret")
            for user in users:
                print(user.username)

        print("ok")
    ```

2. Configure the rate limiter to enforce a limit of two requests per second.

    ```py hl_lines="3 16 18 22 26 30"
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

Meatie comes with a built-in leaky bucket rate limiter implementation. In this example, we configured both the token replenishment rate and capacity. Note that each endpoint subject to rate limiting must define how many tokens are consumed per API call using the `limit()` function. Without this specification, throttling will not be enabled.

## Next Steps

It's inefficient to consume rate limiter tokens when calling API endpoints that return the same data repeatedly. In the next section, we will explore how to enable [caching HTTP responses](./caching.md) to optimize your API usage.
