"""Synthetic-only native plugin probe. No secret access, transforms or network."""
import json


def record(kind, turn_id=None, reason=None, status_code=None, **kwargs):
    from hermes_constants import get_hermes_home
    home = get_hermes_home()
    assert home.parent.name.startswith('hermes-ua-quota-')
    with (home / 'probe-events.jsonl').open('a') as out:
        out.write(json.dumps(dict(kind=kind, turn_id=turn_id, reason=reason,
                                  status_code=status_code)) + '\n')


def register(ctx):
    ctx.register_hook('api_request_error', lambda **kw: record('error', **kw))
    ctx.register_hook('transform_llm_output', lambda **kw: record('output', **kw))
