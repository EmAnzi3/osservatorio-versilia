#!/usr/bin/env python3
"""Estende il Lotto A Amministrazione con l'indicatore regionale sui servizi online.

Fonte: Regione Toscana, Indicatori comunali per le politiche locali, ind18,
derivato dalla rilevazione Istat ICT nelle PA locali. Il valore corrente è il
definitivo al 31/12/2022; il file regionale 2024 lo riporta invariato e non va
quindi reinterpretato come annualità 2024.
"""
from __future__ import annotations

import json
from pathlib import Path

import materialize_amministrazione_lotto_a_v2 as base

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
MONITOR_PATH = ROOT / "data" / "source-monitor-state.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "regione-toscana-servizi-online-2018-2022.json"

ONLINE_KEY = "municipalOnlineServicesAdvanced"
SOURCE_PAGE = "https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali"
PROFILE = "regione-toscana-indicatori-comunali"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def metric(site: dict, snapshot: dict) -> dict:
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    rows = []
    current_values = []
    for town in order:
        raw = snapshot["towns"][town]
        value_2018 = float(raw["2018"])
        value_2022 = float(raw["2022"])
        current_values.append(value_2022)
        rows.append({
            **base.base.identity(site, town),
            "value": value_2022,
            "formatted": pct(value_2022),
            "series": {"years": [2018, 2022], "values": [value_2018, value_2022]},
            "normalized": None,
            "benchmarkValue": value_2022,
        })

    aggregate = sum(current_values) / len(current_values)
    return {
        "meta": {
            "key": ONLINE_KEY,
            "theme": "bilanci",
            "label": "Servizi comunali online al massimo livello di disponibilità",
            "shortLabel": "Servizi online · livello massimo",
            "description": (
                "Percentuale dei servizi offerti online dal Comune ai livelli più avanzati della classificazione Istat. "
                "Il metadato regionale include i livelli 3 e 4: invio telematico della modulistica e, al livello 4, "
                "completamento dell'intero procedimento online incluso l'eventuale pagamento."
            ),
            "unit": "percent",
            "year": "2022",
            "source": "Regione Toscana / Istat — ICT nelle PA locali",
            "polarity": "neutral",
            "searchTerms": [
                "servizi online", "servizi digitali comune", "digitalizzazione comune", "servizi telematici",
                "ict pubblica amministrazione", "procedimenti online", "servizi comunali digitali",
            ],
        },
        "sourceUrl": SOURCE_PAGE,
        "rows": rows,
        "aggregate": {
            "value": aggregate,
            "label": "Versilia · media comunale servizi online avanzati",
            "note": (
                "Media aritmetica dei sette valori comunali 2022. Non è una media ponderata per numero di servizi, "
                "perché la fonte pubblica non espone i denominatori comunali dell'indicatore."
            ),
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore ufficiale Regione Toscana / Istat, codice ind18",
            "formula": (
                "Percentuale di servizi offerti online al massimo livello di disponibilità dai Comuni; "
                "il metadato regionale specifica livelli 3 e 4 della rilevazione Istat ICT nelle PA locali."
            ),
            "caveat": (
                "Il dato corrente è il definitivo al 31/12/2022. Il file regionale Indicatori 2024 lo ripropone "
                "invariato e non viene trattato come dato 2024. Il confronto 2018–2022 è informativo ma non perfettamente "
                "omogeneo: il paniere Istat è passato da 24 servizi osservati nel 2018 a 27 nel 2022. "
                "Una quota maggiore descrive una più ampia disponibilità online avanzata, ma non misura da sola qualità, "
                "usabilità o tempi dei servizi."
            ),
            "coverage": "7/7",
            "history": "Due rilevazioni effettive: 2018 e 2022. Nessun carry-forward artificiale negli anni intermedi.",
        },
    }


def update_theme(site: dict) -> None:
    theme = site["themes"]["bilanci"]
    theme["description"] = "Bilanci comunali, capacità di spesa, struttura del personale e digitalizzazione dei servizi."
    theme["metrics"] = [key for key in theme.get("metrics", []) if key != ONLINE_KEY]
    theme["metrics"].append(ONLINE_KEY)
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    section["metrics"] = [key for key in section.get("metrics", []) if key != ONLINE_KEY]
    section["metrics"].append(ONLINE_KEY)
    section["description"] = (
        "Dotazione di personale, ricambio dell'organico, sostenibilità generazionale, formazione e disponibilità online dei servizi."
    )


def update_registry(registry: dict, site: dict) -> None:
    registry.setdefault("sourceProfiles", {})[PROFILE] = {
        "publisher": "Regione Toscana — Ufficio regionale di Statistica / Istat",
        "frequency": "annual",
        "frequencyLabel": "Aggiornamento annuale della batteria regionale",
        "expectedRelease": (
            "La batteria regionale è aggiornata annualmente; ind18 cambia quando è disponibile una nuova rilevazione Istat ICT nelle PA locali."
        ),
        "acquisitionMethod": (
            "CSV ufficiali Regione Toscana a livello comunale; valori ind18 verificati 7/7 e conservati in snapshot versionato."
        ),
        "licenseName": "Open data / condizioni Regione Toscana",
        "licenseUrl": "https://www.regione.toscana.it/open-data",
    }
    registry.setdefault("metricOverrides", {})[ONLINE_KEY] = {"profile": PROFILE}
    registry.setdefault("sourceProfileByUrl", {})[SOURCE_PAGE] = PROFILE
    external = sum(
        1 for item in site["metrics"].values()
        if item.get("dataStorage", {}).get("type") == "external-climate"
    )
    registry["expectedMetricCount"] = len(site["metrics"])
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(site["metrics"]) - external


def update_monitor(monitor: dict) -> None:
    sources = monitor.setdefault("sources", {})
    state = sources.setdefault(SOURCE_PAGE, {
        "url": SOURCE_PAGE,
        "ok": True,
        "status": 200,
        "finalUrl": SOURCE_PAGE,
        "contentType": "text/html",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
        "metrics": [],
        "roles": ["primary"],
        "profileIds": [PROFILE],
        "frequencies": ["annual"],
    })
    state["metrics"] = sorted(set(state.get("metrics", [])) | {ONLINE_KEY})
    state["profileIds"] = sorted(set(state.get("profileIds", [])) | {PROFILE})
    state["frequencies"] = sorted(set(state.get("frequencies", [])) | {"annual"})


def main() -> None:
    base.main()
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    snapshot = load(SNAPSHOT_PATH)

    site["metrics"].pop(ONLINE_KEY, None)
    site["metrics"][ONLINE_KEY] = metric(site, snapshot)
    update_theme(site)
    update_registry(registry, site)
    update_monitor(monitor)

    if len(site["metrics"]) != 138:
        raise RuntimeError(f"Conteggio inatteso dopo servizi online: {len(site['metrics'])}")

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    print("Amministrazione Lotto A v3: 138 indicatori totali; servizi online avanzati Regione Toscana/Istat 2022 materializzati 7/7.")


if __name__ == "__main__":
    main()
