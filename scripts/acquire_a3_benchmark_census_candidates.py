#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
GOVERNED = ROOT / "data" / "source-snapshots" / "istat-sections-history-v1.8.0.json"
SITE_DATA = ROOT / "data" / "site-data.json"
LOCAL_2024 = ROOT / "data" / "source-snapshots" / "istat-lavoro-istruzione-eta-genere-2024.json"
SDMX_BASE = "https://esploradati.istat.it/SDMXWS/rest"
SDMX_FLOWS = {"labour": "DF_DCSS_ISTR_LAV_PEN_2_TV_3", "education": "DF_DCSS_ISTR_LAV_PEN_2_TV_1"}
RESIDUAL_2024 = {"activityRate", "employmentRate", "unemploymentRate", "tertiary"}

URL = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
YEAR = "2023"

BASE_FIELDS = ["P1", "P102", "P103", "PF1", "PF3", "PF9", "A3", "A8"]
MALE_FIELDS = [f"P{i}" for i in range(33, 43)]
FEMALE_FIELDS = [f"P{i}" for i in range(70, 80)]
REQUIRED_FIELDS = BASE_FIELDS + MALE_FIELDS + FEMALE_FIELDS

METRICS = {
    "femaleEmploymentRate": ("P103", "female1564", 100.0, "percent"),
    "maleEmploymentRate": ("P102", "male1564", 100.0, "percent"),
    "housingStockPer1000": ("A8", "P1", 1000.0, "per1000"),
    "nonOccupiedHomesPer1000": ("A3", "P1", 1000.0, "per1000"),
    "vacantHomes": ("A3", "A8", 100.0, "percent"),
    "singleHouseholds": ("PF3", "PF1", 100.0, "percent"),
    "cohabitingHouseholds": ("PF9", "PF1", 100.0, "percent"),
}

MUNICIPALITY_HEADER_KEYS = {
    "PROCOM", "PROCOMT", "CODCOM", "CODICECOMUNE", "CODCOMUNE",
    "PROCOMUNE", "CODICEISTATCOMUNE",
}


def norm_header(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def code6(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return f"{value:06d}"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):06d}"
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    return digits.zfill(6) if 1 <= len(digits) <= 6 else ""


def number(value: Any, label: str) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, bool):
        raise RuntimeError(f"{label}: booleano inatteso")
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        s = str(value).strip().replace(" ", "").replace(",", ".")
        try:
            result = float(s)
        except ValueError as exc:
            raise RuntimeError(f"{label}: valore non numerico {value!r}") from exc
    if not math.isfinite(result) or result < 0:
        raise RuntimeError(f"{label}: valore invalido {value!r}")
    return result


def find_header(ws) -> tuple[int, dict[str, int], list[Any]]:
    required = set(REQUIRED_FIELDS)
    for row_no, row in enumerate(ws.iter_rows(min_row=1, max_row=30, values_only=True), 1):
        normalized = [norm_header(v) for v in row]
        positions = {name: idx for idx, name in enumerate(normalized) if name}
        if required.issubset(positions):
            return row_no, positions, list(row)
    raise RuntimeError("Header censuario con variabili richieste non trovato nelle prime 30 righe")


def municipality_column(positions: dict[str, int]) -> int:
    candidates = [(name, idx) for name, idx in positions.items() if name in MUNICIPALITY_HEADER_KEYS]
    if len(candidates) == 1:
        return candidates[0][1]
    if candidates:
        # PRO_COM è il contratto storico più comune; preferiscilo se presente.
        for name, idx in candidates:
            if name == "PROCOM":
                return idx
    raise RuntimeError(f"Colonna codice Comune non individuata; header candidati={candidates}")


def empty_totals() -> dict[str, float]:
    return {field: 0.0 for field in REQUIRED_FIELDS}


def add_row(target: dict[str, float], row: tuple[Any, ...], positions: dict[str, int], label: str) -> None:
    for field in REQUIRED_FIELDS:
        idx = positions[field]
        value = row[idx] if idx < len(row) else None
        target[field] += number(value, f"{label}/{field}")


