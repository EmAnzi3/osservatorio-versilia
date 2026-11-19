#!/usr/bin/env python3
"""Serie storica dei contribuenti MEF ogni 100 maggiorenni per i sette Comuni.

Stessa regola del valore pubblicato (anno d'imposta 2024 su residenti 18+ al 1° gennaio
2026): contribuenti dell'anno d'imposta A / residenti di 18 anni e più al 1° gennaio A+2
(Istat POSAS) × 100. Il numeratore viene dal file comunale MEF «Redditi e principali
variabili IRPEF su base comunale» dell'anno A; il denominatore dal file POSAS dei Comuni
dell'anno A+2. Si usano gli anni in cui entrambi i file sono pubblicati, in un intervallo
continuo che termina con l'anno corrente; l'ultimo anno deve coincidere con il valore
pubblicato (stessi contribuenti, stessi maggiorenni).
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
import zipfile
from datetime import date
from typing import Any, Callable

MEF_URL = ("https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/"
           "Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.zip")
POSAS_URL = "https://demo.istat.it/data/posas/POSAS_{year}_it_Comuni.zip"
SNAPSHOT = "data/source-snapshots/mef-contribuenti-serie.json"
METRIC = "taxpayersAdultPopulationRate"
LAG = 2
FIRST = 2012
TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
         "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}


class TaxpayersError(RuntimeError):
    pass


class Unavailable(Exception):
    """Il file dell'anno non è pubblicato (404)."""


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _member(raw: bytes, label: str) -> tuple[str, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))]
        if len(names) != 1:
            raise TaxpayersError(f"{label}: archivio inatteso {names}")
        body = z.read(names[0])
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return names[0], body.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise TaxpayersError(f"{label}: codifica non riconosciuta")


def _int(value: Any, label: str) -> int:
    text = str(value or "").strip().replace(" ", "").replace(" ", "")
    if text in ("", "-", "n.d.", "nd"):
        raise TaxpayersError(f"{label}: valore mancante")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    number = float(text)
    if not number.is_integer() or number < 0:
        raise TaxpayersError(f"{label}: valore non intero {value!r}")
    return int(number)


def mef_taxpayers(raw: bytes, year: int) -> dict[str, Any]:
    member, text = _member(raw, f"MEF {year}")
    try:
        delimiter = csv.Sniffer().sniff(text[:10000], delimiters=";,\t|").delimiter
    except csv.Error:
        delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    code_h = [h for h in headers if norm(h) in ("codice istat comune", "codice istat del comune", "codice comune")]
    count_h = [h for h in headers if norm(h) == "numero contribuenti"]
    if len(code_h) != 1 or len(count_h) != 1:
        raise TaxpayersError(f"MEF {year}: colonne codice/contribuenti {code_h} {count_h}")
    out = {}
    for row in reader:
        code = re.sub(r"\D", "", str(row.get(code_h[0]) or "")).zfill(6)[-6:]
        if code in TOWNS:
            if code in out:
                raise TaxpayersError(f"MEF {year}: riga duplicata {code}")
            out[code] = _int(row.get(count_h[0]), f"MEF {year} {code}")
    if set(out) != set(TOWNS):
        raise TaxpayersError(f"MEF {year}: Comuni trovati {sorted(out)}")
    return {"member": member, "taxpayers": out}


