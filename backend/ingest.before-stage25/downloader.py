"""Resumable, single-threaded downloads from official eISB ELI XML endpoints."""
from __future__ import annotations
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import etree

LOG = logging.getLogger(__name__)
HOST = "www.irishstatutebook.ie"


def url_for(year: int, number: int) -> str:
    if not 1922 <= year <= 2100 or number < 1:
        raise ValueError("Invalid Act year or number")
    return f"https://{HOST}/eli/{year}/act/{number}/enacted/en/xml"


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": os.getenv("INGEST_USER_AGENT", "IrishLawAI-Research/0.2 (polite public-data indexing)"),
                      "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1"})
    retry = Retry(total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"], respect_retry_after_header=True)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def fetch(s: requests.Session, year: int, number: int, root: Path, refresh: bool = False) -> dict:
    url = url_for(year, number)
    dest = root / str(year) / f"act-{number}.xml"
    result = {"year": year, "number": number, "url": url, "file": str(dest)}
    if dest.exists() and not refresh:
        try:
            data = dest.read_bytes()
            etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))
            return {**result, "status": "cached", "sha256": digest(data)}
        except (etree.XMLSyntaxError, OSError):
            LOG.warning("Invalid cached XML, redownloading: %s", dest)
    try:
        response = s.get(url, timeout=(10, 60), allow_redirects=True)
        if urlparse(response.url).hostname != HOST or urlparse(response.url).scheme != "https":
            raise ValueError("Unexpected redirect outside official eISB host")
        if response.status_code == 404:
            return {**result, "status": "missing"}
        response.raise_for_status()
        data = response.content
        etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".xml.part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return {**result, "status": "downloaded", "sha256": digest(data), "bytes": len(data)}
    except (requests.RequestException, etree.XMLSyntaxError, ValueError, OSError) as e:
        return {**result, "status": "error", "error": str(e)}


def run(root: Path, report: Path, start: int, end: int, max_number: int, delay: float,
        refresh: bool = False, manifest: Path | None = None) -> dict:
    if delay < 0.5:
        raise ValueError("Minimum delay is 0.5 seconds to protect the public service")
    if start > end:
        raise ValueError("start year must not exceed end year")
    pairs = []
    if manifest:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                obj = json.loads(line)
                pairs.append((int(obj["year"]), int(obj["number"])))
    else:
        # Exhaustive within configured number ceiling: no fragile stop-on-404 heuristic.
        pairs = [(y, n) for y in range(start, end + 1) for n in range(1, max_number + 1)]
    counts = {}
    with session() as s:
        for year, number in pairs:
            outcome = fetch(s, year, number, root, refresh)
            record(report, outcome)
            counts[outcome["status"]] = counts.get(outcome["status"], 0) + 1
            LOG.info("%s act %s/%s", outcome["status"], year, number)
            if outcome["status"] != "cached":
                time.sleep(delay)
    return counts
