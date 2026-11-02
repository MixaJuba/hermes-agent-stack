"""Pinned catalog installation / stdlib-only startup attestation. No credentials read."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / 'config/cloudflare-plugin.json').read_text())


def attest(home):
    problems = []
    plugins = Path(home) / 'plugins'
    target = plugins / PIN['name']
    if target.is_symlink() or not target.is_dir():
        return ['pinned Cloudflare plugin is missing or symlinked']
    try:
        metadata_path = plugins / '.install-metadata.json'
        if metadata_path.is_symlink():
            return ['plugin provenance symlink requires review']
        record = json.loads(metadata_path.read_text()).get(PIN['name'], {})
        if (record.get('revision') != PIN['commit'] or record.get('pinned') is not True
                or record.get('source') != PIN['repository'] + '#' + PIN['subdir']):
            problems.append('Cloudflare plugin revision/source is not the approved exact pin')
        for name, digest in PIN['files'].items():
            path = target / name
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                problems.append('Cloudflare plugin source integrity mismatch')
        if any(p.name not in PIN['files'] and p.name != '__pycache__' for p in target.iterdir()):
            problems.append('unreviewed files in Cloudflare plugin')
        if any(p.is_dir() and not p.name.startswith('.') and p.name != PIN['name'] for p in plugins.iterdir()):
            problems.append('additional profile plugins require review')
    except (OSError, ValueError, AttributeError):
        problems.append('Cloudflare plugin provenance/integrity unavailable')
    return sorted(set(problems))


def catalog_entry(source):
    # Uses the catalog bundled in the pinned source, never the mutable live catalog.
    from hermes_cli.plugin_catalog import load_catalog
    entry = next(e for e in load_catalog(Path(source) / 'plugin-catalog') if e.name == PIN['name'])
    if (entry.repo, entry.sha, entry.subdir, entry.tier) != (
            PIN['repository'], PIN['commit'], PIN['subdir'], PIN['tier']):
        raise ValueError('Pinned Hermes catalog differs from the approved Cloudflare entry')
    return entry


def install_at_pin(source):
    from hermes_cli.plugins_cmd_catalog import install_catalog_entry
    return install_catalog_entry(catalog_entry(source), force=False, ref=PIN['commit'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('install', 'check'))
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    if args.command == 'install':
        if args.source is None:
            parser.error('install requires the pinned --source')
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from hermes_runtime import source_state
        if source_state(args.source.resolve()) != 'patched':
            parser.error('reviewed patched Hermes source required')
        from hermes_constants import get_hermes_home
        if get_hermes_home().resolve() != args.home.resolve():
            parser.error('run under the intended HERMES_HOME through hermes_runtime.py')
        if (args.home / 'plugins' / PIN['name']).exists():
            problems = attest(args.home)
            if problems:
                parser.error('existing plugin requires review; refusing replacement')
        else:
            install_at_pin(args.source)
    problems = attest(args.home)
    for problem in problems:
        print('BLOCKED: ' + problem)
    if not problems:
        print('Pinned community Cloudflare ProviderProfile attested; no inference performed.')
    return 2 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
