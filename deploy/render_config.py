#!/usr/bin/env python3
"""Render non-secret config after owner confirmation; refuses to overwrite state."""
import argparse
import json
import os
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True)
    args = parser.parse_args()
    owner = os.environ.get('TELEGRAM_ALLOWED_USERS', '')
    if not re.fullmatch(r'[1-9][0-9]*', owner):
        parser.error('Set exactly one confirmed numeric TELEGRAM_ALLOWED_USERS first')
    here = Path(__file__).resolve().parent
    config = json.loads((here / 'hermes-config.json').read_text())
    config['platforms']['telegram']['allowed_chats'] = [owner]
    args.home.mkdir(mode=0o700, parents=True, exist_ok=True)
    locales = args.home / 'locales'
    locales.mkdir(mode=0o700, exist_ok=True)
    plugins = [Path('plugins') / name for name in ('bro-recent-web', 'bro-capabilities')]
    # O_EXCL prevents accidental loss of an existing user profile/config.
    rendered = (json.dumps(config, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    for name, content in [('config.yaml', rendered),
                          ('SOUL.md', (here / 'SOUL.md').read_bytes()),
                          ('locales/uk.yaml', (here / 'locales/uk.yaml').read_bytes()),
                          *((plugin / name, (here / plugin / name).read_bytes())
                            for plugin in plugins
                            for name in ('__init__.py', 'plugin.yaml'))]:
        path = args.home / name
        if path.parent in [args.home / plugin for plugin in plugins]:
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as file:
            os.chmod(path, 0o600)
            file.write(content)
    print('Non-secret profile rendered. No credentials written; gateway not started.')


if __name__ == '__main__':
    main()
