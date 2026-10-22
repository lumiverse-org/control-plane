#!/usr/bin/env python3
"""tools/records/lib/mint_token.py
GitHub App installation token minter for records-writer.
Spec §40.1 fifth secrets tier, §97.1 line 8841; D89; FD-136.

Mints a short-lived (1-hour) installation token from the GitHub App private key.
Never prints, logs, or commits the private key or token.
"""
import argparse
import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

DEFAULT_APP_ID = "5422825"
DEFAULT_INSTALLATION_ID = "174038206"
GITHUB_API_BASE = "https://api.github.com"


def create_jwt(pem_bytes: bytes, app_id: str, lifetime_seconds: int = 540) -> str:
    """Create an RS256 signed JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + lifetime_seconds,
        "iss": str(app_id),
    }

    try:
        import jwt
        # PyJWT accepts str or bytes for key
        return jwt.encode(payload, pem_bytes, algorithm="RS256")
    except ImportError:
        pass

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:
        raise RuntimeError("Neither pyjwt nor cryptography is installed to sign RS256 JWT") from exc

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    header = {"alg": "RS256", "typ": "JWT"}
    header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    unsigned = f"{header_b64}.{payload_b64}"

    private_key = serialization.load_pem_private_key(pem_bytes, password=None)
    signature = private_key.sign(unsigned.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return f"{unsigned}.{b64url(signature)}"


def exchange_jwt_for_token(jwt_token: str, installation_id: str) -> str:
    """Exchange JWT for GitHub App installation access token."""
    url = f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "MultiProduct-Records-Writer",
    }

    req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            tok = data.get("token")
            if not tok:
                raise RuntimeError("Response missing 'token' field")
            return tok
    except urllib.error.HTTPError as exc:
        err_msg = f"GitHub API error {exc.code}: {exc.reason}"
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
            err_json = json.loads(err_body)
            if "message" in err_json:
                err_msg = f"{err_msg} ({err_json['message']})"
        except Exception:
            pass
        raise RuntimeError(err_msg) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error connecting to GitHub: {exc.reason}") from exc


def resolve_pem_path(provided_path: Optional[str] = None) -> pathlib.Path:
    """Resolve the private key path from arguments or environment."""
    if provided_path:
        return pathlib.Path(provided_path)

    rw_pem = os.environ.get("RW_PEM")
    if rw_pem:
        return pathlib.Path(rw_pem)

    secrets_dir = os.environ.get("SECRETS_DIR")
    if secrets_dir:
        return pathlib.Path(secrets_dir) / "records-writer.pem"

    raise RuntimeError("Private key path not specified: set RW_PEM or SECRETS_DIR or pass --pem")


def mint_installation_token(
    pem_path: Optional[pathlib.Path] = None,
    app_id: str = DEFAULT_APP_ID,
    installation_id: str = DEFAULT_INSTALLATION_ID,
) -> str:
    """Mint an installation access token using the specified or resolved PEM key."""
    if pem_path is None:
        pem_path = resolve_pem_path()

    if not pem_path.is_file():
        raise FileNotFoundError(f"Private key file not found: {pem_path}")

    pem_bytes = pem_path.read_bytes()
    jwt_token = create_jwt(pem_bytes, app_id=app_id)
    return exchange_jwt_for_token(jwt_token, installation_id=installation_id)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mint a GitHub App installation token for records-writer")
    parser.add_argument("--pem", help="Path to records-writer private key (.pem)")
    parser.add_argument("--app-id", default=os.environ.get("APP_ID", DEFAULT_APP_ID), help="GitHub App ID")
    parser.add_argument("--installation-id", default=os.environ.get("INSTALLATION_ID", DEFAULT_INSTALLATION_ID), help="GitHub App Installation ID")
    parser.add_argument("--cache", action="store_true", help="Cache token to $SECRETS_DIR/records-writer.token")
    parser.add_argument("--cache-to", help="Explicit file path to write token")
    args = parser.parse_args(argv)

    try:
        pem_path = resolve_pem_path(args.pem)
        if not pem_path.is_file():
            print(f"Error: PEM file not found at {pem_path}", file=sys.stderr)
            return 2

        token = mint_installation_token(
            pem_path=pem_path,
            app_id=args.app_id,
            installation_id=args.installation_id,
        )

        # Print token to stdout (single line)
        print(token)

        # Optional caching for tools/records/lib/rwtoken.py
        cache_dest = None
        if args.cache_to:
            cache_dest = pathlib.Path(args.cache_to)
        elif args.cache:
            secrets_dir = os.environ.get("SECRETS_DIR")
            if secrets_dir:
                cache_dest = pathlib.Path(secrets_dir) / "records-writer.token"

        if cache_dest:
            cache_dest.parent.mkdir(parents=True, exist_ok=True)
            cache_dest.write_text(token.strip() + "\n", encoding="utf-8")

        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error minting token: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
