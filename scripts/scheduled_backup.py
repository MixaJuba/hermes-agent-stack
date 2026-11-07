"""Bounded scheduled wrapper around accepted native backup; never deletes OCI objects.

Protected short-lived operator approval + version-aware inventory + durable
attempt reservation. Lost/ambiguous state fails closed. Stdlib only.
"""
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

import offsite_backup as b

UTC=dt.timezone.utc


def utcnow():
    return dt.datetime.now(UTC)


def timestamp(value):
    if not isinstance(value,str): raise ValueError('UTC string required')
    result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None or result.utcoffset()!=dt.timedelta(0):
        raise ValueError('Explicit UTC timestamp required')
    return result


def protected(path, *, operator=False):
    path=Path(path)
    st=path.lstat()
    mode=stat.S_IMODE(st.st_mode)
    permissions=(mode in (0o600,0o400) or (operator and st.st_uid==0 and mode==0o640
                  and st.st_gid in {*os.getgroups(),os.getgid()}))
    if (path.resolve()!=path or not stat.S_ISREG(st.st_mode) or st.st_nlink!=1
            or not permissions
            or st.st_uid not in ({0,os.getuid()} if operator else {os.getuid()})):
        raise ValueError('Protected regular file required')
    return path


def private_dir(path):
    path=Path(path)
    path.mkdir(mode=0o700,parents=True,exist_ok=True)
    if path.resolve()!=path or path.stat().st_uid!=os.getuid() or stat.S_IMODE(path.stat().st_mode)!=0o700:
        raise ValueError('Private owned state directory required')
    return path


