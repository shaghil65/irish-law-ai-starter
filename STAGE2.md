# Stage 2 — Irish legislation ingestion

This is **the Stage 1 starter plus Stage 2**. Your Next.js app and FastAPI backend remain intact.

## What is included

- Resumable XML downloader for enacted Acts from the official electronic Irish Statute Book.
- Safe XML parser with Act metadata and structural provisions (sections, subsections, schedules, etc.).
- Idempotent PostgreSQL importer with full-text index, transaction rollback and error log.
- Docker Compose ingestion service, CLI, tests and download report.

## Upgrade your existing Stage 1 directory

**Back up your Stage 1 project first.** You can either use this complete project directory or copy the following additions into your existing project:

- `backend/ingest/` (new)
- `backend/tests/` (new)
- `backend/requirements.txt` (replace or append the two new packages)
- `docker-compose.yml` (merge the `ingest` service)
- `.gitignore` (ignore `data/`)

Keep your existing `.env` and PostgreSQL volume. Do not run `docker compose down -v`.

## Run

From the project root:

```bash
# Build ingestion image and keep database running
docker compose up -d db
docker compose build ingest

# First: a small, verifiable test for a known Act
echo '{"year":2017,"number":8}' > sample-acts.jsonl
docker compose --profile ingest run --rm -v "$PWD/sample-acts.jsonl:/app/sample-acts.jsonl:ro" ingest download --manifest /app/sample-acts.jsonl

# Import the downloaded XML into the existing PostgreSQL database
docker compose --profile ingest run --rm ingest import

# Then download and import a full year, with a configurable Act-number ceiling
docker compose --profile ingest run --rm ingest all --start-year 2024 --end-year 2024 --max-number 80
```

`--max-number` is a *probe ceiling*, not a verified catalogue count. Missing Act numbers are recorded in `data/reports/downloads.jsonl`. For production completeness, compare with the eISB's yearly Act list; do not equate "no error" with complete coverage.

To cover multiple years, for example:

```bash
docker compose --profile ingest run --rm ingest all --start-year 2000 --end-year 2025 --max-number 150
```

This makes many requests and may take a while. The downloader uses a minimum 0.5-second pause, retries transient errors, and skips cached XML. Use a descriptive `INGEST_USER_AGENT` in your `.env` for production.

## Check imported records

```bash
docker compose exec db psql -U lawai -d irish_law -c "SELECT act_year, count(*) FROM legislation_documents GROUP BY act_year ORDER BY act_year DESC;"
docker compose exec db psql -U lawai -d irish_law -c "SELECT count(*) FROM legislation_provisions;"
docker compose exec db psql -U lawai -d irish_law -c "SELECT title, source_url FROM legislation_documents LIMIT 10;"
```

Run tests:

```bash
docker compose --profile ingest run --rm --entrypoint python ingest -m unittest discover -s tests -v
```

## Coverage and accuracy warnings

**Scope:** This Stage 2 ingests *enacted English-language Acts of the Oireachtas*, not every type of Irish legislation. It does not yet import statutory instruments, pre-1922 Acts, Irish-language expressions, the Constitution, or Law Reform Commission Revised Acts.

**Current law:** Enacted text is not a current-law consolidation. Commencement, repeal and amendments are not yet resolved. Do not use it to assert current legal position without verifying subsequent legislative changes.

**XML variability:** The parser is namespace-neutral and supports common structural tags, but eISB XML can vary across eras. Validate a sample from each era against the official publication and expand mappings before treating historical coverage as complete. The importer rejects files with zero structural units and logs failures.

**Source:** https://www.irishstatutebook.ie/eli/open-data.html . The official site describes XML source for Acts from 1922 onward at `/eli/{year}/act/{number}/enacted/en/xml` and use under the Oireachtas Open Data PSI Licence, incorporating CC BY 4.0. Preserve source attribution.

**Next:** Stage 3 will add better corpus QA, chunking, hybrid retrieval and citations. The Stage 1 legal-answer API remains disabled until retrieval and safeguards are implemented.
