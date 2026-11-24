#!/usr/bin/env python3
"""IMU su una seconda casa vuota: aliquota per Comune dai prospetti MEF e confronti Toscana e Italia.

Regola (decisione del 24/11/2026): aliquota «Abitazione a disposizione» (abitazioni non locate né concesse in
comodato) se il prospetto la indica per la A/2, altrimenti l'aliquota generale «Altri fabbricati». Vale il
prospetto dell'anno pubblicato entro il 28 ottobre (l'ultimo, se più d'uno); senza prospetto valido dell'anno vale
quello dell'anno precedente (art. 1, comma 767, legge 160/2019). Prospetto illeggibile o ambiguo (righe «a
disposizione» con aliquote diverse, Comune fuso con aliquote differenziate): il Comune resta fuori.

Confronto: media degli importi su 100.000 € di base imponibile pesata per i residenti al 1° gennaio dell'anno
(Istat POSAS: l'IMU si paga nell'anno, i residenti al 1° gennaio successivo non sono ancora pubblicati), pubblicato solo se i Comuni letti coprono almeno il 90% dei residenti dell'ambito.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import irpef_benchmarks as ib
import probe_mef_fiscal as mef

PAGE = mef.BASE + "nuova_imu/risultato.htm?lista=1&r=2&pagina=&cm=O&pr=&DOWNLOAD=Procedi&anno={year}&cc={code}"
SNAPSHOT = "data/source-snapshots/mef-imu-benchmark-{scope}-{year}.json"
METRIC = "municipalImuStandard"
BASE_AMOUNT = 100_000
MIN_SHARE = 0.90
TUSCANY = "09"
TOWNS = {"046005": "B455", "046013": "D730", "046018": "F035", "046024": "G628", "046028": "I622", "046030": "I942", "046033": "L833"}

RATE = r"(\d{1,2}(?:,\d{1,3})?)\s*%"
BASE_LINE = re.compile(r"Altri fabbricati \(fabbricati diversi dall.abitazione principale e dai fabbricati(?: appartenenti al gruppo)?\s+" + RATE)
DISPOSAL = re.compile(r"Abitazione a disposizione\s+" + RATE)
ITEM = re.compile(r"(?=Altri fabbricati \(fabbricati diversi|Fabbricati appartenenti al gruppo catastale D Categoria|Elenco esenzioni)")
RESTRICTED = re.compile(r"Requisiti del soggetto passivo|Ulteriori condizioni|Condizioni locatario|Ubicazione|Zona\b|inagibil", re.I)
NEXT_ITEM = re.compile(r"Altri fabbricati|Abitazione (?:locata|a disposizione|destinata)|Immobili di categoria|Fabbricati appartenenti|"
                       r"Fabbricati rurali|Aree fabbricabili|Terreni agricoli|Elenco esenzioni")
HEADER = re.compile(r"Prospetto aliquote IMU - Comune di .{1,80}? ID Prospetto (\d+) riferito all.anno (\d{4})")
MERGED = re.compile(r"applica aliquote differenziate nei preesistenti comuni:\s*SI\b", re.I)


class ImuBenchmarkError(RuntimeError):
    pass


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _pct(text: str) -> float:
    return float(text.replace(",", "."))


def second_home_rate(pdf_text: str) -> tuple[float | None, str]:
    """(aliquota %, voce usata) dal testo del prospetto, o (None, motivo)."""
    text = clean(pdf_text)
    if MERGED.search(text):
        return None, "Comune fuso con aliquote differenziate nei preesistenti Comuni"
    base = {_pct(m.group(1)) for m in BASE_LINE.finditer(text)}
    disposal = []
    for m in DISPOSAL.finditer(text):
        # La riga finisce dove comincia la successiva del prospetto: condizioni e categorie contano solo lì.
        end = NEXT_ITEM.search(text, m.end())
        chunk = text[m.start():end.start() if end else len(text)]
        cats = re.findall(r"- (A/\d+)\b", chunk)
        if cats and "A/2" not in cats:
            continue  # riga limitata a categorie senza la A/2
        if RESTRICTED.search(chunk):
            continue  # riga per proprietari particolari (ONLUS, disabili) o con condizioni non dichiarate: non è la seconda casa tipica
        disposal.append(_pct(m.group(1)))
    if len(set(disposal)) > 1:
        return None, f"righe «a disposizione» con aliquote diverse: {sorted(set(disposal))}"
    if disposal:
        return disposal[0], "Abitazione a disposizione"
    if len(base) == 1:
        return base.pop(), "Altri fabbricati"
    return None, f"aliquota «Altri fabbricati» non univoca: {sorted(base)}"


def listed(page: str, url: str) -> list[dict[str, Any]]:
    """Prospetti (DIMUNIC) elencati nella pagina con data di pubblicazione."""
    out = []
    for link in mef.links(page, url):
        if not mef.is_doc(link):
            continue
        dates = re.findall(r"\b(\d{2})-(\d{2})-(\d{4})\b", link["row"])
        if len(dates) < 2:
            continue
        d, m, y = dates[1]
        out.append({"url": link["url"], "published": dt.date(int(y), int(m), int(d)).isoformat(), "row": link["row"]})
    return out


def town_rate(code: str, year: int, fetch: Callable[[str], bytes], pdf_text: Callable[[bytes], str]) -> dict[str, Any]:
    """Aliquota del Comune per l'anno: prospetto dell'anno pubblicato entro il 28/10, altrimenti quello dell'anno prima."""
    tried = []
    for y in (year, year - 1):
        url = PAGE.format(year=y, code=code)
        page = fetch(url).decode("utf-8", errors="replace")
        deadline = dt.date(y, 10, 28).isoformat()
        docs = sorted((d for d in listed(page, url) if d["published"] <= deadline), key=lambda d: d["published"], reverse=True)
        for doc in docs:
            text = clean(pdf_text(fetch(doc["url"])))
            head = HEADER.search(text)
            if not head or int(head.group(2)) != y:
                continue  # allegato o prospetto di un altro anno
            rate, basis = second_home_rate(text)
            entry = {"year": y, "prospetto": head.group(1), "published": doc["published"], "url": doc["url"], "page": url}
            if rate is None:
                return {"status": "ambiguous", "reason": basis, **entry}
            return {"status": "ok", "ratePercent": rate, "basis": basis, "carriedFrom": y if y != year else None, **entry}
        tried.append(url)
    return {"status": "missing", "reason": "nessun prospetto valido nell'anno né in quello precedente", "pages": tried}


