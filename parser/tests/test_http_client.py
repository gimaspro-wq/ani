import httpx

from parser.client import HttpClient


def test_http_client_retries_and_user_agent_rotation():
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers.get("User-Agent"))
        if len(calls) == 1:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    client = HttpClient(
        timeout=5,
        max_retries=2,
        backoff_factor=0,
        rate_limit_per_second=100,
        user_agents=["ua1", "ua2"],
        transport=httpx.MockTransport(handler),
    )

    response = client.request("GET", "https://example.org/test")
    assert response.status_code == 200
    # Ensure user-agent rotated between attempts
    assert calls[0] == "ua1"
    assert calls[1] == "ua2"
