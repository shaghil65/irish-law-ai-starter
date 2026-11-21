"""Transactional, repeatable PostgreSQL import."""
from __future__ import annotations
import logging
import os
from pathlib import Path
import psycopg
from .parser import parse, Act

LOG = logging.getLogger(__name__)
SCHEMA = Path(__file__).with_name("schema.sql")


def upsert(conn: psycopg.Connection, act: Act) -> None:
    with conn.transaction():
        row = conn.execute("""
            INSERT INTO legislation_documents
            (canonical_uri, title, act_year, act_number, source_url, sha256, raw_path)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(canonical_uri) DO UPDATE SET
             title=excluded.title, sha256=excluded.sha256, raw_path=excluded.raw_path,
             source_url=excluded.source_url, imported_at=now()
            RETURNING id
        """, (act.canonical_uri, act.title, act.year, act.number,
              act.source_url, act.sha256, act.raw_path)).fetchone()
        doc_id = row[0]
        conn.execute("DELETE FROM legislation_provisions WHERE document_id=%s", (doc_id,))
        with conn.cursor() as cur:
            for p in act.provisions:
                cur.execute("""
                    INSERT INTO legislation_provisions
                    (document_id, provision_key, kind, provision_number, heading,
                     body_text, parent_key, position, structural_path)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (doc_id, p.key, p.kind, p.number, p.heading, p.text,
                      p.parent_key, p.position, p.path))


def import_directory(root: Path, dsn: str, strict: bool = False) -> dict:
    paths = sorted(root.glob("*/act-*.xml"))
    if not paths:
        raise ValueError(f"No XML files found under {root}")
    results = {"imported": 0, "skipped": 0, "failed": 0, "provisions": 0}
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        for path in paths:
            try:
                act = parse(path)
                if not act.provisions:
                    raise ValueError("No structural provisions found; check XML format")
                existing = conn.execute(
                    "SELECT sha256 FROM legislation_documents WHERE canonical_uri=%s",
                    (act.canonical_uri,)
                ).fetchone()
                if existing and existing[0] == act.sha256:
                    results["skipped"] += 1
                    LOG.info("Unchanged, skipping: %s", act.source_url)
                    continue
                upsert(conn, act)
                results["imported"] += 1
                results["provisions"] += len(act.provisions)
                LOG.info("Imported %s: %s provisions", act.source_url, len(act.provisions))
            except Exception as exc:
                results["failed"] += 1
                LOG.exception("Import failed: %s", path)
                conn.execute("INSERT INTO legislation_ingestion_errors(raw_path,error) VALUES(%s,%s)",
                             (str(path), str(exc)))
                if strict:
                    raise
    return results