def finalize(raw: dict[str, float]) -> dict[str, float]:
    out = {k: float(v) for k, v in raw.items()}
    out["male1564"] = sum(out[f"P{i}"] for i in range(33, 43))
    out["female1564"] = sum(out[f"P{i}"] for i in range(70, 80))
    return out


def parse_workbook(blob: bytes, member: str, town_codes: set[str] | None = None):
    wb = load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]
        header_row, positions, headers = find_header(ws)
        mun_idx = municipality_column(positions)

        total = empty_totals()
        towns: dict[str, dict[str, float]] = defaultdict(empty_totals)
        rows = 0
        matched_rows = 0

        for row_no, row in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            if not row or all(v in (None, "") for v in row):
                continue
            add_row(total, row, positions, f"{member}:r{row_no}")
            rows += 1
            if town_codes:
                code = code6(row[mun_idx] if mun_idx < len(row) else None)
                if code in town_codes:
                    add_row(towns[code], row, positions, f"{member}:{code}:r{row_no}")
                    matched_rows += 1

        if rows <= 0:
            raise RuntimeError(f"{member}: nessuna riga dati")
        return finalize(total), {k: finalize(v) for k, v in towns.items()}, {
            "sheet": ws.title,
            "headerRow": header_row,
            "rows": rows,
            "matchedTownRows": matched_rows,
            "municipalityHeader": headers[mun_idx] if mun_idx < len(headers) else None,
            "headersRequired": {field: headers[positions[field]] for field in REQUIRED_FIELDS},
        }
    finally:
        wb.close()


def ratio(raw: dict[str, float], numerator: str, denominator: str, scale: float) -> float:
    den = raw[denominator]
    if den <= 0:
        raise RuntimeError(f"Denominatore nullo per {numerator}/{denominator}")
    return raw[numerator] / den * scale


def reconcile_public_2023(
    towns: dict[str, dict[str, float]],
    site: dict[str, Any],
    governed: dict[str, Any],
) -> dict[str, Any]:
    code_to_town = {
        str(row["code"]): str(row["town"])
        for row in ((governed.get("raw") or {}).get(YEAR) or [])
        if isinstance(row, dict) and row.get("code") and row.get("town")
    }
    errors: list[str] = []
    tolerances = {
        "vacantHomes": 0.051,
        "singleHouseholds": 0.051,
        "cohabitingHouseholds": 1e-9,
        "employmentGenderGap": 1e-9,
    }

    expected_specs = {
        **METRICS,
        "employmentGenderGap": (None, None, None, "percentagePoints"),
    }

    metrics = site.get("metrics") or {}
    for metric_id, spec in expected_specs.items():
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            errors.append(f"{metric_id}: metrica pubblica mancante")
            continue
        meta = metric.get("meta") or {}
        if str(meta.get("year")) != YEAR:
            errors.append(f"{metric_id}: anno pubblico {meta.get('year')!r} != {YEAR}")
        if str(meta.get("unit")) != spec[3]:
            errors.append(f"{metric_id}: unità pubblica {meta.get('unit')!r} != {spec[3]!r}")

        rows = {
            str(row.get("town")): row
            for row in (metric.get("rows") or [])
            if isinstance(row, dict) and row.get("town")
        }
        if set(rows) != set(code_to_town.values()):
            errors.append(f"{metric_id}: perimetro pubblico non 7/7")
            continue

        for code, town_name in code_to_town.items():
            raw = towns.get(code)
            if raw is None:
                errors.append(f"{metric_id}/{town_name}: componenti censuarie mancanti")
                continue
            if metric_id == "employmentGenderGap":
                male = ratio(raw, "P102", "male1564", 100.0)
                female = ratio(raw, "P103", "female1564", 100.0)
                expected = male - female
            else:
                num, den, scale, _unit = spec
                expected = ratio(raw, str(num), str(den), float(scale))
            observed = number(rows[town_name].get("value"), f"{metric_id}/{town_name}: valore pubblico")
            tolerance = tolerances.get(metric_id, 1e-6)
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=tolerance):
                errors.append(f"{metric_id}/{town_name}: {observed} != {expected}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "metrics": sorted(expected_specs),
        "towns": len(code_to_town),
        "errors": errors[:120],
    }


