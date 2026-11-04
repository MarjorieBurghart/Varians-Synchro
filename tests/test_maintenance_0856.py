"""Documentation-only release tests: no Qt, I/O mutations or network."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_maintenance import check, ESSENTIAL, DOC
from generate_module_inventory import inventory_text

class MaintenanceDocumentationTests(unittest.TestCase):
    def test_passation_chapters_present(self):
        self.assertTrue(all((DOC / name).is_file() for name in ESSENTIAL))
    def test_ast_inventory_reproducible(self):
        self.assertEqual((DOC/'annexes/INVENTAIRE_MODULES_AUTOGENERE.md').read_text('utf-8'), inventory_text())
    def test_doc_links_catalogs_and_inventory(self):
        self.assertEqual(check(), [])
    def test_release_version_distinct_from_schema(self):
        from varians_synchro.core import VERSION, new_project
        self.assertEqual(VERSION,'0.8.6.0')
        pr=new_project()
        self.assertEqual((pr['format'],pr['version']),('varians-synchro-project',1))
    def test_docs_are_substantial(self):
        self.assertGreater(sum(len(p.read_text('utf-8')) for p in DOC.rglob('*.md')), 55000)

if __name__=='__main__':unittest.main()
