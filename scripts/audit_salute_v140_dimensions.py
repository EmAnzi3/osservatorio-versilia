#!/usr/bin/env python3
"""Audit raw ARS exports for demographic and geographic dimensions.

This does not materialize extra data. It records what the live ARS exports expose
for the seven municipalities / Zona Versilia and whether the same export contains
Tuscany or Italy geographies. A changed whole-file SHA is recorded but only becomes
blocking when a cell belonging to the exact frozen v1.40 publication slice changes.
Additional periods in the live export are evidence, not release drift.
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
FROZEN = ROOT / "data" / "source-snapshots" / "ars-salute-11-v140.json"


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


def selected_total_rows(rows: list[dict[str, str]], iid: int, spec: dict) -> dict[tuple[str, str], dict]:
    selected: dict[tuple[str, str], dict] = {}
    for row in rows:
        code = str(row.get("codice_geografia") or "").strip()
        sex = str(row.get("sesso") or "").strip().lower()
        strato1 = str(row.get("strato1") or "").strip().lower()
        if code not in release.TOWNS or sex != "totale":
            continue
        if spec["strato"] is not None and strato1 != spec["strato"]:
            continue
        if spec["strato"] is None and strato1 not in ("", "totale"):
            continue
        period = str(row.get("anno") or "").strip()
        key = (release.TOWNS[code], period)
        if key in selected:
            raise RuntimeError(f"ARS {iid}: slice pubblicata ambigua per {key}")
        selected[key] = {
            "den": release.parse_num(row.get("den"), True),
            "num": release.parse_num(row.get("num"), True),
            "raw": release.parse_num(row.get("misura_grezza")),
            "standardized": release.parse_num(row.get("misura_standardizzata")),
            "ci95Low": release.parse_num(row.get("liminf")),
            "ci95High": release.parse_num(row.get("limsup")),
        }
    return selected


def frozen_total_rows(indicator: dict) -> dict[tuple[str, str], dict]:
    result = {}
    for geography, cells in indicator["series"].items():
        for cell in cells:
            result[(geography, str(cell["period"]))] = {
                key: cell.get(key)
                for key in ("den", "num", "raw", "standardized", "ci95Low", "ci95High")
            }
    return result


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    report = {
        "schemaVersion": 3,
        "release": "v1.40.0",
        "scope": "live raw ARS exports for the 11 v1.40 indicators",
        "note": (
            "Presence in the raw export does not by itself authorize publication: "
            "sex/age selectors and Tuscany/Italy benchmarks require homogeneous measure, "
            "period and standardization checks before materialization. Whole-export SHA drift "
            "and additional live periods are informational when every frozen publication cell "
            "is still present and unchanged."
        ),
        "indicators": {},
    }
    changed_slices: list[int] = []

    for iid, spec in release.SPECS.items():
        payload = release.csv_bytes_from_export(iid)
        sha = hashlib.sha256(payload).hexdigest()
        expected_sha = release.EXPECTED_SHA[iid]

        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        required = {
            "id_indicatore", "anno", "codice_geografia", "geografia", "den", "num",
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

        live_slice = selected_total_rows(rows, iid, spec)
        frozen_slice = frozen_total_rows(frozen["indicators"][str(iid)])
        frozen_keys = set(frozen_slice)
        live_keys = set(live_slice)
        missing_from_live = sorted(f"{geo}|{period}" for geo, period in frozen_keys - live_keys)
        new_in_live = sorted(f"{geo}|{period}" for geo, period in live_keys - frozen_keys)
        changed_cells = sorted(
            f"{geo}|{period}"
            for geo, period in frozen_keys & live_keys
            if frozen_slice[(geo, period)] != live_slice[(geo, period)]
        )
        slice_matches = not missing_from_live and not changed_cells
        if not slice_matches:
            changed_slices.append(iid)

        sexes = unique(row.get("sesso") for row in target_rows)
        strata1 = unique(row.get("strato1") for row in target_rows)
        strata2 = unique(row.get("strato2") for row in target_rows)
        periods = unique(row.get("anno") for row in target_rows)
        tuscany = geography_rows(rows, "Toscana")
        italy = geography_rows(rows, "Italia")

        report["indicators"][str(iid)] = {
            "key": spec["key"],
            "label": spec["label"],
            "liveSha256": sha,
            "frozenSha256": expected_sha,
            "wholeExportShaMatchesFrozen": sha == expected_sha,
            "publishedSliceMatchesFrozen": slice_matches,
            "publishedSliceMissingCells": missing_from_live,
            "additionalLiveCellsOutsideFrozenSlice": new_in_live,
            "publishedSliceChangedCells": changed_cells,
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
            f"Toscana={bool(tuscany)} Italia={bool(italy)} "
            f"sha={'same' if sha == expected_sha else 'drift'} "
            f"published-slice={'same' if slice_matches else 'CHANGED'} "
            f"extra-live-cells={len(new_in_live)}"
        )

    report["publishedSliceGate"] = {
        "status": "pass" if not changed_slices else "fail",
        "changedIndicatorIds": changed_slices,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audit dimensioni Salute v1.40: {OUTPUT}")
    if changed_slices:
        raise RuntimeError(f"Slice ARS pubblicata cambiata per gli indicatori: {changed_slices}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
