#!/usr/bin/env python3
"""Materializza la preview Bilanci v1.39.0 in modo riproducibile.

Usa esclusivamente gli archivi Rendiconto OpenBDAP 2019-2025 già registrati
nello snapshot v1.6.0 e ne verifica SHA-256 prima dell'uso. Non imputa zero a
righe assenti: una annualità entra nella serie di un indicatore solo se la
copertura è 7/7 con valore numerico per tutti i Comuni.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
BASELINE_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
OUT_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v139.json"
TIMEOUT = 240

TOWNS = {
    "Massarosa": "018",
    "Viareggio": "033",
    "Camaiore": "005",
    "Pietrasanta": "024",
    "Seravezza": "028",
    "Forte dei Marmi": "013",
    "Stazzema": "030",
}
PROVINCE = "046"
MISSION_MEMBER = "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv"
RESULT_MEMBER = "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv"
PORTAL_URL = "https://openbdap.rgs.mef.gov.it/it/FET/Analizza"

METRICS = {
    "fcdePerResident": {
        "kind": "result",
        "code": "0491",
        "label": "Fondo crediti di dubbia esigibilità per residente",
        "shortLabel": "FCDE",
        "description": "Accantonamento al Fondo crediti di dubbia esigibilità al 31 dicembre, rapportato alla popolazione residente.",
        "formula": "FCDE al 31 dicembre / popolazione residente",
        "caveat": "Il FCDE è un accantonamento prudenziale del risultato di amministrazione a presidio del rischio di mancata riscossione; non equivale alla quota di crediti che il Comune sa di non incassare.",
        "aggregate_note": "Somma del FCDE dei sette Comuni rapportata alla popolazione complessiva.",
    },
    "yearEndCashFundPerResident": {
        "kind": "result",
        "code": "0495",
        "label": "Fondo di cassa al 31 dicembre per residente",
        "shortLabel": "Fondo cassa finale",
        "description": "Consistenza del fondo di cassa al 31 dicembre, rapportata alla popolazione residente.",
        "formula": "fondo di cassa al 31 dicembre / popolazione residente",
        "caveat": "È lo stock complessivo di cassa a fine esercizio: può comprendere somme vincolate e non coincide con la sola cassa libera o immediatamente spendibile.",
        "aggregate_note": "Somma del fondo di cassa finale dei sette Comuni rapportata alla popolazione complessiva.",
    },
    "generalAdministrationMissionExpenditurePerResident": {
        "kind": "mission",
        "code": "01",
        "label": "Spesa impegnata per servizi istituzionali e generali per residente",
        "shortLabel": "Servizi generali",
        "description": "Impegni della Missione 01 «Servizi istituzionali, generali e di gestione», rapportati ai residenti.",
        "formula": "impegni Missione 01 / popolazione residente",
        "caveat": "La classificazione comprende spesa corrente e in conto capitale; organizzazione interna, servizi associati e investimenti straordinari incidono sul confronto.",
        "aggregate_note": "Totale degli impegni Missione 01 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "territorialPlanningMissionExpenditurePerResident": {
        "kind": "mission",
        "code": "08",
        "label": "Spesa impegnata per assetto del territorio ed edilizia abitativa per residente",
        "shortLabel": "Assetto territorio",
        "description": "Impegni della Missione 08 «Assetto del territorio ed edilizia abitativa», rapportati ai residenti.",
        "formula": "impegni Missione 08 / popolazione residente",
        "caveat": "La classificazione comprende spesa corrente e in conto capitale; programmi pluriennali e investimenti straordinari possono rendere i singoli anni molto variabili.",
        "aggregate_note": "Totale degli impegni Missione 08 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "civilProtectionMissionExpenditurePerResident": {
        "kind": "mission",
        "code": "11",
        "label": "Spesa impegnata per soccorso civile per residente",
        "shortLabel": "Soccorso civile",
        "description": "Impegni della Missione 11 «Soccorso civile», rapportati ai residenti.",
        "formula": "impegni Missione 11 / popolazione residente",
        "caveat": "Il valore riflette la classificazione contabile comunale; gestione associata, emergenze e investimenti straordinari possono incidere sul confronto annuale.",
        "aggregate_note": "Totale degli impegni Missione 11 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "economicDevelopmentMissionExpenditurePerResident": {
        "kind": "mission",
        "code": "14",
        "label": "Spesa impegnata per sviluppo economico e competitività per residente",
        "shortLabel": "Sviluppo economico",
        "description": "Impegni della sola Missione 14 «Sviluppo economico e competitività», rapportati ai residenti.",
        "formula": "impegni Missione 14 / popolazione residente",
        "caveat": "Questo indicatore isola la Missione 14. La serie storica già pubblicata «Turismo e sviluppo» resta invece la somma delle Missioni 07 e 14 e non viene modificata.",
        "aggregate_note": "Totale degli impegni Missione 14 dei sette Comuni rapportato alla popolazione complessiva.",
    },
}


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def number(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def read_member(archive: zipfile.ZipFile, suffix: str) -> list[dict[str, str]]:
    matches = [info for info in archive.infolist() if info.filename.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"{suffix}: atteso un file, trovati {len(matches)}")
    text = decode(archive.read(matches[0]))
    return [
        {k: v for k, v in row.items() if k and k.strip()}
        for row in csv.DictReader(io.StringIO(text), delimiter=";")
    ]


def town_name(row: dict[str, str]) -> str | None:
    if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
        return None
    if (row.get("Codice Provincia") or "").strip().zfill(3) != PROVINCE:
        return None
    code = (row.get("Codice Comune") or "").strip().zfill(3)
    return next((town for town, expected in TOWNS.items() if code == expected), None)


def rows_by_town(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = {town: [] for town in TOWNS}
    for row in rows:
        town = town_name(row)
        if town:
            grouped[town].append(row)
    return grouped


def population_map(baseline: dict) -> dict[str, dict[int, int]]:
    out: dict[str, dict[int, int]] = {town: {} for town in TOWNS}
    for town in TOWNS:
        years = baseline.get("raw", {}).get(town, {}).get("years", {})
        for year, values in years.items():
            pop = values.get("population_at_1_january")
            if pop:
                out[town][int(year)] = int(pop)
    return out


def download_verified(session: requests.Session, url: str, sha256: str) -> bytes:
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    if digest != sha256:
        raise RuntimeError(f"SHA-256 inatteso per {url}: {digest} != {sha256}")
    return raw


def extract_year(year: int, raw: bytes) -> tuple[dict[str, dict[str, float | None]], dict]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        missions = rows_by_town(read_member(archive, MISSION_MEMBER))
        results = rows_by_town(read_member(archive, RESULT_MEMBER))

    values = {town: {} for town in TOWNS}
    evidence = {town: {} for town in TOWNS}
    for town in TOWNS:
        mission_index: dict[str, list[dict[str, str]]] = {}
        for row in missions[town]:
            code = (row.get("Codice Missione") or "").strip().zfill(2)
            mission_index.setdefault(code, []).append(row)
        result_index: dict[str, list[dict[str, str]]] = {}
        for row in results[town]:
            code = (row.get("Cod Voce Ris Amm Rend") or "").strip()
            result_index.setdefault(code, []).append(row)

        for key, spec in METRICS.items():
            index = mission_index if spec["kind"] == "mission" else result_index
            hits = index.get(spec["code"], [])
            field = "Impegni" if spec["kind"] == "mission" else "Totale di Gestione"
            if len(hits) != 1:
                values[town][key] = None
                evidence[town][key] = {"status": "absent" if not hits else "duplicate", "rows": len(hits)}
                continue
            amount = number(hits[0].get(field))
            values[town][key] = amount
            evidence[town][key] = {
                "status": "value" if amount is not None else "n.d.",
                "raw": hits[0].get(field),
                "field": field,
                "code": spec["code"],
            }
    return values, evidence


def format_euro(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + "\u00a0€"


def add_after(items: list[str], anchor: str, additions: list[str]) -> list[str]:
    clean = [item for item in items if item not in additions]
    if anchor not in clean:
        return clean + additions
    pos = clean.index(anchor) + 1
    return clean[:pos] + additions + clean[pos:]


def materialize_metric(
    key: str,
    spec: dict,
    values_by_year: dict[int, dict[str, dict[str, float | None]]],
    populations: dict[str, dict[int, int]],
    town_rows: list[dict],
) -> tuple[dict, dict]:
    admissible_years = []
    excluded_years = {}
    for year in sorted(values_by_year):
        missing = [town for town in TOWNS if values_by_year[year][town][key] is None or not populations[town].get(year)]
        if missing:
            excluded_years[str(year)] = missing
        else:
            admissible_years.append(year)

    if 2025 not in admissible_years:
        raise RuntimeError(f"{key}: il 2025 non supera la copertura 7/7")

    rows = []
    by_town = {row["town"]: row for row in town_rows}
    for town in TOWNS:
        base = by_town[town]
        series_values = [values_by_year[year][town][key] / populations[town][year] for year in admissible_years]
        latest = series_values[-1]
        rows.append({
            "town": town,
            "code": base["code"],
            "slug": base["slug"],
            "value": latest,
            "formatted": format_euro(latest),
            "series": {"years": admissible_years, "values": series_values},
            "normalized": None,
            "benchmarkValue": latest,
        })

    latest_year = admissible_years[-1]
    aggregate_num = sum(values_by_year[latest_year][town][key] for town in TOWNS)
    aggregate_den = sum(populations[town][latest_year] for town in TOWNS)
    metric = {
        "meta": {
            "key": key,
            "theme": "bilanci",
            "label": spec["label"],
            "shortLabel": spec["shortLabel"],
            "description": spec["description"],
            "unit": "currency",
            "year": str(latest_year),
            "source": "Ragioneria generale dello Stato — OpenBDAP",
            "polarity": "neutral",
        },
        "sourceUrl": PORTAL_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_num / aggregate_den,
            "label": "Valore pro capite Versilia",
            "note": spec["aggregate_note"],
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali",
            "formula": spec["formula"],
            "caveat": spec["caveat"],
            "coverage": f"7/7 per ciascun anno pubblicato ({admissible_years[0]}–{admissible_years[-1]})" if len(admissible_years) > 1 else "7/7",
        },
    }
    return metric, {"included_years": admissible_years, "excluded_years": excluded_years}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    populations = population_map(baseline)
    years_meta = baseline["source"]["years"]

    legacy_key = "tourismDevelopmentMissionExpenditurePerResident"
    legacy_before = json.dumps(data["metrics"][legacy_key], ensure_ascii=False, sort_keys=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.39-materializer"})
    values_by_year = {}
    evidence_by_year = {}
    archives = {}
    for year in sorted(int(y) for y in years_meta):
        meta = years_meta[str(year)]["schemi"]
        raw = download_verified(session, meta["url"], meta["sha256"])
        values, evidence = extract_year(year, raw)
        values_by_year[year] = values
        evidence_by_year[str(year)] = evidence
        archives[str(year)] = {
            "url": meta["url"],
            "sha256": meta["sha256"],
            "bytes": len(raw),
        }

    population_rows = data["metrics"]["population"]["rows"]
    coverage = {}
    for key, spec in METRICS.items():
        metric, metric_coverage = materialize_metric(key, spec, values_by_year, populations, population_rows)
        data["metrics"][key] = metric
        coverage[key] = metric_coverage

    theme = data["themes"]["bilanci"]
    equity_add = ["fcdePerResident"]
    cash_add = ["yearEndCashFundPerResident"]
    mission_add = [
        "generalAdministrationMissionExpenditurePerResident",
        "territorialPlanningMissionExpenditurePerResident",
        "civilProtectionMissionExpenditurePerResident",
        "economicDevelopmentMissionExpenditurePerResident",
    ]
    theme["metrics"] = add_after(theme["metrics"], "availableAdministrationResultPerResident", equity_add)
    theme["metrics"] = add_after(theme["metrics"], "cashBalancePerResident", cash_add)
    theme["metrics"] = add_after(theme["metrics"], "tourismDevelopmentMissionExpenditurePerResident", mission_add)

    sections = {section["key"]: section for section in theme.get("sections", [])}
    sections["equilibri"]["metrics"] = add_after(
        sections["equilibri"]["metrics"], "availableAdministrationResultPerResident", equity_add
    )
    sections["cassa"]["metrics"] = add_after(sections["cassa"]["metrics"], "cashBalancePerResident", cash_add)
    sections["cassa"]["description"] = "Pagamenti, incassi e saldo registrati da SIOPE nell’anno, con la consistenza del fondo di cassa a fine esercizio da OpenBDAP."
    sections["priorita"]["metrics"] = add_after(
        sections["priorita"]["metrics"], "tourismDevelopmentMissionExpenditurePerResident", mission_add
    )

    data["version"] = "v1.39.0"
    data["release_version"] = "v1.39.0"
    data["updated"] = "2026-09-13"

    legacy_after = json.dumps(data["metrics"][legacy_key], ensure_ascii=False, sort_keys=True)
    if legacy_before != legacy_after:
        raise RuntimeError("La serie legacy Turismo e sviluppo è stata modificata")

    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedExternalMetricCount"] = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedInlineMetricCount"] = registry["expectedMetricCount"] - registry["expectedExternalMetricCount"]

    snapshot = {
        "version": "bilanci-v139",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Sei indicatori Bilanci v1.39.0 materializzati dagli archivi OpenBDAP 2019–2025 già hashati nella baseline v1.6.0.",
        "source": {
            "publisher": "Ragioneria generale dello Stato — OpenBDAP",
            "portal_url": PORTAL_URL,
            "baseline_snapshot": "bilanci-v1.6.0.json",
            "archives": archives,
        },
        "policy": {
            "row_absence": "mai convertita in zero; l'annualità è esclusa dalla serie se un Comune non ha una riga numerica valida",
            "population": "popolazione al 1° gennaio dello stesso esercizio, congelata nella baseline v1.6.0",
            "legacy_guard": legacy_key,
        },
        "coverage": coverage,
        "evidence": evidence_by_year,
        "metrics": {key: data["metrics"][key] for key in METRICS},
    }

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "version": data["version"],
        "metric_count": len(data["metrics"]),
        "added": list(METRICS),
        "coverage": coverage,
        "snapshot": str(OUT_PATH.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
