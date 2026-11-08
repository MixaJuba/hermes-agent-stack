#!/usr/bin/env python3
"""Fail-closed startup checks. Never prints credentials or starts the gateway."""
import argparse
import json
import os
from pathlib import Path
import re
import stat

PROVIDER = 'workers-ai'
MODEL = '@cf/zai-org/glm-4.7-flash'
BASE_PLUGINS = ['cloudflare-workers-ai-provider']
BRO_PLUGIN = 'bro-recent-web'
AUX_TASKS = ('vision', 'compression', 'skills_hub', 'approval', 'review', 'mcp',
             'title_generation', 'memory_query_rewrite', 'tts_audio_tags', 'voice_chat',
             'triage_specifier', 'kanban_decomposer', 'profile_describer', 'goal_judge',
             'curator', 'monitor', 'background_review')


def cloudflare_base_url_valid(value):
    return isinstance(value, str) and re.fullmatch(
        r'https://api\.cloudflare\.com/client/v4/accounts/[0-9a-f]{32}/ai/v1/?', value) is not None


def validate(config, env):
    problems = []
    owner = env.get('TELEGRAM_ALLOWED_USERS', '')
    if not re.fullmatch(r'[1-9][0-9]*', owner):
        problems.append('exactly one confirmed numeric owner ID is required')
    for name in ('CLOUDFLARE_WORKERS_AI_API_TOKEN', 'CLOUDFLARE_WORKERS_AI_BASE_URL', 'EXA_API_KEY', 'TELEGRAM_BOT_TOKEN'):
        if not env.get(name):
            problems.append(name + ' is missing')
    if not cloudflare_base_url_valid(env.get('CLOUDFLARE_WORKERS_AI_BASE_URL')):
        problems.append('protected Cloudflare base URL must be the account OpenAI-compatible HTTPS endpoint')
    # A global/group grant or explicit allow-all must not override the one owner.
    for name in ('GATEWAY_ALLOWED_USERS', 'TELEGRAM_GROUP_ALLOWED_USERS', 'TELEGRAM_GROUP_ALLOWED_CHATS',
                 'TELEGRAM_ALLOWED_GROUPS', 'TELEGRAM_GROUP_ALLOW_FROM'):
        if env.get(name):
            problems.append('additional global/group access is forbidden')
    for name in ('GATEWAY_ALLOW_ALL_USERS', 'TELEGRAM_ALLOW_ALL_USERS'):
        if env.get(name, '').lower() not in ('', 'false', '0', 'no'):
            problems.append('allow-all access is forbidden')
    model = config.get('model', {})
    if (model.get('provider') != PROVIDER or model.get('default') != MODEL
            or set(model) - {'provider', 'default', 'streaming'}
            or config.get('fallback_model') != [] or config.get('fallback_providers') != []
            or config.get('custom_providers') or config.get('providers')):
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
    if auxiliary.get('transient_retries') != 0 or auxiliary.get('free_only') is not True:
        problems.append('auxiliary retries/free-only policy changed')
    if set(auxiliary) - set(AUX_TASKS) - {'transient_retries', 'free_only'}:
        problems.append('unreviewed auxiliary configuration')
    for task in AUX_TASKS:
        route = auxiliary.get(task, {})
        if (route.get('provider') != PROVIDER or route.get('model') != MODEL
                or route.get('fallback_chain') != [] or set(route) - {
                    'provider', 'model', 'fallback_chain', 'enabled', 'model_upgrade_enabled', 'prefer_fast_model'}):
            problems.append('auxiliary routes must use the qualified Cloudflare model without overrides/fallback')
    if (auxiliary.get('title_generation', {}).get('enabled') is not False
            or auxiliary.get('title_generation', {}).get('model_upgrade_enabled') is not False
            or auxiliary.get('title_generation', {}).get('prefer_fast_model') is not False
            or auxiliary.get('background_review', {}).get('enabled') is not False
            or config.get('curator', {}).get('enabled') is not False):
        problems.append('background/title/curator inference must remain disabled')
    plugin_config = config.get('plugins', {})
    enabled = plugin_config.get('enabled')
    if (enabled not in (BASE_PLUGINS, [*BASE_PLUGINS, BRO_PLUGIN])
            or plugin_config.get('auto_apply') is not False or plugin_config.get('auto_update_check_hours') != 0):
        problems.append('unreviewed plugin selection or automatic plugin changes')
    if enabled == [*BASE_PLUGINS, BRO_PLUGIN] and config.get('timezone') != 'Europe/Kyiv':
        problems.append('Bro search requires the Europe/Kyiv profile clock')
    if enabled == [*BASE_PLUGINS, BRO_PLUGIN] and config.get('tools', {}).get('tool_search', {}).get('enabled') != 'off':
        problems.append('Bro search must be exposed directly in the selected web toolset')
    telegram = config.get('platforms', {}).get('telegram', {})
    if (telegram.get('dm_policy') != 'allowlist' or telegram.get('group_policy') != 'disabled'
            or telegram.get('guest_mode') is not False or telegram.get('allowed_chats') != [owner]):
        problems.append('Telegram must be restricted to the confirmed owner DM')
    if telegram.get('extra') or any(telegram.get(k) for k in ('allow_from', 'allow_admin_from', 'group_allow_from')):
        problems.append('additional Telegram policy overrides require review')
    return sorted(set(problems))


def validate_bro_plugin(config, home):
    if config.get('plugins', {}).get('enabled') != [*BASE_PLUGINS, BRO_PLUGIN]:
        return []
    expected = Path(__file__).resolve().parent / 'plugins' / BRO_PLUGIN
    installed = home / 'plugins' / BRO_PLUGIN
    files = {'__init__.py', 'plugin.yaml'}
    try:
        if (installed.is_symlink() or installed.parent.is_symlink()
                or {p.name for p in installed.iterdir()} != files
                or any((installed / name).is_symlink() or not (installed / name).is_file()
                       or (installed / name).read_bytes() != (expected / name).read_bytes()
                       for name in files)):
            return ['Bro search plugin differs from the reviewed package']
    except OSError:
        return ['Bro search plugin is missing or unreadable']
    return []


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
    from cloudflare_plugin import attest as attest_cloudflare
    problems += attest_cloudflare(args.config.parent)
    problems += validate_bro_plugin(config, args.config.parent)
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
