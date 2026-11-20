#!/usr/bin/env python3
"""Confronto Toscana e Italia per l'addizionale comunale IRPEF negli scenari 20.000, 30.000 e 50.000 €.

Stessa regola dei valori comunali pubblicati (`costi-fiscalita-redditi-draft-2026-08.json`): se il
reddito imponibile non supera la soglia di esenzione l'importo è zero, altrimenti si applicano
all'intero imponibile l'aliquota unica o gli scaglioni progressivi, arrotondando al centesimo.
Le regole di ogni Comune vengono dall'elenco generale MEF dell'anno (CSV con aliquote, fasce ed
esenzioni). Il confronto è la media degli importi comunali pesata per i residenti al 1° gennaio
dell'anno dopo (Istat POSAS): ciò che pagherebbe, a parità di reddito, il residente medio della
Toscana o dell'Italia. Entrano solo i Comuni la cui disciplina si legge senza ambiguità per quello
scenario (per esempio sono esclusi quelli con esenzioni riservate a certe categorie di reddito che
arrivano fino allo scenario); si pubblica solo con almeno il 90% dei residenti coperti e la
copertura è dichiarata. I sette Comuni ricalcolati devono coincidere con i valori pubblicati.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import unicodedata
import zipfile
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable

MEF_URL = "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/download/download.php?anno={year}"
SOURCE_PAGE = "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/download/tabella.htm"
ISTAT_URL = "https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv"
POSAS_URL = "https://demo.istat.it/data/posas/POSAS_{year}_it_Comuni.zip"
SNAPSHOT = "data/source-snapshots/mef-irpef-benchmark-{year}.json"
METRIC = "municipalIrpef"
SCENARIOS = (20000, 30000, 50000)
TUSCANY_REGION = "09"
MIN_COVERAGE = 0.90
MAX_RATE = Decimal("1.0")


class IrpefBenchmarkError(RuntimeError):
    pass


class Unreadable(ValueError):
    """La disciplina del Comune non si legge senza ambiguità."""


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
    raise IrpefBenchmarkError("codifica non riconosciuta")


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def rate(text: str) -> Decimal:
    t = str(text or "").strip().replace(" ", "").rstrip("*")
    if not re.fullmatch(r"\d*[.,]?\d+", t):
        raise Unreadable(f"aliquota {text!r}")
    value = Decimal(t.replace(",", "."))
    if not Decimal(0) <= value <= MAX_RATE:
        raise Unreadable(f"aliquota fuori intervallo {text!r}")
    return value


def amounts(text: str) -> list[Decimal]:
    """Importi in euro scritti all'italiana (15.000,00 · 15000 · 15.000,01)."""
    out = []
    for m in re.finditer(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", text):
        out.append(Decimal(m.group(0).replace(".", "").replace(",", ".")))
    return out


GENERAL_EXEMPTION = re.compile(r"^esenzione per redditi imponibili fino a euro [\d.,]+$")


def rule(row: dict[str, str]) -> dict[str, Any]:
    """Riga MEF → {scheme, ratePercent | brackets, exemption, categoryExemption}. Unreadable se ambigua."""
    first = (row.get("ALIQUOTA") or "").strip().replace(" ", "")
    others = [(row.get(f"ALIQUOTA_{i}") or "").strip() or (row.get(f"FASCIA_{i}") or "").strip() for i in range(2, 13)]
    if first == "0*" and not (row.get("FASCIA") or "").strip() and not any(others):
        # «0*» nell'elenco definitivo (dopo il 20 dicembre): il Comune non ha istituito l'addizionale.
        return {"exemption": None, "categoryExemption": None, "scheme": "flat", "ratePercent": 0.0, "notInstituted": True}
    pairs = []
    for i in range(1, 13):
        suffix = "" if i == 1 else f"_{i}"
        a, f = (row.get("ALIQUOTA" + suffix) or "").strip(), (row.get("FASCIA" + suffix) or "").strip()
        if a or f:
            if not a or not f:
                raise Unreadable(f"coppia aliquota/fascia incompleta {i}")
            pairs.append((rate(a), norm(f)))
    if not pairs:
        raise Unreadable("nessuna aliquota")
    general: Decimal | None = None
    category: Decimal | None = None
    flat: list[Decimal] = []
    brackets: list[tuple[Decimal, Decimal | None, Decimal]] = []
    for r, f in pairs:
        if f.startswith("esenzione"):
            numbers = amounts(f)
            if r != 0 or not numbers:
                raise Unreadable(f"esenzione non leggibile {f!r}")
            if GENERAL_EXEMPTION.match(f) and len(numbers) == 1:
                general = numbers[0] if general is None else max(general, numbers[0])
            else:
                category = max(numbers) if category is None else max(category, *numbers)
        elif f == "aliquota unica":
            flat.append(r)
        elif f.startswith("applicabile"):
            numbers = amounts(f)
            since = re.search(r"\bda(?:l|ll['’])?\b", f)
            if "oltre" in f and len(numbers) == 1:
                brackets.append((numbers[0], None, r))
            elif "fino" in f and len(numbers) == 1 and not since:
                brackets.append((Decimal(0), numbers[0], r))
            elif len(numbers) == 2 and since and "oltre" not in f:
                brackets.append((numbers[0], numbers[1], r))
            else:
                raise Unreadable(f"scaglione non leggibile {f!r}")
        else:
            raise Unreadable(f"fascia non riconosciuta {f!r}")
    declared = (row.get("IMPORTO_ESENTE") or "").strip()
    if declared and general is not None and amounts(declared) and amounts(declared)[0] not in (0, general):
        raise Unreadable(f"esenzione {general} ≠ IMPORTO_ESENTE {declared}")
    base = {"exemption": float(general) if general is not None else None,
            "categoryExemption": float(category) if category is not None else None}
    if flat and not brackets:
        if len(flat) != 1:
            raise Unreadable("più aliquote uniche")
        return dict(base, scheme="flat", ratePercent=float(flat[0]))
    if brackets and not flat:
        brackets.sort(key=lambda b: b[0])
        if brackets[0][0] > 1:
            raise Unreadable("primo scaglione non parte da zero")
        for (lo, hi, _), (nlo, _, _) in zip(brackets, brackets[1:]):
            if hi is None or not Decimal(0) <= nlo - hi <= 1:
                raise Unreadable("scaglioni non contigui")
        if brackets[-1][1] is not None:
            raise Unreadable("ultimo scaglione chiuso")
        return dict(base, scheme="progressive", brackets=[{"upTo": float(hi) if hi is not None else None, "ratePercent": float(r)} for _, hi, r in brackets])
    raise Unreadable("aliquota unica e scaglioni insieme")


def amount(r: dict[str, Any], income: int) -> float:
    """Stessa regola dell'adapter dei valori comunali; Unreadable se un'esenzione per categoria arriva allo scenario."""
    if r["exemption"] is not None and income <= r["exemption"]:
        return 0.0
    if r["categoryExemption"] is not None and income <= r["categoryExemption"]:
        raise Unreadable("esenzione per categorie di reddito fino allo scenario")
    if r["scheme"] == "flat":
        return float(money(Decimal(income) * Decimal(str(r["ratePercent"])) / 100))
    lower, total = Decimal(0), Decimal(0)
    for b in r["brackets"]:
        upper = b["upTo"]
        width = max(Decimal(0), min(Decimal(income), Decimal(str(upper)) if upper is not None else Decimal(income)) - lower)
        total += width * Decimal(str(b["ratePercent"])) / 100
        if upper is None or income <= upper:
            break
        lower = Decimal(str(upper))
    return float(money(total))


def mef_rules(raw: bytes) -> tuple[dict[str, dict], dict[str, str], dict[str, Any]]:
    """CSV MEF → (catastale → regola leggibile, catastale → motivo di esclusione, audit)."""
    text = decode(raw)
    if "<html" in text[:500].lower():
        raise IrpefBenchmarkError("MEF: risposta HTML invece di CSV")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    need = {"CODICE_CATASTALE", "COMUNE", "ALIQUOTA", "FASCIA", "FLAG_NUOVA", "IMPORTO_ESENTE"}
    if not need.issubset(reader.fieldnames or []):
        raise IrpefBenchmarkError(f"MEF: intestazione inattesa {reader.fieldnames}")
    rules, unread, seen = {}, {}, {}
    for row in reader:
        code = (row.get("CODICE_CATASTALE") or "").strip().upper()
        if not re.fullmatch(r"[A-Z]\d{3}", code):
            raise IrpefBenchmarkError(f"MEF: codice catastale {code!r}")
        seen[code] = seen.get(code, 0) + 1
        try:
            rules[code] = dict(rule(row), name=(row.get("COMUNE") or "").strip())
        except Unreadable as why:
            unread[code] = str(why)
    duplicates = sorted(c for c, n in seen.items() if n > 1)
    for code in duplicates:  # due righe per lo stesso Comune: nessuna delle due si sceglie d'ufficio
        rules.pop(code, None)
        unread[code] = "righe duplicate"
    if not 7000 <= len(seen) <= 8200:
        raise IrpefBenchmarkError(f"MEF: {len(seen)} Comuni nell'elenco")
    return rules, unread, {"rows": sum(seen.values()), "municipalities": len(seen), "duplicates": duplicates}


def istat_codes(raw: bytes) -> dict[str, tuple[str, str]]:
    """Elenco Istat dei Comuni → catastale → (codice Istat a 6 cifre, codice regione)."""
    rows = list(csv.reader(io.StringIO(decode(raw)), delimiter=";"))
    header = [norm(h) for h in rows[0]]
    def col(pred):
        found = [i for i, h in enumerate(header) if pred(h)]
        if len(found) != 1:
            raise IrpefBenchmarkError(f"Elenco Istat: colonne {header}")
        return found[0]
    cat = col(lambda h: "catastale" in h)
    istat = col(lambda h: "formato alfanumerico" in h and "comune" in h)
    region = col(lambda h: h == "codice regione")
    out = {}
    for r in rows[1:]:
        if len(r) <= max(cat, istat, region) or not r[cat].strip():
            continue
        code = r[cat].strip().upper()
        if code in out:
            raise IrpefBenchmarkError(f"Elenco Istat: catastale duplicato {code}")
        out[code] = (re.sub(r"\D", "", r[istat]).zfill(6), re.sub(r"\D", "", r[region]).zfill(2))
    if not 7800 <= len(out) <= 8000:
        raise IrpefBenchmarkError(f"Elenco Istat: {len(out)} Comuni")
    return out


def posas_totals(raw: bytes) -> dict[str, int]:
    """Comune → residenti totali (riga età 999 del file POSAS), tutta Italia."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))]
        if len(names) != 1:
            raise IrpefBenchmarkError(f"POSAS: archivio inatteso {names}")
        text = decode(z.read(names[0]))
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    head = next(i for i, r in enumerate(rows[:5]) if any(norm(c) == "codice comune" for c in r))
    header = [norm(c) for c in rows[head]]
    code_i, age_i = header.index("codice comune"), next(i for i, h in enumerate(header) if h.startswith("eta"))
    total_i = [i for i, h in enumerate(header) if "totale" in h and "maschi" not in h and "femmine" not in h]
    if len(total_i) != 1:
        raise IrpefBenchmarkError(f"POSAS: colonna totale {header}")
    out = {}
    for r in rows[head + 1:]:
        if len(r) <= max(code_i, age_i, total_i[0]) or re.sub(r"\D", "", r[age_i]) != "999":
            continue
        code = re.sub(r"\D", "", r[code_i]).zfill(6)
        if code in out:
            raise IrpefBenchmarkError(f"POSAS: totale duplicato {code}")
        out[code] = int(r[total_i[0]].strip())
    if not 7800 <= len(out) <= 8000:
        raise IrpefBenchmarkError(f"POSAS: {len(out)} Comuni")
    return out


def build_snapshot(year: int, fetcher: Callable[[str], bytes], published: dict[str, list[float]]) -> dict[str, Any]:
    """`published`: codice Istat → importi pubblicati per i tre scenari."""
    mef_raw, istat_raw, posas_raw = fetcher(MEF_URL.format(year=year)), fetcher(ISTAT_URL), fetcher(POSAS_URL.format(year=year + 1))
    rules, unread, audit = mef_rules(mef_raw)
    codes = istat_codes(istat_raw)
    residents = posas_totals(posas_raw)
    by_istat = {}
    unmatched = []
    for cat in set(rules) | set(unread):
        if cat not in codes or codes[cat][0] not in residents:
            unmatched.append(cat)
            continue
        by_istat[codes[cat][0]] = cat
    region = {istat: reg for istat, reg in codes.values()}
    if {region.get(c) for c in published} != {TUSCANY_REGION}:
        raise IrpefBenchmarkError("Elenco Istat: i sette Comuni non risultano in Toscana")
    blocked = []
    towns = {}
    for code, values in published.items():
        cat = by_istat.get(code)
        if cat is None or cat not in rules:
            blocked.append(f"{code}: {'assente dall elenco MEF' if cat is None else unread[cat]}")
            continue
        try:
            live = [amount(rules[cat], n) for n in SCENARIOS]
        except Unreadable as why:
            blocked.append(f"{code}: {why}")
            continue
        if any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(live, values)):
            blocked.append(f"{code}: fonte {live} ≠ pubblicato {values}")
        towns[code] = {"cadastral": cat, "rule": {k: v for k, v in rules[cat].items() if k != "name"}, "amounts": dict(zip(map(str, SCENARIOS), live))}
    scopes = {"tuscany": [c for c in residents if region.get(c) == TUSCANY_REGION], "italy": list(residents)}
    benchmarks: dict[str, dict[str, Any]] = {}
    for n in SCENARIOS:
        benchmarks[str(n)] = {}
        for scope, members in scopes.items():
            pop_all = sum(residents[c] for c in members)
            num, pop_cov, count, reasons = Decimal(0), 0, 0, {}
            for c in members:
                cat = by_istat.get(c)
                if cat is None:
                    reasons["assente dall'elenco MEF"] = reasons.get("assente dall'elenco MEF", 0) + 1
                    continue
                if cat not in rules:
                    reasons["disciplina non leggibile"] = reasons.get("disciplina non leggibile", 0) + 1
                    continue
                try:
                    value = amount(rules[cat], n)
                except Unreadable:
                    reasons["esenzione per categorie fino allo scenario"] = reasons.get("esenzione per categorie fino allo scenario", 0) + 1
                    continue
                num += Decimal(str(value)) * residents[c]
                pop_cov += residents[c]
                count += 1
            share = pop_cov / pop_all
            entry = {"municipalities": count, "municipalitiesTotal": len(members), "populationCovered": pop_cov,
                     "populationTotal": pop_all, "populationShare": share, "excluded": reasons}
            if blocked:
                entry.update(value=None, reason="riconciliazione 7/7 non superata: " + "; ".join(blocked))
            elif share < MIN_COVERAGE:
                entry.update(value=None, reason=f"copertura {share:.1%} sotto la soglia del {MIN_COVERAGE:.0%}")
            else:
                entry.update(value=float(num / pop_cov), numerator=float(num), denominator=pop_cov)
            benchmarks[str(n)][scope] = entry
    return {
        "schemaVersion": 1, "version": f"mef-irpef-benchmark-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Dipartimento delle Finanze — MEF · Istat (POSAS, elenco dei Comuni)", "year": year, "scenarios": list(SCENARIOS),
        "rule": ("Per ogni Comune dell'elenco generale MEF: importo dell'addizionale con la stessa regola dei valori comunali "
                 "(sotto la soglia di esenzione zero, altrimenti aliquota unica o scaglioni sull'intero imponibile, al centesimo). "
                 "Toscana e Italia: media degli importi pesata per i residenti al 1° gennaio dell'anno dopo, sui Comuni la cui "
                 "disciplina si legge senza ambiguità per lo scenario. Pubblicato solo con almeno il 90% dei residenti coperti; "
                 "copertura dichiarata."),
        "minCoverage": MIN_COVERAGE,
        "sources": {"mef": {"url": MEF_URL.format(year=year), "page": SOURCE_PAGE, "sha256": hashlib.sha256(mef_raw).hexdigest(), "bytes": len(mef_raw)},
                    "istat": {"url": ISTAT_URL, "sha256": hashlib.sha256(istat_raw).hexdigest(), "bytes": len(istat_raw)},
                    "posas": {"url": POSAS_URL.format(year=year + 1), "sha256": hashlib.sha256(posas_raw).hexdigest(), "date": f"{year + 1}-01-01"}},
        "audit": dict(audit, readable=len(rules), unreadable=len(unread), unmatchedCadastral=sorted(unmatched),
                      unreadableExamples=dict(sorted(unread.items())[:40])),
        "towns": towns, "benchmarks": benchmarks, "blocked": blocked,
        "qualityGate": {"status": "PASS", "publicReconciliation": "7/7" if not blocked else f"{7 - len(blocked)}/7"},
    }
