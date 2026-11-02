"""Exact source attestation on a disposable local clone; no commits or installs."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('patch_runtime', ROOT / 'scripts/hermes_runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class SourcePatchTests(unittest.TestCase):
    def test_only_exact_reviewed_patch_is_accepted(self):
        original = Path('/workspace/.hermes-runtime/source')
        if not (original / '.git').exists():
            self.skipTest('Requires the existing pinned cloud source, not a network clone')
        base = Path(tempfile.mkdtemp(prefix='hermes-ua-attestation-')).resolve()
        marker = base / '.test-owned'
        marker.write_text('source-attestation')
        clone = base / 'source'
        try:
            subprocess.run(['git', 'clone', '--shared', '--quiet', str(original), str(clone)], check=True)
            self.assertEqual(runtime.source_state(clone), 'clean')
            subprocess.run(['python3', str(ROOT / 'scripts/hermes_runtime.py'), '--source', str(clone),
                            'apply-patch'], check=True, capture_output=True)
            self.assertEqual(runtime.source_state(clone), 'patched')
            for path in (clone / 'agent/quota_profile_copy.py', clone / 'uv.lock'):
                before = path.read_bytes()
                path.write_bytes(before + b'\n# synthetic tamper\n')
                with self.subTest(path=path.name), self.assertRaises(ValueError):
                    runtime.source_state(clone)
                path.write_bytes(before)  # only this fixture's created clone
            extra = clone / 'agent/unreviewed_extra.py'
            extra.write_text('pass\n')
            with self.assertRaises(ValueError):
                runtime.source_state(clone)
            extra.unlink()
            subprocess.run(['git', 'add', 'agent/turn_recovery.py'], cwd=clone, check=True)
            with self.assertRaises(ValueError):
                runtime.source_state(clone)
            subprocess.run(['git', 'reset', '--quiet', 'HEAD', '--', 'agent/turn_recovery.py'], cwd=clone, check=True)
            self.assertEqual(runtime.source_state(clone), 'patched')
        finally:
            assert base.parent == Path(tempfile.gettempdir()).resolve()
            assert base.name.startswith('hermes-ua-attestation-') and not base.is_symlink()
            assert marker.read_text() == 'source-attestation'
            shutil.rmtree(base)


if __name__ == '__main__':
    unittest.main()
