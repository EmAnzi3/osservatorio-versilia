#!/usr/bin/env python3
"""Audit demographic dimensions available for health indicators already in catalog.

The report is intentionally source-first: it extracts ARS indicator ids from the
metric contract, downloads the official export, and records sex/age strata without
materializing them. This lets the release add only dimensions that are actually
published by the same source and measure.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

import materialize_salute_v140 as v140

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
OUTPUT = ROOT / "reports" / "salute-existing-dimensions.json"
NEW_KEYS = {spec["key"] for spec in v140.SPECS.values()} | {"accreditedRsaCount"}

ARS_ID_PATTERNS = (
    re.compile(r"dettaglio_indicatore[-=/](\d{2,5})", re.I),
    re.compile(r"[?&]indicatore=(\d{2,5})", re.I),
    re.compile(r"(?:^|\D)indicatore\s*[:#-]?\s*(\d{2,5})(?:\D|$)", re.I),
)


def strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value


def ars_ids(metric: dict) -> list[int]:
    found = set()
    for text in strings(metric):
        if "ars.toscana" not in text.casefold() and "indicatore" not in text.casefold():
            continue
        for pattern in ARS_ID_PATTERNS:
            for match in pattern.findall(text):
                found.add(int(match))
    return sorted(found)


def uniq(values):
    return sorted({str(v or "").strip() for v in values if str(v or "").strip()}, key=str.casefold)


def target_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row for row in rows
        if str(row.get("codice_geografia") or "").strip() in v140.TOWNS
    ]


def audit_export(iid: int) -> dict:
    payload = v140.csv_bytes_from_export(iid)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    rows = [row for row in reader if str(row.get("id_indicatore") or "").strip() == str(iid)]
    towns = target_rows(rows)
    sexes = uniq(row.get("sesso") for row in towns)
    strato1 = uniq(row.get("strato1") for row in towns)
    strato2 = uniq(row.get("strato2") for row in towns)
    years = uniq(row.get("anno") for row in towns)
    geographies = uniq(row.get("geografia") for row in rows)
    return {
        "rowCountTownScope": len(towns),
        "sexValues": sexes,
        "strato1Values": strato1,
        "strato2Values": strato2,
        "periods": years,
        "hasSexBreakdown": any(v.casefold() != "totale" for v in sexes),
        "hasAgeOrOtherStratification": any(v.casefold() not in {"totale"} for v in strato1 + strato2),
        "hasRegionTuscany": any(v.casefold() == "regione toscana" for v in geographies),
        "hasItaly": any(v.casefold() == "italia" for v in geographies),
    }


def main() -> int:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    health_keys = list(site.get("themes", {}).get("salute", {}).get("metrics", []))
    report = {
        "schemaVersion": 1,
        "catalogVersion": site.get("version"),
        "healthMetricCount": len(health_keys),
        "excludedV140Keys": sorted(NEW_KEYS),
        "metrics": {},
    }
    for key in health_keys:
        if key in NEW_KEYS:
            continue
        metric = site.get("metrics", {}).get(key) or {}
        meta = metric.get("meta") or {}
        ids = ars_ids(metric)
        item = {
            "label": meta.get("label") or meta.get("shortLabel") or key,
            "unit": meta.get("unit"),
            "source": meta.get("source"),
            "sourceUrl": meta.get("sourceUrl"),
            "arsIndicatorIds": ids,
            "currentCompositeType": meta.get("compositeType"),
            "hasExistingParts": any(bool(row.get("parts")) for row in metric.get("rows", [])),
        }
        if len(ids) == 1:
            try:
                item["exportAudit"] = audit_export(ids[0])
            except Exception as exc:  # evidence job: preserve failure per metric
                item["exportAuditError"] = f"{type(exc).__name__}: {exc}"
        elif len(ids) > 1:
            item["exportAuditError"] = "Più di un id ARS trovato nel contratto; richiede verifica manuale"
        report["metrics"][key] = item
        print(
            key,
            "|", item["label"],
            "| ARS", ids or "-",
            "|", (item.get("exportAudit") or {}).get("sexValues", "-"),
            "|", (item.get("exportAudit") or {}).get("strato1Values", "-"),
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Audit indicatori Salute pre-v1.40:", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
