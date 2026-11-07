"""Verify a code-only export against an explicit trusted Git commit, offline.

No runtime home/credentials are read. Version strings and export directory names
are not provenance. The reference checkout and expected commit come from the
operator's independently preserved recovery record.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess


def verify(reference, commit, export):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Exact trusted commit SHA required')
    export = Path(export)
    if export.resolve() != export or not export.is_dir():
        raise ValueError('Canonical code-only export required')
    git = lambda *args: subprocess.check_output(['git','-C',str(reference),*args],stderr=subprocess.DEVNULL)
    entries = git('ls-tree','-rz','--full-tree',commit).split(b'\0')
    expected = {}
    for entry in filter(None,entries):
        meta, name = entry.split(b'\t',1)
        mode, kind, oid = meta.decode().split()
        name = name.decode()
        if kind != 'blob' or mode not in ('100644','100755') or '..' in Path(name).parts or Path(name).is_absolute():
            raise ValueError('Unsupported export tree entry')
        expected[name] = (mode,oid)
    paths = list(export.rglob('*'))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths):
        raise ValueError('Symlink/special file in export')
    if {p.relative_to(export).as_posix() for p in paths if p.is_file()} != set(expected):
        raise ValueError('Export file set differs from trusted tree')
    for name,(mode,oid) in expected.items():
        p=export/name
        data=p.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=oid or bool(p.stat().st_mode & 0o111)!=(mode=='100755'):
            raise ValueError('Export blob/mode mismatch')
    return {'commit':commit,'tree':git('rev-parse',commit+'^{tree}').decode().strip(),
            'files_verified':len(expected),'status':'PASS; code export only, not runtime attestation'}


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--export',type=Path,required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(verify(args.reference,args.commit,args.export)))
    except (ValueError,OSError,subprocess.SubprocessError):
        parser.exit(1,'Export provenance failed; no runtime changes performed.\n')
