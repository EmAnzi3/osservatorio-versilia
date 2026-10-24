#!/usr/bin/env python3
"""Fail-closed source probe for Bilanci v1.39.0.

Reads official OpenBDAP Rendiconto 2025 archives and queries the same versioned
BDAP/SIOPE DataStore resources already used by v1.6.0. It writes an audit JSON
only; it never mutates canonical site data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
SIOPE_SNAPSHOT = ROOT / "data/source-snapshots/siope-history-v1.6.0.json"
BASE = "https://openbdap.rgs.mef.gov.it"
CKAN_ACTION = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action/datastore_search"
TIMEOUT = 240

TOWNS = {
    "Camaiore": "005", "Forte dei Marmi": "013", "Massarosa": "018",
    "Pietrasanta": "024", "Seravezza": "028", "Stazzema": "030", "Viareggio": "033",
}
PROVINCE = "046"
MISSIONS = ("01", "08", "11", "14", "17")
PDI = (("03", "01"), ("03", "02"))

SCHEMI_PATH = "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip"
PDI_PATH = "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Piano degli indicatori_TOSCANA.zip"
MISSION_MEMBER = "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv"
RESULT_MEMBER = "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv"
PDI_MEMBER = "Rendiconto PDI Sintetici Allegato 2-a_TOSCANA.csv"

ART195 = {
    "entrata": ("E.9.01.99.06.001", "E.9.01.99.06.002"),
    "spesa": ("U.7.01.99.06.001", "U.7.01.99.06.002"),
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def num(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def get_zip(session: requests.Session, path: str) -> tuple[bytes, str]:
    url = BASE + quote(path, safe="/:_-.")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content, response.url


def member(archive: zipfile.ZipFile, suffix: str) -> tuple[list[dict[str, str]], dict]:
    hits = [x for x in archive.infolist() if x.filename.endswith(suffix)]
    if len(hits) != 1:
        raise RuntimeError(f"{suffix}: expected one member, got {len(hits)}")
    info = hits[0]
    raw = archive.read(info)
    reader = csv.DictReader(io.StringIO(decode(raw)), delimiter=";")
    rows = [{k: v for k, v in row.items() if k and k.strip()} for row in reader]
    return rows, {
        "name": info.filename,
        "bytes": info.file_size,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "headers": list(reader.fieldnames or []),
    }


def town(row: dict[str, str]) -> str | None:
    if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
        return None
    if (row.get("Codice Provincia") or "").strip().zfill(3) != PROVINCE:
        return None
    code = (row.get("Codice Comune") or "").strip().zfill(3)
    return next((name for name, expected in TOWNS.items() if code == expected), None)


def grouped(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out = {name: [] for name in TOWNS}
    for row in rows:
        name = town(row)
        if name:
            out[name].append(row)
    return out


def mission_audit(rows: list[dict[str, str]]) -> tuple[dict, list[str]]:
    out, failures = {}, []
    for name, items in grouped(rows).items():
        out[name] = {}
        for code in MISSIONS:
            hits = [r for r in items if (r.get("Codice Missione") or "").strip().zfill(2) == code]
            if len(hits) != 1:
                out[name][code] = {"status": "absent" if not hits else "duplicate", "rows": len(hits)}
                failures.append(f"M{code} {name}: rows={len(hits)}")
                continue
            raw = hits[0].get("Impegni")
            value = num(raw)
            if value is None:
                out[name][code] = {"status": "n.d.", "raw": raw}
                failures.append(f"M{code} {name}: Impegni blank/non-numeric")
            else:
                out[name][code] = {"status": "zero" if value == 0 else "value", "impegni": value, "raw": raw}
    return out, failures


def pdi_audit(rows: list[dict[str, str]]) -> tuple[dict, list[str]]:
    out, failures = {}, []
    for name, items in grouped(rows).items():
        out[name] = {}
        for typ, ind in PDI:
            label = f"{int(typ)}.{int(ind)}"
            hits = [r for r in items if
                    (r.get("Codice Tipologia Indicatore Sintetico 2)a") or "").strip().zfill(2) == typ and
                    (r.get("Codice Indicatore Sintetico 2)a") or "").strip().zfill(2) == ind]
            if len(hits) != 1:
                out[name][label] = {"status": "absent" if not hits else "duplicate", "rows": len(hits)}
                failures.append(f"PDI {label} {name}: rows={len(hits)}")
                continue
            raw = hits[0].get("Indicatore Tutte Le Missioni")
            value = num(raw)
            if value is None:
                out[name][label] = {"status": "n.d.", "raw": raw}
                failures.append(f"PDI {label} {name}: value blank/non-numeric")
            else:
                out[name][label] = {"status": "zero" if value == 0 else "value", "value": value, "raw": raw}
    return out, failures


def fcde_audit(rows: list[dict[str, str]], archive: zipfile.ZipFile) -> tuple[dict, list[str], list[str]]:
    out, failures = {}, []
    for name, items in grouped(rows).items():
        hits = []
        for row in items:
            haystack = " | ".join(norm(v) for v in row.values())
            if "fondo crediti" in haystack and "dubbia esigibilita" in haystack:
                hits.append(row)
        if len(hits) != 1:
            out[name] = {"status": "absent" if not hits else "ambiguous", "rows": len(hits)}
            failures.append(f"FCDE {name}: rows={len(hits)}")
            continue
        row = hits[0]
        raw = row.get("Totale di Gestione")
        value = num(raw)
        if value is None:
            out[name] = {"status": "n.d.", "row": row}
            failures.append(f"FCDE {name}: Totale di Gestione blank/non-numeric")
        else:
            out[name] = {
                "status": "zero" if value == 0 else "value",
                "value": value,
                "raw": raw,
                "row_code": row.get("Cod Voce Ris Amm Rend"),
                "row_description": next((v for v in row.values() if "dubbia esigibilita" in norm(v)), None),
            }
    related = [x.filename for x in archive.infolist() if x.filename.lower().endswith(".csv") and
               any(token in norm(x.filename) for token in ("accanton", "dubbia", "allegato a", "allegato c"))]
    return out, failures, sorted(related)


def ckan_records(session: requests.Session, resource_id: str, codes: tuple[str, ...]) -> list[dict]:
    response = session.get(CKAN_ACTION, params={
        "resource_id": resource_id,
        "limit": 32000,
        "filters": json.dumps({"Codice Gestionale Enti Locali": list(codes)}, ensure_ascii=False),
    }, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN datastore_search unsuccessful: {payload}")
    result = payload.get("result", {})
    if result.get("records_truncated"):
        raise RuntimeError("CKAN art.195 query truncated")
    return result.get("records", [])


def istat_code(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) >= 6:
        return digits[-6:]
    if len(digits) == 3:
        return PROVINCE + digits
    return digits.zfill(6) if digits else ""


def siope_art195(session: requests.Session, snapshot: dict, kind: str) -> dict:
    resource = snapshot["source"]["resources"][f"{kind}-2025-toscana"]
    records = ckan_records(session, resource["package_id"], ART195[kind])
    by_code = {PROVINCE + code: name for name, code in TOWNS.items()}
    latest = {name: {} for name in TOWNS}
    for row in records:
        name = by_code.get(istat_code(row.get("Codice istat comune")))
        if not name:
            continue
        detail = str(row.get("Codice Gestionale Enti Locali") or "").strip()
        month = str(row.get("Anno/Mese calendario") or "").strip()
        current = latest[name].get(detail)
        if current is None or month > current["month"]:
            latest[name][detail] = {
                "month": month,
                "amount": num(row.get("Importo cumulato")),
                "description": row.get("Descrizione CG"),
                "movement": row.get("Tipologia del Movimento"),
            }
    towns = {}
    raw_presence = snapshot.get("raw", {})
    for name in TOWNS:
        present = name in raw_presence and "2025" in raw_presence[name]
        towns[name] = {"entity_present_in_versioned_snapshot": present, "flows": {}}
        for code in ART195[kind]:
            if code in latest[name]:
                towns[name]["flows"][code] = {"status": "row", **latest[name][code]}
            elif present:
                towns[name]["flows"][code] = {
                    "status": "no_transaction_row",
                    "amount": 0.0,
                    "zero_policy": "entity present in the same versioned 2025 SIOPE source; no matching transaction row",
                }
            else:
                towns[name]["flows"][code] = {"status": "entity_absent", "amount": None}
    return {
        "resource_id": resource["package_id"],
        "url": resource["url"],
        "versioned_sha256": resource.get("sha256"),
        "query_records": len(records),
        "towns": towns,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/bilanci-v139-source-audit.json")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "OsservatorioVersilia/1.39-source-gate"
    schemes_raw, schemes_url = get_zip(session, SCHEMI_PATH)
    pdi_raw, pdi_url = get_zip(session, PDI_PATH)

    with zipfile.ZipFile(io.BytesIO(schemes_raw)) as archive:
        mission_rows, mission_meta = member(archive, MISSION_MEMBER)
        result_rows, result_meta = member(archive, RESULT_MEMBER)
        missions, mission_failures = mission_audit(mission_rows)
        fcde, fcde_failures, fcde_members = fcde_audit(result_rows, archive)

    with zipfile.ZipFile(io.BytesIO(pdi_raw)) as archive:
        pdi_rows, pdi_meta = member(archive, PDI_MEMBER)
        liquidity, pdi_failures = pdi_audit(pdi_rows)

    siope_snapshot = json.loads(SIOPE_SNAPSHOT.read_text(encoding="utf-8"))
    siope_error = None
    try:
        art195 = {
            "entrata": siope_art195(session, siope_snapshot, "entrata"),
            "spesa": siope_art195(session, siope_snapshot, "spesa"),
        }
    except Exception as exc:  # optional candidate: report gap, do not weaken hard OpenBDAP gate
        art195 = None
        siope_error = f"{type(exc).__name__}: {exc}"

    hard_failures = mission_failures + pdi_failures + fcde_failures
    report = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": "2592a4694c89fc80f30fd643e0efc6acb67e30d5",
        "scope": "source-only; no canonical mutation",
        "sources": {
            "schemi": {"url": schemes_url, "sha256": hashlib.sha256(schemes_raw).hexdigest(), "bytes": len(schemes_raw), "selected": {"missions": mission_meta, "result": result_meta}},
            "pdi": {"url": pdi_url, "sha256": hashlib.sha256(pdi_raw).hexdigest(), "bytes": len(pdi_raw), "selected": pdi_meta},
            "siope": {"catalogue_api": siope_snapshot["source"]["catalogue_api"]},
        },
        "missions_2025": missions,
        "pdi_3_1_3_2_2025": liquidity,
        "fcde_2025": {"towns": fcde, "reconciliation_candidate_members": fcde_members},
        "siope_art195_2025": art195,
        "siope_art195_error": siope_error,
        "hard_failures": hard_failures,
        "hard_gate": "PASS" if not hard_failures else "FAIL",
    }

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    nonzero_art195 = []
    if art195:
        for name in TOWNS:
            value = art195["spesa"]["towns"][name]["flows"]["U.7.01.99.06.001"]["amount"]
            if value not in (None, 0, 0.0):
                nonzero_art195.append(name)

    print(json.dumps({
        "hard_gate": report["hard_gate"],
        "mission_failures": mission_failures,
        "pdi_failures": pdi_failures,
        "fcde_failures": fcde_failures,
        "art195_query_error": siope_error,
        "art195_nonzero_use_towns_2025": nonzero_art195,
        "output": str(output.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))

    if hard_failures:
        for failure in hard_failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
