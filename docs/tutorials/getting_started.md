# Getting Started

You'll learn how to implement a REST API client using the Meatie library. By completing this tutorial, you will learn how to:

* Install the Meatie library with the HTTPX backend
* Call a GET endpoint with an optional query parameter
* Call a POST endpoint with a request body
* Call a DELETE endpoint with a path parameter
* Use Pydantic to handle the serialization of HTTP requests and responses

The client will send HTTP requests to a mock REST API available at `https://jsonplaceholder.typicode.com`. This is a free online service that requires no additional setup.

Let's get started!

## Steps

1. Install the Meatie library with the HTTPX library as an extra dependency.

    ```shell
    pip install "meatie[httpx]"
    ```

2. Copy the following code sample and save it as a `tutorial.py` Python script.

    ```py
    import httpx
    from meatie_httpx import Client

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            pass

        print("ok")
    ```

3. Run the Python script and ensure it prints `ok` as the output.

    ```shell
    python tutorial.py
    ```

4. Call the `GET /users` endpoint to fetch the list of users and print their usernames to the console.

    ```py hl_lines="2 11 12 13 19 20 21"
    import httpx
    from meatie import endpoint
    from meatie_httpx import Client

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/users")
        def get_users() -> list:
            ...


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users()
            for user in users:
                print(f"{user['username']}")

        print("ok")
    ```

5. Add support for filtering by username using the query parameter `username`.

    ```py hl_lines="13 20"
    import httpx
    from meatie import endpoint
    from meatie_httpx import Client


    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/users")
        def get_users(self, username: str = None) -> list:
            ...


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users(username="Bret")
            for user in users:
                print(f"{user['username']}")

        print("ok")
    ```

6. Call the POST `/users` endpoint with the request body `{"username": "John"}` to create a new user.

    ```py hl_lines="1 4 17 18 19 29 30"
    from typing import Annotated

    import httpx
    from meatie import endpoint, api_ref
    from meatie_httpx import Client

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/users")
        def get_users(self, username: str = None) -> list:
            ...

        @endpoint("/users", method="POST")
        def create_user(self, user: Annotated[api_ref("body"), dict]) -> dict:
            ...


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users(username="Bret")
            for user in users:
                print(f"{user['username']}")

            new_user = client.create_user({"username": "John"})
            print(new_user)


        print("ok")
    ```

7. Call the DELETE `/users/7` endpoint to delete the user with ID `7`.


    ```py hl_lines="21 22 23 36"
    from typing import Annotated

    import httpx
    from meatie import endpoint, api_ref
    from meatie_httpx import Client

    class JsonPlaceholderClient(Client):

        def __init__(self) -> None:
            super().__init__(
                httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/users")
        def get_users(self, username: str = None) -> list:
            ...

        @endpoint("/users", method="POST")
        def create_user(self, user: Annotated[api_ref("body"), dict]) -> dict:
            ...

        @endpoint("/users/{id}")
        def delete_user(self, id: int) -> None:
            ...


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users(username="Bret")
            for user in users:
                print(f"{user['username']}")

            new_user = client.create_user({"username": "John"})
            print(new_user)

            client.delete_user(7)


        print("ok")
    ```

8. Install the `pydantic` library.

    ```shell
    pip install pydantic
    ```

9. Replace untyped data models in the `GET` and `POST` endpoints with a Pydantic model.

    ```py hl_lines="5 7 8 17 21 34 36"
    from typing import Annotated
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
        def delete_user(self, id: int) -> None:
            ...


    if __name__ == '__main__':

        with JsonPlaceholderClient() as client:
            users = client.get_users(username="Bret")
            for user in users:
                print(user.username)

            new_user = client.create_user(User(username="John"))
            print(new_user)

            client.delete_user(7)


        print("ok")
    ```

Congratulations on completing the tutorial! You are now ready to implement your own REST API client using Meatie.

## Next Step: Authentication

Some REST API endpoints may be private, meaning they are restricted for authenticated users only. Authentication in the REST API is typically implemented based on the `Authorization` header, which the client must provide in the HTTP request. Proceed to the [Authentication](./authentication.md) tutorial to add this feature to the existing client.
