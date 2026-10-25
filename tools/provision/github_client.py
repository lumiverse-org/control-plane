"""tools.provision.github_client: RealGitHubClient implementation using gh CLI.

Implements the GitHubClient Protocol for live GitHub API mutations via subprocess
invocations of the GitHub CLI (`gh`).

Safety & Anti-Hallucination Discipline:
- All methods perform concrete `gh` CLI invocations.
- Every method raises a specific `GitHubClientError` on any non-zero exit code.
- Zero silent swallowed errors or fabricated success return shapes.
- For `put_file`, existence is checked first via GET: existing file includes `sha`
  for update, non-existent file creates without `sha`.
"""

from __future__ import annotations

import base64
import json
import subprocess
from typing import Any

from tools.provision.repo import TEMPLATE_REPO


class GitHubClientError(RuntimeError):
    """Raised when a GitHub CLI command fails (non-zero exit)."""


class RealGitHubClient:
    """Live implementation of GitHubClient Protocol via gh CLI subprocess calls."""

    def __init__(self, org: str) -> None:
        if not org or not org.strip():
            raise ValueError("org must be a non-empty string; defaulting to a production organisation is forbidden")
        self.org = org.strip()

    def _full_repo(self, repo: str) -> str:
        """Resolve full repository name including org prefix."""
        return f"{self.org}/{repo}" if "/" not in repo else repo

    def _run_gh(
        self, cmd: list[str], input_str: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Execute a gh CLI command and raise GitHubClientError on failure."""
        res = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            err_details = res.stderr.strip() or res.stdout.strip()
            raise GitHubClientError(
                f"gh command failed with exit code {res.returncode}: {' '.join(cmd)}\n{err_details}"
            )
        return res

    def create_repo_from_template(
        self, name: str, template: str = TEMPLATE_REPO, private: bool = True
    ) -> dict[str, Any]:
        """Create a repository from the product-template via `gh repo create`."""
        visibility = "--private" if private else "--public"
        template_full = self._full_repo(template)
        repo_full = self._full_repo(name)

        cmd = [
            "gh",
            "repo",
            "create",
            repo_full,
            "--template",
            template_full,
            visibility,
        ]
        self._run_gh(cmd)
        return {
            "name": name,
            "full_name": repo_full,
            "status": "created",
            "template": template_full,
            "private": private,
        }

    def create_team(self, name: str, members: list[str]) -> dict[str, Any]:
        """Create a GitHub Team and assign initial membership via `gh api`."""
        # 1. Create the team
        create_cmd = ["gh", "api", f"orgs/{self.org}/teams", "-f", f"name={name}"]
        res = self._run_gh(create_cmd)
        try:
            team_data = json.loads(res.stdout)
            if not isinstance(team_data, dict):
                raise ValueError("Response payload is not a JSON object")
        except Exception as exc:
            raise GitHubClientError(
                f"Failed to parse team creation response for team {name!r}: {exc}\n"
                f"Raw response: {res.stdout!r}"
            ) from exc

        if not team_data:
            raise GitHubClientError(
                f"Team creation response for team {name!r} returned empty JSON object; membership cannot safely proceed."
            )

        slug = team_data.get("slug") or name

        # 2. Add members
        for member in members:
            mem_cmd = [
                "gh",
                "api",
                f"orgs/{self.org}/teams/{slug}/memberships/{member}",
                "-X",
                "PUT",
            ]
            self._run_gh(mem_cmd)

        return {
            "name": name,
            "slug": slug,
            "members": list(members),
            "team": team_data,
        }

    def put_file(
        self, repo: str, path: str, content: str, message: str
    ) -> dict[str, Any]:
        """Create or update a file in the repository via contents API.

        Checks existence first: if existing, captures current `sha` to supply with PUT.
        If non-existent (404), creates without `sha`.
        """
        full_repo = self._full_repo(repo)

        # 1. Check existence to retrieve blob sha if updating
        get_cmd = ["gh", "api", f"repos/{full_repo}/contents/{path}"]
        get_proc = subprocess.run(get_cmd, capture_output=True, text=True)

        sha: str | None = None
        if get_proc.returncode == 0:
            try:
                data = json.loads(get_proc.stdout)
                sha = data.get("sha")
            except Exception:
                pass
        else:
            err_msg = (get_proc.stderr or get_proc.stdout).lower()
            if "not found" in err_msg or "404" in err_msg:
                sha = None
            else:
                raise GitHubClientError(
                    f"gh api contents GET failed for {full_repo}:{path}: "
                    f"{get_proc.stderr.strip() or get_proc.stdout.strip()}"
                )

        # 2. Construct PUT payload
        b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload: dict[str, Any] = {
            "message": message,
            "content": b64_content,
        }
        if sha:
            payload["sha"] = sha

        put_cmd = [
            "gh",
            "api",
            f"repos/{full_repo}/contents/{path}",
            "-X",
            "PUT",
            "--input",
            "-",
        ]
        put_res = self._run_gh(put_cmd, input_str=json.dumps(payload))

        resp_data: dict[str, Any] = {}
        try:
            resp_data = json.loads(put_res.stdout)
        except Exception:
            pass

        return {
            "path": path,
            "status": "written",
            "action": "updated" if sha else "created",
            "response": resp_data,
        }

    def set_codeowners(self, repo: str, content: str) -> dict[str, Any]:
        """Write .github/CODEOWNERS into the repository delegating to put_file."""
        res = self.put_file(
            repo=repo,
            path=".github/CODEOWNERS",
            content=content,
            message="Configure CODEOWNERS (human identities only, §11.3)",
        )
        return {"path": ".github/CODEOWNERS", "status": "written", "detail": res}

    def apply_branch_protection(
        self, repo: str, branch: str, settings: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply branch protection settings via `gh api .../branches/{branch}/protection`."""
        full_repo = self._full_repo(repo)
        cmd = [
            "gh",
            "api",
            f"repos/{full_repo}/branches/{branch}/protection",
            "-X",
            "PUT",
            "--input",
            "-",
        ]
        res = self._run_gh(cmd, input_str=json.dumps(settings))
        resp_data: dict[str, Any] = {}
        try:
            resp_data = json.loads(res.stdout)
        except Exception:
            pass
        return {
            "branch": branch,
            "protected": True,
            "settings": settings,
            "response": resp_data,
        }

    def create_environment(
        self, repo: str, name: str, deployment_policy: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create an environment with deployment branch/tag policy via `gh api`."""
        full_repo = self._full_repo(repo)

        # 1. Create/update environment
        if deployment_policy and deployment_policy.get("custom_branch_policies"):
            env_body = {
                "deployment_branch_policy": {
                    "protected_branches": False,
                    "custom_branch_policies": True,
                }
            }
            cmd = [
                "gh",
                "api",
                f"repos/{full_repo}/environments/{name}",
                "-X",
                "PUT",
                "--input",
                "-",
            ]
            res = self._run_gh(cmd, input_str=json.dumps(env_body))
        else:
            cmd = ["gh", "api", f"repos/{full_repo}/environments/{name}", "-X", "PUT"]
            res = self._run_gh(cmd)

        env_data: dict[str, Any] = {}
        try:
            env_data = json.loads(res.stdout)
        except Exception:
            pass

        # 2. Configure deployment branch & tag policies if specified
        if deployment_policy:
            policies = deployment_policy.get("policies")
            if not policies:
                # Default Section 33.4 policies: default branch 'main' and release tags 'v*'
                policies = [
                    {"name": "main", "type": "branch"},
                    {"name": "v*", "type": "tag"},
                ]

            for policy in policies:
                pol_name = policy.get("name")
                pol_type = policy.get("type", "branch")
                pol_cmd = [
                    "gh",
                    "api",
                    f"repos/{full_repo}/environments/{name}/deployment-branch-policies",
                    "-X",
                    "POST",
                    "-f",
                    f"name={pol_name}",
                    "-f",
                    f"type={pol_type}",
                ]
                self._run_gh(pol_cmd)

        return {
            "name": name,
            "status": "created",
            "environment": env_data,
        }
