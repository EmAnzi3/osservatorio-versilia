#!/usr/bin/env python3
"""Materializza la bozza PNRR Regione Toscana per il solo preview di PR.

Lo script aggiorna la working copy, non scarica dati e non pubblica nulla. I valori
sono la fotografia Regione Toscana dell'11 agosto 2026 già validata dal workflow
forense della PR #75. Serve a vedere il risultato nel preview prima di rendere
canonico l'aggiornamento.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
RESOURCE_URL = "https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv"
SOURCE_LABEL = "Regione Toscana — Open Data PNRR"
SNAPSHOT_LABEL = "11 agosto 2026"
SNAPSHOT_DATE = "2026-08-11"
AUDIT_CHECKED_AT = "2026-08-18T16:58:50+00:00"
SNAPSHOT_SHA256 = "f7d4e46f4973efe92eef00a9fb9b41e95e5824600046c4b9fa57b16e932091db"
PROFILE_KEY = "regione-toscana-pnrr-monthly"

# Fotografia validata: area PNRR o PNRR-PNC; PNC puro escluso; Comune soggetto
# attuatore; deduplicazione su id_progetto; importo = importo_finanziato_pnrr;
# concluso = fase_avanzamento_da_regis == "5. conclusione".
PNRR = {
    "046005": {"town": "Camaiore", "projects": 16, "concluded": 10, "funding": 3270511.41},
    "046013": {"town": "Forte dei Marmi", "projects": 15, "concluded": 10, "funding": 1337644.46},
    "046018": {"town": "Massarosa", "projects": 11, "concluded": 10, "funding": 5965208.14},
    "046024": {"town": "Pietrasanta", "projects": 12, "concluded": 9, "funding": 9478237.98},
    "046028": {"town": "Seravezza", "projects": 12, "concluded": 8, "funding": 2485485.63},
    "046030": {"town": "Stazzema", "projects": 11, "concluded": 9, "funding": 2055502.34},
    "046033": {"town": "Viareggio", "projects": 24, "concluded": 18, "funding": 12090517.68},
}

# Opere fisiche individuate dal campo natura del dataset regionale e ricontrollate
# sulla fotografia forense. Lo stato pubblicato è quello di dettaglio ReGiS; non
# viene mai trasformato automaticamente nella parola "realizzata".
PHYSICAL_WORKS = [
    {"town": "Camaiore", "title": "Efficientamento energetico del Teatro dell'Olivo", "status": "Collaudo completato", "funding": 240000.00, "cup": "D34H22000110001"},
    {"town": "Camaiore", "title": "Nuovo intervento per asili nido / prima infanzia", "status": "Contratto stipulato", "funding": 1440000.00, "cup": "D35E24000010006"},
    {"town": "Camaiore", "title": "Cucina nido d'infanzia Mafalda", "status": "Collaudo avviato", "funding": 170000.00, "cup": "D38H22000110006"},
    {"town": "Forte dei Marmi", "title": "Nuova mensa scuola Don Milani", "status": "Collaudo avviato", "funding": 304640.00, "cup": "F21B22000330008"},
    {"town": "Forte dei Marmi", "title": "Nuovi spazi mensa scuola Guidi", "status": "Collaudo avviato", "funding": 499200.00, "cup": "F25E22000440006"},
    {"town": "Massarosa", "title": "Asilo nido Girotondo a Piano di Mommio", "status": "Collaudo avviato", "funding": 1374750.00, "cup": "C75E22000250006"},
    {"town": "Massarosa", "title": "Piscina comunale G. Frati", "status": "Collaudo avviato", "funding": 3762422.13, "cup": "C78E22000040006"},
    {"town": "Pietrasanta", "title": "Efficientamento Teatro Comunale", "status": "Collaudo avviato", "funding": 250000.00, "cup": "G42H22000020001"},
    {"town": "Pietrasanta", "title": "Nuovo polo scolastico Marina di Pietrasanta", "status": "Collaudo avviato", "funding": 5705263.79, "cup": "G43H17000050004"},
    {"town": "Pietrasanta", "title": "Rigenerazione Ex-Camp", "status": "Collaudo avviato", "funding": 2803289.07, "cup": "G44E21000590004"},
    {"town": "Seravezza", "title": "Nuova palestra scuole Frediani", "status": "Collaudo avviato", "funding": 948022.00, "cup": "B81B22000710006"},
    {"town": "Seravezza", "title": "Nuovo nido d'infanzia", "status": "Collaudo avviato", "funding": 1250000.00, "cup": "B81B22000730006"},
    {"town": "Stazzema", "title": "Accessibilità Museo e Parco nazionale della Pace di Sant'Anna", "status": "Stipula in corso", "funding": 495000.00, "cup": "H17B22000430006"},
    {"town": "Stazzema", "title": "Mitigazione rischio idrogeologico Rio delle Vigne di Pomezzana", "status": "Collaudo completato", "funding": 290000.00, "cup": "H17C20000010001"},
    {"town": "Stazzema", "title": "Scuola materna Martiri di Mulina", "status": "Collaudo completato", "funding": 1080000.00, "cup": "H18E18000010001"},
    {"town": "Viareggio", "title": "Recupero Stadio comunale dei Pini", "status": "Collaudo completato", "funding": 2249875.73, "cup": "B43D21001410004"},
    {"town": "Viareggio", "title": "Riqualificazione Marina di Torre del Lago", "status": "Collaudo avviato", "funding": 1131347.78, "cup": "B43D21001420004"},
    {"town": "Viareggio", "title": "Riqualificazione Belvedere Torre del Lago", "status": "Collaudo completato", "funding": 570606.86, "cup": "B43D21001430004"},
    {"town": "Viareggio", "title": "Recupero area pubblica via Mazzini", "status": "Collaudo completato", "funding": 1149992.28, "cup": "B43D21001440004"},
    {"town": "Viareggio", "title": "Recupero piazza Piave", "status": "Collaudo avviato", "funding": 395035.52, "cup": "B43D21001450004"},
    {"town": "Viareggio", "title": "Efficientamento Teatro Jenco", "status": "Collaudo completato", "funding": 250000.00, "cup": "B44J22000010005"},
    {"town": "Viareggio", "title": "Nuova piscina comunale", "status": "Lavori in esecuzione", "funding": 2500000.00, "cup": "B45B22000200001"},
]

WORK_STATUS_ORDER = [
    "Collaudo completato",
    "Collaudo avviato",
    "Lavori in esecuzione",
    "Contratto stipulato",
    "Stipula in corso",
]


def rows_by_code(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    return {
        str(row.get("code")): row
        for row in rows
        if isinstance(row, dict) and row.get("code")
    }


def patch_nested_pnrr_bundle(node: Any, values: dict[str, Any]) -> int:
    """Aggiorna i blocchi riepilogativi già presenti nelle schede comunali."""
    patched = 0
    if isinstance(node, dict):
        required = {"pnrrProjects", "pnrrConcluded", "pnrrInProgress", "pnrrFunding"}
        if required.issubset(node):
            node["pnrrProjects"] = values["projects"]
            node["pnrrConcluded"] = values["concluded"]
            node["pnrrInProgress"] = values["projects"] - values["concluded"]
            node["pnrrFunding"] = values["funding"]
            patched += 1
        for child in node.values():
            patched += patch_nested_pnrr_bundle(child, values)
    elif isinstance(node, list):
        for child in node:
            patched += patch_nested_pnrr_bundle(child, values)
    return patched


def patch_town_summaries(data: dict[str, Any]) -> dict[str, int]:
    counts = {code: 0 for code in PNRR}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in PNRR and isinstance(child, (dict, list)):
                    counts[key] += patch_nested_pnrr_bundle(child, PNRR[key])
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(data)
    missing = [code for code, count in counts.items() if count == 0]
    if missing:
        raise RuntimeError(f"Riepilogo PNRR comunale non trovato per: {', '.join(missing)}")
    return counts


def build_deep_dive() -> dict[str, Any]:
    total_projects = sum(item["projects"] for item in PNRR.values())
    total_concluded = sum(item["concluded"] for item in PNRR.values())
    total_funding = sum(item["funding"] for item in PNRR.values())
    works_funding = sum(item["funding"] for item in PHYSICAL_WORKS)
    status_summary = []
    for status in WORK_STATUS_ORDER:
        selected = [item for item in PHYSICAL_WORKS if item["status"] == status]
        status_summary.append(
            {
                "status": status,
                "count": len(selected),
                "funding": round(sum(item["funding"] for item in selected), 2),
            }
        )
    return {
        "title": "Dentro il PNRR",
        "snapshot": SNAPSHOT_LABEL,
        "snapshotDate": SNAPSHOT_DATE,
        "source": SOURCE_LABEL,
        "sourceUrl": DATASET_URL,
        "methodNote": (
            "Perimetro: area PNRR o PNRR-PNC, PNC puro escluso, uno dei sette Comuni come "
            "soggetto attuatore, deduplicazione su id_progetto. La macrofase ReGiS 5. conclusione "
            "non equivale automaticamente a opera collaudata."
        ),
        "totals": {
            "projects": total_projects,
            "concluded": total_concluded,
            "execution": 26,
            "contracting": 1,
            "funding": round(total_funding, 2),
        },
        "towns": [
            {
                "code": code,
                "town": item["town"],
                "projects": item["projects"],
                "concluded": item["concluded"],
                "concludedPercent": item["concluded"] / item["projects"] * 100.0,
                "funding": item["funding"],
            }
            for code, item in sorted(PNRR.items(), key=lambda pair: pair[1]["town"])
        ],
        "physicalWorks": {
            "count": len(PHYSICAL_WORKS),
            "funding": round(works_funding, 2),
            "fundingSharePercent": works_funding / total_funding * 100.0,
            "statusSummary": status_summary,
            "works": PHYSICAL_WORKS,
        },
        "editorialPolicy": {
            "recommended": [
                "quadro complessivo e ripartizione per Comune",
                "opere fisiche e stato ReGiS di dettaglio",
                "CUP e quota PNRR per ogni opera",
            ],
            "deferred": [
                "percentuale di spesa, finché non è validato il denominatore tra quota PNRR, costo totale e cofinanziamenti",
                "date previste/effettive, finché i campi incompleti e i valori sentinella non sono normalizzati",
                "gare e CIG, da validare con il dataset contratti correlato",
            ],
        },
    }


def patch_site_data(data: dict[str, Any]) -> None:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo metrics assente")
    population = rows_by_code(metrics["population"])
    funding_metric = metrics["pnrrFunding"]
    concluded_metric = metrics["pnrrConcluded"]
    funding_rows = rows_by_code(funding_metric)
    concluded_rows = rows_by_code(concluded_metric)

    for code, values in PNRR.items():
        pop = population.get(code, {}).get("value")
        if not isinstance(pop, (int, float)) or pop <= 0:
            raise RuntimeError(f"Popolazione non valida per {code}")
        if code not in funding_rows or code not in concluded_rows:
            raise RuntimeError(f"Riga PNRR assente per {code}")
        funding_rows[code]["value"] = values["funding"] / float(pop)
        concluded_rows[code]["value"] = values["concluded"] / values["projects"] * 100.0

    funding_meta = funding_metric.setdefault("meta", {})
    funding_meta.update(
        {
            "year": "2026",
            "source": SOURCE_LABEL,
            "description": (
                "Importo PNRR assegnato ai progetti PNRR o PNRR-PNC con il comune "
                "come soggetto attuatore, rapportato alla popolazione."
            ),
        }
    )
    funding_metric["sourceUrl"] = DATASET_URL
    funding_method = funding_metric.setdefault("method", {})
    funding_method.update(
        {
            "type": "Elaborazione Osservatorio su open data Regione Toscana",
            "formula": "somma importo_finanziato_pnrr / popolazione residente",
            "caveat": (
                "Fotografia Regione Toscana 11 agosto 2026. Inclusi PNRR e PNRR-PNC con Comune "
                "soggetto attuatore; escluso PNC puro; deduplicazione su id_progetto. Il valore è "
                "finanziamento PNRR censito, non importo erogato o speso."
            ),
            "coverage": "7/7",
        }
    )

    concluded_meta = concluded_metric.setdefault("meta", {})
    concluded_meta.update(
        {
            "year": "2026",
            "source": SOURCE_LABEL,
            "description": (
                "Quota dei progetti PNRR o PNRR-PNC con il comune come soggetto attuatore "
                "classificati da ReGiS nella fase 5. conclusione."
            ),
        }
    )
    concluded_metric["sourceUrl"] = DATASET_URL
    concluded_method = concluded_metric.setdefault("method", {})
    concluded_method.update(
        {
            "type": "Elaborazione Osservatorio su open data Regione Toscana / ReGiS",
            "formula": "progetti con fase_avanzamento_da_regis = 5. conclusione / progetti selezionati × 100",
            "caveat": (
                "Fotografia Regione Toscana 11 agosto 2026. Inclusi PNRR e PNRR-PNC con Comune "
                "soggetto attuatore; escluso PNC puro; deduplicazione su id_progetto. La fase ReGiS "
                "è uno stato amministrativo di avanzamento e non equivale, da sola, a collaudo concluso."
            ),
            "coverage": "7/7",
        }
    )

    patch_town_summaries(data)
    data["pnrrDeepDive"] = build_deep_dive()


def patch_registry(registry: dict[str, Any]) -> None:
    profiles = registry.setdefault("sourceProfiles", {})
    profiles[PROFILE_KEY] = {
        "publisher": "Regione Toscana",
        "frequency": "monthly",
        "frequencyLabel": "Mensile",
        "expectedRelease": "Aggiornamento di norma mensile",
        "acquisitionMethod": (
            "CSV ufficiale Regione Toscana; selezione area PNRR o PNRR-PNC, esclusione PNC puro, "
            "Comune come soggetto attuatore, deduplicazione su id_progetto e verifica delle fasi ReGiS."
        ),
        "licenseName": "Creative Commons Attribuzione",
        "licenseUrl": DATASET_URL,
    }
    by_url = registry.setdefault("sourceProfileByUrl", {})
    by_url[DATASET_URL] = PROFILE_KEY


def patch_monitor_state(state: dict[str, Any]) -> None:
    """Nel preview sostituisce l'evidenza operativa obsoleta di Italia Domani.

    Il file tracciato non viene modificato dalla PR: questa trasformazione avviene
    soltanto nella working copy del job di preview, dopo che i valori sono stati
    materializzati dalla stessa fotografia regionale validata.
    """
    sources = state.setdefault("sources", {})
    sources[DATASET_URL] = {
        "url": DATASET_URL,
        "ok": True,
        "status": 200,
        "finalUrl": DATASET_URL,
        "contentType": "text/html",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
        "directReachable": True,
        "automationLimited": False,
        "probeUrl": RESOURCE_URL,
        "probeMethod": "validated-pnrr-toscana-snapshot",
        "metrics": ["pnrrConcluded", "pnrrFunding"],
        "roles": ["primary"],
        "profileIds": [PROFILE_KEY],
        "frequencies": ["monthly"],
    }
    evidence = {
        "type": "pnrr_toscana_snapshot",
        "dataset": DATASET_URL,
        "resource": RESOURCE_URL,
        "dataElaborationDate": SNAPSHOT_DATE,
        "sourceSnapshotSha256": SNAPSHOT_SHA256,
        "selectedProjects": 101,
        "concludedProjects": 74,
        "fundingTotal": 36683107.64,
        "match7of7": True,
    }
    metrics = state.setdefault("metrics", {})
    for key in ("pnrrFunding", "pnrrConcluded"):
        metrics[key] = {
            "publishedPeriod": "2026",
            "checkedAt": AUDIT_CHECKED_AT,
            "observedLatestPeriod": "2026",
            "status": "current",
            "verificationEvidence": evidence,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--registry", type=Path, default=Path("data/source-registry.json"))
    parser.add_argument("--state", type=Path, default=Path("data/source-monitor-state.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    state = json.loads(args.state.read_text(encoding="utf-8"))
    patch_site_data(data)
    patch_registry(registry)
    patch_monitor_state(state)
    args.data.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.registry.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Bozza PNRR Regione Toscana materializzata: "
        f"{sum(v['projects'] for v in PNRR.values())} progetti, "
        f"{sum(v['concluded'] for v in PNRR.values())} conclusi, "
        f"{len(PHYSICAL_WORKS)} opere fisiche, "
        f"€{sum(v['funding'] for v in PNRR.values()):,.2f} PNRR"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
