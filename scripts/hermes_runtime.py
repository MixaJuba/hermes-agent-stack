#!/usr/bin/env python3
"""Pinned Hermes PM entry point. Installs only in the selected remote paths."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]


def source_state(source):
    """Accept only the pinned clean base or the exact reviewed patch; no arbitrary dirt."""
    pin = json.loads((PROJECT / 'config/upstream.json').read_text())
    manifest = json.loads((PROJECT / 'config/hermes-patch.json').read_text())
    patch = PROJECT / manifest['patch']
    if hashlib.sha256(patch.read_bytes()).hexdigest() != manifest['patch_sha256']:
        raise ValueError('Reviewed patch SHA256 mismatch')
    git = lambda *args: subprocess.check_output(['git', *args], cwd=source, text=True).strip()
    if git('rev-parse', 'HEAD') != pin['commit'] or manifest['base_commit'] != pin['commit']:
        raise ValueError('Source HEAD differs from the reviewed Hermes base pin')
    if git('diff', '--cached', '--name-only'):
        raise ValueError('Staged upstream changes are not allowed')
    tracked = set(git('diff', '--name-only', 'HEAD').splitlines())
    untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
    if not tracked and not untracked:
        return 'clean'
    files = manifest['files']
    if tracked != {p for p, v in files.items() if v['base_sha256'] is not None} or untracked != {
            p for p, v in files.items() if v['base_sha256'] is None}:
        raise ValueError('Unreviewed upstream changes or untracked files')
    if git('diff', '--summary', 'HEAD'):
        raise ValueError('Upstream file modes or paths changed')
    for name, hashes in files.items():
        path = source / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != hashes['patched_sha256']:
            raise ValueError('Reviewed patched source file SHA256 mismatch')
    return 'patched'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/workspace/.hermes-runtime/source'))
    parser.add_argument('--home', type=Path, default=Path('/workspace/.hermes-runtime/data'))
    parser.add_argument('--tools', type=Path, default=Path('/workspace/.hermes-runtime/tools'))
    parser.add_argument('command', choices=('apply-patch', 'install', 'cli', 'python'))
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if platform.system() != 'Linux':
        parser.error('This launcher is for the remote Linux environment, not the laptop')
    source = args.source.resolve()
    try:
        state = source_state(source)
    except ValueError as error:
        parser.error(str(error))
    arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
    if args.command == 'apply-patch':
        if arguments:
            parser.error('apply-patch takes no extra arguments')
        if state == 'clean':
            manifest = json.loads((PROJECT / 'config/hermes-patch.json').read_text())
            patch = str(PROJECT / manifest['patch'])
            subprocess.run(['git', 'apply', '--check', patch], cwd=source, check=True)
            subprocess.run(['git', 'apply', patch], cwd=source, check=True)
            if source_state(source) != 'patched':
                parser.error('Patch verification failed; do not run this source')
        print('Pinned source plus reviewed local quota patch verified. No dependency install performed.')
        return 0
    if state != 'patched':
        parser.error('Reviewed local patch absent; run apply-patch first')
    env = dict(os.environ, HERMES_HOME=str(args.home.resolve()),
               HERMES_RUNTIME_DIR=str(args.tools.resolve()))
    # Scripts outside the checkout (and their children) otherwise import PM's
    # installed base snapshot, silently bypassing the verified local source patch.
    env['PYTHONPATH'] = str(source) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    if args.command == 'install':
        if arguments:
            parser.error('install takes no extra arguments')
        env['UV_CACHE_DIR'] = str(args.tools.resolve().parent / 'cache')
        for extra_args in (['--without', 'agent-browser', '--without', 'cua-driver'],
                           ['--extra', 'telegram', '--extra', 'exa']):
            result = subprocess.run([sys.executable, '-m', 'pm.cli', 'install', *extra_args],
                                    cwd=source, env=env)
            if result.returncode:
                return result.returncode
        return 0
    target = {'x86_64': 'linux-x64', 'aarch64': 'linux-arm64'}.get(platform.machine())
    version = json.loads((source / 'pm/lock.json').read_text())['packages']['python']['version']
    base_python = args.tools.resolve() / f'python-{version}-{target}' / 'bin/python3'
    if not base_python.is_file():
        parser.error('Pinned PM Python absent; run the install step first')
    # Resolve the selected application generation through PM, never a guessed venv.
    lookup = 'from pathlib import Path; from pm.environments import project_python; print(project_python(Path.cwd()))'
    app_python = subprocess.check_output([str(base_python), '-c', lookup], cwd=source,
                                         env=env, text=True).strip()
    command = [app_python, str(source / 'hermes'), *arguments] if args.command == 'cli' else [app_python, *arguments]
    return subprocess.run(command, cwd=source, env=env).returncode


if __name__ == '__main__':
    raise SystemExit(main())
