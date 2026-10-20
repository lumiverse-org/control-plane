#!/usr/bin/env python3
"""Notification router (Spec Sections 92.11, 92.1; D79; AT-106; §90.2).

Resolves an event type against the closed push list and prints exactly one
decision line. It never sends anything, never invents a destination, and
never picks between two matching routes.

Decisions:
  ROUTE: PUSH <configuration-key> (class=<push_class>, route=<route_id>)
  ROUTE: DIGEST morning-digest (class=<push_class>, route=<route_id>, D79)
  ROUTE: REFUSED (<event_type> is not on the Section 92.11 closed push list)
  ROUTE: AMBIGUOUS (<n> routes for <event_type>: a, b)
  ROUTE: BLOCKED (<reason>)

An optional --payload is checked by the Layer-B content guard
(notify/tools/layerb_guard.py, Section 90.2) before any destination is
resolved: a guarded refusal is reported as ROUTE: BLOCKED and wins over an
otherwise-resolvable event, on or off the push list.

Exit codes: 0 push or digest, 2 ambiguous or blocked, 3 refused.

Usage: route.py --list
       route.py --event-type <id> [--route <route-id>] [--clock yes|no]
                [--payload <json>]
"""
import argparse
import importlib.util
import json
import os
import sys

import yaml

ROUTING = os.path.join("notify", "routing")
CHANNELS = os.path.join("notify", "channels")
LAYERB_GUARD_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tools", "layerb_guard.py")


def load_layerb_guard():
    """Loads notify/tools/layerb_guard.py by file path, so this router calls
    the real Layer-B content guard regardless of cwd or how route.py itself
    was invoked (script or module)."""
    spec = importlib.util.spec_from_file_location(
        "layerb_guard", LAYERB_GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_routes():
    routes = {}
    if not os.path.isdir(ROUTING):
        return routes
    for name in sorted(os.listdir(ROUTING)):
        if not name.endswith(".yaml"):
            continue
        with open(os.path.join(ROUTING, name), "r",
                  encoding="utf-8") as handle:
            doc = yaml.safe_load(handle) or {}
        if isinstance(doc, dict) and doc.get("route_id"):
            routes[str(doc["route_id"])] = doc
    return routes


def channel_key(channel_id):
    path = os.path.join(CHANNELS, "%s.yaml" % channel_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        doc = yaml.safe_load(handle) or {}
    key = str(doc.get("configuration_key", "")).strip()
    return key or None


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--list", dest="listing", action="store_true")
    parser.add_argument("--event-type", dest="event_type", default=None)
    parser.add_argument("--route", dest="route_id", default=None)
    parser.add_argument("--clock", dest="clock", choices=["yes", "no"],
                        default=None)
    parser.add_argument("--payload", dest="payload", default=None,
                        help="JSON event content, checked by the Layer-B "
                             "content guard before a destination resolves")
    args = parser.parse_args()

    routes = load_routes()
    if not routes:
        print("ROUTE: BLOCKED (no routes declared under %s)" % ROUTING)
        return 2

    if args.listing:
        for route_id in sorted(routes):
            doc = routes[route_id]
            print("%s %s %s" % (route_id, doc.get("event_type"),
                                doc.get("push_class")))
        print("ROUTES: %d" % len(routes))
        return 0

    if not args.event_type:
        print("ROUTE: BLOCKED (no --event-type given)")
        return 2

    matches = [r for r in sorted(routes)
               if str(routes[r].get("event_type")) == args.event_type]
    if args.route_id:
        matches = [r for r in matches if r == args.route_id]
    if not matches:
        print("ROUTE: REFUSED (%s is not on the Section 92.11 closed push "
              "list)" % args.event_type)
        return 3
    if len(matches) > 1:
        print("ROUTE: AMBIGUOUS (%d routes for %s: %s)"
              % (len(matches), args.event_type, ", ".join(matches)))
        return 2

    route_id = matches[0]
    doc = routes[route_id]

    if args.payload is not None:
        layerb_guard = load_layerb_guard()
        try:
            payload = json.loads(args.payload)
        except (TypeError, json.JSONDecodeError):
            print("ROUTE: BLOCKED (--payload is not valid JSON)")
            return 2
        try:
            violation = layerb_guard.check_payload(payload)
        except layerb_guard.GuardFailClosed as exc:
            print("ROUTE: BLOCKED (Layer B content guard fail-closed: %s)"
                  % exc)
            return 2
        if violation is not None:
            field, category = violation
            print("ROUTE: BLOCKED (Layer B content guard refused: payload "
                  "field %s matches data category %s)" % (field, category))
            return 2

    if args.clock is None:
        clock = bool(doc.get("carries_clock"))
    else:
        clock = args.clock == "yes"

    if bool(doc.get("coalesce_into_morning_digest")) and not clock:
        print("ROUTE: DIGEST morning-digest (class=%s, route=%s, D79)"
              % (doc.get("push_class"), route_id))
        return 0

    key = channel_key(str(doc.get("destination_channel")))
    if key is None:
        print("ROUTE: BLOCKED (channel %r declares no configuration_key)"
              % doc.get("destination_channel"))
        return 2
    print("ROUTE: PUSH %s (class=%s, route=%s)"
          % (key, doc.get("push_class"), route_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
