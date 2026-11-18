#!/usr/bin/env python3
"""Fabbisogni standard dei Comuni (OpenCivitas, SOSE e MEF): spesa e servizi rispetto allo standard.

OpenCivitas pubblica, per ogni Comune delle regioni a statuto ordinario, la spesa
storica e la spesa standard (il fabbisogno standard riproporzionato, cioè quanto
servirebbe a un Comune con le stesse caratteristiche) per le funzioni fondamentali,
e lo scostamento percentuale dei servizi svolti dal livello standard.

Il file «Indicatori — Totale funzioni» è in formato lungo (USERNAME; indicatore;
valore). L'anagrafica degli enti collega lo USERNAME al codice Istat e alla regione.
Da qui si ricavano due indicatori:

* `standardNeedsSpendingGap`: (spesa storica / spesa standard − 1) × 100;
* `standardNeedsServiceGap`: scostamento % dei servizi svolti dal livello standard,
  come pubblicato (DIFF_OUT_PERC_TOT).

Aggregati: lo scostamento della spesa si calcola sui totali (Σ spesa storica /
Σ spesa standard); quello dei servizi come media degli scostamenti comunali
ponderata sulla spesa standard. Toscana e Italia usano la stessa regola sui Comuni
valutabili (FL_NO_VALUTABILE = 0); Italia significa Comuni delle regioni a statuto
ordinario, l'unico perimetro dei fabbisogni standard.
"""
from __future__ import annotations

import csv
import hashlib
import http.cookiejar
import io
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

SPENDING = "standardNeedsSpendingGap"
SERVICE = "standardNeedsServiceGap"
METRICS = (SPENDING, SERVICE)
SNAPSHOT_PREFIX = "data/source-snapshots/opencivitas-fabbisogni-"
PAGE = "https://www.opencivitas.it/portale/open-data"
LIST_URL = PAGE + "?xpage={page}&xdelta=6"
LIST_PAGES = 12
PUBLISHER = "OpenCivitas (SOSE — MEF) — Fabbisogni standard dei Comuni"
UA = "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"
# Comune Istat → USERNAME OpenCivitas (provincia di Lucca)
TOWNS = {"046005": "LU005SIF11RN", "046013": "LU013SIF11RV", "046018": "LU018SIF11SA", "046024": "LU024SIF11SG",
         "046028": "LU028SIF11SK", "046030": "LU030SIF11SM", "046033": "LU033SIF11SP"}
FIELDS = {"spesaStorica": "SPESA_STORICA", "spesaStandard": "FST_RIPROPORZIONATO_BI",
          "spesaStoricaProAb": "SPESA_STORICA_PROAB", "spesaStandardProAb": "FST_RIPROPORZIONATO_BI_PROAB",
          "serviceGapPct": "DIFF_OUT_PERC_TOT", "spendingLevel": "POSIZIONE_SPESA_PERC_TOT",
          "serviceLevel": "POSIZIONE_OUTPUT_PERC_TOT", "notEvaluable": "FL_NO_VALUTABILE"}
# Sonda del 17 novembre 2026 sul file 2023 (data/source-probes/opencivitas-totale-2023.json):
# l'acquisizione deve ritrovare esattamente questi valori.
PROBE_2023 = {
    "046005": {"spesaStorica": 29101909.98, "spesaStandard": 31185682.46, "serviceGapPct": 15.39143729},
    "046013": {"spesaStorica": 23349412.38, "spesaStandard": 10590362.97, "serviceGapPct": 254.897841},
    "046018": {"spesaStorica": 14357945.62, "spesaStandard": 15508425.97, "serviceGapPct": -6.115557831},
    "046024": {"spesaStorica": 29952245.92, "spesaStandard": 24129575.89, "serviceGapPct": 99.50314734},
    "046028": {"spesaStorica": 11551204.9, "spesaStandard": 9647934.301, "serviceGapPct": 0.231967868},
    "046030": {"spesaStorica": 3623293.527, "spesaStandard": 2409708.515, "serviceGapPct": -0.432686629},
    "046033": {"spesaStorica": 67452176.99, "spesaStandard": 58725210.89, "serviceGapPct": 16.17809167},
}
TUSCANY_RANGE = (230, 290)   # Comuni toscani nell'anagrafica
ITALY_RANGE = (6000, 7000)   # Comuni delle regioni a statuto ordinario