def compare_governed(towns: dict[str, dict[str, float]], governed: dict[str, Any]) -> dict[str, Any]:
    expected_rows = {
        str(row["code"]): row
        for row in ((governed.get("raw") or {}).get(YEAR) or [])
        if isinstance(row, dict) and row.get("code")
    }
    errors = []
    checks = ["P1", "P102", "P103", "PF1", "PF3", "A3", "A8", "male1564", "female1564"]
    for code, expected in expected_rows.items():
        got = towns.get(code)
        if got is None:
            errors.append(f"{code}: Comune non ricostruito")
            continue
        for field in checks:
            actual = got[field]
            wanted = float(expected[field])
            if not math.isclose(actual, wanted, rel_tol=0.0, abs_tol=1e-9):
                errors.append(f"{code}/{field}: {actual} != {wanted}")
    extras = sorted(set(towns) - set(expected_rows))
    if extras:
        errors.append(f"Codici Versilia inattesi: {extras}")
    return {
        "status": "PASS" if not errors and len(towns) == len(expected_rows) == 7 else "FAIL",
        "townsExpected": len(expected_rows),
        "townsReconstructed": len(towns),
        "errors": errors[:100],
    }



def sdmx_rows(session: requests.Session, flow: str, ref_area: str) -> list[dict[str, str]]:
    key = ".".join(["A", ref_area] + [""] * 8)
    url = f"{SDMX_BASE}/data/IT1,{flow},1.0/{key}/all"
    response = session.get(
        url,
        params={"startPeriod": "2024", "endPeriod": "2024", "format": "csvfile"},
        headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"},
        timeout=180,
    )
    if response.status_code >= 400:
        return []
    text = response.content.decode("utf-8-sig", errors="replace")
    import csv
    return list(csv.DictReader(io.StringIO(text)))


def aggregate_labour_2024(rows: list[dict[str, str]], ref_area: str) -> dict[str, float]:
    wanted_ages = {"Y25-49", "Y50-64"}
    cells: dict[str, float] = {}
    for row in rows:
        if row.get("REF_AREA") != ref_area:
            continue
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("CITIZENSHIP") != "TOTAL" or row.get("EDU_ATTAIN") != "ALL":
            continue
        if row.get("GENDER") != "T" or row.get("AGE_NOCLASS") not in wanted_ages:
            continue
        stat = row.get("CUR_ACT_STAT")
        if stat not in {"1", "12", "22", "99"}:
            continue
        key = f"{row['AGE_NOCLASS']}|{stat}"
        cells[key] = number(row.get("OBS_VALUE"), f"labour/{ref_area}/{key}")

    for age in wanted_ages:
        missing = {"1", "12", "22", "99"} - {k.split("|",1)[1] for k in cells if k.startswith(age+"|")}
        if missing:
            raise RuntimeError(f"labour/{ref_area}/{age}: celle mancanti {sorted(missing)}")
    pop = sum(cells[f"{age}|99"] for age in wanted_ages)
    employed = sum(cells[f"{age}|1"] for age in wanted_ages)
    unemployed = sum(cells[f"{age}|12"] for age in wanted_ages)
    active = sum(cells[f"{age}|22"] for age in wanted_ages)
    if not math.isclose(employed + unemployed, active, rel_tol=0.0, abs_tol=1e-6):
        raise RuntimeError(f"labour/{ref_area}: active mismatch")
    return {
        "population": pop,
        "employed": employed,
        "unemployed": unemployed,
        "active": active,
        "employmentRate": employed / pop * 100.0,
        "unemploymentRate": unemployed / active * 100.0,
        "activityRate": active / pop * 100.0,
    }


