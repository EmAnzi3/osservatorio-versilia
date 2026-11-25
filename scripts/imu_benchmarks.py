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
import queue
import threading
import time
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
# Dove l'IMU non si applica: imposte immobiliari locali proprie (decisione del 24/11/2026: fuori dal perimetro Italia,
# dichiarato nella nota). Province Istat: Bolzano 021, Trento 022; Friuli-Venezia Giulia 030, 031, 032, 093.
NOT_IMU = {"021": "Bolzano (IMI)", "022": "Trento (IMIS)", "030": "Udine (ILIA)", "031": "Gorizia (ILIA)",
           "032": "Trieste (ILIA)", "093": "Pordenone (ILIA)"}
NOT_IMU_NOTE = "esclusi Trentino-Alto Adige e Friuli-Venezia Giulia, dove al posto dell'IMU si applicano IMI, IMIS e ILIA"
WORKERS = 8  # prospetti letti in parallelo: al massimo 8 richieste insieme al sito MEF
DEADLINE = 65 * 60  # secondi per gruppo: una corsa CI ha 90 minuti, meno preparazione, test e commit


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


def read_all(codes: list[str], read: Callable[[str], dict[str, Any]], deadline: float, log: Callable[[str], None] = print) -> list[dict[str, Any]]:
    """Legge i Comuni con WORKERS thread daemon entro `deadline` secondi. Un prospetto che blocca un thread (rete lenta,
    PDF patologico) non ferma la corsa: allo scadere i Comuni non letti restano fuori con il motivo, e la copertura lo
    misura. Avanzamento a intervalli regolari nel log della CI."""
    pending: queue.Queue[str] = queue.Queue()
    for code in codes:
        pending.put(code)
    done: dict[str, dict[str, Any]] = {}

    def worker() -> None:
        while True:
            try:
                code = pending.get_nowait()
            except queue.Empty:
                return
            done[code] = read(code)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(min(WORKERS, len(codes)) or 1)]
    for t in threads:
        t.start()
    start = time.monotonic()
    last = start
    while any(t.is_alive() for t in threads) and time.monotonic() - start < deadline:
        time.sleep(0.2)
        if time.monotonic() - last >= 60:
            last = time.monotonic()
            log(f"  prospetti IMU: {len(done)}/{len(codes)} Comuni in {int(last - start)} s")
    late = [c for c in codes if c not in done]
    log(f"  prospetti IMU: {len(done)}/{len(codes)} Comuni in {int(time.monotonic() - start)} s" + (f"; non letti entro il tempo: {len(late)}" if late else ""))
    return [dict(done[c]) if c in done else {"status": "error", "reason": "non letto entro il tempo della corsa"} for c in codes]


def resumable(previous: dict[str, Any] | None, year: int, scope: str, sources: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Comuni già letti in una corsa precedente dello stesso gruppo (stessi anno ed elenchi Istat e POSAS): si tengono
    gli esiti definitivi (letto, prospetto assente, prospetto ambiguo) e si rileggono solo gli errori di lettura. Così un
    gruppo rallentato dal sito del MEF si completa in più corse senza rileggere quanto già acquisito."""
    if not previous or previous.get("year") != year or previous.get("scope") != scope or previous.get("sources") != sources:
        return {}
    return {k: v for k, v in previous.get("towns", {}).items() if v.get("status") != "error"}


def build_snapshot(year: int, fetch: Callable[[str], bytes], pdf_text: Callable[[bytes], str], scope: str = "toscana",
                   deadline: float = DEADLINE, previous: dict[str, Any] | None = None) -> dict[str, Any]:
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

    sources = {"istat": {"url": ib.ISTAT_URL, "sha256": hashlib.sha256(istat_raw).hexdigest()},
               "posas": {"url": ib.POSAS_URL.format(year=year), "sha256": hashlib.sha256(posas_raw).hexdigest()}}
    kept = resumable(previous, year, scope, sources)
    order = sorted(towns.items())
    todo = [cc for cc, istat in order if istat not in kept]
    print(f"  prospetti IMU: {len(order) - len(todo)} Comuni ripresi dalla corsa precedente, {len(todo)} da leggere")
    results = dict(zip(todo, read_all(todo, read, deadline)))
    rows: dict[str, dict[str, Any]] = {}
    for cc, istat in order:
        r = dict(kept[istat]) if istat in kept else results[cc]
        r["catastale"] = cc
        r["residents"] = residents.get(istat)
        rows[istat] = r
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
    excluded = {k: v for k, v in rows.items() if k[:3] in NOT_IMU}
    if any(v["status"] == "ok" for v in excluded.values()):
        raise ImuBenchmarkError("prospetto IMU letto in un Comune con imposta propria: rivedere il perimetro")
    rows = {k: v for k, v in rows.items() if k not in excluded}
    snap = _summary(year, "italia", dict(sorted(rows.items())), json.loads(sources.pop()))
    snap["excluded"] = {"note": NOT_IMU_NOTE, "provinces": NOT_IMU, "municipalities": len(excluded),
                        "residents": sum(v["residents"] or 0 for v in excluded.values()), "codes": sorted(excluded)}
    snap["retrieved"] = max(p["retrieved"] for p in parts.values())
    snap["parts"] = {name: {"retrieved": p["retrieved"], "municipalities": p["benchmark"]["municipalitiesTotal"],
                            "acquisitionEvidence": p.get("acquisitionEvidence")} for name, p in sorted(parts.items())}
    return snap