class NeedsError(RuntimeError):
    pass


def fetch(url: str) -> bytes:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    errors = []
    for attempt in range(1, 4):
        try:
            with opener.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=600) as r:
                return r.read()
        except Exception as error:  # noqa: BLE001
            errors.append(f"tentativo {attempt}: {type(error).__name__}: {error}")
            time.sleep(15 * attempt)
    raise NeedsError(f"{url}: " + " | ".join(errors))


DATA_RE = re.compile(r"""href=["']([^"']*/documents/20118/0/(20\d\d)_Ind_TOT_01_IT\.csv/[0-9a-f-]+)["']""", re.I)
ENTI_RE = r"""href=["']([^"']*/documents/20118/0/Metadati_Enti_{year}_IT\.xlsx/[0-9a-f-]+)["']"""


def discover(pages: dict[int, str], year: int | None = None) -> dict[str, Any]:
    """Link al file «Totale funzioni» dell'ultima annualità (o di `year`) e alla sua anagrafica enti."""
    data: dict[int, tuple[str, int]] = {}
    for n, text in sorted(pages.items()):
        for m in DATA_RE.finditer(text):
            data.setdefault(int(m.group(2)), (urllib.parse.urljoin(PAGE, m.group(1)), n))
    if not data:
        raise NeedsError("nessun file «Ind_TOT_01_IT» nelle pagine open data")
    chosen = year if year is not None else max(data)
    if chosen not in data:
        raise NeedsError(f"annualità {chosen} non pubblicata (disponibili {sorted(data)})")
    enti = [urllib.parse.urljoin(PAGE, m.group(1)) for text in pages.values() for m in re.finditer(ENTI_RE.format(year=chosen), text, re.I)]
    if not enti:
        raise NeedsError(f"anagrafica enti {chosen} assente")
    return {"year": chosen, "dataUrl": data[chosen][0], "listPage": data[chosen][1], "entiUrl": enti[0], "available": sorted(data)}


def number(text: str) -> float | None:
    text = (text or "").strip().replace(".", "").replace(",", ".") if "," in (text or "") else (text or "").strip()
    if not text:
        return None
    return float(text)


def long_table(raw: bytes) -> dict[str, dict[str, str]]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = [h.strip() for h in next(reader)]
    if header[:3] != ["USERNAME", "Indicatore/Determinante", "Valore"]:
        raise NeedsError(f"intestazione inattesa: {header}")
    out: dict[str, dict[str, str]] = {}
    for row in reader:
        if len(row) >= 3:
            out.setdefault(row[0].strip(), {})[row[1].strip()] = row[2].strip()
    return out


def registry(rows: list[list[Any]]) -> dict[str, dict[str, str]]:
    """USERNAME → {istat, regione, ente} dall'anagrafica (prima riga intestazione)."""
    header = [str(h or "").strip() for h in rows[0]]
    need = ["USERNAME", "TIPOLOGIA_ENTE", "ENTE", "REGIONE_DES", "COMUNE_ISTAT_COD"]
    if any(h not in header for h in need):
        raise NeedsError(f"anagrafica enti: colonne mancanti {[h for h in need if h not in header]}")
    idx = {h: header.index(h) for h in need}
    out = {}
    for row in rows[1:]:
        cells = [str(c or "").strip() for c in row]
        if len(cells) > max(idx.values()) and cells[idx["TIPOLOGIA_ENTE"]] == "COMUNE":
            out[cells[idx["USERNAME"]]] = {"istat": cells[idx["COMUNE_ISTAT_COD"]].zfill(6), "regione": cells[idx["REGIONE_DES"]], "ente": cells[idx["ENTE"]]}
    return out