def aggregate_education_2024(rows: list[dict[str, str]], ref_area: str) -> dict[str, float]:
    wanted_ages = {"Y25-49", "Y50-64"}
    partition = ["NED", "PSE", "LSE", "USE_IF", "BL", "ML_RDD"]
    by_age: dict[str, dict[str, float]] = {age: {} for age in wanted_ages}
    for row in rows:
        if row.get("REF_AREA") != ref_area:
            continue
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("CITIZENSHIP") != "TOTAL" or row.get("CUR_ACT_STAT") != "99":
            continue
        if row.get("GENDER") != "T" or row.get("AGE_NOCLASS") not in wanted_ages:
            continue
        edu = row.get("EDU_ATTAIN")
        if edu not in {"ALL", *partition}:
            continue
        by_age[row["AGE_NOCLASS"]][edu] = number(row.get("OBS_VALUE"), f"education/{ref_area}/{row['AGE_NOCLASS']}/{edu}")

    population = 0.0
    tertiary = 0.0
    for age, vals in by_age.items():
        if "ALL" not in vals:
            raise RuntimeError(f"education/{ref_area}/{age}: ALL mancante")
        parts = sum(vals.get(k, 0.0) for k in partition)
        if not math.isclose(parts, vals["ALL"], rel_tol=0.0, abs_tol=1e-6):
            raise RuntimeError(f"education/{ref_area}/{age}: partition mismatch ALL={vals['ALL']} parts={parts}")
        population += vals["ALL"]
        tertiary += vals.get("BL", 0.0) + vals.get("ML_RDD", 0.0)
    if population <= 0:
        raise RuntimeError(f"education/{ref_area}: popolazione nulla")
    return {"population": population, "tertiary": tertiary, "tertiaryRate": tertiary / population * 100.0}


def reconcile_public_2024(site: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    mapping = {
        "employmentRate": ("labour", "employmentRate"),
        "unemploymentRate": ("labour", "unemploymentRate"),
        "activityRate": ("labour", "activityRate"),
        "tertiary": ("education", "tertiaryRate"),
    }
    towns = local.get("towns") or {}
    if len(towns) != 7:
        return {"status": "FAIL", "errors": ["snapshot 2024 non 7/7"]}
    for metric_id, (section, field) in mapping.items():
        metric = (site.get("metrics") or {}).get(metric_id) or {}
        meta = metric.get("meta") or {}
        if str(meta.get("year")) != "2024":
            errors.append(f"{metric_id}: anno pubblico {meta.get('year')!r} != 2024")
        rows = {str(r.get("town")): r for r in metric.get("rows") or [] if isinstance(r, dict) and r.get("town")}
        if set(rows) != set(towns):
            errors.append(f"{metric_id}: perimetro pubblico non 7/7")
            continue
        for town, raw in towns.items():
            expected = float(raw[section]["25-64"]["total"][field])
            observed = float(rows[town]["value"])
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=0.11):
                errors.append(f"{metric_id}/{town}: {observed} != {expected}")
    return {"status": "PASS" if not errors else "FAIL", "metrics": sorted(mapping), "towns": len(towns), "errors": errors[:100]}


TUSCANY_PROVINCE_PREFIXES = {"045", "046", "047", "048", "049", "050", "051", "052", "053", "100"}


def municipality_ref(value: Any) -> str:
    code = str(value or "").strip()
    return code if re.fullmatch(r"\d{6}", code) else ""


def is_tuscany_municipality(code: str) -> bool:
    return code[:3] in TUSCANY_PROVINCE_PREFIXES


def sdmx_filtered_all(session: requests.Session, flow: str, key: str) -> list[dict[str, str]]:
    url = f"{SDMX_BASE}/data/IT1,{flow},1.0/{key}/all"
    response = session.get(
        url,
        params={"startPeriod": "2024", "endPeriod": "2024", "format": "csvfile"},
        headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"},
        timeout=240,
    )
    response.raise_for_status()
    import csv
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig", errors="replace"))))


