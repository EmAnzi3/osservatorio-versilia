#!/usr/bin/env python3
"""Overlay h6: distingue opportunità comunali e partnership nel daily snapshot."""
from __future__ import annotations

from datetime import date
from typing import Any

import opportunity_daily_refresh_audit_fixed as audit_fixed
import opportunity_municipal_relevance as relevance

_BASE_PREPARE = audit_fixed._prepare_public_audit_fixed
DAILY_HARDENING_VERSION = "0.4.4-h6"


def _prepare_public_relevance(result: dict[str, Any], today: date) -> dict[str, Any]:
    result = _BASE_PREPARE(result, today)
    relevance.apply_to_payload(result, drop_review=True)
    result["dailyHardeningVersion"] = DAILY_HARDENING_VERSION
    result["municipalRelevanceVersion"] = relevance.SCHEMA_VERSION
    return result


def main() -> int:
    original = audit_fixed._prepare_public_audit_fixed
    audit_fixed._prepare_public_audit_fixed = _prepare_public_relevance
    try:
        return audit_fixed.main()
    finally:
        audit_fixed._prepare_public_audit_fixed = original


if __name__ == "__main__":
    raise SystemExit(main())
