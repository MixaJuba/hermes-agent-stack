"""Offline code-export and recovery-document contracts; no accounts or network."""
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('provenance',ROOT/'scripts/stack_provenance.py')
provenance=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(provenance)


class RecoveryReadinessTests(unittest.TestCase):
    def setUp(self):
        self.trip=patch.object(socket.socket,'connect',side_effect=AssertionError('external network forbidden'))
        self.trip.start(); self.addCleanup(self.trip.stop)
        self.tmp=tempfile.TemporaryDirectory(prefix='h001-readiness-'); self.addCleanup(self.tmp.cleanup)
        self.export=Path(self.tmp.name)/'export'; self.export.mkdir()
        self.commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        data=subprocess.check_output(['git','archive',self.commit],cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(self.export,filter='data')

    def test_export_matches_exact_tree_and_rejects_mutation(self):
        result=provenance.verify(ROOT,self.commit,self.export)
        self.assertTrue(result['status'].startswith('PASS'))
        p=self.export/'README.md'; p.write_bytes(p.read_bytes()+b'\nchanged')
        with self.assertRaises(ValueError): provenance.verify(ROOT,self.commit,self.export)

    def test_export_rejects_extra_missing_symlink_and_floating_ref(self):
        extra=self.export/'unexpected.py'; extra.write_text('pass')
        with self.assertRaises(ValueError): provenance.verify(ROOT,self.commit,self.export)
        extra.unlink()
        p=self.export/'README.md'; original=p.read_bytes(); p.unlink()
        with self.assertRaises(ValueError): provenance.verify(ROOT,self.commit,self.export)
        p.write_bytes(original)
        link=self.export/'unexpected-link'; link.symlink_to(p)
        with self.assertRaises(ValueError): provenance.verify(ROOT,self.commit,self.export)
        with self.assertRaises(ValueError): provenance.verify(ROOT,'main',self.export)

    def test_runbook_and_record_keep_live_gate_explicit(self):
        doc=(ROOT/'docs/RECOVERY-RUNBOOK.uk.md').read_text()
        for anchor in ('G1','G2','G3','G4','offsite_restore.py','offsite_native.py',
                       'instance_principal','L-007S','NOT YET VERIFIED','age-keygen',
                       'stack_provenance.py','PYTHONDONTWRITEBYTECODE','Exa','Gate'):
            self.assertIn(anchor,doc)
        self.assertNotIn('AGE-SECRET-KEY-',doc)
        record=json.loads((ROOT/'config/recovery-record.example.json').read_text())
        self.assertTrue(record['encrypted_sha256'].startswith('<'))
        self.assertNotIn('private_key',record)
        # Syntax-check operator shell examples, without executing any command.
        for block in doc.split('```bash\n')[1:]:
            result=subprocess.run(['bash','-n'],input=block.split('```',1)[0],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__': unittest.main()
