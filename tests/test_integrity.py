from pathlib import Path
import tempfile
import unittest
from app import capture,compare

class IntegrityTests(unittest.TestCase):
    def test_states(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'same').write_text('a');(p/'gone').write_text('b');(p/'mod').write_text('c');before=capture(d)
            (p/'gone').unlink();(p/'mod').write_text('changed');(p/'new').write_text('x');r=compare(before,capture(d))
            self.assertEqual(r['UNCHANGED'],['same']);self.assertEqual(r['DELETED'],['gone']);self.assertEqual(r['MODIFIED'],['mod']);self.assertEqual(r['NEW'],['new'])
    def test_root_mismatch(self):
        with self.assertRaises(ValueError):compare({'schema_version':1,'root':'a'},{'root':'b'})
