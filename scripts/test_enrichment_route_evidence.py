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

        compact_payload = {
            "v": 2,
            "y": [2024, 2025],
            "t": [["massarosa", "Massarosa"], ["viareggio", "Viareggio"]],
            "rt": [1000, 1100],
            "tt": [[100, 105], [200, 210]],
            "c": [
                ["A 01", [400, 420], "Agricoltura", [[40, 42], 8], [[70, 73], 12]],
                ["C 10", [300, 330], "Industria", [[30, 31], 5], [[60, 65], 9]],
            ],
        }
        _write_packed(root, "data/compact", compact_payload)
        compact_metric = {
            "dataStorage": {
                "path": "data/compact",
                "prefix": "payload-",
                "compactSchema": {
                    "periodAxis": "y",
                    "territoryAxis": "t",
                    "categoryRows": "c",
                    "regionalSeriesIndex": 1,
                    "townSeriesStartIndex": 3,
                    "townSeriesIndex": 0,
                    "townSecondaryIndex": 1,
                    "territoryTotals": "tt",
                    "regionalTotals": "rt",
                },
            }
        }
        compact_expected = {
            "serie_storica",
            "dettaglio_territoriale",
            "benchmark_toscana_italia",
            "assoluto_normalizzato",
            "numeratore_denominatore",
            "categorie_specifiche",
        }
        for dimension in compact_expected:
            assert structured_route_evidence(compact_metric, dimension, root), dimension
        assert structured_route_evidence(compact_metric, "sesso", root) is None
        assert structured_route_evidence(compact_metric, "eta", root) is None

        trailerless_dir = root / "data" / "trailerless"
        trailerless_dir.mkdir(parents=True)
        trailerless_payload = {
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
                                    "maleTurnout": 61.0,
                                    "femaleTurnout": 59.0,
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
        raw = gzip.compress(json.dumps(trailerless_payload).encode("utf-8"))[:-8]
        trailerless_dir.joinpath("archive-00.b64").write_text(
            base64.b64encode(raw).decode("ascii"),
            encoding="utf-8",
        )
        trailerless_metric = {
            "dataStorage": {
                "path": "data/trailerless",
                "prefix": "archive-00",
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
            assert structured_route_evidence(trailerless_metric, dimension, root), dimension

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
