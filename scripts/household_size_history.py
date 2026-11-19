#!/usr/bin/env python3
"""Numero medio di componenti per famiglia: serie comunale Istat «A misura di Comune» (Famiglie).

Il workbook `3-Famiglie.xlsx` pubblica per ogni Comune, provincia e regione il numero
di famiglie al 31 dicembre (Tav. 1.x) e il numero medio di componenti (Tav. 4.x) per
più anni (oggi 2018–2023). Lo snapshot conserva le righe dei sette Comuni e i totali
di provincia e regione; da qui:

* serie comunale = valore pubblicato in Tav. 4.1;
* Versilia, Toscana e Italia = Σ (famiglie × componenti medi) / Σ famiglie, cioè
  componenti totali su famiglie totali (per la Toscana coincide con la riga regionale
  pubblicata, che resta il riscontro; l'Italia somma tutte le province).
Per il 2018 e il 2019 Istat pubblica famiglie stimate (valori non interi): restano tali.
"""
from __future__ import annotations

import hashlib
import io
import math
from datetime import date
from typing import Any

METRIC = "householdSize"
URL = "https://www.istat.it/storage/misura-comune/3-Famiglie.xlsx"
SNAPSHOT_PREFIX = "data/source-snapshots/istat-famiglie-serie-"
TOWNS = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")
SHEETS = {"families": ("Tav. 1.1 Comuni", "Tav. 1.2 Province e regioni"), "size": ("Tav. 4.1 Comuni", "Tav. 4.2 Province e regioni")}


class HouseholdError(RuntimeError):
    pass


def _table(ws) -> tuple[list[int], list[list[Any]]]:
    ws.reset_dimensions()
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    head = next((i for i, r in enumerate(rows) if r and r[0] == "Ripartizione"), None)
    if head is None:
        raise HouseholdError(f"{ws.title}: intestazione assente")
    years = [int(x) for x in rows[head] if isinstance(x, (int, float)) or (isinstance(x, str) and x.isdigit())]
    return years, [r for r in rows[head + 1:] if r and r[0]]


