"""Offline deployment/attestation contracts; synthetic profile, no HTTP or credentials."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('cf_plugin', ROOT / 'deploy/cloudflare_plugin.py')
plugin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plugin)


def fixture_plugin(home):
    source = Path('/workspace/cloudflare-provider-source')
    if not source.exists():
        raise unittest.SkipTest('Native plugin fixture requires public exact pinned source')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == plugin.PIN['commit']
    target = home / 'plugins' / plugin.PIN['name']
    shutil.copytree(source / plugin.PIN['subdir'], target)
    record = {plugin.PIN['name']: {'pinned': True, 'revision': plugin.PIN['commit'],
              'source': plugin.PIN['repository'] + '#' + plugin.PIN['subdir']}}
    (home / 'plugins/.install-metadata.json').write_text(json.dumps(record))
    return target


class CloudflareDeploymentTests(unittest.TestCase):
    def test_renderer_keeps_account_url_and_credentials_out_of_config(self):
        with tempfile.TemporaryDirectory(prefix='c002-render-') as tmp:
            home = Path(tmp)
            args = ['python3', str(ROOT / 'deploy/render_config.py'), '--home', str(home)]
            result = subprocess.run(args, env=dict(os.environ, TELEGRAM_ALLOWED_USERS='123456789'), capture_output=True)
            self.assertEqual(result.returncode, 0)
            config = json.loads((home / 'config.yaml').read_text())
            self.assertEqual(config['model']['provider'], 'workers-ai')
            self.assertEqual(config['model']['default'], '@cf/zai-org/glm-4.7-flash')
            self.assertNotIn('base_url', config['model'])
            self.assertEqual(config['fallback_providers'], [])
            self.assertEqual((home / 'locales/uk.yaml').read_bytes(), (ROOT / 'deploy/locales/uk.yaml').read_bytes())
            before = (home / 'config.yaml').read_bytes()
            self.assertNotEqual(subprocess.run(args, env=dict(os.environ, TELEGRAM_ALLOWED_USERS='123456789'), capture_output=True).returncode, 0)
            self.assertEqual((home / 'config.yaml').read_bytes(), before)

    def test_exact_plugin_integrity_and_provenance(self):
        with tempfile.TemporaryDirectory(prefix='c002-plugin-') as tmp:
            home = Path(tmp)
            target = fixture_plugin(home)
            self.assertEqual(plugin.attest(home), [])
            path = target / '__init__.py'
            path.write_bytes(path.read_bytes() + b'\n# unreviewed\n')
            self.assertTrue(plugin.attest(home))
        with tempfile.TemporaryDirectory(prefix='c002-plugin-') as tmp:
            home = Path(tmp)
            fixture_plugin(home)
            path = home / 'plugins/.install-metadata.json'
            metadata = json.loads(path.read_text())
            metadata[plugin.PIN['name']]['revision'] = '0' * 40
            path.write_text(json.dumps(metadata))
            self.assertTrue(plugin.attest(home))


if __name__ == '__main__':
    unittest.main()
