#!/usr/bin/env python3
"""Sonda di un flusso SDMX Istat (esploradati), eseguita sui runner GitHub.

`update_source_data.py sdmx-probe --name NOME --flow ID [--key CHIAVE] [--start ANNO]`
scarica la struttura del flusso (dimensioni in ordine, con i nomi dei codici) e i
dati in CSV, poi scrive in `data/source-probes/NOME.json` le colonne, i valori
distinti di ogni colonna e le righe dei sette Comuni, della provincia di Lucca,
della Toscana e dell'Italia. Non modifica il catalogo: serve a scrivere poi
l'aggiornatore sul formato reale del flusso.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASES = ("https://esploradati.istat.it/SDMXWS/rest", "https://sdmx.istat.it/SDMXWS/rest")
UA = "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"
SDMX_CSV = "application/vnd.sdmx.data+csv;version=1.0.0"
AREAS = ("046005", "046013", "046018", "046024", "046028", "046030", "046033", "046", "ITE12", "ITI12", "ITE1", "ITI1", "IT")
MAX_DISTINCT = 60
MAX_ROWS = 600


def fetch(url: str, accept: str) -> bytes:
    errors = []
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(request, timeout=600) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - la sonda registra ogni errore
            errors.append(f"tentativo {attempt}: {type(error).__name__}: {error}")
            time.sleep(20 * attempt)
    raise RuntimeError(" | ".join(errors))


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def structure(xml: bytes) -> dict[str, Any]:
    """Dimensioni in ordine di posizione e nomi italiani dei codici delle liste collegate."""
    root = ET.fromstring(xml)
    names: dict[str, dict[str, str]] = {}
    for codelist in (e for e in root.iter() if local(e.tag) == "Codelist"):
        codes = {}
        for code in (c for c in codelist if local(c.tag) == "Code"):
            label = next((n.text or "" for n in code if local(n.tag) == "Name"
                          and n.get("{http://www.w3.org/XML/1998/namespace}lang") == "it"), "")
            codes[code.get("id", "")] = label or next((n.text or "" for n in code if local(n.tag) == "Name"), "")
        names[codelist.get("id", "")] = codes
    dims = []
    for dim in (e for e in root.iter() if local(e.tag) in {"Dimension", "TimeDimension"}):
        ref = next((r for r in dim.iter() if local(r.tag) == "Ref" and r.get("class") == "Codelist"), None)
        dims.append({"id": dim.get("id"), "position": dim.get("position"), "codelist": ref.get("id") if ref is not None else None})
    return {"dimensions": dims, "codelists": names}


def summarise(raw: bytes, codelists: dict[str, dict[str, str]], dims: list[dict[str, Any]]) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    columns = reader.fieldnames or []
    by_dim = {d["id"]: codelists.get(d.get("codelist") or "", {}) for d in dims}
    distinct: dict[str, dict[str, int]] = {c: {} for c in columns if c not in {"OBS_VALUE"}}
    rows, count = [], 0
    for row in reader:
        count += 1
        for c in distinct:
            v = (row.get(c) or "").strip()
            if len(distinct[c]) < MAX_DISTINCT or v in distinct[c]:
                distinct[c][v] = distinct[c].get(v, 0) + 1
        area = (row.get("REF_AREA") or row.get("ITTER107") or "").strip()
        if area in AREAS and len(rows) < MAX_ROWS:
            rows.append({k: v for k, v in row.items() if v not in (None, "")})
    labelled = {c: [{"code": v, "rows": n, **({"name": by_dim[c][v]} if by_dim.get(c, {}).get(v) else {})}
                    for v, n in sorted(vals.items())] for c, vals in distinct.items()}
    return {"columns": columns, "rows": count, "distinct": labelled, "versilia": rows}


def flows(xml: bytes, pattern: str) -> list[dict[str, str]]:
    """Flussi dell'elenco Istat il cui identificativo o nome corrisponde all'espressione regolare."""
    out = []
    for df in (e for e in ET.fromstring(xml).iter() if local(e.tag) == "Dataflow"):
        names = {n.get("{http://www.w3.org/XML/1998/namespace}lang"): (n.text or "") for n in df if local(n.tag) == "Name"}
        item = {"id": df.get("id", ""), "agency": df.get("agencyID", ""), "version": df.get("version", ""), "name": names.get("it") or next(iter(names.values()), "")}
        if re.search(pattern, item["id"] + " " + item["name"], re.I):
            out.append(item)
    return out


def find(name: str, pattern: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", name):
        raise RuntimeError("Nome della sonda non valido: minuscole, cifre e trattini")
    probe: dict[str, Any] = {"schemaVersion": 1, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "note": "Sonda SDMX: flussi Istat che corrispondono alla ricerca; non è un dato pubblicato.",
                             "pattern": pattern, "results": {}}
    for base in BASES:
        try:
            probe["results"][base] = flows(fetch(f"{base}/dataflow/IT1", "application/xml"), pattern)
        except (RuntimeError, ET.ParseError) as exc:
            probe["results"][base] = {"error": str(exc)}
    path = ROOT / "data" / "source-probes" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(probe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Sonda {name} scritta in {path.relative_to(ROOT)}")
    return path


def run(name: str, flow: str, key: str = "all", start: str | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", name):
        raise RuntimeError("Nome della sonda non valido: minuscole, cifre e trattini")
    if not re.fullmatch(r"[0-9A-Z_]+", flow) or not re.fullmatch(r"[0-9A-Za-z_.+]*|all", key):
        raise RuntimeError("Flusso o chiave SDMX non validi")
    probe: dict[str, Any] = {"schemaVersion": 1, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "note": "Sonda SDMX: struttura e righe della Versilia; non è un dato pubblicato.",
                             "flow": flow, "key": key}
    st: dict[str, Any] = {"dimensions": [], "codelists": {}}
    attempts = []
    for base in BASES:
        try:
            st = structure(fetch(f"{base}/dataflow/IT1/{flow}?references=all", "application/xml"))
            probe["structureUrl"] = f"{base}/dataflow/IT1/{flow}?references=all"
            probe["dimensions"] = st["dimensions"]
            break
        except (RuntimeError, ET.ParseError) as exc:
            attempts.append(f"{base}: {exc}")
    if attempts:
        probe["structureErrors"] = attempts
    errors = []
    for base in BASES:
        url = f"{base}/data/{flow}/{key}" + (f"?startPeriod={start}" if start else "")
        try:
            probe.update(summarise(fetch(url, SDMX_CSV), st["codelists"], st["dimensions"]))
            probe["dataUrl"] = url
            break
        except RuntimeError as exc:
            errors.append(f"{url}: {exc}")
    if errors:
        probe["dataErrors"] = errors
    path = ROOT / "data" / "source-probes" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(probe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Sonda {name} scritta in {path.relative_to(ROOT)}")
    return path
