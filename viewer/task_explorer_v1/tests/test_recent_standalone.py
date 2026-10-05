"""Portable recent-family links contain original bytes, not invented public URLs."""
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_semantics import ROOT, TASKS, get


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; source comparison not run')
class RecentStandaloneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        output = Path(cls.temp.name) / 'ScienceGym-Task-Explorer.html'
        subprocess.run([sys.executable, '-B', str(ROOT / 'export_standalone.py'), '--output', str(output)],
                       check=True, stdout=subprocess.PIPE, text=True)
        cls.page = output.read_text()
        cls.embedded = json.loads(re.search(r'window\.SCIENCEGYM_EMBEDDED_FILES=(.*?);</script>', cls.page).group(1))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_exact_embedded_inventory_and_source_bytes(self):
        expected = {}
        for key in ('lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared', 'conformal', 'scattering', 'qha', 'thermalmeta'):
            f = get(key)
            for item in list(f['source_files'].values()) + f['asset_links']:
                expected[item['url']] = item
        self.assertEqual(len(expected), 400)  # 364 task/asset JSON, nine guides and twenty-seven renders
        self.assertEqual(set(expected), set(self.embedded))
        for url, item in expected.items():
            with self.subTest(url=url):
                blob = base64.b64decode(self.embedded[url]['base64'], validate=True)
                self.assertEqual(blob, (ROOT / url).read_bytes())
                self.assertEqual(hashlib.sha256(blob).hexdigest(), item['sha256'])
                self.assertIn(self.embedded[url]['mime'], ('application/json', 'text/markdown', 'image/png'))

    def test_runtime_is_local_and_source_pin_claim_remains_honest(self):
        self.assertNotRegex(self.page, r'<script\s+src=')
        self.assertNotRegex(self.page, r'<link[^>]+href="styles\.css"')
        self.assertIn('window.SCIENCEGYM_SVGS=', self.page)
        self.assertIn('function linkUrl(url)', self.page)
        self.assertIn('URL.createObjectURL(new Blob', self.page)
        self.assertIn('remote publication is not asserted', self.page)
        self.assertNotIn('https://github.com/openags/ScienceGym/blob/e1e4a74', self.page)
        self.assertNotIn('https://github.com/openags/ScienceGym/blob/98d3bfe', self.page)
        self.assertIn('39 paper-level designs and three bounded subsets', self.page)
        self.assertIn('all 958 route views in a mocked DOM', self.page)

    def test_exact_original_png_bytes_and_safe_no_execution_scope(self):
        pngs = [base64.b64decode(e['base64'], validate=True) for e in self.embedded.values() if e['mime'] == 'image/png']
        self.assertEqual(len(pngs), 27)
        self.assertTrue(all(blob.startswith(b'\x89PNG\r\n\x1a\n') for blob in pngs))
        for key in ('lockable_origami', 'varactor', 'wetting', 'arcmorph', 'midinfrared', 'conformal'):
            family = get(key)
            self.assertFalse(family['actor_projection_implemented'])
            self.assertFalse(family['context']['episode_input_contract']['physical_runtime_available'])
            self.assertFalse(family['context']['RELEASE_BOUNDARY']['whole_paper_execution_complete'])
