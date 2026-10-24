-- Pilot Change: Add disabled_at to customer record
ALTER TABLE customers ADD COLUMN disabled_at TIMESTAMP WITH TIME ZONE NULL;
