#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
APP_PATH = ROOT / "assets" / "app-core.js"
README_PATH = ROOT / "README.md"

VERSION = "v1.6.0"
UPDATED = "6 agosto 2026"
SOURCE_URL = "https://openbdap.rgs.mef.gov.it/it/FET/Analizza"

TOWN_ORDER = [
    "Massarosa",
    "Viareggio",
    "Camaiore",
    "Pietrasanta",
    "Seravezza",
    "Forte dei Marmi",
    "Stazzema",
]

CASH_METRICS = [
    "siopePayments",
    "currentPayments",
    "capitalPayments",
    "cashReceiptsPerResident",
    "cashBalancePerResident",
]

NEW_METRIC_KEYS = [
    "currentRevenueAccruedPerResident",
    "currentExpenditureCommittedPerResident",
    "capitalExpenditureCommittedPerResident",
    "ownRevenueShare",
    "currentCollectionCapacity",
    "currentPaymentCapacity",
    "availableAdministrationResultPerResident",
    "rigidExpenditureShare",
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
]

METRIC_META = {
    "currentRevenueAccruedPerResident": {
        "label": "Entrate correnti accertate per residente",
        "shortLabel": "Entrate correnti",
        "description": "Accertamenti dei primi tre titoli delle entrate, rapportati alla popolazione residente.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "(accertamenti titoli 1 + 2 + 3 delle entrate) / popolazione residente",
        "caveat": "Gli accertamenti sono crediti giuridicamente riconosciuti dal Comune e non coincidono con gli incassi di cassa.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "currentExpenditureCommittedPerResident": {
        "label": "Spesa corrente impegnata per residente",
        "shortLabel": "Spesa corrente impegnata",
        "description": "Impegni del titolo 1 della spesa, destinati a servizi e funzionamento, rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni del titolo 1 della spesa / popolazione residente",
        "caveat": "Gli impegni sono obbligazioni di spesa assunte nell’esercizio e non coincidono con i pagamenti di cassa.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "capitalExpenditureCommittedPerResident": {
        "label": "Spesa in conto capitale impegnata per residente",
        "shortLabel": "Investimenti impegnati",
        "description": "Impegni del titolo 2 della spesa, prevalentemente destinati agli investimenti, rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni del titolo 2 della spesa / popolazione residente",
        "caveat": "Il valore può oscillare molto tra gli anni per la concentrazione di singole opere; non misura da solo la qualità o l’effettiva conclusione degli investimenti.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "ownRevenueShare": {
        "label": "Quota delle entrate proprie",
        "shortLabel": "Entrate proprie",
        "description": "Incidenza delle entrate tributarie ed extratributarie accertate sul totale delle entrate correnti.",
        "unit": "percent",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "(accertamenti titolo 1 + titolo 3) / accertamenti titoli 1 + 2 + 3 × 100",
        "caveat": "È un’elaborazione dell’Osservatorio. Un valore elevato dipende anche da fiscalità locale, tariffe, patrimonio e caratteristiche turistiche del Comune.",
        "aggregate_label": "Valore ponderato Versilia",
        "aggregate_note": "Rapporto calcolato sui totali dei sette Comuni.",
    },
    "currentCollectionCapacity": {
        "label": "Capacità di riscossione corrente",
        "shortLabel": "Riscossione corrente",
        "description": "Quota delle entrate correnti accertate nell’anno effettivamente riscossa in conto competenza.",
        "unit": "percent",
        "polarity": "positive",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "riscossioni in conto competenza dei titoli 1 + 2 + 3 / accertamenti dei titoli 1 + 2 + 3 × 100",
        "caveat": "Esclude le riscossioni riferite ai residui degli anni precedenti. Tempi e modalità di incasso differiscono tra tributi, trasferimenti ed entrate extratributarie.",
        "aggregate_label": "Valore ponderato Versilia",
        "aggregate_note": "Rapporto calcolato sui totali dei sette Comuni.",
    },
    "currentPaymentCapacity": {
        "label": "Capacità di pagamento corrente",
        "shortLabel": "Pagamento corrente",
        "description": "Quota degli impegni di spesa corrente dell’anno pagata in conto competenza.",
        "unit": "percent",
        "polarity": "positive",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "pagamenti in conto competenza del titolo 1 / impegni del titolo 1 × 100",
        "caveat": "Esclude i pagamenti relativi ai residui degli esercizi precedenti e non rappresenta da sola la tempestività dei pagamenti ai fornitori.",
        "aggregate_label": "Valore ponderato Versilia",
        "aggregate_note": "Rapporto calcolato sui totali dei sette Comuni.",
    },
    "availableAdministrationResultPerResident": {
        "label": "Parte disponibile del risultato di amministrazione per residente",
        "shortLabel": "Risultato disponibile",
        "description": "Quota disponibile del risultato di amministrazione, positiva o negativa, rapportata ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "voce 0502 “Totale parte disponibile” dell’allegato A / popolazione residente",
        "caveat": "Non equivale al saldo di cassa. Un valore positivo non è automaticamente interamente spendibile né costituisce da solo una misura di buona gestione; un valore negativo segnala un disavanzo da considerare nel contesto del rendiconto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Somma delle parti disponibili dei sette Comuni rapportata alla popolazione complessiva.",
    },
    "rigidExpenditureShare": {
        "label": "Incidenza delle spese rigide",
        "shortLabel": "Spese rigide",
        "description": "Peso di ripiano del disavanzo, personale e servizio del debito sulle entrate correnti.",
        "unit": "percent",
        "polarity": "negative",
        "type": "Indicatore ufficiale OpenBDAP",
        "formula": "Indicatore ufficiale 1.1 del Piano degli indicatori allegato al rendiconto",
        "caveat": "L’indicatore è pubblicato direttamente da OpenBDAP. La serie viene mostrata solo dal 2025 perché nel file 2024 è stato rilevato almeno un valore formalmente anomalo.",
        "aggregate_label": "Mediana dei 7 Comuni",
        "aggregate_note": "Mediana non ponderata degli indicatori ufficiali comunali; non rappresenta un dato ufficiale aggregato della Versilia.",
    },
    "educationMissionExpenditurePerResident": {
        "label": "Spesa impegnata per istruzione e diritto allo studio per residente",
        "shortLabel": "Istruzione",
        "description": "Impegni della missione 04 “Istruzione e diritto allo studio” rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missione 04 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "socialMissionExpenditurePerResident": {
        "label": "Spesa impegnata per diritti sociali e politiche familiari per residente",
        "shortLabel": "Politiche sociali",
        "description": "Impegni della missione 12 “Diritti sociali, politiche sociali e famiglia” rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missione 12 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "environmentMissionExpenditurePerResident": {
        "label": "Spesa impegnata per territorio e ambiente per residente",
        "shortLabel": "Ambiente",
        "description": "Impegni della missione 09 “Sviluppo sostenibile e tutela del territorio e dell’ambiente” rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missione 09 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "mobilityMissionExpenditurePerResident": {
        "label": "Spesa impegnata per trasporti e mobilità per residente",
        "shortLabel": "Mobilità",
        "description": "Impegni della missione 10 “Trasporti e diritto alla mobilità” rapportati ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missione 10 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "cultureSportMissionExpenditurePerResident": {
        "label": "Spesa impegnata per cultura e sport per residente",
        "shortLabel": "Cultura e sport",
        "description": "Somma degli impegni delle missioni 05 “Tutela e valorizzazione dei beni e attività culturali” e 06 “Politiche giovanili, sport e tempo libero”, rapportata ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missioni 05 + 06 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "tourismDevelopmentMissionExpenditurePerResident": {
        "label": "Spesa impegnata per turismo e sviluppo economico per residente",
        "shortLabel": "Turismo e sviluppo",
        "description": "Somma degli impegni delle missioni 07 “Turismo” e 14 “Sviluppo economico e competitività”, rapportata ai residenti.",
        "unit": "currency",
        "polarity": "neutral",
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "impegni missioni 07 + 14 / popolazione residente",
        "caveat": "La classificazione per missione comprende spesa corrente e in conto capitale. Differenze organizzative, servizi associati e investimenti straordinari possono incidere sul confronto.",
        "aggregate_label": "Valore pro capite Versilia",
        "aggregate_note": "Totale dei sette Comuni rapportato alla popolazione complessiva.",
    },
}

