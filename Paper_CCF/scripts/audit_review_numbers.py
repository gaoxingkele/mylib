"""Small numeric consistency checks for evidence-calibrated reviews.

For ratios, operands are treated as the exact displayed counts supplied in the
ledger; only the reported ratio display is checked against nearest rounding.
This helper deliberately does not propagate ratio input rounding error.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, DecimalException, InvalidOperation, ROUND_HALF_UP, localcontext


MAX_ABS_EXPONENT = 10000


class InputError(ValueError):
    """Raised when the ledger cannot be audited as supplied."""


def audit_ledger(ledger):
    if not isinstance(ledger, dict):
        raise InputError("input error: ledger must be a JSON object")
    checks = ledger.get("checks")
    if not isinstance(checks, list):
        raise InputError("input error: ledger must contain a checks list")

    seen = set()
    audited = []
    for index, check in enumerate(checks):
        audited_check = _audit_check(check, index, seen)
        audited.append(audited_check)
    return {"checks": audited}


def _audit_check(check, index, seen):
    if not isinstance(check, dict):
        raise InputError(f"input error: check {index} must be an object")

    required = ("id", "kind", "operands", "reported", "resolution")
    missing = [name for name in required if name not in check]
    if missing:
        raise InputError(
            f"input error: check {index} missing required field(s): {', '.join(missing)}"
        )

    check_id = check["id"]
    if not isinstance(check_id, str) or not check_id:
        raise InputError(f"input error: check {index} id must be a non-empty string")
    if check_id in seen:
        raise InputError(f"input error: duplicate check id: {check_id}")
    seen.add(check_id)

    kind = check["kind"]
    if not isinstance(kind, str) or kind not in {"sum", "difference", "ratio"}:
        raise InputError(f"input error: {check_id} has unsupported kind: {kind}")

    operands = check["operands"]
    if not isinstance(operands, list):
        raise InputError(f"input error: {check_id} operands must be a list")
    if kind == "sum" and len(operands) < 2:
        raise InputError(f"input error: {check_id} sum requires at least 2 operands")
    if kind in {"difference", "ratio"} and len(operands) != 2:
        raise InputError(f"input error: {check_id} {kind} requires exactly 2 operands")

    numbers = [_finite_decimal(value, f"{check_id} operand {i}") for i, value in enumerate(operands)]
    reported = _finite_decimal(check["reported"], f"{check_id} reported")
    resolution = _finite_decimal(check["resolution"], f"{check_id} resolution")
    if resolution <= 0:
        raise InputError(f"input error: {check_id} resolution must be positive")

    rounding = check.get("rounding", "unknown")
    if not isinstance(rounding, str) or rounding not in {"nearest", "unknown"}:
        raise InputError(f"input error: {check_id} rounding must be nearest or unknown")

    try:
        with localcontext() as context:
            context.prec = _work_precision(numbers + [reported, resolution])
            computed = _compute(kind, numbers, check_id)
            discrepancy = reported - computed
            status = _status(
                kind, numbers, computed, reported, discrepancy, resolution, rounding
            )
    except DecimalException as exc:
        raise InputError(f"input error: {check_id} decimal calculation failed: {exc}") from None

    audited = {
        "id": check_id,
        "kind": kind,
        "operands": list(operands),
        "reported": check["reported"],
        "resolution": check["resolution"],
        "rounding": rounding,
        "computed": _decimal_text(computed),
        "status": status,
        "discrepancy": _decimal_text(discrepancy),
        "source": check.get("source"),
    }
    return audited


def _finite_decimal(value, label):
    if not isinstance(value, str):
        raise InputError(f"input error: {label} must be a numeric string")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise InputError(f"input error: {label} is not a valid number") from None
    if not number.is_finite():
        raise InputError(f"input error: {label} must be finite")
    if abs(number.adjusted()) > MAX_ABS_EXPONENT:
        raise InputError(f"input error: {label} exponent is outside supported range")
    return number


def _compute(kind, operands, check_id):
    if kind == "sum":
        return sum(operands, Decimal("0"))
    if kind == "difference":
        return operands[0] - operands[1]
    if operands[1] == 0:
        raise InputError(f"input error: {check_id} ratio denominator must be non-zero")
    return operands[0] / operands[1]


def _status(kind, operands, computed, reported, discrepancy, resolution, rounding):
    if discrepancy == 0:
        return "consistent"
    if rounding == "unknown":
        return "needs_definition"
    if kind in {"sum", "difference"}:
        rounded_values = len(operands) + 1
        tolerance = resolution * Decimal(rounded_values) / Decimal("2")
        if abs(discrepancy) <= tolerance:
            return "rounding_possible"
        return "mismatch"
    if reported == _nearest_resolution(computed, resolution):
        return "display_consistent"
    return "mismatch"


def _nearest_resolution(value, resolution):
    units = (value / resolution).to_integral_value(rounding=ROUND_HALF_UP)
    return units * resolution


def _decimal_text(value):
    return format(value, "f")


def _work_precision(values):
    digits = 0
    for value in values:
        tuple_digits = len(value.as_tuple().digits)
        integer_digits = max(value.adjusted() + 1, 1)
        digits = max(digits, tuple_digits, integer_digits)
    return max(50, digits + 10)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit numeric consistency in a review-check ledger."
    )
    parser.add_argument("ledger", nargs="?", help="JSON ledger path; reads stdin when omitted")
    args = parser.parse_args(argv)

    try:
        if args.ledger:
            with open(args.ledger, "r", encoding="utf-8") as handle:
                ledger = json.load(handle)
        else:
            ledger = json.load(sys.stdin)
        payload = audit_ledger(ledger)
    except json.JSONDecodeError as exc:
        payload = {"status": "input_error", "error": f"input error: invalid JSON: {exc.msg}"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    except OSError as exc:
        payload = {"status": "input_error", "error": f"input error: {exc}"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    except InputError as exc:
        payload = {"status": "input_error", "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
