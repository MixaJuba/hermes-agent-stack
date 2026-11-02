"""Exercise the installed native Docker backend without any model call."""
from pathlib import Path
import json
import os

from tools.environments.docker import DockerEnvironment

sandbox = DockerEnvironment(
    image='hermes-ua-sandbox:local', cwd='/workspace', timeout=20,
    cpu=1, memory=512, persistent_filesystem=True, task_id=f'hermes-ua-offline-{os.getpid()}',
    volumes=[], forward_env=[], env={}, network=False, auto_mount_cwd=False, run_as_host_user=True,
    extra_args=['--pids-limit', '128'], persist_across_processes=False,
    shm_size='64m', image_pinned=True,
)
try:
    command = '''python - <<'PY'
import os,pathlib,json,socket
assert os.getuid() != 0
print('NON_ROOT_OK', flush=True)
assert not any(os.environ.get(k) for k in ('NVIDIA_API_KEY','EXA_API_KEY','TELEGRAM_BOT_TOKEN'))
print('NO_SECRETS_OK', flush=True)
assert not pathlib.Path('/var/run/docker.sock').exists()
assert not pathlib.Path('/workspace/hermes-agent-stack').exists()
assert not pathlib.Path('/var/lib/hermes-agent/.env').exists()
print('NO_HOST_DATA_OK', flush=True)
pathlib.Path('/workspace/check.txt').write_text('Синтетичний тест')
assert pathlib.Path('/workspace/check.txt').read_text() == 'Синтетичний тест'
print('FILE_ROUND_TRIP_OK', flush=True)
try:
    socket.create_connection(('169.254.169.254',80),timeout=1)
except OSError:
    pass
else:
    raise AssertionError('metadata route unexpectedly accessible')
print(json.dumps({'non_root':True,'secrets_absent':True,'docker_socket_absent':True,'host_checkout_absent':True,'file_round_trip':True,'metadata_unreachable':True}))
PY'''
    result = sandbox.execute(command)
    if result.get('returncode') != 0:
        markers = [m for m in ('NON_ROOT_OK', 'NO_SECRETS_OK', 'NO_HOST_DATA_OK', 'FILE_ROUND_TRIP_OK') if m in result.get('output', '')]
        raise AssertionError(json.dumps({'returncode': result.get('returncode'), 'passed_stages': markers}))
    evidence = json.loads(result['output'].strip().splitlines()[-1])
    evidence.update(native_hermes_backend=True, model_tool_loop=False, inference_requests=0)
    path = Path('/workspace/recovery/hermes-sandbox-check.json')
    path.write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))
finally:
    sandbox.cleanup(force_remove=True)
