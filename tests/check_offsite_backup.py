"""Real pinned native backup/import on synthetic memory/history; no external sockets."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import offsite_backup as b
import offsite_restore as r
from offsite_cli_stub import OfflineCLI
from test_offsite_backup import recipient

ROOT=Path(__file__).resolve().parents[1]
# Each child has its own Python socket tripwire before any Hermes imports.
WRAP="import runpy,sys; from unittest.mock import patch; p=sys.argv.pop(1); ctx=patch('socket.socket.connect',side_effect=AssertionError('external network forbidden')); ctx.start(); runpy.run_path(p,run_name='__main__')"

def child(script,args,home):
    result=subprocess.run([sys.executable,'-c',WRAP,str(script),*map(str,args)],env=dict(os.environ,HERMES_HOME=str(home)),capture_output=True,text=True,timeout=60)
    if result.returncode: raise AssertionError(result.stderr[-2500:])

with tempfile.TemporaryDirectory(prefix='hermes-ua-restore-') as tmp:
    root=Path(tmp); source=root/'source'; target=root/'restore-isolated'
    source.mkdir(mode=0o700)
    config=json.loads((ROOT/'deploy/hermes-config.json').read_text()); config['display']={'language':'uk'}
    (source/'config.yaml').write_text(json.dumps(config)); (source/'config.yaml').chmod(0o600)
    archive=root/'synthetic.zip'
    # Existing real memory tool/history setup and verification, no fake extraction.
    child(ROOT/'tests/check_hermes_backup.py',['create',archive],source)
    import hermes_cli
    source_checkout=Path(hermes_cli.__file__).resolve().parents[1]
    tools=Path(os.environ['HERMES_RUNTIME_DIR'])
    c=dict(recipient=recipient(),namespace='synthetic',bucket='synthetic',region='eu-frankfurt-1',
           prefix='hermes-backups',home=str(source),local_dir=str(root/'backups'),
           restore_root=str(root),hermes_source=str(source_checkout),hermes_tools=str(tools))
    identity=root/'temporary-test-identity'
    identity.write_text('SYNTHETIC NOT A PRIVATE KEY'); identity.chmod(0o600)
    tripwire=root/'tripwire'; tripwire.mkdir()
    (tripwire/'sitecustomize.py').write_text(
        "import socket\ndef deny(*args,**kwargs): raise AssertionError('external network forbidden')\n"
        "socket.socket.connect=deny\nsocket.create_connection=deny\n")
    cli=OfflineCLI()
    def native_worker(c,action,home,archive):
        # Reuse the already-selected PM interpreter. The disposable data home has
        # no PM install records; do not provision/copy runtime state into it.
        # No backup/extraction/memory/history/config implementation is mocked.
        cli.events.append('native-'+action)
        child(ROOT/'scripts/offsite_native.py',[action,home,archive],home)
    safe_env={k:os.environ[k] for k in ('PATH','PYTHONPATH') if k in os.environ}
    safe_env['PYTHONPATH']=str(tripwire)+os.pathsep+safe_env.get('PYTHONPATH','')
    safe_env['HOME']=str(root)
    with patch.dict(os.environ,safe_env,clear=True), \
            patch.object(b.shutil,'which',return_value='/stub/tool'), \
            patch.object(b,'run',side_effect=cli.run),patch.object(r,'run',side_effect=cli.run), \
            patch.object(b,'native',side_effect=native_worker),patch.object(r,'native',side_effect=native_worker), \
            patch('socket.socket.connect',side_effect=AssertionError('external network forbidden')):
        result=b.backup(c)
        r.restore(c,target,identity,result['object'],result['sha256'])
    assert cli.events==['native-backup','encrypt','put','head','head','get','decrypt','native-restore'],cli.events
    assert len(list((root/'backups').glob('*.zip')))==1
    child(ROOT/'tests/check_hermes_backup.py',['verify',archive],target)
    print('PASS: real native backup -> stub age -> CLI put/flat HEAD/get -> checksum -> stub decrypt -> real isolated import; config/memory/history/permissions verified in a fresh process; revival callback only suppressed; external sockets forbidden')
