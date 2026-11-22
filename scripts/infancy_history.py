#!/usr/bin/env python3
"""Serie della ricettività potenziale dei servizi per la prima infanzia nei sette Comuni.

Stessa regola del valore pubblicato (anno educativo 2024/25): «Totale Ricettività potenziale» /
«Totale 3-36 mesi» × 100 dalle righe comunali del dataset regionale «Servizi educativi per la prima
infanzia» (dati.toscana.it), un file per anno educativo. Celle vuote o non numeriche non diventano
zero: l'anno resta fuori e la serie si ferma lì (deve essere continua fino all'anno corrente).
L'anno corrente deve coincidere con i componenti pubblicati (posti e bambini).
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from datetime import date
from typing import Any, Callable

DATASET = "https://dati.toscana.it/dataset/serviziprimainfanzia"
_R = "https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/"
FILES = {
    2014: _R + "9393f775-d89f-41be-87bf-4833bef66b8e/download/toscana_totale14-15_rev.csv",
    2015: _R + "e1a62222-51b0-48a2-aeae-29b6a502aa88/download/toscana2015_16_rev.csv",
    2016: _R + "9a78823a-f2a9-47cb-a194-57d063af4f5f/download/toscana2016_17_rev.csv",
    2017: _R + "f4b3dd14-e0af-4243-97a0-e95f6d048329/download/opendata_2017_18_rev.csv",
    2018: _R + "52b5b87e-2b7c-400e-945a-79c993471f77/download/opendata-2018_19.csv",
    2019: _R + "241c3a25-4c2e-4a38-a063-d1870383fa6b/download/opendata-2019_20_rev.csv",
    2020: _R + "b887af86-19f0-4b5b-8948-c92dfb85b001/download/opendata-_-da-pubblicare-20-21.csv",
    2021: _R + "1d5be3a3-2de7-4530-8edf-27c273c14a31/download/opendata-_-da-pubblicare-21-22.csv",
    2022: _R + "567dfada-eab6-45a8-9677-02462b9e86cc/download/opendata-_-da-pubblicare-22-23.csv",
    2023: _R + "ec21720f-42aa-4d13-89e5-23464bb295a1/download/opendata-_-da-pubblicare-23-24.csv",
    2024: _R + "01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv",
}
SNAPSHOT = "data/source-snapshots/toscana-prima-infanzia-serie.json"
METRIC = "earlyChildhoodPotentialCapacityRate"
TOWNS = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")


class InfancyError(RuntimeError):
    pass


class YearUnusable(InfancyError):
    """Il file dell'anno non permette di ricostruire i sette Comuni con la stessa regola."""


def label(start: int) -> str:
    return f"{start}/{(start + 1) % 100:02d}"


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.lower()).strip()


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise YearUnusable("codifica non riconosciuta")


def count(raw: Any, what: str) -> int:
    text = str(raw or "").strip().replace(".", "")
    if not re.fullmatch(r"\d+", text):
        raise YearUnusable(f"{what}: valore {raw!r}")
    return int(text)


def blank_or_zero(value: Any) -> bool:
    text = str(value or "").strip()
    return text == "" or re.fullmatch(r"0+", text) is not None


def no_services(row: dict[str, str], services_h: list[str], capacity_cols: list[str]) -> bool:
    """Vero solo se la riga dichiara che il Comune non ha servizi: «Totale servizi» presente e vuoto o zero,
    e tutte le colonne di ricettività vuote o zero. Ogni altro vuoto resta un dato mancante."""
    return len(services_h) == 1 and blank_or_zero(row.get(services_h[0])) and bool(capacity_cols) and all(blank_or_zero(row.get(h)) for h in capacity_cols)