BILANCI_THEME = {
    "key": "bilanci",
    "number": "09",
    "label": "Bilanci comunali",
    "question": "Da dove provengono le risorse e come vengono impiegate?",
    "description": "Rendiconto, capacità di riscossione e pagamento, risultato di amministrazione, cassa e priorità di spesa.",
    "metrics": [
        "currentRevenueAccruedPerResident",
        "currentExpenditureCommittedPerResident",
        "capitalExpenditureCommittedPerResident",
        "ownRevenueShare",
        "currentCollectionCapacity",
        "currentPaymentCapacity",
        "availableAdministrationResultPerResident",
        "rigidExpenditureShare",
        *CASH_METRICS,
        "educationMissionExpenditurePerResident",
        "socialMissionExpenditurePerResident",
        "environmentMissionExpenditurePerResident",
        "mobilityMissionExpenditurePerResident",
        "cultureSportMissionExpenditurePerResident",
        "tourismDevelopmentMissionExpenditurePerResident",
    ],
    "sections": [
        {
            "key": "rendiconto",
            "label": "Entrate e spese di competenza",
            "description": "Accertamenti e impegni registrati nel rendiconto, distinti dai movimenti di cassa.",
            "metrics": [
                "currentRevenueAccruedPerResident",
                "currentExpenditureCommittedPerResident",
                "capitalExpenditureCommittedPerResident",
            ],
        },
        {
            "key": "equilibri",
            "label": "Autonomia, riscossione ed equilibri",
            "description": "Composizione delle entrate, capacità di incasso e pagamento, risultato disponibile e rigidità della spesa.",
            "metrics": [
                "ownRevenueShare",
                "currentCollectionCapacity",
                "currentPaymentCapacity",
                "availableAdministrationResultPerResident",
                "rigidExpenditureShare",
            ],
        },
        {
            "key": "cassa",
            "label": "Movimenti di cassa",
            "description": "Pagamenti, incassi e saldo registrati da SIOPE nell’anno.",
            "metrics": CASH_METRICS,
        },
        {
            "key": "priorita",
            "label": "Spesa per missione",
            "description": "Impegni complessivi per alcune principali finalità di intervento, rapportati ai residenti.",
            "metrics": [
                "educationMissionExpenditurePerResident",
                "socialMissionExpenditurePerResident",
                "environmentMissionExpenditurePerResident",
                "mobilityMissionExpenditurePerResident",
                "cultureSportMissionExpenditurePerResident",
                "tourismDevelopmentMissionExpenditurePerResident",
            ],
        },
    ],
    "featured": [
        "currentExpenditureCommittedPerResident",
        "capitalExpenditureCommittedPerResident",
        "currentCollectionCapacity",
    ],
}

