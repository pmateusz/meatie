import json
import urllib.parse
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse


class Handler(SimpleHTTPRequestHandler):
    def send_json(self, status_code: HTTPStatus, message: Any) -> None:
        if isinstance(message, str):
            json_data = message
        else:
            try:
                json_data = json.dumps(message)
            except Exception as exc:
                self.send_text(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    "Failed to serialize response: " + str(exc),
                )
                return

        self.send_bytes(status_code, "application/json", json_data.encode("utf-8"))

    def send_text(self, status_code: HTTPStatus, text: str) -> None:
        self.send_bytes(status_code, "text/plain", text.encode("utf-8"))

    def send_bytes(self, status_code: HTTPStatus, content_type: str, message: bytes) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def safe_content_length(self) -> Optional[int]:
        content_length_raw = self.headers.get("Content-Length", "0")
        try:
            return int(content_length_raw)
        except ValueError:
            self.send_text(
                HTTPStatus.BAD_REQUEST,
                f"Content length should be an integer: '{content_length_raw}'",
            )
            return None

    def safe_bytes(self) -> Optional[bytes]:
        content_length_opt = self.safe_content_length()
        if content_length_opt is None:
            return None

        try:
            return self.rfile.read(content_length_opt)
        except Exception as exc:
            self.send_text(HTTPStatus.BAD_REQUEST, "Failed to read request body: " + str(exc))
            return None

    def safe_text(self) -> Optional[str]:
        raw_body_opt = self.safe_bytes()
        if raw_body_opt is None:
            return None

        content_charset = self.headers.get_content_charset("utf-8")
        try:
            return raw_body_opt.decode(content_charset)
        except Exception as exc:
            self.send_text(HTTPStatus.BAD_REQUEST, "Failed to decode request body: " + str(exc))
            return None


RequestHandler = Callable[[Handler], None]


class StatusHandler:
    def __init__(self, status: HTTPStatus) -> None:
        self.status = status

    def __call__(self, handler: Handler) -> None:
        handler.send_response(self.status)
        handler.end_headers()


def echo_handler(handler: Handler) -> None:
    raw_body_opt = handler.safe_bytes()
    if raw_body_opt is None:
        return

    content_type = handler.headers.get_content_type()
    handler.send_bytes(HTTPStatus.OK, content_type, raw_body_opt)


def diagnostic_handler(handler: Handler) -> None:
    body_opt = handler.safe_text()
    if body_opt is None:
        return

    headers = {key: value for key, value in handler.headers.items()}
    try:
        url = urllib.parse.urlparse(handler.path)
    except Exception as exc:
        handler.send_text(HTTPStatus.BAD_REQUEST, "Failed to parse URL: " + str(exc))
        return

    response = {
        "path": url.path,
        "scheme": url.scheme,
        "params": url.params,
        "query": url.query,
        "fragment": url.fragment,
        "netloc": url.netloc,
        "headers": headers,
        "body": body_opt,
    }
    handler.send_json(HTTPStatus.OK, response)


def service_unavailable(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    request.wfile.write('{"error": "deployment in progress"}'.encode("utf-8"))


def emoji(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.end_headers()
    request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))


def ascii_emoji(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.send_header("Content-Type", "text/plain; charset=ascii")
    request.end_headers()
    request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))


def status_ok(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    request.wfile.write('{"status": "ok"}'.encode("utf-8"))


def status_ok_as_text(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.end_headers()
    request.wfile.write("{'status': 'ok'}".encode("utf-8"))


NGINX_GATEWAY_TIMEOUT = (
    "<html>"
    "<head><title>504 Gateway Time-out</title></head>"
    "<body><center><h1>504 Gateway Time-out</h1></center><hr><center>nginx</center></body>"
    "</html>"
)


def nginx_gateway_timeout(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.GATEWAY_TIMEOUT)
    request.send_header("Content-Type", "text/html")
    request.end_headers()
    request.wfile.write(NGINX_GATEWAY_TIMEOUT.encode("utf-8"))


def truncated_json(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    request.wfile.write("{'status':".encode("utf-8"))


MAGIC_NUMBER = Decimal("42.000000000000001")


def magic_number(request: BaseHTTPRequestHandler) -> None:
    request.send_response(HTTPStatus.OK)
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    request.wfile.write(f'{{"number": {MAGIC_NUMBER}}}'.encode("utf-8"))


def companies_filter_by_sector(request: BaseHTTPRequestHandler) -> None:
    """
    Accepts a query parameter 'sector' and returns a list of companies in that sector.
    """

    items = [
        {"name": "Apple", "sector": "Information Technology"},
        {"name": "Berkshire Hathaway", "sector": "Financials"},
        {"name": "Johnson & Johnson", "sector": "Health Care"},
        {"name": "Chevron Corporation", "sector": "Energy"},
        {"name": "Tesla", "sector": "Consumer Discretionary"},
    ]

    url = urlparse(request.path)
    params = parse_qs(url.query)
    sectors = params.get("sector")
    filtered_items = [item for item in items if item["sector"] in sectors]
    request.send_response(HTTPStatus.OK)
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    request.wfile.write(json.dumps(filtered_items).encode("utf-8"))
