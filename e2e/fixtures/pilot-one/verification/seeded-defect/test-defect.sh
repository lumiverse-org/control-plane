#!/usr/bin/env bash
# Seeded defect that triggers an assertion failure
echo "assertion failed: seeded-defect detected in customer status handler" >&2
exit 1
