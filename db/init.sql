-- =============================================================================
-- Init script for PostgreSQL 16/17 – full schema for the banking platform
--
-- Fixes applied vs. the original draft:
--   1. transaction / audit_log primary keys made composite (id, partition_col)
--      because PostgreSQL requires a partitioned table's PK/UNIQUE constraints
--      to include the partition key column. Without this the CREATE TABLE
--      statements fail outright.
--   2. ml_score / alert now carry the transaction's occurred_at and use a
--      composite FK (transaction_id, transaction_occurred_at) back to
--      transaction, since a FK must reference an actual unique constraint,
--      and transaction_id alone is no longer uniquely constrained by itself.
--   3. Added DEFAULT partitions on transaction and audit_log so inserts for
--      any date not covered by an explicit range partition (e.g. anything
--      from today onward) don't fail with "no partition of relation found".
--   4. fn_audit() no longer assumes a column named "id" (no table has one);
--      it derives the PK value dynamically from "<table_name>_id".
--   5. fn_encrypt_pan() no longer uses invalid psql-variable syntax
--      (":replace_this_key:"); it reads the key from a session GUC that the
--      application must set (app.pan_encryption_key).
--   6. Added the unique index account_balance_mv needs for
--      REFRESH MATERIALIZED VIEW CONCURRENTLY to work at all.
-- All original tables, columns, indexes, RLS policies and comments are kept.
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ENUM Types
CREATE TYPE account_type_enum AS ENUM ('checking','savings','term_deposit','credit_card','loan');
CREATE TYPE account_status_enum AS ENUM ('active','suspended','closed');
CREATE TYPE transaction_type_enum AS ENUM ('deposit','withdrawal','transfer','payment','fee');
CREATE TYPE transaction_status_enum AS ENUM ('pending','settled','reversed','failed');
CREATE TYPE alert_type_enum AS ENUM ('fraud','overdraft','cross_sell','policy_violation');
CREATE TYPE alert_status_enum AS ENUM ('open','acknowledged','closed');
CREATE TYPE notification_type_enum AS ENUM ('email','push','sms');

