#!/usr/bin/env python3
"""Materializza l'espansione v1.4.0 di Lavoro, Istruzione e Abitare.

Lo script è una migrazione esplicita e leggibile: aggiorna i sorgenti del ramo di
lavoro, ma non viene eseguito dalla pipeline di deploy. I dati grezzi e le
formule restano versionati nel repository per rendere riproducibile ogni valore.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
APP_PATH = ROOT / "assets" / "app-core.js"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "lia-v1.4.0.json"

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

# Conteggi aggregati delle sezioni di censimento Istat 2023.
# P33:P42 = maschi 15-64; P70:P79 = femmine 15-64.
ISTAT_RAW = {
    "Massarosa": {"P1": 21865, "male1564": 7095, "female1564": 6976, "P102": 5197, "P103": 3937, "PF1": 9108, "PF9": 134, "A3": 1975, "A8": 11003},
    "Viareggio": {"P1": 60755, "male1564": 18755, "female1564": 19038, "P102": 13174, "P103": 10726, "PF1": 29043, "PF9": 801, "A3": 10491, "A8": 38890},
    "Camaiore": {"P1": 31864, "male1564": 9957, "female1564": 10179, "P102": 7165, "P103": 5684, "PF1": 14316, "PF9": 308, "A3": 8287, "A8": 22384},
    "Pietrasanta": {"P1": 22788, "male1564": 6752, "female1564": 7152, "P102": 4707, "P103": 3858, "PF1": 10544, "PF9": 281, "A3": 7950, "A8": 18328},
    "Seravezza": {"P1": 12435, "male1564": 3748, "female1564": 3917, "P102": 2672, "P103": 2080, "PF1": 5571, "PF9": 116, "A3": 2037, "A8": 7528},
    "Forte dei Marmi": {"P1": 6777, "male1564": 1878, "female1564": 2034, "P102": 1209, "P103": 1004, "PF1": 3378, "PF9": 60, "A3": 5140, "A8": 8477},
    "Stazzema": {"P1": 2903, "male1564": 944, "female1564": 857, "P102": 654, "P103": 428, "PF1": 1371, "PF9": 12, "A3": 2154, "A8": 3518},
}

# Alunni e classi delle scuole primarie e secondarie statali e paritarie
# localizzate nei Comuni, anno scolastico 2024/25.
MIM_RAW = {
    "Massarosa": {"students": 1282, "classes": 72, "primary_students": 747, "full_time_students": 413},
    "Viareggio": {"students": 7508, "classes": 387, "primary_students": 2188, "full_time_students": 1024},
    "Camaiore": {"students": 2739, "classes": 147, "primary_students": 1046, "full_time_students": 402},
    "Pietrasanta": {"students": 1490, "classes": 82, "primary_students": 596, "full_time_students": 373},
    "Seravezza": {"students": 978, "classes": 57, "primary_students": 318, "full_time_students": 66},
    "Forte dei Marmi": {"students": 1065, "classes": 54, "primary_students": 463, "full_time_students": 86},
    "Stazzema": {"students": 106, "classes": 8, "primary_students": 64, "full_time_students": 64},
}

ISTAT_URL = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
MIM_URL = "https://dati.istruzione.it/opendata/"

SOURCE_FILES = {
    "R09_Toscana_2023_sezioni.xlsx": {"sha256": "ac4a4068e5ed2fb93ecbed96bc882914e7feef3d4d0db17013dceb4dcac95fdf", "bytes": 18784761},
    "TRACCIATO_FILE_REGIONALI.xlsx": {"sha256": "98071eb0f9e71a1bc59f5eb49503b8d31e7adc010aaa6c30d96ff3d9d1bfe3be", "bytes": 13786},
    "SCUANAGRAFESTAT20242520250831.csv": {"sha256": "91fac2ac891aa111ad448123e33a0118a854ce58237f985d21b1d7424f0be6fa", "bytes": 13178615},
    "SCUANAGRAFEPAR20242520250831.csv": {"sha256": "fd8ec418966aea01537f0816f3e8fc911391eae2c34063e9ca411f14e7ec0c9b", "bytes": 2493951},
    "ALUCORSOINDCLASTA20242520250831.csv": {"sha256": "9cfa5e077abcd7af99bfb833924c22efbadb51fb8ed6c7205f12dbd2bd222b26", "bytes": 5708520},
    "ALUCORSOINDCLAPAR20242520250831.csv": {"sha256": "f4390e21ce5ed2267115e89e28230ba2a7d38b85d63006ea9f5dd7e2bd3b92dc", "bytes": 751103},
    "ALUTEMPOSCUOLASTA20242520250831.csv": {"sha256": "5cca549e0591d39ee1635be7ae859aaa50630e8c9336c500ba79202a5628fbf9", "bytes": 6453321},
    "ALUTEMPOSCUOLAPAR20242520250831.csv": {"sha256": "f2f3ab1279bd18100d6022823ef2d7fda03f9828d77f3fbf4515e55cd0ba2fbd", "bytes": 483554},
    "locazioni_turistiche_2025.ods": {"sha256": "011b99ba71120cfef3ee94db0846d60d0da84c0bab879ebbd9619ff19ec77ec8", "bytes": 36400},
}

MIM_FILES = [
    {"role": "registry_state", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/SCUANAGRAFESTAT20242520250831.csv", "file": "SCUANAGRAFESTAT20242520250831.csv"},
    {"role": "registry_private", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/SCUANAGRAFEPAR20242520250831.csv", "file": "SCUANAGRAFEPAR20242520250831.csv"},
    {"role": "classes_state", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/ALUCORSOINDCLASTA20242520250831.csv", "file": "ALUCORSOINDCLASTA20242520250831.csv"},
    {"role": "classes_private", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/ALUCORSOINDCLAPAR20242520250831.csv", "file": "ALUCORSOINDCLAPAR20242520250831.csv"},
    {"role": "time_state", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/ALUTEMPOSCUOLASTA20242520250831.csv", "file": "ALUTEMPOSCUOLASTA20242520250831.csv"},
    {"role": "time_private", "url": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/ALUTEMPOSCUOLAPAR20242520250831.csv", "file": "ALUTEMPOSCUOLAPAR20242520250831.csv"},
]


def total(source: dict[str, dict[str, int]], field: str) -> int:
    return sum(row[field] for row in source.values())


def percent(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + "%"


def percentage_points(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " p.p."


def per_thousand(value: float) -> str:
    return f"{value:.2f}".replace(".", ",") + " ogni 1.000"


def people(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def students_per_class(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " alunni/classe"


def rows(calculator, formatter) -> list[dict[str, object]]:
    result = []
    for town in TOWN_ORDER:
        value = calculator(town)
        result.append({
            "town": town,
            "code": TOWN_META[town]["code"],
            "slug": TOWN_META[town]["slug"],
            "value": value,
            "formatted": formatter(value),
            "series": None,
            "normalized": None,
            "benchmarkValue": value,
        })
    return result


def metric(meta, source_url, metric_rows, aggregate, method) -> dict[str, object]:
    return {
        "meta": meta,
        "sourceUrl": source_url,
        "rows": metric_rows,
        "aggregate": aggregate,
        "normalizedAggregate": None,
        "method": method,
    }


def build_metrics() -> dict[str, dict[str, object]]:
    female_total = 100 * total(ISTAT_RAW, "P103") / total(ISTAT_RAW, "female1564")
    male_total = 100 * total(ISTAT_RAW, "P102") / total(ISTAT_RAW, "male1564")
    school_total = total(MIM_RAW, "students")
    class_total = total(MIM_RAW, "classes")
    primary_total = total(MIM_RAW, "primary_students")
    full_time_total = total(MIM_RAW, "full_time_students")

    return {
        "femaleEmploymentRate": metric(
            {"key": "femaleEmploymentRate", "theme": "lavoro", "label": "Tasso di occupazione femminile 15–64 anni", "shortLabel": "Occupazione femminile", "description": "Donne occupate tra 15 e 64 anni sul totale delle donne residenti della stessa fascia d’età.", "unit": "percent", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "positive"},
            ISTAT_URL,
            rows(lambda town: 100 * ISTAT_RAW[town]["P103"] / ISTAT_RAW[town]["female1564"], percent),
            {"value": female_total, "label": "Tasso ponderato Versilia", "note": "Calcolato sulle donne occupate e sulla popolazione femminile 15–64 anni complessive."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "donne occupate 15–64 anni / donne residenti 15–64 anni × 100", "caveat": "La fascia 15–64 anni e l’anno 2023 non coincidono con i tre indicatori generali della sezione, riferiti ai 25–64enni nel 2024.", "coverage": "7/7"},
        ),
        "maleEmploymentRate": metric(
            {"key": "maleEmploymentRate", "theme": "lavoro", "label": "Tasso di occupazione maschile 15–64 anni", "shortLabel": "Occupazione maschile", "description": "Uomini occupati tra 15 e 64 anni sul totale degli uomini residenti della stessa fascia d’età.", "unit": "percent", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "positive"},
            ISTAT_URL,
            rows(lambda town: 100 * ISTAT_RAW[town]["P102"] / ISTAT_RAW[town]["male1564"], percent),
            {"value": male_total, "label": "Tasso ponderato Versilia", "note": "Calcolato sugli uomini occupati e sulla popolazione maschile 15–64 anni complessivi."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "uomini occupati 15–64 anni / uomini residenti 15–64 anni × 100", "caveat": "La fascia 15–64 anni e l’anno 2023 non coincidono con i tre indicatori generali della sezione, riferiti ai 25–64enni nel 2024.", "coverage": "7/7"},
        ),
        "employmentGenderGap": metric(
            {"key": "employmentGenderGap", "theme": "lavoro", "label": "Divario occupazionale di genere 15–64 anni", "shortLabel": "Divario di genere", "description": "Differenza, in punti percentuali, tra il tasso di occupazione maschile e quello femminile nella fascia 15–64 anni.", "unit": "percentagePoints", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "negative"},
            ISTAT_URL,
            rows(lambda town: 100 * ISTAT_RAW[town]["P102"] / ISTAT_RAW[town]["male1564"] - 100 * ISTAT_RAW[town]["P103"] / ISTAT_RAW[town]["female1564"], percentage_points),
            {"value": male_total - female_total, "label": "Divario Versilia", "note": "Differenza tra i due tassi ponderati calcolati sulle rispettive popolazioni 15–64 anni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "tasso di occupazione maschile 15–64 anni − tasso di occupazione femminile 15–64 anni", "caveat": "Misura una differenza statistica e non ne identifica le cause. La fascia e l’anno differiscono dagli indicatori generali 25–64 anni del 2024.", "coverage": "7/7"},
        ),
        "schoolStudents": metric(
            {"key": "schoolStudents", "theme": "istruzione", "label": "Alunni nelle scuole del Comune", "shortLabel": "Alunni frequentanti", "description": "Alunni delle scuole primarie e secondarie, statali e paritarie, localizzate nel territorio comunale.", "unit": "people", "year": "a.s. 2024/25", "source": "MIM — Portale unico dei dati della scuola", "polarity": "neutral"},
            MIM_URL,
            rows(lambda town: MIM_RAW[town]["students"], people),
            {"value": school_total, "label": "Totale Versilia", "note": "Somma degli alunni delle scuole primarie e secondarie localizzate nei sette Comuni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "somma di alunni maschi e femmine per scuola, unendo anagrafe e dati di classe di istituti statali e paritari", "caveat": "Misura gli alunni delle scuole localizzate nel Comune, non gli alunni residenti; non comprende la scuola dell’infanzia.", "coverage": "7/7"},
        ),
        "studentsPerClass": metric(
            {"key": "studentsPerClass", "theme": "istruzione", "label": "Alunni per classe", "shortLabel": "Alunni per classe", "description": "Rapporto tra gli alunni e le classi delle scuole primarie e secondarie, statali e paritarie, localizzate nel Comune.", "unit": "studentsPerClass", "year": "a.s. 2024/25", "source": "MIM — Portale unico dei dati della scuola", "polarity": "neutral"},
            MIM_URL,
            rows(lambda town: MIM_RAW[town]["students"] / MIM_RAW[town]["classes"], students_per_class),
            {"value": school_total / class_total, "label": "Rapporto Versilia", "note": "Totale degli alunni diviso per il totale delle classi dei sette Comuni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "alunni delle scuole primarie e secondarie / classi delle stesse scuole", "caveat": "È un rapporto territoriale complessivo, non la dimensione di ogni singola classe; scuole e alunni sono attribuiti al Comune di localizzazione.", "coverage": "7/7"},
        ),
        "primaryFullTimeShare": metric(
            {"key": "primaryFullTimeShare", "theme": "istruzione", "label": "Alunni della primaria a tempo pieno", "shortLabel": "Tempo pieno primaria", "description": "Quota degli alunni della scuola primaria iscritti a classi con organizzazione a tempo pieno.", "unit": "percent", "year": "a.s. 2024/25", "source": "MIM — Portale unico dei dati della scuola", "polarity": "neutral"},
            MIM_URL,
            rows(lambda town: 100 * MIM_RAW[town]["full_time_students"] / MIM_RAW[town]["primary_students"], percent),
            {"value": 100 * full_time_total / primary_total, "label": "Quota Versilia", "note": "Ponderata sul totale degli alunni della scuola primaria nei sette Comuni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "alunni della primaria con TEMPOSCUOLA = “TEMPO PIENO” / alunni totali della primaria × 100", "caveat": "Descrive l’organizzazione dell’offerta scolastica, non la qualità didattica. Nei Comuni piccoli il valore dipende da pochi alunni.", "coverage": "7/7"},
        ),
        "housingStockPer1000": metric(
            {"key": "housingStockPer1000", "theme": "abitare", "label": "Abitazioni ogni 1.000 residenti", "shortLabel": "Patrimonio abitativo", "description": "Numero complessivo di abitazioni censite rapportato alla popolazione residente.", "unit": "per1000", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "neutral"},
            ISTAT_URL,
            rows(lambda town: 1000 * ISTAT_RAW[town]["A8"] / ISTAT_RAW[town]["P1"], per_thousand),
            {"value": 1000 * total(ISTAT_RAW, "A8") / total(ISTAT_RAW, "P1"), "label": "Rapporto Versilia", "note": "Totale delle abitazioni diviso per la popolazione complessiva dei sette Comuni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "abitazioni totali / popolazione residente × 1.000", "caveat": "Un valore elevato può riflettere seconde case o un patrimonio non utilizzato stabilmente e non equivale, da solo, a maggiore disponibilità abitativa per i residenti.", "coverage": "7/7"},
        ),
        "nonOccupiedHomesPer1000": metric(
            {"key": "nonOccupiedHomesPer1000", "theme": "abitare", "label": "Abitazioni non occupate ogni 1.000 residenti", "shortLabel": "Non occupate per residente", "description": "Abitazioni vuote o occupate soltanto da persone non residenti rapportate alla popolazione residente.", "unit": "per1000", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "neutral"},
            ISTAT_URL,
            rows(lambda town: 1000 * ISTAT_RAW[town]["A3"] / ISTAT_RAW[town]["P1"], per_thousand),
            {"value": 1000 * total(ISTAT_RAW, "A3") / total(ISTAT_RAW, "P1"), "label": "Rapporto Versilia", "note": "Totale delle abitazioni non occupate da residenti diviso per la popolazione complessiva."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "abitazioni vuote o occupate solo da non residenti / popolazione residente × 1.000", "caveat": "Integra la quota sul patrimonio con una misura rapportata ai residenti, ma non distingue seconde case, immobili inutilizzati e altre forme d’uso.", "coverage": "7/7"},
        ),
        "cohabitingHouseholds": metric(
            {"key": "cohabitingHouseholds", "theme": "abitare", "label": "Famiglie coabitanti", "shortLabel": "Famiglie coabitanti", "description": "Famiglie residenti registrate in coabitazione con un’altra famiglia sul totale delle famiglie residenti.", "unit": "percent", "year": "2023", "source": "Istat — Censimento permanente, dati per sezione", "polarity": "neutral"},
            ISTAT_URL,
            rows(lambda town: 100 * ISTAT_RAW[town]["PF9"] / ISTAT_RAW[town]["PF1"], percent),
            {"value": 100 * total(ISTAT_RAW, "PF9") / total(ISTAT_RAW, "PF1"), "label": "Quota Versilia", "note": "Ponderata sul totale delle famiglie residenti nei sette Comuni."},
            {"type": "Elaborazione Osservatorio su dati ufficiali", "formula": "famiglie residenti coabitanti / famiglie residenti totali × 100", "caveat": "La coabitazione anagrafica non identifica automaticamente una condizione di disagio abitativo e non ne spiega le cause.", "coverage": "7/7"},
        ),
    }


def update_themes(data: dict[str, object]) -> None:
    data["themes"]["lavoro"].update({
        "question": "Quante persone lavorano e quali divari emergono?",
        "description": "Occupazione, disoccupazione, partecipazione e differenze tra uomini e donne.",
        "metrics": ["employmentRate", "unemploymentRate", "activityRate", "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"],
        "sections": [
            {"key": "mercato", "label": "Partecipazione e occupazione", "description": "Occupazione, disoccupazione e partecipazione al mercato del lavoro.", "metrics": ["employmentRate", "unemploymentRate", "activityRate"]},
            {"key": "genere", "label": "Divari di genere", "description": "Occupazione femminile e maschile nella stessa fascia di età, con il relativo divario.", "metrics": ["femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"]},
        ],
        "featured": ["employmentRate", "femaleEmploymentRate", "employmentGenderGap"],
    })
    data["themes"]["istruzione"].update({
        "question": "Qual è il livello di istruzione e come è organizzata la rete scolastica?",
        "description": "Titoli di studio, popolazione scolastica, classi e tempo pieno.",
        "metrics": ["diplomaPlus", "tertiary", "schoolSites", "schoolStudents", "studentsPerClass", "primaryFullTimeShare"],
        "sections": [
            {"key": "capitale", "label": "Capitale umano", "description": "Livello di istruzione della popolazione residente.", "metrics": ["diplomaPlus", "tertiary"]},
            {"key": "rete", "label": "Rete e popolazione scolastica", "description": "Sedi e alunni delle scuole localizzate nel territorio comunale.", "metrics": ["schoolSites", "schoolStudents"]},
            {"key": "organizzazione", "label": "Classi e tempo scuola", "description": "Dimensione media delle classi e diffusione del tempo pieno nella primaria.", "metrics": ["studentsPerClass", "primaryFullTimeShare"]},
        ],
        "featured": ["diplomaPlus", "schoolStudents", "primaryFullTimeShare"],
    })
    data["themes"]["abitare"].update({
        "question": "Come viene utilizzato il patrimonio abitativo e come vivono le famiglie?",
        "description": "Patrimonio, abitazioni non occupate, struttura familiare e coabitazione.",
        "metrics": ["housingStockPer1000", "vacantHomes", "nonOccupiedHomesPer1000", "singleHouseholds", "householdSize", "cohabitingHouseholds"],
        "sections": [
            {"key": "patrimonio", "label": "Patrimonio e utilizzo", "description": "Consistenza del patrimonio e abitazioni non occupate.", "metrics": ["housingStockPer1000", "vacantHomes", "nonOccupiedHomesPer1000"]},
            {"key": "famiglie", "label": "Struttura delle famiglie", "description": "Persone sole e dimensione dei nuclei residenti.", "metrics": ["singleHouseholds", "householdSize"]},
            {"key": "coabitazione", "label": "Coabitazione", "description": "Famiglie registrate in coabitazione nella stessa abitazione.", "metrics": ["cohabitingHouseholds"]},
        ],
        "featured": ["vacantHomes", "housingStockPer1000", "cohabitingHouseholds"],
    })


def update_dataset() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    data["version"] = "2026.08.05-local-v1.4.0-lia"
    data["updated"] = "anteprima locale · 5 agosto 2026"
    update_themes(data)

    vacant = data["metrics"]["vacantHomes"]
    vacant["meta"].update({
        "description": "Abitazioni vuote o occupate soltanto da persone non residenti sul totale delle abitazioni censite.",
        "year": "2023",
        "source": "Istat — Censimento permanente, dati per sezione",
    })
    vacant["sourceUrl"] = ISTAT_URL
    vacant["method"] = {
        "type": "Elaborazione Osservatorio su dati ufficiali",
        "formula": "abitazioni vuote o occupate solo da non residenti / abitazioni totali × 100",
        "caveat": "La categoria comprende anche abitazioni occupate soltanto da persone non residenti e non coincide necessariamente con gli immobili inutilizzati.",
        "coverage": "7/7",
    }

    additions = build_metrics()
    positions = {
        "activityRate": ["femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"],
        "schoolSites": ["schoolStudents", "studentsPerClass", "primaryFullTimeShare"],
        "vacantHomes": ["housingStockPer1000", "nonOccupiedHomesPer1000"],
        "householdSize": ["cohabitingHouseholds"],
    }
    old_metrics = data["metrics"]
    result = OrderedDict()
    for key, value in old_metrics.items():
        if key in additions:
            continue
        result[key] = value
        for new_key in positions.get(key, []):
            result[new_key] = additions[new_key]
    data["metrics"] = result
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_app() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    replacements = [
        (
            "    activityRate: ['forza lavoro', 'attivi', 'partecipazione'],\n",
            "    activityRate: ['forza lavoro', 'attivi', 'partecipazione'],\n"
            "    femaleEmploymentRate: ['occupazione femminile', 'donne occupate', 'lavoro donne'],\n"
            "    maleEmploymentRate: ['occupazione maschile', 'uomini occupati', 'lavoro uomini'],\n"
            "    employmentGenderGap: ['divario di genere', 'gender gap', 'differenza occupazione donne uomini'],\n",
        ),
        (
            "    schoolSites: ['scuole', 'istituti scolastici'],\n",
            "    schoolSites: ['scuole', 'istituti scolastici'],\n"
            "    schoolStudents: ['alunni', 'studenti', 'popolazione scolastica'],\n"
            "    studentsPerClass: ['alunni per classe', 'dimensione classi', 'classi scolastiche'],\n"
            "    primaryFullTimeShare: ['tempo pieno', 'scuola primaria', 'orario scolastico'],\n",
        ),
        (
            "    householdSize: ['componenti famiglia', 'nucleo familiare'], landUse: ['consumo di suolo', 'cementificazione'],\n",
            "    householdSize: ['componenti famiglia', 'nucleo familiare'],\n"
            "    housingStockPer1000: ['patrimonio abitativo', 'abitazioni per residenti', 'case per abitante'],\n"
            "    nonOccupiedHomesPer1000: ['case non occupate per residenti', 'abitazioni vuote', 'seconde case'],\n"
            "    cohabitingHouseholds: ['famiglie coabitanti', 'coabitazione', 'disagio abitativo'],\n"
            "    landUse: ['consumo di suolo', 'cementificazione'],\n",
        ),
        (
            "      case 'percent': return `${number1.format(v)}%`;\n",
            "      case 'percent': return `${number1.format(v)}%`;\n"
            "      case 'percentagePoints': return `${number1.format(v)} p.p.`;\n",
        ),
        (
            "      case 'people': return `${number0.format(v)} persone`;\n",
            "      case 'people': return `${number0.format(v)} persone`;\n"
            "      case 'studentsPerClass': return `${number1.format(v)} alunni/classe`;\n",
        ),
    ]
    for old, new in replacements:
        marker = new.splitlines()[1].strip() if len(new.splitlines()) > 1 else new.strip()
        if marker in text:
            continue
        if old not in text:
            raise RuntimeError(f"Punto di aggiornamento non trovato in {APP_PATH}: {old.strip()}")
        text = text.replace(old, new, 1)
    APP_PATH.write_text(text, encoding="utf-8")


def write_snapshot() -> None:
    mim_files = []
    for item in MIM_FILES:
        file_info = SOURCE_FILES[item["file"]]
        mim_files.append({**item, **file_info})
    snapshot = {
        "version": "lia-v1.4.0",
        "created": "2026-08-05",
        "scope": {
            "towns": [{"name": town, **TOWN_META[town]} for town in TOWN_ORDER],
            "coverage": "7/7",
        },
        "sources": {
            "istatSections2023": {
                "landing": "https://www.istat.it/notizia/dati-per-sezioni-di-censimento/",
                "download": ISTAT_URL,
                "files": {
                    "data": {"name": "R09_Toscana_2023_sezioni.xlsx", **SOURCE_FILES["R09_Toscana_2023_sezioni.xlsx"]},
                    "layout": {"name": "TRACCIATO_FILE_REGIONALI.xlsx", **SOURCE_FILES["TRACCIATO_FILE_REGIONALI.xlsx"]},
                },
                "variables": {
                    "P1": "Popolazione residente totale",
                    "P33-P42": "Popolazione maschile 15–64 anni",
                    "P70-P79": "Popolazione femminile 15–64 anni",
                    "P102": "Uomini occupati 15–64 anni",
                    "P103": "Donne occupate 15–64 anni",
                    "PF1": "Famiglie residenti totali",
                    "PF9": "Famiglie residenti coabitanti",
                    "A3": "Abitazioni vuote e abitazioni occupate solo da persone non residenti",
                    "A8": "Abitazioni totali",
                },
            },
            "mimSchool2024_25": {
                "landing": MIM_URL,
                "files": mim_files,
                "universe": "Scuole primarie e secondarie statali e paritarie localizzate nel Comune; la scuola dell’infanzia non è inclusa nei dataset di alunni e classi utilizzati.",
            },
            "tuscanyTourism2025": {
                "landing": "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0",
                "file": {"name": "locazioni_turistiche_2025.ods", "url": "https://www.regione.toscana.it/documents/d/guest/6-locazioni-agg-maggio-2026-", **SOURCE_FILES["locazioni_turistiche_2025.ods"]},
                "finding": "La tavola sulle locazioni turistiche contiene esclusivamente valori provinciali e regionali; non permette indicatori 7/7 per i singoli Comuni.",
            },
        },
        "raw": {
            "istat2023": [{"town": town, "code": TOWN_META[town]["code"], **ISTAT_RAW[town]} for town in TOWN_ORDER],
            "mim2024_25": [{"town": town, "code": TOWN_META[town]["code"], **MIM_RAW[town]} for town in TOWN_ORDER],
        },
        "acceptedIndicators": [
            {"key": "femaleEmploymentRate", "formula": "P103 / somma(P70:P79) × 100"},
            {"key": "maleEmploymentRate", "formula": "P102 / somma(P33:P42) × 100"},
            {"key": "employmentGenderGap", "formula": "maleEmploymentRate − femaleEmploymentRate"},
            {"key": "schoolStudents", "formula": "somma alunni maschi + femmine, statali e paritarie"},
            {"key": "studentsPerClass", "formula": "schoolStudents / classi"},
            {"key": "primaryFullTimeShare", "formula": "alunni primaria TEMPO PIENO / alunni primaria × 100"},
            {"key": "housingStockPer1000", "formula": "A8 / P1 × 1.000"},
            {"key": "nonOccupiedHomesPer1000", "formula": "A3 / P1 × 1.000"},
            {"key": "cohabitingHouseholds", "formula": "PF9 / PF1 × 100"},
        ],
        "correctedIndicators": [
            {"key": "vacantHomes", "correction": "Anno corretto da 2021 a 2023 e definizione allineata alla variabile A3."},
        ],
        "rejectedCandidates": [
            {"candidate": "NEET 15–29 anni", "reason": "La tavola comunale Istat esclude i Comuni fino a 5.000 abitanti; Stazzema non ha valore e la copertura sarebbe 6/7."},
            {"candidate": "Occupazione non stabile", "reason": "La tavola comunale Istat esclude i Comuni fino a 5.000 abitanti; Stazzema non ha valore e la copertura sarebbe 6/7."},
            {"candidate": "Avviamenti e ingressi in disoccupazione SIL", "reason": "Le dashboard regionali sono consultabili, ma non è stato individuato un file comunale statico e riproducibile da versionare; candidato rinviato."},
            {"candidate": "Locazioni turistiche comunali", "reason": "La tavola regionale 2025 disponibile contiene soltanto valori provinciali e regionali."},
            {"candidate": "Indicatore sintetico di sicurezza scolastica", "reason": "Non viene costruito: certificazioni, accessibilità e dati mancanti devono restare indicatori distinti e richiedono un audit dedicato degli edifici."},
            {"candidate": "Servizi educativi per l’infanzia", "reason": "La gestione associata e le modalità di stima richiedono una verifica separata prima di attribuire valori comparabili ai singoli Comuni."},
        ],
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    update_dataset()
    update_app()
    write_snapshot()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if len(data["metrics"]) != 78:
        raise RuntimeError(f"Numero indicatori inatteso: {len(data['metrics'])}")
    print("Espansione LIA v1.4.0 materializzata: 78 indicatori, sorgenti leggibili e copertura 7/7.")


if __name__ == "__main__":
    main()
