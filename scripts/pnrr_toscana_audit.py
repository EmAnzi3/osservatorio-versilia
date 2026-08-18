#!/usr/bin/env python3
"""Audit read-only dei due indicatori PNRR contro Open Data Regione Toscana.

Scopo: verificare se il feed machine-readable regionale, alimentato anche da ReGiS,
può sostituire il controllo manuale del landing Italia Domani senza cambiare i valori
pubblicati. Lo script non scrive mai ``data/site-data.json``.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CKAN_API = "https://www.dati.toscana.it/api/3/action/datastore_search"
MAIN_RESOURCE = "56b0d1e0-2d25-4434-af56-63d316775600"
SUBJECT_RESOURCE = "91c2a7ba-4a44-4f35-925f-30f4a55c74e7"
DATASET_URL = "https://www.dati.toscana.it/dataset/regione-toscana-pnrr"
USER_AGENT = "OsservatorioVersiliaDataMonitor/1.1 (+https://osservatorioversilia.it/)"
PAGE_SIZE = 1000
MAX_RECORDS = 100_000

PROJECT_ALIASES = ("id_progetto", "idprogetto", "progetto_id")
SUBJECT_ALIASES = (
    "soggetto",
    "denominazione_soggetto",
    "soggetto_denominazione",
    "denominazione",
    "nome_soggetto",
)
ROLE_ALIASES = ("ruolo", "tipo_soggetto", "tipologia_soggetto", "ruolo_soggetto")


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def town_subject_match(subject: Any, town: str) -> bool:
    subject_n = norm(subject)
    town_n = norm(town)
    if not subject_n or not town_n:
        return False
    candidates = {
        town_n,
        f"COMUNE {town_n}",
        f"COMUNE DI {town_n}",
        f"COMUNE DEL {town_n}",
    }
    return subject_n in candidates or subject_n.endswith(f" COMUNE DI {town_n}")


def parse_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("€", "").replace("\u00a0", "").replace(" ", "")
    # Formato italiano: 1.234.567,89. Formato internazionale: 1234567.89.
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)
    if not text or text in {"-", ".", "-."}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def truthy_pnrr(record: dict[str, Any]) -> bool:
    amount = parse_number(record.get("finanziato_pnrr"))
    if amount is not None:
        return amount > 0
    raw = norm(record.get("finanziato_pnrr"))
    if raw and raw not in {"NO", "N", "FALSE", "0", "0 00"}:
        return True
    return bool(str(record.get("misura_pnrr_estesa") or "").strip())


def is_concluded(record: dict[str, Any]) -> bool:
    phase = norm(record.get("fase_avanzamento"))
    return "CONCLUS" in phase


def api_page(resource_id: str, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = PAGE_SIZE) -> dict[str, Any]:
    params: dict[str, str] = {
        "resource_id": resource_id,
        "limit": str(limit),
        "offset": str(offset),
    }
    if filters:
        params["filters"] = json.dumps(filters, ensure_ascii=False, separators=(",", ":"))
    url = CKAN_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError(f"CKAN DataStore ha restituito un esito non valido per {resource_id}")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Risposta CKAN priva di result per {resource_id}")
    return result


def all_records(resource_id: str, *, filters: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    fields: list[str] = []
    offset = 0
    total = None
    while total is None or offset < total:
        result = api_page(resource_id, filters=filters, offset=offset)
        if not fields:
            raw_fields = result.get("fields")
            if isinstance(raw_fields, list):
                fields = [str(item.get("id")) for item in raw_fields if isinstance(item, dict) and item.get("id")]
        page = result.get("records")
        if not isinstance(page, list):
            raise RuntimeError("records non è una lista")
        records.extend(item for item in page if isinstance(item, dict))
        raw_total = result.get("total")
        total = int(raw_total) if isinstance(raw_total, (int, float, str)) and str(raw_total).isdigit() else len(records)
        offset = len(records)
        if offset >= MAX_RECORDS:
            raise RuntimeError(f"Risorsa {resource_id} oltre il limite prudenziale di {MAX_RECORDS} record")
        if not page:
            break
    return records, fields


def field_by_alias(fields: list[str], aliases: tuple[str, ...], *, contains: tuple[str, ...] = ()) -> str | None:
    normalized = {norm(field).replace(" ", "_").lower(): field for field in fields}
    for alias in aliases:
        key = norm(alias).replace(" ", "_").lower()
        if key in normalized:
            return normalized[key]
    for field in fields:
        key = norm(field).lower()
        if all(token.upper() in key for token in contains):
            return field
    return None


def metric_rows(data: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    metric = data.get("metrics", {}).get(key, {})
    rows = metric.get("rows") if isinstance(metric, dict) else []
    if not isinstance(rows, list):
        return {}
    return {str(row.get("code")): row for row in rows if isinstance(row, dict) and row.get("code")}


def load_town_projects(code: str) -> tuple[list[dict[str, Any]], str]:
    records, _ = all_records(MAIN_RESOURCE, filters={"cod_istat": code})
    if records:
        return records, code
    short = code.lstrip("0")
    if short != code:
        records, _ = all_records(MAIN_RESOURCE, filters={"cod_istat": short})
        if records:
            return records, short
    return [], code


def published_snapshot(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    funding = metric_rows(data, "pnrrFunding")
    concluded = metric_rows(data, "pnrrConcluded")
    population = metric_rows(data, "population")
    towns = data.get("towns") if isinstance(data.get("towns"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for town in towns:
        if not isinstance(town, dict) or not town.get("code"):
            continue
        code = str(town["code"])
        result[code] = {
            "town": str(town.get("name") or code),
            "population": (population.get(code) or {}).get("value"),
            "fundingPerResident": (funding.get(code) or {}).get("value"),
            "concludedPercent": (concluded.get(code) or {}).get("value"),
        }
    return result


def compare_value(observed: float | None, published: Any, tolerance: float) -> dict[str, Any]:
    expected = parse_number(published)
    if observed is None or expected is None:
        return {"match": False, "delta": None, "reason": "valore non confrontabile"}
    delta = observed - expected
    return {"match": abs(delta) <= tolerance, "delta": round(delta, 4), "reason": ""}


def audit(data: dict[str, Any]) -> dict[str, Any]:
    published = published_snapshot(data)
    if len(published) != 7:
        raise RuntimeError(f"Attesi 7 comuni nel catalogo, trovati {len(published)}")

    subject_error = ""
    subject_records: list[dict[str, Any]] = []
    subject_fields: list[str] = []
    try:
        subject_records, subject_fields = all_records(SUBJECT_RESOURCE)
    except Exception as exc:  # audit esplorativo: riportare il problema senza mascherarlo
        subject_error = f"{type(exc).__name__}: {exc}"

    project_field = field_by_alias(subject_fields, PROJECT_ALIASES, contains=("PROGETTO",))
    role_field = field_by_alias(subject_fields, ROLE_ALIASES, contains=("RUOLO",))
    subject_field = field_by_alias(subject_fields, SUBJECT_ALIASES, contains=("SOGGETTO",))

    subject_index: dict[str, list[dict[str, Any]]] = {}
    if project_field:
        for row in subject_records:
            pid = str(row.get(project_field) or "").strip()
            if pid:
                subject_index.setdefault(pid, []).append(row)

    has_strict_subject_scope = bool(project_field and role_field and subject_field)
    role_samples = sorted({str(row.get(role_field) or "").strip() for row in subject_records if role_field and row.get(role_field)})[:30]
    attuatore_seen = any("ATTUAT" in norm(value) for value in role_samples)
    has_strict_subject_scope = has_strict_subject_scope and attuatore_seen

    per_town: dict[str, Any] = {}
    all_strict = has_strict_subject_scope
    all_matches = True
    project_phases: set[str] = set()
    funding_samples: set[str] = set()

    for code, pub in published.items():
        town = str(pub["town"])
        main_records, code_used = load_town_projects(code)
        pnrr_records = [row for row in main_records if truthy_pnrr(row)]

        selected: list[dict[str, Any]] = []
        scope = "subject_attuatore" if has_strict_subject_scope else "soggetto_richiedente_fallback"
        for row in pnrr_records:
            pid = str(row.get("id_progetto") or "").strip()
            if has_strict_subject_scope and pid:
                subjects = subject_index.get(pid, [])
                if any(
                    "ATTUAT" in norm(item.get(role_field)) and town_subject_match(item.get(subject_field), town)
                    for item in subjects
                ):
                    selected.append(row)
            elif town_subject_match(row.get("soggetto_richiedente"), town):
                selected.append(row)

        dedup: dict[str, dict[str, Any]] = {}
        for row in selected:
            pid = str(row.get("id_progetto") or row.get("cup") or id(row))
            dedup[pid] = row
        selected = list(dedup.values())

        amounts: list[float] = []
        amount_missing = 0
        phase_missing = 0
        concluded_count = 0
        for row in selected:
            funding_samples.add(str(row.get("finanziato_pnrr") or "")[:80])
            amount = parse_number(row.get("finanziato_pnrr"))
            if amount is None:
                amount_missing += 1
            else:
                amounts.append(amount)
            phase = str(row.get("fase_avanzamento") or "").strip()
            if phase:
                project_phases.add(phase)
            else:
                phase_missing += 1
            if is_concluded(row):
                concluded_count += 1

        total_funding = sum(amounts) if selected and amount_missing == 0 else None
        population = parse_number(pub.get("population"))
        funding_per_resident = total_funding / population if total_funding is not None and population else None
        concluded_percent = (concluded_count / len(selected) * 100.0) if selected and phase_missing == 0 else None

        funding_cmp = compare_value(funding_per_resident, pub.get("fundingPerResident"), 0.51)
        concluded_cmp = compare_value(concluded_percent, pub.get("concludedPercent"), 0.11)
        strict = has_strict_subject_scope and amount_missing == 0 and phase_missing == 0 and bool(selected)
        town_match = strict and funding_cmp["match"] and concluded_cmp["match"]
        all_strict = all_strict and strict
        all_matches = all_matches and town_match

        per_town[code] = {
            "town": town,
            "codIstatQueried": code_used,
            "localizedRecords": len(main_records),
            "pnrrLocalizedRecords": len(pnrr_records),
            "selectedProjects": len(selected),
            "scope": scope,
            "strictComparable": strict,
            "missingFundingAmounts": amount_missing,
            "missingPhases": phase_missing,
            "observedFundingTotal": round(total_funding, 2) if total_funding is not None else None,
            "observedFundingPerResident": round(funding_per_resident, 4) if funding_per_resident is not None else None,
            "publishedFundingPerResident": pub.get("fundingPerResident"),
            "fundingComparison": funding_cmp,
            "observedConcluded": concluded_count,
            "observedConcludedPercent": round(concluded_percent, 4) if concluded_percent is not None else None,
            "publishedConcludedPercent": pub.get("concludedPercent"),
            "concludedComparison": concluded_cmp,
            "match": town_match,
        }

    if not all_strict:
        verdict = "not_comparable"
    elif all_matches:
        verdict = "match"
    else:
        verdict = "mismatch"

    return {
        "dataset": DATASET_URL,
        "ckanApi": CKAN_API,
        "mainResource": MAIN_RESOURCE,
        "subjectResource": SUBJECT_RESOURCE,
        "subjectResourceError": subject_error,
        "subjectFields": subject_fields,
        "subjectProjectField": project_field,
        "subjectRoleField": role_field,
        "subjectNameField": subject_field,
        "subjectRoleSamples": role_samples,
        "strictSubjectScopeAvailable": has_strict_subject_scope,
        "phaseSamples": sorted(project_phases),
        "fundingSamples": sorted(funding_samples)[:30],
        "perTown": per_town,
        "verdict": verdict,
        "eligibleForAutomaticVerification": verdict == "match",
        "note": (
            "Solo un match 7/7 con ruolo soggetto attuatore esplicito può abilitare il monitor automatico. "
            "Un fallback sul soggetto richiedente resta esclusivamente diagnostico."
        ),
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Audit PNRR · Regione Toscana",
        "",
        f"**Verdetto:** `{result['verdict']}`  ",
        f"**Verifica automatica abilitabile:** {'sì' if result['eligibleForAutomaticVerification'] else 'no'}",
        "",
        "| Comune | Progetti | €/res osservato | €/res pubblicato | Conclusi osservati | Conclusi pubblicati | Esito |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in result["perTown"].values():
        obs_f = item["observedFundingPerResident"]
        obs_c = item["observedConcludedPercent"]
        lines.append(
            f"| {item['town']} | {item['selectedProjects']} | "
            f"{obs_f if obs_f is not None else 'n.d.'} | {item['publishedFundingPerResident']} | "
            f"{obs_c if obs_c is not None else 'n.d.'}% | {item['publishedConcludedPercent']}% | "
            f"{'OK' if item['match'] else 'DA VERIFICARE'} |"
        )
    lines.extend([
        "",
        "## Diagnostica schema soggetti",
        "",
        f"- campo progetto: `{result.get('subjectProjectField')}`",
        f"- campo ruolo: `{result.get('subjectRoleField')}`",
        f"- campo soggetto: `{result.get('subjectNameField')}`",
        f"- perimetro attuatore rigoroso disponibile: `{result.get('strictSubjectScopeAvailable')}`",
    ])
    if result.get("subjectResourceError"):
        lines.append(f"- errore risorsa soggetti: `{result['subjectResourceError']}`")
    lines.extend(["", "## Fasi osservate", ""])
    for value in result.get("phaseSamples", []):
        lines.append(f"- `{value}`")
    lines.extend(["", result["note"], ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/pnrr-toscana-audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/pnrr-toscana-audit.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    result = audit(data)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(result), encoding="utf-8")
    print(markdown(result))
    # L'audit non fallisce per mismatch: serve proprio a misurare il perimetro.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