COMMUNITY_THEME = {
    "key": "comunita",
    "number": "10",
    "label": "Investimenti e comunità",
    "question": "Quali progetti e reti sostengono il territorio?",
    "description": "Opere pubbliche, PNRR e presenza del Terzo settore.",
    "metrics": ["publicWorks", "pnrrFunding", "pnrrConcluded", "thirdSector"],
    "sections": [
        {
            "key": "investimenti",
            "label": "Investimenti e opere",
            "description": "Opere monitorate e stato dei progetti finanziati dal PNRR.",
            "metrics": ["publicWorks", "pnrrFunding", "pnrrConcluded"],
        },
        {
            "key": "societa",
            "label": "Comunità organizzata",
            "description": "Presenza del Terzo settore.",
            "metrics": ["thirdSector"],
        },
    ],
    "featured": ["publicWorks", "pnrrFunding", "thirdSector"],
}


def format_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    number = f"{round(abs(value)):,}".replace(",", ".")
    return f"{sign}{number}\u00a0€"


def format_percent(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + "%"


def raw(snapshot: dict, town: str, year: int) -> dict:
    return snapshot["raw"][town]["years"][str(year)]


def metric_value(snapshot: dict, key: str, town: str, year: int) -> float:
    return float(snapshot["metrics"][key]["values"][town][str(year)])


def aggregate(snapshot: dict, key: str) -> float:
    latest = [raw(snapshot, town, 2025) for town in TOWN_ORDER]
    total_population = sum(item["population_at_1_january"] for item in latest)
    if key == "currentRevenueAccruedPerResident":
        return sum(item["current_revenue_accruals_titles_1_2_3"] for item in latest) / total_population
    if key == "currentExpenditureCommittedPerResident":
        return sum(item["current_expenditure_commitments_title_1"] for item in latest) / total_population
    if key == "capitalExpenditureCommittedPerResident":
        return sum(item["capital_expenditure_commitments_title_2"] for item in latest) / total_population
    if key == "ownRevenueShare":
        return (
            sum(item["own_revenue_accruals_titles_1_3"] for item in latest)
            / sum(item["current_revenue_accruals_titles_1_2_3"] for item in latest)
            * 100
        )
    if key == "currentCollectionCapacity":
        return (
            sum(item["current_revenue_competence_receipts_titles_1_2_3"] for item in latest)
            / sum(item["current_revenue_accruals_titles_1_2_3"] for item in latest)
            * 100
        )
    if key == "currentPaymentCapacity":
        return (
            sum(item["current_expenditure_competence_payments_title_1"] for item in latest)
            / sum(item["current_expenditure_commitments_title_1"] for item in latest)
            * 100
        )
    if key == "availableAdministrationResultPerResident":
        return sum(item["available_administration_result_code_0502"] for item in latest) / total_population
    if key == "rigidExpenditureShare":
        return statistics.median(
            item["rigid_expenditure_share_official_code_01_01"] for item in latest
        )
    mission_codes = {
        "educationMissionExpenditurePerResident": ["04"],
        "socialMissionExpenditurePerResident": ["12"],
        "environmentMissionExpenditurePerResident": ["09"],
        "mobilityMissionExpenditurePerResident": ["10"],
        "cultureSportMissionExpenditurePerResident": ["05", "06"],
        "tourismDevelopmentMissionExpenditurePerResident": ["07", "14"],
    }[key]
    return (
        sum(
            sum(item["mission_commitments"].get(code, 0) for code in mission_codes)
            for item in latest
        )
        / total_population
    )


def town_meta(data: dict) -> dict[str, dict[str, str]]:
    rows = data["metrics"]["population"]["rows"]
    return {
        row["town"]: {"code": row["code"], "slug": row["slug"]}
        for row in rows
    }


def build_metric(data: dict, snapshot: dict, key: str) -> dict:
    meta = METRIC_META[key]
    lookup = town_meta(data)
    year_list = [2025] if key == "rigidExpenditureShare" else [2024, 2025]
    rows = []
    for town in TOWN_ORDER:
        values = [metric_value(snapshot, key, town, year) for year in year_list]
        value = values[-1]
        rows.append(
            {
                "town": town,
                "code": lookup[town]["code"],
                "slug": lookup[town]["slug"],
                "value": value,
                "formatted": (
                    format_currency(value)
                    if meta["unit"] == "currency"
                    else format_percent(value)
                ),
                "series": (
                    None
                    if key == "rigidExpenditureShare"
                    else {"years": year_list, "values": values}
                ),
                "normalized": None,
                "benchmarkValue": value,
            }
        )
    return {
        "meta": {
            "key": key,
            "theme": "bilanci",
            "label": meta["label"],
            "shortLabel": meta["shortLabel"],
            "description": meta["description"],
            "unit": meta["unit"],
            "year": "2025",
            "source": "OpenBDAP — rendiconto della gestione",
            "polarity": meta["polarity"],
        },
        "sourceUrl": SOURCE_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate(snapshot, key),
            "label": meta["aggregate_label"],
            "note": meta["aggregate_note"],
        },
        "normalizedAggregate": None,
        "method": {
            "type": meta["type"],
            "formula": meta["formula"],
            "caveat": meta["caveat"],
            "coverage": "7/7",
        },
    }