def posas_adults(raw: bytes, year: int) -> dict[str, Any]:
    member, text = _member(raw, f"POSAS {year}")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    head = next((i for i, r in enumerate(rows[:5]) if any(norm(c) == "codice comune" for c in r)), None)
    if head is None:
        raise TaxpayersError(f"POSAS {year}: intestazione assente")
    header = [norm(c) for c in rows[head]]
    code_i = header.index("codice comune")
    age_i = next(i for i, h in enumerate(header) if h in ("eta", "eta anni"))
    total_i = [i for i, h in enumerate(header) if "totale" in h and "maschi" not in h and "femmine" not in h]
    if len(total_i) != 1:
        raise TaxpayersError(f"POSAS {year}: colonna totale {header}")
    adults, check = {c: 0 for c in TOWNS}, {c: [0, None] for c in TOWNS}
    for r in rows[head + 1:]:
        if len(r) <= max(code_i, age_i, total_i[0]):
            continue
        code = re.sub(r"\D", "", r[code_i]).zfill(6)[-6:]
        if code not in TOWNS:
            continue
        age = int(re.sub(r"\D", "", r[age_i]) or -1)
        total = _int(r[total_i[0]], f"POSAS {year} {code} {age}")
        if age == 999:
            check[code][1] = total
            continue
        if age < 0 or age > 120:
            raise TaxpayersError(f"POSAS {year} {code}: età {r[age_i]!r}")
        check[code][0] += total
        if age >= 18:
            adults[code] += total
    for code, (summed, total) in check.items():
        if total is None or summed != total or adults[code] <= 0:
            raise TaxpayersError(f"POSAS {year} {code}: somma età {summed} ≠ totale {total}")
    return {"member": member, "adults": adults}


def build_snapshot(fetcher: Callable[[str], bytes], current: dict[str, dict[str, Any]], last: int) -> dict[str, Any]:
    """`current`: codice → {value, taxpayers, adultPopulation2026} pubblicati; `last`: anno d'imposta corrente."""
    years: dict[int, dict[str, Any]] = {}
    for year in range(last, FIRST - 1, -1):
        try:
            mraw = fetcher(MEF_URL.format(year=year))
            praw = fetcher(POSAS_URL.format(year=year + LAG))
        except Unavailable:
            if year == last:
                raise TaxpayersError(f"anno corrente {year} non disponibile")
            break
        mef, posas = mef_taxpayers(mraw, year), posas_adults(praw, year + LAG)
        years[year] = {
            "mef": {"url": MEF_URL.format(year=year), "sha256": hashlib.sha256(mraw).hexdigest(), "member": mef["member"]},
            "posas": {"url": POSAS_URL.format(year=year + LAG), "sha256": hashlib.sha256(praw).hexdigest(), "member": posas["member"],
                      "date": f"{year + LAG}-01-01"},
            "towns": {c: {"taxpayers": mef["taxpayers"][c], "adults": posas["adults"][c]} for c in TOWNS},
        }
    ordered = sorted(years)
    for code, pub in current.items():
        t = years[last]["towns"][code]
        if t["taxpayers"] != pub["taxpayers"] or t["adults"] != pub["adultPopulation2026"] or t["taxpayers"] / t["adults"] * 100 != pub["value"]:
            raise TaxpayersError(f"{code} {last}: {t} ≠ pubblicato {pub}")
    series = {c: [years[y]["towns"][c]["taxpayers"] / years[y]["towns"][c]["adults"] * 100 for y in ordered] for c in TOWNS}
    return {
        "schemaVersion": 1, "version": f"mef-contribuenti-serie-{ordered[0]}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Dipartimento delle Finanze — MEF / Istat POSAS",
        "sourceUrl": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php", "years": ordered,
        "rule": f"Contribuenti MEF dell'anno d'imposta A / residenti di 18 anni e più al 1° gennaio A+{LAG} (Istat POSAS) × 100, come il valore pubblicato.",
        "archives": {str(y): {k: v for k, v in d.items() if k != "towns"} for y, d in years.items()},
        "towns": {c: {str(y): years[y]["towns"][c] for y in ordered} for c in TOWNS},
        "series": series,
        "qualityGate": {"status": "PASS", "note": f"Anno d'imposta {last} identico al valore pubblicato per i 7 Comuni (contribuenti e maggiorenni)."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    for row in metric["rows"]:
        values = snapshot["series"][row["code"]]
        t = snapshot["towns"][row["code"]][str(years[-1])]
        if values[-1] != row["value"] or t["taxpayers"] != row["taxpayers"] or t["adults"] != row["adultPopulation2026"]:
            raise TaxpayersError(f"{row['town']}: serie {values[-1]} ≠ valore {row['value']}")
        row["series"] = {"years": list(years), "values": list(values)}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    note = (f" Serie {years[0]}–{years[-1]} per anno d'imposta: ogni anno usa i residenti 18+ al 1° gennaio di due anni dopo,"
            " come il valore pubblicato.")
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
