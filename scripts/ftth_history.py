#!/usr/bin/env python3
"""Serie storica dei quattro indicatori FTTH (AGCOM Broadband Map, CSV comunali trimestrali).

Stessa regola dei valori pubblicati (`update_source_data.py agcom-ftth`): per ogni edizione «Consistenze
rilevate al …» del catalogo `report.js` si legge il CSV comunale con `audit_agcom_primary.parse_csv`;
coperture DESI ed entro 20 m sono le percentuali AGCOM, le famiglie raggiunte sono `famiglie_ftth` e le
non raggiunte `famiglie_residenti − famiglie_ftth`. Si risale dall'edizione pubblicata finché il CSV è
leggibile, la base delle famiglie residenti AGCOM è quella dell'edizione pubblicata (un cambio di base,
come tra dicembre 2025 e marzo 2026, rende le edizioni non confrontabili) e i Comuni con il dato sono gli
stessi dell'edizione pubblicata (per le coperture 7/7; per i conteggi Forte dei Marmi resta n.d. come nel
valore pubblicato). L'edizione pubblicata deve coincidere
con i valori del catalogo.
"""
from __future__ import annotations

import hashlib
import math
import re
from datetime import date
from typing import Any, Callable

SNAPSHOT = "data/source-snapshots/agcom-ftth-serie.json"
METRIC = "ftthCoverageDesi, ftthCoverage20m, ftthReachedHouseholds, ftthUnreachedHouseholds"
PCT = {"ftthCoverageDesi": "copertura_ftth_desi_pct", "ftthCoverage20m": "copertura_ftth_20m_pct"}
COUNTS = ("ftthReachedHouseholds", "ftthUnreachedHouseholds")
TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
         "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}


class FtthHistoryError(RuntimeError):
    pass


def editions(text: str) -> list[tuple[str, date]]:
    """(URL del CSV comunale, data di riferimento) per ogni edizione del catalogo, dalla più recente.
    Accetta date con giorno e mese a una o due cifre (il catalogo usa entrambe le scritture)."""
    out = []
    for section in re.split(r"<h2>", text)[1:]:
        m = re.match(r"\s*Consistenze rilevate al (\d{1,2})/(\d{1,2})/(\d{4})", section)
        if not m:
            continue
        link = re.search(r'Dati Comunali\s*<a href="([^"]+)"[^>]*>\s*<u>\s*CSV\s*</u>', section)
        if link:
            out.append((link.group(1), date(int(m.group(3)), int(m.group(2)), int(m.group(1)))))
    return sorted(out, key=lambda item: item[1], reverse=True)


def values(record: dict[str, Any]) -> dict[str, float | None]:
    reached, households = record.get("famiglie_ftth"), record.get("famiglie_residenti")
    out: dict[str, float | None] = {k: record.get(f) for k, f in PCT.items()}
    out["ftthReachedHouseholds"] = None if reached is None else float(reached)
    out["ftthUnreachedHouseholds"] = None if reached is None or households is None else float(households - reached)
    return out


