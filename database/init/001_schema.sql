CREATE EXTENSION IF NOT EXISTS vector;

-- Stage 1 foundation only. Later stages will add source/version and ingestion tables.
CREATE TABLE IF NOT EXISTS statutes (
    id BIGSERIAL PRIMARY KEY,
    jurisdiction TEXT NOT NULL DEFAULT 'Ireland',
    title TEXT NOT NULL,
    short_title TEXT,
    year INTEGER,
    official_identifier TEXT UNIQUE,
    source_url TEXT,
    source_type TEXT NOT NULL DEFAULT 'act',
    text_status TEXT NOT NULL DEFAULT 'unverified',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS provisions (
    id BIGSERIAL PRIMARY KEY,
    statute_id BIGINT NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    provision_number TEXT NOT NULL,
    heading TEXT,
    body TEXT NOT NULL,
    source_url TEXT,
    text_status TEXT NOT NULL DEFAULT 'unverified',
    effective_from DATE,
    effective_to DATE,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (statute_id, provision_number)
);

CREATE INDEX IF NOT EXISTS provisions_statute_id_idx
    ON provisions(statute_id);

CREATE INDEX IF NOT EXISTS provisions_number_idx
    ON provisions(provision_number);

CREATE INDEX IF NOT EXISTS statutes_title_idx
    ON statutes USING GIN (to_tsvector('english', title));
