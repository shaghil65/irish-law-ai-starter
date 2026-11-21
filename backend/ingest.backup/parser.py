"""Namespace-neutral structural XML parser; conservative about source metadata."""
from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from lxml import etree

# Only create a record for independently useful structural units.
UNITS = {"sect", "section", "schedule", "part", "chapter", "article", "regulation", "rule", "subsection", "paragraph", "subparagraph"}
HEADINGS = {"heading", "title", "subtitle", "crossheading", "rubric"}
NUMBERS = {"num", "number", "no"}


def tag(node) -> str:
    return etree.QName(node).localname.lower() if isinstance(node.tag, str) else ""


def normalized(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def content(node) -> str:
    return normalized(" ".join(node.itertext()))


def direct_child(node, names: set[str]):
    return next((child for child in node if tag(child) in names), None)


def metadata_title(root) -> str | None:
    # Avoid accidentally using the heading of the first section as the Act title.
    for el in root.iter():
        if tag(el) in {"shorttitle", "longtitle", "acttitle", "docname"}:
            val = content(el)
            if val:
                return val
    for el in root.iter():
        if tag(el) == "title" and not any(tag(a) in UNITS for a in el.iterancestors()):
            val = content(el)
            if val:
                return val
    return None


@dataclass
class Provision:
    key: str
    kind: str
    number: str | None
    heading: str | None
    text: str
    parent_key: str | None
    position: int
    path: str


@dataclass
class Act:
    year: int
    number: int
    title: str
    source_url: str
    canonical_uri: str
    sha256: str
    raw_path: str
    provisions: list[Provision]


def parse(path: Path) -> Act:
    match = re.search(r"/(\d{4})/act-(\d+)\.xml$", path.resolve().as_posix())
    if not match:
        raise ValueError(f"Expected file path .../YEAR/act-N.xml: {path}")
    year, number = map(int, match.groups())
    raw = path.read_bytes()
    root = etree.fromstring(raw, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False))
    source = f"https://www.irishstatutebook.ie/eli/{year}/act/{number}/enacted/en/xml"
    title = metadata_title(root) or f"Act No. {number} of {year} (title unverified)"
    units = []
    identities = {}
    for el in root.iter():
        kind = tag(el)
        if kind not in UNITS:
            continue
        # Use hierarchy position, not publisher eId, to guarantee unique identifiers.
        parent = next((a for a in el.iterancestors() if tag(a) in UNITS), None)
        parent_key = identities.get(parent) if parent is not None else None
        position = len(units) + 1
        key = f"u{position}"
        identities[el] = key
        number_node = direct_child(el, NUMBERS)
        number_text = el.get("number") or el.get("n") or (content(number_node) if number_node is not None else None)
        heading_node = direct_child(el, HEADINGS)
        heading = content(heading_node) if heading_node is not None else None
        # Prevent duplicate parent/child text in retrieval: parent text excludes nested units.
        fragments = []
        if el.text and el.text.strip():
            fragments.append(el.text)
        for child in el:
            if tag(child) not in UNITS:
                fragments.extend(child.itertext())
            if child.tail and child.tail.strip():
                fragments.append(child.tail)
        body = normalized(" ".join(fragments))
        if not body and not heading:
            continue
        path_id = f"{kind}[{number_text or position}]"
        parent_path = next((u.path for u in reversed(units) if u.key == parent_key), "")
        units.append(Provision(key, kind, number_text, heading, body, parent_key, position,
                               f"{parent_path}/{path_id}"))
    return Act(year, number, title, source, source.removesuffix("/xml"),
               hashlib.sha256(raw).hexdigest(), str(path), units)
