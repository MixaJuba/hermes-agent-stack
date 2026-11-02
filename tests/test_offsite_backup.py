"""Offline DR contracts: binaries/storage stubbed, external socket tripwire."""
import copy
import importlib.util
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
import offsite_restore as r


def recipient():
    # Public-only synthetic bech32 payload; never an age private identity.
    alphabet='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    data=[0]*52
    def polymod(values):
        chk=1
        for v in values:
            top=chk>>25; chk=((chk&0x1ffffff)<<5)^v
            for i,g in enumerate((0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3)):
                if top>>i&1: chk^=g
        return chk
    mod=polymod([3,3,3,0,1,7,5]+data+[0]*6)^1
    return 'age1'+''.join(alphabet[x] for x in data+[mod>>5*(5-i)&31 for i in range(6)])


class OffsiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='h001-test-'); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.c=dict(recipient=recipient(),namespace='synthetic',bucket='synthetic',region='eu-frankfurt-1',prefix='hermes-backups',home=str(self.root/'home'),local_dir=str(self.root/'backups'),restore_root=str(self.root/'restores'))
        (self.root/'home').mkdir()
        self.calls=[]; self.upload=None
        self.env=patch.dict(os.environ,{},clear=True); self.env.start(); self.addCleanup(self.env.stop)
        self.trip=patch.object(socket.socket,'connect',side_effect=AssertionError('external network forbidden')); self.trip.start(); self.addCleanup(self.trip.stop)
        self.which=patch.object(b.shutil,'which',return_value='/stub/tool'); self.which.start(); self.addCleanup(self.which.stop)

    def native(self,action,home,archive):
        self.assertEqual(action,'backup'); archive.write_bytes(b'synthetic raw'); archive.chmod(0o600)

    def age(self,args,**kw):
        self.assertEqual(args[0],'age'); self.calls.append('encrypt')
        Path(args[args.index('--output')+1]).write_bytes(b'age-encryption.org/v1\n'+Path(args[-1]).read_bytes())
        return b''

    def storage(self,c,*args):
        self.calls.append(args[0])
        if args[0]=='put':
            self.upload=Path(args[args.index('--file')+1]); self.assertTrue(self.upload.name.endswith('.zip.age'))
            self.assertTrue(self.upload.read_bytes().startswith(b'age-encryption.org/v1'))
            self.meta=json.loads(args[args.index('--metadata')+1]); return {}
        return {'data':{'content-length':self.upload.stat().st_size,'opc-meta':self.meta}}

    def perform(self):
        with patch.object(b,'native',side_effect=self.native),patch.object(b,'run',side_effect=self.age),patch.object(b,'oci',side_effect=self.storage):
            return b.backup(self.c)

    def test_encrypted_upload_then_mandatory_head(self):
        result=self.perform(); self.assertEqual(self.calls,['encrypt','put','head'])
        self.assertEqual(result['sha256'],b.digest(self.upload))
        self.assertEqual(len(list(Path(self.c['local_dir']).glob('*.zip'))),1)
        self.assertEqual(set(self.meta),{'format','timestamp','sha256','hermes'})

    def test_config_recipient_and_credentials_fail_closed(self):
        for value in ('',None,'age1bad','age1'+'q'*58):
            c={**self.c,'recipient':value}; path=self.root/'config.json'; path.write_text(json.dumps(c))
            with self.subTest(value=value),self.assertRaises(ValueError): b.load_config(path)
        path.write_text(json.dumps({**self.c,'private_key':'not-allowed'}))
        with self.assertRaises(ValueError): b.load_config(path)
        for key in ('OCI_AUTH','OCI_API_KEY','OCI_CONFIG_FILE','OCI_CLI_AUTH','OCI_RESOURCE_PRINCIPAL_RPST'):
            with patch.dict(os.environ,{key:'synthetic'}),self.assertRaises(ValueError): b.preflight()

    def test_upload_failure_keeps_raw_and_encrypted(self):
        with patch.object(b,'native',side_effect=self.native),patch.object(b,'run',side_effect=self.age),patch.object(b,'oci',side_effect=RuntimeError('stub')):
            with self.assertRaises(RuntimeError): b.backup(self.c)
        self.assertEqual(len(list(Path(self.c['local_dir']).glob('*.zip'))),1)
        self.assertEqual(len(list(Path(self.c['local_dir']).glob('*.age'))),1)

    def test_raw_output_or_age_failure_never_uploaded(self):
        def raw_output(args, **kwargs):
            Path(args[args.index('--output')+1]).write_bytes(b'raw not encrypted')
        with patch.object(b,'native',side_effect=self.native),patch.object(b,'run',side_effect=raw_output),patch.object(b,'oci') as upload:
            with self.assertRaises(ValueError): b.backup(self.c)
            upload.assert_not_called()
        with patch.object(b,'native',side_effect=self.native),patch.object(b,'run',side_effect=RuntimeError('age failure')),patch.object(b,'oci') as upload:
            with self.assertRaises(RuntimeError): b.backup(self.c)
            upload.assert_not_called()

    def test_tools_required_and_valid_config(self):
        path=self.root/'config.json'; path.write_text(json.dumps(self.c))
        self.assertEqual(b.load_config(path),self.c)
        with patch.object(b.shutil,'which',return_value=None),self.assertRaises(ValueError): b.preflight()

    def test_remote_mismatch_and_verification_failure_rejected(self):
        self.perform()
        with patch.object(b,'oci',return_value={'data':{'content-length':1,'opc-meta':{}}}),self.assertRaises(ValueError):
            b.check_remote(self.c,'name','0'*64,20)
        with patch.object(b,'oci',side_effect=RuntimeError('HEAD fail')),self.assertRaises(RuntimeError):
            b.check_remote(self.c,'name','0'*64,20)

    def test_instance_principal_cli_only(self):
        with patch.object(b,'run',return_value=b'{}') as run:
            b.oci(self.c,'head','--name','synthetic')
        args=run.call_args.args[0]
        self.assertEqual(args[args.index('--auth')+1],'instance_principal')
        self.assertEqual(args[args.index('--config-file')+1],'/dev/null')
        self.assertEqual(args[args.index('--max-retries')+1],'0')

    def test_unsafe_restore_targets(self):
        root=Path(self.c['restore_root']); root.mkdir()
        good=root/'restore-test'; good.mkdir()
        self.assertEqual(r.target_valid(self.c,good),good)
        (good/'unsafe').write_text('occupied')
        link=root/'restore-link'; link.symlink_to(good,target_is_directory=True)
        for target in (b.LIVE,Path(self.c['home']),good,link,self.root/'unexpected'):
            with self.subTest(target=target),self.assertRaises(ValueError): r.target_valid(self.c,target)

    def test_restore_checksum_prevents_decrypt(self):
        key=self.root/'temporary-test-identity'; key.write_text('SYNTHETIC NOT A PRIVATE KEY'); key.chmod(0o600)
        with patch.object(r,'oci',side_effect=[{'data':{'opc-meta':{'sha256':'0'*64}}},{}]),patch.object(r,'digest',return_value='1'*64),patch.object(r,'run') as age:
            with self.assertRaises(ValueError): r.restore(self.c,Path(self.c['restore_root'])/'restore-test',key,'hermes-backups/synthetic.zip.age','0'*64)
            age.assert_not_called()

    def test_systemd_sanity(self):
        service=(ROOT/'deploy/hermes-backup-offsite.service').read_text(); timer=(ROOT/'deploy/hermes-backup-offsite.timer').read_text()
        self.assertIn('Type=oneshot',service); self.assertIn('Restart=no',service)
        self.assertEqual(service.count('ExecStart='),1); self.assertNotIn('EnvironmentFile=',service)
        self.assertEqual(timer.count('OnCalendar='),1); self.assertNotIn('OnUnitActiveSec=',timer)
        result=subprocess.run(['systemd-analyze','verify','--man=no',str(ROOT/'deploy/hermes-backup-offsite.service'),str(ROOT/'deploy/hermes-backup-offsite.timer')],capture_output=True)
        self.assertEqual(result.returncode,0)


if __name__=='__main__': unittest.main()