# L'Italia si legge in quattro gruppi di regioni, uno per corsa CI (circa 2.000 Comuni, sotto il limite di 90 minuti),
# poi `combine` li unisce: stessi elenco Istat e POSAS, regioni disgiunte che coprono tutte le venti.
ITALY_GROUPS = {
    "italia-1": ("01", "02", "04", "06", "07"),             # Piemonte, Valle d'Aosta, Trentino-Alto Adige, Friuli-VG, Liguria
    "italia-2": ("03", "05"),                               # Lombardia, Veneto
    "italia-3": ("08", "09", "10", "11", "12", "13", "14", "20"),  # Emilia-Romagna … Molise, Sardegna (con la Toscana)
    "italia-4": ("15", "16", "17", "18", "19"),             # Campania, Puglia, Basilicata, Calabria, Sicilia
}
SCOPES = {"toscana": (TUSCANY,), **ITALY_GROUPS}
REGIONS = tuple(f"{n:02d}" for n in range(1, 21))
WORKERS = 8  # prospetti letti in parallelo: al massimo 8 richieste insieme al sito MEF


def _summary(year: int, scope: str, rows: dict[str, dict[str, Any]], sources: dict[str, Any]) -> dict[str, Any]:
    ok = {k: v for k, v in rows.items() if v["status"] == "ok" and v["residents"]}
    total = sum(v["residents"] or 0 for v in rows.values())
    covered = sum(v["residents"] for v in ok.values())
    share = covered / total if total else 0.0
    value = round(sum(v["ratePercent"] / 100 * BASE_AMOUNT * v["residents"] for v in ok.values()) / covered, 2) if covered else None
    with_versilia = all(k in rows for k in TOWNS)
    missing_towns = [k for k in TOWNS if rows.get(k, {}).get("status") != "ok"] if with_versilia else []
    return {
        "schemaVersion": 1, "year": year, "scope": scope,
        "retrieved": dt.date.today().isoformat(),
        "rule": ("Aliquota «Abitazione a disposizione» se indicata per la A/2, altrimenti «Altri fabbricati»; prospetto dell'anno "
                 "pubblicato entro il 28/10, altrimenti quello dell'anno precedente. Media degli importi su 100.000 € pesata "
                 "per i residenti al 1° gennaio dell'anno."),
        "sources": sources,
        "towns": rows,
        "benchmark": {"value": value if share >= MIN_SHARE else None, "municipalities": len(ok), "municipalitiesTotal": len(rows),
                      "populationShare": round(share, 4), "minShare": MIN_SHARE},
        **({"versilia": {k: rows[k] for k in TOWNS}} if with_versilia else {}),
        "qualityGate": {"status": "PASS" if not missing_towns else "FAIL",
                        "note": ("7/7 Comuni della Versilia letti" if with_versilia else "gruppo senza la Versilia")
                        if not missing_towns else f"Versilia non letta: {missing_towns}"},
    }


