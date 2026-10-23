#!/usr/bin/env python3
"""Hermes Agent cage-configuration contract validator (Spec Sections 37.8, 100.6; AT-108, AT-109; Invariant 85).

Enforces machine-checkable container and runtime isolation bounds across:
- infra/hermes/*.yaml (background-worker.yaml, ops-console.yaml, pr-review.yaml)
- infra/hermes/docker-compose.yaml

Rules:
  CAGE-01 memory.memory_enabled == false
  CAGE-02 model.background_review.enabled == false
  CAGE-03 approvals.cron_mode == "deny"
  CAGE-04 security.allow_lazy_installs == false
  CAGE-05 plugins.enabled == false
  CAGE-06 sync.enabled == false
  CAGE-07 telemetry.enabled == false
  CAGE-08 mcp_servers == {}
  CAGE-09 agent.disabled_toolsets contains at minimum: terminal, code_execution, web, browser, mcp, kanban
  CAGE-10 hermes_home and os_user both present, non-empty, and distinct per instance
  CAGE-11 gateway.unauthorized_dm_behavior == "ignore" (ops-console and pr-review)
  CAGE-12 gateway.sender_allowlist entries must resolve to role "founder-integrator" in registries/people/ (ops-console)
  CAGE-13 docker-compose services enforce read_only: true, cap_drop: [ALL], security_opt: [no-new-privileges:true],
          numeric non-root user, and distinct named volumes
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Set, Tuple

import yaml

REQUIRED_DISABLED_TOOLSETS = {
    "terminal",
    "code_execution",
    "web",
    "browser",
    "mcp",
    "kanban",
}

NUMERIC_USER_RE = re.compile(r"^[0-9]+(:[0-9]+)?$")


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_founder_logins(people_dir: str) -> Set[str]:
    """Return set of IDs and GitHub logins of people with role 'founder-integrator'."""
    founders = set()
    if not os.path.isdir(people_dir):
        return founders
    for entry in os.listdir(people_dir):
        if not entry.endswith(".yaml") or entry.startswith("_"):
            continue
        p_path = os.path.join(people_dir, entry)
        try:
            doc = load_yaml(p_path)
            if isinstance(doc, dict) and doc.get("role") == "founder-integrator":
                if doc.get("id"):
                    founders.add(str(doc["id"]))
                if doc.get("github_login"):
                    founders.add(str(doc["github_login"]))
        except Exception:
            pass
    return founders


def check_instance_config(
    path: str,
    doc: dict,
    founders: Set[str],
) -> List[str]:
    errors = []
    basename = os.path.basename(path)

    if not isinstance(doc, dict):
        return ["CAGE file is not a YAML mapping"]

    # CAGE-01: memory.memory_enabled == false
    memory = doc.get("memory")
    if not isinstance(memory, dict) or memory.get("memory_enabled") is not False:
        errors.append("CAGE-01 memory.memory_enabled must be false")

    # CAGE-02: model.background_review.enabled == false
    model = doc.get("model")
    if not isinstance(model, dict):
        errors.append("CAGE-02 model section missing")
    else:
        bg_review = model.get("background_review")
        if not isinstance(bg_review, dict) or bg_review.get("enabled") is not False:
            errors.append("CAGE-02 model.background_review.enabled must be false")

    # CAGE-03: approvals.cron_mode == "deny"
    approvals = doc.get("approvals")
    if not isinstance(approvals, dict) or approvals.get("cron_mode") != "deny":
        errors.append("CAGE-03 approvals.cron_mode must be 'deny'")

    # CAGE-04: security.allow_lazy_installs == false
    security = doc.get("security")
    if not isinstance(security, dict) or security.get("allow_lazy_installs") is not False:
        errors.append("CAGE-04 security.allow_lazy_installs must be false")

    # CAGE-05: plugins.enabled == false
    plugins = doc.get("plugins")
    if not isinstance(plugins, dict) or plugins.get("enabled") is not False:
        errors.append("CAGE-05 plugins.enabled must be false")

    # CAGE-06: sync.enabled == false
    sync = doc.get("sync")
    if not isinstance(sync, dict) or sync.get("enabled") is not False:
        errors.append("CAGE-06 sync.enabled must be false")

    # CAGE-07: telemetry.enabled == false
    telemetry = doc.get("telemetry")
    if not isinstance(telemetry, dict) or telemetry.get("enabled") is not False:
        errors.append("CAGE-07 telemetry.enabled must be false")

    # CAGE-08: mcp_servers == {}
    mcp_servers = doc.get("mcp_servers")
    if not isinstance(mcp_servers, dict) or len(mcp_servers) != 0:
        errors.append("CAGE-08 mcp_servers must be empty dict {}")

    # CAGE-09: agent.disabled_toolsets
    agent = doc.get("agent")
    if not isinstance(agent, dict):
        errors.append("CAGE-09 agent section missing")
    else:
        disabled = agent.get("disabled_toolsets")
        if not isinstance(disabled, list):
            errors.append("CAGE-09 agent.disabled_toolsets must be a list")
        else:
            disabled_set = set(str(item) for item in disabled)
            missing = REQUIRED_DISABLED_TOOLSETS - disabled_set
            if missing:
                errors.append(
                    f"CAGE-09 agent.disabled_toolsets missing required toolsets: {sorted(missing)}"
                )

    # CAGE-10: hermes_home and os_user present and non-empty
    hermes_home = str(doc.get("hermes_home", "")).strip()
    if not hermes_home:
        errors.append("CAGE-10 hermes_home must be present and non-empty")
    os_user = str(doc.get("os_user", "")).strip()
    if not os_user:
        errors.append("CAGE-10 os_user must be present and non-empty")

    # CAGE-11 & CAGE-12: Gateway rules for ops-console and pr-review
    if basename in ("ops-console.yaml", "pr-review.yaml") or "gateway" in doc:
        gateway = doc.get("gateway")
        if not isinstance(gateway, dict):
            errors.append("CAGE-11 gateway section missing")
        else:
            if gateway.get("unauthorized_dm_behavior") != "ignore":
                errors.append("CAGE-11 gateway.unauthorized_dm_behavior must be 'ignore'")

            if basename == "ops-console.yaml":
                allowlist = gateway.get("sender_allowlist")
                if not isinstance(allowlist, list):
                    errors.append("CAGE-12 gateway.sender_allowlist must be a list")
                elif len(allowlist) == 0:
                    errors.append("CAGE-12 gateway.sender_allowlist must not be empty for ops-console")
                else:
                    for sender in allowlist:
                        s_str = str(sender)
                        if s_str not in founders:
                            errors.append(
                                f"CAGE-12 sender_allowlist entry '{s_str}' does not resolve to a founder-integrator"
                            )

    return errors


def check_docker_compose(path: str, doc: dict) -> List[str]:
    errors = []
    if not isinstance(doc, dict):
        return ["CAGE-13 docker-compose is not a YAML mapping"]

    services = doc.get("services")
    if not isinstance(services, dict) or not services:
        return ["CAGE-13 docker-compose has no services defined"]

    seen_volumes: Dict[str, str] = {}  # volume_name -> service_name

    for svc_name, svc in services.items():
        if not isinstance(svc, dict):
            errors.append(f"CAGE-13 service '{svc_name}' is not a mapping")
            continue

        # read_only: true
        if svc.get("read_only") is not True:
            errors.append(f"CAGE-13 service '{svc_name}': read_only must be true")

        # cap_drop: contains ALL
        cap_drop = svc.get("cap_drop")
        if not isinstance(cap_drop, list) or "ALL" not in [str(c).upper() for c in cap_drop]:
            errors.append(f"CAGE-13 service '{svc_name}': cap_drop must contain 'ALL'")

        # security_opt: contains no-new-privileges:true
        sec_opt = svc.get("security_opt")
        if not isinstance(sec_opt, list) or not any("no-new-privileges:true" in str(s) for s in sec_opt):
            errors.append(f"CAGE-13 service '{svc_name}': security_opt must contain 'no-new-privileges:true'")

        # numeric non-root user
        user = str(svc.get("user", "")).strip()
        if not user or not NUMERIC_USER_RE.match(user) or user.startswith("0"):
            errors.append(f"CAGE-13 service '{svc_name}': user '{user}' must be numeric non-root (e.g. 1001:1001)")

        # distinct named volume
        vols = svc.get("volumes", [])
        if not isinstance(vols, list):
            errors.append(f"CAGE-13 service '{svc_name}': volumes must be a list")
        else:
            svc_named_vols = []
            for vol in vols:
                if isinstance(vol, dict) and vol.get("type") == "volume":
                    src = vol.get("source")
                    if src:
                        svc_named_vols.append(str(src))
                elif isinstance(vol, str) and ":" in vol and not vol.startswith("."):
                    src = vol.split(":")[0]
                    if not src.startswith("/") and not src.startswith("."):
                        svc_named_vols.append(src)

            if not svc_named_vols:
                errors.append(f"CAGE-13 service '{svc_name}': missing dedicated named volume")
            for vol_src in svc_named_vols:
                if vol_src in seen_volumes:
                    errors.append(
                        f"CAGE-13 service '{svc_name}': named volume '{vol_src}' is shared with '{seen_volumes[vol_src]}'"
                    )
                else:
                    seen_volumes[vol_src] = svc_name

    return errors


def validate_hermes_cage(
    hermes_dir: str = "infra/hermes",
    people_dir: str = "registries/people",
) -> Tuple[int, List[str]]:
    """Validate all Hermes cage configuration files in hermes_dir."""
    output_lines = []
    total_errors = 0

    if not os.path.isdir(hermes_dir):
        msg = f"FAIL {hermes_dir}: directory not found"
        output_lines.append(msg)
        return 1, output_lines

    founders = get_founder_logins(people_dir)

    # Collect instance YAMLs and docker-compose
    all_files = sorted(os.listdir(hermes_dir))
    config_files = [
        f for f in all_files
        if f.endswith(".yaml") and f != "docker-compose.yaml" and not f.startswith(".")
    ]
    compose_files = [f for f in all_files if f == "docker-compose.yaml"]

    seen_homes: Dict[str, str] = {}
    seen_users: Dict[str, str] = {}

    validated_count = 0

    for cfile in config_files:
        cpath = os.path.join(hermes_dir, cfile)
        try:
            doc = load_yaml(cpath)
        except Exception as e:
            output_lines.append(f"FAIL {cpath}: cannot parse YAML: {e}")
            total_errors += 1
            continue

        errors = check_instance_config(cpath, doc, founders)

        # CAGE-10 distinct check
        home = str(doc.get("hermes_home", "")).strip()
        user = str(doc.get("os_user", "")).strip()
        if home:
            if home in seen_homes:
                errors.append(f"CAGE-10 hermes_home '{home}' is shared with {seen_homes[home]}")
            else:
                seen_homes[home] = cfile
        if user:
            if user in seen_users:
                errors.append(f"CAGE-10 os_user '{user}' is shared with {seen_users[user]}")
            else:
                seen_users[user] = cfile

        if errors:
            total_errors += len(errors)
            for err in errors:
                output_lines.append(f"FAIL {cpath}: {err}")
        else:
            output_lines.append(f"OK {cpath}")
        validated_count += 1

    for cfile in compose_files:
        cpath = os.path.join(hermes_dir, cfile)
        try:
            doc = load_yaml(cpath)
        except Exception as e:
            output_lines.append(f"FAIL {cpath}: cannot parse YAML: {e}")
            total_errors += 1
            continue

        errors = check_docker_compose(cpath, doc)
        if errors:
            total_errors += len(errors)
            for err in errors:
                output_lines.append(f"FAIL {cpath}: {err}")
        else:
            output_lines.append(f"OK {cpath}")
        validated_count += 1

    if total_errors:
        output_lines.append(f"HERMES-CAGE-VALIDATE: FAIL ({total_errors} errors)")
        return 1, output_lines

    output_lines.append(f"HERMES-CAGE-VALIDATE: PASS ({validated_count} files validated)")
    return 0, output_lines


def main():
    parser = argparse.ArgumentParser(description="Validate Hermes Agent cage configuration")
    parser.add_argument("--dir", default="infra/hermes", help="Directory containing cage configurations")
    parser.add_argument("--people-dir", default="registries/people", help="Directory containing people registry")
    args = parser.parse_args()

    rc, lines = validate_hermes_cage(hermes_dir=args.dir, people_dir=args.people_dir)
    for line in lines:
        print(line)
    return rc


if __name__ == "__main__":
    sys.exit(main())
