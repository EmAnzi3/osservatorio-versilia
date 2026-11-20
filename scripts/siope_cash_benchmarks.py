#!/usr/bin/env python3
"""Confronto Toscana per incassi e saldo di cassa SIOPE per residente (anno 2025).

Stessa regola dei valori comunali pubblicati (`siope-history-v1.6.0.json`): incassi e pagamenti
complessivi cumulati a dicembre dei Comuni (ente CO) dai dump SIOPE regionali di OpenBDAP, divisi
per i residenti al 1° gennaio dell'anno dopo (Istat POSAS). Il confronto aggrega i Comuni toscani
presenti in entrambi i flussi: somma dei numeratori / somma dei loro residenti, pubblicato solo se
coprono almeno il 90% dei residenti toscani (regola già usata per i rendiconti). I sette Comuni
ricalcolati devono coincidere con i valori pubblicati. Italia non calcolata: OpenBDAP pubblica il
flusso per regione e il nazionale richiederebbe tutti i dump regionali.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import zipfile
from datetime import date
from typing import Any, Callable

SNAPSHOT = "data/source-snapshots/siope-cash-benchmark-{year}.json"
POSAS_URL = "https://demo.istat.it/data/posas/POSAS_{year}_it_Comuni.zip"
METRICS = ("cashReceiptsPerResident", "cashBalancePerResident")
TUSCANY = ("045", "046", "047", "048", "049", "050", "051", "052", "053", "100")
MIN_COVERAGE = 0.90


class CashBenchmarkError(RuntimeError):
    pass


def posas_totals(raw: bytes) -> dict[str, int]:
    """Comune toscano → residenti totali (riga età 999 del file POSAS)."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))]
        if len(names) != 1:
            raise CashBenchmarkError(f"POSAS: archivio inatteso {names}")
        text = z.read(names[0]).decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    head = next(i for i, r in enumerate(rows[:5]) if any(c.strip().lower() == "codice comune" for c in r))
    header = [c.strip().lower() for c in rows[head]]
    code_i, age_i = header.index("codice comune"), next(i for i, h in enumerate(header) if h.startswith("et"))
    total_i = [i for i, h in enumerate(header) if "totale" in h and "maschi" not in h and "femmine" not in h]
    if len(total_i) != 1:
        raise CashBenchmarkError(f"POSAS: colonna totale {header}")
    out = {}
    for r in rows[head + 1:]:
        if len(r) <= max(code_i, age_i, total_i[0]):
            continue
        code = re.sub(r"\D", "", r[code_i]).zfill(6)
        if code.startswith(TUSCANY) and re.sub(r"\D", "", r[age_i]) == "999":
            if code in out:
                raise CashBenchmarkError(f"POSAS: totale duplicato {code}")
            out[code] = int(r[total_i[0]].strip())
    if not 260 <= len(out) <= 290:
        raise CashBenchmarkError(f"POSAS: {len(out)} Comuni toscani")
    return out


def build_snapshot(year: int, fetcher: Callable[[str], bytes], parser: Callable[[bytes, str], tuple[dict, dict]],
                   urls: dict[str, str], published: dict[str, dict[str, float]], residents_published: dict[str, float]) -> dict[str, Any]:
    """`parser`: dump → ({codice: {total, population, …}}, audit); `published`: metrica → {codice: valore};
    `residents_published`: codice → residenti usati per il valore comunale."""
    blobs = {k: fetcher(u) for k, u in urls.items()}
    entrata, ea = parser(blobs["entrata"], "entrata")
    spesa, sa = parser(blobs["spesa"], "spesa")
    posas_raw = fetcher(POSAS_URL.format(year=year + 1))
    residents = posas_totals(posas_raw)
    for code, value in residents_published.items():
        if residents.get(code) != value:
            raise CashBenchmarkError(f"{code}: residenti POSAS {residents.get(code)} ≠ denominatore pubblicato {value}")
    filed = sorted(c for c in residents if c in entrata and c in spesa)
    unknown = sorted(c for c in set(entrata) | set(spesa) if c not in residents)
    pop_all = sum(residents.values())
    pop_cov = sum(residents[c] for c in filed)
    receipts = sum(entrata[c]["total"] for c in filed)
    payments = sum(spesa[c]["total"] for c in filed)
    blocked: dict[str, list[str]] = {}
    for metric, towns in published.items():
        for code, value in towns.items():
            if code not in entrata or code not in spesa:
                blocked.setdefault(metric, []).append(f"{code}: righe SIOPE assenti")
                continue
            n = entrata[code]["total"] if metric == "cashReceiptsPerResident" else entrata[code]["total"] - spesa[code]["total"]
            live = n / residents[code]
            if not math.isclose(live, value, rel_tol=0, abs_tol=1e-6):
                blocked.setdefault(metric, []).append(f"{code}: fonte {live} ≠ pubblicato {value}")
    share = pop_cov / pop_all
    coverage = {"municipalities": len(filed), "municipalitiesTotal": len(residents), "populationCovered": pop_cov,
                "populationTotal": pop_all, "populationShare": share}
    benchmarks = {}
    for metric in METRICS:
        numerator = receipts if metric == "cashReceiptsPerResident" else receipts - payments
        entry = dict(coverage)
        if metric in blocked:
            entry.update(value=None, reason="riconciliazione 7/7 non superata: " + "; ".join(blocked[metric]))
        elif share < MIN_COVERAGE:
            entry.update(value=None, reason=f"copertura {share:.1%} sotto la soglia del {MIN_COVERAGE:.0%}")
        else:
            entry.update(value=numerator / pop_cov, numerator=numerator, denominator=pop_cov)
        benchmarks[metric] = {"tuscany": entry, "italy": {"value": None, "reason": "flusso SIOPE pubblicato per regione: aggregato nazionale non calcolato"}}
    return {
        "schemaVersion": 1, "version": f"siope-cash-benchmark-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Ragioneria Generale dello Stato — OpenBDAP/SIOPE · Istat (POSAS)", "year": year,
        "rule": ("Comuni toscani presenti nei flussi SIOPE di entrata e di spesa (dicembre, cumulato): somma degli incassi (o degli "
                 "incassi meno i pagamenti) / somma dei loro residenti al 1° gennaio dell'anno dopo. Pubblicato solo con almeno il 90% "
                 "dei residenti coperti; copertura dichiarata."),
        "minCoverage": MIN_COVERAGE,
        "sources": {k: {"url": urls[k], "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)} for k, b in blobs.items()}
                   | {"posas": {"url": POSAS_URL.format(year=year + 1), "sha256": hashlib.sha256(posas_raw).hexdigest(), "date": f"{year + 1}-01-01"}},
        "audit": {"entrata": ea, "spesa": sa, "unknownCodes": unknown},
        "towns": {c: {"receipts": entrata[c]["total"], "payments": spesa[c]["total"], "residents": residents[c]} for c in residents_published if c in entrata and c in spesa},
        "benchmarks": benchmarks, "blocked": blocked,
        "qualityGate": {"status": "PASS", "publicReconciliation": f"{len(METRICS) - len(blocked)} indicatori × 7/7"},
    }
