# Getting Started

This guide will walk you through creating your first API client with Meatie.
For a general overview of Meatie and its features, see the
[home page](./index.md).

## Installation

For this guide, we will use the `httpx` library as the HTTP client. We will
also use the `pydantic` library for defining the data models. To install the
required libraries, run the following command:

```bash
pip install meatie[httpx] pydantic
```

Using the `[httpx]` extra will install the `httpx` backend for Meatie. This
ensures the compatibility between `meatie` and the specific version of `httpx`.

!!! note

    If you want to learn how to use Meatie with different HTTP clients, check
    out the [Backends section](./backends/overview.md).

## Quick Start

We will create a simple client for the
[JSONPlaceholder](https://jsonplaceholder.typicode.com/) API. We will use it to
get some posts. First, we need to define a pydantic model for the post. The
JSONPlaceholder API returns the following JSON object for a post:

```json
{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
}
```

Using this information, we can define the `Post` model:

```python
from pydantic import BaseModel

class Post(BaseModel):
    userId: int
    id: int
    title: str
    body: str
```

Next, we will create the client for the JSONPlaceholder API. As mentioned
above, we will use the `httpx` library as a backend. Let's create the
boilerplate to define a client:

```python
import httpx
from meatie import endpoint
from meatie_httpx import Client

class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(httpx.Client(base_url="https://jsonplaceholder.typicode.com"))
```

Now, defining the endpoints is straightforward. We will create a method to get
a post by number:

```python
    @endpoint("/posts/{post_id}") # (1)!
    def get_post(self, post_id: int) -> Post: ... # (2)!
```

1. Path parameters are defined using curly braces, similar to FastAPI
2. The `...` (ellipsis) is a placeholder - Meatie will generate the method body
   and anything inside will be discarded.

That's it! We have defined a client for the JSONPlaceholder API. We can now use
it to get a post by its number:

```python
with JsonPlaceholderClient() as client:
    post = client.get_post(1)
    print(post)
```

Using the client in a `with` block ensures that the client is properly closed
after the block is executed, preventing any resource leaks.

Let's add another endpoint to the client to get all posts:

```python
    @endpoint("/posts")
    def get_posts(self) -> list[Post]: ...
```

Now, we can get all posts using the following code:

```python
with JsonPlaceholderClient() as client:
    posts: list[Post] = client.get_posts()
    for post in posts:
        print(post)
```

Let's finish the client by adding a method to create a new post. For that, we need to create some new models:

```python
class PostCreate(BaseModel):
    userId: int
    title: str
    body: str

class PostCreateResponse(BaseModel):
    id: int
```

Now, we can add the method to the client:

```python
    @endpoint("/posts", method="POST") # (1)!
    def create_post(self, post: PostCreate) -> PostCreateResponse: ...
```

1. Usually, the method is inferred from the function name, using a prefix (like
   `get_`, `post_`, etc.). However, when the request method cannot be inferred,
   You can specify it using the `method` parameter.

??? example "Full Code"
    ```python linenums="1"
    import httpx
    from meatie import endpoint
    from meatie_httpx import Client
    from pydantic import BaseModel

    class Post(BaseModel):
        userId: int
        id: int
        title: str
        body: str

    class PostCreate(BaseModel):
        userId: int
        title: str
        body: str

    class PostCreateResponse(BaseModel):
        id: int

    class JsonPlaceholderClient(Client):
        def __init__(self) -> None:
            super().__init__(httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

        @endpoint("/posts/{post_id}")
        def get_post(self, post_id: int) -> Post: ...

        @endpoint("/posts")
        def get_posts(self) -> list[Post]: ...

        @endpoint("/posts", method="POST")
        def create_post(self, post: PostCreate) -> PostCreateResponse: ...

    with JsonPlaceholderClient() as client:
        post = client.get_post(1)
        print(post)
        print("-" * 80)
        posts = client.get_posts()
        for post in posts[:10]:
            print(post)
        print("-" * 80)
        post_id = client.create_post(PostCreate(userId=1, title="New Post", body="This is a new post."))
        print(post_id)
    ```

## Next Steps

That concludes our quick start guide. You should now have a basic understanding
of what Meatie is and how to use it to create API clients really simply. Still,
this is just the tip of the iceberg. There is much more to learn about Meatie.
Here are some suggestions on where to go and what to do next:

!!! tip
    Check out our [advanced topics](./advanced/overview.md) section to learn
    more about things like authentication, error handling, custom serialization
    and more.

!!! tip
    Interested in how Meatie works under the hood? Check out the
    [architecture](./internals/architecture.md) section, learn about the
    [request lifecycle](./internals/request_lifecycle.md), or learn about the
    [endpoint descriptor](./internals/endpoint_descriptor.md).

!!! question
    Have a question or need help? Shoot us a message vie GitHub
    [issues](https://github.com/pmateusz/meatie/issues) or
    [discussions](https://github.com/pmateusz/meatie/discussions)
