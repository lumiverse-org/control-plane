# Lane 5 ownership manifest
Lane 5 (Access, Infra and Ops) owns exactly these paths in control-plane:
access/**  infra/**  ops-vm/**  notify/**  assets/**
Subsystems: K (AI runtime contract enforcement), L (access-control architecture),
M (operations VM), Q (asset inventory and deadline watch), R (notification routing).
Lane 5 writes NO file under: contracts/, docs/, CODEOWNERS, Makefile, root files,
schemas/, registries/, validators/, .github/workflows/, templates/, tools/,
reconciler/, metrics/, and nothing in the control-plane-records repository.
Source of this rule: Code/implementation/PARTITION.md v1 (FROZEN).
