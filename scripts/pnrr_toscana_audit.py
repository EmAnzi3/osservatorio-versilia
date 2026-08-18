#!/usr/bin/env python3
"""Audit read-only dei due indicatori PNRR contro Open Data Regione Toscana.

Il feed regionale espone direttamente soggetto attuatore, importo PNRR e fasi
ReGiS. L'audit legge il CSV ufficiale in streaming, seleziona esclusivamente i
sette Comuni dell'Osservatorio come soggetti attuatori e confronta la fotografia
corrente con i valori già pubblicati. Non modifica mai ``data/site-data.json``.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any, Iterable

DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
MAIN_CSV_URL = "https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv"
USER_AGENT = "OsservatorioVersiliaDataMonitor/1.1 (+https://osservatorioversilia.it/)"

REQUIRED_FIELDS = {
    "id_progetto",
    "area",
    "misura_pnrr_estesa",
    "soggetto_attuatore",
    "cf_soggetto_attuatore",
    "importo_finanziato_pnrr",
    "data_elaborazione",
}
CONCLUSION_FIELDS = (
    "fase_avanzamento_da_regis",
    "fase_avanzamento_da_monitoraggio_progetti",
    "fase_regis",
    "data_fine_effettiva_chiusura_intervento",
)


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
    if not text or norm(text) in {"NULL", "ND", "N D", "NON DISPONIBILE"}:
        return None
    text = text.replace("€", "").replace("\u00a0", "").replace(" ", "")
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


def is_pnrr(record: dict[str, Any]) -> bool:
    return norm(record.get("area")) == "PNRR" or bool(str(record.get("misura_pnrr_estesa") or "").strip())


def concluded_from(record: dict[str, Any], field: str) -> bool:
    value = str(record.get(field) or "").strip()
    if field == "data_fine_effettiva_chiusura_intervento":
        return bool(value and norm(value) not in {"NULL", "ND", "N D", "NON DISPONIBILE"})
    return "CONCLUS" in norm(value)


def metric_rows(data: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    metric = data.get("metrics", {}).get(key, {})
    rows = metric.get("rows") if isinstance(metric, dict) else []
    if not isinstance(rows, list):
        return {}
    return {str(row.get("code")): row for row in rows if isinstance(row, dict) and row.get("code")}


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


def iter_csv_records(url: str = MAIN_CSV_URL) -> Iterable[dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        text = io.TextIOWrapper(response, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.DictReader(text)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_FIELDS - fields)
        if missing:
            raise RuntimeError(f"Tracciato PNRR Toscana incompleto: {', '.join(missing)}")
        for field in CONCLUSION_FIELDS:
            if field not in fields:
                raise RuntimeError(f"Campo conclusione assente: {field}")
        yield from reader


def select_town_projects(
    records: Iterable[dict[str, Any]],
    published: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, dict[str, Any]]], set[str], int]:
    by_town: dict[str, dict[str, dict[str, Any]]] = {code: {} for code in published}
    elaboration_dates: set[str] = set()
    scanned = 0

    for row in records:
        scanned += 1
        if not is_pnrr(row):
            continue
        subject = str(row.get("soggetto_attuatore") or "")
        matched_code = next(
            (code for code, item in published.items() if town_subject_match(subject, item["town"])),
            None,
        )
        if matched_code is None:
            continue
        project_id = str(row.get("id_progetto") or row.get("cup") or "").strip()
        if not project_id:
            continue
        by_town[matched_code][project_id] = dict(row)
        date = str(row.get("data_elaborazione") or "").strip()
        if date:
            elaboration_dates.add(date)
    return by_town, elaboration_dates, scanned


def audit_records(data: dict[str, Any], records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    published = published_snapshot(data)
    if len(published) != 7:
        raise RuntimeError(f"Attesi 7 comuni nel catalogo, trovati {len(published)}")

    projects, elaboration_dates, scanned = select_town_projects(records, published)
    per_town: dict[str, Any] = {}
    funding_match_all = True
    conclusion_matches: dict[str, bool] = {field: True for field in CONCLUSION_FIELDS}
    conclusion_samples: dict[str, set[str]] = {field: set() for field in CONCLUSION_FIELDS}
    total_selected = 0

    for code, pub in published.items():
        selected = list(projects[code].values())
        total_selected += len(selected)
        amounts = [parse_number(row.get("importo_finanziato_pnrr")) for row in selected]
        missing_amounts = sum(value is None for value in amounts)
        known_amounts = [value for value in amounts if value is not None]
        total_funding = sum(known_amounts) if selected and missing_amounts == 0 else None
        population = parse_number(pub.get("population"))
        funding_per_resident = total_funding / population if total_funding is not None and population else None
        funding_cmp = compare_value(funding_per_resident, pub.get("fundingPerResident"), 0.51)
        funding_match_all = funding_match_all and funding_cmp["match"]

        conclusion_candidates: dict[str, Any] = {}
        for field in CONCLUSION_FIELDS:
            for row in selected:
                raw = str(row.get(field) or "").strip()
                if raw:
                    conclusion_samples[field].add(raw)
            count = sum(concluded_from(row, field) for row in selected)
            percent = count / len(selected) * 100.0 if selected else None
            cmp = compare_value(percent, pub.get("concludedPercent"), 0.11)
            conclusion_matches[field] = conclusion_matches[field] and cmp["match"]
            conclusion_candidates[field] = {
                "count": count,
                "percent": round(percent, 4) if percent is not None else None,
                "comparison": cmp,
            }

        implied_published_total = None
        published_per_resident = parse_number(pub.get("fundingPerResident"))
        if population is not None and published_per_resident is not None:
            implied_published_total = population * published_per_resident

        per_town[code] = {
            "town": pub["town"],
            "selectedProjects": len(selected),
            "missingFundingAmounts": missing_amounts,
            "observedFundingTotal": round(total_funding, 2) if total_funding is not None else None,
            "publishedImpliedFundingTotal": round(implied_published_total, 2) if implied_published_total is not None else None,
            "observedFundingPerResident": round(funding_per_resident, 4) if funding_per_resident is not None else None,
            "publishedFundingPerResident": pub.get("fundingPerResident"),
            "fundingComparison": funding_cmp,
            "publishedConcludedPercent": pub.get("concludedPercent"),
            "conclusionCandidates": conclusion_candidates,
        }

    matching_conclusion_fields = [field for field, match in conclusion_matches.items() if match]
    schema_comparable = total_selected > 0 and all(item["selectedProjects"] > 0 for item in per_town.values())
    if not schema_comparable:
        verdict = "not_comparable"
    elif funding_match_all and matching_conclusion_fields:
        verdict = "match"
    else:
        verdict = "different_current_snapshot"

    return {
        "dataset": DATASET_URL,
        "resource": MAIN_CSV_URL,
        "sourceRole": "machine_readable_verification",
        "upstreamDeclaredSource": "Italia Domani / ReGiS",
        "recordsScanned": scanned,
        "selectedProjects": total_selected,
        "dataElaborationDates": sorted(elaboration_dates),
        "perTown": per_town,
        "fundingMatch7of7": funding_match_all,
        "conclusionDefinitionMatches": matching_conclusion_fields,
        "conclusionFieldMatchMatrix": conclusion_matches,
        "conclusionSamples": {field: sorted(values)[:30] for field, values in conclusion_samples.items()},
        "verdict": verdict,
        "eligibleForAutomaticVerification": verdict == "match",
        "note": (
            "Il feed viene considerato equivalente solo con confronto 7/7. "
            "Una fotografia più recente ma numericamente diversa non modifica automaticamente i dati pubblicati: "
            "diventa un segnale di rilascio da validare."
        ),
    }


def audit(data: dict[str, Any]) -> dict[str, Any]:
    return audit_records(data, iter_csv_records())


def markdown(result: dict[str, Any]) -> str:
    fields = result.get("conclusionDefinitionMatches") or []
    conclusion_field = fields[0] if fields else "fase_avanzamento_da_regis"
    lines = [
        "# Audit PNRR · Regione Toscana",
        "",
        f"**Verdetto:** `{result['verdict']}`  ",
        f"**Fotografia regionale:** {', '.join(result.get('dataElaborationDates', [])) or 'n.d.'}  ",
        f"**Progetti selezionati:** {result.get('selectedProjects', 0)}  ",
        f"**Finanziamenti coincidenti 7/7:** {'sì' if result.get('fundingMatch7of7') else 'no'}  ",
        f"**Definizione conclusione coincidente 7/7:** {', '.join(fields) if fields else 'nessuna'}",
        "",
        "| Comune | Progetti | €/res osservato | €/res pubblicato | Conclusi osservati | Conclusi pubblicati |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in result["perTown"].values():
        candidate = item["conclusionCandidates"][conclusion_field]
        obs_f = item["observedFundingPerResident"]
        obs_c = candidate["percent"]
        lines.append(
            f"| {item['town']} | {item['selectedProjects']} | "
            f"{obs_f if obs_f is not None else 'n.d.'} | {item['publishedFundingPerResident']} | "
            f"{obs_c if obs_c is not None else 'n.d.'}% | {item['publishedConcludedPercent']}% |"
        )
    lines.extend(["", "## Esito per definizione di conclusione", ""])
    for field, match in result.get("conclusionFieldMatchMatrix", {}).items():
        lines.append(f"- `{field}`: {'match 7/7' if match else 'differenze presenti'}")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
