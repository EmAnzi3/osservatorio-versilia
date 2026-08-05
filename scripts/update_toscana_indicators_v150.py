#!/usr/bin/env python3
"""Materializza sei indicatori comunali regionali verificati per la v1.5.0.

La migrazione aggiorna soltanto i sorgenti del ramo di anteprima. Non viene
eseguita durante il deploy e non modifica il sito pubblico.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
APP_PATH = ROOT / "assets" / "app-parts" / "00.txt"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "toscana-indicatori-v1.5.0.json"

SOURCE_URL = "https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali"
METADATA_URL = "https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1"
TOWN_ORDER = [
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
]
TOWN_META = {
    "Massarosa": {"code": "046018", "slug": "massarosa"},
    "Viareggio": {"code": "046033", "slug": "viareggio"},
    "Camaiore": {"code": "046005", "slug": "camaiore"},
    "Pietrasanta": {"code": "046024", "slug": "pietrasanta"},
    "Seravezza": {"code": "046028", "slug": "seravezza"},
    "Forte dei Marmi": {"code": "046013", "slug": "forte-dei-marmi"},
    "Stazzema": {"code": "046030", "slug": "stazzema"},
}


def format_value(value: float, unit: str) -> str:
    formatted = f"{value:.1f}".replace(".", ",")
    if unit == "minutes":
        return formatted + " min"
    if unit == "per1000":
        return formatted + " ogni 1.000"
    return formatted + "%"


def rows_from_snapshot(snapshot_metric: dict, unit: str) -> list[dict[str, object]]:
    source_rows = {row["town"]: row for row in snapshot_metric["rows"]}
    result = []
    for town in TOWN_ORDER:
        raw = source_rows[town]
        years = raw["years"]
        values = raw["values"]
        value = values[-1]
        result.append({
            "town": town,
            "code": TOWN_META[town]["code"],
            "slug": TOWN_META[town]["slug"],
            "value": value,
            "formatted": format_value(value, unit),
            "series": {"years": years, "values": values},
            "normalized": None,
            "benchmarkValue": value,
        })
    return result


def metric(snapshot_metric: dict, *, key: str, theme: str, label: str,
           short_label: str, description: str, unit: str, polarity: str,
           caveat: str) -> dict[str, object]:
    metric_rows = rows_from_snapshot(snapshot_metric, unit)
    med = median(row["value"] for row in metric_rows)
    return {
        "meta": {
            "key": key,
            "theme": theme,
            "label": label,
            "shortLabel": short_label,
            "description": description,
            "unit": unit,
            "year": "2024",
            "source": "Regione Toscana — Indicatori comunali per le politiche locali",
            "polarity": polarity,
        },
        "sourceUrl": SOURCE_URL,
        "rows": metric_rows,
        "aggregate": {
            "value": med,
            "label": "Mediana dei 7 Comuni",
            "note": "Mediana non ponderata dei valori comunali; non rappresenta un dato ufficiale aggregato della Versilia.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato ufficiale regionale",
            "formula": "Valore comunale pubblicato dalla Regione Toscana senza trasformazioni; serie ricomposta dai file annuali ufficiali.",
            "caveat": caveat,
            "coverage": "7/7",
        },
    }


def build_metrics(snapshot: dict) -> dict[str, dict[str, object]]:
    source = snapshot["indicators"]
    return {
        "youthOtherStatus": metric(
            source["youthOtherStatus"],
            key="youthOtherStatus",
            theme="lavoro",
            label="Giovani 15–24 anni in altra condizione professionale",
            short_label="Giovani in altra condizione",
            description="Quota dei giovani tra 15 e 24 anni classificati dalla fonte in altra condizione professionale.",
            unit="percent",
            polarity="neutral",
            caveat="Non è il tasso di disoccupazione giovanile e non coincide automaticamente con la definizione europea di NEET. Il dato 2020 non è disponibile dalla fonte.",
        ),
        "foreignBornSoleProprietorShare": metric(
            source["foreignBornSoleProprietorShare"],
            key="foreignBornSoleProprietorShare",
            theme="economia",
            label="Ditte individuali con titolare nato all’estero",
            short_label="Titolari nati all’estero",
            description="Quota delle ditte individuali attive il cui conduttore è nato all’estero.",
            unit="percent",
            polarity="neutral",
            caveat="La nascita all’estero non coincide necessariamente con la cittadinanza straniera. L’indicatore riguarda soltanto le ditte individuali attive.",
        ),
        "innovationBusinessShare": metric(
            source["innovationBusinessShare"],
            key="innovationBusinessShare",
            theme="economia",
            label="Imprese attive nei settori dell’innovazione",
            short_label="Imprese dell’innovazione",
            description="Quota delle imprese attive appartenenti alle divisioni Ateco individuate dalla Regione Toscana come settori dell’innovazione.",
            unit="percent",
            polarity="neutral",
            caveat="La classificazione comprende un insieme definito di divisioni Ateco e non equivale a una misura diretta dell’innovazione prodotta o degli investimenti in ricerca.",
        ),
        "emsResponseTimeP75": metric(
            source["emsResponseTimeP75"],
            key="emsResponseTimeP75",
            theme="salute",
            label="Tempo di risposta del 118 — 75° percentile",
            short_label="Risposta del 118",
            description="Minuti entro i quali si colloca il 75% degli intervalli tra la ricezione della chiamata e l’arrivo del primo mezzo di soccorso.",
            unit="minutes",
            polarity="negative",
            caveat="Non è un tempo medio. Nei Comuni con pochi interventi il valore può oscillare sensibilmente tra un anno e l’altro e non misura da solo la qualità complessiva dell’emergenza-urgenza.",
        ),
        "disability064Per1000": metric(
            source["disability064Per1000"],
            key="disability064Per1000",
            theme="salute",
            label="Persone 0–64 anni con disabilità riconosciuta",
            short_label="Disabilità riconosciuta",
            description="Persone tra 0 e 64 anni con disabilità, anche grave, ogni 1.000 residenti della stessa fascia d’età.",
            unit="per1000",
            polarity="neutral",
            caveat="L’indicatore riflette riconoscimenti e registrazioni amministrative; non rappresenta la prevalenza sanitaria complessiva della disabilità nella popolazione.",
        ),
        "organicAgriculturalAreaShare": metric(
            source["organicAgriculturalAreaShare"],
            key="organicAgriculturalAreaShare",
            theme="ambiente",
            label="Superficie agricola utilizzata biologica",
            short_label="SAU biologica",
            description="Quota della superficie agricola utilizzata coltivata con metodo biologico.",
            unit="percent",
            polarity="neutral",
            caveat="La quota dipende anche dalla dimensione e dalla struttura agricola del Comune. Un valore basso nei territori poco agricoli non costituisce da solo una valutazione ambientale negativa.",
        ),
    }


def update_themes(data: dict[str, object]) -> None:
    lavoro = data["themes"]["lavoro"]
    lavoro["question"] = "Quante persone lavorano e quali divari emergono tra genere e generazioni?"
    lavoro["description"] = "Occupazione, disoccupazione, partecipazione, differenze di genere e condizione dei giovani."
    lavoro["metrics"] = [
        "employmentRate", "unemploymentRate", "activityRate",
        "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap",
        "youthOtherStatus",
    ]
    lavoro["sections"] = [
        {"key": "mercato", "label": "Partecipazione e occupazione", "description": "Occupazione, disoccupazione e partecipazione al mercato del lavoro.", "metrics": ["employmentRate", "unemploymentRate", "activityRate"]},
        {"key": "genere", "label": "Divari di genere", "description": "Occupazione femminile e maschile nella stessa fascia di età, con il relativo divario.", "metrics": ["femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"]},
        {"key": "giovani", "label": "Condizione dei giovani", "description": "Una misura comunale della condizione professionale dei giovani tra 15 e 24 anni.", "metrics": ["youthOtherStatus"]},
    ]
    lavoro["featured"] = ["employmentRate", "employmentGenderGap", "youthOtherStatus"]

    economia = data["themes"]["economia"]
    economia["description"] = "Redditi, risultati delle imprese, struttura produttiva, imprenditorialità e capacità turistica."
    economia["metrics"] = [
        "income", "incomeUnder15k", "businessValueAdded", "labourProductivity",
        "industryValueAddedShare", "industryWorkerShare", "localUnits", "microUnits",
        "foreignBornSoleProprietorShare", "innovationBusinessShare",
        "tourismPresences", "tourismArrivals", "tourismAverageStay", "tourismBeds",
        "tourismSeasonality", "foreignTourismShare", "tourismIntensity",
        "tourismBedsPer1000", "tourismStructuresPer1000",
    ]
    economia["sections"] = [
        {"key": "redditi", "label": "Redditi", "description": "Livelli e distribuzione dei redditi dichiarati.", "metrics": ["income", "incomeUnder15k"]},
        {"key": "produzione", "label": "Sistema produttivo", "description": "Unità locali, addetti, produttività e specializzazione.", "metrics": ["businessValueAdded", "labourProductivity", "industryValueAddedShare", "industryWorkerShare", "localUnits", "microUnits"]},
        {"key": "imprenditorialita", "label": "Imprenditorialità e innovazione", "description": "Caratteristiche delle ditte individuali e presenza dei settori individuati come innovativi.", "metrics": ["foreignBornSoleProprietorShare", "innovationBusinessShare"]},
        {"key": "turismo", "label": "Turismo", "description": "Flussi, capacità ricettiva e pressione stagionale.", "metrics": ["tourismPresences", "tourismArrivals", "tourismAverageStay", "tourismBeds", "tourismSeasonality", "foreignTourismShare", "tourismIntensity", "tourismBedsPer1000", "tourismStructuresPer1000"]},
    ]
    economia["featured"] = ["income", "innovationBusinessShare", "tourismIntensity"]

    salute = data["themes"]["salute"]
    salute["description"] = "Speranza di vita, mortalità, cronicità, disabilità riconosciuta, emergenza, ricoveri, assistenza e presìdi."
    salute["metrics"] = [
        "lifeExpectancy", "mortalityAll", "chronicTotal", "diabetes", "dementia",
        "disability064Per1000", "emergencyAccess", "emsResponseTimeP75",
        "hospitalizedAll", "elderlyHomeCare", "pharmaciesPer1000", "hospitals",
    ]
    salute["sections"] = [
        {"key": "esiti", "label": "Condizioni di salute", "description": "Speranza di vita, mortalità, cronicità e disabilità riconosciuta.", "metrics": ["lifeExpectancy", "mortalityAll", "chronicTotal", "diabetes", "dementia", "disability064Per1000"]},
        {"key": "emergenza", "label": "Emergenza e ricoveri", "description": "Ricorso al pronto soccorso, tempi del 118 e ospedalizzazione.", "metrics": ["emergencyAccess", "emsResponseTimeP75", "hospitalizedAll"]},
        {"key": "territorio", "label": "Assistenza e presìdi territoriali", "description": "Assistenza domiciliare, farmacie e strutture ospedaliere.", "metrics": ["elderlyHomeCare", "pharmaciesPer1000", "hospitals"]},
    ]
    salute["featured"] = ["lifeExpectancy", "emsResponseTimeP75", "disability064Per1000"]

    ambiente = data["themes"]["ambiente"]
    ambiente["description"] = "Suolo, rifiuti, agricoltura biologica ed esposizione concreta ai rischi idrogeologici."
    ambiente["metrics"] = [
        "landUse", "landUseChange", "floodExposure", "landslideExposure",
        "organicAgriculturalAreaShare", "recycling", "wastePerResident", "residualWaste",
    ]
    ambiente["sections"] = [
        {"key": "territorio", "label": "Territorio e rischi", "description": "Consumo di suolo ed esposizione idrogeologica.", "metrics": ["landUse", "landUseChange", "floodExposure", "landslideExposure"]},
        {"key": "agricoltura", "label": "Agricoltura e territorio", "description": "Diffusione delle coltivazioni biologiche sulla superficie agricola utilizzata.", "metrics": ["organicAgriculturalAreaShare"]},
        {"key": "rifiuti", "label": "Rifiuti e circolarità", "description": "Produzione, raccolta differenziata e residuo.", "metrics": ["recycling", "wastePerResident", "residualWaste"]},
    ]
    ambiente["featured"] = ["recycling", "organicAgriculturalAreaShare", "landUse"]


def update_dataset() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    data["version"] = "2026.08.05-local-v1.5.0-toscana"
    data["updated"] = "anteprima locale · 5 agosto 2026"
    update_themes(data)
    additions = build_metrics(snapshot)

    insertion = {
        "employmentGenderGap": ["youthOtherStatus"],
        "microUnits": ["foreignBornSoleProprietorShare", "innovationBusinessShare"],
        "dementia": ["disability064Per1000"],
        "emergencyAccess": ["emsResponseTimeP75"],
        "landslideExposure": ["organicAgriculturalAreaShare"],
    }
    result = OrderedDict()
    for key, value in data["metrics"].items():
        if key in additions:
            continue
        result[key] = value
        for new_key in insertion.get(key, []):
            result[new_key] = additions[new_key]
    data["metrics"] = result
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_app() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    replacements = [
        (
            "    employmentGenderGap: ['divario di genere', 'gender gap', 'differenza occupazione donne uomini'],\n",
            "    employmentGenderGap: ['divario di genere', 'gender gap', 'differenza occupazione donne uomini'],\n"
            "    youthOtherStatus: ['giovani', '15 24 anni', 'altra condizione professionale', 'neet'],\n",
        ),
        (
            "    microUnits: ['pmi', 'piccole imprese', 'microimprese'],\n",
            "    microUnits: ['pmi', 'piccole imprese', 'microimprese'],\n"
            "    foreignBornSoleProprietorShare: ['imprenditori stranieri', 'titolari nati all estero', 'ditte individuali'],\n"
            "    innovationBusinessShare: ['innovazione', 'imprese innovative', 'settori innovativi'],\n",
        ),
        (
            "    chronicTotal: ['cronici', 'malattie croniche', 'patologie croniche'],\n",
            "    chronicTotal: ['cronici', 'malattie croniche', 'patologie croniche'],\n"
            "    disability064Per1000: ['disabilita', 'persone con disabilita', 'invalidita'],\n",
        ),
        (
            "    emergencyAccess: ['pronto soccorso', 'emergenza', 'accessi ps'],\n",
            "    emergencyAccess: ['pronto soccorso', 'emergenza', 'accessi ps'],\n"
            "    emsResponseTimeP75: ['118', 'ambulanza', 'tempo di soccorso', 'emergenza urgenza'],\n",
        ),
        (
            "    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],\n",
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\n"
            "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\n"
            "    thirdSector: ['associazioni', 'volontariato'],\n",
        ),
        (
            "      case 'studentsPerClass': return `${number1.format(v)} alunni/classe`;\n",
            "      case 'studentsPerClass': return `${number1.format(v)} alunni/classe`;\n"
            "      case 'minutes': return `${number1.format(v)} min`;\n",
        ),
    ]
    for old, new in replacements:
        marker = new.splitlines()[-1].strip()
        if marker in text:
            continue
        if old not in text:
            raise RuntimeError(f"Punto di aggiornamento non trovato: {old.strip()}")
        text = text.replace(old, new, 1)
    APP_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    update_dataset()
    update_app()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if len(data["metrics"]) != 84:
        raise RuntimeError(f"Numero indicatori inatteso: {len(data['metrics'])}")
    for key in (
        "youthOtherStatus", "foreignBornSoleProprietorShare", "innovationBusinessShare",
        "emsResponseTimeP75", "disability064Per1000", "organicAgriculturalAreaShare",
    ):
        if len(data["metrics"][key]["rows"]) != 7:
            raise RuntimeError(f"Copertura incompleta per {key}")
    print("v1.5.0 Toscana materializzata: 84 indicatori e copertura 7/7.")


if __name__ == "__main__":
    main()