def xlsx_rows(raw: bytes) -> list[list[Any]]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    ws.reset_dimensions()
    return [list(r) for r in ws.iter_rows(values_only=True)]


def town_record(values: dict[str, str], username: str) -> dict[str, Any]:
    rec: dict[str, Any] = {"username": username}
    for key, field in FIELDS.items():
        if field not in values:
            raise NeedsError(f"{username}: campo {field} assente")
        rec[key] = number(values[field])
    rec["notEvaluable"] = int(rec["notEvaluable"] or 0)
    for key in ("spesaStorica", "spesaStandard", "spesaStoricaProAb", "spesaStandardProAb", "serviceGapPct"):
        if rec[key] is None:
            raise NeedsError(f"{username}: valore {FIELDS[key]} vuoto")
    # La popolazione implicita nei valori pro capite deve essere la stessa per spesa storica e standard.
    pop_hist = rec["spesaStorica"] / rec["spesaStoricaProAb"]
    pop_std = rec["spesaStandard"] / rec["spesaStandardProAb"]
    if abs(pop_hist - pop_std) > 1:
        raise NeedsError(f"{username}: popolazione implicita incoerente ({pop_hist:.1f} ≠ {pop_std:.1f})")
    rec["population"] = round(pop_hist)
    return rec


def scope_totals(table: dict[str, dict[str, str]], users: list[str]) -> dict[str, Any]:
    spesa = standard = weighted = 0.0
    evaluable = 0
    for u in users:
        v = table.get(u, {})
        try:
            s, f, g = number(v.get("SPESA_STORICA", "")), number(v.get("FST_RIPROPORZIONATO_BI", "")), number(v.get("DIFF_OUT_PERC_TOT", ""))
        except ValueError:
            continue
        if str(v.get("FL_NO_VALUTABILE", "")).strip() not in ("0", "") or None in (s, f, g) or not f:
            continue
        evaluable += 1
        spesa += s
        standard += f
        weighted += g * f
    return {"municipalities": len(users), "evaluable": evaluable, "spesaStorica": round(spesa, 2),
            "spesaStandard": round(standard, 2), "serviceGapWeightedSum": round(weighted, 4)}


def build_snapshot(found: dict[str, Any], raw: bytes, enti_raw: bytes, enti_rows: list[list[Any]] | None = None) -> dict[str, Any]:
    year = found["year"]
    table = long_table(raw)
    reg = registry(enti_rows if enti_rows is not None else xlsx_rows(enti_raw))
    by_istat = {v["istat"]: u for u, v in reg.items()}
    towns = {}
    for code, username in TOWNS.items():
        if by_istat.get(code) != username:
            raise NeedsError(f"Comune {code}: USERNAME {by_istat.get(code)!r}, atteso {username}")
        if username not in table:
            raise NeedsError(f"{username}: assente nel file {year}")
        rec = town_record(table[username], username)
        if rec["notEvaluable"]:
            raise NeedsError(f"{username}: spesa o servizi non valutabili nel {year}")
        towns[code] = {"ente": reg[username]["ente"], **rec}
    if year == 2023:
        for code, expect in PROBE_2023.items():
            for key, value in expect.items():
                if abs(towns[code][key] - value) > 1e-6 * max(1.0, abs(value)):
                    raise NeedsError(f"{code} {key}: {towns[code][key]} diverso dalla sonda ({value})")
    present = [u for u in reg if u in table]
    tuscany = [u for u in present if reg[u]["regione"] == "TOSCANA"]
    scopes = {"tuscany": scope_totals(table, tuscany), "italy": scope_totals(table, present)}
    if not TUSCANY_RANGE[0] <= scopes["tuscany"]["evaluable"] <= TUSCANY_RANGE[1]:
        raise NeedsError(f"Comuni toscani valutabili fuori intervallo: {scopes['tuscany']}")
    if not ITALY_RANGE[0] <= scopes["italy"]["evaluable"] <= ITALY_RANGE[1]:
        raise NeedsError(f"Comuni valutabili in Italia fuori intervallo: {scopes['italy']}")
    return {
        "schemaVersion": 1, "version": f"opencivitas-fabbisogni-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": PUBLISHER, "sourceUrl": PAGE, "dataUrl": found["dataUrl"], "entiUrl": found["entiUrl"],
        "listPage": found["listPage"], "availableYears": found["available"], "year": year,
        "archive": {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "entities": len(table)},
        "entiArchive": {"bytes": len(enti_raw), "sha256": hashlib.sha256(enti_raw).hexdigest(), "municipalities": len(reg)},
        "rule": ("Spesa storica e spesa standard (fabbisogno standard riproporzionato) del totale delle funzioni fondamentali; "
                 "scostamento dei servizi svolti dal livello standard come pubblicato. Aggregati sui Comuni valutabili: "
                 "Σ spesa storica / Σ spesa standard; servizi come media ponderata sulla spesa standard."),
        "towns": towns,
        "scopes": scopes,
        "qualityGate": {"status": "PASS", "probe2023": year != 2023 or "7/7",
                        "note": "Valori dei sette Comuni identici alla sonda del file 2023; popolazione implicita coerente fra spesa storica e standard."},
    }


