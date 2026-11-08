"""Bounded owner reminders on the native Hermes scheduler."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import stat
from threading import Lock
import time
import unicodedata
from uuid import uuid4


TOOL = 'bro_remind_once'
SEND_TOOL = 'bro_send_documents'
OUT = 'sandboxes/docker/default/workspace/out'
FILE_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,80}\.(?:pdf|docx|xlsx|csv|pptx)')
FILE_MAX_BYTES = 8 * 1024 * 1024
JOB = 'Bro one-shot reminder'
CREATE_LOCK = Lock()
SCHEMA = {
    'name': TOOL,
    'description': ('Schedule one plain-text Telegram reminder to the current owner DM. '
                    'Requires an explicit request. No recurring reminders.'),
    'parameters': {
        'type': 'object',
        'properties': {
            'minutes': {'type': 'integer', 'minimum': 1, 'maximum': 10080},
            'message': {'type': 'string', 'maxLength': 240},
        },
        'required': ['minutes', 'message'],
        'additionalProperties': False,
    },
}
SEND_SCHEMA = {
    'name': SEND_TOOL,
    'description': ('Send up to three freshly generated document files from /workspace/out '
                    'to the current Telegram owner DM. Supply only filenames.'),
    'parameters': {
        'type': 'object',
        'properties': {
            'files': {'type': 'array', 'minItems': 1, 'maxItems': 3, 'uniqueItems': True,
                      'items': {'type': 'string'}},
        },
        'required': ['files'],
        'additionalProperties': False,
    },
}


def _telegram_owner():
    from gateway.session_context import get_session_env

    owner = os.environ.get('TELEGRAM_ALLOWED_USERS', '')
    if (not re.fullmatch(r'[1-9][0-9]*', owner)
            or get_session_env('HERMES_SESSION_PLATFORM') != 'telegram'
            or get_session_env('HERMES_SESSION_CHAT_TYPE') not in ('dm', 'private')
            or get_session_env('HERMES_SESSION_CHAT_ID') != owner
            or get_session_env('HERMES_SESSION_USER_ID') != owner):
        return None
    return owner


def schedule_once(minutes, message):
    from cron.jobs import create_job, list_jobs
    from hermes_constants import get_hermes_home

    owner = _telegram_owner()
    if owner is None:
        return {'success': False, 'error': 'Нагадування доступні лише власнику в особистому чаті.'}
    if (type(minutes) is not int or not 1 <= minutes <= 10080
            or not isinstance(message, str) or not 1 <= len(message.strip()) <= 240
            or any(unicodedata.category(char).startswith('C') for char in message)
            or re.search(r'media\s*:', message, re.I)):
        return {'success': False, 'error': 'Потрібен один рядок тексту і затримка від 1 хвилини до 7 діб.'}

    with CREATE_LOCK:
        if any(job.get('name') == JOB for job in list_jobs()):
            return {'success': False, 'error': 'Вже є одне заплановане нагадування.'}
        scripts = Path(get_hermes_home()) / 'scripts'
        scripts.mkdir(mode=0o700, exist_ok=True)
        if scripts.is_symlink() or scripts.stat().st_uid != os.getuid() or scripts.stat().st_mode & 0o022:
            return {'success': False, 'error': 'Не вдалося безпечно підготувати нагадування.'}
        name = f'bro-once-{uuid4().hex}.py'
        path = scripts / name
        body = ('from pathlib import Path\n'
                'Path(__file__).unlink()\n'
                f'print({("🔔 Нагадування: " + message.strip())!r})\n')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(body)
            when = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            create_job(prompt=None, schedule=when.isoformat(), name=JOB, repeat=1,
                       deliver=f'telegram:{owner}', script=name, no_agent=True)
        except Exception:
            # A failed persistence operation may have committed the job before raising.
            if not any(job.get('script') == name for job in list_jobs(include_disabled=True)):
                path.unlink(missing_ok=True)
            return {'success': False, 'error': 'Планувальник не підтвердив створення. Перевірте перед повтором.'}
    return {'success': True, 'scheduled_at': when.isoformat(), 'repeat': 1}


def send_documents(files):
    from hermes_constants import get_hermes_home
    from tools.send_message_tool import send_message_tool

    owner = _telegram_owner()
    if owner is None:
        return {'success': False, 'error': 'Доставка доступна лише власнику в особистому чаті.'}
    if (not isinstance(files, list) or not 1 <= len(files) <= 3
            or any(not isinstance(n, str) or not FILE_NAME.fullmatch(n) for n in files)
            or len(set(files)) != len(files)):
        return {'success': False, 'error': 'Потрібні від одного до трьох різних імен документів із /workspace/out.'}
    root = Path(get_hermes_home()) / OUT
    paths = [root / name for name in files]
    try:
        if root.resolve(strict=True) != root or root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
            raise ValueError('untrusted output directory')
        for path in paths:
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                    or not 0 < info.st_size <= FILE_MAX_BYTES or not 0 <= time.time() - info.st_mtime <= 600):
                raise ValueError('untrusted document')
    except (OSError, ValueError, RuntimeError):
        return {'success': False, 'error': 'Доступні лише щойно створені файли в /workspace/out, до 8 МіБ кожен.'}

    delivered = []
    for path in paths:
        try:
            result = json.loads(send_message_tool({
                'action': 'send', 'target': f'telegram:{owner}', 'message': f'MEDIA:{path}',
            }))
        except Exception:
            result = {}
        if not isinstance(result, dict) or not result.get('success') or result.get('media_dropped'):
            return {'success': False, 'delivered': delivered,
                    'error': 'Telegram не підтвердив усі вкладення. Повтор автоматично не виконується.'}
        delivered.append(path.name)
    return {'success': True, 'delivered': delivered}


def register(ctx):
    def handle(args, **_kwargs):
        return json.dumps(schedule_once(args.get('minutes'), args.get('message')), ensure_ascii=False)

    ctx.register_tool(name=TOOL, toolset='bro-capabilities', schema=SCHEMA, handler=handle,
                      description=SCHEMA['description'])
    ctx.register_tool(name=SEND_TOOL, toolset='bro-capabilities', schema=SEND_SCHEMA,
                      handler=lambda args, **_kw: json.dumps(send_documents(args.get('files')), ensure_ascii=False),
                      description=SEND_SCHEMA['description'])
