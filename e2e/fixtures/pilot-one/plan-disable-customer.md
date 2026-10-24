# Pilot Change Plan: Disable Customer

## Summary
Add `disabled_at` timestamp to customer record and implement `POST /customers/{id}/disable`.

## Change Class
normal

## Impact Scope
single-product

## Reversibility
fully-reversible

## Automated Verification Commands
```bash
python -m pytest tests/test_disable_customer.py
```

## Rollback Strategy
Revert migration `002_add_disabled_at.sql` and restore previous container digest. Fully backwards-compatible.
