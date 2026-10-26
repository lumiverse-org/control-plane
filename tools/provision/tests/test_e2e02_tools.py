"""Unit tests for E2E-02 tools: apply-assignments, verify-codeowners, diff-team-membership, check-permission."""

from __future__ import annotations

import types
from importlib.machinery import SourceFileLoader
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_tool(name: str):
    path = REPO_ROOT / "tools" / "provision" / name
    loader = SourceFileLoader(name.replace("-", "_"), str(path))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(path)
    loader.exec_module(mod)
    return mod


apply_assignments = _load_tool("apply-assignments")
verify_codeowners = _load_tool("verify-codeowners")
diff_team_membership = _load_tool("diff-team-membership")
check_permission = _load_tool("check-permission")


@pytest.fixture
def temp_repo_root(tmp_path: Path) -> Path:
    declared = tmp_path / "declared"
    declared.mkdir(parents=True)
    products_dir = declared / "products"
    products_dir.mkdir()

    people = {
        "people": [
            {"id": "lead-1", "github_login": "lead-1", "availability": "active", "capabilities": ["reviewer-matrix-change"]},
            {"id": "dev-a", "github_login": "dev-a", "availability": "active", "capabilities": ["code-review"]},
            {"id": "dev-b", "github_login": "dev-b", "availability": "active", "capabilities": ["code-review"]},
            {"id": "qa-1", "github_login": "qa-1", "availability": "active", "capabilities": ["verification"]},
        ]
    }
    (declared / "people.yaml").write_text(yaml.safe_dump(people), encoding="utf-8")

    product = {
        "product": "test-prod",
        "assignments": {},
        "temporary_assignments": [],
    }
    (products_dir / "test-prod.yaml").write_text(yaml.safe_dump(product), encoding="utf-8")
    return tmp_path


# --- apply-assignments tests ---