def spending_gap(spesa: float, standard: float) -> float:
    return (spesa / standard - 1) * 100


def signed(value: float) -> str:
    text = f"{abs(value):.1f}".replace(".", ",") + "%"
    return ("+" if value > 0 else "−" if value < 0 else "") + text


def euro(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + " €"


def build_metrics(snapshot: dict[str, Any], rows_meta: list[dict[str, Any]], path: str) -> dict[str, dict[str, Any]]:
    year = str(snapshot["year"])
    towns = snapshot["towns"]
    sc = snapshot["scopes"]
    spesa_rows, service_rows = [], []
    for base in rows_meta:
        t = towns[base["code"]]
        gap = spending_gap(t["spesaStorica"], t["spesaStandard"])
        common = {"town": base["town"], "code": base["code"], "slug": base["slug"], "normalized": None}
        spesa_rows.append({**common, "value": gap, "formatted": signed(gap), "series": {"years": [int(year)], "values": [gap]}, "benchmarkValue": gap})
        g = t["serviceGapPct"]
        service_rows.append({**common, "value": g, "formatted": signed(g), "series": {"years": [int(year)], "values": [g]}, "benchmarkValue": g})
    tot_s = sum(towns[c]["spesaStorica"] for c in TOWNS)
    tot_f = sum(towns[c]["spesaStandard"] for c in TOWNS)
    pop = sum(towns[c]["population"] for c in TOWNS)
    service_agg = sum(towns[c]["serviceGapPct"] * towns[c]["spesaStandard"] for c in TOWNS) / tot_f
    bench_note = ("Toscana: {t} Comuni valutabili; Italia: {i} Comuni valutabili delle regioni a statuto ordinario "
                  "(i fabbisogni standard non si calcolano per i Comuni delle regioni a statuto speciale).")
    note = bench_note.format(t=sc["tuscany"]["evaluable"], i=sc["italy"]["evaluable"])
    period = f"annualità {year} di OpenCivitas"
    source = "OpenCivitas — Fabbisogni standard dei Comuni (SOSE, MEF)"
    caveat_common = ("Il fabbisogno standard è una stima del Ministero dell'Economia e di SOSE, non un obiettivo di bilancio. "
                     "Riguarda le funzioni fondamentali (amministrazione, polizia locale, istruzione, viabilità e territorio, "
                     "ambiente e rifiuti, sociale, asili nido, trasporto pubblico) e usa i residenti: nei Comuni turistici "
                     "una parte della spesa e dei servizi serve presenze che i residenti non misurano. ")
    spending = {
        "meta": {
            "key": SPENDING, "theme": "bilanci", "label": "Spesa effettiva rispetto al fabbisogno standard",
            "shortLabel": "Spesa vs fabbisogno standard",
            "description": (f"Di quanto la spesa storica del Comune per le funzioni fondamentali supera (+) o resta sotto (−) "
                            f"la spesa standard stimata per un Comune con le stesse caratteristiche ({period})."),
            "unit": "percent", "year": year, "source": source, "polarity": "neutral",
            "benchmark": {"year": year, "tuscany": spending_gap(sc["tuscany"]["spesaStorica"], sc["tuscany"]["spesaStandard"]),
                          "italy": spending_gap(sc["italy"]["spesaStorica"], sc["italy"]["spesaStandard"]),
                          "source": source, "url": snapshot["dataUrl"], "sourceSnapshot": path,
                          "note": note + " Scostamento calcolato sui totali di spesa storica e spesa standard."},
            "sourceMeta": {"snapshot": path, "note": "Valori dei sette Comuni riconciliati con la sonda del file OpenCivitas."},
        },
        "sourceUrl": snapshot["sourceUrl"],
        "rows": spesa_rows,
        "aggregate": {"value": spending_gap(tot_s, tot_f), "label": "Versilia sui totali",
                      "note": (f"Spesa storica dei sette Comuni {euro(tot_s)} ({euro(tot_s / pop)} per residente) "
                               f"contro una spesa standard di {euro(tot_f)} ({euro(tot_f / pop)} per residente).")},
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali",
            "formula": "(spesa storica / spesa standard − 1) × 100, sul totale delle funzioni fondamentali; aggregati sui totali in euro.",
            "caveat": caveat_common + ("Spendere più dello standard non è di per sé uno spreco: può voler dire più servizi, "
                                       "costi più alti o fattori che il modello non coglie. Va letto insieme allo scostamento dei servizi."),
            "coverage": f"7/7 ({period})",
        },
    }
    service = {
        "meta": {
            "key": SERVICE, "theme": "bilanci", "label": "Servizi svolti rispetto al livello standard",
            "shortLabel": "Servizi vs livello standard",
            "description": (f"Di quanto i servizi svolti dal Comune nelle funzioni fondamentali superano (+) o restano sotto (−) "
                            f"il livello standard stimato per un Comune con le stesse caratteristiche ({period})."),
            "unit": "percent", "year": year, "source": source, "polarity": "neutral",
            "benchmark": {"year": year,
                          "tuscany": sc["tuscany"]["serviceGapWeightedSum"] / sc["tuscany"]["spesaStandard"],
                          "italy": sc["italy"]["serviceGapWeightedSum"] / sc["italy"]["spesaStandard"],
                          "source": source, "url": snapshot["dataUrl"], "sourceSnapshot": path,
                          "note": note + " Media degli scostamenti comunali ponderata sulla spesa standard."},
            "sourceMeta": {"snapshot": path, "note": "Scostamento pubblicato da OpenCivitas (DIFF_OUT_PERC_TOT), non ricalcolato."},
        },
        "sourceUrl": snapshot["sourceUrl"],
        "rows": service_rows,
        "aggregate": {"value": service_agg, "label": "Versilia ponderata",
                      "note": "Media dei sette scostamenti ponderata sulla spesa standard di ciascun Comune."},
        "normalizedAggregate": None,
        "method": {
            "type": "Dato ufficiale; aggregati Osservatorio",
            "formula": ("Scostamento percentuale dei servizi svolti dal livello standard, come pubblicato da OpenCivitas; "
                        "aggregati come media ponderata sulla spesa standard."),
            "caveat": caveat_common + ("Lo scostamento misura la quantità di servizi rilevata dai questionari SOSE, non la loro qualità "
                                       "né la soddisfazione dei cittadini."),
            "coverage": f"7/7 ({period})",
        },
    }
    return {SPENDING: spending, SERVICE: service}
