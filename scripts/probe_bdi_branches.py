#!/usr/bin/env python3
"""Sonda degli sportelli bancari della Banca d'Italia, eseguita sui runner GitHub.

`update_source_data.py bdi-branches-probe` scarica la «Lista succursali banche»
(open data GIAVA, storico delle sedi) e conta, al 31 dicembre di ogni anno, le
sedi operative per Comune della Versilia, per la Toscana e per l'Italia,
separando i tipi di sede. Scrive `data/source-probes/bdi-sportelli-conteggi.json`.
Non modifica il catalogo: serve a riconciliare il conteggio con la serie Istat
«Servizi bancari - dati comunali» prima di scrivere l'aggiornatore.
"""
from __future__ import annotations

import csv
import http.cookiejar
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
URL = ("https://infostat.bancaditalia.it/GIAVAInquiry-public/getAreaDownloadExport.do?referenceDate="
       "&product=VFLUSSO_SEDE_BANCHE&language=IT&exportType=CSV&username=OBLIXANONYMOUS&isCompressed=S")
LOC_URL = URL.replace("VFLUSSO_SEDE_BANCHE", "VFLUSSO_LOCALITA")
UA = "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"
TOWNS = ("CAMAIORE", "FORTE DEI MARMI", "MASSAROSA", "PIETRASANTA", "SERAVEZZA", "STAZZEMA", "VIAREGGIO")
YEARS = range(2012, 2027)


def fetch(url: str) -> bytes:
    """Il servizio GIAVA reindirizza impostando un cookie di sessione: serve un opener con i cookie."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    errors = []
    for attempt in range(1, 4):
        try:
            with opener.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=600) as r:
                return r.read()
        except Exception as error:  # noqa: BLE001
            errors.append(f"tentativo {attempt}: {type(error).__name__}: {error}")
            time.sleep(20 * attempt)
    raise RuntimeError(" | ".join(errors))


def rows(archive: bytes) -> Iterable[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        text = z.read(name).decode("utf-8-sig", errors="replace")
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        yield {k.strip(): (v or "").strip() for k, v in row.items() if k}


def active(row: dict[str, str], day: str) -> bool:
    """Sede operativa in quel giorno, nella versione anagrafica valida quel giorno."""
    return (row["DATA_I_OPER"] <= day <= row["DATA_F_OPER"]) and (row["DATA_I_VAL"] <= day <= row["DATA_F_VAL"])


def count(table: list[dict[str, str]], tuscany_cabs: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        day = f"{year}-12-31" if year < 2026 else "2026-11-16"
        by: dict[str, dict[str, set[str]]] = {}
        for row in table:
            if row.get("STATO") != "86" or not active(row, day):
                continue
            kind = row.get("DES_TIPO_SEDE") or row.get("TIPO_SEDE") or "?"
            town = row.get("DES_COM_ITA", "")
            keys = ["italy"] + (["tuscany"] if row.get("CAB_COM_ITA") in tuscany_cabs else []) + ([town] if town in TOWNS else [])
            for key in keys:
                by.setdefault(key, {}).setdefault(kind, set()).add(row["ID_SEDE"])
        out[day] = {key: {kind: len(ids) for kind, ids in kinds.items()} | {"tutte": len(set().union(*kinds.values()))}
                    for key, kinds in by.items()}
    return out


def run() -> Path:
    probe: dict[str, Any] = {"schemaVersion": 1, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "note": "Sonda: sedi bancarie operative per Comune, Toscana e Italia; non è un dato pubblicato.",
                             "url": URL}
    try:
        locs = list(rows(fetch(LOC_URL)))
        tuscany = {r["CAB_COMUNE"] for r in locs if r.get("DEN_REGIONE") == "TOSCANA" and r.get("CAB_COMUNE") not in ("", "0")}
        probe["tuscanyComuni"] = len(tuscany)
        probe["versiliaCab"] = {r["DEN_COMUNE"]: r["CAB_COMUNE"] for r in locs if r.get("DEN_PROVINCIA") == "LUCCA" and r.get("DEN_COMUNE") in TOWNS}
        archive = fetch(URL)
        table = list(rows(archive))
        probe["records"] = len(table)
        probe["types"] = sorted({f'{r.get("TIPO_SEDE")} {r.get("DES_TIPO_SEDE")}' for r in table})
        probe["counts"] = count(table, tuscany)
    except Exception as exc:  # noqa: BLE001
        probe["error"] = f"{type(exc).__name__}: {exc}"
    path = ROOT / "data" / "source-probes" / "bdi-sportelli-conteggi.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(probe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Sonda scritta in {path.relative_to(ROOT)}")
    return path
