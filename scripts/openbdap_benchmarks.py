#!/usr/bin/env python3
"""Confronto Toscana/Italia per gli indicatori di rendiconto dei Comuni (OpenBDAP, schemi di bilancio).

Regola (decisa il 18 novembre 2026): l'aggregato di un territorio si calcola sui Comuni
che hanno trasmesso il rendiconto con le righe necessarie, sommando numeratori e
denominatori degli stessi Comuni (per i valori per residente, la loro popolazione al
1° gennaio dell'anno, la stessa dei valori comunali). Il territorio è pubblicato solo
se quei Comuni coprono almeno il 90% dei residenti; la copertura è dichiarata.

Fonti: gli archivi regionali «AAAA_Rendiconto - Schemi di bilancio_REGIONE.zip» e il
bilancio demografico Istat P2 dell'anno (colonna della popolazione di ogni Comune al
1° gennaio). I valori dei sette Comuni ricalcolati qui devono coincidere con
quelli pubblicati (riconciliazione 7/7) prima che un aggregato sia accettato.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import time
import urllib.error
import urllib.parse
import zipfile
from collections import defaultdict
from datetime import date
from typing import Any, Callable

BASE = "https://openbdap.rgs.mef.gov.it"
PORTAL = BASE + "/it/FET/Analizza"
ARCHIVE = "/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto - Schemi di bilancio_{region}.zip"
P2_URL = "https://demo.istat.it/data/p2/P2_{year}_it_Comuni.zip"
SNAPSHOT_PREFIX = "data/source-snapshots/openbdap-benchmark-"
UA = "OsservatorioVersilia-A3-OpenBDAP-benchmark/1.0"
MIN_COVERAGE = 0.90
TUSCANY = "09"
# Codice regione Istat → nomi possibili nel file OpenBDAP (si prova nell'ordine)
REGIONS = {
    "01": ("PIEMONTE",), "02": ("VALLE D'AOSTA", "VALLE D AOSTA", "VALLE DAOSTA", "VALLE_D_AOSTA"),
    "03": ("LOMBARDIA",), "04": ("TRENTINO-ALTO ADIGE", "TRENTINO ALTO ADIGE", "TRENTINO-ALTO ADIGE-SUDTIROL"),
    "05": ("VENETO",), "06": ("FRIULI-VENEZIA GIULIA", "FRIULI VENEZIA GIULIA"), "07": ("LIGURIA",),
    "08": ("EMILIA-ROMAGNA", "EMILIA ROMAGNA"), "09": ("TOSCANA",), "10": ("UMBRIA",), "11": ("MARCHE",),
    "12": ("LAZIO",), "13": ("ABRUZZO",), "14": ("MOLISE",), "15": ("CAMPANIA",), "16": ("PUGLIA",),
    "17": ("BASILICATA",), "18": ("CALABRIA",), "19": ("SICILIA",), "20": ("SARDEGNA",),
}
MEMBERS = {"entrate": "Rendiconto SDB Entrate Riepilogo Titoli", "spese": "Rendiconto SDB Spese Riepilogo Titoli",
           "missioni": "Rendiconto SDB Spese Riepilogo Missioni", "risultato": "Rendiconto SDB Allegato A Risultato di Amministrazione"}
MISSIONS = {
    "educationMissionExpenditurePerResident": ("04",), "socialMissionExpenditurePerResident": ("12",),
    "environmentMissionExpenditurePerResident": ("09",), "mobilityMissionExpenditurePerResident": ("10",),
    "cultureSportMissionExpenditurePerResident": ("05", "06"), "tourismDevelopmentMissionExpenditurePerResident": ("07", "14"),
    "generalAdministrationMissionExpenditurePerResident": ("01",), "territorialPlanningMissionExpenditurePerResident": ("08",),
    "civilProtectionMissionExpenditurePerResident": ("11",), "economicDevelopmentMissionExpenditurePerResident": ("14",),
}
RESULTS = {"availableAdministrationResultPerResident": "0502", "fcdePerResident": "0491", "yearEndCashFundPerResident": "0495"}
RATIOS = {"ownRevenueShare", "currentCollectionCapacity", "currentPaymentCapacity"}
METRICS = ("currentRevenueAccruedPerResident", "currentExpenditureCommittedPerResident", "capitalExpenditureCommittedPerResident",
           *sorted(RATIOS), *sorted(RESULTS), *sorted(MISSIONS))


class BenchmarkError(RuntimeError):
    pass


def fetch(url: str) -> bytes:
    """Scarica con `requests` e lo stesso User-Agent dell'acquisizione toscana già verificata; 404 → HTTPError."""
    import requests

    errors = []
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=600)
            if r.status_code == 404:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            r.raise_for_status()
            return r.content
        except urllib.error.HTTPError:
            raise
        except Exception as error:  # noqa: BLE001
            errors.append(f"{attempt}: {type(error).__name__}: {error}")
        time.sleep(10 * attempt)
    raise BenchmarkError(f"{url}: " + " | ".join(errors))


