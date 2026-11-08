import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest


PLUGIN = Path(__file__).resolve().parents[1] / "deploy/plugins/bro-recent-web/__init__.py"
SPEC = importlib.util.spec_from_file_location("bro_recent_web", PLUGIN)
recent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recent)
NOW = datetime(2026, 11, 8, 0, 15, tzinfo=timezone.utc)
BASE = "https://mrckyiv.dsns.gov.ua/news/ostanni-novini"


def hit(slug, stamp, host_url=BASE):
    return SimpleNamespace(title=slug, url=f"{host_url}/{slug}", text=f"### {slug}\n\n{stamp}\n\nСтаття.")


class RecentSearchTests(unittest.TestCase):
    def test_filters_and_orders_source_dates_and_direct_urls(self):
        recent_hit = hit("newest", "07.11.2026 21:40")
        duplicate = SimpleNamespace(**vars(recent_hit))
        duplicate.url += "#duplicate"
        listing = hit("ostanni-novini", "07.11.2026 23:00", "https://dsns.gov.ua/news")
        spoof = hit("spoof", "07.11.2026 23:00", "https://dsns.gov.ua.example.com/news/ostanni-novini")
        unknown = hit("event-date", "Подія сталася 07.11.2026 14:00")
        unknown.published_date = "2026-11-07T12:00:00Z"
        rows = [
            hit("older", "17.07.2026 17:15"), hit("boundary", "06.11.2026 02:15"),
            hit("outside", "06.11.2026 02:14"), hit("future", "08.11.2026 02:16"),
            duplicate, recent_hit, listing, spoof, unknown,
        ]
        seen = []

        def search(query, start, end, domains, candidates):
            seen.append((query, start, end, domains, candidates))
            return rows

        result = recent.search_recent("новини ДСНС", 48, ["DSNS.GOV.UA"], now=NOW, search=search)
        self.assertEqual(seen, [("новини ДСНС", NOW - timedelta(hours=48), NOW, ["dsns.gov.ua"], 8)])
        self.assertEqual(result["window"]["start"], "2026-11-06T02:15:00+02:00")
        self.assertEqual(result["window"]["end"], "2026-11-08T02:15:00+02:00")
        self.assertEqual([row["url"] for row in result["results"]], [recent_hit.url, BASE + "/boundary"])

    def test_real_elapsed_window_over_dst(self):
        now = datetime(2026, 10, 25, 5, tzinfo=timezone.utc)
        result = recent.search_recent("test", 6, now=now, search=lambda *_: [])
        self.assertEqual(result["window"]["start"], "2026-10-25T02:00:00+03:00")
        self.assertEqual(result["window"]["end"], "2026-10-25T07:00:00+02:00")
        ambiguous = hit("ambiguous", "25.10.2026 03:30")
        self.assertEqual(recent.search_recent("test", 6, now=now, search=lambda *_: [ambiguous])["results"], [])

    def test_finds_article_without_index_date_using_one_bounded_retry(self):
        calls = []

        def search(query, start, end, domains, limit):
            calls.append((query, start, end, domains, limit))
            return [] if start is not None else [
                hit("actual", "07.11.2026 18:25"),
                hit("stale", "17.07.2026 17:15"),
                hit("page", "07.11.2026 23:00", BASE + "/archive"),
            ]

        result = recent.search_recent("ДСНС", 48, ["dsns.gov.ua"], now=NOW, search=search)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1:], (None, None, ["dsns.gov.ua"], 8))
        self.assertIn("2026-11-06", calls[1][0])
        self.assertEqual([r["title"] for r in result["results"]], ["actual"])

    def test_explicit_offset_date_on_other_official_sites(self):
        result = recent.search_recent("test", 48, ["example.gov"], now=NOW, search=lambda *_: [
            SimpleNamespace(title="Update", url="https://example.gov/news/update",
                            text="Update\nPublished: 2026-11-07T15:00:00Z\nBody"),
            SimpleNamespace(title="Other", url="https://example.gov/news/other",
                            text="Other\nUpdated: 2026-11-07T15:00:00Z\nBody"),
        ])
        self.assertEqual([r["title"] for r in result["results"]], ["Update"])

    def test_invalid_args_and_provider_failure(self):
        def should_not_search(*_):
            self.fail("invalid input reached Exa")

        for args in [("x", 0, None), ("x", True, None), ("", 48, None), ("x", 48, ["https://dsns.gov.ua"])]:
            self.assertFalse(recent.search_recent(*args, search=should_not_search)["success"])

        def failing_search(*_):
            raise RuntimeError("sensitive upstream error")

        result = recent.search_recent("valid", 48, now=NOW, search=failing_search)
        self.assertFalse(result["success"])
        self.assertNotIn("sensitive", json.dumps(result))

    def test_registers_web_tool_without_overriding_native_tools(self):
        registered = {}
        recent.register(SimpleNamespace(register_tool=lambda **kw: registered.update(kw)))
        self.assertEqual(registered["name"], "web_search_recent")
        self.assertEqual(registered["toolset"], "web")
        self.assertFalse(registered.get("override", False))
        self.assertFalse(json.loads(registered["handler"]({}))["success"])


if __name__ == "__main__":
    unittest.main()
