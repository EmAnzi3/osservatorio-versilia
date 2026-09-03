#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
BILANCI_SNAPSHOT = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
FINANCIAL_SNAPSHOT = ROOT / "data" / "source-snapshots" / "salute-finanziaria-v129.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
APP03_PATH = ROOT / "assets" / "app-parts" / "03.txt"
README_PATH = ROOT / "README.md"

VERSION = "v1.29.0"
UPDATED = "3 settembre 2026"
METRIC_KEY = "financialDebtProfile"
TOWN_ORDER = [
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def town_meta(data: dict, town: str) -> dict:
    item = next(row for row in data["towns"] if row["name"] == town)
    return {
        "town": town,
        "code": item["code"],
        "slug": town.lower().replace(" ", "-").replace("à", "a"),
    }


def population_series(bilanci: dict, town: str, years: list[int]) -> list[float]:
    source = bilanci["raw"][town]["years"]
    values = []
    for year in years:
        value = source[str(year)].get("population_at_1_january")
        if value is None or float(value) <= 0:
            raise ValueError(f"Popolazione non valida per {town} {year}: {value}")
        values.append(float(value))
    return values


def ratio_percent(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise ValueError(f"Denominatore non positivo: {denominator}")
    return numerator / denominator * 100.0


def debt_per_resident(debt: float, population: float) -> float:
    if population <= 0:
        raise ValueError(f"Popolazione non positiva: {population}")
    return debt / population


def part(key: str, label: str, selector: str, unit: str, values: list[float], **extra) -> dict:
    result = {
        "key": key,
        "label": label,
        "selectorLabel": selector,
        "unit": unit,
        "value": values[-1],
        "series": {"years": list(range(2019, 2026)), "values": values},
    }
    result.update(extra)
    return result


def build_metric(data: dict, bilanci: dict, snapshot: dict) -> dict:
    years = snapshot["years"]
    if years != list(range(2019, 2026)):
        raise ValueError(f"Storico inatteso: {years}")

    rows = []
    aggregate_debt = [0.0] * len(years)
    aggregate_population = [0.0] * len(years)
    aggregate_interest = [0.0] * len(years)
    aggregate_revenue = [0.0] * len(years)
    sustainability_weighted_num = [0.0] * len(years)

    for town in TOWN_ORDER:
        raw = snapshot["towns"][town]
        populations = population_series(bilanci, town, years)
        revenues = [float(v) for v in raw["current_revenue"]]
        interests = [float(v) for v in raw["interest_commitments"]]
        debts = [float(v) for v in raw["debt_financing_d1"]]
        sustainability = [None if v is None else float(v) for v in raw["debt_sustainability_10_3"]]
        provenance = raw["debt_sustainability_source"]

        if any(v is None for v in sustainability):
            raise ValueError(f"10.3 incompleto per {town}: {sustainability}")
        if len({len(populations), len(revenues), len(interests), len(debts), len(sustainability), len(provenance)}) != 1:
            raise ValueError(f"Lunghezze non coerenti per {town}")

        debt_values = [debt_per_resident(debt, pop) for debt, pop in zip(debts, populations, strict=True)]
        interest_values = [ratio_percent(value, revenue) for value, revenue in zip(interests, revenues, strict=True)]

        for index, _year in enumerate(years):
            aggregate_debt[index] += debts[index]
            aggregate_population[index] += populations[index]
            aggregate_interest[index] += interests[index]
            aggregate_revenue[index] += revenues[index]
            sustainability_weighted_num[index] += sustainability[index] * revenues[index]

        row_parts = [
            part(
                "debtPerResident",
                "Debito finanziario pro capite",
                "Debito finanziario pro capite",
                "currencyPerResident",
                debt_values,
                provenance="Ricalcolato da D1 Debiti da finanziamento / popolazione residente al 1° gennaio.",
            ),
            part(
                "interestShare",
                "Interessi sulle entrate correnti",
                "Interessi sulle entrate correnti",
                "percent2",
                interest_values,
                provenance="Indicatore 6.1 ricalcolato dagli impegni per interessi passivi e dagli accertamenti dei Titoli 1+2+3.",
            ),
            part(
                "debtSustainability",
                "Sostenibilità dei debiti finanziari",
                "Sostenibilità dei debiti finanziari",
                "percent2",
                sustainability,
                provenanceSeries=provenance,
                provenance="PDI 10.3; normalizzazioni e ricostruzioni sono congelate nello snapshot con provenienza annuale.",
            ),
        ]
        row = {
            **town_meta(data, town),
            "value": debt_values[-1],
            "formatted": None,
            "series": row_parts[0]["series"],
            "normalized": None,
            "benchmarkValue": debt_values[-1],
            "parts": row_parts,
        }
        if town == "Massarosa":
            row["contextNote"] = (
                "Massarosa ha dichiarato il dissesto il 27/11/2019. Durante il periodo di dissesto "
                "la gestione OSL delle passività pregresse ha avuto un perimetro separato: il debito finanziario D1 "
                "del Rendiconto ordinario non rappresenta quindi l’intero insieme delle passività gestite dalla procedura."
            )
        rows.append(row)

    debt_aggregate = [debt_per_resident(d, p) for d, p in zip(aggregate_debt, aggregate_population, strict=True)]
    interest_aggregate = [ratio_percent(i, r) for i, r in zip(aggregate_interest, aggregate_revenue, strict=True)]
    sustainability_aggregate = [n / r for n, r in zip(sustainability_weighted_num, aggregate_revenue, strict=True)]

    aggregate_parts = [
        part(
            "debtPerResident",
            "Debito finanziario pro capite",
            "Debito finanziario pro capite",
            "currencyPerResident",
            debt_aggregate,
            aggregation="Σ debiti da finanziamento D1 / Σ popolazione al 1° gennaio",
        ),
        part(
            "interestShare",
            "Interessi sulle entrate correnti",
            "Interessi sulle entrate correnti",
            "percent2",
            interest_aggregate,
            aggregation="Σ interessi passivi / Σ entrate correnti × 100",
        ),
        part(
            "debtSustainability",
            "Sostenibilità dei debiti finanziari",
            "Sostenibilità dei debiti finanziari",
            "percent2",
            sustainability_aggregate,
            aggregation="Media ponderata dei rapporti comunali 10.3 con peso pari alle entrate correnti; non è un indicatore OpenBDAP ufficiale della Versilia.",
        ),
    ]

    return {
        "meta": {
            "key": METRIC_KEY,
            "theme": "bilanci",
            "label": "Debito finanziario e costo degli interessi",
            "shortLabel": "Debito e interessi",
            "description": (
                "Tre letture complementari del debito comunale: debiti da finanziamento per residente, "
                "peso degli interessi sulle entrate correnti e sostenibilità dei debiti finanziari secondo il Piano degli indicatori."
            ),
            "unit": "currencyPerResident",
            "year": "2025",
            "source": "RGS — OpenBDAP · Rendiconto",
            "polarity": "neutral",
            "compositeType": "financialProfile",
            "selectorLabel": "Lettura",
            "searchTerms": [
                "debito", "indebitamento", "debiti finanziari", "interessi passivi",
                "sostenibilità debito", "openbdap 6.1", "openbdap 10.3", "openbdap 10.4",
            ],
        },
        "sourceUrl": snapshot["source"]["portal_url"],
        "rows": rows,
        "aggregate": {
            "value": debt_aggregate[-1],
            "label": "Versilia · debito finanziario pro capite",
            "note": (
                "Gli aggregati non sono medie semplici dei sette valori comunali: il debito pro capite è il rapporto fra "
                "i debiti D1 e la popolazione complessivi; il 6.1 è il rapporto fra interessi ed entrate complessivi; "
                "il 10.3 è ponderato sulle entrate correnti comunali."
            ),
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali OpenBDAP",
            "formula": (
                "10.4: debiti da finanziamento D1 al 31/12 / popolazione residente al 1° gennaio; "
                "6.1: impegni Macroaggregato 1.7 Interessi passivi / accertamenti Titoli 1+2+3 × 100; "
                "10.3: indicatore ufficiale del Piano degli indicatori, con le sole normalizzazioni/ricostruzioni documentate nello snapshot."
            ),
            "caveat": (
                "Il debito finanziario D1 non coincide con tutte le passività dell’ente: non comprende automaticamente debiti commerciali, "
                "debiti fuori bilancio o passività gestite in un perimetro straordinario. Per Massarosa il dissesto dichiarato nel 2019 e la "
                "gestione OSL delle passività pregresse introducono una discontinuità di perimetro nella lettura storica. "
                "Il 10.3 di Camaiore 2023–2024 è normalizzato dividendo per 100 per perdita sistematica del separatore decimale; "
                "Forte dei Marmi 2019 e 2023–2025 è ricostruito dai componenti ufficiali, con 2023–2025 pari a zero perché il numeratore è verificato nullo."
            ),
            "coverage": "7/7 · 2019–2025",
        },
    }


def update_theme(data: dict) -> None:
    theme = data["themes"]["bilanci"]
    if METRIC_KEY not in theme["metrics"]:
        theme["metrics"].append(METRIC_KEY)
    section = next((item for item in theme.get("sections", []) if item.get("key") == "equilibri"), None)
    if section is None:
        raise ValueError("Sezione bilanci/equilibri non trovata")
    if METRIC_KEY not in section["metrics"]:
        section["metrics"].append(METRIC_KEY)


def patch_app() -> None:
    text = APP03_PATH.read_text(encoding="utf-8")
    old_group = "['securityMeasures','agricultureProfile']"
    new_group = "['securityMeasures','agricultureProfile','financialProfile']"
    count = text.count(old_group)
    if count:
        if count < 5:
            raise ValueError(f"Hook compositi attesi non trovati: {count}")
        text = text.replace(old_group, new_group)
    elif text.count(new_group) < 5:
        raise ValueError("Hook compositi financialProfile non trovati nello stato già materializzato")

    marker = "  function compositeTownMarkup(metric, row) {\n"
    if "function financialProfileHistoryMarkup" not in text:
        if marker not in text:
            raise ValueError("Marker compositeTownMarkup non trovato")
        helper = '''  function financialProfileHistoryMarkup(metric,row,index=0) {\n    const part=row.parts?.[index] || row.parts?.[0] || {};\n    const unit=part.unit || metric.meta.unit;\n    const chart=part.series?.values?.length ? seriesChart(part.series,unit,`${part.label || metric.meta.label} a ${row.town}`) : '<p class="aggregate-note">Storico non disponibile.</p>';\n    const provenance=part.provenance ? `<p class="aggregate-note"><b>Origine del dato:</b> ${html(part.provenance)}</p>` : '';\n    const context=row.contextNote ? `<p class="aggregate-note"><b>Nota di lettura:</b> ${html(row.contextNote)}</p>` : '';\n    return `${chart}${provenance}${context}`;\n  }\n\n'''
        text = text.replace(marker, helper + marker, 1)

    branch_marker = "    const parts = row.parts || [];\n    if (metric.meta.compositeType === 'sexBreakdown') return '';"
    if "data-financial-profile-history" not in text:
        if branch_marker not in text:
            raise ValueError("Marker parts/compositeTownMarkup non trovato")
        branch = '''    const parts = row.parts || [];\n    if (metric.meta.compositeType === 'financialProfile') {\n      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div><div data-financial-profile-history>${financialProfileHistoryMarkup(metric,row,0)}</div>`;\n    }\n    if (metric.meta.compositeType === 'sexBreakdown') return '';'''
        text = text.replace(branch_marker, branch, 1)

    choice_marker = "        updateExtractiveTownPosition(metric,row,choice,position);\n        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));"
    if "financialProfileHistoryMarkup(metric,row,index)" not in text:
        if choice_marker not in text:
            raise ValueError("Marker applyChoice non trovato")
        replacement = '''        updateExtractiveTownPosition(metric,row,choice,position);\n        if(metric.meta.compositeType === 'financialProfile') {\n          const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);\n          const historyHost=container.querySelector('[data-financial-profile-history]');\n          if(historyHost) historyHost.innerHTML=financialProfileHistoryMarkup(metric,row,index);\n        }\n        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));'''
        text = text.replace(choice_marker, replacement, 1)

    APP03_PATH.write_text(text, encoding="utf-8")


def update_registry() -> None:
    registry = load(REGISTRY_PATH)
    registry["expectedMetricCount"] = 181
    registry["expectedInlineMetricCount"] = 177
    registry["expectedExternalMetricCount"] = 4
    registry.setdefault("metricOverrides", {})[METRIC_KEY] = {"profile": "openbdap-annual"}
    dump(REGISTRY_PATH, registry)


def update_readme() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    replacements = {
        "Versione dati corrente: **v1.28.0** — 2 settembre 2026.": f"Versione dati corrente: **{VERSION}** — {UPDATED}.",
        "180 indicatori nel catalogo canonico: 176 con valori incorporati e 4 climatici con storici separati": "181 indicatori nel catalogo canonico: 177 con valori incorporati e 4 climatici con storici separati",
        "`indicatori/`: 176 pagine canoniche generate in build": "`indicatori/`: 177 pagine canoniche generate in build",
        "catalogo canonico dei 180 indicatori, con dati incorporati per 176": "catalogo canonico dei 181 indicatori, con dati incorporati per 177",
        "catalogo e i metadati dei 180 indicatori": "catalogo e i metadati dei 181 indicatori",
        "valida tutti i 180 indicatori canonici, la ripartizione fra 176 valori incorporati e 4 storici climatici": "valida tutti i 181 indicatori canonici, la ripartizione fra 177 valori incorporati e 4 storici climatici",
        "ciascuno dei 176 indicatori incorporati": "ciascuno dei 177 indicatori incorporati",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise ValueError(f"README: né baseline né valore materializzato trovati: {old}")
    README_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    data = load(DATA_PATH)
    bilanci = load(BILANCI_SNAPSHOT)
    snapshot = load(FINANCIAL_SNAPSHOT)

    metric = build_metric(data, bilanci, snapshot)
    data["metrics"][METRIC_KEY] = metric
    update_theme(data)
    data["version"] = VERSION
    data["updated"] = UPDATED
    dump(DATA_PATH, data)

    patch_app()
    update_registry()
    update_readme()
    print(f"Materializzato {METRIC_KEY}: 7/7 Comuni, 2019–2025, versione {VERSION}.")


if __name__ == "__main__":
    main()