-- Reference tables
CREATE TABLE currency (
    currency_code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(5)
);
CREATE TABLE address (
    address_id BIGSERIAL PRIMARY KEY,
    street VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ
);
CREATE TABLE exchange_rate (
    rate_id BIGSERIAL PRIMARY KEY,
    source_currency CHAR(3) NOT NULL REFERENCES currency(currency_code),
    target_currency CHAR(3) NOT NULL REFERENCES currency(currency_code),
    rate NUMERIC(12,6) NOT NULL CHECK (rate > 0),
    effective_date DATE NOT NULL,
    UNIQUE (source_currency, target_currency, effective_date)
);
CREATE TABLE agency (
    agency_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    address_id BIGINT REFERENCES address(address_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ
);
CREATE TABLE ia_model (
    model_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    trained_at TIMESTAMPTZ NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Core domain entities
CREATE TABLE client (
    client_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    address_id BIGINT REFERENCES address(address_id),
    national_id VARCHAR(30) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE employee (
    employee_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    agency_id BIGINT NOT NULL REFERENCES agency(agency_id),
    email VARCHAR(255) NOT NULL UNIQUE,
    position VARCHAR(100),
    hire_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE "user" (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    client_id BIGINT UNIQUE REFERENCES client(client_id) ON DELETE SET NULL,
    employee_id BIGINT UNIQUE REFERENCES employee(employee_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    last_login TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE role (
    role_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE permission (
    permission_id BIGSERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE user_role (
    user_id BIGINT NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES role(role_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
CREATE TABLE role_permission (
    role_id BIGINT NOT NULL REFERENCES role(role_id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES permission(permission_id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
CREATE TABLE account (
    account_id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES client(client_id) ON DELETE RESTRICT,
    agency_id BIGINT NOT NULL REFERENCES agency(agency_id),
    currency_code CHAR(3) NOT NULL REFERENCES currency(currency_code),
    account_number VARCHAR(20) NOT NULL UNIQUE,
    account_type account_type_enum NOT NULL,
    balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    status account_status_enum NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Card & Payment (PCI‑DSS)
CREATE TABLE card (
    card_id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES account(account_id) ON DELETE RESTRICT,
    encrypted_pan BYTEA NOT NULL,
    expiration_month SMALLINT NOT NULL CHECK (expiration_month BETWEEN 1 AND 12),
    expiration_year SMALLINT NOT NULL,
    cvv_hash VARCHAR(255) NOT NULL,
    card_type VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Loans (simplified)
CREATE TABLE loan (
    loan_id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES client(client_id) ON DELETE RESTRICT,
    account_id BIGINT NOT NULL REFERENCES account(account_id) ON DELETE RESTRICT,
    principal_amount NUMERIC(18,2) NOT NULL CHECK (principal_amount > 0),
    currency_code CHAR(3) NOT NULL REFERENCES currency(currency_code),
    interest_rate NUMERIC(5,4) NOT NULL CHECK (interest_rate >= 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending','active','closed','defaulted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Transactions (partitioned by occurred_at)
-- NOTE: PostgreSQL requires that a partitioned table's PRIMARY KEY / UNIQUE
-- constraints include the partition key. transaction_id is still globally
-- unique in practice (it comes from a single sequence), but Postgres can
-- only *enforce and reference* uniqueness via the composite key below.
CREATE TABLE transaction (
    transaction_id BIGSERIAL,
    account_id BIGINT NOT NULL REFERENCES account(account_id) ON DELETE RESTRICT,
    counterparty_account VARCHAR(20),
    amount NUMERIC(18,2) NOT NULL CHECK (amount <> 0),
    currency_code CHAR(3) NOT NULL REFERENCES currency(currency_code),
    transaction_type transaction_type_enum NOT NULL,
    status transaction_status_enum NOT NULL DEFAULT 'pending',
    occurred_at TIMESTAMPTZ NOT NULL,
    posted_at TIMESTAMPTZ,
    description VARCHAR(255),
    is_fraudulent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT chk_settled_posted CHECK (status <> 'settled' OR posted_at IS NOT NULL),
    PRIMARY KEY (transaction_id, occurred_at)
) PARTITION BY RANGE (occurred_at);
-- Example monthly partitions – generate more as needed
CREATE TABLE transaction_2024_01 PARTITION OF transaction FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE transaction_2024_02 PARTITION OF transaction FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- Catch-all partition so inserts for any date not yet given an explicit
-- range (e.g. anything from 2024-03 onward, including today) don't fail
-- with "no partition of relation found for row". Split rows out of the
-- default into dedicated partitions over time as your retention job runs.
CREATE TABLE transaction_default PARTITION OF transaction DEFAULT;

-- ML Score & Alerts
-- transaction_occurred_at is stored here so the FK below can reference the
-- transaction table's composite key (transaction_id, occurred_at) — a FK
-- can only point at columns backed by an actual unique constraint, and on
-- a partitioned table that constraint must include the partition column.
CREATE TABLE ml_score (
    score_id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    transaction_occurred_at TIMESTAMPTZ NOT NULL,
    model_id BIGINT NOT NULL REFERENCES ia_model(model_id),
    risk_score NUMERIC(5,4) NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    shap_values JSONB,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_ml_score_transaction FOREIGN KEY (transaction_id, transaction_occurred_at)
        REFERENCES transaction (transaction_id, occurred_at) ON DELETE CASCADE
);
CREATE TABLE alert (
    alert_id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL UNIQUE,
    transaction_occurred_at TIMESTAMPTZ NOT NULL,
    score_id BIGINT NOT NULL REFERENCES ml_score(score_id) ON DELETE RESTRICT,
    alert_type alert_type_enum NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    CONSTRAINT fk_alert_transaction FOREIGN KEY (transaction_id, transaction_occurred_at)
        REFERENCES transaction (transaction_id, occurred_at) ON DELETE RESTRICT
);

-- Notifications
CREATE TABLE notification (
    notification_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type notification_type_enum NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ
);

-- Audit Log (partitioned by performed_at) – same composite-PK requirement
-- as transaction above.
CREATE TABLE audit_log (
    audit_id BIGSERIAL,
    entity_name VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    action VARCHAR(30) NOT NULL,
    performed_by BIGINT REFERENCES "user"(user_id),
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    change_summary JSONB,
    comment TEXT,
    PRIMARY KEY (audit_id, performed_at)
) PARTITION BY RANGE (performed_at);
CREATE TABLE audit_log_2024 PARTITION OF audit_log FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE audit_log_2025 PARTITION OF audit_log FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
-- Catch-all partition for any year not yet given an explicit range
-- (e.g. 2026 onward). Without this, audit inserts today would fail.
CREATE TABLE audit_log_default PARTITION OF audit_log DEFAULT;

-- Indexes
CREATE UNIQUE INDEX uq_account_number ON account(account_number);
CREATE INDEX idx_transaction_account_date ON transaction(account_id, occurred_at DESC);
CREATE INDEX idx_transaction_status_pending ON transaction(status) WHERE status = 'pending';
CREATE INDEX idx_ml_score_tx ON ml_score(transaction_id);
CREATE INDEX idx_alert_status ON alert(status);
CREATE INDEX idx_audit_entity_time ON audit_log(entity_name, performed_at DESC);
CREATE INDEX idx_notification_user_unread ON notification(user_id) WHERE read_at IS NULL;
CREATE INDEX idx_exchange_rate_pair_date ON exchange_rate(source_currency, target_currency, effective_date);
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_role_name ON role(name);
CREATE INDEX idx_permission_action ON permission(action);

-- Materialized view for balances
CREATE MATERIALIZED VIEW account_balance_mv AS
SELECT a.account_id,
       a.currency_code,
       SUM(t.amount) FILTER (WHERE t.status = 'settled') AS balance
FROM account a
LEFT JOIN transaction t ON t.account_id = a.account_id
GROUP BY a.account_id, a.currency_code
WITH DATA;

-- Required for REFRESH MATERIALIZED VIEW CONCURRENTLY below: Postgres needs
-- a unique index on the view or the refresh fails at call time.
CREATE UNIQUE INDEX uq_account_balance_mv_account ON account_balance_mv(account_id);

-- Refresh function for the materialized view
CREATE OR REPLACE FUNCTION refresh_account_balance_mv()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY account_balance_mv;
END;
$$;

-- Trigger functions (audit, immutability, blocked accounts, PAN encryption)
CREATE OR REPLACE FUNCTION fn_audit()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_old JSONB;
    v_new JSONB;
    v_entity_id BIGINT;
BEGIN
    -- Every audited table uses "<table_name>_id" as its primary key column
    -- (account_id, transaction_id, ...), not a generic "id" column, so the
    -- PK value is looked up dynamically via TG_TABLE_NAME.
    IF TG_OP = 'INSERT' THEN
        v_new := to_jsonb(NEW);
        v_entity_id := (v_new ->> (TG_TABLE_NAME || '_id'))::BIGINT;
        INSERT INTO audit_log(entity_name, entity_id, action, performed_by, change_summary)
        VALUES (TG_TABLE_NAME, v_entity_id, TG_OP, current_setting('app.current_user_id', true)::BIGINT, jsonb_build_object('new', v_new));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
        v_entity_id := (v_new ->> (TG_TABLE_NAME || '_id'))::BIGINT;
        INSERT INTO audit_log(entity_name, entity_id, action, performed_by, change_summary)
        VALUES (TG_TABLE_NAME, v_entity_id, TG_OP, current_setting('app.current_user_id', true)::BIGINT,
                jsonb_build_object('old', v_old, 'new', v_new));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_old := to_jsonb(OLD);
        v_entity_id := (v_old ->> (TG_TABLE_NAME || '_id'))::BIGINT;
        INSERT INTO audit_log(entity_name, entity_id, action, performed_by, change_summary)
        VALUES (TG_TABLE_NAME, v_entity_id, TG_OP, current_setting('app.current_user_id', true)::BIGINT,
                jsonb_build_object('old', v_old));
        RETURN OLD;
    END IF;
END;
$$;
CREATE TRIGGER trg_audit_account AFTER INSERT OR UPDATE OR DELETE ON account FOR EACH ROW EXECUTE FUNCTION fn_audit();
CREATE TRIGGER trg_audit_transaction AFTER INSERT OR UPDATE OR DELETE ON transaction FOR EACH ROW EXECUTE FUNCTION fn_audit();

CREATE OR REPLACE FUNCTION fn_immutable_settled()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status = 'settled' THEN
        RAISE EXCEPTION 'A settled transaction is immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER trg_immutable_settled BEFORE UPDATE ON transaction FOR EACH ROW EXECUTE FUNCTION fn_immutable_settled();

CREATE OR REPLACE FUNCTION fn_block_suspended_account()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_status account_status_enum;
BEGIN
    SELECT status INTO v_status FROM account WHERE account_id = NEW.account_id;
    IF v_status = 'suspended' THEN
        RAISE EXCEPTION 'Cannot create a transaction on a suspended account';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER trg_block_suspended_account BEFORE INSERT ON transaction FOR EACH ROW EXECUTE FUNCTION fn_block_suspended_account();

CREATE OR REPLACE FUNCTION fn_encrypt_pan()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- The encryption key is read from a session-level setting the
    -- application must configure (e.g. SET app.pan_encryption_key = '...'
    -- per connection/session, or ALTER DATABASE ... SET). The previous
    -- placeholder ":replace_this_key:" was psql-variable syntax and is not
    -- valid inside a stored function body — CREATE FUNCTION would fail.
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.encrypted_pan IS DISTINCT FROM OLD.encrypted_pan) THEN
        NEW.encrypted_pan := pgp_sym_encrypt(NEW.encrypted_pan::text, current_setting('app.pan_encryption_key'));
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER trg_encrypt_pan BEFORE INSERT OR UPDATE ON card FOR EACH ROW EXECUTE FUNCTION fn_encrypt_pan();

-- Row‑Level Security
ALTER TABLE account ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction ENABLE ROW LEVEL SECURITY;
ALTER TABLE client ENABLE ROW LEVEL SECURITY;
CREATE POLICY client_account_policy ON account USING (client_id = current_setting('app.current_client_id')::BIGINT);
CREATE POLICY client_transaction_policy ON transaction USING (account_id IN (SELECT account_id FROM account WHERE client_id = current_setting('app.current_client_id')::BIGINT));
CREATE POLICY admin_bypass_account ON account USING (current_setting('app.is_admin', true)::BOOLEAN);
CREATE POLICY admin_bypass_transaction ON transaction USING (current_setting('app.is_admin', true)::BOOLEAN);

-- Documentation comments
COMMENT ON TABLE client IS 'Natural person or corporate entity that owns banking products';
COMMENT ON COLUMN client.national_id IS 'Government‑issued identifier (passport, SSN, CIN) – required for KYC';
COMMENT ON TABLE account IS 'Core deposit / credit product – balance is derived from settled transactions';
COMMENT ON COLUMN account.is_deleted IS 'Soft‑delete flag; rows stay for audit & referential integrity';
COMMENT ON TABLE transaction IS 'Immutable once settled; partitioned monthly for massive scale';
COMMENT ON COLUMN transaction.is_fraudulent IS 'Flag set by AI engine – triggers alert generation';
COMMENT ON TABLE card IS 'PCI‑DSS compliant storage – PAN encrypted, CVV hashed';
COMMENT ON TABLE audit_log IS 'Append‑only immutable log for regulatory compliance (7‑year retention)';
COMMENT ON TABLE exchange_rate IS 'Daily rates – used for multi‑currency conversions in reporting';
COMMENT ON MATERIALIZED VIEW account_balance_mv IS 'Fast pre‑aggregated balance view refreshed every minute';
COMMENT ON FUNCTION fn_audit IS 'Generic audit trigger – records before/after JSON snapshots';
COMMENT ON FUNCTION fn_immutable_settled IS 'Prevents modification of settled transactions';
COMMENT ON FUNCTION fn_block_suspended_account IS 'Blocks new transactions on suspended accounts';
COMMENT ON FUNCTION fn_encrypt_pan IS 'Encrypts PAN with pgp_sym_encrypt – key must be supplied by the app';
COMMENT ON POLICY client_account_policy ON account IS 'Ensures a client can only access his/her own accounts';
COMMENT ON POLICY client_transaction_policy ON transaction IS 'Ensures a client can only see transactions belonging to his/her accounts';
