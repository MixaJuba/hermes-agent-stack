import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1] / 'deploy/plugins/bro-capabilities/__init__.py'
spec = importlib.util.spec_from_file_location('bro_capabilities', PLUGIN)
bro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bro)


@unittest.skipUnless(os.name == 'posix', 'production owner checks require POSIX')
class ReminderTests(unittest.TestCase):
    def test_native_schedule_is_one_shot_script_only_and_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = []
            values = {'HERMES_SESSION_PLATFORM': 'telegram', 'HERMES_SESSION_CHAT_TYPE': 'dm',
                      'HERMES_SESSION_CHAT_ID': '123', 'HERMES_SESSION_USER_ID': '123'}
            modules = {
                'cron.jobs': SimpleNamespace(create_job=lambda **kw: jobs.append(kw),
                                             list_jobs=lambda **kw: jobs),
                'gateway.session_context': SimpleNamespace(get_session_env=values.get),
                'hermes_constants': SimpleNamespace(get_hermes_home=lambda: Path(tmp)),
            }
            with patch.dict(sys.modules, modules), patch.dict(os.environ, TELEGRAM_ALLOWED_USERS='123'):
                for minutes, msg in [(0, 'ok'), (1, 'MEDIA:/etc/passwd'), (1, 'a\nb'), (True, 'ok')]:
                    self.assertFalse(bro.schedule_once(minutes, msg)['success'])
                values['HERMES_SESSION_USER_ID'] = '124'
                self.assertFalse(bro.schedule_once(1, 'ok')['success'])
                values['HERMES_SESSION_USER_ID'] = '123'
                message = "Read the draft: 'done'; print(42)"
                self.assertTrue(bro.schedule_once(1, message)['success'])
                self.assertFalse(bro.schedule_once(1, 'duplicate')['success'])
            job, = jobs
            self.assertEqual(job['deliver'], 'telegram:123')
            self.assertEqual(job['repeat'], 1)
            self.assertTrue(job['no_agent'])
            self.assertIsNone(job['prompt'])
            self.assertIn('T', job['schedule'])
            script = Path(tmp) / 'scripts' / job['script']
            self.assertEqual(script.stat().st_mode & 0o777, 0o600)
            output = subprocess.check_output([sys.executable, str(script)], text=True, encoding='utf-8')
            self.assertEqual(output.strip(), '🔔 Нагадування: ' + message)
            self.assertFalse(script.exists())

    def test_document_delivery_is_owner_bound_and_rejects_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / bro.OUT
            root.mkdir(parents=True, mode=0o700)
            good = root / 'good.pdf'
            good.write_bytes(b'%PDF-test')
            (root / 'link.pdf').symlink_to(good)
            calls = []

            def native_sender(args):
                calls.append(args)
                return json.dumps({'success': True})

            modules = {
                'hermes_constants': SimpleNamespace(get_hermes_home=lambda: Path(tmp)),
                'tools.send_message_tool': SimpleNamespace(send_message_tool=native_sender),
            }
            with patch.dict(sys.modules, modules), patch.object(bro, '_telegram_owner', return_value='123'):
                for names in (['../good.pdf'], ['link.pdf'], ['good.pdf', 'good.pdf'], ['good.png']):
                    self.assertFalse(bro.send_documents(names)['success'])
                self.assertEqual(calls, [])
                self.assertEqual(bro.send_documents(['good.pdf']), {'success': True, 'delivered': ['good.pdf']})
                with patch.object(bro, '_telegram_owner', return_value=None):
                    self.assertFalse(bro.send_documents(['good.pdf'])['success'])
            self.assertEqual(calls, [{'action': 'send', 'target': 'telegram:123', 'message': f'MEDIA:{good}'}])