def aggregate_all_municipal_2024(session: requests.Session) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    labour_key = "A..RESPOP_AV.T.Y25-49+Y50-64.TOTAL.ALL.1+12+22+99.."
    education_key = "A..RESPOP_AV.T.Y25-49+Y50-64.TOTAL.BL+ML_RDD+ALL.99.."
    labour_rows = sdmx_filtered_all(session, SDMX_FLOWS["labour"], labour_key)
    education_rows = sdmx_filtered_all(session, SDMX_FLOWS["education"], education_key)

    labour_by: dict[str, dict[str, float]] = {}
    for row in labour_rows:
        code = municipality_ref(row.get("REF_AREA"))
        if not code:
            continue
        age = row.get("AGE_NOCLASS")
        stat = row.get("CUR_ACT_STAT")
        if age not in {"Y25-49", "Y50-64"} or stat not in {"1", "12", "22", "99"}:
            continue
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("GENDER") != "T" or row.get("CITIZENSHIP") != "TOTAL" or row.get("EDU_ATTAIN") != "ALL":
            continue
        labour_by.setdefault(code, {})[f"{age}|{stat}"] = number(row.get("OBS_VALUE"), f"labour/{code}/{age}/{stat}")

    education_by: dict[str, dict[str, float]] = {}
    for row in education_rows:
        code = municipality_ref(row.get("REF_AREA"))
        if not code:
            continue
        age = row.get("AGE_NOCLASS")
        edu = row.get("EDU_ATTAIN")
        if age not in {"Y25-49", "Y50-64"} or edu not in {"ALL", "BL", "ML_RDD"}:
            continue
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("GENDER") != "T" or row.get("CITIZENSHIP") != "TOTAL" or row.get("CUR_ACT_STAT") != "99":
            continue
        education_by.setdefault(code, {})[f"{age}|{edu}"] = number(row.get("OBS_VALUE"), f"education/{code}/{age}/{edu}")

    labour_required = {f"{age}|{stat}" for age in ("Y25-49", "Y50-64") for stat in ("1", "12", "22", "99")}
    education_required = {f"{age}|{edu}" for age in ("Y25-49", "Y50-64") for edu in ("ALL", "BL", "ML_RDD")}

    labour_complete = {code for code, vals in labour_by.items() if set(vals) == labour_required}
    education_complete = {code for code, vals in education_by.items() if set(vals) == education_required}
    common = labour_complete & education_complete

    if not (7800 <= len(common) <= 8000):
        raise RuntimeError(f"Copertura comunale nazionale inattesa: labour={len(labour_complete)} education={len(education_complete)} common={len(common)}")
    tuscany_codes = {code for code in common if is_tuscany_municipality(code)}
    if not (270 <= len(tuscany_codes) <= 280):
        raise RuntimeError(f"Copertura comunale Toscana inattesa: {len(tuscany_codes)}")

    def aggregate_scope(codes: set[str]) -> tuple[dict[str, float], dict[str, float]]:
        labour = {"population": 0.0, "employed": 0.0, "unemployed": 0.0, "active": 0.0}
        education = {"population": 0.0, "tertiary": 0.0}
        for code in codes:
            l = labour_by[code]
            labour["population"] += l["Y25-49|99"] + l["Y50-64|99"]
            labour["employed"] += l["Y25-49|1"] + l["Y50-64|1"]
            labour["unemployed"] += l["Y25-49|12"] + l["Y50-64|12"]
            labour["active"] += l["Y25-49|22"] + l["Y50-64|22"]
            e = education_by[code]
            education["population"] += e["Y25-49|ALL"] + e["Y50-64|ALL"]
            education["tertiary"] += (
                e["Y25-49|BL"] + e["Y25-49|ML_RDD"] +
                e["Y50-64|BL"] + e["Y50-64|ML_RDD"]
            )
        if not math.isclose(labour["employed"] + labour["unemployed"], labour["active"], rel_tol=0.0, abs_tol=1e-4):
            raise RuntimeError("Aggregato labour: employed + unemployed != active")
        if not math.isclose(labour["population"], education["population"], rel_tol=0.0, abs_tol=1e-4):
            raise RuntimeError(f"Aggregato 25-64: popolazione labour {labour['population']} != education {education['population']}")
        labour["employmentRate"] = labour["employed"] / labour["population"] * 100.0
        labour["unemploymentRate"] = labour["unemployed"] / labour["active"] * 100.0
        labour["activityRate"] = labour["active"] / labour["population"] * 100.0
        education["tertiaryRate"] = education["tertiary"] / education["population"] * 100.0
        return labour, education

    tus_labour, tus_education = aggregate_scope(tuscany_codes)
    ita_labour, ita_education = aggregate_scope(common)

    diagnostics = {
        "labourRows": len(labour_rows),
        "educationRows": len(education_rows),
        "labourMunicipalitiesComplete": len(labour_complete),
        "educationMunicipalitiesComplete": len(education_complete),
        "commonMunicipalities": len(common),
        "tuscanyMunicipalities": len(tuscany_codes),
        "labourKey": labour_key,
        "educationKey": education_key,
    }
    return {"labour": tus_labour, "education": tus_education}, {"labour": ita_labour, "education": ita_education}, diagnostics


