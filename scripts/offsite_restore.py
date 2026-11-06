"""Explicit isolated DR only; private identity is a runtime file, never config."""
import argparse
import os
from pathlib import Path
import re
import stat
import subprocess
from offsite_backup import load_config, preflight, oci, run, digest, native, LIVE, validate_head


def target_valid(c, target):
    target=Path(target)
    root=Path(c['restore_root'])
    live=Path(c['home']).resolve()
    if (not target.is_absolute() or target.is_symlink() or target.resolve()!=target
            or target.parent!=root or not re.fullmatch(r'restore-[A-Za-z0-9_-]+', target.name)
            or target==LIVE or target==live or live in target.parents or target in live.parents
            or LIVE in target.parents or target in LIVE.parents):
        raise ValueError('Explicit isolated restore target required')
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError('Restore target must be empty')
    return target


def restore(c, target, identity, name, expected_sha):
    target=target_valid(c,target)
    key=Path(identity)
    if (key.is_symlink() or not key.is_file() or stat.S_IMODE(key.stat().st_mode)!=0o600
            or key.stat().st_uid!=os.getuid() or Path(c['home']) in key.resolve().parents):
        raise ValueError('Temporary protected recovery identity required outside live home')
    if not re.fullmatch(re.escape(c['prefix'])+r'/[A-Za-z0-9_-]+\.zip\.age', name) or not re.fullmatch('[0-9a-f]{64}',expected_sha):
        raise ValueError('Explicit object name and trusted encrypted SHA256 required')
    preflight()
    os.umask(0o077)
    target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    # Separate private staging, never overwrite/download into target or live state.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='dr-stage-',dir=target.parent) as tmp:
        encrypted=Path(tmp)/'backup.age'; raw=Path(tmp)/'backup.zip'
        size=validate_head(oci(c,'head','--name',name),expected_sha)
        oci(c,'get','--name',name,'--file',str(encrypted))
        if (not encrypted.is_file() or encrypted.is_symlink()
                or encrypted.stat().st_size!=size or digest(encrypted)!=expected_sha):
            raise ValueError('Encrypted checksum mismatch')
        run(['age','--decrypt','--identity',str(key),'--output',str(raw),str(encrypted)])
        target.mkdir(mode=0o700,exist_ok=True)
        target.chmod(0o700)
        native(c,'restore',target,raw)
    return {'status':'isolated native restore verified'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','target','identity','object','sha256'):
        p.add_argument('--'+name, required=True)
    a=p.parse_args()
    try:
        restore(load_config(a.config),a.target,a.identity,a.object,a.sha256)
        print('Isolated restore verified. No gateway started. Remove temporary identity securely after recovery.')
    except (ValueError,OSError,RuntimeError,subprocess.SubprocessError):
        p.exit(1,'Restore failed; target may contain partial state. Live home untouched; private output withheld.\n')


if __name__=='__main__':
    main()
