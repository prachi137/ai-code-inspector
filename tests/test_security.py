"""Unit tests for GitHub webhook HMAC SHA-256 signature verification."""

import hashlib
import hmac
import os

import pytest

# Must be set before `from config import settings`: the Settings singleton is
# instantiated at import time and reads credentials from the environment.
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["GITHUB_TOKEN"] = "test-github-token"
os.environ["WEBHOOK_SECRET"] = "test-secret"

from config import settings
from utils.security import verify_github_signature


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    """Ensure a WEBHOOK_SECRET is configured for signature tests."""
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")


def _signature(payload: bytes, secret: str, sha_type: str = "sha256") -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
    return f"{sha_type}={mac.hexdigest()}"


def test_valid_signature_returns_true():
    payload = b'{"action": "opened", "pull_request": {"number": 1}}'
    sig = _signature(payload, "test-secret")
    assert verify_github_signature(payload, sig) is True


def test_tampered_payload_returns_false():
    original = b'{"action": "opened", "pull_request": {"number": 1}}'
    tampered = b'{"action": "closed", "pull_request": {"number": 1}}'
    sig = _signature(original, "test-secret")
    assert verify_github_signature(tampered, sig) is False


def test_wrong_secret_returns_false():
    payload = b'{"action": "opened"}'
    sig = _signature(payload, "another-secret")
    assert verify_github_signature(payload, sig) is False


def test_missing_signature_header_returns_false():
    payload = b'{"action": "opened"}'
    assert verify_github_signature(payload, "") is False
    assert verify_github_signature(payload, None) is False


def test_empty_secret_returns_false(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "")
    payload = b'{"action": "opened"}'
    sig = _signature(payload, "")
    assert verify_github_signature(payload, sig) is False


def test_unsupported_sha_type_returns_false():
    payload = b'{"action": "opened"}'
    sig = _signature(payload, "test-secret", sha_type="sha1")
    assert verify_github_signature(payload, sig) is False


def test_malformed_header_returns_false():
    payload = b'{"action": "opened"}'
    assert verify_github_signature(payload, "not-a-signature-header") is False


def test_valid_signature_with_exact_bytes_preserved():
    """Whitespace/newline differences in the raw body must invalidate the signature."""
    body_a = b'{"action": "opened"}\n'
    body_b = b'{"action": "opened"}'
    sig = _signature(body_a, "test-secret")
    assert verify_github_signature(body_a, sig) is True
    assert verify_github_signature(body_b, sig) is False
