#!/usr/bin/env python3
"""Integra in site-data.json il dettaglio ATECO 2 cifre di ISTAT ASIA-UL.

Il modulo non crea decine di nuovi indicatori: aggiunge un dataset strutturato
per le schede comunali e per il confronto settoriale. Usa esclusivamente lo
shard ASIA già acquisito dal Cruscotto Italia/AgID e conserva la fonte primaria
ISTAT.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

ATECO_LABELS = {
    "01": "Agricoltura e produzione animale", "02": "Silvicoltura", "03": "Pesca e acquacoltura",
    "05": "Estrazione carbone", "06": "Estrazione petrolio e gas", "07": "Estrazione minerali metalliferi",
    "08": "Altre attività estrattive", "09": "Servizi di supporto estrazione", "10": "Industrie alimentari",
    "11": "Industria bevande", "12": "Industria tabacco", "13": "Industrie tessili",
    "14": "Confezione articoli abbigliamento", "15": "Pelli e calzature", "16": "Industria legno",
    "17": "Carta", "18": "Stampa e supporti registrati", "19": "Coke e prodotti petroliferi",
    "20": "Prodotti chimici", "21": "Prodotti farmaceutici", "22": "Articoli in gomma e plastica",
    "23": "Lavorazione minerali non metalliferi", "24": "Metallurgia", "25": "Prodotti in metallo",
    "26": "Computer, elettronica, ottica", "27": "Apparecchiature elettriche", "28": "Macchinari",
    "29": "Autoveicoli", "30": "Altri mezzi di trasporto", "31": "Mobili",
    "32": "Altre industrie manifatturiere", "33": "Riparazione e installazione macchinari",
    "35": "Energia elettrica, gas, vapore", "36": "Raccolta e trattamento acque", "37": "Gestione reti fognarie",
    "38": "Rifiuti", "39": "Risanamento e bonifica", "41": "Costruzione edifici", "42": "Ingegneria civile",
    "43": "Lavori di costruzione specializzati", "45": "Commercio e riparazione autoveicoli",
    "46": "Commercio all'ingrosso", "47": "Commercio al dettaglio", "49": "Trasporto terrestre",
    "50": "Trasporto marittimo", "51": "Trasporto aereo", "52": "Magazzinaggio e supporto al trasporto",
    "53": "Servizi postali e corriere", "55": "Alloggio", "56": "Ristorazione", "58": "Editoria",
    "59": "Cinema, video e musica", "60": "Radio e TV", "61": "Telecomunicazioni",
    "62": "Informatica e software", "63": "Servizi di informazione", "64": "Servizi finanziari",
    "65": "Assicurazioni e fondi pensione", "66": "Servizi finanziari ausiliari", "68": "Attività immobiliari",
    "69": "Attività legali e contabili", "70": "Direzione aziendale e consulenza",
    "71": "Studi tecnici e architettura", "72": "Ricerca e sviluppo", "73": "Pubblicità e ricerche di mercato",
    "74": "Altre attività professionali", "75": "Veterinaria", "77": "Noleggio e leasing",
    "78": "Ricerca e selezione del personale", "79": "Agenzie di viaggio", "80": "Vigilanza e investigazioni",
    "81": "Servizi per edifici e paesaggio", "82": "Supporto d'ufficio e altri servizi alle imprese",
    "84": "Amministrazione pubblica e difesa", "85": "Istruzione", "86": "Assistenza sanitaria",
    "87": "Assistenza sociale residenziale", "88": "Assistenza sociale non residenziale",
    "90": "Attività creative e artistiche", "91": "Biblioteche e musei", "92": "Lotterie, scommesse e casinò",
    "93": "Attività sportive e intrattenimento", "94": "Organizzazioni associative",
    "95": "Riparazione computer e beni personali", "96": "Altri servizi personali",
    "97": "Servizi domestici", "98": "Produzione di beni per uso proprio", "99": "Organismi extraterritoriali",
}


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise base.DataError(f"{label}: valore numerico mancante o non valido")
    number = float(value)
    if not math.isfinite(number):
        raise base.DataError(f"{label}: valore non finito")
    return number


def _top_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise base.DataError(f"{label}: lista mancante")
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).zfill(2)
        if code == "0010" or not code:
            continue
        ul = _finite(item.get("ul"), f"{label} {code} ul")
        addetti = _finite(item.get("addetti"), f"{label} {code} addetti")
        result.append({
            "code": code,
            "label": str(item.get("label") or ATECO_LABELS.get(code) or f"ATECO {code}"),
            "localUnits": ul,
            "employees": addetti,
        })
    return result[:10]


def _sectors(shard: dict[str, Any], code: str) -> list[dict[str, Any]]:
    detail = shard.get("ateco_dettaglio")
    if not isinstance(detail, dict):
        raise base.DataError(f"ASIA {code}: ateco_dettaglio mancante")
    year = detail.get("2023") or detail.get(2023)
    if not isinstance(year, dict):
        raise base.DataError(f"ASIA {code}: dettaglio ATECO 2023 mancante")
    kpi = shard.get("kpi") or {}
    total_ul = _finite(kpi.get("ul_totali"), f"ASIA {code} ul_totali")
    total_employees = _finite(kpi.get("addetti_totali"), f"ASIA {code} addetti_totali")
    rows: list[dict[str, Any]] = []
    for raw_code, classes in year.items():
        sector_code = str(raw_code).zfill(2)
        if sector_code == "0010" or sector_code not in ATECO_LABELS:
            continue
        if not isinstance(classes, dict):
            continue
        total = classes.get("TOTAL")
        if not isinstance(total, dict):
            continue
        ul = total.get("ul")
        employees = total.get("addetti")
        if ul is None and employees is None:
            continue
        ul_num = 0.0 if ul is None else _finite(ul, f"ASIA {code} ATECO {sector_code} ul")
        emp_num = 0.0 if employees is None else _finite(employees, f"ASIA {code} ATECO {sector_code} addetti")
        if ul_num == 0 and emp_num == 0:
            continue
        rows.append({
            "code": sector_code,
            "label": ATECO_LABELS[sector_code],
            "localUnits": ul_num,
            "employees": emp_num,
            "localUnitsShare": (ul_num / total_ul * 100.0) if total_ul else None,
            "employeesShare": (emp_num / total_employees * 100.0) if total_employees else None,
        })
    rows.sort(key=lambda item: (-item["localUnits"], item["code"]))
    return rows


def apply(data: dict[str, Any], asia: dict[str, dict[str, Any]]) -> dict[str, Any]:
    towns = base._town_rows(data)
    payload = {
        "year": 2023,
        "classification": "ATECO 2007 / NACE Rev.2 — divisioni a 2 cifre",
        "source": "ISTAT — ASIA Unità Locali",
        "sourceUrl": base.ASIA_SOURCE_URL,
        "coverage": "7/7",
        "caveat": (
            "ASIA misura unità locali e addetti medi annui nel luogo di lavoro. "
            "Le unità locali non coincidono con il numero di imprese giuridiche."
        ),
        "towns": {},
    }
    for town in towns:
        code = town["code"]
        shard = asia.get(code)
        if not shard:
            raise base.DataError(f"ASIA {code}: shard mancante")
        base.validate_asia(code, shard)
        kpi = shard.get("kpi") or {}
        sectors = _sectors(shard, code)
        payload["towns"][code] = {
            "town": town["town"],
            "totalLocalUnits": _finite(kpi.get("ul_totali"), f"ASIA {code} ul_totali"),
            "totalEmployees": _finite(kpi.get("addetti_totali"), f"ASIA {code} addetti_totali"),
            "topByLocalUnits": _top_list(kpi.get("top_settori_ul"), f"ASIA {code} top_settori_ul"),
            "topByEmployees": _top_list(kpi.get("top_settori_addetti"), f"ASIA {code} top_settori_addetti"),
            "sectors": sectors,
        }
    data["ateco"] = payload
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--source-dir", type=Path)
    args = parser.parse_args(argv)

    data = base._json_load(args.site_data)
    codes = [row["code"] for row in base._town_rows(data)]
    asia, _agcom, _provenance = base.load_source_shards(codes, args.source_dir)
    updated = apply(data, asia)
    base._json_write(args.site_data, updated)
    print(json.dumps({
        "status": "ok",
        "towns": len(updated["ateco"]["towns"]),
        "year": updated["ateco"]["year"],
        "sectorRows": sum(len(item["sectors"]) for item in updated["ateco"]["towns"].values()),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
