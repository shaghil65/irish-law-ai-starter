import tempfile
import unittest
from pathlib import Path
from ingest.downloader import url_for
from ingest.parser import parse

SAMPLE = b'''<?xml version="1.0" encoding="UTF-8"?>
<Act xmlns="urn:example"><preface><shortTitle>Sample Act 2024</shortTitle></preface>
<body><part><heading>Preliminary</heading>
<section eId="sec1"><num>1.</num><heading>Interpretation</heading>
<subsection><num>(1)</num><p>In this Act, words have meanings.</p></subsection>
</section></part></body></Act>'''

class IngestTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(url_for(2017, 8), "https://www.irishstatutebook.ie/eli/2017/act/8/enacted/en/xml")

    def test_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "2024"
            folder.mkdir()
            f = folder / "act-1.xml"
            f.write_bytes(SAMPLE)
            act = parse(f)
            self.assertEqual(act.title, "Sample Act 2024")
            self.assertEqual((act.year, act.number), (2024, 1))
            self.assertTrue(any(p.kind == "section" for p in act.provisions))
            self.assertTrue(any(p.kind == "subsection" for p in act.provisions))
            self.assertNotIn("In this Act", next(p.text for p in act.provisions if p.kind == "section"))

if __name__ == "__main__":
    unittest.main()
