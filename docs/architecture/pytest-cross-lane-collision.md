# Cross-Lane Pytest Collection Collision Report

**Date:** 2026-10-23  
**Status:** REPORTED (Do not silently fix — requires lane-guard architectural review)  
**Governance:** AGENTS.md §2 (radical honesty, zero unevidenced changes)

---

## 1. Executive Summary

When test suites are invoked independently per lane or per test package, all test suites execute cleanly and pass:
- `python -m pytest reconciler -q` &rarr; **300 passed**
- `python -m pytest validators -q` &rarr; **756 passed, 3 xfailed**
- `python -m pytest access -q` &rarr; **28 passed**
- `python -m pytest tools/records/tests -q` &rarr; **57 passed**
- `python -m pytest tools/evidence/tests -q` &rarr; **149 passed**
- `python -m pytest tools/hermes/tests -q` &rarr; **6 passed**

However, invoking pytest across multiple lane roots in a single invocation:
```bash
python -m pytest reconciler validators access tools -q
```
aborts test collection with **9 errors**:
```
ModuleNotFoundError: No module named 'tests.test_event_append'
ModuleNotFoundError: No module named 'tests.test_eventpath'
ModuleNotFoundError: No module named 'tests.test_mint_token'
ModuleNotFoundError: No module named 'tests.test_nooverwrite'
ModuleNotFoundError: No module named 'tests.test_record_decision'
ModuleNotFoundError: No module named 'tests.test_record_write'
ModuleNotFoundError: No module named 'tests.test_rvr'
ModuleNotFoundError: No module named 'tests.test_rwtoken'
ModuleNotFoundError: No module named 'tests.test_writer'
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!
============================= 9 errors in 12.23s ==============================
```

---

## 2. Root Cause Analysis

The root cause is a Python module-name collision in pytest's standard `prepend` rootdir import mode:
1. Multiple engineering lanes maintain test directories named bare `tests/` without qualified namespace package wrappers:
   - `reconciler/tests/` (Lane 3)
   - `validators/registry/tests/` (Lane 1)
   - `access/tests/` (Lane 5)
   - `tools/records/tests/` (Lane 4)
   - `tools/evidence/tests/` (Lane 2)
   - `tools/hermes/tests/` (Lane 5)
2. When pytest collects tests across all four lane roots (`reconciler`, `validators`, `access`, `tools`), `reconciler/tests` is discovered first and loaded into Python's `sys.modules` under the top-level name `tests`.
3. When collection progresses to `tools/records/tests/`, pytest attempts to import test files like `tools/records/tests/test_event_append.py` as `tests.test_event_append`. Because `sys.modules["tests"]` already points to `reconciler/tests`, Python looks for `test_event_append` inside `reconciler/tests/`, fails to locate it, and raises:
   `ModuleNotFoundError: No module named 'tests.test_event_append'`.

---

## 3. Why This Is Not Silently Fixed

Resolving this collision requires one of the following architectural changes:
1. Adding `--import-mode=importlib` to `pytest.ini` at repository root.
2. Renaming test directories to qualified package paths (e.g., `tools/records/record_tests/`, `reconciler/reconciler_tests/`).
3. Adding explicit `__init__.py` files creating distinct top-level packages.

Any of these modifications represents a **cross-lane structural change** touching files governed by Lane 0, Lane 1, Lane 2, Lane 3, and Lane 4. Per `AGENTS.md` and repository lane-guard discipline:
- No lane runner or automated agent may modify cross-lane test discovery configurations or rename sibling lane packages without explicit Founder review.
- CI and lane self-checks currently invoke each lane's test suites by scoped target paths (e.g. `pytest reconciler/`, `pytest validators/registry/tests/`, `pytest tools/records/tests/`), which succeed completely without error.

---

## 4. Live Command Evidence

### Per-Lane Isolated Invocations (All PASS)
```text
$ python -m pytest reconciler -q
============================= 300 passed in 5.88s =============================

$ python -m pytest validators -q
======================= 756 passed, 3 xfailed in 21.82s =======================

$ python -m pytest access -q
============================= 28 passed in 13.11s =============================

$ python -m pytest tools/records/tests -q
======================= 57 passed, 6 warnings in 3.56s ========================

$ python -m pytest tools/evidence/tests -q
============================ 149 passed in 35.83s =============================

$ python -m pytest tools/hermes/tests -q
============================== 6 passed in 0.14s ==============================
```

### Combined Cross-Lane Invocation (FAIL)
```text
$ python -m pytest reconciler validators access tools -q
collected 1362 items / 9 errors

ERROR tools/records/tests/test_event_append.py
ERROR tools/records/tests/test_eventpath.py
ERROR tools/records/tests/test_mint_token.py
ERROR tools/records/tests/test_nooverwrite.py
ERROR tools/records/tests/test_record_decision.py
ERROR tools/records/tests/test_record_write.py
ERROR tools/records/tests/test_rvr.py
ERROR tools/records/tests/test_rwtoken.py
ERROR tools/records/tests/test_writer.py
ModuleNotFoundError: No module named 'tests.test_event_append'
```
