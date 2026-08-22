#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOWS = {
    "lavoro": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "istruzione": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}
TOWNS = {
    "Camaiore": "046005",
    "Forte dei Marmi": "046013",
    "Massarosa": "046018",
    "Pietrasanta": "046024",
    "Seravezza": "046028",
    "Stazzema": "046030",
    "Viareggio": "046033",
}


def fetch(url: str, accept: str = "application/vnd.sdmx.structure+json;version=1.0", timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0", "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def print_json_structure(flow: str) -> None:
    url = f"{BASE}/dataflow/IT1/{flow}/1.0?references=all&format=jsonstructure"
    raw = fetch(url)
    obj = json.loads(raw)
    print(f"\n=== {flow} STRUCTURE JSON keys ===")
    print(list(obj.keys()))
    text = raw.decode("utf-8", errors="replace")
    for needle in ["SEX", "ETA", "AGE", "TERRITORIO", "ITTER107", "CITTAD", "ISTRUZ", "OCCUP", "COND"]:
        if needle.lower() in text.lower():
            print("FOUND", needle)
    # Ricerca ricorsiva di oggetti che sembrano dimensioni/codelist.
    hits = []
    def walk(x, path=""):
        if isinstance(x, dict):
            keys = set(x)
            if any(k in keys for k in ("id", "name", "values", "codelist", "position")):
                s = json.dumps(x, ensure_ascii=False)
                if any(n.lower() in s.lower() for n in ("sex", "sesso", "age", "eta", "età", "occup", "istru", "territ", "itter")):
                    hits.append((path, x))
            for k,v in x.items():
                walk(v, f"{path}/{k}")
        elif isinstance(x, list):
            for i,v in enumerate(x[:5000]):
                walk(v, f"{path}/{i}")
    walk(obj)
    for path, hit in hits[:80]:
        print("HIT", path, json.dumps(hit, ensure_ascii=False)[:1200])


def sample_csv(flow: str) -> None:
    # Chiede le chiavi di serie: serve per ricavare ordine e codici delle dimensioni senza scaricare tutte le osservazioni.
    url = f"{BASE}/data/IT1,{flow},1.0?detail=serieskeysonly&format=csvfile"
    raw = fetch(url, "application/vnd.sdmx.data+csv;version=1.0.0", 240)
    text = raw.decode("utf-8-sig", errors="replace")
    print(f"\n=== {flow} SERIES CSV bytes={len(raw)} ===")
    lines = text.splitlines()
    for line in lines[:25]:
        print(line[:2000])
    if not lines:
        return
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i,row in enumerate(reader):
        rows.append(row)
        if i >= 200000:
            break
    print("HEADER", reader.fieldnames)
    # Mostra cardinalità iniziali per colonne, utile per riconoscere sesso/età/territorio.
    if rows:
        for col in reader.fieldnames or []:
            vals = sorted({str(r.get(col, "")) for r in rows if r.get(col, "") != ""})
            if len(vals) <= 80:
                print("VALUES", col, vals[:80])
            else:
                print("VALUES", col, f"{len(vals)} distinct", vals[:20])


def main() -> None:
    for name, flow in FLOWS.items():
        print(f"\n######## {name.upper()} {flow} ########")
        try:
            print_json_structure(flow)
        except Exception as exc:
            print("STRUCTURE ERROR", type(exc).__name__, repr(exc))
        time.sleep(13)  # ISTAT limita a 5 query/minuto/IP.
        try:
            sample_csv(flow)
        except Exception as exc:
            print("SERIES ERROR", type(exc).__name__, repr(exc))
        time.sleep(13)


if __name__ == "__main__":
    main()
