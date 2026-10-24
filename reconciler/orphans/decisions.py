"""
reconciler/orphans/decisions.py — Decision constants for orphan detection and expiry warnings.

Spec: lanes/L3-05-orphans.md §5 (DECISION REQUIRED: DR-L3-05-A through DR-L3-05-E).

Values are supplied by L0 on the blocker issue and pasted here verbatim.
Do not invent a value.
# FROM REG-039: replace None with the approved literal values.

Decisions:
- DR-L3-05-A: Operational asset inventory location and type vocabulary (blocks L3-05-10..13)
- DR-L3-05-B: Delegation-type assignment types (blocks L3-05-26, L3-P0-DEL14)
- DR-L3-05-C: Board snapshot source and shape for H1 items (blocks L3-05-17)
- DR-L3-05-D: Open gate-relevant work input surface (blocks L3-05-18, L3-05-27)
- DR-L3-05-E: Customer commitment owner resolution rule (blocks L3-05-14)
"""

# DR-L3-05-A: Operational asset inventory location and type vocabulary
ASSET_INVENTORY_PATHS = None
ASSET_ENTRIES_KEY = None
ASSET_ID_KEY = None
ASSET_OWNER_KEY = None
ASSET_TYPE_KEY = None
ASSET_TYPE_CERTIFICATE = None
ASSET_TYPE_DOMAIN = None
ASSET_TYPE_VENDOR = None

# DR-L3-05-B: Delegation-type assignment types
# FD-129 specifies a general principle ("temporary or acting assignments only")
# with illustrative examples ("e.g. acting-team-lead, temporary coverage roles"),
# not an exhaustive closed list. Only "acting-team-lead" matches a confirmed real
# role definition in this repository (registries/roles/acting-team-lead.yaml).
# The remaining scope of "temporary coverage roles" versus assignments[].type
# delegates remains an open interpretation question pending formal L0 enumeration.
DELEGATION_WARNING_TYPES = (
    "acting-team-lead",
)

# DR-L3-05-C: Board snapshot source and shape for H1 items
BOARD_SNAPSHOT_PATH = None
BOARD_ITEMS_KEY = None
BOARD_ITEM_ID_KEY = None
BOARD_ASSIGNEE_KEY = None
BOARD_COLUMN_KEY = None
BOARD_BLOCKED_KEY = None
BOARD_H1_COLUMNS = None

# DR-L3-05-D: Open gate-relevant work input surface
OPEN_WORK_SNAPSHOT_PATH = None
OPEN_WORK_ITEMS_KEY = None
OPEN_WORK_ID_KEY = None
OPEN_WORK_HOLDER_KEY = None
OPEN_WORK_KIND_KEY = None
OPEN_WORK_PRODUCT_KEY = None
OPEN_WORK_GATE_RELEVANT_KINDS = None

# DR-L3-05-E: Customer commitment owner resolution rule
COMMITMENT_OWNER_RESOLUTION = None
