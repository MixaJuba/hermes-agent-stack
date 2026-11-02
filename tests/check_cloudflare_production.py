"""Pinned native Hermes/Cloudflare config, auxiliary routing and synthetic quota. No HTTP."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_cloudflare_deploy import fixture_plugin, plugin

MODEL = '@cf/zai-org/glm-4.7-flash'
FAKE_BASE = 'https://api.cloudflare.com/client/v4/accounts/' + '0' * 32 + '/ai/v1'


def worker(home):
    import faulthandler
    faulthandler.dump_traceback_later(20, exit=True)
    import httpx
    from openai import APIStatusError
    from hermes_cli.config import load_config, validate_config_structure
    config = load_config()
    assert not [i for i in validate_config_structure(config) if i.severity == 'error']
    spec = importlib.util.spec_from_file_location('guard', ROOT / 'deploy/gateway_guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    assert not guard.validate(json.loads((home/'config.yaml').read_text()), os.environ)
    assert plugin.attest(home) == []
    entry = plugin.catalog_entry(Path.cwd())
    assert entry.sha == plugin.PIN['commit']
    assert entry.install_identifier == plugin.PIN['repository'] + '#' + plugin.PIN['subdir']
    with patch('hermes_cli.plugins_cmd_catalog.install_catalog_entry') as install:
        plugin.install_at_pin(Path.cwd())
        selected = install.call_args.args[0]
        assert selected.sha==entry.sha and selected.install_identifier==entry.install_identifier
        assert install.call_args.kwargs=={'force':False,'ref':entry.sha}
    from providers import get_provider_profile
    profile = get_provider_profile('workers-ai')
    assert profile and profile.get_model_context_length(MODEL) == 131072
    assert profile.model_capabilities[MODEL]['supports_tools'] is True
    assert profile.default_aux_model != MODEL  # explicit config must override this default
    from hermes_cli.runtime_provider import resolve_runtime_provider
    runtime = resolve_runtime_provider(requested='workers-ai')
    assert runtime['provider'] == 'workers-ai' and runtime['base_url'].rstrip('/') == FAKE_BASE
    assert runtime['api_key'] == 'synthetic-test-only'

    from agent import auxiliary_client as aux
    report = {'schema': 'PASS', 'plugin_catalog_pin': entry.sha,
              'frozen_catalog_install_contract':'PASS (installer invocation inspected; no PM install executed)',
              'plugin_attestation': 'PASS', 'provider_runtime': 'PASS', 'context_window':131072,
              'auxiliary_routes': {}, 'inference_requests':0, 'telegram_started':False,
              'exa_used':False}
    # Tripwires, not replacement routing: any unconfigured provider selection fails.
    with contextlib.ExitStack() as stack:
        network = stack.enter_context(patch('socket.socket.connect', side_effect=AssertionError('HTTP forbidden')))
        # SDK-only fixture: take Hermes' native no-op instrumentation path. Rust
        # Relay middleware initialization is unrelated to provider/quota routing.
        stack.enter_context(patch('agent.relay_runtime._load_nemo_relay', side_effect=ImportError('offline instrumentation fixture')))
        report['relay_telemetry'] = 'native NoopRelayRuntime; middleware load isolated for synthetic SDK test'
        for name in ('_try_discovery_chain', '_try_openrouter', '_resolve_codex_credential_and_base'):
            stack.enter_context(patch.object(aux, name, side_effect=AssertionError('foreign provider forbidden')))
        for task in guard.AUX_TASKS:
            provider, model, base, key, mode = aux._resolve_task_provider_model(task)
            assert (provider, model, base, key) == ('workers-ai', MODEL, None, None), task
            client, model = aux.get_text_auxiliary_client(task)
            assert model == MODEL and str(client.base_url).rstrip('/') == FAKE_BASE
            assert client.max_retries == 0
            client.close()
            report['auxiliary_routes'][task] = 'workers-ai / ' + MODEL
        assert aux._discovery_chain_allowed('workers-ai') is False
        assert aux._try_configured_fallback_chain('compression','workers-ai') == (None, None, '')
        assert aux._try_main_agent_model_fallback('workers-ai', 'compression', failed_model=MODEL, failed_base_url=FAKE_BASE) == (None, None, '')
        # Cloudflare v4 errors envelope + supplied documented Free-allocation semantics.
        # No invented account fact/error-code; never exhaust a real account.
        body = {'success':False, 'errors':[{'message':'Account limited: daily free allocation exhausted'}]}
        error = APIStatusError('Account limited: daily free allocation exhausted', response=httpx.Response(
            429, request=httpx.Request('POST',FAKE_BASE+'/chat/completions'), json=body), body=body)
        from run_agent import AIAgent
        client = MagicMock()
        client.chat.completions.create.side_effect = error
        with patch('model_tools.get_tool_definitions', return_value=[]), \
             patch('model_tools.check_toolset_requirements',return_value={}), \
             patch('agent.process_bootstrap.OpenAI',return_value=client):
            agent = AIAgent(provider='workers-ai', requested_provider='workers-ai', model=MODEL,
                            api_key='synthetic-test-only',base_url=FAKE_BASE,fallback_model=[],credential_pool=None,
                            quiet_mode=True,skip_memory=True,skip_context_files=True,skip_background_review=True,
                            enabled_toolsets=[],max_iterations=2)
            agent.client=client
            agent._cached_system_prompt='Синтетична перевірка.'
            agent._use_prompt_caching=False
            agent.compression_enabled=False
            with patch.object(agent,'_try_activate_fallback',wraps=agent._try_activate_fallback) as fallback:
                result=agent.run_conversation('Синтетична перевірка безкоштовної квоти.')
            assert client.chat.completions.create.call_count == 1
            assert agent._api_max_retries==1 and agent._auto_recovery_cycles==0
            assert agent._fallback_chain==[] and agent.provider=='workers-ai' and agent.model==MODEL
            assert result['failed'] is True and result['completed'] is False
            assert result['failure_reason'] in ('billing','rate_limit')
            import hermes_yaml
            expected=hermes_yaml.safe_load((home/'locales/uk.yaml').read_text())['profile']['quota'][result['failure_reason']]
            assert result['final_response']==expected
            assert isinstance(result['failure_retryable'],bool) and result['error']
            report['cloudflare_daily_free_429']={'status':'PASS','attempts':1,'fallback_activated':False,
                'model_switch':False,'paid_fallback':False,'failure_reason':result['failure_reason'],
                'failure_retryable':result['failure_retryable'],'metadata_preserved':True,
                'final_response':result['final_response']}
        # Real auxiliary failure path, mocked transport only; no alternate model/provider calls.
        from openai import OpenAI
        requests = []
        def quota_transport(request):
            payload=json.loads(request.content)
            assert payload['model']==MODEL and str(request.url)==FAKE_BASE+'/chat/completions'
            requests.append(payload['model'])
            return httpx.Response(429,json=body,request=request)
        def sdk_factory(**kwargs):
            assert kwargs['api_key']=='synthetic-test-only' and kwargs['base_url'].rstrip('/')==FAKE_BASE
            kwargs['max_retries']=0
            kwargs['http_client']=httpx.Client(transport=httpx.MockTransport(quota_transport))
            return OpenAI(**kwargs)
        with aux._client_cache_lock:
            aux._client_cache.clear()
        aux._reset_aux_unhealthy_cache()
        with patch.object(aux,'_create_openai_client',side_effect=sdk_factory):
            try:
                aux.call_llm(task='compression', messages=[{'role':'user','content':'synthetic'}])
            except APIStatusError:
                pass
            else:
                raise AssertionError('quota must propagate after bounded failure')
        # Pinned auxiliary credential recovery has one built-in same-provider
        # retry for rate-limit errors, separate from transient_retries=0. Both
        # requests must stay on this exact Free model and endpoint.
        assert len(requests) == 2, len(requests)
        report['auxiliary_quota_failure']={'status':'PASS','attempts':len(requests),
            'native_same_provider_429_retry':1,'transient_retries':0,'provider_or_model_fallback':False}
        network.assert_not_called()
    faulthandler.cancel_dump_traceback_later()
    (ROOT/'reports/c002-native-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


def main():
    if len(sys.argv)>1:
        worker(Path(sys.argv[1])); return
    with tempfile.TemporaryDirectory(prefix='c002-native-') as tmp:
        home=Path(tmp)
        env=dict(os.environ,HERMES_HOME=str(home),HERMES_LANGUAGE='',
                 CLOUDFLARE_WORKERS_AI_API_TOKEN='synthetic-test-only',CLOUDFLARE_WORKERS_AI_BASE_URL=FAKE_BASE,
                 EXA_API_KEY='test-only',TELEGRAM_BOT_TOKEN='test-only',TELEGRAM_ALLOWED_USERS='123456789')
        subprocess.run([sys.executable,str(ROOT/'deploy/render_config.py'),'--home',str(home)],env=env,check=True,capture_output=True)
        fixture_plugin(home)
        child=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(home)],env=env,
                             capture_output=True,text=True,timeout=60)
        if child.returncode:
            raise AssertionError(child.stderr[-4000:]+child.stdout[-1500:])
        print(child.stdout)


if __name__=='__main__':
    main()
