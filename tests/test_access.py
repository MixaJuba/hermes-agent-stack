"""Contract tests for credential-safe, read-only prerequisite diagnostics."""

import importlib.util
import io
import json
from pathlib import Path
import unittest
import urllib.error
import urllib.request

SPEC = importlib.util.spec_from_file_location(
    "check_access", Path(__file__).resolve().parents[1] / "scripts/check_access.py"
)
access = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(access)


class Response(io.BytesIO):
    status = 200


class AccessTests(unittest.TestCase):
    def test_missing_key_does_not_attempt_authenticated_catalog(self):
        calls = []

        def get(name, url, **kwargs):
            calls.append((url, kwargs))
            return {"name": name, "status": "reachable"}

        result = access.report(online=True, environ={}, fetcher=get)
        self.assertFalse(result["access_checks_passed"])
        self.assertNotIn(access.CATALOG_URL, [url for url, _ in calls])
        self.assertFalse(result["bot_ready"])

    def test_credentials_never_appear_in_report_even_if_access_passes(self):
        env = {name: "sensitive-example-value" for name in access.PRESENCE_NAMES}
        env["TELEGRAM_ALLOWED_USERS"] = "123456789"
        result = access.report(
            online=True, environ=env,
            fetcher=lambda name, url, **kwargs: {"name": name, "status": "reachable"},
        )
        self.assertTrue(result["access_checks_passed"])
        self.assertFalse(result["bot_ready"])
        self.assertNotIn("sensitive-example-value", json.dumps(result))
        self.assertNotIn("123456789", json.dumps(result))

    def test_foreign_owner_lists_and_allow_all_are_rejected(self):
        for owner in ("*", "123,456", "123 456", "0", "-123", "@owner"):
            with self.subTest(owner=owner):
                result = access.report(environ={"TELEGRAM_ALLOWED_USERS": owner})
                self.assertEqual(result["credential_presence"][-1]["status"],
                                 "missing_or_invalid")

    def test_network_policy_denial_is_not_model_unavailability(self):
        error = urllib.error.URLError("Tunnel connection failed: 403 Forbidden")
        self.assertEqual(access.error_status(error), "proxy_policy_denied")

    def test_api_errors_do_not_disclose_provider_body_or_key(self):
        class Client:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(
                    access.CATALOG_URL, 402, "secret-in-error", {},
                    io.BytesIO(b'secret-in-provider-body'),
                )

        result = access.fetch("catalog", access.CATALOG_URL,
                              api_key="secret-key", opener=Client())
        self.assertEqual(result["status"], "payment_required_stop")
        self.assertNotIn("secret", json.dumps(result))

    def test_catalog_is_get_only_and_credential_has_fixed_destination(self):
        requests = []

        class Client:
            def open(self, request, timeout):
                requests.append(request)
                return Response(b'{"data": [{"id": "deepseek-ai/deepseek-v4.1-flash"}]}')

        result = access.fetch("catalog", access.CATALOG_URL,
                              api_key="example", opener=Client())
        self.assertEqual(requests[0].get_method(), "GET")
        self.assertEqual(result["candidate_model_ids"],
                         ["deepseek-ai/deepseek-v4.1-flash"])
        with self.assertRaises(ValueError):
            access.fetch("other", access.PUBLIC_URLS["exa_pricing"], api_key="example")

    def test_authenticated_redirect_cannot_leak_credential(self):
        request = urllib.request.Request(access.CATALOG_URL,
                                         headers={"Authorization": "Bearer example"})
        with self.assertRaises(access.RedirectBlocked):
            access.SafeRedirect().redirect_request(
                request, None, 302, "Found", {}, "https://docs.nvidia.com/",
            )

    def test_public_redirect_never_downgrades_tls_or_uses_unknown_host(self):
        request = urllib.request.Request(access.PUBLIC_URLS["exa_pricing"])
        for url in ("http://exa.ai/", "https://unknown.invalid/", "https://exa.ai:8443/"):
            with self.subTest(url=url), self.assertRaises(access.RedirectBlocked):
                access.SafeRedirect().redirect_request(request, None, 302, "Found", {}, url)

    def test_html_or_invented_catalog_cannot_pass_as_model_listing(self):
        for body in (b"<html>login</html>", b'{"models": []}', b'{"data": [42]}'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                access.catalog_candidates(body)

    def test_offline_checks_never_make_network_requests(self):
        def network_must_not_run(*args, **kwargs):
            self.fail("offline diagnostics contacted a provider")

        result = access.report(environ={}, fetcher=network_must_not_run)
        self.assertEqual(result["network"], [])
        self.assertFalse(result["inference_requests_performed"])
        self.assertFalse(result["exa_search_requests_performed"])
        self.assertFalse(result["oracle_resources_created"])


if __name__ == "__main__":
    unittest.main()