def year_components(raw: bytes, start: int) -> dict[str, dict[str, int]]:
    text = decode(raw)
    if "<html" in text[:500].lower():
        raise YearUnusable("risposta HTML invece di CSV")
    try:
        delimiter = csv.Sniffer().sniff(text[:8000], delimiters=";,\t").delimiter
    except csv.Error:
        delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    def col(pred, what):
        found = [h for h in headers if pred(norm(h))]
        if len(found) != 1:
            raise YearUnusable(f"colonna {what}: {found or 'assente'}")
        return found[0]
    code_h = col(lambda h: h in ("codice istat", "cod istat", "codice istat comune"), "codice Istat")
    cap_h = col(lambda h: "ricettivita potenziale" in h and h.startswith("totale"), "ricettività potenziale")
    # «Totale 3-36 mesi» dal 2024/25, «Popolazione 3-36 mesi» negli anni precedenti: stessa grandezza (residenti 3–36 mesi).
    kids_h = col(lambda h: "3-36" in h.replace(" ", "") and h.startswith(("totale", "popolazione")) and "ricettivita" not in h, "bambini 3-36 mesi")
    year_h = next((h for h in headers if norm(h) == "anno educativo"), None)
    services_h = [h for h in headers if norm(h) == "totale servizi"]
    capacity_cols = [h for h in headers if "ricettivita" in norm(h)]
    out: dict[str, dict[str, int]] = {}
    no_service_towns: list[str] = []
    for row in reader:
        code = re.sub(r"\D", "", str(row.get(code_h) or "")).zfill(6) if str(row.get(code_h) or "").strip() else ""
        if code not in TOWNS:
            continue
        if year_h and norm(row.get(year_h)).replace("/", "-") not in (f"{start}-{(start + 1) % 100:02d}", f"{start}-{start + 1}"):
            raise YearUnusable(f"{code}: anno educativo {row.get(year_h)!r}")
        if code in out:
            raise YearUnusable(f"{code}: riga duplicata")
        kids = count(row.get(kids_h), f"{code} bambini")
        if not str(row.get(cap_h) or "").strip() and no_services(row, services_h, capacity_cols):
            # Comune senza alcun servizio (totale servizi e tutte le ricettività vuoti o zero): posti zero, dichiarato.
            cap = 0
            no_service_towns.append(code)
        else:
            cap = count(row.get(cap_h), f"{code} posti")
        if kids <= 0:
            raise YearUnusable(f"{code}: denominatore nullo")
        out[code] = {"potentialCapacity": cap, "children3to36Months": kids}
    if set(out) != set(TOWNS):
        raise YearUnusable(f"Comuni trovati {sorted(out)}")
    for code in no_service_towns:
        out[code]["noServices"] = True
    return out


def build_snapshot(fetcher: Callable[[str], bytes], current: dict[str, dict[str, int]], last: int = 2024) -> dict[str, Any]:
    """`current`: codice → {potentialCapacity, children3to36Months} pubblicati per l'anno `last`."""
    years: dict[int, dict[str, Any]] = {}
    stopped = None
    for start in range(last, min(FILES) - 1, -1):
        raw = fetcher(FILES[start])
        try:
            towns = year_components(raw, start)
        except YearUnusable as why:
            if start == last:
                raise InfancyError(f"anno corrente {label(last)} non leggibile: {why}")
            stopped = {"schoolYear": label(start), "reason": str(why)}
            break
        years[start] = {"url": FILES[start], "sha256": hashlib.sha256(raw).hexdigest(), "towns": towns}
    for code, pub in current.items():
        got = years[last]["towns"][code]
        if {k: got[k] for k in ("potentialCapacity", "children3to36Months")} != {"potentialCapacity": pub["potentialCapacity"], "children3to36Months": pub["children3to36Months"]}:
            raise InfancyError(f"{code} {label(last)}: {got} ≠ pubblicato {pub}")
    starts = sorted(years)
    return {
        "schemaVersion": 1, "version": f"toscana-prima-infanzia-serie-{label(starts[0]).replace('/', '-')}-{label(last).replace('/', '-')}-v1",
        "retrieved": date.today().isoformat(), "publisher": "Regione Toscana — Servizi educativi per la prima infanzia", "sourceUrl": DATASET,
        "schoolYears": [label(s) for s in starts],
        "rule": "Totale Ricettività potenziale / Totale 3-36 mesi × 100 dalle righe comunali di ciascun anno educativo; celle vuote mai trasformate in zero.",
        "archives": {label(s): {k: v for k, v in years[s].items() if k != "towns"} for s in starts},
        "towns": {c: {label(s): years[s]["towns"][c] for s in starts} for c in TOWNS},
        "series": {c: [years[s]["towns"][c]["potentialCapacity"] / years[s]["towns"][c]["children3to36Months"] * 100 for s in starts] for c in TOWNS},
        "stoppedAt": stopped,
        "noServiceCells": {label(s): sorted(c for c, v in years[s]["towns"].items() if v.get("noServices")) for s in starts if any(v.get("noServices") for v in years[s]["towns"].values())},
        "qualityGate": {"status": "PASS", "note": f"a.s. {label(last)} identico ai componenti pubblicati per i 7 Comuni."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["schoolYears"]
    if years[-1] != metric["meta"]["year"]:
        raise InfancyError(f"serie fino al {years[-1]}, valore pubblicato {metric['meta']['year']}")
    for row in metric["rows"]:
        values = snapshot["series"][row["code"]]
        t = snapshot["towns"][row["code"]][years[-1]]
        if values[-1] != row["value"] or t["potentialCapacity"] != row["potentialCapacity"] or t["children3to36Months"] != row["children3to36Months"]:
            raise InfancyError(f"{row['town']}: serie {values[-1]} ≠ valore {row['value']}")
        row["series"] = {"years": list(years), "values": list(values)}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    note = (f" Serie dall'anno educativo {years[0]} al {years[-1]}, stessa regola su ciascun file regionale; dove il file lascia "
            "vuoti i posti di un Comune senza alcun servizio (totale servizi e ricettività vuoti), i posti valgono zero.")
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
