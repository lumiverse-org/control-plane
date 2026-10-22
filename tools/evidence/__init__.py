"""tools.evidence — subsystem F, the production evidence toolchain (Lane 2 Pipeline & Evidence).

Package root for every tools/evidence/** module. Exports TOOL_CONTRACT, the single definition of
the Section 0.4 deterministic output-contract grammar (lanes/L2-05-tasks.md Section 0.4), so every
later module under this tree imports the grammar instead of restating it.

Deterministic output contract (Section 0.4): every program under tools/evidence/ accepts --summary
and prints, on --summary, exactly one line to stdout matching TOOL_CONTRACT below. Diagnostic detail
goes to stderr, never stdout.

Toolchain: Python 3.12, dependencies pinned by exact ==, no lockfile generator. This is FD-005 /
REG-003 (lanes/L0-04-decisions-register.md), Option A, decided 2026-09-02, state "Closed" -- the
live, ratified answer for every lane, Lane 2 included. (This task's own Deps column cites "D-L2-07";
this file's own Section 1 now defines D-L2-07 as something unrelated -- feature-branch merge
criteria, reconciled 2026-09-09 per FD-084. REG-003's "Raised as" row still lists the original
"D-L2-07 (lanes/L2-05 Section 1)" as one of ten lane-local aliases for the one toolchain question,
which is FD-005/REG-003 and which is already closed as Python 3.12 with == pins -- exactly what this
file assumes. There is nothing open here to STOP on.)

Namespace-package rule (Section 0.1): tools/ itself stays an implicit PEP 420 namespace package.
Do not add tools/__init__.py -- tools/provision/** is Lane 3's and tools/records/** is Lane 4's, and
a tools/__init__.py write is a foreign-path write that lane-guard rejects.

Authority: lanes/L2-05-tasks.md L2-T530.
"""

TOOL_CONTRACT = "<STATUS> <tool-id> checked=<int> failed=<int>"
STATUS_OK, STATUS_FAIL, STATUS_ERROR = "OK", "FAIL", "ERROR"
EXIT_OK, EXIT_FAIL, EXIT_ERROR = 0, 2, 3