def build_snapshot(raw: bytes) -> dict[str, Any]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    out: dict[str, Any] = {}
    years_seen = set()
    for kind, (town_sheet, area_sheet) in SHEETS.items():
        years, rows = _table(wb[town_sheet])
        years_seen.add(tuple(years))
        n = len(years)
        towns = {}
        for r in rows:
            code = str(r[6]).zfill(6)
            if code in TOWNS:
                values = r[7:7 + n]
                if any(not isinstance(v, (int, float)) or not v > 0 for v in values):
                    raise HouseholdError(f"{town_sheet} {code}: valori non numerici {values}")
                towns[code] = {"town": r[5], "values": [float(v) for v in values]}
        if set(towns) != set(TOWNS):
            raise HouseholdError(f"{town_sheet}: Comuni trovati {sorted(towns)}")
        years2, arows = _table(wb[area_sheet])
        if years2 != years:
            raise HouseholdError(f"{area_sheet}: anni {years2} ≠ {years}")
        provinces, tuscany_total = [], None
        for r in arows:
            values = r[4:4 + n]
            if any(not isinstance(v, (int, float)) for v in values):
                continue
            entry = {"region": str(r[1]).zfill(2), "area": r[3], "values": [float(v) for v in values]}
            if str(r[3]).strip().upper() == "TOTALE":
                if entry["region"] == "09":
                    tuscany_total = entry
            else:
                provinces.append(entry)
        if tuscany_total is None or not 100 <= len(provinces) <= 115:
            raise HouseholdError(f"{area_sheet}: {len(provinces)} province, totale Toscana {tuscany_total is not None}")
        out[kind] = {"years": years, "towns": towns, "provinces": provinces, "tuscanyTotal": tuscany_total}
    if len(years_seen) != 1:
        raise HouseholdError(f"anni diversi fra le tavole: {years_seen}")
    years = out["size"]["years"]

    def pooled(pairs: list[tuple[list[float], list[float]]]) -> list[dict[str, float]]:
        res = []
        for j in range(len(years)):
            fam = math.fsum(f[j] for f, _ in pairs)
            members = math.fsum(f[j] * s[j] for f, s in pairs)
            res.append({"families": fam, "members": members, "value": members / fam})
        return res

    def area_pairs(pred) -> list[tuple[list[float], list[float]]]:
        fam = [p for p in out["families"]["provinces"] if pred(p)]
        size = [p for p in out["size"]["provinces"] if pred(p)]
        if [(p["region"], p["area"]) for p in fam] != [(p["region"], p["area"]) for p in size]:
            raise HouseholdError("province diverse fra Tav. 1.2 e Tav. 4.2")
        return [(f["values"], s["values"]) for f, s in zip(fam, size)]

    tuscany = pooled(area_pairs(lambda p: p["region"] == "09"))
    for j, t in enumerate(tuscany):
        if not math.isclose(t["value"], out["size"]["tuscanyTotal"]["values"][j], rel_tol=0, abs_tol=5e-4):
            raise HouseholdError(f"Toscana {years[j]}: {t['value']} ≠ riga pubblicata {out['size']['tuscanyTotal']['values'][j]}")
    italy = pooled(area_pairs(lambda p: True))
    versilia = pooled([(out["families"]["towns"][c]["values"], out["size"]["towns"][c]["values"]) for c in TOWNS])
    return {
        "schemaVersion": 1, "version": f"istat-famiglie-serie-{years[-1]}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Istat — A misura di Comune · Famiglie", "sourceUrl": URL, "years": years,
        "workbook": {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
        "towns": {c: {"town": out["size"]["towns"][c]["town"], "size": out["size"]["towns"][c]["values"],
                      "families": out["families"]["towns"][c]["values"]} for c in TOWNS},
        "scopes": {"versilia": versilia, "tuscany": tuscany, "italy": italy},
        "tuscanyPublishedRow": out["size"]["tuscanyTotal"]["values"],
        "provinceCount": len(out["size"]["provinces"]),
        "rule": "Componenti medi pubblicati per Comune; aggregati = Σ (famiglie × componenti medi) / Σ famiglie.",
        "qualityGate": {"status": "PASS", "note": "Toscana ricalcolata dalle province uguale alla riga regionale pubblicata in ogni anno."},
    }


def fmt(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def apply(metric: dict[str, Any], snapshot: dict[str, Any], path: str) -> None:
    years = snapshot["years"]
    last = str(years[-1])
    for row in metric["rows"]:
        t = snapshot["towns"][row["code"]]
        if t["town"] != row["town"]:
            raise HouseholdError(f"{row['code']}: {t['town']} ≠ {row['town']}")
        row.update(value=t["size"][-1], formatted=fmt(t["size"][-1]), benchmarkValue=t["size"][-1],
                   series={"years": list(years), "values": list(t["size"])})
    sc = snapshot["scopes"]
    metric["aggregate"] = {"value": sc["versilia"][-1]["value"], "label": "Valore Versilia",
                           "note": "Componenti totali dei sette Comuni divisi per le famiglie totali."}
    metric["meta"].update(year=last, benchmark={
        "year": last, "tuscany": sc["tuscany"][-1]["value"], "italy": sc["italy"][-1]["value"],
        "source": snapshot["publisher"], "url": snapshot["sourceUrl"], "sourceSnapshot": path,
        "note": ("Toscana e Italia: componenti totali divisi per famiglie totali, sommando le province del workbook "
                 "(per la Toscana uguale alla riga regionale pubblicata).")})
    metric["meta"]["sourceMeta"] = {"snapshot": path, "note": f"Serie comunale Istat {years[0]}–{last}, workbook «A misura di Comune · Famiglie»."}
    metric["meta"]["source"] = snapshot["publisher"]
    metric["method"].update(
        type="Dato ufficiale",
        formula="Numero medio di componenti per famiglia pubblicato da Istat per Comune; Versilia, Toscana e Italia come componenti totali / famiglie totali.",
        caveat=(f"Famiglie al 31 dicembre. Per il {years[0]} e il {years[1]} Istat pubblica un numero di famiglie stimato. "
                "Indicatore di struttura delle famiglie, non di condizione economica."),
        coverage=f"7/7 ({years[0]}–{last})")