def build_snapshot(year: int, fetch: Callable[[str], bytes], pdf_text: Callable[[bytes], str], scope: str = "toscana") -> dict[str, Any]:
    if scope not in SCOPES:
        raise ImuBenchmarkError(f"ambito sconosciuto: {scope}")
    regions = set(SCOPES[scope])
    istat_raw, posas_raw = fetch(ib.ISTAT_URL), fetch(ib.POSAS_URL.format(year=year))
    codes = ib.istat_codes(istat_raw)
    residents = ib.posas_totals(posas_raw)
    towns = {cc: istat for cc, (istat, region) in codes.items() if region in regions}
    if TUSCANY in regions:
        for istat, cc in TOWNS.items():
            if towns.get(cc) != istat:
                raise ImuBenchmarkError(f"codice catastale {cc} non associato a {istat}")

    def read(cc: str) -> dict[str, Any]:
        try:
            return town_rate(cc, year, fetch, pdf_text)
        except Exception as error:  # noqa: BLE001 - un Comune illeggibile resta fuori, con il motivo
            return {"status": "error", "reason": f"{type(error).__name__}: {error}"[:300]}

    order = sorted(towns.items())
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(read, [cc for cc, _ in order]))
    rows: dict[str, dict[str, Any]] = {}
    for (cc, istat), r in zip(order, results):
        r["catastale"] = cc
        r["residents"] = residents.get(istat)
        rows[istat] = r
    sources = {"istat": {"url": ib.ISTAT_URL, "sha256": hashlib.sha256(istat_raw).hexdigest()},
               "posas": {"url": ib.POSAS_URL.format(year=year), "sha256": hashlib.sha256(posas_raw).hexdigest()}}
    snap = _summary(year, scope, rows, sources)
    snap["regions"] = sorted(regions)
    if scope == "toscana":
        snap.pop("regions")  # forma invariata dello snapshot Toscana già pubblicato
    return snap


def combine(year: int, parts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Snapshot Italia dai quattro gruppi: stesso anno, stessi elenco Istat e POSAS, regioni disgiunte e complete."""
    if set(parts) != set(ITALY_GROUPS):
        raise ImuBenchmarkError(f"gruppi Italia mancanti: {sorted(set(ITALY_GROUPS) - set(parts))}")
    sources = {json.dumps(p["sources"], sort_keys=True) for p in parts.values()}
    if len(sources) != 1:
        raise ImuBenchmarkError("gruppi Italia letti con elenchi Istat o POSAS diversi: rileggere")
    rows: dict[str, dict[str, Any]] = {}
    for name, part in sorted(parts.items()):
        if part["year"] != year or part["scope"] != name or part.get("regions") != sorted(ITALY_GROUPS[name]):
            raise ImuBenchmarkError(f"gruppo {name}: anno, ambito o regioni diversi da quelli attesi")
        overlap = set(rows) & set(part["towns"])
        if overlap:
            raise ImuBenchmarkError(f"Comuni in più gruppi: {sorted(overlap)[:5]}")
        rows.update(part["towns"])
    if sorted(r for g in ITALY_GROUPS.values() for r in g) != list(REGIONS):
        raise ImuBenchmarkError("i gruppi non coprono esattamente le venti regioni")
    snap = _summary(year, "italia", dict(sorted(rows.items())), json.loads(sources.pop()))
    snap["retrieved"] = max(p["retrieved"] for p in parts.values())
    snap["parts"] = {name: {"retrieved": p["retrieved"], "municipalities": p["benchmark"]["municipalitiesTotal"],
                            "acquisitionEvidence": p.get("acquisitionEvidence")} for name, p in sorted(parts.items())}
    return snap
