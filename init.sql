-- =============================================================================
-- PostgreSQL initialization script
-- Runs once when the container is first created
-- =============================================================================

-- Enable UUID generation (used by Transaction.transaction_id)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set timezone to UTC
ALTER DATABASE bank_management SET timezone TO 'UTC';