#!/usr/bin/env python3
"""Regression tests for the A3 publication adapter."""
from __future__ import annotations

from copy import deepcopy

from materialize_a3_publication_adapter import apply_publication_adapter


def fixture() -> dict:
    return {
        "metrics": {
            "points": {
                "rows": [{
                    "town": "Massarosa",
                    "a3History": {
                        "source": "Fixture source",
                        "series": [{"year": 2023, "value": 1.0}, {"year": 2024, "value": 2.0}],
                    },
                }],
            },
            "vectors": {
                "rows": [{
                    "town": "Viareggio",
                    "a3History": {
                        "source": "Fixture source",
                        "periods": ["2013-2022", "2014-2023"],
                        "values": [10.0, 9.5],
                    },
                }],
            },
        }
    }


def test_normalization_and_idempotence() -> None:
    site = fixture()
    summary = apply_publication_adapter(site)
    assert summary == {"metricsAdapted": 2, "rowsAdapted": 2, "aggregatesAdapted": 0}
    assert site["metrics"]["points"]["rows"][0]["series"]["years"] == [2023, 2024]
    assert site["metrics"]["vectors"]["rows"][0]["series"]["years"] == ["2013-2022", "2014-2023"]
    assert all("a3History" not in metric["rows"][0] for metric in site["metrics"].values())
    assert apply_publication_adapter(site) == {"metricsAdapted": 0, "rowsAdapted": 0, "aggregatesAdapted": 0}


def test_conflicting_public_series_fails() -> None:
    site = fixture()
    row = site["metrics"]["points"]["rows"][0]
    row["series"] = {"years": [2023, 2024], "values": [1.0, 99.0]}
    try:
        apply_publication_adapter(site)
    except RuntimeError as exc:
        assert "diversa da a3History" in str(exc)
    else:
        raise AssertionError("Un conflitto tra series pubblica e a3History deve fallire")


if __name__ == "__main__":
    test_normalization_and_idempotence()
    test_conflicting_public_series_fails()
    print("A3 publication adapter regression passed.")
