#!/usr/bin/env python3
"""Regression tests for A3.2 route/storage-aware structural evidence."""
from __future__ import annotations

import base64
import gzip
import json
import tempfile
from pathlib import Path

from enrichment_route_evidence import structured_route_evidence


def _write_packed(root: Path, relative: str, payload: object) -> None:
    directory = root / relative
    directory.mkdir(parents=True)
    raw = gzip.compress(json.dumps(payload).encode("utf-8"))
    encoded = base64.b64encode(raw).decode("ascii")
    pivot = len(encoded) // 2
    directory.joinpath("payload-00.b64").write_text(encoded[:pivot], encoding="utf-8")
    directory.joinpath("payload-01.b64").write_text(encoded[pivot:], encoding="utf-8")


def test_route_evidence() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        payload = {
            "series": [
                {
                    "year": 2024,
                    "section": "001",
                    "sex": "female",
                    "category": "A",
                    "voters": 60,
                    "electors": 100,
                    "percentage": 60.0,
                    "benchmark": {"Toscana": 61.0},
                },
                {
                    "year": 2025,
                    "section": "001",
                    "sex": "male",
                    "category": "B",
                    "voters": 70,
                    "electors": 100,
                    "percentage": 70.0,
                    "benchmark": {"Toscana": 68.0},
                },
            ]
        }
        _write_packed(root, "data/packed", payload)
        metric = {"dataStorage": {"path": "data/packed", "prefix": "payload-"}}

        expected = {
            "serie_storica",
            "sesso",
            "dettaglio_territoriale",
            "benchmark_toscana_italia",
            "assoluto_normalizzato",
            "numeratore_denominatore",
            "categorie_specifiche",
        }
        for dimension in expected:
            assert structured_route_evidence(metric, dimension, root), dimension

        assert structured_route_evidence(metric, "eta", root) is None
        assert structured_route_evidence(metric, "frequenza_infra_annuale", root) is None

        turnout_payload = {
            "families": {
                "referendum": {
                    "events": [
                        {
                            "year": 2024,
                            "municipalities": [
                                {
                                    "town": "Massarosa",
                                    "voters": 60,
                                    "electors": 100,
                                    "turnout": 60.0,
                                    "maleTurnout": 62.0,
                                    "femaleTurnout": 58.0,
                                }
                            ],
                        },
                        {
                            "year": 2025,
                            "municipalities": [
                                {
                                    "town": "Massarosa",
                                    "voters": 70,
                                    "electors": 100,
                                    "turnout": 70.0,
                                    "maleTurnout": 71.0,
                                    "femaleTurnout": 69.0,
                                }
                            ],
                        },
                    ]
                }
            }
        }
        _write_packed(root, "data/turnout", turnout_payload)
        turnout_metric = {
            "dataStorage": {
                "path": "data/turnout",
                "prefix": "payload-",
            }
        }
        for dimension in {
            "serie_storica",
            "sesso",
            "dettaglio_territoriale",
            "assoluto_normalizzato",
            "numeratore_denominatore",
            "categorie_specifiche",
        }:
            assert structured_route_evidence(turnout_metric, dimension, root), dimension
        assert structured_route_evidence(turnout_metric, "eta", root) is None
        assert structured_route_evidence(turnout_metric, "benchmark_toscana_italia", root) is None
        assert structured_route_evidence(turnout_metric, "frequenza_infra_annuale", root) is None

        climate = {"dataStorage": {"backend": "external-climate", "normalizedPercent": True}}
        evidence = structured_route_evidence(climate, "assoluto_normalizzato", root) or ""
        assert "normalizedPercent" in evidence
        assert structured_route_evidence(climate, "serie_storica", root) is None

        undeclared = {"rows": payload["series"]}
        assert structured_route_evidence(undeclared, "serie_storica", root) is None

        escaped = {"dataStorage": {"path": "../outside"}}
        assert structured_route_evidence(escaped, "serie_storica", root) is None


if __name__ == "__main__":
    test_route_evidence()
    print("A3.2 route-aware evidence regressions passed.")
