"""Offline CLI contract fixture, not an OCI emulator or real age encryption.

Object HEAD returns a flat JSON header map, with individual opc-meta-* headers.
PUT metadata is a JSON object argument. GET writes --file; its stdout is not
the downloaded object. Only synthetic bytes live in this fixture.
"""
import hashlib
import json
from pathlib import Path


class OfflineCLI:
    AGE_HEADER = b'age-encryption.org/v1\n'

    def __init__(self):
        self.objects = {}
        self.events = []
        self.corrupt_download = False
        self.get_stdout = b''
        self.extra_versions = []

    def run(self, args, *, env=None):
        if args[0] == 'age':
            action = args[1]
            assert action in ('--encrypt', '--decrypt')
            expected = ['age', action, '--recipient' if action == '--encrypt' else '--identity',
                        args[3], '--output', args[5], args[6]]
            assert args == expected
            source, target = Path(args[6]), Path(args[5])
            assert not target.exists()
            payload = source.read_bytes()
            self.events.append('encrypt' if action == '--encrypt' else 'decrypt')
            if action == '--encrypt':
                target.write_bytes(self.AGE_HEADER + payload)
            else:
                assert payload.startswith(self.AGE_HEADER)
                target.write_bytes(payload[len(self.AGE_HEADER):])
            target.chmod(0o600)
            return b''

        assert args[0] == 'oci', 'Unstubbed subprocess forbidden'
        assert args[1:15] == ['--output', 'json', '--auth', 'instance_principal',
                             '--region', args[6], '--config-file', '/dev/null',
                             '--max-retries', '0', '--connection-timeout', '15',
                             '--read-timeout', '60']
        assert args[15:17] == ['os', 'object']
        assert set(env or {}) <= {'PATH', 'LANG', 'SSL_CERT_FILE'}
        action = args[17]
        self.events.append(action)
        flags = args[18:]
        opts = {}
        while flags:
            key, *flags = flags
            assert key not in opts
            if key in ('--no-overwrite','--no-multipart'):
                opts[key] = True
            else:
                value, *flags = flags
                opts[key] = value
        common = {'--name', '--namespace-name', '--bucket-name'}
        if action == 'list-object-versions':
            assert set(opts)=={'--namespace-name','--bucket-name','--fields','--limit'}
            assert opts['--fields']=='name,size,storageTier'
            items=[{'name':name,'size':len(data),'storage-tier':'Standard'} for name,(data,metadata) in self.objects.items()]
            items+=self.extra_versions
            return json.dumps({'data':{'items':items[:int(opts['--limit'])],'prefixes':[]}}).encode()
        name = opts['--name']
        if action == 'put':
            assert set(opts)-{'--no-multipart'} == common | {'--file', '--no-overwrite', '--storage-tier', '--metadata'}
            assert opts['--storage-tier'] == 'Standard' and name not in self.objects
            data = Path(opts['--file']).read_bytes()
            assert opts['--file'].endswith('.zip.age') and data.startswith(self.AGE_HEADER)
            metadata = json.loads(opts['--metadata'])
            assert set(metadata) == {'sha256', 'format', 'timestamp', 'hermes'}
            assert metadata['sha256'] == hashlib.sha256(data).hexdigest()
            self.objects[name] = (data, metadata)
            # PUT returns headers, not the uploaded bytes or HEAD metadata.
            return json.dumps({'etag': 'synthetic-etag', 'last-modified': 'Sat, 07 Nov 2026 00:00:00 GMT',
                               'opc-content-md5': 'synthetic-md5'}).encode()
        if action == 'head':
            assert set(opts) == common
            data, metadata = self.objects[name]
            return json.dumps({'content-length': str(len(data)), 'etag': 'synthetic-etag',
                               'content-type': 'application/octet-stream',
                               **{'opc-meta-' + k: v for k, v in metadata.items()}}).encode()
        if action == 'get':
            assert set(opts) == common | {'--file'}
            data = self.objects[name][0]
            if self.corrupt_download:
                data = data[:-1] + bytes([data[-1] ^ 1])
            target = Path(opts['--file'])
            assert not target.exists()
            target.write_bytes(data)
            target.chmod(0o600)
            return self.get_stdout
        raise AssertionError('Unexpected OCI operation')
