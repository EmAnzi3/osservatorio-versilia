#!/usr/bin/env python3
"""Reconcile existing Salute metrics against candidate ARS exports.

This is an evidence probe, not a materializer. Candidate ids come from the public
ARS indicator catalogue. A candidate is considered usable only when its official
export reproduces the seven currently published municipal values for the same
period/measure (within display precision). The report also records demographic
strata exposed by the source.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path

import materialize_salute_v140 as ars

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
OUTPUT = ROOT / "reports" / "salute-existing-ars-reconciliation.json"

# ARS public catalogue ids. No id is inferred from proximity or numbering.
CANDIDATES = {
    "mortalityAll": 1438,          # Mortalità per tutte le cause
    "chronicTotal": 2815,          # Prevalenza malati cronici (appendice Welfare)
    "diabetes": 271,               # Malati cronici di diabete mellito
    "dementia": 270,               # Malati cronici di demenza
    "emergencyAccess": 1657,       # Accessi in Pronto Soccorso
    "hospitalizedAll": 1274,       # Dimissioni ospedaliere per tutte le cause
    "elderlyHomeCare": 260,        # Anziani assistiti in domiciliare diretta
}

TOWN_BY_CODE = {code: town for code, town in ars.TOWNS.items() if code != "202M"}


def parse(value):
    return ars.parse_num(value)


def period_sort_key(value: str):
    text = str(value or "")
    nums = [int(part) for part in text.replace("–", "-").split("-") if part.isdigit()]
    return tuple(nums) if nums else (0,)


def total_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for row in rows:
        code = str(row.get("codice_geografia") or "").strip()
        sex = str(row.get("sesso") or "").strip().casefold()
        strato1 = str(row.get("strato1") or "").strip().casefold()
        strato2 = str(row.get("strato2") or "").strip().casefold()
        if code not in set(TOWN_BY_CODE) | {"202M", "90"}:
            continue
        if sex not in {"", "totale"}:
            continue
        if strato1 not in {"", "totale"} or strato2 not in {"", "totale"}:
            continue
        result.append(row)
    return result


def display_tolerance(value: float) -> float:
    # Existing Salute cards print two decimals. Half a last displayed digit plus
    # a tiny float margin is enough to prove the same published number.
    return max(0.0051, abs(value) * 1e-9)


def candidate_measure(row: dict[str, str], expected: float) -> tuple[str | None, float | None, float | None]:
    measures = {
        "standardized": parse(row.get("misura_standardizzata")),
        "raw": parse(row.get("misura_grezza")),
    }
    ranked = []
    for name, value in measures.items():
        if value is None:
            continue
        ranked.append((abs(float(value) - expected), name, float(value)))
    if not ranked:
        return None, None, None
    delta, name, value = min(ranked)
    return name, value, delta


def uniq(rows, key):
    return sorted({str(row.get(key) or "").strip() for row in rows if str(row.get(key) or "").strip()}, key=str.casefold)


def main() -> int:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    report = {"schemaVersion": 1, "candidates": {}}

    for key, iid in CANDIDATES.items():
        metric = site["metrics"][key]
        expected_by_town = {row["town"]: float(row["value"]) for row in metric.get("rows", [])}
        payload = ars.csv_bytes_from_export(iid)
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        rows = [row for row in reader if str(row.get("id_indicatore") or "").strip() == str(iid)]
        town_scope = [row for row in rows if str(row.get("codice_geografia") or "").strip() in TOWN_BY_CODE]
        totals = total_rows(rows)
        periods = sorted({str(row.get("anno") or "").strip() for row in totals}, key=period_sort_key)

        evaluations = []
        for period in periods:
            period_rows = {
                str(row.get("codice_geografia") or "").strip(): row
                for row in totals
                if str(row.get("anno") or "").strip() == period
            }
            matched = 0
            deltas = []
            measures = []
            details = []
            for code, town in TOWN_BY_CODE.items():
                expected = expected_by_town.get(town)
                row = period_rows.get(code)
                if expected is None or row is None:
                    details.append({"town": town, "expected": expected, "status": "missing"})
                    continue
                measure, observed, delta = candidate_measure(row, expected)
                ok = observed is not None and delta is not None and delta <= display_tolerance(expected)
                if ok:
                    matched += 1
                if delta is not None:
                    deltas.append(delta)
                if measure:
                    measures.append(measure)
                details.append({
                    "town": town,
                    "expected": expected,
                    "observed": observed,
                    "measure": measure,
                    "delta": delta,
                    "match": ok,
                })
            evaluations.append({
                "period": period,
                "matchedTowns": matched,
                "maxDelta": max(deltas) if deltas else None,
                "measureCandidates": sorted(set(measures)),
                "details": details,
            })

        best = max(
            evaluations,
            key=lambda item: (item["matchedTowns"], -(item["maxDelta"] if item["maxDelta"] is not None else math.inf)),
            default=None,
        )
        geographies = {str(row.get("geografia") or "").strip().casefold() for row in rows}
        entry = {
            "indicatorId": iid,
            "label": (metric.get("meta") or {}).get("label") or key,
            "publishedPeriod": (metric.get("meta") or {}).get("year"),
            "sexValues": uniq(town_scope, "sesso"),
            "strato1Values": uniq(town_scope, "strato1"),
            "strato2Values": uniq(town_scope, "strato2"),
            "hasTuscany": "regione toscana" in geographies,
            "hasItaly": "italia" in geographies,
            "bestReconciliation": best,
            "acceptedSameIndicator": bool(best and best["matchedTowns"] == 7),
        }
        report["candidates"][key] = entry
        print(
            f"{key} -> ARS {iid}: match={entry['acceptedSameIndicator']} "
            f"best={best['period'] if best else '-'} {best['matchedTowns'] if best else 0}/7 "
            f"sex={entry['sexValues'] or ['<vuoto>']} age={entry['strato1Values'] or ['<vuoto>']}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Reconciliation report:", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
