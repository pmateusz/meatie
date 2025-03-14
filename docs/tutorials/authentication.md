# Authentication

In this tutorial, you will learn how to include additional information in HTTP requests using the Meatie library. A common use case is to provide an `Authorization` header for authentication purposes.

Before proceeding, ensure you have completed the [Getting Started](./getting_started.md) tutorial.

## Steps

1. Copy the following code sample and save it as a `tutorial.py` Python script.
    ```py
        from typing import Annotated
    in HTTP
        import httpx
        from meatie import endpoint, api_ref
        from meatie_httpx import Client
        from pydantic import BaseModel

        class User(BaseModel):
            username: str

        class JsonPlaceholderClient(Client):

            def __init__(self) -> None:
                super().__init__(
                    httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

            @endpoint("/users")
            def get_users(self, username: str = None) -> list[User]:
                ...

            @endpoint("/users", method="POST")
            def create_user(self, user: Annotated[User, api_ref("body")]) -> User:
                ...

            @endpoint("/users/{id}")
            def delete_user(self, id: str) -> None:
                ...


        if __name__ == '__main__':

            with JsonPlaceholderClient() as client:
                users = client.get_users(username="Bret")
                for user in users:
                    print(user.username)

            print("ok")
    ```

1. Modify the script to include a `Bearer` token `meatie` in the `Authorization` header for every HTTP request.

    ```py hl_lines="1 3 16 20 24 28 29 30"
        from typing import Annotated, override
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

    In this modification, we override the `authenticate` method to include `Bearer bWVhdGll` in the `Authorization` header. This method is invoked before sending an HTTP request from any endpoint marked as `private`.

    ## Next Steps

    You have learned everything you need to know to call REST API endpoints using the Meatie library! We encourage you to take a break from reading the documentation and build your muscle memory through practice. We are actively working on tutorials to cover more advanced topics such as rate limiting, caching, error handling, and retries.