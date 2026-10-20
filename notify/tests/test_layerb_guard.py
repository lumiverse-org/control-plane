"""notify/tests/test_layerb_guard.py

Behavioral pytest suite for L5-T42 (spec 90.2, machine-identities row,
invariants 106 and 109). Each test invokes the real CLI --
`notify/tools/layerb_guard.py --payload <json>` -- as a subprocess, and the
last test drives `notify/route.py` itself, so this suite genuinely exercises
the guard's outcome for a specific payload rather than importing its
internals.
"""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GUARD = os.path.join(REPO_ROOT, "notify", "tools", "layerb_guard.py")
ROUTE = os.path.join(REPO_ROOT, "notify", "route.py")


def _run_guard(payload, matrix=None):
    args = [sys.executable, GUARD, "--payload", json.dumps(payload)]
    if matrix is not None:
        args += ["--matrix", matrix]
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)


def _run_route(event_type, payload=None):
    args = [sys.executable, ROUTE, "--event-type", event_type]
    if payload is not None:
        args += ["--payload", json.dumps(payload)]
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)


def test_clean_payload_passes():
    result = _run_guard({"event": "drift_detected", "severity": "blocking"})
    assert result.returncode == 0
    assert "LAYER B GUARD REFUSED" not in result.stdout


def test_payload_keyed_on_data_category_refuses():
    result = _run_guard({"compensation_information": "redacted"})
    assert result.returncode == 1
    assert "LAYER B GUARD REFUSED" in result.stdout
    assert "Compensation information" in result.stdout


def test_payload_value_matching_data_category_refuses():
    result = _run_guard({"note": "flagged under promotion signal review"})
    assert result.returncode == 1
    assert "LAYER B GUARD REFUSED" in result.stdout
    assert "Promotion signal" in result.stdout


def test_refusal_names_category_and_never_the_content():
    secret_marker = "MARKER-9f31-do-not-echo"
    result = _run_guard(
        {"note": "%s promotion signal review" % secret_marker})
    assert result.returncode == 1
    assert "matches data category Promotion signal" in result.stdout
    assert secret_marker not in result.stdout
    assert secret_marker not in result.stderr


def test_absent_matrix_fails_closed():
    result = _run_guard({}, matrix="nope.yaml")
    assert result.returncode == 1


def test_route_refuses_layerb_content_even_on_push_list():
    # drift_detected (route: blocking-class-drift) is on the closed push
    # list and resolves cleanly with no payload.
    clean = _run_route("drift_detected")
    assert clean.returncode == 0
    assert clean.stdout.startswith("ROUTE: PUSH")

    # The same event, carrying Layer B content, must be refused by the
    # router itself even though the event type is on the push list.
    guarded = _run_route(
        "drift_detected",
        payload={"note": "see individual performance evidence for this"})
    assert guarded.returncode != 0
    assert "ROUTE: PUSH" not in guarded.stdout
    assert "BLOCKED" in guarded.stdout
    assert "Individual performance evidence" in guarded.stdout
