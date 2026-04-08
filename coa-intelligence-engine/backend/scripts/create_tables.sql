-- ============================================================
-- CoA Intelligence Engine — Supabase Database Schema
-- Run this in the Supabase SQL editor to create all tables
-- ============================================================

-- Enable UUID extension (already enabled on Supabase by default)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Reference tables ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    grade       TEXT,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS spec_tables (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id     UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    version        TEXT NOT NULL,
    effective_date TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, version)
);

CREATE TABLE IF NOT EXISTS spec_parameters (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_table_id       UUID NOT NULL REFERENCES spec_tables(id) ON DELETE CASCADE,
    parameter_name      TEXT NOT NULL,
    method_reference    TEXT,
    specification_limit TEXT NOT NULL,
    is_quantitative     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── Transactional tables ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS coa_submissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_filename   TEXT NOT NULL,
    file_path           TEXT NOT NULL,
    file_size_bytes     BIGINT NOT NULL,
    mime_type           TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','processing','completed','failed')),
    page_count          INT,
    pages_processed     INT NOT NULL DEFAULT 0,
    matched_product_id  UUID REFERENCES products(id),
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS coa_extractions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id         UUID NOT NULL REFERENCES coa_submissions(id) ON DELETE CASCADE,
    product_name          TEXT,
    product_grade         TEXT,
    supplier_name         TEXT,
    batch_number          TEXT,
    manufacture_date      TEXT,
    expiry_date           TEXT,
    coa_number            TEXT,
    header_confidence     FLOAT,
    raw_extraction_json   JSONB NOT NULL,
    extraction_notes      TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS coa_parameter_results (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id           UUID NOT NULL REFERENCES coa_submissions(id) ON DELETE CASCADE,
    parameter_name          TEXT NOT NULL,
    method_reference        TEXT,
    result_value            TEXT NOT NULL,
    result_unit             TEXT,
    specification_limit     TEXT,
    coa_pass_fail           TEXT,
    extraction_confidence   FLOAT NOT NULL,
    validation_status       TEXT NOT NULL
                                CHECK (validation_status IN ('PASS','WARNING','FAIL','REVIEW','ERROR')),
    margin_from_boundary    FLOAT,
    spec_parameter_id       UUID REFERENCES spec_parameters(id),
    is_quantitative         BOOLEAN NOT NULL DEFAULT TRUE,
    validation_notes        TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_coa_submissions_status
    ON coa_submissions(status);

CREATE INDEX IF NOT EXISTS idx_coa_submissions_created_at
    ON coa_submissions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_coa_extractions_submission_id
    ON coa_extractions(submission_id);

CREATE INDEX IF NOT EXISTS idx_coa_parameter_results_submission_id
    ON coa_parameter_results(submission_id);

CREATE INDEX IF NOT EXISTS idx_spec_parameters_spec_table_id
    ON spec_parameters(spec_table_id);

-- ─── Storage bucket ───────────────────────────────────────────────────────────
-- Run this separately or via Supabase dashboard:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('coa-uploads', 'coa-uploads', false);