def archive_url(year: int, region: str) -> str:
    return BASE + urllib.parse.quote(ARCHIVE.format(year=year, region=region), safe="/:_-.'")


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def num(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        x = float(text)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def read_members(raw: bytes, region: str) -> dict[str, list[dict[str, str]]]:
    out = {}
    squash = lambda t: "".join(ch for ch in t.lower() if ch.isalnum())
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        for key, prefix in MEMBERS.items():
            hits = [n for n in names if squash(n.rsplit("/", 1)[-1]).endswith(squash(f"{prefix}_{region}.csv"))]
            if len(hits) != 1:
                raise BenchmarkError(f"{prefix}: atteso 1 CSV, trovati {hits} fra {[n for n in names if n.lower().endswith('.csv')][:60]}")
            reader = csv.DictReader(io.StringIO(decode(z.read(hits[0]))), delimiter=";")
            out[key] = [{k.strip(): v for k, v in row.items() if k and k.strip()} for row in reader]
    return out


def code(row: dict[str, str]) -> str:
    prov = str(row.get("Codice Provincia") or "").strip().zfill(3)
    com = str(row.get("Codice Comune") or "").strip().zfill(3)
    return prov + com if prov.strip("0") and com.strip("0") else ""


def is_municipality(row: dict[str, str]) -> bool:
    return str(row.get("Codice Tipologia Soggetto") or "").strip() == "ELCOMU"


def index(rows: list[dict[str, str]], key_field: str) -> dict[tuple[str, str], list[dict[str, str]]]:
    out: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if is_municipality(row) and (c := code(row)) and (k := str(row.get(key_field) or "").strip()):
            out[(c, k)].append(row)
    return out


class MissionIndex(dict):
    """Indice delle missioni con l'elenco dei Comuni che hanno trasmesso il riepilogo (ricerca veloce)."""

    def __init__(self, data: dict, towns: set[str]):
        super().__init__(data)
        self.towns = towns


def exact(idx: dict, c: str, k: str, field: str) -> float:
    hits = idx.get((c, k), [])
    if len(hits) != 1:
        raise ValueError(f"{k}: righe {len(hits)}")
    value = num(hits[0].get(field))
    if value is None:
        raise ValueError(f"{k}/{field}: non numerico")
    return value


def components(tables: dict[str, dict], c: str, metric: str) -> tuple[float, float | None]:
    """(numeratore, denominatore) in euro per i rapporti; (totale, None) per i valori per residente."""
    e, s, m, r = tables["entrate"], tables["spese"], tables["missioni"], tables["risultato"]
    acc = lambda: sum(exact(e, c, k, "Accertamenti") for k in ("01", "02", "03"))
    if metric == "currentRevenueAccruedPerResident":
        return acc(), None
    if metric == "currentExpenditureCommittedPerResident":
        return exact(s, c, "01", "Impegni"), None
    if metric == "capitalExpenditureCommittedPerResident":
        return exact(s, c, "02", "Impegni"), None
    if metric == "ownRevenueShare":
        return sum(exact(e, c, k, "Accertamenti") for k in ("01", "03")), acc()
    if metric == "currentCollectionCapacity":
        return sum(exact(e, c, k, "Riscossioni in C/Competenza") for k in ("01", "02", "03")), acc()
    if metric == "currentPaymentCapacity":
        return exact(s, c, "01", "Pagamenti in C/Competenza"), exact(s, c, "01", "Impegni")
    if metric in RESULTS:
        return exact(r, c, RESULTS[metric], "Totale di Gestione"), None
    if metric in MISSIONS:
        # Il riepilogo per missioni elenca solo le missioni con importi: un Comune che ha trasmesso il
        # riepilogo senza la riga di una missione non ha impegni su quella missione (zero, non dato mancante).
        towns = m.towns if isinstance(m, MissionIndex) else {cc for cc, _ in m}
        if c not in towns:
            raise ValueError("riepilogo missioni assente")
        return sum(exact(m, c, k, "Impegni") if (c, k) in m else 0.0 for k in MISSIONS[metric]), None
    raise KeyError(metric)


def p2_population(raw: bytes) -> dict[str, int]:
    """Comune → popolazione al 1° gennaio (colonna «Popolazione al 1° gennaio - Totale» del bilancio P2)."""
    from acquire_a3_benchmark_demography_candidates import code_of, num as p2num, pick_population_total

    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))]
        if len(names) != 1:
            raise BenchmarkError(f"P2: archivio inatteso {names}")
        text = z.read(names[0]).decode("utf-8-sig")
    parsed = list(csv.reader(io.StringIO(text), delimiter=";"))
    headers = [h.strip() for h in parsed[1]]
    jan1 = pick_population_total(headers, "gennaio")
    out = {}
    for cells in parsed[2:]:
        if not cells:
            continue
        row = dict(zip(headers, cells))
        c = code_of(row)
        if len(c) == 6 and c.isdigit() and c != "000000":
            out[c] = int(p2num(row.get(jan1)))
    if not 7500 <= len(out) <= 8100:
        raise BenchmarkError(f"P2: {len(out)} Comuni")
    return out


