"""Smoke test suite (§33.4, CP-0705)."""
import os
import urllib.request
import pytest

TARGET_URL = os.environ.get("TARGET_URL") or os.environ.get("STAGING_URL") or "http://localhost:8080"


def test_health():
    url = f"{TARGET_URL.rstrip('/')}/health"
    req = urllib.request.Request(url, headers={"User-Agent": "smoke-tests/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200


def test_version():
    url = f"{TARGET_URL.rstrip('/')}/version"
    req = urllib.request.Request(url, headers={"User-Agent": "smoke-tests/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200


def test_metrics():
    url = f"{TARGET_URL.rstrip('/')}/metrics"
    req = urllib.request.Request(url, headers={"User-Agent": "smoke-tests/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
