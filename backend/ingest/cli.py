"""Run with python -m ingest.cli download|import|all."""
import argparse
import json
import logging
import os
from pathlib import Path
from .downloader import run
from .importer import import_directory


def main():
    p = argparse.ArgumentParser(description="Irish Statute Book enacted Acts importer")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("download", "import", "all"):
        s = sub.add_parser(name)
        s.add_argument("--start-year", type=int, default=2024)
        s.add_argument("--end-year", type=int, default=2024)
        s.add_argument("--max-number", type=int, default=60)
        s.add_argument("--delay", type=float, default=0.5)
        s.add_argument("--manifest", type=Path, help="Optional JSONL containing year and number")
        s.add_argument("--refresh", action="store_true")
        s.add_argument("--strict", action="store_true")
        s.add_argument("--data-dir", type=Path, default=Path("/data"))
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raw = a.data_dir / "raw" / "acts"
    if a.command in ("download", "all"):
        print(json.dumps(run(raw, a.data_dir / "reports" / "downloads.jsonl", a.start_year,
                             a.end_year, a.max_number, a.delay, a.refresh, a.manifest), indent=2))
    if a.command in ("import", "all"):
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            p.error("DATABASE_URL is required for import")
        print(json.dumps(import_directory(raw, dsn, a.strict), indent=2))


if __name__ == "__main__":
    main()
