import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from extended import collect


class ExtendedEvidenceTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt' and shutil.which('pwsh'), 'Windows PowerShell backend')
    def test_reads_acl_and_hashes_fixture_alternate_stream(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / 'fixture.txt'
            file.write_bytes(b'primary')
            stream = Path(str(file) + ':prestige-test')
            try:
                stream.write_bytes(b'alternate fixture')
            except OSError:
                self.skipTest('Temporary filesystem does not support named streams')
            row = collect(temporary, ['fixture.txt'])['fixture.txt']
            self.assertEqual(row['acl_status'], 'OK')
            self.assertTrue(row['sddl'])
            self.assertEqual(row['ads_status'], 'OK')
            named = next(item for item in row['streams'] if item['name'] == 'prestige-test')
            self.assertEqual(named['sha256'].lower(), hashlib.sha256(b'alternate fixture').hexdigest())

