CREATE TABLE IF NOT EXISTS legislation_documents (
 id BIGSERIAL PRIMARY KEY,
 canonical_uri TEXT NOT NULL UNIQUE,
 title TEXT NOT NULL,
 act_year INT NOT NULL,
 act_number INT NOT NULL,
 legislation_type TEXT NOT NULL DEFAULT 'act',
 source_version TEXT NOT NULL DEFAULT 'enacted',
 source_url TEXT NOT NULL,
 language TEXT NOT NULL DEFAULT 'en',
 sha256 CHAR(64) NOT NULL,
 raw_path TEXT NOT NULL,
 attribution TEXT NOT NULL DEFAULT 'eISB / Houses of the Oireachtas; Oireachtas Open Data PSI Licence (CC BY 4.0)',
 imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(act_year, act_number, source_version, language)
);
CREATE TABLE IF NOT EXISTS legislation_provisions (
 id BIGSERIAL PRIMARY KEY,
 document_id BIGINT NOT NULL REFERENCES legislation_documents(id) ON DELETE CASCADE,
 provision_key TEXT NOT NULL,
 kind TEXT NOT NULL,
 provision_number TEXT,
 heading TEXT,
 body_text TEXT NOT NULL,
 parent_key TEXT,
 position INT NOT NULL,
 structural_path TEXT NOT NULL,
 search_vector TSVECTOR GENERATED ALWAYS AS
   (to_tsvector('english', coalesce(heading,'') || ' ' || body_text)) STORED,
 UNIQUE(document_id, provision_key)
);
CREATE INDEX IF NOT EXISTS legislation_provisions_search_idx ON legislation_provisions USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS legislation_provisions_doc_idx ON legislation_provisions(document_id);
CREATE TABLE IF NOT EXISTS legislation_ingestion_errors (
 id BIGSERIAL PRIMARY KEY,
 raw_path TEXT NOT NULL,
 error TEXT NOT NULL,
 occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
