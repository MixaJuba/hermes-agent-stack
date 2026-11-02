"""PM-interpreter worker; real native backup/import, no gateway activation."""
import json
import os
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace
from unittest.mock import patch
import zipfile


def execute(action, home, archive):
    if action == 'restore' and (home == Path('/var/lib/hermes-agent') or Path('/var/lib/hermes-agent') in home.parents or home.resolve() != home):
        raise ValueError('Isolated canonical target required')
    os.environ['HERMES_HOME']=str(home)
    os.umask(0o077)
    if action == 'restore' and (any(home.iterdir()) or home.is_symlink()):
        raise ValueError('Restore worker requires empty target')
    from hermes_cli.backup import run_backup, run_import
    if action=='backup':
        if run_backup(SimpleNamespace(output=str(archive),keep=0)) is not True:
            raise ValueError('Native backup incomplete')
        return
    # Native external-provider entries could otherwise write outside isolated home.
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            p=Path(item.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in item.filename
                    or any(part in {'_external','profiles'} for part in p.parts)
                    or (item.external_attr>>16)&0o170000==0o120000):
                raise ValueError('Unsafe/external archive member')
        config=z.read('config.yaml')
        state=z.read('state.db')
        memories={i.filename:z.read(i) for i in z.infolist() if i.filename.startswith('memories/') and not i.is_dir()}
    with patch('hermes_cli.backup._revive_gateway_after_import') as revival:
        if run_import(SimpleNamespace(zipfile=str(archive),force=False)) not in (None,0):
            raise ValueError('Native import incomplete')
        revival.assert_called_once_with(home)
    if (home/'config.yaml').read_bytes()!=config:
        raise ValueError('Config restore mismatch')
    for name,data in memories.items():
        if (home/name).read_bytes()!=data:
            raise ValueError('Memory restore mismatch')
    db=sqlite3.connect((home/'state.db').as_uri()+'?mode=ro',uri=True)
    try:
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):
            raise ValueError('Restored history database invalid')
        import tempfile
        with tempfile.TemporaryDirectory(prefix='verify-state-', dir=home.parent) as tmp:
            original=Path(tmp)/'state.db'; original.write_bytes(state)
            source=sqlite3.connect(original.as_uri()+'?mode=ro',uri=True)
            try:
                for table in ('sessions','messages'):
                    query='SELECT * FROM '+table+' ORDER BY rowid'
                    if source.execute(query).fetchall()!=db.execute(query).fetchall():
                        raise ValueError('Session/history restore mismatch')
            finally:
                source.close()
    finally:
        db.close()
    for p in home.rglob('*'):
        if p.is_symlink():
            raise ValueError('Restored symlink forbidden')
        if p.stat().st_mode & 0o077:
            p.chmod(0o700 if p.is_dir() else 0o600)


if __name__=='__main__':
    execute(sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]))
