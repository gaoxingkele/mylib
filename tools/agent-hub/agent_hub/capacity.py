"""Time-aware presentation of already authorized, shared-pool-deduplicated quota rows."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone


def _time(value):
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
        return stamp.astimezone(timezone.utc) if isinstance(stamp, datetime) and stamp.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def _utc(stamp):
    return stamp.isoformat().replace("+00:00", "Z") if stamp is not None else None


def _window(raw, freshness, now):
    period = raw.get("period")
    unit = raw.get("unit")
    remaining = raw.get("remaining")
    reset = _time(raw.get("reset_at"))
    state = "current"
    if raw.get("reset_at") is not None and reset is None:
        state = "unknown"
    elif reset is not None and reset <= now:
        state = "period_ended"
    elif freshness != "fresh":
        state = "stale"
    elif (not isinstance(period, str) or not isinstance(unit, str)
          or type(remaining) not in (int, float) or not 0 <= remaining <= 2**63 - 1
          or (unit == "percent" and remaining > 100)):
        state = "unknown"
    return {
        "period": period, "unit": unit, "state": state, "reset_at": _utc(reset),
        "remaining": remaining if state == "current" else None,
        **({"window_minutes": raw["window_minutes"]} if raw.get("window_minutes") is not None else {}),
    }


def _capacity(row, now, maximum_age):
    latest = row.get("latest") or {}
    success = row.get("last_success") or {}
    observed = _time(success.get("observed_at"))
    if not latest:
        freshness = "missing"
    elif latest.get("status") != "ok":
        freshness = "query_failed"
    elif observed is None or not now - maximum_age <= observed <= now:
        freshness = "stale"
    elif _time(latest.get("observed_at")) != observed:
        freshness = "stale"
    else:
        freshness = "fresh"
    windows = [_window(raw, freshness, now) for raw in success.get("windows", []) if isinstance(raw, dict)]
    # A subscription can have additional paid overage credits. A zero optional
    # balance does not block a still-available included subscription. A pure
    # balance pool is assessed on its own.
    limits = [window for window in windows if window["period"] != "balance"] or windows
    blocked = [window for window in limits if window["state"] == "current" and window["remaining"] == 0]
    verified = bool(limits) and all(window["state"] == "current" for window in limits)
    earliest = None
    if blocked:
        eligibility = "blocked"
        if verified and all(window["reset_at"] for window in blocked):
            earliest = max(_time(window["reset_at"]) for window in blocked)
    elif verified:
        eligibility = "available"
        earliest = now
    else:
        eligibility = "unknown"
    if freshness == "fresh" and any(window["state"] == "period_ended" for window in limits):
        freshness = "period_ended"
    return {"freshness": freshness, "eligibility": eligibility,
            "eligible": {"available": True, "blocked": False, "unknown": None}[eligibility],
            "earliest_possible_at": _utc(earliest), "windows": windows}


def capacity_overview(rows, *, now=None, max_age_seconds=900):
    """Return read-only quota facts and rankings within comparable provider/product units.

    The caller supplies rows after account ACL filtering and trusted shared-pool
    mapping. `now` takes an offset-aware datetime or ISO timestamp for replay.
    """
    now = datetime.now(timezone.utc) if now is None else _time(now)
    if now is None or type(max_age_seconds) != int or not 1 <= max_age_seconds <= 7 * 86400:
        raise ValueError("invalid_capacity_window")
    maximum_age = timedelta(seconds=max_age_seconds)
    accounts = []
    groups = defaultdict(dict)
    for row in rows:
        capacity = _capacity(row, now, maximum_age)
        accounts.append({**row, "capacity": capacity})
        if capacity["eligibility"] != "available" or capacity["freshness"] != "fresh":
            continue
        success = row["last_success"]
        provider = success.get("provider")
        pool_class = row.get("comparison_group") or row.get("pool")
        if not all(isinstance(value, str) and value for value in (provider, pool_class, row.get("account"))):
            continue
        weekly = [window for window in capacity["windows"] if window["period"] == "weekly"]
        # One meaningful weekly limit has clear semantics. A pure monetary
        # balance pool can only be compared within its currency and provider.
        rank_windows = weekly
        if not rank_windows and all(w["period"] == "balance" for w in capacity["windows"]):
            rank_windows = capacity["windows"]
        if len(rank_windows) != 1:
            continue
        metric = rank_windows[0]
        if metric["remaining"] is None or metric["remaining"] <= 0:
            continue
        key = (provider, pool_class, metric["period"], metric["unit"])
        entry = {field: row[field] for field in ("project", "projects", "account", "pool") if field in row}
        entry.update(remaining=metric["remaining"], reset_at=metric["reset_at"])
        member = (tuple(sorted(row.get("projects") or [row.get("project", "")])), row["account"], row.get("pool"))
        groups[key][member] = entry

    recommendations = []
    for (provider, pool_class, period, unit), members in sorted(groups.items()):
        ordered = sorted(members.values(), key=lambda item: (
            -item["remaining"], _time(item["reset_at"]) or datetime.max.replace(tzinfo=timezone.utc),
            item["account"], item.get("project", ""),
        ))
        recommendations.append({"provider": provider, "pool_class": pool_class,
                                "period": period, "unit": unit, "accounts": ordered})
    return {"accounts": accounts, "recommendations": recommendations, "as_of": _utc(now)}
