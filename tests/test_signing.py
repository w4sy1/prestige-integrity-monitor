import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from signing import new_key,sign,verify


@unittest.skipUnless(importlib.util.find_spec('cryptography'),'Opcjonalna zależność cryptography nie jest zainstalowana')
class SigningTests(unittest.TestCase):
    def test_sign_verify_tamper_wrong_key(self):
        with tempfile.TemporaryDirectory() as temporary,patch.dict(os.environ,{'PRESTIGE_SIGNING_PASSWORD':'fixture-password-not-for-production'}):
            root=Path(temporary);private=root/'key.pem';public=root/'public.pem';file=root/'manifest.json';signature=root/'signature.json'
            file.write_text('{"fixture":true}')
            new_key(private,public);self.assertIn(b'ENCRYPTED PRIVATE KEY',private.read_bytes())
            sign(file,private,signature);self.assertTrue(verify(file,public,signature)['ok'])
            new_key(root/'other.pem',root/'other.pub')
            self.assertFalse(verify(file,root/'other.pub',signature)['ok'])
            file.write_text('{"tampered":true}');self.assertFalse(verify(file,public,signature)['ok'])

    def test_does_not_overwrite_keys(self):
        with tempfile.TemporaryDirectory() as temporary,patch.dict(os.environ,{'PRESTIGE_SIGNING_PASSWORD':'fixture-password-not-for-production'}):
            root=Path(temporary);(root/'key.pem').write_text('keep')
            with self.assertRaises(ValueError):new_key(root/'key.pem',root/'public.pem')
            self.assertEqual((root/'key.pem').read_text(),'keep')
