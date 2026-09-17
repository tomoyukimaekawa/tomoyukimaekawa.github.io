"""Guard the reviewed content, DOM structure, attributes, order and CSS.

The baseline hashes represent the reviewed HTML after the public information additions. Ignore formatting whitespace and normalize optional </li> tags,
but retain every element, text value and attribute (including image alt text).
If intentionally changing published content later, review/update the baseline.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = ['', {}, []]
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'li' and self.stack[-1][0] == 'li':
            self.stack.pop()
        node = [tag, dict(attrs), []]
        self.stack[-1][2].append(node)
        if tag not in ('meta', 'hr', 'img', 'br', 'link'):
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, value):
        value = re.sub(r'\s+', ' ', value).strip()
        if value:
            self.stack[-1][2].append(value)


def fingerprint(source):
    value = json.dumps(Document(source).root, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(value.encode()).hexdigest()


class BuildTests(unittest.TestCase):
    def test_reviewed_content_and_structure_preserved(self):
        baseline = json.loads((Path(__file__).parent / 'expected_fingerprints.json').read_text())
        for name, content in build.build().items():
            with self.subTest(page=name):
                self.assertEqual(fingerprint(content), baseline[name])

    def test_committed_pages_are_current(self):
        for name, content in build.build().items():
            self.assertEqual((build.ROOT / name).read_text(), content)

    def test_text_is_escaped(self):
        self.assertEqual(build.paragraph('A < B & C'), '<p>A &lt; B &amp; C</p>')

    def test_broken_publication_reference_fails(self):
        research = build.load('research')
        research[0]['related_work'][0]['id'] = 'missing'
        with self.assertRaises(KeyError):
            build.render_research(research, build.load('publications')['entries'])

    def test_duplicate_or_unlisted_publication_fails(self):
        publications = build.load('publications')
        publications['categories'][0]['publications'].pop()
        with self.assertRaises(ValueError):
            build.render_publications(publications)


if __name__ == '__main__':
    unittest.main()
