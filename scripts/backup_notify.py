"""One outbound Telegram sendMessage; no gateway, poller, inference or raw errors."""
import datetime as dt
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

import scheduled_backup as s


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def credentials(path):
    values={}
    for line in s.protected(path,operator=True).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        key,sep,value=line.partition('=')
        key=key.strip(); value=value.strip()
        if not sep or key not in ('TELEGRAM_BOT_TOKEN','TELEGRAM_ALLOWED_USERS') or key in values:
            raise ValueError('Only two existing Telegram credentials may be provided')
        if len(value)>=2 and value[0]==value[-1] and value[0] in ('"',"'"): value=value[1:-1]
        values[key]=value
    token=values.get('TELEGRAM_BOT_TOKEN',''); owner=values.get('TELEGRAM_ALLOWED_USERS','')
    if not re.fullmatch(r'[0-9]{5,15}:[A-Za-z0-9_-]{30,100}',token) or not re.fullmatch(r'[1-9][0-9]*',owner):
        raise ValueError('Exactly one owner and valid bot credential required')
    return token,owner


def send(path,text):
    token,owner=credentials(path)
    request=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',
        data=urllib.parse.urlencode({'chat_id':owner,'text':text,'disable_notification':'false'}).encode(),method='POST')
    opener=urllib.request.build_opener(NoRedirect())
    # Caller never emits URLs, token-bearing exceptions or provider bodies.
    with opener.open(request,timeout=10) as response:
        raw=response.read(16385)
        if response.status!=200 or len(raw)>16384: raise ValueError('Notification unavailable')
        payload=json.loads(raw)
        if payload.get('ok') is not True or str(payload.get('result',{}).get('chat',{}).get('id'))!=owner:
            raise ValueError('Owner delivery not confirmed')


def watch(policy_path,credential_path,state_dir,force=False,now=None):
    now=now or s.utcnow()
    directory=s.private_dir(state_dir)
    ref=None
    try:
        p,digest=s.load_policy(policy_path)
        if Path(p['state_dir'])!=directory: raise ValueError('Unreviewed state path')
        issue=s.health(p,digest,directory,now,force=force)
        if p['owner_receipt_delivery_confirmed'] is True:
            ref=s.read_state(directory,digest)['latest']
    except (ValueError,TypeError,KeyError,OSError): issue='configuration'
    with s.lock(directory,'.notify.lock'):
        path=directory/'notify.json'
        n=json.loads(s.protected(path).read_text()) if path.exists() else {'day':None,'attempts':0,'last_attempt':None,'delivered':None}
        if (not isinstance(n,dict) or type(n.get('attempts')) is not int or n['attempts']<0
                or not {'day','last_attempt','delivered'}<=set(n)):
            raise ValueError('Notification state corrupt; operator review required')
        # A successful heartbeat once a UTC day is the owner's dead-man signal.
        event=issue+':'+now.date().isoformat()+(':'+ref['sha256'] if ref else '')
        if n.get('day')!=now.date().isoformat(): n.update(day=now.date().isoformat(),attempts=0)
        if n.get('delivered')==event: return
        if n.get('last_attempt') and now-s.timestamp(n['last_attempt'])<dt.timedelta(hours=1): return
        if type(n.get('attempts')) is not int or n['attempts']>=3: return
        n.update(attempts=n['attempts']+1,last_attempt=now.isoformat(),pending=event)
        s.atomic(path,n)  # reserve before send; lost acknowledgement is not blindly retried
        messages={
            'healthy':'Остання підтверджена копія не старша 36 годин, контроль пройдено. Це не новий тест відновлення.',
            'failed':'Спроба резервування завершилася помилкою.',
            'stale':'Немає підтвердженої свіжої копії понад 36 годин.',
            'interrupted':'Спроба резервування не завершилася вчасно.',
            'renewal':'Потрібна нова перевірка квот і дозволеного періоду резервування.',
            'clock':'Час сервера не узгоджується зі станом резервування.',
            'configuration':'Конфігурація регулярного резервування недоступна або некоректна.',
            'review':'Дозвіл або захищений стан резервування потребує перевірки.'}
        text='Резервування Hermes: '+messages[issue]
        if issue!='healthy': text+=' Останні копії не видаляти. Потрібен Локальний Codex.'
        if ref:
            text+='\nПриватний recovery record останньої підтвердженої копії:\n'
            text+='\n'.join(key+': '+str(ref[key]) for key in ('object','sha256','bytes','verified_at'))
            text+='\nЗбережи разом із позасерверним записом сховища. Приватний ключ тут не передається.'
        try: send(credential_path,text)
        except Exception:
            raise RuntimeError('Owner notification pending; private details withheld') from None
        n.update(delivered=event,pending=None)
        s.atomic(path,n)
