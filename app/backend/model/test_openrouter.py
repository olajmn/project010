"""Checks for openrouter.chat() and the provider switch in client.py - no
network, no real key, no model call.
"""

import importlib
import io
import json
import urllib.error
from unittest import mock

import pytest

from backend.model import client, openrouter

FAKE_KEY = "test-key-not-real"
MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "hi"},
]


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _reply(payload: dict) -> _Response:
    return _Response(json.dumps(payload).encode())


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_KEY)


def test_missing_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(
        openrouter.OpenRouterError, match="^OPENROUTER_API_KEY is not set$"
    ):
        openrouter.chat("m", MESSAGES, 0.2)


def test_request_sent(key) -> None:
    ok = _reply({"choices": [{"message": {"content": "Hello."}}]})
    with mock.patch("urllib.request.urlopen", return_value=ok) as urlopen:
        assert openrouter.chat("qwen/qwen3.5-9b", MESSAGES, 0.2) == "Hello."
    request = urlopen.call_args.args[0]
    sent = json.loads(request.data)
    assert sent["model"] == "qwen/qwen3.5-9b"
    assert sent["messages"] == MESSAGES
    assert sent["temperature"] == 0.2
    assert sent["reasoning"] == {"enabled": False}
    assert sent["max_tokens"] == openrouter.MAX_TOKENS
    assert request.get_header("Authorization") == f"Bearer {FAKE_KEY}"
    assert urlopen.call_args.kwargs["timeout"] == openrouter.TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "urlopen, message",
    [
        pytest.param(
            {
                "side_effect": urllib.error.HTTPError(
                    openrouter.URL,
                    401,
                    "Unauthorized",
                    {},
                    io.BytesIO(FAKE_KEY.encode()),
                )
            },
            "HTTP 401",
            id="http_error",
        ),
        pytest.param(
            {"side_effect": TimeoutError()},
            "request failed: TimeoutError",
            id="timeout",
        ),
        pytest.param(
            {
                "return_value": _reply(
                    {"error": {"message": "provider down", "code": 502}}
                )
            },
            "no reply in response",
            id="upstream_error",
        ),
        pytest.param(
            {"return_value": _reply({"choices": [{"message": {"content": "  "}}]})},
            "empty reply",
            id="empty_reply",
        ),
    ],
)
def test_errors_say_what_failed(key, urlopen, message) -> None:
    # Never the key or the response body.
    with mock.patch("urllib.request.urlopen", **urlopen):
        with pytest.raises(openrouter.OpenRouterError) as raised:
            openrouter.chat("m", MESSAGES, 0.2)
    assert str(raised.value) == message
    assert FAKE_KEY not in str(raised.value)


@pytest.fixture
def reload_client(monkeypatch):
    """Reload client.py under a test's TALK_PROVIDER, then back under the
    real environment (restored first, so the last reload sees it)."""
    yield lambda: importlib.reload(client)
    monkeypatch.undo()
    importlib.reload(client)


def test_default_provider_is_ollama(monkeypatch, reload_client) -> None:
    monkeypatch.setenv("TALK_PROVIDER", "")
    reload_client()
    assert client.PROVIDER == "ollama"
    assert client.MODEL_IN_USE == client.MODEL == "qwen3.5:9b"
    with (
        mock.patch("backend.model.openrouter.chat") as hosted,
        mock.patch(
            "ollama.chat", return_value={"message": {"content": "local"}}
        ) as local,
    ):
        assert client.send_chat(MESSAGES) == "local"
    hosted.assert_not_called()
    # Ollama's own default context is 4,096 tokens; the app asks for more.
    assert local.call_args.kwargs["options"]["num_ctx"] == client.CONTEXT_TOKENS


def test_openrouter_provider(monkeypatch, reload_client) -> None:
    monkeypatch.setenv("TALK_PROVIDER", "OpenRouter")
    reload_client()
    assert client.PROVIDER == "openrouter"
    assert client.MODEL_IN_USE == client.OPENROUTER_MODEL == "qwen/qwen3.5-9b"
    with (
        mock.patch("backend.model.openrouter.chat", return_value="hosted") as hosted,
        mock.patch("ollama.chat") as local,
    ):
        assert client.send_chat(MESSAGES) == "hosted"
    hosted.assert_called_once_with("qwen/qwen3.5-9b", MESSAGES, client.TEMPERATURE)
    local.assert_not_called()


def test_unknown_provider_stops_start(monkeypatch, reload_client) -> None:
    monkeypatch.setenv("TALK_PROVIDER", "openai")
    with pytest.raises(ValueError):
        reload_client()
