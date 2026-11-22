"""The projection uses synthetic, already-authorized snapshots and a frozen clock."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_hub.capacity import capacity_overview


NOW = "2026-11-22T10:00:00Z"
WEEK_RESET = "2026-11-23T12:00:00Z"
SHORT_RESET = "2026-11-22T12:00:00Z"


def window(value, *, period="weekly", unit="percent", reset=WEEK_RESET):
    return {"period": period, "unit": unit, "remaining": value, "reset_at": reset}


def row(alias, windows, *, stamp=NOW, provider="codex", pool="included"):
    good = {"status": "ok", "provider": provider, "observed_at": stamp, "windows": windows}
    return {"project": "demo", "account": alias, "pool": pool, "latest": good, "last_success": good}


class CapacityTests(unittest.TestCase):
    def test_rank_only_comparable_available_accounts_and_preserve_scopes(self):
        entries = [
            row("low", [window(30)]), row("high", [window(85)]),
            row("blocked", [window(98), window(0, period="short", reset=SHORT_RESET)]),
            row("points", [window(200, unit="credits")]), row("other-site", [window(95)], provider="grok"),
            row("other-product", [window(97)], pool="team"), row("no-source", [window(99)], provider=""),
        ]
        entries[1].update(projects=["team", "demo"])
        before = deepcopy(entries)
        report = capacity_overview(entries, now=NOW)
        self.assertEqual(report["as_of"], NOW)
        self.assertEqual(entries, before)
        groups = {(g["provider"],g["pool_class"],g["period"],g["unit"]):g["accounts"]
                  for g in report["recommendations"]}
        seats = groups["codex","included","weekly","percent"]
        self.assertEqual([r["account"] for r in seats], ["high","low"])
        self.assertEqual(seats[0]["projects"], ["team","demo"])
        self.assertEqual(len(groups),4)
        blocked = report["accounts"][2]["capacity"]
        self.assertFalse(blocked["eligible"])
        self.assertEqual(blocked["earliest_possible_at"], SHORT_RESET)

    def test_zero_windows_choose_latest_known_reset_or_unknown_if_any_missing(self):
        values = [row("known", [window(0), window(0, period="short", reset=SHORT_RESET)]),
                  row("unknown", [window(0), window(0, period="short", reset=None)])]
        result = capacity_overview(values, now=NOW)
        first, second = [r["capacity"] for r in result["accounts"]]
        self.assertEqual((first["eligibility"], first["earliest_possible_at"]), ("blocked",WEEK_RESET))
        self.assertEqual((second["eligibility"], second["earliest_possible_at"]), ("blocked",None))
        self.assertEqual(result["recommendations"], [])

    def test_stale_or_expired_windows_hide_current_figures_but_keep_dated_history(self):
        cases = [row("aged", [window(88)], stamp="2026-11-22T09:44:59Z"),
                 row("expired", [window(77, reset=NOW)]), row("failed", [window(66)]),
                 row("short-expired", [window(99),window(0,period="short",reset=NOW)]),
                 {"account":"never", "pool":"included", "latest":None, "last_success":None}]
        cases[2]["latest"] = {"status":"auth_required", "observed_at":NOW}
        result = capacity_overview(cases, now=NOW)
        self.assertFalse(result["recommendations"])
        capacities = [r["capacity"] for r in result["accounts"]]
        self.assertEqual([c["freshness"] for c in capacities],
                         ["stale","period_ended","query_failed","period_ended","missing"])
        self.assertTrue(all(c["eligible"] is None for c in capacities))
        self.assertEqual([c["windows"][0]["remaining"] for c in capacities[:3]], [None,None,None])
        self.assertEqual(capacities[3]["windows"][0]["remaining"],99)
        self.assertEqual(capacities[3]["windows"][1]["remaining"],None)
        self.assertEqual(result["accounts"][0]["last_success"]["windows"][0]["remaining"],88)

    def test_pure_balances_by_currency_and_ambiguous_pools(self):
        entries = [row("usd", [window(60,period="balance",unit="USD",reset=None)],pool="api"),
                   row("cny", [window(33,period="balance",unit="CNY",reset=None)],pool="api"),
                   row("two-weeks", [window(44),window(90)]),
                   row("short-only", [window(10,period="short",reset=SHORT_RESET)]),
                   row("subscription", [window(20),window(0,period="balance",unit="USD",reset=None)])]
        report = capacity_overview(entries, now=NOW)
        groups = {(r["period"],r["unit"]):r["accounts"] for r in report["recommendations"]}
        self.assertEqual(set(groups), {("balance","USD"),("balance","CNY"),("weekly","percent")})
        self.assertEqual([r["account"] for r in groups["weekly","percent"]],["subscription"])
        self.assertTrue(report["accounts"][-1]["capacity"]["eligible"])

    def test_unknown_or_future_times_never_become_fresh_recommendations(self):
        entries = [row("future",[window(10)],stamp="2026-11-22T12:00:00Z"),
                   row("no-tz",[window(43)],stamp="2026-11-22T10:00:00"),
                   row("bad-reset",[window(66,reset="broken")]),
                   row("bad-value",[window(None)])]
        report = capacity_overview(entries, now=NOW)
        self.assertEqual(report["recommendations"],[])
        self.assertTrue(all(r["capacity"]["eligible"] is None for r in report["accounts"]))
        with self.assertRaisesRegex(ValueError, "invalid_capacity_window"):
            capacity_overview([], now="2026-11-22T10:00:00")

    def test_global_shared_pool_is_not_multiplied_by_project_count(self):
        shared = row("mine",[window(76)])
        shared["projects"] = ["private-a","private-b"]
        report = capacity_overview([shared], now=NOW)
        [group] = report["recommendations"]
        self.assertEqual(len(group["accounts"]),1)
        [observed] = group["accounts"]
        self.assertEqual(observed["remaining"],76)
        self.assertEqual(set(observed["projects"]),set(shared["projects"]))


if __name__ == "__main__":
    unittest.main()
