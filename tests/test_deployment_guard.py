"""Security boundary tests for the deployment startup gate, using fake credentials."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('gateway_guard', ROOT / 'deploy/gateway_guard.py')
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class DeploymentGuardTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'deploy/hermes-config.json').read_text())
        self.env = {'NVIDIA_API_KEY': 'test-only', 'EXA_API_KEY': 'test-only',
                    'TELEGRAM_BOT_TOKEN': 'test-only', 'TELEGRAM_ALLOWED_USERS': '123456789'}
        self.config['platforms']['telegram']['allowed_chats'] = ['123456789']

    def test_unconfigured_template_cannot_start(self):
        template = json.loads((ROOT / 'deploy/hermes-config.json').read_text())
        self.assertTrue(guard.validate(template, {}))

    def test_complete_owner_only_configuration_passes(self):
        self.assertEqual(guard.validate(self.config, self.env), [])

    def test_missing_or_wildcard_owner_cannot_start(self):
        for owner in ('', '*', '123,456', '-123', '0'):
            with self.subTest(owner=owner):
                self.assertTrue(guard.validate(self.config, {**self.env, 'TELEGRAM_ALLOWED_USERS': owner}))

    def test_foreign_chat_grant_cannot_start(self):
        self.config['platforms']['telegram']['allowed_chats'].append('987654321')
        self.assertTrue(guard.validate(self.config, self.env))

    def test_global_grant_cannot_override_owner(self):
        for key in ('GATEWAY_ALLOWED_USERS', 'GATEWAY_ALLOW_ALL_USERS', 'TELEGRAM_GROUP_ALLOWED_CHATS'):
            with self.subTest(key=key):
                self.assertTrue(guard.validate(self.config, {**self.env, key: '*'}))

    def test_fallback_and_secret_forwarding_cannot_start(self):
        for path, value in [(('fallback_model',), [{'provider': 'other', 'model': 'other'}]),
                            (('terminal', 'docker_forward_env'), ['NVIDIA_API_KEY']),
                            (('terminal', 'docker_network'), True),
                            (('terminal', 'docker_extra_args'), ['--privileged']),
                            (('agent', 'auto_recovery_cycles'), 5),
                            (('security', 'allow_lazy_installs'), True),
                            (('platforms', 'telegram', 'extra'), {'allowed_chats': ['*']}),
                            (('web', 'keyless_rescue'), True)]:
            config = copy.deepcopy(self.config)
            target = config
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            with self.subTest(path=path):
                self.assertTrue(guard.validate(config, self.env))

    def test_foreign_pairing_is_blocked_and_never_deleted(self):
        for directory in ('pairing', 'platforms/pairing'):
            with self.subTest(directory=directory), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp)
                path = home / directory / 'telegram-approved.json'
                path.parent.mkdir(parents=True)
                content = json.dumps({'987654321': {'user_name': 'synthetic'}})
                path.write_text(content)
                self.assertTrue(guard.validate_pairing(home, '123456789'))
                self.assertEqual(path.read_text(), content)

    def test_only_owner_pairing_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            path = home / 'pairing/telegram-approved.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'123456789': {}}))
            self.assertEqual(guard.validate_pairing(home, '123456789'), [])


if __name__ == '__main__':
    unittest.main()
