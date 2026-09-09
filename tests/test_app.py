"""Tests for the Flask routes in app.py, using Flask's built-in test client
(no live server needs to be running)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_index_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Password Strength Analyzer" in resp.data


def test_check_endpoint_returns_json_report(client):
    resp = client.post("/api/check", json={"password": "Str0ng!Passw0rd#2026"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["verdict"] == "Strong"
    assert "labels" in body


def test_check_endpoint_never_echoes_password(client):
    resp = client.post("/api/check", json={"password": "SuperSecret123!"})
    assert b"SuperSecret123!" not in resp.data


def test_check_endpoint_rejects_overlong_password(client):
    resp = client.post("/api/check", json={"password": "a" * 300})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_check_endpoint_rejects_non_string_password(client):
    resp = client.post("/api/check", json={"password": 12345})
    assert resp.status_code == 400


def test_check_endpoint_handles_missing_body_gracefully(client):
    resp = client.post("/api/check", data="not-json", content_type="application/json")
    assert resp.status_code == 200
    assert resp.get_json()["verdict"] == "Idle"


def test_unknown_api_route_returns_json_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Not found."}


def test_oversized_request_body_is_rejected(client):
    huge_payload = {"password": "a" * (20 * 1024)}
    resp = client.post("/api/check", json=huge_payload)
    assert resp.status_code == 413
