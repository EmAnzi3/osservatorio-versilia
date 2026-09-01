#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import opportunity_daily_refresh_revalidated as hardened


class ExpiredLifecycleTest(unittest.TestCase):
    def test_expired_application_skips_live_transport(self) -> None:
        entry = {
            "coverage_id": "expired-test",
            "lifecycle_stage": "application_open",
            "deadline_at": "2026-08-31",
            "url": "https://example.invalid/removed-after-deadline",
            "required_terms": ["must never be fetched"],
        }

        original = hardened._ORIGINAL_VERIFY

        def fail_if_called(*args, **kwargs):
            raise AssertionError("La verifica di rete non deve partire per un bando già scaduto")

        hardened._ORIGINAL_VERIFY = fail_if_called
        try:
            result = hardened.verify_entry_resilient(entry, date(2026, 9, 1), live=True)
        finally:
            hardened._ORIGINAL_VERIFY = original

        self.assertEqual(result, (True, "expired_deadline", None))

    def test_current_application_still_uses_strict_verification(self) -> None:
        entry = {
            "coverage_id": "current-test",
            "lifecycle_stage": "application_open",
            "deadline_at": "2026-09-30",
            "url": "https://example.invalid/current",
            "required_terms": ["required"],
        }
        calls = []
        original = hardened._ORIGINAL_VERIFY

        def strict_verifier(*args, **kwargs):
            calls.append((args, kwargs))
            return False, "failed", "strict verification reached"

        hardened._ORIGINAL_VERIFY = strict_verifier
        try:
            result = hardened.verify_entry_resilient(
                entry,
                date(2026, 9, 1),
                detail_payloads={entry["url"]: "missing required term"},
                live=True,
            )
        finally:
            hardened._ORIGINAL_VERIFY = original

        self.assertTrue(calls)
        self.assertEqual(result, (False, "failed", "strict verification reached"))


if __name__ == "__main__":
    unittest.main()