def aggregate(values: dict[str, tuple[float, float | None]], population: dict[str, int], metric: str) -> tuple[float, float, float]:
    num_total = sum(v[0] for v in values.values())
    den_total = sum(v[1] for v in values.values()) if metric in RATIOS else sum(population[c] for c in values)
    value = num_total / den_total * 100 if metric in RATIOS else num_total / den_total
    return value, num_total, den_total


def build_snapshot(year: int, fetcher: Callable[[str], bytes], published: dict[str, dict[str, float]],
                   towns: dict[str, str]) -> dict[str, Any]:
    """`published`: metrica → {codice: valore pubblico anno `year`}; `towns`: codice → nome."""
    p2_raw = fetcher(P2_URL.format(year=year))
    population = p2_population(p2_raw)
    regions: dict[str, Any] = {}
    per_metric: dict[str, dict[str, dict[str, tuple[float, float | None]]]] = {m: {} for m in METRICS}
    reporting: dict[str, set[str]] = {}
    missing_regions = {}
    for reg, names in REGIONS.items():
        raw, tried = None, []
        for name in names:
            url = archive_url(year, name)
            tried.append(url)
            try:
                raw = fetcher(url)
                break
            except urllib.error.HTTPError as error:
                tried[-1] = f"{url} → HTTP {error.code}"
                continue
        if raw is None:
            missing_regions[reg] = tried
            continue
        try:
            members = read_members(raw, name)
        except (BenchmarkError, zipfile.BadZipFile) as error:
            missing_regions[reg] = {"archive": url, "error": str(error)[:2000]}
            continue
        tables = {"entrate": index(members["entrate"], "Codice Titolo"), "spese": index(members["spese"], "Codice Titolo"),
                  "missioni": index(members["missioni"], "Codice Missione"), "risultato": index(members["risultato"], "Cod Voce Ris Amm Rend")}
        mission_towns = {c for c, _ in tables["missioni"]}
        tables["missioni"] = MissionIndex(tables["missioni"], mission_towns)
        codes = sorted({code(r) for r in members["entrate"] if is_municipality(r) and code(r)})
        reporting[reg] = set(codes)
        print(f"OpenBDAP {reg}: {len(codes)} Comuni", flush=True)
        regions[reg] = {"archive": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "municipalities": len(codes)}
        for c in codes:
            for metric in METRICS:
                try:
                    per_metric[metric][c] = components(tables, c, metric)
                except ValueError:
                    pass
    region_of = {c: reg for reg, cs in reporting.items() for c in cs}
    unknown = sorted(c for c in region_of if c not in population)
    # Codici OpenBDAP non presenti nel P2 dell'anno (nuove province sarde, fusioni): esclusi e dichiarati;
    # contano come Comuni non coperti, mai come zeri.
    if len(unknown) > 600:
        raise BenchmarkError(f"{len(unknown)} codici OpenBDAP assenti dal P2: {unknown[:10]}")
    # Riconciliazione 7/7 per indicatore: se un valore comunale ricalcolato non è quello pubblicato
    # (rendiconto ritrasmesso, regola diversa), quell'indicatore resta senza confronto e il motivo è dichiarato.
    blocked: dict[str, list[str]] = {}
    for metric, expected in published.items():
        for c, value in expected.items():
            if c not in per_metric[metric]:
                blocked.setdefault(metric, []).append(f"{towns[c]}: righe assenti")
                continue
            n, d = per_metric[metric][c]
            live = n / d * 100 if metric in RATIOS else n / population[c]
            if not math.isclose(live, value, rel_tol=0, abs_tol=1e-6):
                blocked.setdefault(metric, []).append(f"{towns[c]}: fonte {live} ≠ pubblicato {value}")
    if len(blocked) > len(published) // 2:
        raise BenchmarkError("riconciliazione 7/7 non superata: " + json.dumps(blocked, ensure_ascii=False)[:1500]
                             + f" — Toscana: {missing_regions.get(TUSCANY, regions.get(TUSCANY))}")
    tuscany_codes = {c for c in population if c.startswith(("045", "046", "047", "048", "049", "050", "051", "052", "053", "100"))}
    scopes = {"tuscany": tuscany_codes, "italy": set(population)}
    benchmarks: dict[str, Any] = {}
    for metric in METRICS:
        out = {}
        if metric in blocked:
            benchmarks[metric] = {scope: {"value": None, "reason": "riconciliazione 7/7 non superata: " + "; ".join(blocked[metric])}
                                  for scope in scopes}
            continue
        for scope, perimeter in scopes.items():
            values = {c: v for c, v in per_metric[metric].items() if c in perimeter and c in population}
            pop_all = sum(population[c] for c in perimeter)
            pop_cov = sum(population[c] for c in values)
            share = pop_cov / pop_all
            entry = {"municipalities": len(values), "municipalitiesTotal": len(perimeter), "populationCovered": pop_cov,
                     "populationTotal": pop_all, "populationShare": share}
            if share >= MIN_COVERAGE:
                value, n, d = aggregate(values, population, metric)
                entry.update(value=value, numerator=n, denominator=d)
            else:
                entry.update(value=None, reason=f"copertura {share:.1%} sotto la soglia del {MIN_COVERAGE:.0%}")
            out[scope] = entry
        benchmarks[metric] = out
    return {
        "schemaVersion": 1, "version": f"openbdap-benchmark-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Ragioneria Generale dello Stato — OpenBDAP (rendiconti) · Istat (bilancio demografico P2)",
        "sourceUrl": PORTAL, "year": year,
        "rule": ("Aggregato sui Comuni che hanno trasmesso il rendiconto con le righe necessarie (una missione assente dal riepilogo di un Comune vale zero): somma dei numeratori / somma dei "
                 "denominatori (popolazione al 1° gennaio per i valori per residente). Pubblicato solo con almeno il 90% dei "
                 "residenti coperti; copertura dichiarata."),
        "minCoverage": MIN_COVERAGE,
        "population": {"url": P2_URL.format(year=year), "sha256": hashlib.sha256(p2_raw).hexdigest(), "municipalities": len(population),
                       "date": f"{year}-01-01"},
        "regions": regions, "missingRegions": missing_regions, "unknownCodes": unknown,
        "towns": {c: {m: list(per_metric[m][c]) for m in METRICS if c in per_metric[m]} | {"population": population[c]} for c in towns},
        "benchmarks": benchmarks,
        "blocked": blocked,
        "qualityGate": {"status": "PASS", "publicReconciliation": f"{len(published) - len(blocked)} indicatori × 7/7; {len(blocked)} esclusi dal confronto"},
    }
