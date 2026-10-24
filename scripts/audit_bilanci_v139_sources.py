#!/usr/bin/env python3
"""Source-only audit for Bilanci v1.39.0.

This script MUST NOT mutate canonical site data. It probes the official OpenBDAP
Rendiconto 2025 archives and the already-versioned SIOPE 2025 resources used by
v1.6.0, then writes a JSON audit report.

Hard gates:
- 7/7 municipal rows for Missions 01, 08, 11, 14, 17;
- explicit numeric `Impegni` for every selected mission row;
- 7/7 PDI 3.1 and 3.2 rows with explicit numeric values;
- one unambiguous FCDE row in Allegato A for every municipality.

The art. 195 TUEL SIOPE flows are audited but are deliberately NOT a hard gate:
if they are absent or uninformative the public metric must simply omit that
selector rather than manufacture a proxy.
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
SIOPE_SNAPSHOT = ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json"
BASE = "https://openbdap.rgs.mef.gov.it"
PORTAL_URL = BASE + "/it/FET/Analizza"
TIMEOUT = 240

TOWNS = {
    "Camaiore": "005",
    "Forte dei Marmi": "013",
    "Massarosa": "018",
    "Pietrasanta": "024",
    "Seravezza": "028",
    "Stazzema": "030",
    "Viareggio": "033",
}
PROVINCE = "046"
MISSION_CODES = ("01", "08", "11", "14", "17")
PDI_CODES = (("03", "01"), ("03", "02"))

ARCHIVES = {
    "schemi": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "indicatori": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Piano degli indicatori_TOSCANA.zip",
}
MEMBER_MISSIONS = "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv"
MEMBER_RESULT = "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv"
MEMBER_PDI = "Rendiconto PDI Sintetici Allegato 2-a_TOSCANA.csv"

ART195 = {
    "entrata": {
        "E.9.01.99.06.001": "Destinazione incassi vincolati a spese correnti ai sensi dell'art. 195 TUEL",
        "E.9.01.99.06.002": "Reintegro incassi vincolati ai sensi dell'art. 195 TUEL",
    },
    "spesa": {
        "U.7.01.99.06.001": "Utilizzo incassi vincolati ai sensi dell'art. 195 TUEL",
        "U.7.01.99.06.002": "Destinazione incassi liberi al reintegro incassi vincolati",
    },
}


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_number(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    # OpenBDAP CSV values are normally machine decimals. Keep handling narrow:
    # only a comma-only decimal notation is normalized, thousands separators are
    # not guessed.
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def download(session: requests.Session, path: str) -> tuple[bytes, str]:
    url = BASE + quote(path, safe="/:_-.")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content, response.url


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def find_member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    matches = [item for item in archive.infolist() if item.filename.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one member ending in {suffix!r}, got {len(matches)}")
    return matches[0]


def read_csv_member(archive: zipfile.ZipFile, suffix: str) -> tuple[list[dict[str, str]], dict]:
    info = find_member(archive, suffix)
    raw = archive.read(info)
    reader = csv.DictReader(io.StringIO(decode(raw)), delimiter=";")
    rows = [{k: v for k, v in row.items() if k and k.strip()} for row in reader]
    return rows, {
        "name": info.filename,
        "bytes": info.file_size,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "headers": list(reader.fieldnames or []),
    }


def town_for_row(row: dict[str, str]) -> str | None:
    if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
        return None
    if (row.get("Codice Provincia") or "").strip().zfill(3) != PROVINCE:
        return None
    code = (row.get("Codice Comune") or "").strip().zfill(3)
    for town, expected in TOWNS.items():
        if code == expected:
            return town
    return None


def filter_towns(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = {town: [] for town in TOWNS}
    for row in rows:
        town = town_for_row(row)
        if town:
            grouped[town].append(row)
    return grouped


def audit_missions(rows: list[dict[str, str]]) -> dict:
    grouped = filter_towns(rows)
    result: dict[str, dict] = {}
    failures: list[str] = []
    for town, town_rows in grouped.items():
        by_code: dict[str, list[dict[str, str]]] = {}
        for row in town_rows:
            code = (row.get("Codice Missione") or "").strip().zfill(2)
            if code in MISSION_CODES:
                by_code.setdefault(code, []).append(row)
        result[town] = {}
        for code in MISSION_CODES:
            matches = by_code.get(code, [])
            if len(matches) != 1:
                result[town][code] = {"status": "missing" if not matches else "duplicate", "rows": len(matches)}
                failures.append(f"mission {code} {town}: expected 1 row, got {len(matches)}")
                continue
            raw = matches[0].get("Impegni")
            value = parse_number(raw)
            if value is None:
                result[town][code] = {"status": "not_available", "raw": raw}
                failures.append(f"mission {code} {town}: Impegni is blank/non-numeric")
                continue
            result[town][code] = {
                "status": "zero" if value == 0 else "value",
                "impegni": value,
                "raw": raw,
            }
    return {"towns": result, "failures": failures, "coverage": f"{7 - len({x.split()[2] for x in failures if len(x.split()) > 2})}/7" if failures else "7/7"}


def audit_pdi(rows: list[dict[str, str]]) -> dict:
    grouped = filter_towns(rows)
    result: dict[str, dict] = {}
    failures: list[str] = []
    for town, town_rows in grouped.items():
        index: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in town_rows:
            key = (
                (row.get("Codice Tipologia Indicatore Sintetico 2)a") or "").strip().zfill(2),
                (row.get("Codice Indicatore Sintetico 2)a") or "").strip().zfill(2),
            )
            if key in PDI_CODES:
                index.setdefault(key, []).append(row)
        result[town] = {}
        for key in PDI_CODES:
            code = f"{int(key[0])}.{int(key[1])}"
            matches = index.get(key, [])
            if len(matches) != 1:
                result[town][code] = {"status": "missing" if not matches else "duplicate", "rows": len(matches)}
                failures.append(f"PDI {code} {town}: expected 1 row, got {len(matches)}")
                continue
            raw = matches[0].get("Indicatore Tutte Le Missioni")
            value = parse_number(raw)
            if value is None:
                result[town][code] = {"status": "not_available", "raw": raw}
                failures.append(f"PDI {code} {town}: value is blank/non-numeric")
                continue
            result[town][code] = {"status": "zero" if value == 0 else "value", "value": value, "raw": raw}
    return {"towns": result, "failures": failures, "coverage": "7/7" if not failures else "incomplete"}


def audit_fcde(result_rows: list[dict[str, str]], archive: zipfile.ZipFile) -> dict:
    grouped = filter_towns(result_rows)
    output: dict[str, dict] = {}
    failures: list[str] = []
    for town, rows in grouped.items():
        matches = []
        for row in rows:
            haystack = " | ".join(normalize(value) for value in row.values())
            if "fondo crediti" in haystack and "dubbia esigibilita" in haystack:
                matches.append(row)
        if len(matches) != 1:
            output[town] = {"status": "missing" if not matches else "ambiguous", "rows": len(matches)}
            failures.append(f"FCDE {town}: expected 1 Allegato A row, got {len(matches)}")
            continue
        row = matches[0]
        raw = row.get("Totale di Gestione")
        value = parse_number(raw)
        if value is None:
            # Preserve row evidence rather than guessing another numeric column.
            output[town] = {"status": "not_available", "row": row}
            failures.append(f"FCDE {town}: Totale di Gestione blank/non-numeric")
            continue
        output[town] = {
            "status": "zero" if value == 0 else "value",
            "value": value,
            "raw": raw,
            "row_code": row.get("Cod Voce Ris Amm Rend"),
            "row_description": next((v for v in row.values() if "dubbia esigibilita" in normalize(v)), None),
        }

    # Discovery evidence for the reconciliation step: never infer a total from
    # unknown columns. We only expose the relevant official members and let the
    # materializer use an exact field once this audit has identified it.
    related_members = []
    for item in archive.infolist():
        name = normalize(item.filename)
        if item.filename.lower().endswith(".csv") and (
            "accanton" in name or "dubbia" in name or "allegato a" in name or "allegato c" in name
        ):
            related_members.append(item.filename)

    return {
        "towns": output,
        "failures": failures,
        "coverage": "7/7" if not failures else "incomplete",
        "reconciliation_candidate_members": sorted(related_members),
    }


def siope_resource(snapshot: dict, kind: str) -> dict:
    key = f"{kind}-2025-toscana"
    resource = snapshot.get("source", {}).get("resources", {}).get(key)
    if not resource:
        raise RuntimeError(f"Versioned SIOPE resource missing: {key}")
    return resource


def normalize_istat_commune(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) >= 6:
        return digits[-6:]
    if len(digits) == 3:
        return PROVINCE + digits
    return digits.zfill(6) if digits else ""


def audit_siope_dump(session: requests.Session, resource: dict, kind: str) -> dict:
    url = resource["url"]
    response = session.get(url, timeout=TIMEOUT, stream=True)
    response.raise_for_status()
    response.raw.decode_content = True
    wrapper = io.TextIOWrapper(response.raw, encoding="cp1252", errors="replace", newline="")
    reader = csv.DictReader(wrapper, delimiter=";")
    wanted = ART195[kind]
    seen_entities = {town: False for town in TOWNS}
    latest: dict[str, dict[str, dict]] = {town: {} for town in TOWNS}
    code_to_town = {PROVINCE + code: town for town, code in TOWNS.items()}

    for row in reader:
        commune = normalize_istat_commune(row.get("Codice istat comune"))
        town = code_to_town.get(commune)
        if not town:
            continue
        # The resource is Tuscany-wide. Presence of any row proves the entity is
        # represented; absence of a specific transaction code can then be
        # reported distinctly from an absent municipality.
        seen_entities[town] = True
        detail = (row.get("Codice Gestionale Enti Locali") or "").strip()
        if detail not in wanted:
            continue
        month = str(row.get("Anno/Mese calendario") or "").strip()
        amount = parse_number(row.get("Importo cumulato"))
        current = latest[town].get(detail)
        if current is None or month > current["month"]:
            latest[town][detail] = {
                "month": month,
                "amount": amount,
                "description": row.get("Descrizione CG"),
                "movement": row.get("Tipologia del Movimento"),
            }

    towns = {}
    for town in TOWNS:
        towns[town] = {"entity_present": seen_entities[town], "flows": {}}
        for code, label in wanted.items():
            hit = latest[town].get(code)
            if hit:
                towns[town]["flows"][code] = {"status": "row", "label": label, **hit}
            elif seen_entities[town]:
                towns[town]["flows"][code] = {
                    "status": "no_transaction_row",
                    "label": label,
                    "amount": 0.0,
                    "zero_policy": "reconstructed only because the municipality is present in the same official transaction resource",
                }
            else:
                towns[town]["flows"][code] = {"status": "municipality_absent", "label": label, "amount": None}

    return {
        "resource_id": resource.get("package_id"),
        "url": url,
        "versioned_sha256": resource.get("sha256"),
        "versioned_bytes": resource.get("bytes"),
        "headers": list(reader.fieldnames or []),
        "towns": towns,
        "coverage": f"{sum(seen_entities.values())}/7",
    }


def summarize_art195(siope: dict) -> dict:
    use_code = "U.7.01.99.06.001"
    reintegrate_code = "E.9.01.99.06.002"
    use_values = {}
    reintegration_values = {}
    for town in TOWNS:
        use_values[town] = siope["spesa"]["towns"][town]["flows"][use_code]["amount"]
        reintegration_values[town] = siope["entrata"]["towns"][town]["flows"][reintegrate_code]["amount"]
    nonzero_use = [town for town, value in use_values.items() if value not in (None, 0, 0.0)]
    return {
        "use_values_2025": use_values,
        "reintegration_values_2025": reintegration_values,
        "nonzero_use_towns": nonzero_use,
        "recommendation": (
            "eligible_for_history_probe" if nonzero_use else
            "omit_public_selector_unless_an_earlier-year_history_probe_shows_material_use"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/bilanci-v139-source-audit.json")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.39-source-audit (+https://emanzi3.github.io/osservatorio-versilia/)",
        "Accept": "*/*",
    })

    downloaded = {name: download(session, path) for name, path in ARCHIVES.items()}
    schemes_raw, schemes_url = downloaded["schemi"]
    pdi_raw, pdi_url = downloaded["indicatori"]

    with zipfile.ZipFile(io.BytesIO(schemes_raw)) as archive:
        mission_rows, mission_meta = read_csv_member(archive, MEMBER_MISSIONS)
        result_rows, result_meta = read_csv_member(archive, MEMBER_RESULT)
        missions = audit_missions(mission_rows)
        fcde = audit_fcde(result_rows, archive)
        scheme_members = [item.filename for item in archive.infolist()]

    with zipfile.ZipFile(io.BytesIO(pdi_raw)) as archive:
        pdi_rows, pdi_meta = read_csv_member(archive, MEMBER_PDI)
        pdi = audit_pdi(pdi_rows)

    siope_snapshot = json.loads(SIOPE_SNAPSHOT.read_text(encoding="utf-8"))
    siope = {
        "entrata": audit_siope_dump(session, siope_resource(siope_snapshot, "entrata"), "entrata"),
        "spesa": audit_siope_dump(session, siope_resource(siope_snapshot, "spesa"), "spesa"),
    }
    art195 = summarize_art195(siope)

    hard_failures = missions["failures"] + pdi["failures"] + fcde["failures"]
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Bilanci v1.39 source-only gate; no canonical data mutation",
        "baseline": "2592a4694c89fc80f30fd643e0efc6acb67e30d5",
        "official_sources": {
            "openbdap_portal": PORTAL_URL,
            "schemi": {
                "url": schemes_url,
                "sha256": hashlib.sha256(schemes_raw).hexdigest(),
                "bytes": len(schemes_raw),
                "members": scheme_members,
                "selected": {"missions": mission_meta, "result": result_meta},
            },
            "pdi": {
                "url": pdi_url,
                "sha256": hashlib.sha256(pdi_raw).hexdigest(),
                "bytes": len(pdi_raw),
                "selected": pdi_meta,
            },
            "siope": {
                "publisher": siope_snapshot.get("source", {}).get("publisher"),
                "catalogue_api": siope_snapshot.get("source", {}).get("catalogue_api"),
            },
        },
        "missions_2025": missions,
        "pdi_liquidity_2025": pdi,
        "fcde_2025": fcde,
        "siope_art195_2025": siope,
        "art195_decision_support": art195,
        "hard_failures": hard_failures,
        "hard_gate": "PASS" if not hard_failures else "FAIL",
    }

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "hard_gate": report["hard_gate"],
        "missions": missions["coverage"],
        "pdi": pdi["coverage"],
        "fcde": fcde["coverage"],
        "siope_entrata": siope["entrata"]["coverage"],
        "siope_spesa": siope["spesa"]["coverage"],
        "art195_nonzero_use_towns": art195["nonzero_use_towns"],
        "output": str(output.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))

    if hard_failures:
        for failure in hard_failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