def build_snapshot(fetch: Callable[[str], bytes], parse: Callable[[bytes], dict], metrics: dict[str, Any], published: date) -> dict[str, Any]:
    """`parse`: lettore del CSV comunale AGCOM (`audit_agcom_primary.parse_csv`)."""
    from audit_agcom_primary import REPORT_SCRIPT_URL
    catalogue = fetch(REPORT_SCRIPT_URL).decode("utf-8-sig")
    found = [e for e in editions(catalogue) if e[1] <= published]
    if not found or found[0][1] != published:
        raise FtthHistoryError(f"edizione pubblicata {published} assente dal catalogo")
    pub = {k: {r["code"]: r["value"] for r in metrics[k]["rows"]} for k in (*PCT, *COUNTS)}
    pattern = {k: {c for c, v in pub[k].items() if v is not None} for k in pub}
    taken: dict[str, dict[str, Any]] = {}
    sources: dict[str, Any] = {}
    stop = None
    for url, when in found:
        try:
            body = fetch(url)
            rows = parse(body)
        except Exception as error:  # noqa: BLE001 - CSV non leggibile con la regola corrente: la serie si ferma
            if when == published:
                raise FtthHistoryError(f"edizione pubblicata non leggibile: {error}") from error
            stop = f"{when.isoformat()}: CSV non leggibile ({str(error)[:160]})"
            break
        missing = [TOWNS[c] for c in TOWNS if c not in rows]
        if missing:
            stop = f"{when.isoformat()}: Comuni assenti {missing}"
            break
        base = {c: rows[c].get("famiglie_residenti") for c in TOWNS}
        if when == published:
            base_published = base
        elif base != base_published:
            changed = sorted(TOWNS[c] for c in TOWNS if base[c] != base_published[c])
            stop = f"{when.isoformat()}: famiglie residenti AGCOM diverse dall'edizione pubblicata ({changed})"
            break
        taken[when.isoformat()] = {c: values(rows[c]) for c in TOWNS}
        sources[when.isoformat()] = {"url": url, "sha256": hashlib.sha256(body).hexdigest()}
    first = published.isoformat()
    for key, by_code in pub.items():
        for code, value in by_code.items():
            live = taken[first][code][key]
            if (value is None) != (live is None) or (value is not None and not math.isclose(live, value, rel_tol=0, abs_tol=1e-9)):
                raise FtthHistoryError(f"{key} {TOWNS[code]} {first}: fonte {live} ≠ pubblicato {value}")
    series: dict[str, Any] = {}
    for key in pub:
        dates = []
        for when in taken:  # dalla più recente
            available = {c for c, v in taken[when].items() if v[key] is not None}
            if available != pattern[key]:
                series.setdefault("stoppedAt", {})[key] = f"{when}: Comuni con il dato {sorted(TOWNS[c] for c in available)}"
                break
            dates.append(when)
        series[key] = sorted(dates)
    return {
        "schemaVersion": 1, "version": f"agcom-ftth-serie-{first}-v1", "retrieved": date.today().isoformat(),
        "publisher": "AGCOM — Broadband Map, reportistica comunale", "catalogue": REPORT_SCRIPT_URL,
        "rule": ("Edizioni trimestrali consecutive fino a quella pubblicata, CSV comunale letto con la regola corrente, stessa base "
                 "delle famiglie residenti AGCOM e stessi "
                 "Comuni con il dato dell'edizione pubblicata; edizione pubblicata identica ai valori del catalogo."),
        "stoppedAt": stop, "seriesStoppedAt": series.pop("stoppedAt", {}), "dates": series, "sources": sources,
        "towns": {TOWNS[c]: {when: taken[when][c] for when in taken} for c in TOWNS},
        "years": sorted(taken),
        "qualityGate": {"status": "PASS", "note": f"Edizione {first} identica ai valori pubblicati dei quattro indicatori."},
    }


def apply(metrics: dict[str, Any], snapshot: dict[str, Any], path: str) -> None:
    for key in (*PCT, *COUNTS):
        dates = snapshot["dates"][key]
        if len(dates) < 2:
            continue
        m = metrics[key]
        for row in m["rows"]:
            vals = [snapshot["towns"][row["town"]][d][key] for d in dates]
            if any(v is None for v in vals):
                continue
            if not math.isclose(vals[-1], row["value"], rel_tol=0, abs_tol=1e-9):
                raise FtthHistoryError(f"{key} {row['town']}: serie ≠ valore pubblicato")
            row["series"] = {"years": list(dates), "values": vals}
        m["method"]["historyNote"] = (f"Serie trimestrale {dates[0]} – {dates[-1]} dalle edizioni della Broadband Map AGCOM (CSV comunali), "
                                      "stessa colonna e stessa regola del valore pubblicato.")
        m["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
