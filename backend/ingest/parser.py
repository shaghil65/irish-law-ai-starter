"""Conservative eISB XML parser. Preserves enacted provenance and avoids TOC text."""
from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from lxml import etree

UNITS = {"sect", "section", "schedule", "sch", "part", "chapter", "article", "regulation", "rule", "subsection", "subsect", "paragraph", "subparagraph"}
HEADINGS = {"heading", "title", "subtitle", "crossheading", "rubric", "subject"}
NUMBERS = {"num", "number", "no"}

def tag(node):
    return etree.QName(node).localname.lower() if isinstance(node.tag, str) else ""

def normalized(value):
    return re.sub(r"\s+", " ", value or "").strip()

def content(node):
    return normalized(" ".join(node.itertext()))

def direct_child(node, names):
    return next((child for child in node if tag(child) in names), None)

def metadata_title(root):
    meta = direct_child(root, {"metadata", "meta"})
    if meta is not None:
        item = direct_child(meta, {"title", "shorttitle", "longtitle", "acttitle"})
        if item is not None and content(item):
            return content(item)
    for node in root.iter():
        if tag(node) in {"shorttitle", "longtitle", "acttitle", "docname"} and content(node):
            return content(node)
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
        raise ValueError(f"Expected .../YEAR/act-N.xml: {path}")
    year, number = map(int, match.groups())
    raw = path.read_bytes()
    root = etree.fromstring(raw, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False))
    if tag(root) not in {"act", "akomaNtoso".lower()}:
        raise ValueError(f"Unexpected root element: {tag(root)}")
    meta = direct_child(root, {"metadata"})
    if meta is not None:
        for name, expected in (("year", year), ("number", number)):
            el = direct_child(meta, {name})
            if el is not None and content(el).isdigit() and int(content(el)) != expected:
                raise ValueError(f"Metadata {name} conflicts with file path")
    body = direct_child(root, {"body"})
    if body is None:
        raise ValueError("Missing Act body; refusing to index frontmatter or table of contents")
    source = f"https://www.irishstatutebook.ie/eli/{year}/act/{number}/enacted/en/xml"
    title = metadata_title(root) or f"Act No. {number} of {year} (title unverified)"
    units, identities = [], {}
    for el in body.iter():
        kind = tag(el)
        if kind not in UNITS:
            continue
        parent = next((ancestor for ancestor in el.iterancestors() if tag(ancestor) in UNITS), None)
        parent_key = identities.get(parent) if parent is not None else None
        number_node = direct_child(el, NUMBERS)
        number_text = el.get("number") or el.get("n") or (content(number_node) if number_node is not None else None)
        heading_node = direct_child(el, HEADINGS)
        heading = content(heading_node) if heading_node is not None else None
        # Remove descendant structural units to avoid duplicate parent/child passages.
        clone = etree.fromstring(etree.tostring(el), etree.XMLParser(resolve_entities=False, no_network=True))
        for nested in list(clone.iterdescendants()):
            if tag(nested) in UNITS:
                parent_clone = nested.getparent()
                if parent_clone is not None:
                    if nested.tail:
                        previous = nested.getprevious()
                        if previous is not None:
                            previous.tail = (previous.tail or "") + nested.tail
                        else:
                            parent_clone.text = (parent_clone.text or "") + nested.tail
                    parent_clone.remove(nested)
        text = content(clone)
        if not text and not heading:
            continue
        position = len(units) + 1
        key = f"u{position}"
        identities[el] = key
        parent_path = next((unit.path for unit in reversed(units) if unit.key == parent_key), "")
        path_id = f"{kind}[{number_text or position}]"
        units.append(Provision(key, kind, number_text, heading, text, parent_key, position, f"{parent_path}/{path_id}"))
    return Act(year, number, title, source, source.removesuffix("/xml"), hashlib.sha256(raw).hexdigest(), str(path), units)