def resolve_scope_2024(session: requests.Session, candidates: list[str]) -> tuple[str, dict[str, float], dict[str, float]]:
    attempts = []
    for code in candidates:
        try:
            labour_rows = sdmx_rows(session, SDMX_FLOWS["labour"], code)
            education_rows = sdmx_rows(session, SDMX_FLOWS["education"], code)
            if not labour_rows or not education_rows:
                attempts.append({"code": code, "labourRows": len(labour_rows), "educationRows": len(education_rows), "status": "empty"})
                continue
            labour = aggregate_labour_2024(labour_rows, code)
            education = aggregate_education_2024(education_rows, code)
            return code, labour, education
        except Exception as exc:
            attempts.append({"code": code, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    raise RuntimeError(f"REF_AREA 2024 non risolto: {attempts}")


def acquire_residual_2024(session: requests.Session, site: dict[str, Any]) -> dict[str, Any]:
    local = json.loads(LOCAL_2024.read_text(encoding="utf-8"))
    reconcile = reconcile_public_2024(site, local)
    direct_error = None
    try:
        tus_code, tus_labour, tus_education = resolve_scope_2024(session, ["09", "ITI1"])
        ita_code, ita_labour, ita_education = resolve_scope_2024(session, ["IT"])
        diagnostics = {"mode": "direct-ref-area"}
    except Exception as exc:
        direct_error = f"{type(exc).__name__}: {exc}"
        tus_scope, ita_scope, diagnostics = aggregate_all_municipal_2024(session)
        tus_code = "SUM_MUNICIPALITIES_TOSCANA"
        ita_code = "SUM_MUNICIPALITIES_ITALIA"
        tus_labour, tus_education = tus_scope["labour"], tus_scope["education"]
        ita_labour, ita_education = ita_scope["labour"], ita_scope["education"]
        diagnostics = {"mode": "municipal-sum", "directScopeError": direct_error, **diagnostics}
    benchmarks = {
        "employmentRate": {"year": 2024, "unit": "percent", "tuscany": tus_labour["employmentRate"], "italy": ita_labour["employmentRate"]},
        "unemploymentRate": {"year": 2024, "unit": "percent", "tuscany": tus_labour["unemploymentRate"], "italy": ita_labour["unemploymentRate"]},
        "activityRate": {"year": 2024, "unit": "percent", "tuscany": tus_labour["activityRate"], "italy": ita_labour["activityRate"]},
        "tertiary": {"year": 2024, "unit": "percent", "tuscany": tus_education["tertiaryRate"], "italy": ita_education["tertiaryRate"]},
    }
    sanity = {
        "publicMetricReconciliation": reconcile["status"] == "PASS",
        "tuscanyResolved": bool(tus_code),
        "italyResolved": bool(ita_code),
        "ratesInRange": all(0.0 <= float(spec[scope]) <= 100.0 for spec in benchmarks.values() for scope in ("tuscany", "italy")),
    }
    return {
        "schemaVersion": 3,
        "publisher": "Istat — Censimento permanente della popolazione",
        "profileId": "istat-census-annual",
        "referenceYear": 2024,
        "source": {"api": SDMX_BASE, "flows": SDMX_FLOWS, "tuscanyRefArea": tus_code, "italyRefArea": ita_code},
        "method": "Aggregazione dei conteggi SDMX 2024 sulle classi 25–49 e 50–64. Se il dataflow comunale non espone aggregati territoriali, Toscana e Italia sono ottenute sommando i conteggi comunali completi prima del calcolo dei tassi; mai come media di percentuali.",
        "diagnostics": diagnostics,
        "components": {"tuscany": {"labour": tus_labour, "education": tus_education}, "italy": {"labour": ita_labour, "education": ita_education}},
        "benchmarks": benchmarks,
        "publicMetricReconciliation": reconcile,
        "sanityGate": sanity,
        "status": "ACQUIRED_CANDIDATE" if all(sanity.values()) else "CANDIDATE_REJECTED",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--metrics", default="")
    args = ap.parse_args()

    governed = json.loads(GOVERNED.read_text(encoding="utf-8"))
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    requested = {x.strip() for x in args.metrics.split(",") if x.strip()}
    if requested and requested.issubset(RESIDUAL_2024):
        session = requests.Session()
        session.headers["User-Agent"] = "OsservatorioVersilia-A3-census-benchmark/3.0"
        payload = acquire_residual_2024(session, site)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "metrics": sorted(payload["benchmarks"]), "tuscanyRefArea": payload["source"]["tuscanyRefArea"], "italyRefArea": payload["source"]["italyRefArea"], "publicReconciliation": payload["publicMetricReconciliation"]["status"], "output": str(out)}, ensure_ascii=False))
        return
    town_codes = {
        str(item["code"])
        for item in ((governed.get("scope") or {}).get("towns") or [])
        if isinstance(item, dict) and item.get("code")
    }
    if len(town_codes) != 7:
        raise RuntimeError("Perimetro governato Versilia non 7/7")

    session = requests.Session()
    session.headers["User-Agent"] = "OsservatorioVersilia-A3-census-benchmark/2.0"

    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        sha = hashlib.sha256()
        total_bytes = 0
        with session.get(URL, stream=True, timeout=240) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                tmp.write(chunk)
                sha.update(chunk)
                total_bytes += len(chunk)
        tmp.flush()

        italy_acc = empty_totals()
        tuscany = None
        tuscany_towns = {}
        diagnostics = {}
        workbook_hashes = {}

        with zipfile.ZipFile(tmp.name) as archive:
            members = [
                name for name in archive.namelist()
                if re.search(r"R\d{2}_.+_2023_sezioni\.xlsx$", Path(name).name, re.IGNORECASE)
                and not Path(name).name.startswith("~$")
            ]
            if not (20 <= len(members) <= 22):
                raise RuntimeError(f"Numero file regionali inatteso: {len(members)}; sample={members[:10]}")

            region_codes = []
            for member in sorted(members):
                base = Path(member).name
                match = re.match(r"R(\d{2})_", base, re.IGNORECASE)
                if not match:
                    raise RuntimeError(f"Codice regione non ricavabile da {base}")
                region_code = match.group(1)
                region_codes.append(region_code)

                blob = archive.read(member)
                workbook_hashes[base] = hashlib.sha256(blob).hexdigest()
                is_tuscany = region_code == "09"
                regional, towns, diag = parse_workbook(blob, base, town_codes if is_tuscany else None)
                diagnostics[base] = diag
                for field in REQUIRED_FIELDS:
                    italy_acc[field] += regional[field]
                if is_tuscany:
                    tuscany = regional
                    tuscany_towns = towns

            if len(set(region_codes)) != len(region_codes):
                raise RuntimeError(f"Codici regione duplicati nel pacchetto: {region_codes}")

    if tuscany is None:
        raise RuntimeError("File Toscana R09 non trovato")

    italy = finalize(italy_acc)
    reconcile = compare_governed(tuscany_towns, governed)
    public_reconcile = reconcile_public_2023(tuscany_towns, site, governed)

    sanity = {
        "regionalFiles": 20 <= len(diagnostics) <= 22,
        "tuscanyPopulation": 3_000_000 <= tuscany["P1"] <= 4_500_000,
        "italyPopulation": 55_000_000 <= italy["P1"] <= 65_000_000,
        "tuscanyVsItaly": 0 < tuscany["P1"] < italy["P1"],
        "versiliaReconciliation": reconcile["status"] == "PASS",
        "publicMetricReconciliation": public_reconcile["status"] == "PASS",
    }

    raw = {"tuscany": tuscany, "italy": italy}
    benchmarks = {}
    for metric_id, (num, den, scale, unit) in METRICS.items():
        benchmarks[metric_id] = {
            "year": 2023,
            "unit": unit,
            "formula": f"{num} / {den} × {scale:g}",
            "tuscany": ratio(tuscany, num, den, scale),
            "italy": ratio(italy, num, den, scale),
            "raw": {
                "tuscany": {"numerator": tuscany[num], "denominator": tuscany[den]},
                "italy": {"numerator": italy[num], "denominator": italy[den]},
            },
        }

    benchmarks["employmentGenderGap"] = {
        "year": 2023,
        "unit": "percentagePoints",
        "formula": "maleEmploymentRate − femaleEmploymentRate",
        "tuscany": benchmarks["maleEmploymentRate"]["tuscany"] - benchmarks["femaleEmploymentRate"]["tuscany"],
        "italy": benchmarks["maleEmploymentRate"]["italy"] - benchmarks["femaleEmploymentRate"]["italy"],
        "raw": {
            "tuscany": {
                "maleEmploymentRate": benchmarks["maleEmploymentRate"]["tuscany"],
                "femaleEmploymentRate": benchmarks["femaleEmploymentRate"]["tuscany"],
            },
            "italy": {
                "maleEmploymentRate": benchmarks["maleEmploymentRate"]["italy"],
                "femaleEmploymentRate": benchmarks["femaleEmploymentRate"]["italy"],
            },
        },
    }

    status = "ACQUIRED_CANDIDATE" if all(sanity.values()) else "CANDIDATE_REJECTED"
    payload = {
        "schemaVersion": 2,
        "publisher": "Istat — Censimento permanente della popolazione e delle abitazioni",
        "profileId": "istat-census-annual",
        "referenceYear": 2023,
        "source": {
            "url": URL,
            "bytes": total_bytes,
            "sha256": sha.hexdigest(),
            "regionalWorkbookCount": len(diagnostics),
            "regionalWorkbookHashes": workbook_hashes,
        },
        "method": "Aggregazione delle variabili additive nei file regionali ufficiali per sezione 2023. Toscana = file R09; Italia = somma dei file regionali. Nessuna derivazione dal perimetro subcomunale Comuni_2023.",
        "raw": raw,
        "benchmarks": benchmarks,
        "tuscanyVersiliaReconciliation": reconcile,
        "publicMetricReconciliation": public_reconcile,
        "diagnostics": diagnostics,
        "sanityGate": sanity,
        "status": status,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "metrics": sorted(benchmarks),
        "tuscanyPopulation": tuscany["P1"],
        "italyPopulation": italy["P1"],
        "reconciliation": reconcile["status"],
        "publicReconciliation": public_reconcile["status"],
        "output": str(out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
