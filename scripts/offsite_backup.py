"""Native full backup -> age -> SHA256 -> instance-principal OCI upload/HEAD.
No pruning, credential files, or automatic retry. Stdlib only.
"""
import argparse
import datetime
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
    keys = {'recipient', 'namespace', 'bucket', 'region', 'prefix', 'home', 'local_dir', 'restore_root', 'hermes_source', 'hermes_tools'}
    if set(c) != keys or not recipient_valid(c['recipient']):
        raise ValueError('Invalid non-secret config or age recipient')
    for key in ('namespace', 'bucket', 'region', 'prefix'):
        if not isinstance(c[key], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', c[key]) or c[key].startswith('REPLACE'):
            raise ValueError('Missing/invalid storage setting')
    for key in ('home', 'local_dir', 'restore_root', 'hermes_source', 'hermes_tools'):
        p = Path(c[key])
        if not p.is_absolute() or p.resolve() != p or str(p) == '/':
            raise ValueError('Paths must be absolute, canonical, and not symlinked')
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
                str(ROOT/'scripts/offsite_native.py'), action, str(home), str(archive)])


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
    if directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise ValueError('Backup directory must be private')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name = stamp + '-' + uuid.uuid4().hex
    raw, encrypted = directory/(name+'.zip'), directory/(name+'.zip.age')
    native(c, 'backup', Path(c['home']), raw)
    if not raw.is_file() or raw.is_symlink() or raw.stat().st_mode & 0o077:
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
