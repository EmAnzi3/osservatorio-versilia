#!/usr/bin/env python3
"""Audit raw ARS exports for demographic and geographic dimensions.

This does not materialize extra data. It records what the frozen-source exports
actually expose for the seven municipalities / Zona Versilia and whether the same
export contains Tuscany or Italy geographies. The report is evidence for deciding
future UI selectors and external benchmarks without proxies.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import materialize_salute_v140 as release

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "salute-v140-source-dimensions.json"


def unique(values):
    return sorted({str(value or "").strip() for value in values if str(value or "").strip()}, key=str.casefold)


def geography_rows(rows: list[dict[str, str]], token: str) -> list[dict[str, str]]:
    result = []
    seen = set()
    for row in rows:
        name = str(row.get("geografia") or "").strip()
        if token.casefold() not in name.casefold():
            continue
        item = (str(row.get("codice_geografia") or "").strip(), name)
        if item in seen:
            continue
        seen.add(item)
        result.append({"code": item[0], "name": item[1]})
    return sorted(result, key=lambda item: (item["name"].casefold(), item["code"]))


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": 1,
        "release": "v1.40.0",
        "scope": "raw ARS exports for the 11 v1.40 indicators",
        "note": (
            "Presence in the raw export does not by itself authorize publication: "
            "sex/age selectors and Tuscany/Italy benchmarks require homogeneous measure, "
            "period and standardization checks before materialization."
        ),
        "indicators": {},
    }

    for iid, spec in release.SPECS.items():
        payload = release.csv_bytes_from_export(iid)
        sha = hashlib.sha256(payload).hexdigest()
        expected_sha = release.EXPECTED_SHA[iid]
        if sha != expected_sha:
            raise RuntimeError(f"ARS {iid}: SHA inatteso {sha}, atteso {expected_sha}")

        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        required = {
            "id_indicatore", "anno", "codice_geografia", "geografia",
            "misura_grezza", "misura_standardizzata", "liminf", "limsup",
            "sesso", "strato1", "strato2",
        }
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"ARS {iid}: schema raw inatteso: {reader.fieldnames}")
        rows = [row for row in reader if str(row.get("id_indicatore") or "").strip() == str(iid)]

        target_rows = [
            row for row in rows
            if str(row.get("codice_geografia") or "").strip() in release.TOWNS
        ]
        if not target_rows:
            raise RuntimeError(f"ARS {iid}: nessuna riga nel perimetro comunale/202M")

        sexes = unique(row.get("sesso") for row in target_rows)
        strata1 = unique(row.get("strato1") for row in target_rows)
        strata2 = unique(row.get("strato2") for row in target_rows)
        periods = unique(row.get("anno") for row in target_rows)
        tuscany = geography_rows(rows, "Toscana")
        italy = geography_rows(rows, "Italia")

        report["indicators"][str(iid)] = {
            "key": spec["key"],
            "label": spec["label"],
            "sha256": sha,
            "targetRowCount": len(target_rows),
            "sexValues": sexes,
            "strato1Values": strata1,
            "strato2Values": strata2,
            "periodCount": len(periods),
            "tuscanyGeographies": tuscany,
            "italyGeographies": italy,
            "hasSexBreakdownInTargetScope": len([value for value in sexes if value.casefold() != "totale"]) > 0,
            "hasStratificationInTargetScope": bool(
                [value for value in strata1 if value.casefold() not in {"totale"}]
                or [value for value in strata2 if value.casefold() not in {"totale"}]
            ),
            "hasTuscanyInSameExport": bool(tuscany),
            "hasItalyInSameExport": bool(italy),
        }
        print(
            f"ARS {iid} {spec['key']}: sesso={sexes or ['<vuoto>']} "
            f"strato1={strata1 or ['<vuoto>']} strato2={strata2 or ['<vuoto>']} "
            f"Toscana={bool(tuscany)} Italia={bool(italy)}"
        )

    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audit dimensioni Salute v1.40: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
