import asyncio
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_hub.quota import UsageError, _read_codex, codex_windows, fetch_deepseek, run_one


class QuotaTests(unittest.TestCase):
    def test_deepseek_currency_balance_with_pinned_account(self):
        import httpx
        key = 'synthetic-fixture-key'
        profile = dict(provider='deepseek',pool='api',account='demo',key_sha256=hashlib.sha256(key.encode()).hexdigest())
        urls = []

        def handler(request):
            urls.append(str(request.url))
            raw = b'{"balance_infos":[{"currency":"CNY","total_balance":"12.50"}]}'
            return httpx.Response(200, stream=httpx.ByteStream(raw))

        with patch.dict(os.environ, MYLIB_HUB_DEEPSEEK_KEY=key):
            transport = httpx.MockTransport(handler)
            result = fetch_deepseek(profile, {'account':'demo'}, self.now, transport=transport)
            self.assertEqual(result['windows'], [dict(period='balance',unit='CNY',remaining=12.5,reset_at=None)])
            with self.assertRaises(UsageError):
                fetch_deepseek(profile, {'account':'other'}, self.now, transport=transport)
            self.assertEqual(urls, ['https://api.deepseek.com/user/balance'])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.snapshot_file = Path(self.directory.name) / "usage.json"
        self.profile = dict(project="project-a", account="seat-1", pool="included", provider="claude",
                            worker="worker-a", source="operator_usage_export", snapshot_file=str(self.snapshot_file))
        self.job = dict(project="project-a", account="seat-1", worker="worker-a", job_id=7,
                        accepted_at="2026-11-21T12:00:00Z", lease_token="test-lease")
        self.now = datetime(2026, 11, 21, 12, 2, tzinfo=timezone.utc)
        self.export = {"provider": "claude", "account": "seat-1", "pool": "included",
                       "observed_at": "2026-11-21T20:01:00+08:00", "windows": [
                           {"period": "weekly", "remaining": 40, "unit": "percent", "reset_at": "2026-11-23T04:00:00+08:00"},
                           {"period": "short", "remaining": None, "unit": "percent", "reset_at": None}]}
        self.recorded = []

    def call(self, method, params):
        if method == "claim_usage_job":
            self.assertEqual(params, {"project": "project-a", "account": "seat-1", "worker": "worker-a"})
            return self.job
        self.assertEqual(method, "record_usage_snapshot")
        self.assertEqual(params["project"], "project-a")
        self.assertEqual(params["account"], "seat-1")
        self.recorded.append(params["snapshot"])
        return {"job_id": 7, "status": params["snapshot"]["status"]}

    def run_export(self):
        self.snapshot_file.write_text(json.dumps(self.export), encoding="utf-8")
        return run_one(self.profile, self.call, now=lambda: self.now)

    def test_official_view_exports_retain_account_unit_reset_and_timestamp(self):
        for provider in ["claude", "grok"]:
            self.profile["provider"] = self.export["provider"] = provider
            self.export["extra"] = "synthetic-private-metadata"
            self.assertEqual(self.run_export()["status"], "ok")
            result = self.recorded[-1]
            self.assertEqual((result["job_id"], result["lease_token"]), (7, "test-lease"))
            self.assertEqual(result["observed_at"], "2026-11-21T12:01:00Z")
            self.assertEqual(result["windows"][0]["reset_at"], "2026-11-22T20:00:00Z")
            self.assertEqual(result["windows"][0]["remaining"], 40)
            self.assertIsNone(result["windows"][1]["remaining"])
            self.assertNotIn("synthetic-private-metadata", json.dumps(result))

    def test_old_exports_and_foreign_login_and_unknown_source(self):
        self.export["observed_at"] = "2026-11-21T11:59:59Z"
        self.assertEqual(self.run_export()["status"], "unavailable")
        self.export["account"] = "other-seat"
        self.assertEqual(self.run_export()["status"], "auth_required")
        self.profile["source"] = "unknown_source"
        self.assertEqual(self.run_export()["status"], "unsupported")

    def test_bad_resets_and_fraction_validation(self):
        for changes in ({"remaining": 110}, {"remaining": float("nan")}, {"reset_at": "tomorrow"}):
            with self.subTest(changes=changes):
                old = self.export["windows"][0]
                self.export["windows"][0] = {**old, **changes}
                self.assertEqual(self.run_export()["status"], "unavailable")
                self.assertEqual(self.recorded[-1]["windows"], [])
                self.export["windows"][0] = old

    def test_idle_and_mismatched_lease(self):
        old_job = self.job
        self.job = None
        self.assertEqual(self.run_export(), {"status": "idle"})
        self.job = {}
        self.assertEqual(self.run_export(), {"status": "idle"})
        self.assertEqual(self.recorded, [])
        self.job = {**old_job, "account": "different-account"}
        with self.assertRaisesRegex(ValueError, "binding"):
            self.run_export()
        self.assertEqual(self.recorded, [])

    def test_optional_idle_refresh_uses_configured_worker_interval(self):
        requests = []
        def idle(name, args):
            requests.append((name, args))
            return {}
        self.assertEqual(run_one({**self.profile, "idle_after_seconds": 1800}, idle), {"status": "idle"})
        self.assertEqual(requests[0][1]["idle_after_seconds"], 1800)
        with self.assertRaises(ValueError):
            run_one({**self.profile, "idle_after_seconds": 1}, idle)
        self.assertEqual(len(requests), 1)

    def test_codex_uses_duration_and_exact_pool_with_identity(self):
        sample = {"accountId": "official-seat-id", "rateLimitsByLimitId": {
            "default": {"primary": {"usedPercent": 80, "windowDurationMins": 10080, "resetsAt": 1800000000},
                        "secondary": {"usedPercent": 100, "windowDurationMins": 300, "resetsAt": None}}}}
        profile = {"codex_account_id": "official-seat-id", "limit_id": "default"}
        windows = codex_windows(sample, profile)
        self.assertEqual((windows[0]["remaining"], windows[0]["period"]), (20, "weekly"))
        self.assertEqual((windows[1]["remaining"], windows[1]["period"]), (0, "short"))
        for options, status in (({**profile, "limit_id": "missing"}, "unsupported"),
                                ({**profile, "codex_account_id": "other-seat"}, "auth_required")):
            with self.assertRaises(UsageError) as cm:
                codex_windows(sample, options)
            self.assertEqual(cm.exception.status, status)
        sample["rateLimitsByLimitId"]["default"]["primary"]["windowDurationMins"] = None
        self.assertEqual(codex_windows(sample, profile)[0]["period"], "other")

    def test_submitted_step_drives_sqlite_snapshot_after_commit(self):
        from agent_hub.storage import Store
        store = Store(Path(self.directory.name) / "hub.sqlite3")
        step = dict(event_id="e1", task_id="t1", attempt_id="a1", account="seat-1",
                    tool="claude", summary="synthetic completed verification", status="completed")
        receipt = store.report_step("project-a", "test-hook", step)
        self.export["observed_at"] = datetime.now(timezone.utc).isoformat()
        self.snapshot_file.write_text(json.dumps(self.export), encoding="utf-8")
        def call(method, arguments):
            return getattr(store, method)(**arguments)
        result = run_one(self.profile, call)
        self.assertEqual(result["job_id"], receipt["usage_job_id"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(run_one(self.profile, call), {"status": "idle"})
        overview = store.get_usage_overview("project-a")["accounts"]
        self.assertEqual(len(overview), 1)
        self.assertEqual(overview[0]["last_success"]["windows"][0]["remaining"], 40)

    def test_readonly_codex_stdio_protocol_and_errors(self):
        source = (
            "import json,sys\n"
            "first=json.loads(sys.stdin.readline()); assert first['method']=='initialize'\n"
            "print(json.dumps({'id':1,'result':{}}),flush=True)\n"
            "assert json.loads(sys.stdin.readline())=={'method':'initialized'}\n"
            "assert json.loads(sys.stdin.readline())=={'method':'account/rateLimits/read','id':2}\n"
            "print(json.dumps({'method':'notice','params':{}}),flush=True)\n"
            "print(json.dumps({'id':2, **json.loads(sys.argv[1])}),flush=True)\n"
        )
        def query(response):
            return asyncio.run(_read_codex([sys.executable, "-c", source, json.dumps(response)],
                                           os.environ.copy(), self.directory.name, timeout=3))
        self.assertEqual(query({"result": {"accountId": "fake-seat"}}), {"accountId": "fake-seat"})
        with self.assertRaises(UsageError) as cm:
            query({"error": {"code": 429, "message": "synthetic-secret"}})
        self.assertEqual(str(cm.exception), "rate_limited")


if __name__ == "__main__":
    unittest.main()
