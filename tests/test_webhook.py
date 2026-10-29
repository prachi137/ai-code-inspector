"""Endpoint tests for the GitHub webhook handler using FastAPI TestClient.

Covers:
- 200 OK for ping events
- 200 OK for pull_request events with a valid HMAC SHA-256 signature
- 401 Unauthorized for invalid / missing / tampered signatures
- Background task scheduling on valid pull_request events
"""

import hashlib
import hmac
import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Must be set before `import main`: the app constructs GitHub/Gemini clients
# at import time, which would otherwise fail with dummy/empty credentials.
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["GITHUB_TOKEN"] = "test-github-token"
os.environ["WEBHOOK_SECRET"] = "test-secret"

import main


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(main.settings, "WEBHOOK_SECRET", "test-secret")


@pytest.fixture()
def client(monkeypatch):
    # Never touch real GitHub / Gemini during tests.
    monkeypatch.setattr(main, "run_ai_code_review", MagicMock())
    return TestClient(main.app)


def _signature(payload: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def _headers(payload: bytes, secret: str = "test-secret", event: str = "pull_request"):
    return {
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": _signature(payload, secret),
        "Content-Type": "application/json",
    }


def test_ping_event_returns_200(client):
    payload = b'{"zen": "Keep it simple."}'
    resp = client.post("/webhook", content=payload, headers=_headers(payload, event="ping"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "Pong" in body["message"]


def test_pull_request_event_valid_signature_returns_200(client):
    payload = (
        b'{"action": "opened", "number": 1, "pull_request": {"number": 1},'
        b' "repository": {"full_name": "octocat/Hello-World"}}'
    )
    resp = client.post("/webhook", content=payload, headers=_headers(payload))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "pull_request" in body["message"]


def test_pull_request_event_schedules_background_task(client):
    payload = (
        b'{"action": "opened", "number": 2, "pull_request": {"number": 2},'
        b' "repository": {"full_name": "octocat/Hello-World"}}'
    )
    resp = client.post("/webhook", content=payload, headers=_headers(payload))
    assert resp.status_code == 200
    main.run_ai_code_review.assert_called_once_with("octocat/Hello-World", 2)


def test_invalid_signature_returns_401(client):
    payload = b'{"action": "opened", "number": 1, "pull_request": {"number": 1}}'
    headers = _headers(payload, secret="wrong-secret")
    resp = client.post("/webhook", content=payload, headers=headers)
    assert resp.status_code == 401


def test_missing_signature_returns_401(client):
    payload = b'{"action": "opened", "number": 1, "pull_request": {"number": 1}}'
    headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
    resp = client.post("/webhook", content=payload, headers=headers)
    assert resp.status_code == 401


def test_tampered_payload_returns_401(client):
    original = b'{"action": "opened", "number": 1, "pull_request": {"number": 1}}'
    tampered = b'{"action": "opened", "number": 999, "pull_request": {"number": 999}}'
    headers = _headers(original)
    resp = client.post("/webhook", content=tampered, headers=headers)
    assert resp.status_code == 401


def test_no_secret_configured_accepts_ping(client, monkeypatch):
    monkeypatch.setattr(main.settings, "WEBHOOK_SECRET", "")
    payload = b'{"zen": "Keep it simple."}'
    resp = client.post(
        "/webhook",
        content=payload,
        headers={"X-GitHub-Event": "ping", "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
