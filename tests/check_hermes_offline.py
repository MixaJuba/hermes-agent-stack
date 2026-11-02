"""Run with the PM application Python. Real Hermes imports; no inference or gateway."""
from pathlib import Path
import importlib.metadata
import json
import os
import platform
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'deploy/hermes-config.json').read_text())
results = {}
with tempfile.TemporaryDirectory(prefix='hermes-ua-offline-') as tmp:
    home = Path(tmp)
    os.environ['HERMES_HOME'] = str(home)
    (home / 'config.yaml').write_text(json.dumps(config))
    from hermes_cli.config import validate_config_structure
    issues = validate_config_structure(config)
    errors = [issue.message for issue in issues if issue.severity == 'error']
    assert not errors, errors
    results['hermes_config_validation'] = 'passed'

    from tools.web_tools import _get_search_backend, _get_extract_backend
    from tools.web_tools_rescue import _keyless_rescue_enabled
    from plugins.web.keyless_mcp import use_keyless
    assert _get_search_backend() == _get_extract_backend() == 'exa'
    assert _keyless_rescue_enabled() is False
    assert use_keyless('exa', '') is False
    results['exa_only_no_keyless_resolution'] = 'passed'

    from gateway.run import GatewayRunner
    from gateway.config import Platform
    from gateway.session import SessionSource
    runner = object.__new__(GatewayRunner)
    runner.pairing_store = None
    def source(uid):
        return SessionSource(platform=Platform.TELEGRAM, chat_id=uid, user_id=uid, chat_type='dm')
    fixed = {'GATEWAY_ALLOW_ALL_USERS': 'false', 'TELEGRAM_ALLOW_ALL_USERS': 'false',
             'GATEWAY_ALLOWED_USERS': '', 'TELEGRAM_GROUP_ALLOWED_USERS': '',
             'TELEGRAM_GROUP_ALLOWED_CHATS': '', 'TELEGRAM_ALLOWED_USERS': ''}
    with patch.dict(os.environ, fixed):
        assert runner._is_user_authorized(source('123456789')) is False
        os.environ['TELEGRAM_ALLOWED_USERS'] = '123456789'
        assert runner._is_user_authorized(source('123456789')) is True
        assert runner._is_user_authorized(source('987654321')) is False
    results['real_gateway_owner_missing_and_foreign_denied'] = 'passed'

    # Verify the upstream UNION behavior and our read-only startup protection.
    import importlib.util
    spec = importlib.util.spec_from_file_location('deployment_guard', ROOT / 'deploy/gateway_guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    from gateway.pairing import PairingStore
    pairing = PairingStore()
    approved = pairing._dir / 'telegram-approved.json'
    original = json.dumps({'987654321': {'user_name': 'synthetic'}})
    approved.write_text(original)
    runner.pairing_store = pairing
    with patch.dict(os.environ, {**fixed, 'TELEGRAM_ALLOWED_USERS': '123456789'}):
        assert runner._is_user_authorized(source('987654321')) is True
        assert guard.validate_pairing(home, '123456789')
        assert approved.read_text() == original
    results['native_pairing_union_detected_and_startup_blocked'] = 'passed'

    from hermes_state import SessionDB
    db_path = home / 'test-history.sqlite'
    db = SessionDB(db_path=db_path)
    db.create_session('synthetic-three-message-test', source='test')
    expected = [f'Синтетичне повідомлення {i}' for i in range(1, 4)]
    for text in expected:
        db.append_message('synthetic-three-message-test', role='user', content=text)
    db.close()
    db = SessionDB(db_path=db_path)
    actual = [m['content'] for m in db.get_messages('synthetic-three-message-test')]
    assert actual == expected
    db.close()
    results['three_messages_survive_database_close_reopen'] = 'passed'

results['python_version'] = platform.python_version()
results['packages'] = {name: importlib.metadata.version(name) for name in ('openai', 'python-telegram-bot', 'exa-py')}
results['optional_voice_packages'] = {}
for name in ('faster-whisper', 'sounddevice', 'edge-tts', 'elevenlabs'):
    try:
        results['optional_voice_packages'][name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        results['optional_voice_packages'][name] = 'not installed'
results['inference_requests'] = 0
results['telegram_gateway_started'] = False
out = Path('/workspace/recovery/hermes-offline-checks.json')
out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
