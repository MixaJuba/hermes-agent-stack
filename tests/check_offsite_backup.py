"""Real pinned native backup/import on synthetic memory/history; no external sockets."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
# Each child has its own Python socket tripwire before any Hermes imports.
WRAP="import runpy,sys; from unittest.mock import patch; p=sys.argv.pop(1); ctx=patch('socket.socket.connect',side_effect=AssertionError('external network forbidden')); ctx.start(); runpy.run_path(p,run_name='__main__')"

def child(script,args,home):
    result=subprocess.run([sys.executable,'-c',WRAP,str(script),*map(str,args)],env=dict(os.environ,HERMES_HOME=str(home)),capture_output=True,text=True,timeout=60)
    if result.returncode: raise AssertionError(result.stderr[-2500:])

with tempfile.TemporaryDirectory(prefix='hermes-ua-restore-') as tmp:
    root=Path(tmp); source=root/'source'; target=root/'restore-isolated'
    source.mkdir(mode=0o700); target.mkdir(mode=0o700)
    config=json.loads((ROOT/'deploy/hermes-config.json').read_text()); config['display']={'language':'uk'}
    (source/'config.yaml').write_text(json.dumps(config)); (source/'config.yaml').chmod(0o600)
    archive=root/'synthetic.zip'
    # Existing real memory tool/history setup and verification, no fake extraction.
    child(ROOT/'tests/check_hermes_backup.py',['create',archive],source)
    child(ROOT/'scripts/offsite_native.py',['restore',target,archive],target)
    child(ROOT/'tests/check_hermes_backup.py',['verify',archive],target)
    print('PASS: native import/extraction/config/memory/history; revival callback only suppressed; external sockets forbidden')
