"""Date-bounded Exa search for the pinned Hermes runtime."""
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo


TOOL_NAME = "web_search_recent"
KYIV = ZoneInfo("Europe/Kyiv")
HOSTNAME = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}")
DSNS_SECTIONS = {"ostanni-novini", "nadzvicaini-podiyi", "ostanni-podiyi"}
COLLECTIONS = DSNS_SECTIONS | {"news", "press", "blog", "articles", "posts", "archive"}
LOCAL_STAMP = re.compile(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})(?=\s|$)")
LABELED_STAMP = re.compile(
    r"^\s*(?:published(?: on)?|date published|дата публікації|опубліковано)\s*:?\s*"
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2}))\s*$",
    re.IGNORECASE | re.MULTILINE,
)

SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Find dated articles via Exa for the preceding N hours, ending now in Kyiv. "
        "Returns direct article URLs, source publication timestamps and page excerpts. "
        "An empty result means there is insufficient verified evidence, not no publications."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic in natural language, without site: operators."},
            "hours": {"type": "integer", "minimum": 1, "maximum": 720},
            "domains": {
                "type": "array", "minItems": 1, "maxItems": 4,
                "items": {"type": "string"},
                "description": "Bare official hostnames. A domain also permits its subdomains.",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "required": ["query", "hours"],
        "additionalProperties": False,
    },
}


def _page_publication(text, title, dsns):
    """Require an article-header timestamp, not a date mentioned in the story."""
    header = text[:1200]
    if dsns:
        # Exa plain text preserves the DSNS headline and its local publication time.
        for line in re.finditer(r"^.*$", header, re.MULTILINE):
            if " ".join(line.group().strip(" #\t").split()) != " ".join(title.split()):
                continue
            tail = header[line.end():].lstrip()
            match = LOCAL_STAMP.match(tail)
            if match:
                local = datetime.strptime(" ".join(match.groups()), "%d.%m.%Y %H:%M").replace(tzinfo=KYIV)
                return local if local.utcoffset() == local.replace(fold=1).utcoffset() else None
    match = LABELED_STAMP.search(header)
    return datetime.fromisoformat(match.group(1)) if match else None


def _article_url(url, domains):
    parts = urlsplit(url)
    host = parts.hostname or ""
    path = parts.path.rstrip("/")
    segments = path.strip("/").split("/")
    dsns = host == "dsns.gov.ua" or host.endswith(".dsns.gov.ua")
    if (parts.scheme != "https" or not HOSTNAME.fullmatch(host)
            or parts.username or parts.password or parts.port is not None
            or not path or segments[-1].casefold() in COLLECTIONS
            or (domains and not any(host == domain or host.endswith("." + domain) for domain in domains))
            or (dsns and (len(segments) < 2 or segments[-2] not in DSNS_SECTIONS
                         or not any(c.isalpha() for c in segments[-1])))):
        return None, False
    return urlunsplit(("https", host, parts.path, parts.query, "")), dsns


def _exa_search(query, start, end, domains, candidates):
    # Reuse the pinned Hermes keyed Exa client; there is no anonymous rescue.
    from plugins.web.exa.provider import _get_exa_client
    from tools.web_tools import _get_search_backend

    if _get_search_backend() != "exa":
        raise RuntimeError("Exa is not selected")
    options = {"include_domains": [entry for domain in domains for entry in (domain, "*." + domain)]} if domains else {}
    if start is not None:
        options.update(start_published_date=start.isoformat(), end_published_date=end.isoformat())
    return _get_exa_client().search(
        query,
        num_results=candidates,
        contents={"text": {"max_characters": 3000}},
        **options,
    ).results


def _verified_articles(rows, domains, start, end):
    articles = {}
    for row in rows or []:
        text = getattr(row, "text", "") or ""
        title = (getattr(row, "title", "") or "").strip()
        try:
            url, dsns = _article_url(getattr(row, "url", "") or "", domains)
            published = _page_publication(text, title, dsns) if url and title else None
        except ValueError:
            continue
        if published is not None and start <= published.astimezone(timezone.utc) <= end:
            articles.setdefault(url, (published, title, text))
    return articles


def search_recent(query, hours, domains=None, limit=2, *, now=None, search=_exa_search):
    if (not isinstance(query, str) or not query.strip() or len(query) > 500
            or type(hours) is not int or not 1 <= hours <= 720
            or type(limit) is not int or not 1 <= limit <= 5
            or (domains is not None and (
                not isinstance(domains, list) or not 1 <= len(domains) <= 4
                or any(not isinstance(d, str) or not HOSTNAME.fullmatch(d.lower()) for d in domains)
            ))):
        return {"success": False, "error": "Некоректний запит, період, домен або ліміт."}
    domains = list(dict.fromkeys(d.lower() for d in domains or []))
    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    start = end - timedelta(hours=hours)
    window = {
        "start": start.astimezone(KYIV).isoformat(timespec="seconds"),
        "end": end.astimezone(KYIV).isoformat(timespec="seconds"),
        "timezone": KYIV.key,
    }
    candidates = min(10, limit * 4)
    try:
        rows = search(query.strip(), start, end, domains, candidates)
    except Exception:
        return {"success": False, "window": window, "error": "Не вдалося отримати результат Exa."}

    articles = _verified_articles(rows, domains, start, end)
    coverage = "Лише статті, дати яких підтвердив доступний текст сторінки."
    if len(articles) < limit and domains:
        # Some official pages expose a timestamp in the text but not in Exa's index.
        dated_query = f"{query.strip()} Опубліковано {window['start'][:10]} — {window['end'][:10]}."
        try:
            extra = search(dated_query, None, None, domains, candidates)
        except Exception:
            coverage += " Додатковий пошук Exa недоступний."
        else:
            for url, evidence in _verified_articles(extra, domains, start, end).items():
                articles.setdefault(url, evidence)

    matches = sorted(articles.items(), key=lambda item: item[1][0].timestamp(), reverse=True)[:limit]
    return {
        "success": True,
        "provider": "exa",
        "window": window,
        "results": [
            {
                "url": url,
                "title": title,
                "published_at": published.astimezone(KYIV).isoformat(),
                "excerpt": text[:750],
            }
            for url, (published, title, text) in matches
        ],
        "coverage": coverage,
    }


def register(ctx):
    def handle(args, **_kwargs):
        return json.dumps(search_recent(
            args.get("query"), args.get("hours"), args.get("domains"), args.get("limit", 2),
        ), ensure_ascii=False)

    ctx.register_tool(
        name=TOOL_NAME, toolset="web", schema=SCHEMA, handler=handle,
        requires_env=["EXA_API_KEY"], description=SCHEMA["description"],
    )
