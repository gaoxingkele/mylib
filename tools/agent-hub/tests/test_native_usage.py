"""Provider-free tests for native quota observations."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_hub.native_usage import (
    _fetch_grok, _grok_usage, collect_native, grok_shape_fingerprint,
    observe_claude_statusline,
)
from agent_hub.quota import UsageError, run_one


NOW = datetime(2026, 11, 22, 12, tzinfo=timezone.utc)


class NativeUsageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.root / "claude-pilot"
        self.config.mkdir()
        self.profile = {
            "native_enabled": True, "project": "pilot", "account": "seat", "pool": "included",
            "worker": "pilot-worker", "origin_source": "pilot-machine", "provider": "claude",
            "source": "claude_statusline", "claude_config_dir": str(self.config),
            "claude_session_id": "pilot-session", "claude_version": "2.1.fixture",
            "observer_db": str(self.root / "claude-observer.sqlite"),
        }
        self.environment = {"CLAUDE_CONFIG_DIR": str(self.config)}
        self.job = {
            "project": "pilot", "account": "seat", "worker": "pilot-worker", "trigger": "step",
            "source": "pilot-machine", "tool": "claude", "accepted_at": NOW.isoformat(),
            "event_id": "step-1", "job_id": 1, "lease_token": "fixture-lease",
        }

    def claude_payload(self, used):
        return {
            "session_id": "pilot-session", "version": "2.1.fixture",
            "transcript_path": "private-fixture-transcript.jsonl", "opaque_secret": "fixture-secret",
            "rate_limits": {
                "seven_day": {"used_percentage": used, "resets_at": int((NOW + timedelta(days=3)).timestamp())},
                "five_hour": {"used_percentage": 25, "resets_at": int((NOW + timedelta(hours=1)).timestamp())},
            },
        }

    def observe(self, payload, seconds=0, **kwargs):
        return observe_claude_statusline(
            self.profile, json.dumps(payload).encode(), now=NOW + timedelta(seconds=seconds),
            environ=kwargs.get("environment", self.environment),
        )

    def grok_fixture(self):
        # Deliberately fictitious field names. These are not a vendor schema.
        payload = {
            "fixture_identity": "fixture-account-42", "fixture_observed": int(NOW.timestamp()),
            "fixture_week": {"used": 42.5, "reset": int((NOW + timedelta(days=3)).timestamp())},
            "fixture_secret": "do-not-forward",
        }
        review = {
            "shape_sha256": grok_shape_fingerprint(payload), "account_path": ["fixture_identity"],
            "observed_at_path": ["fixture_observed"], "observed_at_format": "unix_seconds",
            "windows": [{"period": "weekly", "window_minutes": 10080,
                         "used_percent_path": ["fixture_week", "used"],
                         "reset_path": ["fixture_week", "reset"], "reset_format": "unix_seconds"}],
        }
        profile = {**self.profile, "source": "grok_cli", "provider": "grok", "grok_schema": review,
                   "grok_account_id": "fixture-account-42", "grok_version_line": "grok fixture [test]"}
        return profile, {**self.job, "tool": "grok"}, payload

    def test_claude_redisplay_does_not_manufacture_fresh_observation(self):
        self.assertFalse(self.observe(self.claude_payload(30), -1))
        self.assertFalse(self.observe(self.claude_payload(30), 1))
        with self.assertRaisesRegex(UsageError, "unavailable"):
            collect_native(self.profile, self.job, NOW + timedelta(seconds=1))
        self.assertTrue(self.observe(self.claude_payload(39), 2))
        self.assertFalse(self.observe(self.claude_payload(39), 3))
        self.assertFalse(self.observe(self.claude_payload(38), 4))
        snapshot = collect_native(self.profile, self.job, NOW + timedelta(seconds=5))
        self.assertEqual(snapshot["observed_at"], "2026-11-22T12:00:02Z")
        self.assertEqual([window["remaining"] for window in snapshot["windows"]], [61])
        self.assertNotIn(b"private-fixture-transcript", Path(self.profile["observer_db"]).read_bytes())
        self.assertNotIn(b"fixture-secret", Path(self.profile["observer_db"]).read_bytes())
        newer = {**self.job, "accepted_at": (NOW + timedelta(seconds=3)).isoformat()}
        with self.assertRaisesRegex(UsageError, "unavailable"):
            collect_native(self.profile, newer, NOW + timedelta(seconds=5))

    def test_a_short_window_change_cannot_stamp_stale_weekly_usage(self):
        self.observe(self.claude_payload(30), -3)
        self.observe(self.claude_payload(32), -2)
        short_only = self.claude_payload(32)
        short_only["rate_limits"]["five_hour"]["used_percentage"] = 35
        self.assertTrue(self.observe(short_only, 1))
        with self.assertRaisesRegex(UsageError, "unavailable"):
            collect_native(self.profile, self.job, NOW + timedelta(seconds=1))
        short_only["rate_limits"]["seven_day"]["used_percentage"] = 34
        self.assertTrue(self.observe(short_only, 2))
        snapshot = collect_native(self.profile, self.job, NOW + timedelta(seconds=3))
        self.assertEqual([window["remaining"] for window in snapshot["windows"]], [66, 65])
        self.assertEqual(snapshot["observed_at"], "2026-11-22T12:00:01Z")

    def test_claude_scope_login_and_layout_checks_are_independent(self):
        for payload, env in (
            ({**self.claude_payload(10), "session_id": "alien"}, self.environment),
            ({**self.claude_payload(10), "version": "other"}, self.environment),
            (self.claude_payload(10), {"CLAUDE_CONFIG_DIR": str(self.root)}),
            (self.claude_payload(10), {**self.environment, "ANTHROPIC_API_KEY": "test-marker"}),
        ):
            with self.subTest(payload_keys=list(payload)):
                with self.assertRaisesRegex(UsageError, "auth_required"):
                    self.observe(payload, environment=env)
        missing = self.claude_payload(1)
        missing["rate_limits"] = {"spend_limit": {"used_percentage": 70}}
        self.assertFalse(self.observe(missing))
        bad = self.claude_payload(0)
        bad["rate_limits"]["seven_day"]["used_percentage"] = True
        with self.assertRaisesRegex(UsageError, "unavailable"):
            self.observe(bad)
        with self.assertRaisesRegex(UsageError, "auth_required"):
            collect_native(self.profile, {**self.job, "source": "wrong-machine"}, NOW)
        with self.assertRaisesRegex(UsageError, "unsupported"):
            collect_native({**self.profile, "native_enabled": False}, self.job, NOW)

    def test_claude_scheduled_jobs_still_need_recent_account_bound_observation(self):
        self.observe(self.claude_payload(40), -2)
        self.observe(self.claude_payload(41), 1)
        scheduled = {**self.job, "source": None, "tool": None, "event_id": None, "trigger": "scheduled"}
        self.assertEqual(collect_native(self.profile, scheduled, NOW + timedelta(seconds=2))["status"], "ok")
        with self.assertRaisesRegex(UsageError, "auth_required"):
            collect_native({**self.profile, "claude_session_id": "other-session"}, scheduled,
                           NOW + timedelta(seconds=2))
        with self.assertRaisesRegex(UsageError, "unavailable"):
            collect_native(self.profile, scheduled, NOW + timedelta(minutes=16))

    def test_grok_projection_needs_exact_layout_identity_and_timestamp(self):
        profile, job, payload = self.grok_fixture()
        valid = _grok_usage(profile, job, NOW, payload)
        self.assertEqual(valid["windows"][0]["remaining"], 57.5)
        self.assertNotIn("do-not-forward", json.dumps(valid))
        for changed, expected in (
            ({**payload, "fixture_observed": int(NOW.timestamp()) - 1}, "unavailable"),
            ({**payload, "fixture_observed": int(NOW.timestamp()) + 1}, "unavailable"),
            ({**payload, "fixture_identity": "other"}, "auth_required"),
            ({**payload, "unknown_field": None}, "unsupported"),
            ({**payload, "fixture_week": {"used": 101, "reset": payload["fixture_week"]["reset"]}}, "unavailable"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(UsageError, expected):
                    _grok_usage(profile, job, NOW, changed)

    def test_grok_command_is_pinned_to_the_opted_in_build_and_leader(self):
        profile, job, payload = self.grok_fixture()
        argv_list = []

        async def runner(argv, cwd, environment):
            self.assertTrue(Path(cwd).is_dir())
            self.assertNotIn("AGENT_HUB_QUOTA_TOKEN", environment)
            self.assertNotIn("XAI_API_KEY", environment)
            argv_list.append(argv)
            return b"grok fixture [test]\n" if argv[-1] == "--version" else json.dumps(payload).encode()

        binary = self.root / "grok.exe"
        socket = self.root / "leader-pilot.sock"
        with patch("agent_hub.native_usage._grok_paths", return_value=(binary, socket)), patch.dict(
            os.environ, {"XAI_API_KEY": "fixture", "AGENT_HUB_QUOTA_TOKEN": "fixture"}
        ):
            result = _fetch_grok(profile, job, NOW, runner=runner, clock=lambda: NOW)
            self.assertEqual(result["observed_at"], "2026-11-22T12:00:00Z")
            self.assertEqual(argv_list, [[str(binary), "--version"],
                                        [str(binary), "usage", "--json", "--leader-socket", str(socket)]])
            argv_list.clear()
            with self.assertRaisesRegex(UsageError, "unsupported"):
                _fetch_grok({**profile, "grok_version_line": "other"}, job, NOW, runner=runner, clock=lambda: NOW)
            self.assertEqual(len(argv_list), 1)

    def test_unknown_grok_schema_never_queries_account_and_writes_failure(self):
        profile, job, _ = self.grok_fixture()
        profile.pop("grok_schema")
        calls = []

        def call(name, values):
            calls.append((name, values))
            return job if name == "claim_usage_job" else values["snapshot"]

        with patch("agent_hub.native_usage._grok_paths") as paths:
            self.assertEqual(run_one(profile, call, now=lambda: NOW)["status"], "unsupported")
            paths.assert_not_called()
        self.assertEqual(calls[1][0], "record_usage_snapshot")
        self.assertEqual(calls[1][1]["snapshot"]["windows"], [])
