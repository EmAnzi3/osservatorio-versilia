#!/usr/bin/env python3
"""Materializza il primo draft di Costi e fiscalità locale.

Il draft pubblica soltanto gli indicatori che hanno superato l'audit 7/7.
Al 15 agosto 2026 questo significa l'addizionale comunale IRPEF effettiva
per tre redditi imponibili standardizzati. Gli altri candidati restano nello
snapshot di audit e non vengono inseriti nel catalogo.

Lo script è idempotente e non modifica la versione dati: il bump verrà deciso
solo dopo il collaudo dell'intera fase.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "costi-fiscalita-redditi-draft-2026-08.json"
APP00 = ROOT / "assets" / "app-parts" / "00.txt"

METRIC_KEY = "municipalIrpef"
PROFILE_KEY = "mef-municipal-irpef-annual"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def eur(value: float) -> str:
    text = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} €"


def build_irpef(data: dict, snapshot: dict) -> dict:
    raw = snapshot["municipalIrpef"]
    scenarios = [int(value) for value in raw["scenarios"]]
    source_url = raw["source"]["url"]
    identity = {
        row["town"]: {"code": row["code"], "slug": row["slug"]}
        for row in data["metrics"]["income"]["rows"]
    }

    rows = []
    scenario_values: dict[int, list[float]] = {scenario: [] for scenario in scenarios}
    # Mantiene l'ordine territoriale già usato dal catalogo corrente.
    for income_row in data["metrics"]["income"]["rows"]:
        town = income_row["town"]
        town_raw = raw["towns"][town]
        parts = []
        component_series = {}
        for scenario in scenarios:
            value = float(town_raw["amounts"][str(scenario)])
            scenario_values[scenario].append(value)
            label = f"Reddito imponibile {scenario:,.0f} €".replace(",", ".")
            selector = f"{scenario:,.0f} €".replace(",", ".")
            parts.append({
                "label": label,
                "selectorLabel": selector,
                "value": value,
                "unit": "currency",
            })
            component_series[selector] = {"years": [raw["year"]], "values": [value]}
        rows.append({
            "town": town,
            "code": identity[town]["code"],
            "slug": identity[town]["slug"],
            "value": parts[0]["value"],
            "formatted": eur(parts[0]["value"]),
            "series": {"years": [raw["year"]], "values": [parts[0]["value"]]},
            "normalized": None,
            "benchmarkValue": parts[0]["value"],
            "parts": parts,
            "componentSeries": component_series,
        })

    aggregate_parts = []
    for scenario in scenarios:
        value = statistics.fmean(scenario_values[scenario])
        label = f"Reddito imponibile {scenario:,.0f} €".replace(",", ".")
        selector = f"{scenario:,.0f} €".replace(",", ".")
        aggregate_parts.append({
            "label": label,
            "selectorLabel": selector,
            "value": value,
            "unit": "currency",
        })

    return {
        "meta": {
            "key": METRIC_KEY,
            "theme": "economia",
            "label": "Addizionale comunale IRPEF effettiva",
            "shortLabel": "Addizionale comunale IRPEF",
            "description": "Importo annuo dell'addizionale comunale IRPEF dovuta applicando aliquote, scaglioni ed esenzioni del Comune allo stesso reddito imponibile teorico. Il selettore cambia lo scenario di reddito.",
            "unit": "currency",
            "year": str(raw["year"]),
            "source": "Dipartimento delle Finanze — MEF",
            "polarity": "neutral",
            "compositeType": "securityMeasures",
            "selectorLabel": "Reddito imponibile",
            "searchTerms": [
                "addizionale comunale",
                "irpef comunale",
                "aliquota irpef",
                "fiscalità locale",
                "tasse comunali",
            ],
        },
        "sourceUrl": source_url,
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Media semplice dei 7 comuni",
            "note": "Ogni Comune pesa allo stesso modo. È un benchmark fiscale standardizzato, non una stima del gettito o della famiglia media.",
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su disciplina ufficiale MEF",
            "formula": "Per ciascuno scenario: se il reddito imponibile non supera la soglia di esenzione, imposta = 0; altrimenti si applicano all'intero imponibile l'aliquota unica o gli scaglioni progressivi pubblicati dal MEF.",
            "caveat": "Gli scenari 20.000 €, 30.000 € e 50.000 € servono a confrontare la struttura della fiscalità comunale. Non rappresentano redditi disponibili familiari e non includono l'addizionale regionale o l'IRPEF statale.",
            "coverage": "7/7",
        },
    }


def update_economy_theme(data: dict) -> None:
    theme = data["themes"]["economia"]
    metrics = theme.setdefault("metrics", [])
    if METRIC_KEY not in metrics:
        anchor = "incomeDistribution"
        index = metrics.index(anchor) + 1 if anchor in metrics else 0
        metrics.insert(index, METRIC_KEY)

    sections = theme.setdefault("sections", [])
    fiscal = next((section for section in sections if section.get("key") == "costi-fiscalita"), None)
    if fiscal is None:
        fiscal = {
            "key": "costi-fiscalita",
            "label": "Costi e fiscalità locale",
            "description": "Confronti standardizzati sui costi e sui tributi comunali, pubblicati solo quando la disciplina è omogeneamente ricostruibile 7/7.",
            "metrics": [METRIC_KEY],
        }
        redditi_index = next((i for i, section in enumerate(sections) if section.get("key") == "redditi"), -1)
        sections.insert(redditi_index + 1, fiscal)
    elif METRIC_KEY not in fiscal.setdefault("metrics", []):
        fiscal["metrics"].append(METRIC_KEY)

    theme["description"] = "Redditi, fiscalità locale, unità locali, addetti, struttura produttiva, imprenditorialità e capacità turistica."


def update_registry(data: dict, snapshot: dict) -> None:
    registry = load(REGISTRY_PATH)
    external = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedInlineMetricCount"] = len(data["metrics"]) - external
    registry["expectedExternalMetricCount"] = external

    source = snapshot["municipalIrpef"]["source"]
    registry.setdefault("sourceProfiles", {})[PROFILE_KEY] = {
        "publisher": "Dipartimento delle Finanze — MEF",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la pubblicazione delle delibere comunali nell'apposita banca dati MEF",
        "acquisitionMethod": "Consultazione della banca dati ufficiale delle aliquote dell'addizionale comunale IRPEF; calcolo degli importi su scenari standardizzati conservato nello snapshot versionato.",
        "licenseName": "Condizioni indicate dal MEF",
        "licenseUrl": source["url"],
    }
    registry.setdefault("sourceProfileByUrl", {})[source["url"]] = PROFILE_KEY
    registry.setdefault("metricOverrides", {})[METRIC_KEY] = {"profile": PROFILE_KEY}
    save(REGISTRY_PATH, registry)


def patch_search_synonyms() -> None:
    text = APP00.read_text(encoding="utf-8")
    if "municipalIrpef:" in text:
        return
    anchor = "    incomeDistribution: ['fasce reddito', 'redditi bassi', 'irpef', 'dichiaranti', 'oltre 55000'],"
    if anchor not in text:
        raise RuntimeError("Anchor searchSynonyms incomeDistribution non trovato")
    replacement = (
        anchor
        + "\n    municipalIrpef: ['addizionale comunale', 'irpef comunale', 'aliquota irpef', 'fiscalità locale', 'tasse comunali'],"
    )
    APP00.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")


def main() -> None:
    data = load(DATA_PATH)
    snapshot = load(SNAPSHOT_PATH)
    data["metrics"][METRIC_KEY] = build_irpef(data, snapshot)
    update_economy_theme(data)
    data["costsFiscalDraft"] = {
        "status": "draft",
        "auditDate": snapshot["created"],
        "publishedInDraft": [METRIC_KEY],
        "notPublished": [
            "tari",
            "imu",
            "fuelPrices",
            "schoolMeals",
            "wasteServiceCost",
            "inflation",
            "incomeHistory",
            "realIncome",
        ],
        "note": "Entrano nel catalogo solo i candidati con dati già materializzati e verificati 7/7; gli altri restano nello snapshot di audit.",
    }
    save(DATA_PATH, data)
    update_registry(data, snapshot)
    patch_search_synonyms()
    print(
        f"Draft costi/fiscalità applicato: {len(data['metrics'])} indicatori "
        f"({METRIC_KEY} aggiunto; versione dati invariata {data.get('version')})."
    )


if __name__ == "__main__":
    main()
