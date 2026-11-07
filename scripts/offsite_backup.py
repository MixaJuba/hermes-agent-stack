"""Native full backup -> age -> SHA256 -> instance-principal OCI upload/HEAD.
No pruning, credential files, or automatic retry. Stdlib only.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('/var/lib/hermes-agent')


def recipient_valid(value):
    if not isinstance(value, str) or not value.startswith('age1') or len(value) != 62:
        return False
    alphabet = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    if any(c not in alphabet for c in value[4:]):
        return False
    chk = 1
    values = [ord(c) >> 5 for c in 'age'] + [0] + [ord(c) & 31 for c in 'age']
    for v in values + [alphabet.index(c) for c in value[4:]]:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i, g in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if (top >> i) & 1:
                chk ^= g
    return chk == 1


def load_config(path):
    c = json.loads(Path(path).read_text())
    keys = {'recipient', 'namespace', 'bucket', 'region', 'prefix', 'home', 'local_dir', 'restore_root', 'hermes_source', 'hermes_tools',
            'max_raw_archives', 'max_archive_bytes', 'max_local_bytes', 'min_free_bytes'}
    if set(c) != keys or not recipient_valid(c['recipient']):
        raise ValueError('Invalid non-secret config or age recipient')
    for key in ('namespace', 'bucket', 'region', 'prefix'):
        if not isinstance(c[key], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', c[key]) or c[key].startswith('REPLACE'):
            raise ValueError('Missing/invalid storage setting')
    for key in ('home', 'local_dir', 'restore_root', 'hermes_source', 'hermes_tools'):
        p = Path(c[key])
        if not p.is_absolute() or p.resolve() != p or str(p) == '/':
            raise ValueError('Paths must be absolute, canonical, and not symlinked')
    for key in ('max_raw_archives', 'max_archive_bytes', 'max_local_bytes', 'min_free_bytes'):
        if type(c[key]) is not int or c[key] <= 0:
            raise ValueError('Positive explicit storage bounds required')
    if c['max_raw_archives'] < 2 or c['max_local_bytes'] < 2*c['max_archive_bytes'] + 1048576:
        raise ValueError('Storage bounds must allow a retained raw and one bounded attempt')
    return c


def preflight():
    # Explicitly refuse static OCI configuration; subprocesses get an allowlisted env.
    if any(k.startswith('OCI_') for k in os.environ):
        raise ValueError('OCI environment overrides/static credentials forbidden')
    if not shutil.which('age') or not shutil.which('oci'):
        raise ValueError('age and OCI CLI are required')


def run(args, *, env=None):
    p = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if p.returncode:
        raise RuntimeError('Backup/recovery command failed; private output withheld')
    return p.stdout


def oci(c, *args):
    # No inherited credentials, proxies, user profile, key paths, or arbitrary CLI arguments.
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'SSL_CERT_FILE') if k in os.environ}
    output = run(['oci', '--output', 'json', '--auth', 'instance_principal', '--region', c['region'],
                           '--config-file', '/dev/null', '--max-retries', '0', '--connection-timeout', '15', '--read-timeout', '60',
                           'os', 'object', *args, '--namespace-name', c['namespace'],
                           '--bucket-name', c['bucket']], env=env)
    result = json.loads(output or b'{}')
    if not isinstance(result, dict):
        raise ValueError('Unexpected OCI CLI response shape')
    return result


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def native(c, action, home, archive):
    return run(['python3', str(ROOT/'scripts/hermes_runtime.py'),
                '--source', c['hermes_source'], '--home', c['home'], '--tools', c['hermes_tools'], 'python', '--',
                str(ROOT/'scripts/offsite_native.py'), action, str(home), str(archive),
                *(['--max-archive-bytes', str(c['max_archive_bytes'])] if action == 'backup' else [])])


def storage_budget(c, directory):
    """Count ALL local files, including failed/unmanaged attempts; never adopt them."""
    files = list(directory.iterdir())
    if any(p.is_symlink() or not p.is_file() or p.stat().st_uid != os.getuid()
           or p.stat().st_mode & 0o077 or p.stat().st_nlink != 1 for p in files):
        raise ValueError('Local backup area contains unsafe entries')
    # A killed pinned native writer can leave .<name>.zip.<pid>-<thread>.partial.
    # Count it as raw too; never auto-delete/adopt it after a crash.
    raw = [p for p in files if p.suffix == '.zip' or ('.zip.' in p.name and p.suffix == '.partial')]
    if len(raw) >= c['max_raw_archives'] or any(p.stat().st_size > c['max_archive_bytes'] for p in raw):
        raise ValueError('Raw backup limit reached; retain copies and review failed/unmanaged attempts')
    # Space for capped raw ZIP + age output, while preserving an explicit reserve.
    reservation = 2*c['max_archive_bytes'] + 1048576
    if (sum(p.stat().st_size for p in files) + reservation > c['max_local_bytes']
            or shutil.disk_usage(directory).free < reservation + c['min_free_bytes']):
        raise ValueError('Local backup budget/free space insufficient; no new archive started')


def verified_raw(raw, saved):
    encrypted = raw.with_suffix('.zip.age')
    return (isinstance(saved, dict) and saved.get('format') == 'h001c-local-v1'
            and saved.get('raw_name') == raw.name and saved.get('remote_verified') is True
            and not raw.is_symlink() and raw.is_file() and raw.stat().st_nlink == 1
            and raw.stat().st_size == saved.get('raw_size') and digest(raw) == saved.get('raw_sha256')
            and not encrypted.is_symlink() and encrypted.is_file()
            and digest(encrypted) == saved.get('encrypted_sha256'))


def retain_latest_raw(directory, latest, receipt):
    """Prune ONLY earlier helper-owned, hash-matching, HEAD-verified raw copies.

    Receipts are private local bookkeeping, not off-instance recovery evidence.
    Legacy L-006F/L-007S ZIPs and raw files without valid receipts are never adopted.
    Encryption outputs and receipts are not automatically deleted.
    """
    if not verified_raw(latest, receipt):
        raise ValueError('Latest verified raw missing/changed; no raw may be pruned')
    for artifact in (latest, latest.with_suffix('.zip.age')):
        with artifact.open('rb') as stream:
            os.fsync(stream.fileno())
    path = directory/('.h001c-'+latest.stem+'.json')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    for old in sorted(directory.glob('*.zip')):
        if old == latest or not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}\.zip', old.name):
            continue
        record = directory/('.h001c-'+old.stem+'.json')
        if not record.exists():
            continue  # old H-001C files without ownership evidence are also preserved
        if record.is_symlink() or not record.is_file() or record.stat().st_mode & 0o077:
            raise ValueError('Unsafe raw retention receipt; copies retained')
        saved = json.loads(record.read_text())
        if not verified_raw(old, saved):
            raise ValueError('Raw retention provenance/integrity mismatch; copies retained')
        old.unlink()  # failure is propagated; latest verified copy has already been retained
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def remote_metadata(data):
    # `oci os object head` serializes response HEADERS directly, not under data.
    # --metadata on put becomes individual opc-meta-* headers on head/get.
    return {k.removeprefix('opc-meta-'): v for k, v in data.items() if k.startswith('opc-meta-')}


def validate_head(data, sha, size=None):
    if not isinstance(data, dict) or any(not isinstance(k, str) for k in data):
        raise ValueError('Unexpected OCI HEAD response shape')
    # HTTP header names are case-insensitive; ambiguous duplicates fail closed.
    headers = {k.lower(): v for k, v in data.items()}
    if len(headers) != len(data):
        raise ValueError('Ambiguous OCI HEAD headers')
    length = headers.get('content-length')
    if (type(length) not in (int, str) or not re.fullmatch(r'[0-9]+', str(length))
            or int(length) <= 0):
        raise ValueError('Missing/invalid OCI HEAD content length')
    metadata = remote_metadata(headers)
    if ((size is not None and int(length) != size) or metadata.get('sha256') != sha
            or metadata.get('format') != 'hermes-age-v1'):
        raise ValueError('Remote HEAD integrity metadata/size mismatch')
    return int(length)


def check_remote(c, name, sha, size):
    data = oci(c, 'head', '--name', name)
    validate_head(data, sha, size)
    return data


def backup(c):
    preflight()
    os.umask(0o077)
    directory = Path(c['local_dir'])
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.resolve() != directory or directory.is_symlink() or directory.stat().st_mode & 0o077 or directory.stat().st_uid != os.getuid():
        raise ValueError('Backup directory must be private')
    # systemd/manual runs cannot race each other's limits or retention.
    fd = os.open(directory/'.backup.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another offsite backup is active') from None
        storage_budget(c, directory)
        return backup_locked(c, directory)


def backup_locked(c, directory):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name = stamp + '-' + uuid.uuid4().hex
    raw, encrypted = directory/(name+'.zip'), directory/(name+'.zip.age')
    native(c, 'backup', Path(c['home']), raw)
    if (not raw.is_file() or raw.is_symlink() or raw.stat().st_mode & 0o077
            or not 0 < raw.stat().st_size <= c['max_archive_bytes']):
        raise ValueError('Native backup missing or unsafe permissions')
    run(['age', '--encrypt', '--recipient', c['recipient'], '--output', str(encrypted), str(raw)])
    if not encrypted.is_file() or encrypted.is_symlink() or encrypted.stat().st_size == 0:
        raise ValueError('Encrypted artifact missing')
    with encrypted.open('rb') as stream:
        if stream.read(22) != b'age-encryption.org/v1\n':
            raise ValueError('Artifact is not age encrypted')
    encrypted.chmod(0o600)
    sha = digest(encrypted)
    encrypted.with_suffix(encrypted.suffix+'.sha256').write_text(sha+'\n')
    metadata = {'format':'hermes-age-v1', 'timestamp':stamp, 'sha256':sha, 'hermes':'v0.22.5'}
    object_name = c['prefix']+'/'+encrypted.name
    oci(c, 'put', '--name', object_name, '--file', str(encrypted), '--no-overwrite',
        '--storage-tier', 'Standard', '--metadata', json.dumps(metadata))
    check_remote(c, object_name, sha, encrypted.stat().st_size)
    receipt = {'format':'h001c-local-v1', 'raw_name':raw.name, 'raw_size':raw.stat().st_size,
               'raw_sha256':digest(raw), 'encrypted_sha256':sha, 'remote_verified':True}
    retain_latest_raw(directory, raw, receipt)
    return {'status':'verified', 'object':object_name, 'sha256':sha}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    a=p.parse_args()
    try:
        print(json.dumps(backup(load_config(a.config))))
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
        p.exit(1, 'Offsite backup failed; local artifacts retained; private details withheld.\n')


if __name__=='__main__':
    main()
