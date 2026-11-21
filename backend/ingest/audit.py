"""Local audit of source XML against extracted structural provisions."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from lxml import etree
from .parser import parse, tag, UNITS

def audit_directory(root: Path, output: Path) -> dict:
    files = sorted(root.glob('*/act-*.xml'))
    report = {'files': len(files), 'valid': 0, 'invalid': 0, 'total_provisions': 0, 'records': []}
    for path in files:
        item = {'file': str(path)}
        try:
            act = parse(path)
            xml = etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True))
            body = next((el for el in xml.getroot() if tag(el) == 'body'), None)
            source_counts = Counter(tag(el) for el in body.iter() if tag(el) in UNITS)
            parsed_counts = Counter(p.kind for p in act.provisions)
            item.update(status='valid', title=act.title, year=act.year, number=act.number,
                        sha256=act.sha256, source_units=dict(source_counts),
                        parsed_units=dict(parsed_counts), extracted=len(act.provisions),
                        warning='Review omissions, numbering and nested text manually' if source_counts != parsed_counts else None)
            if not act.provisions:
                item['status'] = 'invalid'
                item['error'] = 'No structural provisions extracted'
            report['total_provisions'] += len(act.provisions)
        except Exception as exc:
            item.update(status='invalid', error=str(exc))
        report['valid' if item['status'] == 'valid' else 'invalid'] += 1
        report['records'].append(item)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return {'files': report['files'], 'valid': report['valid'], 'invalid': report['invalid'],
            'total_provisions': report['total_provisions'], 'report': str(output)}
