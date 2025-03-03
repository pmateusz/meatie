![Header Image](https://repository-images.githubusercontent.com/735134836/df6752b8-38fa-4550-968e-cd2eda4adb37)

[![GitHub Test Badge][1]][2] [![Docs][3]][4] [![codecov.io][5]][6] [![pypi.org][7]][8] [![versions][9]][10]
[![downloads][11]][12] [![License][13]][14]

[1]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml/badge.svg "GitHub CI Badge"

[2]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml "GitHub Actions Page"

[3]: https://readthedocs.org/projects/meatie/badge/?version=latest "Docs Latest Version Badge"

[4]: https://meatie.readthedocs.io/

[5]: https://codecov.io/gh/pmateusz/meatie/branch/master/graph/badge.svg?branch=master "Coverage Badge"

[6]: https://codecov.io/gh/pmateusz/meatie?branch=master "Codecov site"

[7]: https://img.shields.io/pypi/v/meatie.svg "Pypi Latest Version Badge"

[8]: https://pypi.python.org/pypi/meatie "Pypi site"

[9]:https://img.shields.io/pypi/pyversions/meatie.svg

[10]: https://github.com/pmateusz/meatie

[11]: https://static.pepy.tech/badge/meatie

[12]: https://pepy.tech/project/meatie

[13]: https://img.shields.io/github/license/pmateusz/meatie "License Badge"

[14]: https://opensource.org/license/bsd-3-clause "License"

Meatie is a Python library that simplifies the implementation of REST API clients. The library generates code for
calling REST endpoints based on method signatures annotated with type hints. Meatie takes care of mechanics related to
HTTP communication, such as building URLs, encoding query parameters, and serializing the body in the HTTP requests and
responses. Rate limiting, retries, and caching are available with some modest extra setup.

Meatie works with all major HTTP client libraries (request, httpx, aiohttp) and offers seamless integration with
Pydantic (v1 and v2). The minimum officially supported version is Python 3.9.

If you want to get started quickly, check out our [Getting Started Guide](getting_started.md).