def test_apply_assignments_merges_into_product_yaml(temp_repo_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("E2E_OUT", str(tmp_path / "out"))
    rc = apply_assignments.main([
        "--product", "test-prod",
        "--set", "primary_owner=dev-a",
        "--set", "cross_reviewer=dev-b",
        "--set", "backup_owner=dev-b",
        "--set", "primary_responder=dev-a",
        "--set", "backup_responder=dev-b",
        "--set", "verification=qa-1",
        "--target-dir", str(temp_repo_root / "declared"),
    ])
    assert rc == 0

    prod_file = temp_repo_root / "declared" / "products" / "test-prod.yaml"
    data = yaml.safe_load(prod_file.read_text(encoding="utf-8"))
    assert data["assignments"]["primary_owner"] == "dev-a"
    assert data["assignments"]["cross_reviewer"] == "dev-b"
    assert data["assignments"]["incident_responder_primary"] == "dev-a"
    assert data["assignments"]["verification_responsibility"] == "qa-1"

    out_file = tmp_path / "out" / "assignments" / "test-prod.yaml"
    assert out_file.is_file()


def test_apply_assignments_rejects_malformed_pair():
    rc = apply_assignments.main(["--product", "test-prod", "--set", "not_a_pair"])
    assert rc == 1


# --- verify-codeowners tests ---

def test_verify_codeowners_accepts_clean_generated_file(temp_repo_root: Path, tmp_path: Path):
    # Apply assignments first
    apply_assignments.main([
        "--product", "test-prod",
        "--set", "primary_owner=dev-a",
        "--set", "cross_reviewer=dev-b",
        "--set", "backup_owner=dev-b",
        "--set", "verification=qa-1",
        "--target-dir", str(temp_repo_root / "declared"),
    ])

    codeowners_content = (
        "* @dev-a @dev-b\n"
        "/verification/ @qa-1\n"
        "/product.yaml @lead-1\n"
        "/migrations/ @lead-1\n"
        "/.github/workflows/ @lead-1\n"
    )
    codeowners_file = tmp_path / "CODEOWNERS"
    codeowners_file.write_text(codeowners_content, encoding="utf-8")

    rc = verify_codeowners.main([
        "--repo", "lumiverse-org/test-prod-api",
        "--codeowners-file", str(codeowners_file),
        "--derived-from", "registry",
        "--forbid-machine-identities",
        "--declared-dir", str(temp_repo_root / "declared"),
    ])
    assert rc == 0


def test_verify_codeowners_rejects_machine_identity(temp_repo_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    codeowners_content = "* @dev-a @automation[bot]\n/product.yaml @lead-1\n"
    codeowners_file = tmp_path / "CODEOWNERS"
    codeowners_file.write_text(codeowners_content, encoding="utf-8")

    rc = verify_codeowners.main([
        "--repo", "lumiverse-org/test-prod-api",
        "--codeowners-file", str(codeowners_file),
        "--forbid-machine-identities",
        "--declared-dir", str(temp_repo_root / "declared"),
    ])
    assert rc == 1
    _, err = capsys.readouterr()
    assert "machine identities detected" in err
    assert "@automation[bot]" in err


def test_verify_codeowners_rejects_mismatched_derivation(temp_repo_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    # Product yaml has no assignments yet
    codeowners_content = "* @dev-a @dev-b\n/product.yaml @lead-1\n"
    codeowners_file = tmp_path / "CODEOWNERS"
    codeowners_file.write_text(codeowners_content, encoding="utf-8")

    rc = verify_codeowners.main([
        "--repo", "lumiverse-org/test-prod-api",
        "--codeowners-file", str(codeowners_file),
        "--derived-from", "registry",
        "--declared-dir", str(temp_repo_root / "declared"),
    ])
    assert rc == 1
    _, err = capsys.readouterr()
    assert "does not match canonical registry derivation" in err


# --- diff-team-membership tests ---

def test_diff_team_membership_exact_match(temp_repo_root: Path):
    apply_assignments.main([
        "--product", "test-prod",
        "--set", "primary_owner=dev-a",
        "--set", "cross_reviewer=dev-b",
        "--target-dir", str(temp_repo_root / "declared"),
    ])

    rc = diff_team_membership.main([
        "--product", "test-prod",
        "--actual-members", "dev-a,dev-b",
        "--declared-dir", str(temp_repo_root / "declared"),
        "--exit-nonzero-on-diff",
    ])
    assert rc == 0


def test_diff_team_membership_detects_mismatch(temp_repo_root: Path, capsys: pytest.CaptureFixture[str]):
    apply_assignments.main([
        "--product", "test-prod",
        "--set", "primary_owner=dev-a",
        "--set", "cross_reviewer=dev-b",
        "--target-dir", str(temp_repo_root / "declared"),
    ])

    rc = diff_team_membership.main([
        "--product", "test-prod",
        "--actual-members", "dev-a,rogue-user",
        "--declared-dir", str(temp_repo_root / "declared"),
        "--exit-nonzero-on-diff",
    ])
    assert rc == 1
    _, err = capsys.readouterr()
    assert "Missing  (1): dev-b" in err
    assert "Unexpected (1): rogue-user" in err


# --- check-permission tests ---

def test_check_permission_write_satisfied():
    rc = check_permission.main([
        "--repo", "lumiverse-org/pilot-one-api",
        "--login", "dev-b",
        "--expect", "write",
        "--mock-permission", "write",
    ])
    assert rc == 0


def test_check_permission_admin_satisfies_write():
    rc = check_permission.main([
        "--repo", "lumiverse-org/pilot-one-api",
        "--login", "dev-b",
        "--expect", "write",
        "--mock-permission", "admin",
    ])
    assert rc == 0


def test_check_permission_read_fails_expected_write(capsys: pytest.CaptureFixture[str]):
    rc = check_permission.main([
        "--repo", "lumiverse-org/pilot-one-api",
        "--login", "dev-b",
        "--expect", "write",
        "--mock-permission", "read",
    ])
    assert rc == 1
    _, err = capsys.readouterr()
    assert "cross-reviewer must hold write, not read/none" in err
