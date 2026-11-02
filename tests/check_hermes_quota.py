"""Exercise the actual Hermes conversation/error loop with an offline fake client."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'deepseek-ai/deepseek-v4.1-flash'
BASE_URL = 'https://integrate.api.nvidia.com/v1'


def worker(status, overlay):
    import httpx
    from openai import APIStatusError
    from hermes_cli.plugins import discover_plugins, has_hook, invoke_hook
    discover_plugins(force=True)
    assert has_hook('api_request_error') and has_hook('transform_llm_output')
    # Positive control: prove the real profile plugin was discovered and can run.
    invoke_hook('transform_llm_output', response_text='synthetic control', turn_id='probe-control')
    from run_agent import AIAgent
    import run_agent
    import agent.turn_recovery
    assert Path(run_agent.__file__).resolve() == Path.cwd() / 'run_agent.py'
    assert Path(agent.turn_recovery.__file__).resolve() == Path.cwd() / 'agent/turn_recovery.py'
    message = 'Synthetic insufficient credits' if status == 402 else 'Synthetic rate limit exceeded'
    body = {'error': {'message': message, 'code': 'insufficient_quota' if status == 402 else 'rate_limit_exceeded'}}
    error = APIStatusError(message, response=httpx.Response(status,
        request=httpx.Request('POST', BASE_URL + '/chat/completions'), json=body), body=body)
    client = MagicMock()
    client.chat.completions.create.side_effect = error
    # Mirrors the pinned project's own real AIAgent test injection seams.
    # Real error/retry/fallback logic stays intact. Any network escape fails this test.
    with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')) as network, \
         patch('model_tools.get_tool_definitions', return_value=[]), \
         patch('model_tools.check_toolset_requirements', return_value={}), \
         patch('agent.process_bootstrap.OpenAI', return_value=client):
        agent = AIAgent(provider='nvidia', requested_provider='nvidia', model=MODEL,
                        api_key='synthetic-test-only', base_url=BASE_URL,
                        fallback_model=[], credential_pool=None, max_iterations=2,
                        quiet_mode=True, skip_context_files=True, skip_memory=True,
                        skip_background_review=True, enabled_toolsets=[])
        agent.client = client
        agent._cached_system_prompt = 'Синтетичний тест.'
        agent._use_prompt_caching = False
        agent.compression_enabled = False
        assert agent._api_max_retries == 1 and agent._auto_recovery_cycles == 0
        assert agent._fallback_chain == [] and not agent._has_pending_fallback()
        with patch.object(agent, '_try_activate_fallback', wraps=agent._try_activate_fallback) as fallback:
            result = agent.run_conversation('Синтетична перевірка квоти.')
        attempts = client.chat.completions.create.call_count
        assert attempts == 1, attempts
        assert result['failed'] is True and result['completed'] is False, result
        assert result.get('final_response'), result
        assert agent.provider == 'nvidia' and agent.model == MODEL
        assert agent._fallback_chain == []
        network.assert_not_called()
        from agent.i18n import get_language
        assert get_language() == 'uk'
        reason = 'billing' if status == 402 else 'rate_limit'
        assert result['failure_reason'] == reason
        assert isinstance(result['failure_retryable'], bool)
        assert result['error'] == 'HTTP ' + str(status) + ': ' + message
        import hermes_yaml
        translations = hermes_yaml.safe_load((ROOT / 'deploy/locales/uk.yaml').read_text())['profile']['quota']
        if overlay:
            assert result['final_response'] == translations[reason], result['final_response']
        else:
            assert result['final_response'] != translations[reason]
            assert ('Billing or credits exhausted' if status == 402 else 'rate-limiting requests') in result['final_response']
        from agent.quota_profile_copy import apply_profile_quota_copy
        negative = {}
        for name, case in {
            'success': {'failed': False, 'failure_reason': 'billing'},
            'auth': {'failed': True, 'failure_reason': 'auth'},
            'partial': {'failed': True, 'failure_reason': reason, 'partial': True},
            'usage_window': {'failed': True, 'failure_reason': 'billing', 'usage_window_message': 'synthetic reset'},
        }.items():
            case['final_response'] = 'original synthetic response'
            assert apply_profile_quota_copy(case) is case
            negative[name] = 'unchanged'
        if not overlay:
            case = {'failed': True, 'failure_reason': reason, 'final_response': 'old synthetic copy'}
            assert apply_profile_quota_copy(case) is case
            negative['no_overlay'] = 'unchanged'
        events = [json.loads(line) for line in Path(os.environ['HERMES_HOME'], 'probe-events.jsonl').read_text().splitlines()]
        controls = [e for e in events if e['turn_id'] == 'probe-control']
        errors = [e for e in events if e['kind'] == 'error']
        outputs = [e for e in events if e['kind'] == 'output' and e['turn_id'] != 'probe-control']
        assert len(controls) == 1 and len(errors) == 1 and not outputs, events
        assert errors[0]['reason'] == ('billing' if status == 402 else 'rate_limit')
        # A check for an empty chain is allowed; activation must never succeed.
        report = {'http_status_simulated': status, 'client_attempts': attempts,
                  'api_max_retries': agent._api_max_retries,
                  'auto_recovery_cycles': agent._auto_recovery_cycles,
                  'fallback_chain_length': len(agent._fallback_chain),
                  'fallback_checks': fallback.call_count, 'fallback_activated': False,
                  'final_response': result['final_response'],
                  'display_language_resolved': get_language(),
                  'profile_overlay_enabled': overlay,
                  'native_agent_final_localized': overlay,
                  'negative_cases': negative,
                  'failure_retryable': result['failure_retryable'],
                  'error_metadata_preserved': True,
                  'billing_block_present': isinstance(result.get('billing_block'), dict),
                  'real_profile_plugin_discovered': True,
                  'output_hook_positive_control': True,
                  'native_error_hook_categories': [e['reason'] for e in errors],
                  'output_hook_calls_for_failed_turn': len(outputs),
                  'failure_reason': result.get('failure_reason'),
                  'turn_exit_reason': result.get('turn_exit_reason'),
                  'real_network_requests': 0}
        Path(os.environ['HERMES_HOME'], 'result.json').write_text(json.dumps(report, ensure_ascii=False))


def main():
    if len(sys.argv) > 1:
        worker(int(sys.argv[1]), sys.argv[2] == 'overlay')
        return
    cases = []
    base = Path(tempfile.mkdtemp(prefix='hermes-ua-quota-')).resolve()
    marker = base / '.synthetic-test-owned'
    marker.write_text('hermes-ua-quota-check')
    try:
        for status, overlay in ((402, True), (429, True), (402, False), (429, False)):
            home = base / (str(status) + ('-overlay' if overlay else '-plain'))
            home.mkdir(mode=0o700)
            rendered = subprocess.run([sys.executable, str(ROOT / 'deploy/render_config.py'), '--home', str(home)],
                                      env=dict(os.environ, TELEGRAM_ALLOWED_USERS='123456789'),
                                      capture_output=True, text=True, timeout=15)
            assert rendered.returncode == 0, rendered.stderr
            if not overlay:
                assert home.parent == base and marker.read_text() == 'hermes-ua-quota-check'
                (home / 'locales/uk.yaml').unlink()
            config = json.loads((home / 'config.yaml').read_text())
            config['plugins'] = {'enabled': ['quota-hook-probe']}
            (home / 'config.yaml').write_text(json.dumps(config))
            shutil.copytree(ROOT / 'tests/fixtures/quota-hook-probe', home / 'plugins/quota-hook-probe')
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(status), 'overlay' if overlay else 'plain'],
                                    env=dict(os.environ, HERMES_HOME=str(home), HERMES_LANGUAGE=''),
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise AssertionError(str(status) + ': ' + result.stderr[-3500:] + result.stdout[-1500:])
            cases.append(json.loads((home / 'result.json').read_text()))
        report = {'native_agent_error_loop': True, 'cases': cases,
                  'quota_final_ukrainian_requirement_met': True,
                  'runtime': 'Hermes v0.22.5 pinned base plus reviewed local quota patch',
                  'gateway_started': False, 'live_telegram_delivery_verified': False,
                  'inference_requests': 0}
        (ROOT / 'reports/quota-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        assert base.parent == Path(tempfile.gettempdir()).resolve()
        assert base.name.startswith('hermes-ua-quota-') and not base.is_symlink()
        assert marker.read_text() == 'hermes-ua-quota-check'
        shutil.rmtree(base)


if __name__ == '__main__':
    main()
