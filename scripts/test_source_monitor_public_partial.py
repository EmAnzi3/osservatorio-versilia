#!/usr/bin/env python3
"""Regressione: il monitor rispetta i n.d. ufficiali dichiarati dal catalogo pubblico."""
from __future__ import annotations

import monthly_data_check_coverage as coverage


def main() -> None:
    data = {
        "metrics": {
            "partialPublicMetric": {
                "meta": {
                    "key": "partialPublicMetric",
                    "allowPartialHistory": True,
                },
                "method": {
                    "coverage": "4/7 · 6/7 secondo vista; n.d. mantenuti senza stime.",
                },
                "rows": [
                    {
                        "town": "Comune A",
                        "value": None,
                        "formatted": "n.d.",
                        "series": {
                            "years": [2023, 2024, 2025],
                            "values": [10.0, None, 12.0],
                        },
                    },
                    {
                        "town": "Comune B",
                        "value": 9.0,
                        "formatted": "9,0",
                        "series": {
                            "years": [2023, 2024, 2025],
                            "values": [8.0, 8.5, 9.0],
                        },
                    },
                ],
            }
        }
    }

    original_validate = coverage.ORIGINAL_VALIDATE
    observed = {}

    def fake_base_validate(prepared, _registry):
        row = prepared["metrics"]["partialPublicMetric"]["rows"][0]
        observed["value"] = row["value"]
        observed["years"] = row["series"]["years"]
        observed["values"] = row["series"]["values"]
        return [], {}, {"metricCount": 1}

    try:
        coverage.ORIGINAL_VALIDATE = fake_base_validate
        findings, _, _ = coverage.validate_dataset(data, {"expectedTowns": []})
    finally:
        coverage.ORIGINAL_VALIDATE = original_validate

    assert findings == [], findings
    assert observed == {
        "value": 0,
        "years": [2023, 2025],
        "values": [10.0, 12.0],
    }, observed

    # Il dataset originario non deve essere alterato dal validatore.
    original = data["metrics"]["partialPublicMetric"]["rows"][0]
    assert original["value"] is None
    assert original["series"]["values"] == [10.0, None, 12.0]
    print("Source monitor partial-history regression passed.")


if __name__ == "__main__":
    main()
