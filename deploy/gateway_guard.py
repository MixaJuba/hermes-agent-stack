#!/usr/bin/env python3
"""Fail-closed startup checks. Never prints credentials or starts the gateway."""
import argparse
import json
import os
from pathlib import Path
import re
import stat


def validate(config, env):
    problems = []
    owner = env.get('TELEGRAM_ALLOWED_USERS', '')
    if not re.fullmatch(r'[1-9][0-9]*', owner):
        problems.append('exactly one confirmed numeric owner ID is required')
    for name in ('NVIDIA_API_KEY', 'EXA_API_KEY', 'TELEGRAM_BOT_TOKEN'):
        if not env.get(name):
            problems.append(name + ' is missing')
    # A global/group grant or explicit allow-all must not override the one owner.
    for name in ('GATEWAY_ALLOWED_USERS', 'TELEGRAM_GROUP_ALLOWED_USERS', 'TELEGRAM_GROUP_ALLOWED_CHATS',
                 'TELEGRAM_ALLOWED_GROUPS', 'TELEGRAM_GROUP_ALLOW_FROM'):
        if env.get(name):
            problems.append('additional global/group access is forbidden')
    for name in ('GATEWAY_ALLOW_ALL_USERS', 'TELEGRAM_ALLOW_ALL_USERS'):
        if env.get(name, '').lower() not in ('', 'false', '0', 'no'):
            problems.append('allow-all access is forbidden')
    model = config.get('model', {})
    if (model.get('provider') != 'nvidia' or model.get('default') != 'deepseek-ai/deepseek-v4.1-flash'
            or model.get('base_url') != 'https://integrate.api.nvidia.com/v1' or config.get('fallback_model') != []):
        problems.append('unreviewed model route or fallback')
    web = config.get('web', {})
    if any(web.get(k) != 'exa' for k in ('backend', 'search_backend', 'extract_backend')) or any(
            web.get(k) is not False for k in ('keyless_fallback', 'keyless_rescue')):
        problems.append('web routing must be Exa only, with rescue disabled')
    terminal = config.get('terminal', {})
    if (terminal.get('backend') != 'docker' or terminal.get('docker_network') is not False
            or terminal.get('docker_mount_cwd_to_workspace') is not False
            or terminal.get('docker_run_as_host_user') is not True
            or any(terminal.get(k) for k in ('docker_forward_env', 'docker_env', 'docker_volumes'))):
        problems.append('tool sandbox permits host data, secrets or network')
    if terminal.get('docker_extra_args') != ['--pids-limit', '128']:
        problems.append('unreviewed Docker flags')
    if config.get('auth', {}).get('adopt_external_logins') is not False:
        problems.append('external login adoption must stay disabled')
    if config.get('security', {}).get('allow_lazy_installs') is not False:
        problems.append('automatic dependency installation must stay disabled')
    agent = config.get('agent', {})
    if agent.get('api_max_retries') != 1 or agent.get('auto_recovery_cycles') != 0:
        problems.append('automatic inference retry ladder must stay disabled')
    auxiliary = config.get('auxiliary', {})
    for task in ('compression', 'session_search', 'web_extract'):
        route = auxiliary.get(task, {})
        if (route.get('provider') != 'nvidia' or route.get('model') != model.get('default')
                or route.get('fallback_chain') != []):
            problems.append('auxiliary routes must be pinned to NVIDIA without fallback')
    telegram = config.get('platforms', {}).get('telegram', {})
    if (telegram.get('dm_policy') != 'allowlist' or telegram.get('group_policy') != 'disabled'
            or telegram.get('guest_mode') is not False or telegram.get('allowed_chats') != [owner]):
        problems.append('Telegram must be restricted to the confirmed owner DM')
    if telegram.get('extra') or any(telegram.get(k) for k in ('allow_from', 'allow_admin_from', 'group_allow_from')):
        problems.append('additional Telegram policy overrides require review')
    return sorted(set(problems))


def validate_pairing(home, owner):
    """Inspect both upstream layouts without creating/migrating/deleting state."""
    problems = []
    for directory in ('pairing', 'platforms/pairing'):
        path = home / directory / 'telegram-approved.json'
        if path.is_symlink():
            problems.append('pairing state symlink requires review')
            continue
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
            if not isinstance(data, dict) or any(str(uid) != owner for uid in data):
                problems.append('pairing grants include a non-owner; existing state preserved')
        except (OSError, ValueError):
            problems.append('unreadable pairing state requires review')
    profiles = home / 'profiles'
    if profiles.exists() and (profiles.is_symlink() or any(profiles.iterdir())):
        problems.append('additional profiles require separate access review')
    return sorted(set(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--secret-file', type=Path, required=True)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
    except (OSError, ValueError):
        print('BLOCKED: generated JSON configuration is missing or invalid')
        return 2
    problems = validate(config, os.environ)
    problems += validate_pairing(args.config.parent, os.environ.get('TELEGRAM_ALLOWED_USERS', ''))
    try:
        st = args.secret_file.lstat()
        if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600 or st.st_uid != os.getuid():
            problems.append('secret file must be a regular owner-owned file with mode 0600')
    except OSError:
        problems.append('protected secret file is missing')
    for problem in problems:
        print('BLOCKED: ' + problem)
    return 2 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
