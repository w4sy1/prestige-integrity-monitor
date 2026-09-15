from pathlib import Path
import copy
import tempfile
import unittest
from unittest.mock import patch
from argparse import Namespace
import app


class FailureTests(unittest.TestCase):
    def test_identical_unknown_acl_is_not_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'file').write_text('fixture')
            with patch('extended.collect',return_value={'file':{'acl_status':'UNKNOWN','ads_status':'UNKNOWN'}}):
                snapshot=app.capture(root,True)
            result=app.compare(snapshot,snapshot)
            self.assertFalse(result['ok']);self.assertEqual(result['INCOMPLETE'],['file'])

    def test_stream_without_hash_remains_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'file').write_text('fixture')
            with patch('extended.collect',return_value={'file':{'acl_status':'OK','ads_status':'OK','streams':[{'name':'ads','sha256':None}]}}):
                self.assertFalse(app.capture(root,True)['ok'])

    def test_corrupt_baseline_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'file').write_text('fixture');snapshot=app.capture(root)
            for replacement in ({}, {'size':0,'mtime_ns':0,'sha256':'bad'}, []):
                broken=copy.deepcopy(snapshot);broken['files']['file']=replacement
                with self.assertRaises(ValueError):app.compare(broken,snapshot)

    def test_failed_atomic_update_preserves_original_and_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();(source/'file').write_text('before')
            baseline=root/'baseline.json';app.atomic_json(baseline,app.capture(source));original=baseline.read_bytes()
            (source/'file').write_text('after')
            args=Namespace(command='update',root=str(source),baseline=str(baseline),extended=False,accept_changes=True)
            with patch('app.atomic_json',side_effect=PermissionError('fixture failure')):
                with self.assertRaises(PermissionError):app.handle(args)
            self.assertEqual(baseline.read_bytes(),original)
            backups=list(root.glob('baseline.json.*.bak'));self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_bytes(),original)

    def test_incomplete_update_does_not_replace_trusted_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();(source/'file').write_text('fixture')
            baseline=root/'baseline.json';app.atomic_json(baseline,app.capture(source));original=baseline.read_bytes()
            args=Namespace(command='update',root=str(source),baseline=str(baseline),extended=True,accept_changes=True)
            with patch('extended.collect',return_value={}):result=app.handle(args)
            self.assertFalse(result['updated']);self.assertFalse(result['ok'])
            self.assertEqual(baseline.read_bytes(),original)
            self.assertEqual(list(root.glob('*.bak')),[])