def atomic(path, data):
    path=Path(path)
    if path.exists(): protected(path)
    elif path.is_symlink(): raise ValueError('State symlink forbidden')
    fd,name=tempfile.mkstemp(prefix='.state-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(name): os.unlink(name)  # only this function's newly-created temporary


@contextmanager
def lock(directory,name):
    fd=os.open(directory/name,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'r+') as f:
        protected(directory/name)
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def load_policy(path):
    raw=protected(path,operator=True).read_bytes()
    p=json.loads(raw)
    keys={'backup_config','state_dir','checked_at','expires_at','zero_cost_confirmed',
          'independent_recovery_confirmed','exclusive_bucket_writer_confirmed','owner_receipt_delivery_confirmed','max_runs',
          'max_remote_objects','max_remote_bytes','last_verified'}
    if not isinstance(p,dict) or set(p)!=keys: raise ValueError('Unexpected scheduled policy')
    for key in ('backup_config','state_dir'):
        value=Path(p[key])
        if not value.is_absolute() or value.resolve()!=value or value==Path('/'):
            raise ValueError('Canonical paths required')
    for key,maximum in (('max_runs',7),('max_remote_objects',100),('max_remote_bytes',1073741824)):
        if type(p[key]) is not int or not 1<=p[key]<=maximum: raise ValueError('Explicit conservative bounds required')
    start,end=timestamp(p['checked_at']),timestamp(p['expires_at'])
    if not dt.timedelta(0)<end-start<=dt.timedelta(days=7): raise ValueError('Approval window must be at most seven days')
    ref=p['last_verified']
    if (not isinstance(ref,dict) or set(ref)!={'object','sha256','bytes','verified_at'}
            or not isinstance(ref['object'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]+\.zip\.age',ref['object'])
            or len(ref['object'])>300 or not isinstance(ref['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',ref['sha256'])
            or type(ref['bytes']) is not int or ref['bytes']<=0): raise ValueError('Known verified backup reference required')
    if timestamp(ref['verified_at'])>start: raise ValueError('Backup verification time cannot be invented/future')
    return p,hashlib.sha256(raw).hexdigest()


def approved(p,now):
    if any(p[k] is not True for k in ('zero_cost_confirmed','independent_recovery_confirmed','exclusive_bucket_writer_confirmed','owner_receipt_delivery_confirmed')):
        raise ValueError('Operator approval missing')
    if not timestamp(p['checked_at'])<=now<timestamp(p['expires_at']): raise ValueError('Approval expired or clock invalid')


def inventory(c,p,reserve):
    # Generated OCI CLI list-object-versions: data.items, explicit fields; --limit
    # bounds results even for a bucket with unexpected writes/versions. No --all.
    response=b.oci(c,'list-object-versions','--fields','name,size,storageTier',
                   '--limit',str(p['max_remote_objects']))
    data=response.get('data')
    if not isinstance(data,dict) or not isinstance(data.get('items'),list) or data.get('prefixes'):
        raise ValueError('Unknown version inventory')
    items=data['items']
    if (len(items)>=p['max_remote_objects'] or response.get('opc-next-page')
            or data.get('next-start-with') or data.get('next-start-with-version-id')):
        raise ValueError('Inventory incomplete or remote object cap reached')
    total=0
    for item in items:
        if not isinstance(item,dict) or not isinstance(item.get('name'),str): raise ValueError('Malformed version')
        size=item.get('size')
        if item.get('is-delete-marker') is True and size is None: size=0
        if type(size) is not int or size<0: raise ValueError('Version size unknown')
        if item.get('storage-tier')!='Standard' and item.get('is-delete-marker') is not True:
            raise ValueError('Unexpected/unknown storage tier')
        total+=size
    if total+reserve>p['max_remote_bytes']: raise ValueError('Remote byte budget reached')
    return {'versions':len(items),'bytes':total}


def read_state(directory,digest):
    s=json.loads(protected(directory/'job.json').read_text())
    if (not isinstance(s,dict) or s.get('schema')!='h002-job-v1' or s.get('policy_sha256')!=digest
            or type(s.get('runs')) is not int or s['runs']<0 or s.get('status') not in ('initialized','running','failed','verified')
            or not {'last_success','last_attempt','latest','inventory'}<=set(s)):
        raise ValueError('State absent/ambiguous or policy changed; operator reconciliation required')
    timestamp(s['last_success'])
    ref=s['latest']
    if (not isinstance(ref,dict) or set(ref)!={'object','sha256','bytes','verified_at'}
            or not isinstance(ref['object'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]+\.zip\.age',ref['object'])
            or len(ref['object'])>300 or not isinstance(ref['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',ref['sha256'])
            or type(ref['bytes']) is not int or ref['bytes']<=0
            or timestamp(ref['verified_at'])!=timestamp(s['last_success'])):
        raise ValueError('Verified reference inconsistent')
    if s['last_attempt'] is not None: timestamp(s['last_attempt'])
    if s['status']!='initialized' and s['last_attempt'] is None: raise ValueError('Missing attempt timestamp')
    return s


def verify_previous(c,ref):
    if not re.fullmatch(re.escape(c['prefix'])+r'/[A-Za-z0-9_-]+\.zip\.age',ref['object']):
        raise ValueError('Unexpected verified object reference')
    b.check_remote(c,ref['object'],ref['sha256'],ref['bytes'])


def execute(policy_path,initialize=False,now=None):
    os.umask(0o077)
    clock=(lambda: now) if now is not None else utcnow
    now=clock()
    p,digest=load_policy(policy_path); approved(p,now)
    c=b.load_config(protected(p['backup_config'],operator=True)); b.preflight()
    directory=private_dir(p['state_dir'])
    with lock(directory,'.job.lock'):
        if initialize:
            if (directory/'job.json').exists() or (directory/'job.json').is_symlink(): raise ValueError('Never overwrite existing job state')
            usage=inventory(c,p,c['max_archive_bytes']+1048576)
            verify_previous(c,p['last_verified'])
            s={'schema':'h002-job-v1','policy_sha256':digest,'runs':0,'status':'initialized',
               'last_success':p['last_verified']['verified_at'],'last_attempt':None,'latest':p['last_verified'],'inventory':usage}
            atomic(directory/'job.json',s)
            return
        s=read_state(directory,digest)
        if now<timestamp(s['last_success']): raise ValueError('Clock precedes latest verified backup')
        if s['runs']>=p['max_runs']: raise ValueError('Run budget exhausted')
        if s['last_attempt'] and now.date()<=timestamp(s['last_attempt']).date(): raise ValueError('At most one attempt per UTC day')
        # Reserve before the first network call. Timeout/ambiguous PUT is charged,
        # never refunded or blindly retried, even if the upload actually succeeded.
        s.update(runs=s['runs']+1,status='running',stage='inventory',last_attempt=now.isoformat())
        atomic(directory/'job.json',s)
        try:
            s['inventory']=inventory(c,p,c['max_archive_bytes']+1048576)
            s['stage']='previous_reference'; atomic(directory/'job.json',s)
            verify_previous(c,s['latest'])
            s['stage']='native_encrypt_upload'; atomic(directory/'job.json',s)
            def upload_gate():
                current,signature=load_policy(policy_path)
                if signature!=digest: raise ValueError('Approval revoked/changed during backup')
                approved(current,clock())
            result=b.backup(c,no_multipart=True,before_upload=upload_gate)
            encrypted=Path(c['local_dir'])/Path(result['object']).name
            verified=clock().isoformat()
            s.update(status='verified',stage='verified',last_success=verified,
                     latest={'object':result['object'],'sha256':result['sha256'],'bytes':encrypted.stat().st_size,'verified_at':verified})
            atomic(directory/'job.json',s)
        except Exception:
            s['status']='failed'; atomic(directory/'job.json',s)
            raise


def health(p,digest,directory,now,force=False):
    if force: return 'failed'
    try:
        approved(p,now); s=read_state(directory,digest)
        if now<timestamp(s['last_success']): return 'clock'
        if s['status']=='failed': return 'failed'
        if now-timestamp(s['last_success'])>dt.timedelta(hours=36): return 'stale'
        if s['last_attempt'] and now<timestamp(s['last_attempt']): return 'clock'
        if s['status']=='running' and now-timestamp(s['last_attempt'])>dt.timedelta(hours=1): return 'interrupted'
        if s['runs']>=p['max_runs'] or timestamp(p['expires_at'])-now<dt.timedelta(hours=24): return 'renewal'
        return 'healthy'
    except (ValueError,TypeError,KeyError,OSError): return 'review'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('init','run','watch'))
    parser.add_argument('--policy',required=True,type=Path)
    parser.add_argument('--notification-file',type=Path)
    parser.add_argument('--state-dir',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='watch':
            from backup_notify import watch
            if args.notification_file is None or args.state_dir is None: raise ValueError('Protected notification file/state directory required')
            watch(args.policy,args.notification_file,args.state_dir,force=os.environ.get('MONITOR_SERVICE_RESULT','success')!='success')
        else: execute(args.policy,initialize=args.command=='init')
        print('Backup automation check completed; private details withheld.')
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,subprocess.SubprocessError):
        parser.exit(1,'Backup automation requires review; private details withheld.\n')


if __name__=='__main__': main()
