#!/usr/bin/env python3
"""Aggiorna gli indicatori ASIA-UL e AGCOM Broadband Map.

Il programma legge ``data/site-data.json``, acquisisce per i sette Comuni gli
shard pubblici di Cruscotto Italia (AgID), valida i metadati di origine e
scrive esclusivamente dati riconducibili alle fonti primarie ISTAT e AGCOM.

Uso:
    python scripts/update_agid_indicators.py
    python scripts/update_agid_indicators.py --source-dir tests/fixtures/agid

Con ``--source-dir`` la rete non viene usata: sono attesi i file
``asia/<codice>.json`` e ``agcom_bbmap/<codice>.json``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
SOURCE_REGISTRY = ROOT / "data" / "source-registry.json"
README = ROOT / "README.md"
MONTHLY_DOC = ROOT / "docs" / "aggiornamento-mensile-dati.md"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "agid-asia-agcom-2026-08.json"

AGID_BASE = "https://cruscotto-italia.dati.gov.it/data"
ASIA_SOURCE_URL = (
    "https://esploradati.istat.it/databrowser/#/it/dw/categories/"
    "IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/"
    "183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
)
AGCOM_SOURCE_URL = "https://geo.agcom.it/reportistica/ai/index.html"
AGID_PROJECT_URL = "https://cruscotto-italia.dati.gov.it/"
USER_AGENT = (
    "Osservatorio-Versilia/1.0 "
    "(+https://github.com/EmAnzi3/osservatorio-versilia)"
)

NEW_ECONOMY_KEYS = [
    "localEmployees",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
]
NEW_BROADBAND_KEYS = [
    "ftthCoverageDesi",
    "ftthReachedHouseholds",
    "ftthUnreachedHouseholds",
    "ftthCoverage20m",
]


class DataError(RuntimeError):
    """Errore di integrità o coerenza dei dati di origine."""


def _json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _fetch_bytes(url: str, attempts: int = 4) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
            if len(body) < 10:
                raise DataError(f"Risposta troppo breve da {url}")
            return body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 3)
    raise DataError(f"Impossibile scaricare {url}: {last_error}")


def _fetch_json(url: str) -> tuple[dict[str, Any], str]:
    body = _fetch_bytes(url)
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataError(f"JSON non valido da {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise DataError(f"Struttura JSON inattesa da {url}")
    return value, hashlib.sha256(body).hexdigest()


def load_source_shards(
    town_codes: Iterable[str], source_dir: Path | None = None
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
    asia: dict[str, dict[str, Any]] = {}
    agcom: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, str]] = {}

    for code in town_codes:
        if source_dir:
            asia_path = source_dir / "asia" / f"{code}.json"
            agcom_path = source_dir / "agcom_bbmap" / f"{code}.json"
            if not asia_path.exists() or not agcom_path.exists():
                raise DataError(f"Fixture mancanti per il Comune {code}")
            asia_body = asia_path.read_bytes()
            agcom_body = agcom_path.read_bytes()
            asia[code] = json.loads(asia_body.decode("utf-8"))
            agcom[code] = json.loads(agcom_body.decode("utf-8"))
            provenance[code] = {
                "asiaUrl": str(asia_path),
                "asiaSha256": hashlib.sha256(asia_body).hexdigest(),
                "agcomUrl": str(agcom_path),
                "agcomSha256": hashlib.sha256(agcom_body).hexdigest(),
            }
            continue

        asia_url = f"{AGID_BASE}/asia/{code}.json"
        agcom_url = f"{AGID_BASE}/agcom_bbmap/{code}.json"
        asia[code], asia_sha = _fetch_json(asia_url)
        agcom[code], agcom_sha = _fetch_json(agcom_url)
        provenance[code] = {
            "asiaUrl": asia_url,
            "asiaSha256": asia_sha,
            "agcomUrl": agcom_url,
            "agcomSha256": agcom_sha,
        }

    return asia, agcom, provenance


def _as_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataError(f"{label}: valore numerico mancante o non valido")
    number = float(value)
    if not math.isfinite(number):
        raise DataError(f"{label}: valore non finito")
    return number


def validate_asia(code: str, shard: dict[str, Any]) -> None:
    years = shard.get("_years_available")
    latest = shard.get("_latest_year")
    series = shard.get("serie_storica")
    kpi = shard.get("kpi")
    if years != [2018, 2019, 2020, 2021, 2022, 2023] or latest != 2023:
        raise DataError(f"ASIA {code}: annualità inattese ({years}, latest={latest})")
    if not isinstance(series, dict) or not isinstance(kpi, dict):
        raise DataError(f"ASIA {code}: sezioni kpi/serie_storica mancanti")
    if series.get("anni") != years:
        raise DataError(f"ASIA {code}: anni della serie non coerenti")
    for key in ("ul", "addetti"):
        values = series.get(key)
        if not isinstance(values, list) or len(values) != len(years):
            raise DataError(f"ASIA {code}: serie {key} incompleta")
        for index, value in enumerate(values):
            _as_number(value, f"ASIA {code} {key} {years[index]}")
    for key in ("ul_totali", "addetti_totali", "addetti_per_ul"):
        _as_number(kpi.get(key), f"ASIA {code} {key}")


def validate_agcom(code: str, shard: dict[str, Any]) -> None:
    period = shard.get("_data_period")
    kpi = shard.get("kpi")
    if period != "31/12/2025":
        raise DataError(f"AGCOM {code}: periodo inatteso ({period})")
    if not isinstance(kpi, dict):
        raise DataError(f"AGCOM {code}: sezione kpi mancante")
    for key in (
        "famiglie_residenti",
        "famiglie_ftth",
        "famiglie_ftth_20m",
        "copertura_ftth_desi_pct",
        "copertura_ftth_20m_pct",
    ):
        value = _as_number(kpi.get(key), f"AGCOM {code} {key}")
        if value < 0:
            raise DataError(f"AGCOM {code} {key}: valore negativo")
    if kpi["famiglie_ftth"] > kpi["famiglie_residenti"]:
        raise DataError(f"AGCOM {code}: famiglie FTTH maggiori delle residenti")


def _format_int(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def _format_decimal(value: float, decimals: int = 1) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def _format_people(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return _format_int(value)
    return _format_decimal(value, 1)


def _format_percent(value: float) -> str:
    return f"{_format_decimal(value, 1)}%"


def _pct_change(first: float, last: float) -> float:
    if first == 0:
        raise DataError("Impossibile calcolare una variazione percentuale da base zero")
    return (last / first - 1.0) * 100.0


def _weighted_pct(numerators: Iterable[float], denominators: Iterable[float]) -> float:
    numerator = sum(numerators)
    denominator = sum(denominators)
    if denominator <= 0:
        raise DataError("Denominatore aggregato nullo")
    return numerator / denominator * 100.0


def _insert_after(items: list[str], after: str, new_items: Iterable[str]) -> list[str]:
    clean = [item for item in items if item not in set(new_items)]
    try:
        index = clean.index(after) + 1
    except ValueError:
        index = len(clean)
    for offset, item in enumerate(new_items):
        clean.insert(index + offset, item)
    return clean


def _replace_or_append_section(
    sections: list[dict[str, Any]], section: dict[str, Any], before_key: str | None = None
) -> list[dict[str, Any]]:
    result = [item for item in sections if item.get("key") != section["key"]]
    if before_key:
        for index, item in enumerate(result):
            if item.get("key") == before_key:
                result.insert(index, section)
                break
        else:
            result.append(section)
    else:
        result.append(section)
    return result


def _town_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    local_rows = {
        row["code"]: row
        for row in data["metrics"]["localUnits"]["rows"]
    }
    rows: list[dict[str, str]] = []
    for town in data.get("towns", []):
        code = str(town.get("code", ""))
        local = local_rows.get(code)
        if not local:
            raise DataError(f"Comune {code}: riga localUnits mancante")
        rows.append(
            {
                "town": local["town"],
                "code": code,
                "slug": local["slug"],
            }
        )
    if len(rows) != 7:
        raise DataError(f"Attesi 7 Comuni, trovati {len(rows)}")
    return rows


def _row(
    town: dict[str, str],
    value: float,
    formatted: str,
    series: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **town,
        "value": value,
        "formatted": formatted,
        "series": series,
        "normalized": None,
        "benchmarkValue": value,
    }


def _metric(
    key: str,
    theme: str,
    label: str,
    short_label: str,
    description: str,
    unit: str,
    year: str,
    source: str,
    source_url: str,
    rows: list[dict[str, Any]],
    aggregate: dict[str, Any],
    method_type: str,
    formula: str,
    caveat: str,
) -> dict[str, Any]:
    return {
        "meta": {
            "key": key,
            "theme": theme,
            "label": label,
            "shortLabel": short_label,
            "description": description,
            "unit": unit,
            "year": year,
            "source": source,
            "polarity": "neutral",
        },
        "sourceUrl": source_url,
        "rows": rows,
        "aggregate": aggregate,
        "normalizedAggregate": None,
        "method": {
            "type": method_type,
            "formula": formula,
            "caveat": caveat,
            "coverage": "7/7",
        },
    }


def apply_updates(
    source_data: dict[str, Any],
    asia: dict[str, dict[str, Any]],
    agcom: dict[str, dict[str, Any]],
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = copy.deepcopy(source_data)
    towns = _town_rows(data)
    for town in towns:
        code = town["code"]
        if code not in asia or code not in agcom:
            raise DataError(f"Fonti mancanti per il Comune {code}")
        validate_asia(code, asia[code])
        validate_agcom(code, agcom[code])

    local_units = data["metrics"]["localUnits"]
    local_by_code = {row["code"]: row for row in local_units["rows"]}
    for town in towns:
        code = town["code"]
        series = asia[code]["serie_storica"]
        values = [float(value) for value in series["ul"]]
        row = local_by_code[code]
        latest = values[-1]
        row["value"] = int(round(latest))
        row["formatted"] = _format_int(latest)
        row["series"] = {"years": series["anni"], "values": [int(round(v)) for v in values]}
        row["benchmarkValue"] = int(round(latest))
    local_totals = [float(asia[town["code"]]["serie_storica"]["ul"][-1]) for town in towns]
    local_units["aggregate"] = {
        "value": int(round(sum(local_totals))),
        "label": "Totale Versilia",
        "note": "Somma delle unità locali attive nei sette Comuni.",
    }
    local_units["method"] = {
        "type": "Dato ufficiale",
        "formula": "Stock di unità locali attive pubblicato da ISTAT ASIA-UL; serie 2018–2023 acquisita tramite Cruscotto Italia (AgID).",
        "caveat": "Le unità locali sono sedi operative, stabilimenti, uffici o negozi: non coincidono con il numero di imprese giuridiche. Un’impresa con più sedi può comparire in più Comuni.",
        "coverage": "7/7",
    }

    employees_rows: list[dict[str, Any]] = []
    avg_rows: list[dict[str, Any]] = []
    ul_change_rows: list[dict[str, Any]] = []
    emp_change_rows: list[dict[str, Any]] = []
    for town in towns:
        code = town["code"]
        series = asia[code]["serie_storica"]
        years = series["anni"]
        ul_values = [float(value) for value in series["ul"]]
        emp_values = [float(value) for value in series["addetti"]]
        avg_values = [emp / ul if ul else 0.0 for emp, ul in zip(emp_values, ul_values)]
        employees_rows.append(
            _row(
                town,
                emp_values[-1],
                _format_people(emp_values[-1]),
                {"years": years, "values": emp_values},
            )
        )
        avg_rows.append(
            _row(
                town,
                avg_values[-1],
                f"{_format_decimal(avg_values[-1], 2)} addetti/UL",
                {"years": years, "values": avg_values},
            )
        )
        ul_change = _pct_change(ul_values[0], ul_values[-1])
        emp_change = _pct_change(emp_values[0], emp_values[-1])
        ul_change_rows.append(_row(town, ul_change, _format_percent(ul_change)))
        emp_change_rows.append(_row(town, emp_change, _format_percent(emp_change)))

    total_emp_latest = sum(row["value"] for row in employees_rows)
    total_ul_latest = sum(row["value"] for row in local_units["rows"])
    total_emp_first = sum(float(asia[town["code"]]["serie_storica"]["addetti"][0]) for town in towns)
    total_ul_first = sum(float(asia[town["code"]]["serie_storica"]["ul"][0]) for town in towns)

    data["metrics"]["localEmployees"] = _metric(
        "localEmployees",
        "economia",
        "Addetti nelle unità locali",
        "Addetti nelle unità locali",
        "Addetti medi annui impiegati nelle unità locali attive presenti nel Comune.",
        "people",
        "2023",
        "ISTAT — ASIA unità locali",
        ASIA_SOURCE_URL,
        employees_rows,
        {
            "value": total_emp_latest,
            "label": "Totale Versilia",
            "note": "Somma degli addetti medi annui delle unità locali nei sette Comuni.",
        },
        "Dato ufficiale",
        "Addetti delle unità locali, media annua, misura LUEMPDAA del registro ISTAT ASIA-UL; acquisizione tramite Cruscotto Italia (AgID).",
        "Gli addetti sono riferiti al luogo di lavoro e non alla residenza. Il valore è una media annua e può contenere decimali.",
    )
    data["metrics"]["employeesPerLocalUnit"] = _metric(
        "employeesPerLocalUnit",
        "economia",
        "Addetti per unità locale",
        "Dimensione media delle unità locali",
        "Rapporto tra addetti medi annui e unità locali attive presenti nel Comune.",
        "decimal",
        "2023",
        "Elaborazione Osservatorio su dati ISTAT ASIA-UL",
        ASIA_SOURCE_URL,
        avg_rows,
        {
            "value": total_emp_latest / total_ul_latest,
            "label": "Rapporto Versilia",
            "note": "Totale degli addetti medi annui diviso per il totale delle unità locali dei sette Comuni.",
        },
        "Elaborazione Osservatorio su dati ufficiali",
        "addetti medi annui delle unità locali / unità locali attive",
        "È una dimensione media territoriale: non descrive la distribuzione interna delle imprese né la loro produttività.",
    )
    data["metrics"]["localUnitsChange"] = _metric(
        "localUnitsChange",
        "economia",
        "Variazione delle unità locali 2018–2023",
        "Variazione unità locali",
        "Variazione percentuale dello stock di unità locali attive tra il 2018 e il 2023.",
        "percent",
        "2018–2023",
        "Elaborazione Osservatorio su dati ISTAT ASIA-UL",
        ASIA_SOURCE_URL,
        ul_change_rows,
        {
            "value": _pct_change(total_ul_first, total_ul_latest),
            "label": "Variazione Versilia",
            "note": "Variazione calcolata sulla somma delle unità locali dei sette Comuni.",
        },
        "Elaborazione Osservatorio su dati ufficiali",
        "((unità locali 2023 / unità locali 2018) − 1) × 100",
        "Dal 2019 il regolamento europeo EBS ha modificato il criterio di attività delle imprese; il confronto con il 2018 va interpretato con cautela.",
    )
    data["metrics"]["localEmployeesChange"] = _metric(
        "localEmployeesChange",
        "economia",
        "Variazione degli addetti 2018–2023",
        "Variazione addetti",
        "Variazione percentuale degli addetti medi annui nelle unità locali tra il 2018 e il 2023.",
        "percent",
        "2018–2023",
        "Elaborazione Osservatorio su dati ISTAT ASIA-UL",
        ASIA_SOURCE_URL,
        emp_change_rows,
        {
            "value": _pct_change(total_emp_first, total_emp_latest),
            "label": "Variazione Versilia",
            "note": "Variazione calcolata sulla somma degli addetti medi annui dei sette Comuni.",
        },
        "Elaborazione Osservatorio su dati ufficiali",
        "((addetti medi annui 2023 / addetti medi annui 2018) − 1) × 100",
        "Il dato misura gli addetti nei luoghi di lavoro presenti sul territorio, non il tasso di occupazione dei residenti.",
    )

    ftth_pct_rows: list[dict[str, Any]] = []
    ftth_reached_rows: list[dict[str, Any]] = []
    ftth_unreached_rows: list[dict[str, Any]] = []
    ftth_20m_rows: list[dict[str, Any]] = []
    resident_households: list[float] = []
    reached_households: list[float] = []
    reached_20m_households: list[float] = []
    for town in towns:
        code = town["code"]
        kpi = agcom[code]["kpi"]
        resident = float(kpi["famiglie_residenti"])
        reached = float(kpi["famiglie_ftth"])
        reached_20m = float(kpi["famiglie_ftth_20m"])
        pct = float(kpi["copertura_ftth_desi_pct"])
        pct_20m = float(kpi["copertura_ftth_20m_pct"])
        unreached = max(resident - reached, 0.0)
        resident_households.append(resident)
        reached_households.append(reached)
        reached_20m_households.append(reached_20m)
        ftth_pct_rows.append(_row(town, pct, _format_percent(pct)))
        ftth_reached_rows.append(_row(town, reached, _format_int(reached)))
        ftth_unreached_rows.append(_row(town, unreached, _format_int(unreached)))
        ftth_20m_rows.append(_row(town, pct_20m, _format_percent(pct_20m)))

    data["metrics"]["ftthCoverageDesi"] = _metric(
        "ftthCoverageDesi",
        "mobilita",
        "Copertura FTTH DESI",
        "Copertura FTTH",
        "Quota delle famiglie residenti raggiunte da una rete fissa in fibra fino all’edificio secondo la metrica europea DESI.",
        "percent",
        "31 dicembre 2025",
        "AGCOM — Broadband Map",
        AGCOM_SOURCE_URL,
        ftth_pct_rows,
        {
            "value": _weighted_pct(reached_households, resident_households),
            "label": "Copertura ponderata Versilia",
            "note": "Famiglie FTTH complessive divise per le famiglie residenti complessive dei sette Comuni.",
        },
        "Dato ufficiale",
        "Copertura FTTH DESI pubblicata da AGCOM; acquisizione tramite Cruscotto Italia (AgID).",
        "Indica la disponibilità dichiarata della rete, non gli abbonamenti attivi, la velocità effettiva o la certezza di attivazione per ogni singolo civico.",
    )
    data["metrics"]["ftthReachedHouseholds"] = _metric(
        "ftthReachedHouseholds",
        "mobilita",
        "Famiglie raggiunte da FTTH",
        "Famiglie raggiunte da FTTH",
        "Numero di famiglie residenti considerate raggiunte dalla rete FTTH secondo la metrica DESI.",
        "number",
        "31 dicembre 2025",
        "AGCOM — Broadband Map",
        AGCOM_SOURCE_URL,
        ftth_reached_rows,
        {
            "value": sum(reached_households),
            "label": "Totale Versilia",
            "note": "Somma delle famiglie raggiunte nei sette Comuni.",
        },
        "Dato ufficiale",
        "Famiglie FTTH pubblicate da AGCOM nella reportistica comunale Broadband Map.",
        "Il numero deriva dalla modellazione territoriale AGCOM e non coincide con gli accessi o i contratti attivi.",
    )
    data["metrics"]["ftthUnreachedHouseholds"] = _metric(
        "ftthUnreachedHouseholds",
        "mobilita",
        "Famiglie non raggiunte da FTTH",
        "Famiglie non raggiunte",
        "Stima contabile delle famiglie residenti non comprese tra quelle raggiunte da FTTH secondo la metrica DESI.",
        "number",
        "31 dicembre 2025",
        "Elaborazione Osservatorio su dati AGCOM Broadband Map",
        AGCOM_SOURCE_URL,
        ftth_unreached_rows,
        {
            "value": sum(resident_households) - sum(reached_households),
            "label": "Totale Versilia",
            "note": "Famiglie residenti complessive meno famiglie FTTH complessive nei sette Comuni.",
        },
        "Elaborazione Osservatorio su dati ufficiali",
        "famiglie residenti AGCOM − famiglie raggiunte da FTTH DESI",
        "È il complemento aritmetico della copertura dichiarata AGCOM, non un censimento dei civici privi di servizio attivabile.",
    )
    data["metrics"]["ftthCoverage20m"] = _metric(
        "ftthCoverage20m",
        "mobilita",
        "Copertura FTTH entro 20 metri",
        "FTTH entro 20 metri",
        "Quota delle famiglie residenti con infrastruttura FTTH dichiarata entro 20 metri dall’abitazione.",
        "percent",
        "31 dicembre 2025",
        "AGCOM — Broadband Map",
        AGCOM_SOURCE_URL,
        ftth_20m_rows,
        {
            "value": _weighted_pct(reached_20m_households, resident_households),
            "label": "Copertura ponderata Versilia",
            "note": "Famiglie con FTTH entro 20 metri divise per le famiglie residenti complessive dei sette Comuni.",
        },
        "Dato ufficiale",
        "Copertura calcolata da AGCOM sulla prossimità della rete FTTH entro 20 metri dall’abitazione.",
        "La prossimità fisica non garantisce da sola la vendibilità commerciale o l’attivazione immediata del servizio.",
    )

    economy = data["themes"]["economia"]
    economy["description"] = "Redditi, unità locali, addetti, struttura produttiva, imprenditorialità e capacità turistica."
    economy["metrics"] = _insert_after(economy["metrics"], "localUnits", NEW_ECONOMY_KEYS)
    for section in economy["sections"]:
        if section.get("key") == "produzione":
            section["description"] = "Consistenza, dimensione e dinamica delle unità locali e degli addetti, produttività e specializzazione."
            section["metrics"] = _insert_after(section["metrics"], "localUnits", NEW_ECONOMY_KEYS)
    economy["featured"] = ["income", "localEmployees", "tourismIntensity"]

    mobility = data["themes"]["mobilita"]
    mobility["label"] = "Mobilità e infrastrutture"
    mobility["question"] = "Come si muove e quanto è connessa la Versilia?"
    mobility["description"] = "Pendolarismo, parco veicolare, ricarica elettrica, connettività digitale e sicurezza stradale."
    mobility["metrics"] = _insert_after(mobility["metrics"], "evPoints", NEW_BROADBAND_KEYS)
    connectivity_section = {
        "key": "connettivita",
        "label": "Connettività digitale",
        "description": "Copertura della rete fissa FTTH e famiglie raggiunte secondo la reportistica comunale AGCOM.",
        "metrics": NEW_BROADBAND_KEYS,
    }
    mobility["sections"] = _replace_or_append_section(
        mobility["sections"], connectivity_section, before_key="sicurezza"
    )
    mobility["featured"] = ["outsideMunicipality", "ftthCoverageDesi", "roadInjuries"]

    data["version"] = "v1.7.0"
    data["updated"] = "7 agosto 2026"

    snapshot_towns: list[dict[str, Any]] = []
    for town in towns:
        code = town["code"]
        snapshot_towns.append(
            {
                **town,
                "asia": {
                    "years": asia[code]["serie_storica"]["anni"],
                    "localUnits": asia[code]["serie_storica"]["ul"],
                    "employeesAverageAnnual": asia[code]["serie_storica"]["addetti"],
                },
                "agcom": {
                    "dataPeriod": agcom[code]["_data_period"],
                    "residentHouseholds": agcom[code]["kpi"]["famiglie_residenti"],
                    "ftthHouseholds": agcom[code]["kpi"]["famiglie_ftth"],
                    "ftthHouseholdsWithin20m": agcom[code]["kpi"]["famiglie_ftth_20m"],
                    "ftthDesiCoveragePercent": agcom[code]["kpi"]["copertura_ftth_desi_pct"],
                    "ftthWithin20mCoveragePercent": agcom[code]["kpi"]["copertura_ftth_20m_pct"],
                },
            }
        )
    snapshot = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "scope": "Sette Comuni della Versilia storica",
        "acquisitionLayer": {
            "name": "AgID — Cruscotto Italia",
            "url": AGID_PROJECT_URL,
            "note": "Cruscotto Italia normalizza gli shard comunali; titolari dei dati restano ISTAT e AGCOM.",
        },
        "sources": {
            "asia": {
                "owner": "ISTAT",
                "dataset": "Archivio Statistico Imprese Attive — Unità Locali (ASIA-UL)",
                "url": ASIA_SOURCE_URL,
                "license": "CC BY 3.0 IT",
                "years": [2018, 2019, 2020, 2021, 2022, 2023],
            },
            "agcom": {
                "owner": "AGCOM",
                "dataset": "Broadband Map — reportistica comunale rete cablata",
                "url": AGCOM_SOURCE_URL,
                "license": "CC BY 4.0",
                "dataPeriod": "31/12/2025",
            },
        },
        "formulas": {
            "employeesPerLocalUnit": "addetti medi annui / unità locali attive",
            "localUnitsChange": "((UL 2023 / UL 2018) - 1) * 100",
            "localEmployeesChange": "((addetti 2023 / addetti 2018) - 1) * 100",
            "ftthUnreachedHouseholds": "famiglie residenti - famiglie FTTH DESI",
        },
        "towns": snapshot_towns,
    }
    return data, snapshot


def update_count_files(metric_count: int, previous_count: int) -> None:
    registry = _json_load(SOURCE_REGISTRY)
    registry["expectedMetricCount"] = metric_count
    _json_write(SOURCE_REGISTRY, registry)

    replacements = (
        (README, [
            (rf"- {previous_count} indicatori;", f"- {metric_count} indicatori;"),
            (rf"valida i {previous_count} indicatori", f"valida i {metric_count} indicatori"),
        ]),
        (MONTHLY_DOC, [
            (rf"\b{previous_count} indicatori\b", f"{metric_count} indicatori"),
        ]),
    )
    for path, rules in replacements:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, replacement in rules:
            text = re.sub(pattern, replacement, text)
        path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Directory fixture con sottocartelle asia/ e agcom_bbmap/.",
    )
    parser.add_argument("--site-data", type=Path, default=SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = parser.parse_args(argv)

    source_data = _json_load(args.site_data)
    towns = _town_rows(source_data)
    codes = [town["code"] for town in towns]
    asia, agcom, provenance = load_source_shards(codes, args.source_dir)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    updated, snapshot = apply_updates(source_data, asia, agcom, generated_at)
    snapshot["provenance"] = provenance

    previous_count = len(source_data["metrics"])
    metric_count = len(updated["metrics"])
    expected = previous_count + len(NEW_ECONOMY_KEYS) + len(NEW_BROADBAND_KEYS)
    if metric_count != expected:
        raise DataError(
            f"Conteggio indicatori inatteso: {metric_count}; previsto {expected}"
        )

    _json_write(args.site_data, updated)
    _json_write(args.snapshot, snapshot)
    if args.site_data.resolve() == SITE_DATA.resolve():
        update_count_files(metric_count, previous_count)

    print(
        json.dumps(
            {
                "status": "ok",
                "metricCount": metric_count,
                "newMetrics": NEW_ECONOMY_KEYS + NEW_BROADBAND_KEYS,
                "snapshot": str(args.snapshot),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
