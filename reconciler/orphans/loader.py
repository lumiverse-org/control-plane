"""Control-plane loader for the expiry-warning acceptance path.

Spec: lanes/L3-05-orphans.md L3-05-03, consumed by L3-P0-DEL14.
A missing file is recorded and left empty. A file that exists but does
not parse raises ControlPlaneParseError. The loader never calls the
network and never writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from reconciler.orphans.decisions import (
    ASSET_INVENTORY_PATHS,
    BOARD_SNAPSHOT_PATH,
    OPEN_WORK_SNAPSHOT_PATH,
)


class ControlPlaneParseError(Exception):
    """A registry file exists but is not parseable YAML."""


def _read_yaml(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlPlaneParseError(str(path)) from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ControlPlaneParseError(str(path)) from exc


def _mapping(document: Any) -> dict[str, Any]:
    if document is None:
        return {}
    if not isinstance(document, dict):
        raise ControlPlaneParseError("document is not a mapping")
    return document


@dataclass(frozen=True)
class ControlPlane:
    people: dict[str, dict[str, Any]]
    products: dict[str, dict[str, Any]]
    services: dict[str, dict[str, Any]]
    policies: list[dict[str, Any]]
    exceptions: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    board_items: list[dict[str, Any]]
    open_work: list[dict[str, Any]]
    missing: tuple[str, ...]
    as_of: date
    mode: str

    def require(self, *keys: str) -> tuple[str, ...]:
        missing = set(self.missing)
        return tuple(key for key in keys if key in missing)


def _load_optional_file(root: Path, relative: str, missing: list[str]) -> Any | None:
    path = root / relative
    if not path.is_file():
        missing.append(relative)
        return None
    document = _read_yaml(path)
    if document is None:
        return None
    return document


def _load_people(root: Path, missing: list[str]) -> dict[str, dict[str, Any]]:
    document = _load_optional_file(root, "people.yaml", missing)
    if document is None:
        return {}
    try:
        mapping = _mapping(document)
    except ControlPlaneParseError as exc:
        raise ControlPlaneParseError(str(root / "people.yaml")) from exc
    people: dict[str, dict[str, Any]] = {}
    for row in mapping.get("people") or []:
        if isinstance(row, dict) and row.get("id"):
            people[str(row["id"])] = row
    return people


def _load_scoped(root: Path, directory: str, filename: str, missing_token: str, missing: list[str]) -> dict[str, dict[str, Any]]:
    folder = root / directory
    if not folder.is_dir():
        missing.append(missing_token)
        return {}
    loaded: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob(f"*/{filename}")):
        document = _read_yaml(path)
        if document is None:
            continue
        try:
            mapping = _mapping(document)
        except ControlPlaneParseError as exc:
            raise ControlPlaneParseError(str(path)) from exc
        identity = mapping.get("identity") or {}
        key = identity.get("id") or path.parent.name
        loaded[str(key)] = mapping
    return loaded


def _load_list(root: Path, relative: str, key: str, missing: list[str]) -> list[dict[str, Any]]:
    document = _load_optional_file(root, relative, missing)
    if document is None:
        return []
    try:
        mapping = _mapping(document)
    except ControlPlaneParseError as exc:
        raise ControlPlaneParseError(str(root / relative)) from exc
    rows = mapping.get(key) or []
    return [row for row in rows if isinstance(row, dict)]


def _load_decision_list(root: Path, paths: Any, unanswered: str, missing: list[str], key: str) -> list[dict[str, Any]]:
    if paths is None:
        missing.append(unanswered)
        return []
    if isinstance(paths, str):
        paths = [paths]
    rows: list[dict[str, Any]] = []
    for relative in paths:
        document = _load_optional_file(root, str(relative), missing)
        if document is None:
            continue
        if isinstance(document, list):
            rows.extend(row for row in document if isinstance(row, dict))
            continue
        try:
            mapping = _mapping(document)
        except ControlPlaneParseError as exc:
            raise ControlPlaneParseError(str(root / str(relative))) from exc
        rows.extend(row for row in (mapping.get(key) or []) if isinstance(row, dict))
    return rows


def load_control_plane(root: Path, as_of: date, mode: str) -> ControlPlane:
    root = Path(root)
    missing: list[str] = []
    people = _load_people(root, missing)
    products = _load_scoped(root, "products", "product.yaml", "products/*/product.yaml", missing)
    services = _load_scoped(root, "shared-services", "service.yaml", "shared-services/*/service.yaml", missing)
    policies = _load_list(root, "policies.yaml", "policies", missing)
    exceptions = _load_list(root, "exceptions.yaml", "exceptions", missing)
    assets = _load_decision_list(root, ASSET_INVENTORY_PATHS, "DR-L3-05-A unanswered", missing, "assets")
    board_items = _load_decision_list(root, BOARD_SNAPSHOT_PATH, "DR-L3-05-C unanswered", missing, "items")
    open_work = _load_decision_list(root, OPEN_WORK_SNAPSHOT_PATH, "DR-L3-05-D unanswered", missing, "items")
    return ControlPlane(
        people=people,
        products=products,
        services=services,
        policies=policies,
        exceptions=exceptions,
        assets=assets,
        board_items=board_items,
        open_work=open_work,
        missing=tuple(missing),
        as_of=as_of,
        mode=mode,
    )
