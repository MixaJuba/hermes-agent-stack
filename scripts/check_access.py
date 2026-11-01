#!/usr/bin/env python3
"""Read-only stage-one diagnostics. No inference, search, or cloud provisioning.

Uses only Python's standard library, inherited proxy configuration and verified
TLS. Output contains presence flags and safe classifications, never key values,
response bodies, exception text or authentication headers. Exit 0 means access
checks passed, not that the bot or the free-tier account quotas were verified.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import re
import shutil
import ssl
import urllib.error
import urllib.parse
import urllib.request


PUBLIC_URLS = {
    "nvidia_catalog_page": "https://build.nvidia.com/models",
    "nvidia_api_docs": "https://docs.api.nvidia.com/nim/docs/api-quickstart",
    "exa_pricing": "https://exa.ai/pricing",
    "exa_rate_limits": "https://docs.exa.ai/reference/rate-limits",
    "oracle_always_free_docs": (
        "https://docs.oracle.com/en-us/iaas/Content/FreeTier/"
        "freetier_topic-Always_Free_Resources.htm"
    ),
}
CATALOG_URL = "https://integrate.api.nvidia.com/v1/models"
PUBLIC_HOSTS = frozenset({
    "build.nvidia.com", "docs.api.nvidia.com", "docs.nvidia.com",
    "exa.ai", "www.exa.ai", "exa.com", "www.exa.com", "docs.exa.ai",
    "docs.oracle.com", "www.oracle.com",
})
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
PRESENCE_NAMES = ("NVIDIA_API_KEY", "EXA_API_KEY", "TELEGRAM_BOT_TOKEN")


class RedirectBlocked(Exception):
    pass


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        # Never forward an API credential through a redirect, even same-host.
        if req.has_header("Authorization"):
            raise RedirectBlocked()
        if (target.scheme != "https" or target.hostname not in PUBLIC_HOSTS
                or target.username is not None or target.password is not None
                or target.port not in (None, 443)):
            raise RedirectBlocked()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def error_status(error):
    """Do not return exceptions: transport errors may embed credentials."""
    if isinstance(error, RedirectBlocked):
        return "redirect_blocked"
    if isinstance(error, urllib.error.HTTPError):
        return {
            401: "authentication_required_or_rejected",
            402: "payment_required_stop",
            403: "provider_access_denied",
            429: "rate_limited",
        }.get(error.code, f"http_{error.code}")
    if isinstance(error, (ssl.SSLError, ssl.CertificateError)):
        return "tls_verification_failed"
    if isinstance(error, (TimeoutError,)):
        return "timeout"
    if isinstance(error, urllib.error.URLError):
        reason = str(error.reason).lower()
        if "tunnel connection failed: 403" in reason:
            return "proxy_policy_denied"
        if isinstance(error.reason, (ssl.SSLError, ssl.CertificateError)):
            return "tls_verification_failed"
        if isinstance(error.reason, TimeoutError):
            return "timeout"
    return "transport_unavailable"


def catalog_candidates(body):
    data = json.loads(body)
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ValueError("invalid catalog structure")
    models = data["data"]
    if any(not isinstance(item, dict) or not isinstance(item.get("id"), str)
           for item in models):
        raise ValueError("invalid model entry")
    # Candidate names are not a selected model and not a tool-use compatibility
    # claim. Restrict printable identifiers to avoid including arbitrary text.
    ids = []
    for item in models:
        model_id = item["id"]
        normalized = re.sub(r"[^a-z0-9]", "", model_id.lower())
        if ("deepseekv41flash" in normalized
                and re.fullmatch(r"[A-Za-z0-9_./:@+-]{1,200}", model_id)):
            ids.append(model_id)
    return sorted(set(ids))


def fetch(name, url, *, api_key=None, opener=None):
    if api_key is not None and url != CATALOG_URL:
        raise ValueError("credentials restricted to official NVIDIA catalog")
    if url not in (*PUBLIC_URLS.values(), CATALOG_URL):
        raise ValueError("only fixed read-only destinations are supported")
    headers = {"User-Agent": "hermes-agent-stack-access-check/1"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    try:
        client = opener or urllib.request.build_opener(
            urllib.request.ProxyHandler(), SafeRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        request = urllib.request.Request(url, headers=headers, method="GET")
        with client.open(request, timeout=15) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            status = response.status
        if len(body) > MAX_RESPONSE_BYTES:
            return {"name": name, "status": "response_too_large"}
        if not 200 <= status < 300:
            return {"name": name, "status": f"http_{status}"}
        result = {"name": name, "status": "reachable", "http_status": status}
        if url == CATALOG_URL:
            try:
                result["candidate_model_ids"] = catalog_candidates(body)
            except (ValueError, UnicodeError):
                result["status"] = "invalid_catalog_response"
        return result
    except Exception as error:
        return {"name": name, "status": error_status(error)}


def report(*, online=False, environ=None, fetcher=None):
    env = os.environ if environ is None else environ
    checks = [
        {"name": name, "status": "present" if env.get(name) else "missing"}
        for name in PRESENCE_NAMES
    ]
    owner = env.get("TELEGRAM_ALLOWED_USERS", "")
    # One numeric owner, never an allow-all wildcard or a list of other users.
    valid_owner = bool(re.fullmatch(r"[1-9][0-9]*", owner))
    checks.append({"name": "single_numeric_telegram_owner",
                   "status": "present" if valid_owner else "missing_or_invalid"})
    network = []
    if online:
        get = fetch if fetcher is None else fetcher
        with ThreadPoolExecutor(max_workers=5) as pool:
            network = list(pool.map(lambda item: get(*item), PUBLIC_URLS.items()))
        key = env.get("NVIDIA_API_KEY")
        if key:
            network.append(get("nvidia_model_catalog", CATALOG_URL, api_key=key))
        else:
            network.append({"name": "nvidia_model_catalog",
                            "status": "skipped_missing_key"})
    complete = online and all(c["status"] == "present" for c in checks)
    complete = complete and all(n["status"] == "reachable" for n in network)
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "read_only_access_diagnostics",
        "access_checks_passed": complete,
        "bot_ready": False,
        "hermes_executable_present": shutil.which("hermes") is not None,
        "credential_presence": checks,
        "network": network,
        "inference_requests_performed": False,
        "exa_search_requests_performed": False,
        "oracle_resources_created": False,
        "still_unverified": [
            "NVIDIA account free eligibility, quota, expiry and prototype terms",
            "Exact model ID and full installed-Hermes tool-call round trip",
            "Full Hermes prompt/tool schema size versus provider request limits",
            "Exa account free quota, permitted operations and billing disabled",
            "Oracle account Always Free quotas, shape availability and access",
            "Telegram owner identity, text, memory, tools and web end-to-end",
            "Restart recovery, quota handling and backup restoration",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true",
                        help="GET official public docs and NVIDIA catalog if a key exists")
    args = parser.parse_args()
    result = report(online=args.online)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["access_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
