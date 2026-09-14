#!/usr/bin/env python3
"""Build a compact evidence snapshot for Salute sex/age selectors.

The script is CI/audit-only: it downloads official ARS CSV exports and writes the
exact current publication period for municipalities, Zona Versilia (202M) and
Regione Toscana (90). Nothing is wired into the public build until the generated
snapshot has been reviewed and committed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import materialize_salute_v140 as ars

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "ars-salute-demographics-v140.json"

# Exact indicators/periods currently published by the Observatory and reconciled
# against ARS. 1274 and 2815 are deliberately excluded: the generic exports did
# not reproduce the current Observatory slice and therefore cannot be used safely.
SPECS = {
    1290: {"key": "lifeExpectancy", "period": "2022", "unit": "years"},
    1438: {"key": "mortalityAll", "period": "2013-2022", "unit": "per100k"},
    1499: {"key": "mortalityCancer", "period": "2013-2022", "unit": "per100k"},
    1327: {"key": "mortalityCirculatory", "period": "2013-2022", "unit": "per100k"},
    1606: {"key": "mortalityRespiratory", "period": "2013-2022", "unit": "per100k"},
    255: {"key": "hypertensionPrevalence", "period": "2025", "unit": "per1000"},
    268: {"key": "copdPrevalence", "period": "2025", "unit": "per1000"},
    269: {"key": "ischemicHeartDiseasePrevalence", "period": "2025", "unit": "per1000"},
    272: {"key": "heartFailurePrevalence", "period": "2025", "unit": "per1000"},
    273: {"key": "priorStrokePrevalence", "period": "2025", "unit": "per1000"},
    271: {"key": "diabetes", "period": "2025", "unit": "per1000"},
    270: {"key": "dementia", "period": "2025", "unit": "per1000"},
    261: {"key": "permanentRsaAssisted", "period": "2024", "unit": "per1000"},
    1657: {"key": "emergencyAccess", "period": "2025", "unit": "per100"},
    1425: {"key": "specialistVisits7Psr", "period": "2025", "unit": "per1000"},
    1325: {"key": "diagnosticImagingServices", "period": "2025", "unit": "per1000"},
    260: {"key": "elderlyHomeCare", "period": "2024", "unit": "per1000"},
}

TARGET_CODES = set(ars.TOWNS) | {"90"}


def clean(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def source_value(row: dict[str, str]) -> dict:
    return {
        "den": ars.parse_num(row.get("den"), True),
        "num": ars.parse_num(row.get("num"), True),
        "raw": ars.parse_num(row.get("misura_grezza")),
        "standardized": ars.parse_num(row.get("misura_standardizzata")),
        "ci95Low": ars.parse_num(row.get("liminf")),
        "ci95High": ars.parse_num(row.get("limsup")),
    }


def main() -> int:
    out = {
        "schemaVersion": 1,
        "release": "v1.40.0",
        "publisher": "ARS Toscana",
        "geography": {
            "municipalities": {code: name for code, name in ars.TOWNS.items() if code != "202M"},
            "versilia": {"code": "202M", "label": "Zona Versilia"},
            "tuscany": {"code": "90", "label": "Regione Toscana"},
        },
        "indicators": {},
    }

    for iid, spec in SPECS.items():
        payload = ars.csv_bytes_from_export(iid)
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        required = {
            "id_indicatore", "anno", "codice_geografia", "geografia", "sesso",
            "strato1", "strato2", "den", "num", "misura_grezza",
            "misura_standardizzata", "liminf", "limsup",
        }
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"ARS {iid}: schema inatteso: {reader.fieldnames}")

        selected = []
        for row in reader:
            if str(row.get("id_indicatore") or "").strip() != str(iid):
                continue
            if str(row.get("anno") or "").strip() != spec["period"]:
                continue
            code = str(row.get("codice_geografia") or "").strip()
            if code not in TARGET_CODES:
                continue
            selected.append({
                "geoCode": code,
                "geography": clean(row.get("geografia")),
                "period": spec["period"],
                "sex": clean(row.get("sesso")),
                "strato1": clean(row.get("strato1")),
                "strato2": clean(row.get("strato2")),
                **source_value(row),
            })

        if not selected:
            raise RuntimeError(f"ARS {iid} {spec['key']}: nessuna riga per {spec['period']}")

        municipality_codes = {
            row["geoCode"] for row in selected
            if row["geoCode"] not in {"202M", "90"}
        }
        expected_municipalities = set(ars.TOWNS) - {"202M"}
        if municipality_codes != expected_municipalities:
            raise RuntimeError(
                f"ARS {iid} {spec['key']}: copertura comuni inattesa: "
                f"{sorted(municipality_codes)}"
            )
        if not any(row["geoCode"] == "202M" for row in selected):
            raise RuntimeError(f"ARS {iid} {spec['key']}: manca Zona Versilia 202M")
        if not any(row["geoCode"] == "90" for row in selected):
            raise RuntimeError(f"ARS {iid} {spec['key']}: manca Regione Toscana 90")

        sexes = sorted({row["sex"] for row in selected if row["sex"]}, key=str.casefold)
        strata1 = sorted({row["strato1"] for row in selected if row["strato1"]}, key=str.casefold)
        strata2 = sorted({row["strato2"] for row in selected if row["strato2"]}, key=str.casefold)
        out["indicators"][str(iid)] = {
            **spec,
            "indicatorId": iid,
            "exportUrl": f"https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={iid}",
            "sourceSha256": hashlib.sha256(payload).hexdigest(),
            "sexValues": sexes,
            "strato1Values": strata1,
            "strato2Values": strata2,
            "rows": selected,
        }
        print(
            f"ARS {iid} {spec['key']}: {len(selected)} righe · "
            f"sesso={sexes or ['<vuoto>']} · strato1={strata1 or ['<vuoto>']}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Snapshot demografico Salute pronto per revisione:", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
