import http.server
import json
import threading
from urllib.parse import parse_qs, urlparse

import pytest

from enterprise_ai_platform.tool_engine import ToolDefinition, ToolRequest
from enterprise_ai_platform.tool_engine.adapters import RESTAdapter


class _Handler(http.server.BaseHTTPRequestHandler):
    """
    Minimal real HTTP server used to test RESTAdapter end-to-end
    against genuine HTTP behavior, rather than mocking the requests
    library.
    """

    def do_GET(self):

        query = parse_qs(urlparse(self.path).query)

        if self.path.startswith("/policy/status"):
            payload = json.dumps(
                {
                    "policy_id": query.get("policy_id", [None])[0],
                    "status": "active",
                }
            ).encode()
            self._respond(200, payload)
        elif self.path.startswith("/notfound"):
            self._respond(404, b'{"error": "not found"}')
        else:
            self._respond(200, b"{}")

    def do_POST(self):

        length = int(self.headers.get("Content-Length", 0))

        body = json.loads(self.rfile.read(length)) if length else {}

        payload = json.dumps({"created": True, "data": body}).encode()

        self._respond(201, payload)

    def _respond(self, status_code, payload):

        self.send_response(status_code)

        self.send_header("Content-Type", "application/json")

        self.send_header("Content-Length", str(len(payload)))

        self.end_headers()

        self.wfile.write(payload)

    def log_message(self, format, *args):

        pass


@pytest.fixture(scope="module")
def test_server():

    server = http.server.HTTPServer(("127.0.0.1", 8790), _Handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)

    thread.start()

    yield "http://127.0.0.1:8790"

    server.shutdown()


def test_get_request_with_query_parameters(test_server) -> None:

    adapter = RESTAdapter()

    tool = ToolDefinition(
        name="check_policy_status",
        version="1.0.0",
        configuration={
            "url": f"{test_server}/policy/status",
            "method": "GET",
        },
    )

    response = adapter.execute(
        ToolRequest(
            tool_name="check_policy_status",
            parameters={"policy_id": "POL123"},
        ),
        tool,
    )

    assert response.status == "success"

    assert response.result == {"policy_id": "POL123", "status": "active"}

    assert response.metadata["status_code"] == 200


def test_post_request_sends_json_body(test_server) -> None:

    adapter = RESTAdapter()

    tool = ToolDefinition(
        name="create_lead",
        version="1.0.0",
        configuration={"url": f"{test_server}/leads", "method": "POST"},
    )

    response = adapter.execute(
        ToolRequest(
            tool_name="create_lead",
            parameters={"name": "Rahul", "phone": "9999999999"},
        ),
        tool,
    )

    assert response.status == "success"

    assert response.result == {
        "created": True,
        "data": {"name": "Rahul", "phone": "9999999999"},
    }

    assert response.metadata["status_code"] == 201


def test_missing_url_in_configuration_raises_clear_error() -> None:

    adapter = RESTAdapter()

    tool = ToolDefinition(name="broken_tool", version="1.0.0")

    with pytest.raises(ValueError, match="broken_tool"):
        adapter.execute(ToolRequest(tool_name="broken_tool"), tool)


def test_http_error_status_raises(test_server) -> None:

    import requests

    adapter = RESTAdapter()

    tool = ToolDefinition(
        name="bad_endpoint",
        version="1.0.0",
        configuration={"url": f"{test_server}/notfound", "method": "GET"},
    )

    with pytest.raises(requests.exceptions.HTTPError):
        adapter.execute(ToolRequest(tool_name="bad_endpoint"), tool)


def test_default_method_is_get(test_server) -> None:

    adapter = RESTAdapter()

    tool = ToolDefinition(
        name="check_policy_status",
        version="1.0.0",
        configuration={"url": f"{test_server}/policy/status"},
    )

    response = adapter.execute(
        ToolRequest(
            tool_name="check_policy_status",
            parameters={"policy_id": "POL456"},
        ),
        tool,
    )

    assert response.result["policy_id"] == "POL456"