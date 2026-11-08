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


def fixture_plugin(home, *, with_sidecar=True):
    source = Path('/workspace/cloudflare-provider-source')
    if not source.exists():
        raise unittest.SkipTest('Native plugin fixture requires public exact pinned source')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == plugin.PIN['commit']
    target = home / 'plugins' / plugin.PIN['name']
    shutil.copytree(source / plugin.PIN['subdir'], target)
    catalog = {'name': plugin.PIN['name'], 'repo': plugin.PIN['repository'], 'tier': plugin.PIN['tier']}
    record = {plugin.PIN['name']: {'pinned': True, 'revision': plugin.PIN['commit'],
              'source': plugin.PIN['repository'] + '#' + plugin.PIN['subdir'],
              'catalog': {**catalog, 'pin': plugin.PIN['commit'], 'sha': plugin.PIN['commit']}}}
    (home / 'plugins/.install-metadata.json').write_text(json.dumps(record))
    if with_sidecar:
        # Exercise the actual pinned installer writer rather than invent its output.
        # PM's existing interpreter is reused; no install, network, or credentials.
        script = ('import json,sys; from pathlib import Path; '
                  'from hermes_cli.plugins_cmd_catalog import write_catalog_sidecar_record; '
                  'write_catalog_sidecar_record(Path(sys.argv[1]), json.loads(sys.argv[2]), sys.argv[3])')
        subprocess.run(['python3', str(ROOT / 'scripts/hermes_runtime.py'), 'python', '--', '-c',
                        script, str(target), json.dumps(catalog), plugin.PIN['commit']],
                       cwd=ROOT, check=True, capture_output=True, text=True, timeout=20)
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
            self.assertEqual(config['timezone'], 'Europe/Kyiv')
            self.assertEqual(config['tools']['tool_search']['enabled'], 'off')
            self.assertEqual(config['plugins']['enabled'], ['cloudflare-workers-ai-provider', 'bro-recent-web'])
            guard_path = ROOT / 'deploy/gateway_guard.py'
            guard_spec = importlib.util.spec_from_file_location('gateway_guard', guard_path)
            guard = importlib.util.module_from_spec(guard_spec)
            guard_spec.loader.exec_module(guard)
            self.assertEqual(guard.validate_bro_plugin(config, home), [])
            (home / 'plugins/bro-recent-web/__init__.py').write_text('# changed')
            self.assertTrue(guard.validate_bro_plugin(config, home))
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

    def test_native_installer_sidecar_and_optional_absence(self):
        with tempfile.TemporaryDirectory(prefix='c002a-plugin-') as tmp:
            home = Path(tmp)
            target = fixture_plugin(home)
            sidecar = target / plugin.CATALOG_SIDECAR
            data = json.loads(sidecar.read_text())
            self.assertEqual(data['catalog_name'], plugin.PIN['name'])
            self.assertEqual(data['repo'], plugin.PIN['repository'])
            self.assertEqual(data['sha'], plugin.PIN['commit'])
            self.assertEqual(data['tier'], 'community')
            self.assertIsInstance(data['installed_at'], str)
            self.assertEqual(plugin.attest(home), [])
            for stamp in ('2026-11-02T12:00:00Z', '2031-06-15T09:12:23+00:00'):
                data['installed_at'] = stamp
                sidecar.write_text(json.dumps(data))
                self.assertEqual(plugin.attest(home), [])
            del data['installed_at']
            sidecar.write_text(json.dumps(data))
            self.assertEqual(plugin.attest(home), [])
            sidecar.unlink()  # Only this fixture's generated sidecar.
            self.assertEqual(plugin.attest(home), [])

    def test_unexpected_files_including_dotfiles_and_json_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='c002a-plugin-') as tmp:
            home = Path(tmp)
            target = fixture_plugin(home)
            for name in ('unreviewed.txt', '.another.json', 'extra.json', '.hidden'):
                path = target / name
                path.write_text('{}')
                with self.subTest(name=name):
                    self.assertIn('unreviewed files in Cloudflare plugin', plugin.attest(home))
                path.unlink()

    def test_sidecar_never_substitutes_for_authoritative_metadata(self):
        with tempfile.TemporaryDirectory(prefix='c002a-plugin-') as tmp:
            home = Path(tmp)
            fixture_plugin(home)
            path = home / 'plugins/.install-metadata.json'
            original = path.read_text()
            for field, value in [('revision', '0' * 40), ('source', 'https://example.invalid/plugin'),
                                 ('pinned', False)]:
                metadata = json.loads(original)
                metadata[plugin.PIN['name']][field] = value
                path.write_text(json.dumps(metadata))
                with self.subTest(field=field):
                    self.assertTrue(plugin.attest(home))
            path.unlink()
            self.assertTrue(plugin.attest(home))  # Valid sidecar alone is never sufficient.

    def test_symlinked_sidecar_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='c002a-plugin-') as tmp:
            home = Path(tmp)
            target = fixture_plugin(home)
            sidecar = target / plugin.CATALOG_SIDECAR
            original = sidecar.read_text()
            sidecar.unlink()
            outside = home / 'outside-sidecar.json'
            outside.write_text(original)
            try:
                sidecar.symlink_to(outside)
            except (NotImplementedError, OSError):
                self.skipTest('Platform cannot create symlinks')
            self.assertTrue(plugin.attest(home))
            outside.unlink()  # Dangling symlinks must fail too.
            self.assertTrue(plugin.attest(home))

    def test_malformed_or_non_inert_sidecars_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='c002a-plugin-') as tmp:
            home = Path(tmp)
            target = fixture_plugin(home)
            path = target / plugin.CATALOG_SIDECAR
            valid = json.loads(path.read_text())
            for text in ('{broken json', '[]', 'null', '{}'):
                path.write_text(text)
                with self.subTest(malformed=text):
                    self.assertTrue(plugin.attest(home))
            for field in ('catalog_name', 'repo', 'sha', 'tier'):
                data = {**valid, field: 'unreviewed'}
                path.write_text(json.dumps(data))
                with self.subTest(field=field):
                    self.assertTrue(plugin.attest(home))
                data.pop(field)
                path.write_text(json.dumps(data))
                with self.subTest(missing=field):
                    self.assertTrue(plugin.attest(home))
            for stamp in (None, 123, [], '', ' ', 'line\nbreak', 'control\x00'):
                path.write_text(json.dumps({**valid, 'installed_at': stamp}))
                with self.subTest(stamp=stamp):
                    self.assertTrue(plugin.attest(home))
            path.write_text(json.dumps({**valid, 'extra': 'unexpected'}))
            self.assertTrue(plugin.attest(home))


if __name__ == '__main__':
    unittest.main()
