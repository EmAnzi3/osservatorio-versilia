#!/usr/bin/env python3
"""Materializza il lotto Cultura e biblioteche v1.21.0 dallo snapshot Regione Toscana verificato."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "regione-toscana-cultura-biblioteche-2024.json"
FINALIZER = ROOT / "scripts" / "finalize_catalog_release.py"
CATALOG_TEST = ROOT / "scripts" / "test_catalog_release_v116.py"
README = ROOT / "README.md"
HISTORY_DOC = ROOT / "docs" / "copertura-serie-storiche.md"
APP_JS = ROOT / "assets" / "app.js"
APP_PART_05 = ROOT / "assets" / "app-parts" / "05.txt"
SERVICE_WORKER = ROOT / "service-worker.js"

VERSION = "v1.21.0"
UPDATED = "27 agosto 2026"
KEYS = (
    "libraryLoansPerResident",
    "libraryActiveBorrowersPer100",
    "libraryWeeklyOpeningHours",
)
PROFILE = "regione-toscana-biblioteche-annual"
SNAPSHOT_REF = "data/source-snapshots/regione-toscana-cultura-biblioteche-2024.json"
CATALOG_URL = "https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale"
MONITORING_URL = "https://www.regione.toscana.it/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria"
INDICATORS_CSV = "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/6e2fd7ad-9699-4d1d-b90d-c96a69a18179/download/dataset_indicatori.csv"
LIBRARIES_CSV = "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/873b9a04-a1a3-4dab-b0d3-7e98dd67e068/download/dataset_biblioteche.csv"
INDICATORS_LAYOUT = "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/788569d3-24e3-414f-a886-f55b89115b1a/download/tracciato-dataset-indicator.pdf"
LIBRARIES_LAYOUT = "https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/b28e346a-9f71-49af-9bea-55f3909c366c/download/tracciato-dataset-biblioteche-3mag2023-1.pdf"

SOURCE_URLS = {
    "monitoring": MONITORING_URL,
    "catalog": CATALOG_URL,
    "indicatorsCsv": INDICATORS_CSV,
    "librariesCsv": LIBRARIES_CSV,
    "indicatorsRecordLayout": INDICATORS_LAYOUT,
    "librariesRecordLayout": LIBRARIES_LAYOUT,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Pattern non trovato in {path}: {old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def validate_snapshot(snapshot: dict, site: dict) -> None:
    codes = {town["code"] for town in site["towns"]}
    if set(snapshot["scope"]["townCodes"]) != codes or len(codes) != 7:
        raise RuntimeError("Snapshot biblioteche: perimetro diverso dai sette Comuni canonici")
    if snapshot["scope"]["referenceYear"] != 2024:
        raise RuntimeError("Snapshot biblioteche: anno corrente diverso dal 2024")
    if snapshot["sources"]["indicatorCsv"]["sha256"] != "847b5e4a3d4d3104dd219e8da766228127d7ba764f7a2a7316f979b772608978":
        raise RuntimeError("Hash Dataset Indicatori inatteso")
    if snapshot["sources"]["librariesCsv"]["sha256"] != "4914a35c89bede4ba5ae735925e62380a2db4db9dc578e072708356e552165c5":
        raise RuntimeError("Hash Dataset Biblioteche inatteso")
    current = {row["code"]: row for row in snapshot["current2024"]}
    if set(current) != codes:
        raise RuntimeError("Snapshot biblioteche: righe comunali incomplete")
    if current["046018"]["selectedIndicatorRow"]["Indice di prestito Comunale"] is not None:
        raise RuntimeError("Massarosa 2024 deve restare n.d.")
    if current["046030"]["indicatorRowPresent"]:
        raise RuntimeError("Stazzema non deve essere trasformata in una riga/zero")
    via = current["046033"]["allIndicatorRows2024"]
    if len(via) != 2 or sum(r["Indice di prestito Comunale"] is not None for r in via) != 1:
        raise RuntimeError("Deduplicazione della doppia riga Viareggio non documentata")


def fmt(value: float | None, unit: str) -> str:
    if value is None:
        return "n.d."
    number = f"{value:.2f}".replace(".", ",")
    if unit == "per100":
        return f"{number} ogni 100"
    if unit == "hours":
        return f"{number} h"
    return number


def build_rows(site: dict, snapshot: dict, metric_key: str, unit: str) -> list[dict]:
    series = snapshot["series"][metric_key]
    years = series["years"]
    values = series["values"]
    slug_by_code = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}
    rows = []
    for town in site["towns"]:
        town_values = values[town["name"]]
        current = town_values[-1]
        pairs = [(year, value) for year, value in zip(years, town_values) if value is not None]
        row_series = {
            "years": [year for year, _ in pairs],
            "values": [value for _, value in pairs],
        } if pairs else None
        rows.append({
            "town": town["name"],
            "code": town["code"],
            "slug": slug_by_code[town["code"]],
            "value": current,
            "formatted": fmt(current, unit),
            "series": row_series,
            "normalized": None,
            "benchmarkValue": current,
        })
    return rows


def meta(key: str, label: str, short: str, description: str, unit: str, search_terms: list[str]) -> dict:
    return {
        "key": key,
        "theme": "comunita",
        "label": label,
        "shortLabel": short,
        "description": description,
        "unit": unit,
        "year": "2024",
        "source": "Regione Toscana — Monitoraggio biblioteche pubbliche",
        "polarity": "neutral",
        "searchTerms": search_terms,
        "sourceMeta": {
            "publisher": "Regione Toscana",
            "snapshot": SNAPSHOT_REF,
            "note": "Indicatori IFLA comunali ufficiali; mancanti conservati come n.d. senza stime.",
        },
    }


def build_metrics(site: dict, snapshot: dict) -> OrderedDict:
    terms = ["biblioteca", "biblioteche", "cultura", "lettura", "prestiti", "utenti", "iscritti", "apertura", "servizio"]
    agg = snapshot["aggregation"]

    loans = {
        "meta": meta(
            KEYS[0], "Prestiti bibliotecari per residente", "Prestiti bibliotecari",
            "Numero medio di prestiti bibliotecari effettuati nell’anno per residente, secondo l’indicatore IFLA comunale pubblicato dalla Regione Toscana.",
            "decimal", terms + ["prestiti pro capite", "indice di prestito"],
        ),
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": build_rows(site, snapshot, KEYS[0], "decimal"),
        "aggregate": {
            "value": agg[KEYS[0]]["value"],
            "label": "Versilia · comuni con dato disponibile (5/7)",
            "note": "Media aritmetica dei cinque Comuni con indicatore 2024 disponibile; Massarosa e Stazzema sono esclusi perché n.d.",
            "formatted": "0,34 prestiti per residente",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore IFLA comunale ufficiale",
            "formula": "Valore pubblicato nel campo “Indice di prestito Comunale” (prestiti pro capite). Aggregato Versilia = media aritmetica dei valori comunali disponibili; i Comuni n.d. non entrano né nel numeratore né nel divisore.",
            "caveat": "Copertura 2024 5/7 per eccezione approvata: Massarosa ha riga comunale ma valore non alimentato; Stazzema è assente dal monitoraggio regionale. Nessun mancante è trasformato in zero. Il 2020, incluso nello storico, è un anno anomalo per le limitazioni pandemiche.",
            "coverage": "5/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    impact = {
        "meta": meta(
            KEYS[1], "Utenti attivi del prestito ogni 100 residenti", "Utenti attivi del prestito",
            "Utenti che hanno effettuato almeno un prestito nell’anno ogni 100 abitanti, secondo l’Indice di impatto comunale IFLA.",
            "per100", terms + ["utenti attivi", "indice di impatto", "impatto biblioteca"],
        ),
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": build_rows(site, snapshot, KEYS[1], "per100"),
        "aggregate": {
            "value": agg[KEYS[1]]["value"],
            "label": "Versilia · comuni con dato disponibile (5/7)",
            "note": "Media aritmetica dei cinque Comuni con indicatore 2024 disponibile. È un indice su 100 abitanti, non un conteggio di persone uniche della Versilia.",
            "formatted": "7,89 ogni 100",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore IFLA comunale ufficiale",
            "formula": "Valore pubblicato nel campo “Indice di impatto Comunale” = utenti attivi del servizio di prestito su 100 abitanti. Aggregato Versilia = media aritmetica dei valori comunali disponibili; i Comuni n.d. non entrano né nel numeratore né nel divisore.",
            "caveat": "L’unità ufficiale resta ogni 100 abitanti: non è convertita a 1.000. Copertura 2024 5/7 per eccezione approvata; Massarosa è n.d. e Stazzema è assente dal monitoraggio. Gli utenti attivi delle singole sedi non vengono sommati per ricostruire il valore comunale. Il 2020 è segnalato come anno pandemico anomalo.",
            "coverage": "5/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    opening = {
        "meta": meta(
            KEYS[2], "Ore medie di apertura settimanale", "Apertura settimanale",
            "Ore medie settimanali di apertura delle biblioteche del Comune, nel valore comunale già pubblicato dalla Regione Toscana.",
            "hours", terms + ["orari biblioteca", "ore settimanali", "accessibilità"],
        ),
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": build_rows(site, snapshot, KEYS[2], "hours"),
        "aggregate": {
            "value": agg[KEYS[2]]["value"],
            "label": "Versilia · comuni con dato disponibile (5/7)",
            "note": "Media aritmetica dei cinque indicatori comunali 2024 disponibili. Le ore dei Comuni non vengono sommate e non sono ponderate per popolazione.",
            "formatted": "54,08 h",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore comunale ufficiale Regione Toscana",
            "formula": "Valore pubblicato nel campo “Ore medie di apertura settimanale Comunale”. Aggregato Versilia = media aritmetica dei valori comunali disponibili.",
            "caveat": "Copertura 2024 5/7 per eccezione approvata. Massarosa ha riga comunale ma valore non alimentato; Stazzema è assente dal monitoraggio. Lo storico della card parte dal 2022: nel file Indicatori 2019–2021 il campo coincide con l’Indice di apertura e non con le ore settimanali del dettaglio biblioteche.",
            "coverage": "5/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    return OrderedDict((key, value) for key, value in zip(KEYS, (loans, impact, opening)))


def apply_site(site: dict, snapshot: dict) -> None:
    validate_snapshot(snapshot, site)
    metrics = build_metrics(site, snapshot)
    for key in KEYS:
        site["metrics"].pop(key, None)
    rebuilt = OrderedDict()
    inserted = False
    for key, value in site["metrics"].items():
        rebuilt[key] = value
        if key == "socialSpendingByUserArea":
            rebuilt.update(metrics)
            inserted = True
    if not inserted:
        raise RuntimeError("Punto di inserimento Comunità non trovato")
    site["metrics"] = rebuilt

    theme = site["themes"]["comunita"]
    theme["description"] = "Investimenti pubblici, Terzo settore, welfare, servizi sociali, cultura e biblioteche per leggere risorse e reti della comunità."
    theme["sections"] = [section for section in theme["sections"] if section.get("key") != "cultura-biblioteche"]
    theme["sections"].append({
        "key": "cultura-biblioteche",
        "label": "Cultura e biblioteche",
        "description": "Prestiti, utenti attivi e accessibilità oraria delle biblioteche pubbliche monitorate dalla Regione Toscana.",
        "metrics": list(KEYS),
    })
    theme["metrics"] = [key for section in theme["sections"] for key in section["metrics"]]
    site["version"] = VERSION
    site["updated"] = UPDATED


def apply_registry(registry: dict) -> None:
    registry["sourceProfiles"][PROFILE] = {
        "publisher": "Regione Toscana",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la validazione annuale del monitoraggio biblioteche",
        "acquisitionMethod": "Download dei CSV ufficiali Dataset Indicatori e Dataset Biblioteche; indicatori IFLA comunali preferiti, dettaglio sedi deduplicato per Codice ICCU; nessuna stima dei mancanti.",
        "licenseName": "Creative Commons Attribution",
        "licenseUrl": CATALOG_URL,
    }
    for url in (CATALOG_URL, MONITORING_URL, INDICATORS_CSV, LIBRARIES_CSV, INDICATORS_LAYOUT, LIBRARIES_LAYOUT):
        registry.setdefault("sourceProfileByUrl", {})[url] = PROFILE
        registry.setdefault("sourceUrlProfiles", {})[url] = PROFILE
    for key in KEYS:
        registry.setdefault("metricOverrides", {})[key] = {"profile": PROFILE}
    registry["expectedMetricCount"] = 157
    registry["expectedInlineMetricCount"] = 153
    registry["expectedExternalMetricCount"] = 4


def patch_release_files() -> None:
    text = FINALIZER.read_text(encoding="utf-8")
    text = text.replace("catalogo pubblico v1.20.0", "catalogo pubblico v1.21.0")
    text = text.replace('VERSION = "v1.20.0"', 'VERSION = "v1.21.0"')
    text = text.replace('UPDATED = "26 agosto 2026"', 'UPDATED = "27 agosto 2026"')
    text = text.replace("EXPECTED_METRICS = 154", "EXPECTED_METRICS = 157")
    text = text.replace("EXPECTED_INLINE = 150", "EXPECTED_INLINE = 153")
    FINALIZER.write_text(text, encoding="utf-8")

    text = CATALOG_TEST.read_text(encoding="utf-8")
    text = text.replace("release v1.20.0", "release v1.21.0")
    text = text.replace(
        'assert "2026.08.26-v1.20.0" in app and "154 indicatori complessivi" in app',
        'assert "2026.08.27-v1.21.0" in app and "157 indicatori complessivi" in app',
    )
    CATALOG_TEST.write_text(text, encoding="utf-8")

    text = README.read_text(encoding="utf-8")
    text = text.replace("Versione dati corrente: **v1.20.0** — 26 agosto 2026.", "Versione dati corrente: **v1.21.0** — 27 agosto 2026.")
    text = text.replace("154 indicatori nel catalogo canonico: 150 con valori incorporati", "157 indicatori nel catalogo canonico: 153 con valori incorporati")
    text = text.replace("`indicatori/`: 150 pagine canoniche", "`indicatori/`: 153 pagine canoniche")
    text = text.replace("catalogo canonico dei 154 indicatori, con dati incorporati per 150", "catalogo canonico dei 157 indicatori, con dati incorporati per 153")
    text = text.replace("metadati dei 154 indicatori", "metadati dei 157 indicatori")
    text = text.replace("valida tutti i 154 indicatori canonici, la ripartizione fra 150 valori incorporati", "valida tutti i 157 indicatori canonici, la ripartizione fra 153 valori incorporati")
    text = text.replace("ciascuno dei 150 indicatori incorporati", "ciascuno dei 153 indicatori incorporati")
    old = "Coperture inferiori richiedono un'eccezione esplicita, documentata nello snapshot e nei test: nella v1.20.0 l'unico caso è la sottodimensione “Olive da tavola” del Profilo colture, pubblicata 4/7 con gli altri tre Comuni indicati come `n.d.`."
    new = old + " Nella v1.21.0 il lotto Cultura e biblioteche usa inoltre il 2024 con copertura 5/7: Massarosa e Stazzema restano `n.d.` e le serie degli altri Comuni proseguono senza stime."
    if new not in text:
        text = text.replace(old, new)
    README.write_text(text, encoding="utf-8")

    history = HISTORY_DOC.read_text(encoding="utf-8")
    marker = "## Lotto Cultura e biblioteche v1.21.0"
    if marker not in history:
        history += (
            "\n\n## Lotto Cultura e biblioteche v1.21.0\n\n"
            "Il monitoraggio annuale Regione Toscana è usato con anno corrente 2024 per tre misure comunali: "
            "Indice di prestito, Indice di impatto e Ore medie di apertura settimanale. È approvata un'eccezione esplicita "
            "5/7: Camaiore, Forte dei Marmi, Pietrasanta, Seravezza e Viareggio hanno valori 2024; Massarosa ha la riga "
            "comunale e la biblioteca IT-LU0029 aperta/attiva ma i campi del lotto non sono alimentati; Stazzema è assente "
            "dal monitoraggio. Entrambi restano `n.d.`, senza zeri, stime o trascinamento dell'ultimo valore.\n\n"
            "Prestiti e impatto espongono l'intera serie ufficiale 1998–2024 dove disponibile e segnalano il 2020 come anno pandemico anomalo. "
            "Per l'apertura la serie è limitata al 2022–2024: nel file Indicatori 2019–2021 il campo delle ore medie "
            "settimanali coincide con l'Indice di apertura e non con `ORESETTIMANALI` del dettaglio biblioteche.\n"
        )
    HISTORY_DOC.write_text(history, encoding="utf-8")

    replace_required(APP_JS, "const VERSION='20260826-v120';", "const VERSION='20260827-v121';")
    replace_required(SERVICE_WORKER, "const VERSION = 'ov-pwa-20260826-v120';", "const VERSION = 'ov-pwa-20260827-v121';")

    text = APP_PART_05.read_text(encoding="utf-8")
    if "2026.08.27-v1.21.0" not in text:
        if "2026.08.26-v1.20.0" not in text:
            raise RuntimeError("Versione v1.20.0 non trovata nel changelog pubblico")
        text = text.replace("2026.08.26-v1.20.0", "2026.08.27-v1.21.0", 1)
        text = text.replace("154 indicatori complessivi", "157 indicatori complessivi", 1)
    APP_PART_05.write_text(text, encoding="utf-8")

    # I workflow CI non sono output del materializzatore dati. Il lotto ha gate
    # dedicati versionati separatamente; mutare .github/workflows qui rendeva
    # il materializzatore non idempotente durante i test della Draft PR.


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    snapshot = load(SNAPSHOT_PATH)
    apply_site(site, snapshot)
    apply_registry(registry)
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    patch_release_files()
    subprocess.run([sys.executable, str(FINALIZER)], check=True, cwd=ROOT)
    print("Cultura e biblioteche v1.21.0 materializzata: 3 indicatori canonici 2024, copertura 5/7 esplicita, nessuna stima.")


if __name__ == "__main__":
    main()