def update_dataset() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    data["version"] = VERSION
    data["updated"] = UPDATED

    themes = OrderedDict()
    for key, value in data["themes"].items():
        if key == "bilanci":
            continue
        if key == "comunita":
            themes["bilanci"] = BILANCI_THEME
            themes["comunita"] = COMMUNITY_THEME
        else:
            themes[key] = value
    if "bilanci" not in themes:
        themes["bilanci"] = BILANCI_THEME
        themes["comunita"] = COMMUNITY_THEME
    data["themes"] = themes

    for key in CASH_METRICS:
        data["metrics"][key]["meta"]["theme"] = "bilanci"
    for key in NEW_METRIC_KEYS:
        data["metrics"][key] = build_metric(data, snapshot, key)

    if len(data["themes"]) != 10:
        raise RuntimeError(f"Numero temi inatteso: {len(data['themes'])}")
    if len(data["metrics"]) != 98:
        raise RuntimeError(f"Numero indicatori inatteso: {len(data['metrics'])}")

    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Punto di aggiornamento non trovato: {label}")
    return text.replace(old, new, 1)


def update_app() -> None:
    app = APP_PATH.read_text(encoding="utf-8")
    app = replace_once(
        app,
        "    comunita: '<path d=\"M10 12h4\"></path>",
        "    bilanci: '<path d=\"M3 22h18\"></path><path d=\"M6 18v-7\"></path><path d=\"M10 18v-7\"></path><path d=\"M14 18v-7\"></path><path d=\"M18 18v-7\"></path><path d=\"M12 2 2 7h20Z\"></path>',\n"
        "    comunita: '<path d=\"M10 12h4\"></path>",
        "icona Bilanci",
    )
    synonym_block = """    currentRevenueAccruedPerResident: ['entrate correnti', 'accertamenti', 'risorse comunali'],
    currentExpenditureCommittedPerResident: ['spesa corrente', 'impegni', 'servizi comunali'],
    capitalExpenditureCommittedPerResident: ['investimenti', 'conto capitale', 'impegni capitale'],
    ownRevenueShare: ['entrate proprie', 'autonomia finanziaria', 'tributi e tariffe'],
    currentCollectionCapacity: ['riscossione', 'incassi competenza', 'capacita di riscossione'],
    currentPaymentCapacity: ['pagamenti competenza', 'capacita di pagamento', 'impegni pagati'],
    availableAdministrationResultPerResident: ['risultato di amministrazione', 'avanzo disponibile', 'disavanzo'],
    rigidExpenditureShare: ['spese rigide', 'personale e debito', 'rigidita bilancio'],
    educationMissionExpenditurePerResident: ['spesa istruzione', 'bilancio scuola', 'missione 04'],
    socialMissionExpenditurePerResident: ['spesa sociale', 'famiglia', 'missione 12'],
    environmentMissionExpenditurePerResident: ['spesa ambiente', 'territorio', 'missione 09'],
    mobilityMissionExpenditurePerResident: ['spesa mobilita', 'trasporti', 'missione 10'],
    cultureSportMissionExpenditurePerResident: ['spesa cultura', 'spesa sport', 'missioni 05 06'],
    tourismDevelopmentMissionExpenditurePerResident: ['spesa turismo', 'sviluppo economico', 'missioni 07 14'],
"""
    app = replace_once(
        app,
        "    thirdSector: ['associazioni', 'volontariato'],\n",
        synonym_block + "    thirdSector: ['associazioni', 'volontariato'],\n",
        "sinonimi Bilanci",
    )
    app = app.replace(
        '<span>7 comuni · 9 temi</span>',
        '<span>7 comuni · ${Object.keys(data.themes).length} temi</span>',
    )
    app = app.replace(
        "<span>9 temi</span>",
        "<span>${Object.keys(data.themes).length} temi</span>",
    )
    version_row = (
        "      ['2026.08.05-v1.6.0','5 agosto 2026','98 indicatori. "
        "Aggiunto il tema Bilanci comunali con rendiconto 2024–2025, "
        "capacità di riscossione e pagamento, risultato di amministrazione "
        "e spesa per missione.'],\n"
    )
    marker = "    const versions = [\n"
    if version_row not in app:
        if marker not in app:
            raise RuntimeError("Elenco versioni non trovato")
        app = app.replace(marker, marker + version_row, 1)
    APP_PATH.write_text(app, encoding="utf-8")


def update_readme() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    text = text.replace("- 9 aree tematiche;", "- 10 aree tematiche;")
    text = text.replace("- 84 indicatori;", "- 98 indicatori;")
    README_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    update_dataset()
    update_app()
    update_readme()
    print("Bilanci comunali v1.6.0 materializzati.")


if __name__ == "__main__":
    main()
