"""Synthetic schedule/storage/notification failures; no real external sockets."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import offsite_backup as b
import scheduled_backup as s
import backup_notify as n
from offsite_cli_stub import OfflineCLI
from test_offsite_backup import recipient,LIMITS


class ScheduledBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='h002-offline-'); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.now=dt.datetime(2026,11,7,7,tzinfo=s.UTC)
        self.c=dict(recipient=recipient(),namespace='synthetic',bucket='synthetic',region='eu-frankfurt-1',prefix='hermes-backups',home=str(self.root/'home'),local_dir=str(self.root/'backups'),restore_root=str(self.root/'restores'),hermes_source=str(self.root/'source'),hermes_tools=str(self.root/'tools'),**LIMITS)
        Path(self.c['home']).mkdir(mode=0o700)
        self.backup=self.root/'backup.json'; self.write(self.backup,self.c)
        self.cli=OfflineCLI(); payload=OfflineCLI.AGE_HEADER+b'known synthetic recovery'
        self.ref={'object':'hermes-backups/seed.zip.age','sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),
                  'verified_at':(self.now-dt.timedelta(hours=1)).isoformat()}
        self.cli.objects[self.ref['object']]=(payload,{'format':'hermes-age-v1','sha256':self.ref['sha256']})
        self.p={'backup_config':str(self.backup),'state_dir':str(self.root/'state'),
                'checked_at':self.now.isoformat(),'expires_at':(self.now+dt.timedelta(days=6)).isoformat(),
                'zero_cost_confirmed':True,'independent_recovery_confirmed':True,'exclusive_bucket_writer_confirmed':True,'owner_receipt_delivery_confirmed':True,
                'max_runs':7,'max_remote_objects':14,'max_remote_bytes':268435456,'last_verified':self.ref}
        self.policy=self.root/'schedule.json'; self.write(self.policy,self.p)
        self.cred=self.root/'telegram-only.env'
        self.cred.write_text('TELEGRAM_BOT_TOKEN='+str(123456789)+':'+'x'*35+'\nTELEGRAM_ALLOWED_USERS=1234567\n')
        self.cred.chmod(0o600)
        for patcher in (patch.dict(os.environ,{},clear=True),patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),
                        patch('socket.create_connection',side_effect=AssertionError('network forbidden')),patch.object(b,'preflight'),
                        patch.object(b,'run',side_effect=self.cli.run),patch.object(b,'native',side_effect=self.native)):
            patcher.start(); self.addCleanup(patcher.stop)

    def write(self,path,value):
        path.write_text(json.dumps(value)); path.chmod(0o600)

    def native(self,c,action,home,archive):
        self.assertEqual(action,'backup'); archive.write_bytes(b'synthetic raw'); archive.chmod(0o600)

    def init(self): s.execute(self.policy,initialize=True,now=self.now)

    def state(self):
        return s.read_state(Path(self.p['state_dir']),s.load_policy(self.policy)[1])

    def watch(self,now=None,force=False):
        return n.watch(self.policy,self.cred,Path(self.p['state_dir']),now=now or self.now,force=force)

    def test_real_wrapper_accepted_backup_cli_path_and_daily_reservation(self):
        self.init(); self.cli.events.clear()
        s.execute(self.policy,now=self.now)
        self.assertEqual(self.cli.events,['list-object-versions','head','encrypt','put','head'])
        state=self.state(); self.assertEqual(state['status'],'verified'); self.assertEqual(state['runs'],1)
        self.assertIn(self.ref['object'],self.cli.objects)  # no remote deletion
        self.assertNotEqual(state['latest']['object'],self.ref['object'])
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now+dt.timedelta(minutes=1))
        self.assertEqual(self.state()['runs'],1)
        s.execute(self.policy,now=self.now+dt.timedelta(days=1))
        self.assertEqual(self.state()['runs'],2)
        self.assertEqual(len(list(Path(self.c['local_dir']).glob('*.zip'))),1)

    def test_default_false_approval_expiry_future_and_changed_policy_stop(self):
        for change in ({'zero_cost_confirmed':False},{'independent_recovery_confirmed':False},
                       {'exclusive_bucket_writer_confirmed':False}, {'owner_receipt_delivery_confirmed':False}, {'max_runs':8},
                       {'checked_at':None},{'expires_at':(self.now+dt.timedelta(days=8)).isoformat()}):
            self.write(self.policy,{**self.p,**change})
            with self.subTest(change=change),self.assertRaises((ValueError,TypeError)): self.init()
        self.write(self.policy,self.p); self.init()
        for now in (self.now-dt.timedelta(seconds=1),self.now+dt.timedelta(days=7)):
            with self.assertRaises(ValueError): s.execute(self.policy,now=now)
        self.write(self.policy,{**self.p,'max_runs':6})
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)

    def test_missing_corrupt_state_never_reinitializes_or_uploads(self):
        with self.assertRaises(OSError): s.execute(self.policy,now=self.now)
        self.assertFalse(self.cli.events)
        self.init()
        with self.assertRaises(ValueError): self.init()
        self.write(Path(self.p['state_dir'])/'job.json',{})
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.assertNotIn('put',self.cli.events)

    def test_remote_versions_and_bytes_limits_fail_before_native_or_put(self):
        self.init()
        # Old versions count independently, even when their object name is the same.
        self.cli.extra_versions=[{'name':self.ref['object'],'size':1,'storage-tier':'Standard'}]*13
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.assertNotIn('put',self.cli.events)
        self.assertEqual(self.state()['runs'],1)
        self.assertEqual(self.state()['latest'],self.ref)
        for items in ([{'name':'old','size':268435456}], [{'name':'unknown'}],
                      [{'name':'paid','size':1,'storage-tier':'Archive'}]):
            with patch.object(b,'oci',return_value={'data':{'items':items}}),self.assertRaises(ValueError):
                s.inventory(self.c,self.p,1)

    def test_unknown_inventory_pagination_delete_marker_and_flat_contract(self):
        for response in ({}, {'data':{'objects':[]}}, {'data':{'items':[]},'opc-next-page':'synthetic'},
                         {'data':{'items':[],'prefixes':['unknown/']}}, {'data':{'items':[None]}}):
            with self.subTest(response=response),patch.object(b,'oci',return_value=response),self.assertRaises(ValueError):
                s.inventory(self.c,self.p,1)
        with patch.object(b,'oci',return_value={'data':{'items':[{'name':'old','is-delete-marker':True,'size':None}]}}):
            self.assertEqual(s.inventory(self.c,self.p,1),{'versions':1,'bytes':0})

    def test_iam_timeout_and_last_verified_reference_failure_spend_attempt(self):
        self.init(); previous=self.ref.copy()
        with patch.object(b,'oci',side_effect=RuntimeError('synthetic denied or timeout')):
            with self.assertRaises(RuntimeError): s.execute(self.policy,now=self.now)
        state=self.state(); self.assertEqual(state['runs'],1); self.assertEqual(state['status'],'failed')
        self.assertEqual(state['stage'],'inventory'); self.assertEqual(state['latest'],previous)
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.cli.objects[self.ref['object']][1]['sha256']='0'*64
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now+dt.timedelta(days=1))
        self.assertEqual(self.state()['stage'],'previous_reference')
        self.assertNotIn('put',self.cli.events)

    def test_ambiguous_put_is_not_refunded_or_blindly_retried(self):
        self.init(); original=self.cli.run
        def transport(args,**kwargs):
            data=original(args,**kwargs)
            if 'put' in args:
                self.assertIn('--no-multipart',args)
                raise RuntimeError('Synthetic acknowledgement loss')
            return data
        with patch.object(b,'run',side_effect=transport),self.assertRaises(RuntimeError): s.execute(self.policy,now=self.now)
        self.assertEqual(self.state()['runs'],1); self.assertEqual(self.state()['latest'],self.ref)
        self.assertEqual(self.cli.events.count('put'),1)
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.assertEqual(self.cli.events.count('put'),1)

    def test_revoked_or_expired_approval_is_rechecked_before_upload(self):
        self.init(); original=self.cli.run
        def revoke(args,**kwargs):
            result=original(args,**kwargs)
            if args[0]=='age': self.write(self.policy,{**self.p,'zero_cost_confirmed':False})
            return result
        with patch.object(b,'run',side_effect=revoke),self.assertRaises(ValueError):
            s.execute(self.policy,now=self.now)
        self.assertNotIn('put',self.cli.events)
        self.assertIn(self.ref['object'],self.cli.objects)
        self.write(self.policy,self.p)
        # Across midnight/expiry, use a fresh live clock at the upload boundary.
        day=self.now+dt.timedelta(days=1)
        with patch.object(s,'utcnow',side_effect=[day,self.now+dt.timedelta(days=7)]),self.assertRaises(ValueError):
            s.execute(self.policy)
        self.assertNotIn('put',self.cli.events)

    def test_budget_exhausted_clock_and_stale_freshness_are_detected(self):
        self.init(); directory=Path(self.p['state_dir']); digest=s.load_policy(self.policy)[1]
        self.assertEqual(s.health(self.p,digest,directory,self.now),'healthy')
        self.assertEqual(s.health(self.p,digest,directory,self.now+dt.timedelta(hours=37)),'stale')
        self.assertEqual(s.health(self.p,digest,directory,self.now-dt.timedelta(minutes=1)),'review')
        state=self.state(); state['runs']=7; s.atomic(directory/'job.json',state)
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.assertEqual(s.health(self.p,digest,directory,self.now),'renewal')

    def test_notifications_persist_offline_retry_bound_and_healthy_heartbeat(self):
        self.init()
        with patch.object(n,'send',side_effect=OSError('synthetic offline')) as send:
            for hour in range(5):
                if hour<3:
                    with self.assertRaises(RuntimeError): self.watch(self.now+dt.timedelta(hours=hour),True)
                else: self.watch(self.now+dt.timedelta(hours=hour),True)
            self.assertEqual(send.call_count,3)
        queue=json.loads((Path(self.p['state_dir'])/'notify.json').read_text())
        self.assertIsNotNone(queue['pending']); self.assertIsNone(queue['delivered'])
        with patch.object(n,'send') as send:
            self.watch(self.now+dt.timedelta(days=1))
            self.watch(self.now+dt.timedelta(days=1,minutes=30))
            self.assertEqual(send.call_count,1)
            self.assertIn('36',send.call_args.args[1])

    def test_policy_failure_and_forced_systemd_failure_still_alert(self):
        self.init(); self.policy.write_text('{}')
        with patch.object(n,'send') as send:
            self.watch(); self.assertIn('Конфігурація',send.call_args.args[1])
        self.write(self.policy,self.p)
        with patch.object(n,'send') as send:
            self.watch(self.now+dt.timedelta(hours=1),True)
            self.assertIn('помилкою',send.call_args.args[1])

    def test_new_verified_receipt_is_sent_even_after_same_day_heartbeat(self):
        self.init()
        with patch.object(n,'send') as send:
            self.watch()
            s.execute(self.policy,now=self.now)
            self.watch(self.now+dt.timedelta(hours=1))
            self.assertEqual(send.call_count,2)
            text=send.call_args.args[1]; latest=self.state()['latest']
            self.assertIn(latest['object'],text); self.assertIn(latest['sha256'],text)
            self.assertNotIn('TELEGRAM_BOT_TOKEN',text)
            queue=json.loads((Path(self.p['state_dir'])/'notify.json').read_text())
            self.assertIn(latest['sha256'],queue['delivered'])

    def test_state_permission_symlink_and_corruption_fail_closed(self):
        self.init(); directory=Path(self.p['state_dir'])
        with (directory/'.job.lock').open('r+') as lock:
            s.fcntl.flock(lock,s.fcntl.LOCK_EX|s.fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError): s.execute(self.policy,now=self.now)
        path=directory/'job.json'; path.chmod(0o644)
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        path.chmod(0o600)
        state=self.state(); state['latest']['sha256']='not-a-digest'; self.write(path,state)
        with self.assertRaises(ValueError): s.execute(self.policy,now=self.now)
        self.assertNotIn('put',self.cli.events)

    def test_credential_permissions_owner_and_extra_routes_rejected(self):
        for text in ('TELEGRAM_ALLOWED_USERS=*\n',self.cred.read_text()+'EXA_API_KEY=forbidden\n',
                     self.cred.read_text()+'TELEGRAM_ALLOWED_USERS=999\n'):
            path=self.root/'invalid.env'; path.write_text(text); path.chmod(0o600)
            with self.assertRaises(ValueError): n.credentials(path)
        self.cred.chmod(0o644)
        with self.assertRaises(ValueError): n.credentials(self.cred)
        link=self.root/'link'; link.symlink_to(self.policy)
        with self.assertRaises(ValueError): s.load_policy(link)

    def test_sender_uses_only_sendmessage_no_redirects_or_untrusted_owner(self):
        class Response:
            status=200
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self,limit): return b'{"ok":true,"result":{"chat":{"id":1234567}}}'
        with patch.object(n.urllib.request,'build_opener') as build:
            build.return_value.open.return_value=Response()
            n.send(self.cred,'synthetic Ukrainian text')
            request=build.return_value.open.call_args.args[0]
            self.assertTrue(request.full_url.endswith('/sendMessage'))
            self.assertEqual(request.method,'POST')
            self.assertNotIn('getUpdates',request.full_url)
            self.assertEqual(build.return_value.open.call_args.kwargs['timeout'],10)
            self.assertIsNone(n.NoRedirect().redirect_request(None,None,None,None,None,None))
        self.assertNotIn('polling',(ROOT/'scripts/backup_notify.py').read_text())

    def test_units_are_oneshot_bounded_inactive_artifacts(self):
        units=[ROOT/'deploy'/name for name in ('hermes-backup-offsite.service','hermes-backup-offsite.timer',
                                               'hermes-backup-watch.service','hermes-backup-watch.timer')]
        result=subprocess.run(['systemd-analyze','verify','--man=no',*map(str,units)],capture_output=True)
        self.assertEqual(result.returncode,0)
        service=units[0].read_text(); watch=units[2].read_text()
        self.assertIn('OnFailure=hermes-backup-watch.service',service)
        self.assertNotIn('EnvironmentFile=',service+watch)
        self.assertIn('LoadCredential=',watch)
        self.assertIn('InaccessiblePaths=/var/lib/hermes-agent',watch)
        self.assertEqual(service.count('ExecStart='),1)
        self.assertIn('Restart=no',service+watch)


if __name__=='__main__': unittest.main()
