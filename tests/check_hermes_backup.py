"""Native synthetic backup/import round trip; run with the PM application Python."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FACT = 'Синтетичний проєкт «Калина» має контрольний колір бірюзовий.'
MESSAGES = ['Синтетичне повідомлення ' + str(i) for i in range(1, 4)]


def worker(stage, archive):
    home = Path(os.environ['HERMES_HOME'])
    assert home.parent.name.startswith('hermes-ua-restore-')
    os.umask(0o077)
    # Offline safety tripwire; these native operations have no reason to connect.
    with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
        if stage == 'create':
            from tools.memory_tool import load_on_disk_store, memory_tool
            result = json.loads(memory_tool('add', content=FACT, store=load_on_disk_store()))
            assert result.get('success') is True, result
            from hermes_state import SessionDB
            db = SessionDB(db_path=home / 'state.db')
            db.create_session('synthetic-restore', source='test')
            for text in MESSAGES:
                db.append_message('synthetic-restore', role='user', content=text)
            db.close()
            from hermes_cli.backup import run_backup
            assert run_backup(SimpleNamespace(output=str(archive), keep=0)) is True
        elif stage == 'restore':
            assert not any(home.iterdir()), 'restore destination must be empty'
            from hermes_cli.backup import run_import
            # Native import's post-restore service activation is outside this test.
            with patch('hermes_cli.backup._revive_gateway_after_import') as revive:
                assert run_import(SimpleNamespace(zipfile=str(archive), force=False)) in (0, None)
                revive.assert_called_once_with(home)
        else:
            from tools.memory_tool import load_on_disk_store
            assert FACT in load_on_disk_store().memory_entries
            from hermes_state import SessionDB
            db = SessionDB(db_path=home / 'state.db')
            assert [m['content'] for m in db.get_messages('synthetic-restore')] == MESSAGES
            db.close()
            config = json.loads((home / 'config.yaml').read_text())
            assert config['display']['language'] == 'uk'
            required = [home, home / 'config.yaml', home / 'state.db', home / 'memories/MEMORY.md']
            for path in required:
                assert path.stat().st_uid == os.getuid()
                assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, path.name


def main():
    if len(sys.argv) > 1:
        worker(sys.argv[1], Path(sys.argv[2]))
        return
    base = Path(tempfile.mkdtemp(prefix='hermes-ua-restore-')).resolve()
    marker = base / '.synthetic-test-owned'
    marker.write_text('hermes-ua-backup-check')
    try:
        source, target = base / 'source', base / 'target'
        for home in (source, target):
            home.mkdir(mode=0o700)
        config = json.loads((ROOT / 'deploy/hermes-config.json').read_text())
        config['display'] = {'language': 'uk'}
        path = source / 'config.yaml'
        path.write_text(json.dumps(config, ensure_ascii=False))
        path.chmod(0o600)
        archive = base / 'synthetic.zip'
        for stage, home in [('create', source), ('restore', target), ('verify', target)]:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), stage, str(archive)],
                                    env=dict(os.environ, HERMES_HOME=str(home)),
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                # Workers only touch synthetic data; no HTTP clients/real secret files.
                raise AssertionError(stage + ': ' + result.stderr[-3000:] + result.stdout[-1000:])
            if stage == 'create':
                with zipfile.ZipFile(archive) as zf:
                    names = zf.namelist()
                    assert not any(set(Path(n).parts) & {'.env', 'auth.json', 'credentials', 'pairing', 'platforms'} for n in names)
                    assert all(not n.startswith('_external') for n in names)
                    assert 'state.db' in names and 'memories/MEMORY.md' in names
        report = dict(native_memory_tool='passed', native_backup_import='passed',
                      restored_in_fresh_process=True, separate_empty_destination=True,
                      three_messages_restored=True, owner_only_permissions=True,
                      archive_members=names, real_secret_files_in_archive=False,
                      import_service_activation_intercepted=True, gateway_started=False,
                      vm_reboot_test=False, inference_requests=0)
        (ROOT / 'reports/backup-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        # Never delete a pre-existing/work/runtime directory, even on failure.
        assert base.parent == Path(tempfile.gettempdir()).resolve()
        assert base.name.startswith('hermes-ua-restore-') and not base.is_symlink()
        assert marker.read_text() == 'hermes-ua-backup-check'
        shutil.rmtree(base)


if __name__ == '__main__':
    main()
