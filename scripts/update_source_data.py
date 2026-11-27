#!/usr/bin/env python3
"""Aggiornatori dei dati dalla fonte ufficiale, dopo un periodo nuovo o una revisione.

Ogni aggiornatore legge il file ufficiale (scaricato qui oppure indicato con
`--file`), aggiorna lo snapshot versionato e il catalogo `data/site-data.json`
e stampa ogni valore che cambia. Non inventa nulla: se il file non ha la forma
attesa o i Comuni non sono 7/7, si ferma senza scrivere.

    # ricoveri ARS (export 1332) — stesso periodo rivisto dalla fonte
    python scripts/update_source_data.py ars-legacy --metric hospitalizedAll [--file 1332.zip]

    # mobilità residenziale (Istat P2, tutti i Comuni) — anno nuovo
    python scripts/update_source_data.py istat-mobility --year 2025 [--file P2_2025_it_Comuni.zip]

    # unità locali e addetti (Istat ASIA-UL, SDMX) — anno nuovo o revisione
    python scripts/update_source_data.py istat-asia --year 2024 [--dir cartella-con-lu.csv-emp.csv-micro.csv]

    # copertura FTTH (AGCOM Broadband Map) — ultima edizione indicata da report.js
    python scripts/update_source_data.py agcom-ftth [--dir cartella-con-report.js-e-comuni.csv]
    python scripts/update_source_data.py istat-tourism --year 2025 [--file archivio.zip]
    python scripts/update_source_data.py aci-vehicles --year 2025 [--file Autoritratto2025_Parco_veicolare.zip]
    python scripts/update_source_data.py ispra-soil --year 2025 [--file consumo_suolo_2026_Com_Prov_Reg_Naz.xlsx]
    python scripts/update_source_data.py omi-residential --semester 2026-S1
    python scripts/update_source_data.py erp-arrears --year 2025
    python scripts/update_source_data.py gaia-water --period 2026-S1
    python scripts/update_source_data.py mim-schools --year 2026 [--file SCUANAGRAFESTAT20262720260901.csv]
    python scripts/update_source_data.py source-probe --name NOME --url URL [--follow REGEX] [--post URL::CAMPI ...]

Con `--dry-run` mostra le differenze senza scrivere. I server GitHub raggiungono
fonti che altrove non rispondono: il workflow «Aggiorna dati dalla fonte» esegue
questi comandi e committa il risultato sul ramo della PR.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html.parser
import io
import json
import math
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import acquire_a3_5_ars_legacy_history as ars_legacy  # noqa: E402
import acquire_a3_benchmark_demography_candidates as demo  # noqa: E402
import release_period_probes as probes  # noqa: E402

ROOT = SCRIPT_DIR.parent
SITE = ROOT / "data" / "site-data.json"
SNAP = ROOT / "data" / "source-snapshots"
ARS_LEGACY = SNAP / "ars-a3-5-legacy-history.json"
COMPOSITE = SNAP / "composite-indicators-v1.9.0.json"
MOBILITY = ("internalResidentialMobility", "foreignResidentialMobility", "totalResidentialMobility")
TOWN_CODES = probes.TOWN_CODES
# Codice ARS della Regione Toscana (par_top_geografia=090 nelle pagine «La salute dei comuni»).
TUSCANY_ARS_CODES = {"90"}


class UpdateError(RuntimeError):
    pass


def keep_retrieved(new: dict[str, Any], old: dict[str, Any] | None) -> dict[str, Any]:
    """Se il contenuto non cambia, la data di acquisizione resta quella già registrata."""
    if old is not None and {**old, "retrieved": None} == {**new, "retrieved": None}:
        return {**new, "retrieved": old["retrieved"]}
    return new


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict[str, Any], *, compact: bool = False) -> None:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(value, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def fetch(url: str, file: Path | None) -> bytes:
    if file is not None:
        return file.read_bytes()
    return probes.http_fetch(url)


def it_number(value: float, decimals: int) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


class Changes:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def note(self, label: str, old: Any, new: Any) -> None:
        if old != new:
            self.lines.append(f"  {label}: {old} → {new}")

    def report(self, title: str) -> None:
        print(title)
        print("\n".join(self.lines) if self.lines else "  nessuna differenza")


# ------------------------------------------------------------------ ARS legacy (es. ricoveri 1332)

def ars_csv(payload: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        name = next((n for n in names if n.lower().endswith(".csv")), None)
        if name:
            return archive.read(name)
        nested = next((n for n in names if n.lower().endswith(".zip")), None)
        if nested:
            return ars_csv(archive.read(nested))
    raise UpdateError("export ARS senza CSV")


def ars_series(indicator_id: int, raw: bytes) -> tuple[list[str], dict[str, list[float]], float | None]:
    """Serie standardizzate 7 Comuni + Zona Versilia e valore Toscana dell'ultimo periodo."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    by_geo: dict[str, dict[str, float]] = {}
    tuscany: dict[str, float] = {}
    other: set[str] = set()
    for row in reader:
        if str(row.get("id_indicatore") or "").strip() != str(indicator_id):
            continue
        if not all(ars_legacy._is_total(row.get(k)) for k in ("sesso", "strato1", "strato2")):
            continue
        value = ars_legacy.parse_num(row.get("misura_standardizzata"))
        if value is None:
            value = ars_legacy.parse_num(row.get("misura_grezza"))
        if value is None:
            continue
        period = ars_legacy._norm_period(row.get("anno"))
        code = str(row.get("codice_geografia") or "").strip()
        if code in ars_legacy.TOWNS:
            by_geo.setdefault(ars_legacy.TOWNS[code], {})[period] = float(value)
        elif code.lstrip("0") in TUSCANY_ARS_CODES or str(row.get("geografia") or "").strip().casefold() in {"toscana", "regione toscana"}:
            tuscany[period] = float(value)
        elif "tosc" in str(row.get("geografia") or "").casefold():
            other.add(f"{code} {row.get('geografia')}")
    missing = [g for g in ars_legacy.TOWNS.values() if g not in by_geo]
    if missing:
        raise UpdateError(f"ARS {indicator_id}: serie assenti per {missing}")
    periods = sorted(set.intersection(*(set(v) for v in by_geo.values())), key=ars_legacy._period_key)
    values = {geo: [series[p] for p in periods] for geo, series in by_geo.items()}
    if periods[-1] not in tuscany:
        raise UpdateError(f"ARS {indicator_id}: riga Toscana {periods[-1]} assente; geografie simili: {sorted(other)[:10]}")
    return periods, values, tuscany[periods[-1]]


def update_ars_legacy(metric_key: str, file: Path | None, dry_run: bool) -> Changes:
    snapshot = load(ARS_LEGACY)
    entry = snapshot["indicators"][metric_key]
    payload = fetch(entry["exportUrl"], file)
    raw = ars_csv(payload)
    periods, values, tuscany = ars_series(entry["indicatorId"], raw)
    site = load(SITE)
    metric = site["metrics"][metric_key]
    published = probes.norm_period(metric["meta"]["year"])
    if published not in periods:
        raise UpdateError(f"{metric_key}: il periodo pubblicato {published} non è più alla fonte ({periods[-3:]})")
    if periods[-1] != published:
        # Un periodo nuovo cambia etichette, domande verificate e test: va pubblicato con una PR dedicata.
        raise UpdateError(f"{metric_key}: la fonte pubblica {periods[-1]} (pubblicato {published}); questo aggiornatore gestisce le revisioni dello stesso periodo")
    changes = Changes()
    old_periods = entry["periods"]
    if periods[: len(old_periods)] != old_periods:
        raise UpdateError(f"{metric_key}: periodi storici cambiati alla fonte {old_periods} → {periods}")
    for geo, series in values.items():
        for period, old, new in zip(periods, entry["values"][geo], series):
            if not math.isclose(old, new, rel_tol=0, abs_tol=1e-9):
                changes.note(f"snapshot {geo} {period}", old, new)
    entry["values"] = values
    entry["periods"] = periods
    entry["sourceFile"] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    unit_label = "ogni 1.000" if metric["meta"].get("unit") == "per1000" else "ogni 100.000"
    for row in metric["rows"]:
        new = round(values[row["town"]][-1] + 1e-12, 2)
        changes.note(f"catalogo {row['town']} {published}", row["value"], new)
        row["value"] = row["benchmarkValue"] = new
        row["formatted"] = f"{it_number(new, 2)} {unit_label}"
    aggregate = round(values["Versilia"][-1] + 1e-12, 2)
    changes.note(f"catalogo Zona Versilia {published}", metric["aggregate"]["value"], aggregate)
    metric["aggregate"]["value"] = aggregate
    benchmark = metric["meta"].get("benchmark")
    if isinstance(benchmark, dict) and "tuscany" in benchmark:
        new = round(tuscany + 1e-12, 2)
        changes.note(f"catalogo Toscana {published}", benchmark["tuscany"], new)
        benchmark["tuscany"] = new
    if not dry_run:
        save(ARS_LEGACY, snapshot, compact=True)
        save(SITE, site)
    return changes


# ------------------------------------------------------------------ Istat P2: mobilità residenziale

def p2_rows(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if not probes.is_zip(payload):
        raise UpdateError("il file P2 non è uno ZIP")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".csv", ".txt"))]
        if len(names) != 1:
            raise UpdateError(f"archivio P2 inatteso: {names}")
        text = archive.read(names[0]).decode("utf-8-sig")
    parsed = list(csv.reader(io.StringIO(text), delimiter=";"))
    headers = [c.strip() for c in parsed[1]]
    rows = [dict(zip(headers, r + [""] * (len(headers) - len(r)))) for r in parsed[2:] if r]
    return headers, rows


def mobility_counts(headers: list[str], rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    h = demo.p2_mobility_headers(headers)
    out = {}
    for row in rows:
        code = demo.code_of(row)
        if code in TOWN_CODES:
            if code in out:
                raise UpdateError(f"P2: Comune {code} duplicato")
            out[code] = {key: demo.num(row.get(col)) for key, col in h.items()}
    if set(out) != set(TOWN_CODES):
        raise UpdateError(f"P2: Comuni trovati {sorted(out)} su 7")
    return out


def flows(counts: dict[str, float], key: str) -> tuple[float, float]:
    if key == MOBILITY[0]:
        return counts["internalIn"], counts["internalOut"]
    if key == MOBILITY[1]:
        return counts["foreignIn"], counts["foreignOut"]
    return counts["internalIn"] + counts["foreignIn"], counts["internalOut"] + counts["foreignOut"]


def append_point(series: dict[str, Any], year: int, value: float) -> None:
    years = list(series["years"])
    if year in years:
        series["values"][years.index(year)] = value
    elif years and year != years[-1] + 1:
        raise UpdateError(f"anno {year} non consecutivo a {years[-1]}")
    else:
        series["years"] = years + [year]
        series["values"] = list(series["values"]) + [value]


def update_istat_mobility(year: int, file: Path | None, dry_run: bool) -> Changes:
    url = f"https://demo.istat.it/data/p2/P2_{year}_it_Comuni.zip"
    headers, rows = p2_rows(fetch(url, file))
    towns = mobility_counts(headers, rows)
    scopes = {}
    for scope, predicate in (("tuscany", demo.pred_tuscany), ("italy", demo.pred_italy)):
        scopes[scope] = demo.aggregate_p2(headers, rows, predicate, "mobility")
    site = load(SITE)
    composite = load(COMPOSITE)
    lotto_a = load(SNAP / "istat-demography-lotto-a-2026-08.json")
    changes = Changes()
    template = ROOT / site["metrics"][MOBILITY[0]]["meta"]["benchmark"]["sourceSnapshot"]
    for key in MOBILITY:
        metric = site["metrics"][key]
        published = int(metric["meta"]["year"])
        if year not in (published, published + 1):
            raise UpdateError(f"{key}: anno {year} non successivo al pubblicato {published}")
        totals = [0.0, 0.0, 0.0]
        population = 0.0
        for row in metric["rows"]:
            counts = towns[row["code"]]
            mean = (counts["jan1"] + counts["dec31"]) / 2
            # La popolazione media deve coincidere con quella del bilancio già pubblicato.
            p02 = probes_one(lotto_a["p02"]["towns"][row["town"]], year)
            if p02 is not None and not math.isclose(p02["meanPopulation"], mean, rel_tol=0, abs_tol=0.5):
                raise UpdateError(f"{row['town']} {year}: popolazione media P2 {mean} ≠ bilancio pubblicato {p02['meanPopulation']}")
            inbound, outbound = flows(counts, key)
            numbers = [inbound, outbound, inbound - outbound]
            rates = [n / mean * 1000 for n in numbers]
            totals = [t + n for t, n in zip(totals, numbers)]
            population += mean
            changes.note(f"{key} {row['town']} saldo {year}", row["value"] if published == year else None, rates[2])
            row["value"] = row["benchmarkValue"] = rates[2]
            if row.get("formatted") is not None:
                row["formatted"] = f"{it_number(rates[2], 1)} ogni 1.000"
            append_point(row["series"], year, rates[2])
            for part, rate, count in zip(row["parts"], rates, numbers):
                part["value"], part["count"] = rate, int(count)
                append_point(row["componentSeries"][part["label"]], year, rate)
        aggregate = metric["aggregate"]
        for part, count in zip(aggregate["parts"], totals):
            part["value"], part["count"] = count / population * 1000, int(count)
        changes.note(f"{key} Versilia saldo {year}", aggregate["value"] if published == year else None, aggregate["parts"][2]["value"])
        aggregate["value"] = aggregate["parts"][2]["value"]
        bench = metric["meta"]["benchmark"]
        for scope, a in scopes.items():
            inbound, outbound = flows(a, key)
            value = (inbound - outbound) / a["meanPopulation"] * 1000
            # Saldo interno nazionale: per costruzione zero (ogni trasferimento interno è un'iscrizione e una cancellazione).
            bench[scope] = 0 if key == MOBILITY[0] and scope == "italy" else value
            changes.note(f"{key} benchmark {scope} {year}", None, bench[scope])
        bench.update(year=str(year), url=url, sourceSnapshot=f"data/source-snapshots/a3-istat-demography-mobility-benchmark-{year}.json")
        metric["meta"]["year"] = str(year)
    composite_text = COMPOSITE.read_text(encoding="utf-8")
    for row in site["metrics"][MOBILITY[0]]["rows"]:
        counts = towns[row["code"]]
        composite_text = composite_flow(composite_text, row["town"], year, int(counts["internalIn"]), int(counts["internalOut"]))
    years_line = re.search(r'("internalResidentialMobility": \{[^}]*?"years": \[)([^\]]*)\]', composite_text)
    years = [int(y) for y in years_line.group(2).split(",")]
    if year not in years:
        composite_text = composite_text[:years_line.start(2)] + years_line.group(2) + f", {year}" + composite_text[years_line.end(2):]
    if json.loads(composite_text)["raw"].keys() != composite["raw"].keys():
        raise UpdateError("snapshot compositi alterato")
    previous = load(template)
    benchmark_snapshot = {
        **previous,
        "version": f"a3-istat-demography-mobility-benchmark-{year}-v1",
        "retrieved": date.today().isoformat(),
        "sourceUrl": url,
        "benchmarks": {k: {**previous["benchmarks"][k], "year": str(year),
                           "tuscany": site["metrics"][k]["meta"]["benchmark"]["tuscany"],
                           "italy": site["metrics"][k]["meta"]["benchmark"]["italy"]} for k in MOBILITY},
        "components": {scope: {k: (int(v) if k != "meanPopulation" else v) for k, v in a.items()} for scope, a in scopes.items()},
        "acquisitionEvidence": {"script": "scripts/update_source_data.py istat-mobility", "sha256": None},
    }
    target = SNAP / f"a3-istat-demography-mobility-benchmark-{year}.json"
    benchmark_snapshot = keep_retrieved(benchmark_snapshot, load(target) if target.exists() else None)
    if not dry_run:
        save(SITE, site)
        COMPOSITE.write_text(composite_text, encoding="utf-8")
        save(target, benchmark_snapshot)
    return changes


# ------------------------------------------------------------------ Istat ASIA-UL: unità locali e addetti

ASIA_SDMX = "https://esploradati.istat.it/SDMXWS/rest/data/IT1,183_1163_DF_DICA_ASIAULP_TERRIFDATA_7,1.0/"
ASIA_PAGE = ("https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0900ENT,1.0/"
             "DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7")
ASIA_QUERIES = {
    "lu": "A..LU.0010.TOTAL?startPeriod={first}&endPeriod={year}",
    "emp": "A..LUEMPDAA.0010.TOTAL?startPeriod={first}&endPeriod={year}",
    "micro": "A..LU.0010.W0_9+TOTAL?startPeriod={year}&endPeriod={year}",
}
ASIA_FIRST = 2018
ASIA_METRICS = ("localUnits", "localEmployees", "employeesPerLocalUnit", "localUnitsChange", "localEmployeesChange", "microUnits")
TUSCANY_PREFIXES = ("045", "046", "047", "048", "049", "050", "051", "052", "053", "100")
SDMX_CSV = "application/vnd.sdmx.data+csv;version=1.0.0"


def sdmx_csv(url: str, file: Path | None) -> bytes:
    """CSV SDMX Istat (l'intestazione Accept sceglie il CSV invece dell'XML)."""
    if file is not None:
        return file.read_bytes()
    import time
    import urllib.request
    errors = []
    for attempt in range(1, 4):
        request = urllib.request.Request(url, headers={"User-Agent": probes.USER_AGENT, "Accept": SDMX_CSV})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001
            errors.append(f"tentativo {attempt}: {error}")
            time.sleep(30 * attempt)
    raise UpdateError(f"{url}: " + " | ".join(errors))


def asia_panel(raw: bytes, data_type: str) -> dict[tuple[str, str], dict[int, float]]:
    """{(area, classe dimensionale): {anno: valore}} per i Comuni (6 cifre), Toscana (ITE1) e Italia (IT)."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not {"REF_AREA", "DATA_TYPE", "TIME_PERIOD", "OBS_VALUE"} <= set(reader.fieldnames or []):
        raise UpdateError(f"ASIA-UL {data_type}: schema CSV inatteso {reader.fieldnames}")
    out: dict[tuple[str, str], dict[int, float]] = {}
    for row in reader:
        if (row.get("DATA_TYPE") or "").strip() != data_type or not (row.get("OBS_VALUE") or "").strip():
            continue
        area = (row.get("REF_AREA") or "").strip()
        if not (re.fullmatch(r"\d{6}", area) or area in {"IT", "ITE1"}):
            continue
        key = (area, (row.get("PERS_EMPL_SIZE_CLASS") or "TOTAL").strip())
        year = int(str(row["TIME_PERIOD"])[:4])
        value = float(row["OBS_VALUE"].replace(",", "."))
        old = out.setdefault(key, {}).get(year)
        if old is not None and not math.isclose(old, value, rel_tol=0, abs_tol=1e-9):
            raise UpdateError(f"ASIA-UL {data_type}: {key} {year} duplicato ({old} ≠ {value})")
        out[key][year] = value
    return out


def asia_scopes(panel: dict[tuple[str, str], dict[int, float]], year: int, size: str = "TOTAL") -> dict[str, float]:
    """Toscana e Italia come somma delle osservazioni comunali ufficiali dello stesso anno."""
    towns = {a: v[year] for (a, s), v in panel.items() if s == size and len(a) == 6 and year in v}
    if len(towns) < 7800:
        raise UpdateError(f"ASIA-UL {year}: copertura comunale insufficiente ({len(towns)})")
    return {"tuscany": sum(v for a, v in towns.items() if a[:3] in TUSCANY_PREFIXES), "italy": sum(towns.values())}


def pct_change(first: float, last: float) -> float:
    if not first:
        raise UpdateError("variazione percentuale da base zero")
    return (last / first - 1) * 100


def update_istat_asia(year: int, folder: Path | None, dry_run: bool) -> Changes:
    years = list(range(ASIA_FIRST, year + 1))
    raws = {name: sdmx_csv(ASIA_SDMX + q.format(first=ASIA_FIRST, year=year), folder / f"{name}.csv" if folder else None)
            for name, q in ASIA_QUERIES.items()}
    lu, emp, micro = asia_panel(raws["lu"], "LU"), asia_panel(raws["emp"], "LUEMPDAA"), asia_panel(raws["micro"], "LU")
    series: dict[str, dict[str, list[float]]] = {}
    for code in TOWN_CODES:
        got = {"lu": lu.get((code, "TOTAL"), {}), "emp": emp.get((code, "TOTAL"), {})}
        missing = [f"{k} {y}" for k, v in got.items() for y in years if y not in v]
        if missing:
            raise UpdateError(f"ASIA-UL {code}: anni assenti {missing}")
        series[code] = {k: [v[y] for y in years] for k, v in got.items()}
        series[code]["micro"] = [micro.get((code, s), {}).get(year) for s in ("W0_9", "TOTAL")]
        if None in series[code]["micro"] or series[code]["micro"][1] != series[code]["lu"][-1]:
            raise UpdateError(f"ASIA-UL {code}: classi dimensionali {year} assenti o incoerenti con il totale")
    scopes = {name: {y: asia_scopes(panel, y) for y in (ASIA_FIRST, year)} for name, panel in (("lu", lu), ("emp", emp))}
    native = {}
    for scope, area in (("tuscany", "ITE1"), ("italy", "IT")):
        w, t = (micro.get((area, s), {}).get(year) for s in ("W0_9", "TOTAL"))
        if w is None or t is None or not math.isclose(t, scopes["lu"][year][scope], rel_tol=0, abs_tol=0.5):
            raise UpdateError(f"ASIA-UL {area} {year}: totale nativo {t} ≠ somma comunale {scopes['lu'][year][scope]}")
        native[scope] = w / t * 100

    site = load(SITE)
    m = {k: site["metrics"][k] for k in ASIA_METRICS}
    published = int(m["localUnits"]["meta"]["year"])
    if year < published:
        raise UpdateError(f"ASIA-UL: anno {year} precedente al pubblicato {published}")
    changes = Changes()
    span, old_span = f"{ASIA_FIRST}–{year}", f"{ASIA_FIRST}–{published}"
    towns_path = f"data/source-snapshots/istat-asia-ul-{year}.json"
    business_path = f"data/source-snapshots/a3-istat-business-benchmark-{year}.json"
    micro_path = f"data/source-snapshots/a3-istat-micro-units-benchmark-{year}.json"
    benchmarks = {
        "localUnits": {scope: scopes["lu"][year][scope] for scope in ("tuscany", "italy")},
        "localEmployees": {scope: round(scopes["emp"][year][scope], 2) for scope in ("tuscany", "italy")},
        "employeesPerLocalUnit": {scope: scopes["emp"][year][scope] / scopes["lu"][year][scope] for scope in ("tuscany", "italy")},
        "localUnitsChange": {scope: pct_change(scopes["lu"][ASIA_FIRST][scope], scopes["lu"][year][scope]) for scope in ("tuscany", "italy")},
        "localEmployeesChange": {scope: pct_change(scopes["emp"][ASIA_FIRST][scope], scopes["emp"][year][scope]) for scope in ("tuscany", "italy")},
        "microUnits": native,
    }
    benchmarks["localUnits"] = {k: int(round(v)) for k, v in benchmarks["localUnits"].items()}

    def town_values(code: str) -> dict[str, Any]:
        s = series[code]
        ratio = [e / u for e, u in zip(s["emp"], s["lu"])]
        return {
            "localUnits": (int(round(s["lu"][-1])), it_number(s["lu"][-1], 0), [int(round(v)) for v in s["lu"]]),
            "localEmployees": (round(s["emp"][-1], 2), it_number(s["emp"][-1], 0) if abs(s["emp"][-1] - round(s["emp"][-1])) < 0.05 else it_number(s["emp"][-1], 1), [round(v, 2) for v in s["emp"]]),
            "employeesPerLocalUnit": (ratio[-1], f"{it_number(ratio[-1], 2)} addetti/UL", ratio),
            "localUnitsChange": (pct_change(s["lu"][0], s["lu"][-1]), None, None),
            "localEmployeesChange": (pct_change(s["emp"][0], s["emp"][-1]), None, None),
            "microUnits": (round(s["micro"][0] / s["micro"][1] * 100, 2), None, None),
        }

    totals = {k: [sum(series[c][k][i] for c in TOWN_CODES) for i in range(len(years))] for k in ("lu", "emp")}
    aggregates = {
        "localUnits": int(round(totals["lu"][-1])),
        "localEmployees": round(totals["emp"][-1], 2),
        "employeesPerLocalUnit": totals["emp"][-1] / totals["lu"][-1],
        "localUnitsChange": pct_change(totals["lu"][0], totals["lu"][-1]),
        "localEmployeesChange": pct_change(totals["emp"][0], totals["emp"][-1]),
        "microUnits": sum(series[c]["micro"][0] for c in TOWN_CODES) / sum(series[c]["micro"][1] for c in TOWN_CODES) * 100,
    }
    population = 0.0
    for key, metric in m.items():
        for row in metric["rows"]:
            value, formatted, values = town_values(row["code"])[key]
            changes.note(f"{key} {row['town']}", row["value"], value)
            if key == "localUnits" and row.get("normalized"):
                pop = row["value"] / row["normalized"]["value"] * 1000
                population += pop
                row["normalized"]["value"] = value / pop * 1000
            row["value"] = row["benchmarkValue"] = value
            row["formatted"] = formatted or f"{it_number(value, 1)}%"
            if values is not None:
                row["series"] = {"years": years, "values": values}
        changes.note(f"{key} Versilia", metric["aggregate"]["value"], aggregates[key])
        metric["aggregate"]["value"] = aggregates[key]
        if key == "localUnits" and metric.get("normalizedAggregate"):
            metric["normalizedAggregate"]["value"] = aggregates[key] / population * 1000
        meta = metric["meta"]
        if key.endswith("Change"):
            for field in ("label", "description", "year"):
                meta[field] = meta[field].replace(old_span, span).replace(f"e il {published}", f"e il {year}")
            metric["method"]["formula"] = metric["method"]["formula"].replace(str(published), str(year))
        else:
            meta["year"] = str(year)
        bench = meta["benchmark"]
        for scope, value in benchmarks[key].items():
            changes.note(f"{key} benchmark {scope}", bench.get(scope), value)
            bench[scope] = value
        bench.update(year=meta["year"], sourceSnapshot=micro_path if key == "microUnits" else business_path, url=ASIA_PAGE)
        metric["method"]["formula"] = re.sub(r"serie 2018–\d{4} acquisita tramite Cruscotto Italia \(AgID\)",
                                             f"serie {span} dal servizio SDMX Istat", metric["method"]["formula"])
        metric["method"]["formula"] = metric["method"]["formula"].replace("; acquisizione tramite Cruscotto Italia (AgID)", "; servizio SDMX Istat")
    sources = {name: {"url": ASIA_SDMX + q.format(first=ASIA_FIRST, year=year), "sha256": hashlib.sha256(raws[name]).hexdigest(), "bytes": len(raws[name])}
               for name, q in ASIA_QUERIES.items()}
    rows = {r["code"]: r for r in m["localUnits"]["rows"]}
    towns_snapshot = {
        "schemaVersion": 1,
        "version": f"istat-asia-ul-{year}-v1",
        "retrieved": date.today().isoformat(),
        "scope": "Sette Comuni della Versilia storica",
        "acquisitionLayer": {"name": "Istat — servizio SDMX esploradati", "url": ASIA_SDMX,
                             "note": "Serie comunali lette direttamente dal servizio SDMX Istat (CSV)."},
        "sources": {"asia": {"owner": "ISTAT", "dataset": "Archivio Statistico Imprese Attive — Unità Locali (ASIA-UL)",
                             "url": ASIA_PAGE, "license": "CC BY 3.0 IT", "years": years, "sdmx": sources}},
        "towns": [{"town": rows[c]["town"], "code": c, "slug": rows[c]["slug"],
                   "asia": {"years": years, "localUnits": [int(round(v)) for v in series[c]["lu"]],
                            "employeesAverageAnnual": [round(v, 2) for v in series[c]["emp"]]}} for c in TOWN_CODES],
        "acquisitionEvidence": {"script": f"scripts/update_source_data.py istat-asia --year {year}"},
    }
    def bench_entry(key: str, unit: str, formula: str) -> dict[str, Any]:
        return {"year": span if key.endswith("Change") else str(year), "unit": unit, "formula": formula, **benchmarks[key]}
    business = {
        "schemaVersion": 1,
        "version": f"a3-istat-business-benchmark-{year}-v1",
        "retrieved": date.today().isoformat(),
        "publisher": "Istat — ASIA Unità Locali",
        "sourceProfileId": "istat-business-annual",
        "candidateState": "ACQUIRED_CANDIDATE",
        "sourceUrl": ASIA_PAGE,
        "retrieval": "Istat SEP SDMX ufficiale",
        "qualityGate": {"status": "PASS", "errors": [], "candidateMetrics": sorted(k for k in benchmarks if k != "microUnits"),
                        "publicSnapshotReconciliation": f"metric-level 7/7 × {ASIA_FIRST}/{year}; Toscana e Italia aggregati dalle stesse osservazioni comunali ufficiali"},
        "benchmarks": {
            "localUnits": bench_entry("localUnits", "number", "unità locali attive"),
            "localUnitsChange": bench_entry("localUnitsChange", "percent", f"((UL {year} / UL {ASIA_FIRST})-1)×100"),
            "localEmployees": bench_entry("localEmployees", "number", "addetti medi annui"),
            "localEmployeesChange": bench_entry("localEmployeesChange", "percent", f"((addetti {year} / addetti {ASIA_FIRST})-1)×100"),
            "employeesPerLocalUnit": bench_entry("employeesPerLocalUnit", "decimal", "addetti medi annui / unità locali"),
        },
        "evidence": {
            "LU": {scope: {str(y): int(round(scopes["lu"][y][scope])) for y in (ASIA_FIRST, year)} for scope in ("tuscany", "italy")},
            "LUEMPDAA": {scope: {str(y): round(scopes["emp"][y][scope], 2) for y in (ASIA_FIRST, year)} for scope in ("tuscany", "italy")},
            "historicalTuscanyMunicipalityCount": {str(y): sum(1 for (a, s), v in lu.items() if s == "TOTAL" and len(a) == 6 and a[:3] in TUSCANY_PREFIXES and y in v)
                                                   for y in (ASIA_FIRST, year)},
        },
        "blocked": {"microUnits": "richiede distribuzione per classe dimensionale ASIA-UL; non inferita dal totale"},
        "acquisitionEvidence": {"script": f"scripts/update_source_data.py istat-asia --year {year}", "sources": sources},
    }
    import acquire_a3_benchmark_istat_business_micro_units as micro_acq
    micro_sources, micro_records = {}, {}
    for area in sorted(micro_acq.AREAS):
        text = sdmx_csv(micro_acq.source_url(area, year), folder / f"micro-{area}.csv" if folder else None).decode("utf-8-sig")
        micro_sources[area] = {"url": micro_acq.source_url(area, year), "csv": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
        micro_records[area] = micro_acq.parse_csv(text, area, year)
    panel, geographies = micro_acq.parse_panel(raws["micro"], year)
    micro_snapshot = {
        "schemaVersion": 1, "publisher": "Istat — ASIA Unità Locali", "sourceProfileId": "istat-business-annual",
        "status": "ACQUIRED_CANDIDATE", "sourceUrl": ASIA_PAGE, "sources": micro_sources, "records": micro_records,
        "benchmarks": {"microUnits": {"year": str(year), "unit": "percent", "formula": "unità locali con 0–9 addetti / unità locali totali × 100",
                                      "tuscany": micro_records["ITE1"]["W0_9"] / micro_records["ITE1"]["TOTAL"] * 100,
                                      "italy": micro_records["IT"]["W0_9"] / micro_records["IT"]["TOTAL"] * 100}},
        "qualityGate": {"status": "PASS", "errors": [], "candidateMetrics": ["microUnits"],
                        "publicSnapshotReconciliation": f"7/7, native LU W0_9 and TOTAL {year}; public rounding at two decimals"},
        "scope": {"note": f"Rapporto tra conteggi ufficiali ASIA-UL {year} W0_9 e TOTAL; aggregati nativi Toscana e Italia, stessa attività economica 0010. Non media delle quote comunali."},
        "municipalPanel": panel,
        "panelSource": {"url": micro_acq.panel_url(year), "sha256": hashlib.sha256(raws["micro"]).hexdigest(), "bytes": len(raws["micro"]),
                        "nativeGeographies": geographies, "municipalities": len(panel),
                        "tuscanyMunicipalities": sum(1 for r in panel if r[0][:3] in TUSCANY_PREFIXES)},
    }
    for scope in ("tuscany", "italy"):
        if micro_snapshot["benchmarks"]["microUnits"][scope] != benchmarks["microUnits"][scope]:
            raise UpdateError(f"ASIA-UL {scope}: quota micro della query per area ≠ pannello")
    if not dry_run:
        save(SITE, site)
        for path, value in ((towns_path, towns_snapshot), (business_path, business), (micro_path, micro_snapshot)):
            target = ROOT / path
            save(target, keep_retrieved(value, load(target) if target.exists() else None) if "retrieved" in value else value)
    return changes


FTTH_PCT = {"ftthCoverageDesi": "copertura_ftth_desi_pct", "ftthCoverage20m": "copertura_ftth_20m_pct"}
FTTH_COUNTS = ("ftthReachedHouseholds", "ftthUnreachedHouseholds")


def ftth_count(key: str, record: dict[str, Any]) -> float | None:
    reached = record["famiglie_ftth"]
    if reached is None:
        return None
    return float(reached if key == "ftthReachedHouseholds" else record["famiglie_residenti"] - reached)


def update_agcom_ftth(folder: Path | None, dry_run: bool) -> Changes:
    """Broadband Map AGCOM: ultima edizione del CSV comunale indicata dal catalogo datato report.js."""
    import agcom_sources
    import acquire_a3_benchmark_agcom_quarterly as bench_acq
    import audit_agcom_primary as ag

    catalogue = fetch(ag.REPORT_SCRIPT_URL, folder / "report.js" if folder else None)
    text = catalogue.decode("utf-8-sig")
    try:
        candidates = ag.dated_primary_candidates(text)
    except ag.base.DataError as error:
        raise UpdateError(str(error)) from error
    if not candidates:
        raise UpdateError("AGCOM: nessuna edizione «Consistenze rilevate al …» con CSV comunale in report.js")
    csv_url, period = candidates[0]
    heading = re.search(r"Consistenze rilevate al " + re.escape(period) + r"[^<]*", text).group(0).strip()
    revision = re.search(r"rev\. del (\d{2}/\d{2}/\d{4})", heading)
    native_old = load(ROOT / agcom_sources.NATIVE)
    published = native_old["agcomAudit"]["dataPeriod"]
    if ag.base.agcom_period(period) < ag.base.agcom_period(published):
        raise UpdateError(f"AGCOM: edizione {period} precedente alla pubblicata {published}")
    body = fetch(csv_url, folder / "comuni.csv" if folder else None)
    try:
        rows = ag.parse_csv(body)
        ag.validate_primary_rows(rows, set(TOWN_CODES))
    except ag.base.DataError as error:
        raise UpdateError(str(error)) from error
    italy, tuscany = bench_acq.scope_rows(rows, False), bench_acq.scope_rows(rows, True)
    if not (7800 <= len(italy) <= 8000 and 270 <= len(tuscany) <= 280):
        raise UpdateError(f"AGCOM: copertura inattesa (Italia {len(italy)}, Toscana {len(tuscany)})")
    label = ag.base.agcom_period_label(period)
    iso = ag.base.agcom_period(period).isoformat()
    native_path = f"data/source-snapshots/agcom-ftth-{iso}.json"
    bench_path = f"data/source-snapshots/a3-agcom-benchmark-{iso}.json"
    benchmarks = {key: {"year": label, "unit": "percent", "formula": "media delle percentuali comunali AGCOM ponderata per famiglie residenti",
                        "tuscany": bench_acq.weighted(tuscany, field), "italy": bench_acq.weighted(italy, field)}
                  for key, field in FTTH_PCT.items()}

    site = load(SITE)
    names = {t["code"]: t["name"] for t in site["towns"]}
    missing = [names[c] for c in TOWN_CODES if rows[c]["famiglie_ftth"] is None]
    available = len(TOWN_CODES) - len(missing)
    changes = Changes()
    for key in (*FTTH_PCT, *FTTH_COUNTS):
        metric = site["metrics"][key]
        for row in metric["rows"]:
            record = rows[row["code"]]
            value = record[FTTH_PCT[key]] if key in FTTH_PCT else ftth_count(key, record)
            changes.note(f"{key} {row['town']}", row["value"], value)
            row["value"] = row["benchmarkValue"] = value
            row["formatted"] = "n.d." if value is None else f"{it_number(value, 1)}%" if key in FTTH_PCT else it_number(value, 0)
        aggregate = metric["aggregate"]
        if key in FTTH_PCT:
            total = math.fsum(rows[c][FTTH_PCT[key]] * rows[c]["famiglie_residenti"] for c in TOWN_CODES) / sum(rows[c]["famiglie_residenti"] for c in TOWN_CODES)
            bench = metric["meta"]["benchmark"]
            for scope in ("tuscany", "italy"):
                changes.note(f"{key} benchmark {scope}", bench.get(scope), benchmarks[key][scope])
                bench[scope] = benchmarks[key][scope]
            bench.update(year=label, url=csv_url, sourceSnapshot=bench_path)
        else:
            total = sum(v for c in TOWN_CODES if (v := ftth_count(key, rows[c])) is not None)
            caveat = re.sub(r" Dato non disponibile per .*$", "", metric["method"]["caveat"])
            if missing:
                aggregate["label"] = f"Totale parziale Versilia ({available}/7)"
                aggregate["note"] = (f"Somma dei valori ufficiali disponibili per {available} Comuni; escluso {', '.join(missing)}, "
                                     "per cui il dato AGCOM non è disponibile.")
                caveat += f" Dato non disponibile per {', '.join(missing)}; nessuna stima effettuata."
            else:
                aggregate["label"] = "Totale Versilia"
                aggregate["note"] = "Somma dei valori ufficiali dei sette Comuni."
            metric["method"].update(caveat=caveat, coverage=f"{available}/7")
        changes.note(f"{key} Versilia", aggregate["value"], total)
        aggregate["value"] = total
        metric["meta"]["year"] = label
        metric["sourceUrl"] = ag.PUBLIC_MAP_URL

    catalogue_sha = hashlib.sha256(catalogue).hexdigest()
    csv_sha = hashlib.sha256(body).hexdigest()
    evidence = {"script": "scripts/update_source_data.py agcom-ftth", "catalogueSha256": catalogue_sha, "csvSha256": csv_sha}
    town_rows = {r["code"]: r for r in site["metrics"]["ftthCoverageDesi"]["rows"]}
    native = {
        "schemaVersion": 1,
        "version": f"agcom-ftth-{iso}-v1",
        "retrieved": date.today().isoformat(),
        "scope": "Sette Comuni della Versilia storica",
        "towns": [{"town": town_rows[c]["town"], "code": c, "slug": town_rows[c]["slug"], "agcom": {"primaryOfficialCsv": rows[c]}}
                  for c in TOWN_CODES],
        "agcomAudit": {
            "sourceType": "primary_official_csv", "dataPeriod": period, "revisionDate": revision.group(1) if revision else None,
            "officialHeading": heading, "periodEvidenceUrl": ag.REPORT_SCRIPT_URL, "publicMapUrl": ag.PUBLIC_MAP_URL,
            "officialCsvUrl": csv_url, "rowCount": len(rows), "missingAbsoluteTowns": missing,
            "rule": "Valori comunali letti dal CSV primario AGCOM; nessun conteggio assoluto ricostruito dalle percentuali.",
        },
        "acquisitionEvidence": evidence,
    }
    benchmark = {
        "schemaVersion": 1,
        "version": f"a3-agcom-benchmark-{iso}-v1",
        "retrieved": date.today().isoformat(),
        "publisher": "AGCOM — Broadband Map, reportistica comunale",
        "sourceProfileId": "agcom-quarterly",
        "candidateState": "ACQUIRED_CANDIDATE",
        "sourceUrl": csv_url,
        "referenceDate": period,
        "qualityGate": {"status": "PASS", "municipalityCountItaly": len(italy), "municipalityCountTuscany": len(tuscany),
                        "publicPercentageReconciliation": "2 metrics × 7/7 PASS", "errors": []},
        "benchmarks": benchmarks,
        "blocked": {key: "benchmark assoluto non pubblicato: celle ufficiali mancanti, nessuna ricostruzione dalle percentuali" for key in FTTH_COUNTS},
        "acquisitionEvidence": evidence,
    }
    if not dry_run:
        save(SITE, site)
        for path, value in ((native_path, native), (bench_path, benchmark)):
            target = ROOT / path
            save(target, keep_retrieved(value, load(target) if target.exists() else None))
    return changes


def composite_flow(text: str, town: str, year: int, inbound: int, outbound: int) -> str:
    """Aggiunge (o sostituisce) l'anno nel flusso interno del Comune mantenendo il formato del file."""
    start = text.index(f'"{town}": {{', text.index('"raw"'))
    array = text.index('"internalResidentialMobility": [', start)
    end = text.index("\n      ]", array)
    lines = text[array:end].split("\n")
    item = f'        {{"year": {year}, "registeredIn": {inbound}, "registeredOut": {outbound}}}'
    if f'"year": {year},' in lines[-1]:
        lines[-1] = item
    else:
        if f'"year": {year - 1},' not in lines[-1]:
            raise UpdateError(f"{town}: flusso interno {year - 1} assente dallo snapshot")
        lines[-1] += ","
        lines.append(item)
    return text[:array] + "\n".join(lines) + text[end:]


def probes_one(items: list[dict[str, Any]], year: int) -> dict[str, Any] | None:
    hits = [i for i in items if int(i["year"]) == year]
    return hits[0] if len(hits) == 1 else None


TOURISM_RATES = {"tourismBedsPer1000": (4, "Posti letto"), "tourismStructuresPer1000": (5, "Strutture ricettive")}


def update_istat_tourism(year: int, file: Path | None, dry_run: bool) -> Changes:
    """Capacità ricettiva Istat (posti letto, strutture) per un anno di riferimento, 7/7 dal pannello nativo."""
    import acquire_a3_benchmark_istat_tourism_annual as capacity

    site = load(SITE)
    published = int(site["metrics"][capacity.METRIC]["meta"]["year"])
    if year < published:
        raise UpdateError(f"Capacità ricettiva: anno {year} precedente al pubblicato {published}")
    body = fetch(capacity.URL, file)
    try:
        snapshot = capacity.build_snapshot(body, site, year)
    except RuntimeError as error:
        raise UpdateError(f"Capacità ricettiva {year}: {error}") from error
    path = f"data/source-snapshots/{capacity.SNAPSHOT_PREFIX}{year}.json"
    by_code = {r[0]: r for r in snapshot["records"]}
    population = {r["code"]: r["value"] for r in site["metrics"]["population"]["rows"]}
    if site["metrics"]["population"]["meta"]["year"] != "2026":
        raise UpdateError("Capacità ricettiva: popolazione pubblica non al 1° gennaio 2026")
    changes = Changes()
    scope = (f" Dal {year} il perimetro Istat include anche gli alloggi privati non imprenditoriali: valori non confrontabili con il 2024 e gli anni precedenti."
             if year > 2024 else "")

    def bench(key: str) -> dict[str, Any]:
        b = snapshot["benchmarks"][key]
        return {"year": str(year), "tuscany": b["tuscany"], "italy": b["italy"], "source": snapshot["publisher"],
                "url": snapshot["sourceUrl"], "sourceSnapshot": path, "note": snapshot["scope"]["note"]}

    beds = site["metrics"][capacity.METRIC]
    for row in beds["rows"]:
        value = by_code[row["code"]][4]
        changes.note(f"{capacity.METRIC} {row['town']}", row["value"], value)
        if row.get("series") not in (None, {}):
            raise UpdateError(f"Capacità ricettiva {row['town']}: serie pubblicata da rivedere prima del cambio di perimetro")
        row.update(value=value, formatted=it_number(value, 0), benchmarkValue=value)
        row["normalized"]["value"] = value / population[row["code"]] * 1000
    beds["aggregate"]["value"] = sum(r["value"] for r in beds["rows"])
    beds["meta"].update(year=str(year), benchmark=bench(capacity.METRIC))
    if scope:
        beds["method"]["caveat"] = "Non trasformare dati di stock o struttura in giudizi di performance; mantenere la denominazione della fonte." + scope
    for key, (column, label) in TOURISM_RATES.items():
        metric = site["metrics"][key]
        for row in metric["rows"]:
            value = by_code[row["code"]][column] / population[row["code"]] * 1000
            changes.note(f"{key} {row['town']}", round(row["value"], 4), round(value, 4))
            row.update(value=value, benchmarkValue=value)
        total = sum(by_code[c][column] for c in population)
        metric["aggregate"]["value"] = total / sum(population.values()) * 1000
        noun = label.lower()
        metric["meta"].update(year=str(year), description=f"{label} Istat {year} ogni 1.000 residenti al 1° gennaio 2026.", benchmark=bench(key))
        metric["meta"]["sourceMeta"].update(snapshot=path, note=f"Conteggi Istat {year} riconciliati 7/7 sul pannello comunale nativo; popolazione al 1° gennaio 2026.")
        metric["method"].update(formula=f"{noun} Istat {year} / popolazione residente al 1° gennaio 2026 × 1.000",
                                caveat=f"Capacità ricettiva {year} rapportata alla popolazione al 1° gennaio 2026, come nei valori comunali pubblicati.{scope or ' Il perimetro Istat 2024 non include gli alloggi privati non imprenditoriali aggiunti nel 2025.'} Indicatore di struttura, non di performance.")
    try:
        for key in capacity.METRICS:
            capacity.validate_snapshot(site["metrics"][key], snapshot, site["metrics"]["population"])
    except RuntimeError as error:
        raise UpdateError(f"Capacità ricettiva {year}: {error}") from error
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py istat-tourism --year {year}", "archiveUrl": capacity.URL}
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot, compact=True)
    return changes


# ------------------------------------------------------------------ Banca d'Italia: sportelli bancari

def update_bdi_branches(year: int, folder: Path | None, dry_run: bool) -> Changes:
    """Sportelli bancari dalla Lista succursali banche (GIAVA): scrive lo snapshot riconciliato.

    L'indicatore `bankBranchesPer1000` entra nel catalogo effettivo in build
    (`materialize_bank_branches.py`), come gli altri indicatori nati dopo il catalogo canonico.
    """
    import bank_branches as bb
    import materialize_bank_branches as mat

    site = load(SITE)
    old_path = None
    try:
        old_path = mat.latest_snapshot(ROOT)
    except RuntimeError:
        pass
    old = load(ROOT / old_path) if old_path else None
    if old and year < old["years"][-1]:
        raise UpdateError(f"Sportelli bancari: anno {year} precedente al pubblicato {old['years'][-1]}")
    pop_rows = site["metrics"]["population"]["rows"]
    towns = {r["code"]: dict(zip(r["series"]["years"], r["series"]["values"])) for r in pop_rows}
    bench_path = ROOT / f"data/source-snapshots/a3-istat-demography-benchmark-{year + 1}.json"
    if not bench_path.exists():
        raise UpdateError(f"Sportelli bancari: popolazione Toscana/Italia al 1° gennaio {year + 1} non disponibile")
    scopes = load(bench_path)["benchmarks"]["population"]
    try:
        archive = (folder / "succursali.zip").read_bytes() if folder else bb.fetch(bb.URL)
        localities = (folder / "localita.zip").read_bytes() if folder else bb.fetch(bb.LOC_URL)
        snapshot = bb.build_snapshot(year, archive, localities, {"towns": towns, "tuscany": scopes["tuscany"],
                                                                  "italy": scopes["italy"], "year": scopes["year"]})
        mat.validate(snapshot, pop_rows)
    except (bb.BranchError, RuntimeError, KeyError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Sportelli bancari {year}: {error}") from error
    path = f"{bb.SNAPSHOT_PREFIX}{year}.json"
    metric = bb.build_metric(snapshot, pop_rows, path)
    previous = bb.build_metric(old, pop_rows, old_path) if old and old["years"][-1] == year else None
    before = {r["code"]: round(r["value"], 4) for r in (previous or {}).get("rows", [])}
    changes = Changes()
    for row in metric["rows"]:
        changes.note(f"{bb.METRIC} {row['town']}", before.get(row["code"]), round(row["value"], 4))
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py bdi-branches --year {year}"}
    if not dry_run:
        save(ROOT / path, snapshot)
    return changes


# ------------------------------------------------------------------ ACI: serie del parco autovetture

def update_aci_vehicles_history(dry_run: bool) -> Changes:
    """Serie 2018–2025 di motorizzazione e quota Euro 0–3 dagli archivi ACI; ultimo anno = valore pubblicato."""
    import vehicles_history as vh

    site = load(SITE)
    population = {r["code"]: dict(zip(r["series"]["years"], r["series"]["values"])) for r in site["metrics"]["population"]["rows"]}
    current = {k: {r["code"]: r["value"] for r in site["metrics"][k]["rows"]} for k in ("motorization", "pollutingCars")}
    try:
        snapshot = vh.build_snapshot(probes.http_fetch, population, current)
    except (vh.VehiclesError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Serie parco autovetture: {error}") from error
    changes = Changes()
    for key, towns in snapshot["series"].items():
        for code, values in towns.items():
            changes.note(f"{key} {code} {snapshot['years'][0]}", None, values[0])
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py aci-vehicles-history"}
    if not dry_run:
        save(ROOT / vh.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ SIOPE: confronto Toscana di incassi e saldo di cassa

def update_siope_cash_benchmarks(year: int, dry_run: bool, fetch=None) -> Changes:
    """Toscana per incassi e saldo di cassa per residente; 7/7 riconciliati, ≥90% dei residenti coperti."""
    import acquire_a3_benchmark_siope_candidates as siope
    import siope_cash_benchmarks as cb

    if year != 2025:
        raise UpdateError("Confronto cassa SIOPE: dump regionali fissati per il 2025")
    site = load(SITE)
    history = load(ROOT / "data/source-snapshots/siope-history-v1.6.0.json")
    published = {k: {r["code"]: r["value"] for r in site["metrics"][k]["rows"]} for k in cb.METRICS}
    codes = {r["town"]: r["code"] for r in site["metrics"][cb.METRICS[0]]["rows"]}
    residents = {codes[t]: v[str(year)]["population_resident"] for t, v in history["raw"].items()}

    def fetcher(url: str) -> bytes:
        if fetch:
            return fetch(url)
        if url in (siope.ENTRATA, siope.SPESA):  # dump CSV da ~100 MB: stessa sessione requests dell'acquisizione A3
            import requests
            return siope.get_blob(requests.Session(), url)
        return probes.http_fetch(url)

    try:
        snapshot = cb.build_snapshot(year, fetcher, siope.parse, {"entrata": siope.ENTRATA, "spesa": siope.SPESA}, published, residents)
    except (cb.CashBenchmarkError, RuntimeError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Confronto cassa SIOPE: {error}") from error
    changes = Changes()
    for metric, entries in snapshot["benchmarks"].items():
        changes.note(f"{metric} Toscana {year}", None, entries["tuscany"].get("value"))
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py siope-cash-benchmarks --year {year}"}
    if not dry_run:
        save(ROOT / cb.SNAPSHOT.format(year=year), snapshot)
    return changes


# ------------------------------------------------------------------ MEF: confronto Toscana/Italia dell'addizionale comunale IRPEF

def update_irpef_benchmarks(year: int, dry_run: bool, fetch=None) -> Changes:
    """Toscana e Italia per i tre scenari dell'addizionale comunale IRPEF; 7/7 riconciliati, ≥90% dei residenti coperti."""
    import irpef_benchmarks as ib

    site = load(SITE)
    metric = site["metrics"][ib.METRIC]
    if str(metric["meta"]["year"]) != str(year):
        raise UpdateError(f"Confronto addizionale IRPEF: anno pubblicato {metric['meta']['year']} ≠ {year}")
    published = {r["code"]: [p["value"] for p in r["parts"]] for r in metric["rows"]}
    try:
        snapshot = ib.build_snapshot(year, fetch or probes.http_fetch, published)
    except (ib.IrpefBenchmarkError, RuntimeError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Confronto addizionale IRPEF: {error}") from error
    changes = Changes()
    for income, scopes in snapshot["benchmarks"].items():
        for scope, entry in scopes.items():
            changes.note(f"{income} € {scope} {year} (copertura {entry['populationShare']:.1%})", None, entry.get("value"))
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py mef-irpef-benchmarks --year {year}"}
    if not dry_run:
        save(ROOT / ib.SNAPSHOT.format(year=year), snapshot)
    return changes


# ------------------------------------------------------------------ MEF: serie delle fasce di reddito

def update_income_distribution_history(dry_run: bool, fetch=None) -> Changes:
    """Serie delle quote di dichiaranti nelle quattro fasce dai file comunali MEF annuali; ultimo anno = quote pubblicate."""
    import os

    import income_distribution_history as idh
    import taxpayers_history as tx

    def fetcher(url: str) -> bytes:
        try:
            raw = (fetch or probes.http_fetch)(url)
        except probes.ProbeError as error:
            if error.reason == "not_found":
                raise tx.Unavailable(url) from error
            raise
        if not raw.startswith(b"PK"):
            raise tx.Unavailable(url)
        return raw

    site = load(SITE)
    metric = site["metrics"][idh.METRIC]
    published = {r["code"]: [p["value"] for p in r["parts"]] for r in metric["rows"]}
    try:
        snapshot = idh.build_snapshot(fetcher, published, int(metric["meta"]["year"]))
    except (idh.IncomeDistributionError, tx.TaxpayersError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie fasce di reddito: {error}") from error
    changes = Changes()
    for code, series in snapshot["series"].items():
        changes.note(f"{idh.METRIC} {code} {snapshot['years'][0]}–{snapshot['years'][-1]}", None, series[0][0])
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py mef-income-distribution-history",
                                       "where": "runner GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else "fuori dalla CI"}
    if not dry_run:
        save(ROOT / idh.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ OMI: serie semestrale delle quotazioni

def update_omi_history(dry_run: bool, session: Any = None, deadline: float | None = None) -> Changes:
    """Serie semestrale delle medie OMI per Comune, solo con le stesse zone del semestre pubblicato.

    Riprende i Comuni già letti da uno snapshot INCOMPLETE dello stesso semestre (la consultazione
    rallenta dopo molte richieste): basta rilanciare la richiesta finché lo snapshot è PASS.
    """
    import os

    import omi_history as oh
    import update_omi as omi

    path = ROOT / oh.SNAPSHOT
    previous = load(path) if path.exists() else None
    try:
        snapshot = oh.build_snapshot(session or omi.Session(), load(SITE), previous, deadline)
    except (oh.OmiHistoryError, omi.OmiError, KeyError, ValueError) as error:
        raise UpdateError(f"Serie OMI: {error}") from error
    changes = Changes()
    if snapshot["qualityGate"]["status"] != "PASS":
        print(f"Serie OMI incompleta: {snapshot['qualityGate']['note']}; rilanciare la richiesta omiHistory per continuare")
    for code, town in snapshot["towns"].items():
        changes.note(f"OMI {town['town']} semestri", None, f"{town['semesters'][0]}–{town['semesters'][-1]}")
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py omi-history",
                                       "where": "runner GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else
                                       "fuori dalla CI: la consultazione OMI limita le richieste dai runner GitHub (2 semestri in 50 minuti)"}
    if not dry_run:
        save(ROOT / oh.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ OpenBDAP: rendiconti già pubblicati

def update_openbdap_refresh(dry_run: bool, fetch=None) -> Changes:
    """Riscarica gli archivi toscani dei rendiconti 2019–2025 e applica le ritrasmissioni dei sette Comuni."""
    import openbdap_refresh as orf

    def get(url: str) -> bytes:
        return (fetch or probes.http_fetch)(url)

    site = load(SITE)
    snapshot = load(ROOT / orf.SNAPSHOT)
    try:
        diffs, metrics, _ = orf.run(get, snapshot, site)
    except (orf.RefreshError, RuntimeError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Rendiconti OpenBDAP: {error}") from error
    changes = Changes()
    for d in diffs:
        changes.note(f"{d['town']} {d['year']} {d['field']}", d["old"], d["new"])
    if diffs:
        print("Indicatori ricalcolati: " + ", ".join(metrics))
    if diffs and not dry_run:
        save(ROOT / orf.SNAPSHOT, snapshot)
        save(SITE, site)
    return changes


# ------------------------------------------------------------------ ISPRA e Regione Toscana: serie annuali (chiusura storici)

def _where() -> str:
    import os
    return "runner GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else "fuori dalla CI"


def update_waste_cost_history(dry_run: bool, fetch=None) -> Changes:
    """Serie del costo del servizio rifiuti per abitante (ISPRA CTOTab), solo righe comunali; ultimo anno = pubblicato."""
    import waste_cost_history as wh

    def get(url: str) -> str:
        return (fetch or probes.http_fetch)(url).decode("utf-8", errors="replace")

    metric = load(SITE)["metrics"][wh.METRIC]
    try:
        snapshot = wh.build_snapshot(get, {r["town"]: r["value"] for r in metric["rows"]}, int(metric["meta"]["year"]))
    except (wh.WasteHistoryError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie costo rifiuti: {error}") from error
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py ispra-waste-cost-history", "where": _where()}
    changes = Changes()
    changes.note(f"{wh.METRIC} anni", None, f"{snapshot['years'][0]}–{snapshot['years'][-1]}")
    if not dry_run:
        save(ROOT / wh.SNAPSHOT, snapshot)
    return changes


def update_seasonality_history(dry_run: bool, fetch=None) -> Changes:
    """Serie della concentrazione turistica nei tre mesi principali dai file regionali mensili."""
    import seasonality_history as sh
    try:
        snapshot = sh.build_snapshot(fetch or probes.http_fetch, load(SITE))
    except (sh.SeasonalityError, RuntimeError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie stagionalità: {error}") from error
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py tourism-seasonality-history", "where": _where()}
    changes = Changes()
    changes.note(f"{sh.METRIC} anni", None, f"{snapshot['years'][0]}–{snapshot['years'][-1]}")
    if not dry_run:
        save(ROOT / sh.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ MEF: serie dell'addizionale comunale IRPEF

def update_irpef_history(dry_run: bool, fetch=None) -> Changes:
    """Serie degli importi dell'addizionale nei tre scenari dagli elenchi MEF annuali; ultimo anno = valori pubblicati."""
    import os

    import irpef_history as ih

    def fetcher(url: str) -> bytes:
        try:
            return (fetch or probes.http_fetch)(url)
        except probes.ProbeError as error:
            if error.reason == "not_found":
                raise ih.Unavailable(url) from error
            raise

    site = load(SITE)
    metric = site["metrics"][ih.METRIC]
    published = {r["code"]: [p["value"] for p in r["parts"]] for r in metric["rows"]}
    try:
        snapshot = ih.build_snapshot(fetcher, published, int(metric["meta"]["year"]))
    except (ih.IrpefHistoryError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie addizionale IRPEF: {error}") from error
    changes = Changes()
    for code, series in snapshot["series"].items():
        changes.note(f"{ih.METRIC} {code} {snapshot['years'][0]}–{snapshot['years'][-1]}", None, series["20000"][0])
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py mef-irpef-history",
                                       "where": "runner GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else "fuori dalla CI"}
    if not dry_run:
        save(ROOT / ih.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ Istat ASIA-UL: serie della quota di micro unità locali

def update_asia_micro_units_history(dry_run: bool, fetch=None) -> Changes:
    """Serie 2018–ultimo anno della quota di unità locali con 0–9 addetti; totali = serie delle unità locali pubblicata."""
    import micro_units_history as mu

    site = load(SITE)
    current = {r["code"]: r["value"] for r in site["metrics"][mu.METRIC]["rows"]}
    local_units = {r["code"]: dict(zip(r["series"]["years"], r["series"]["values"])) for r in site["metrics"]["localUnits"]["rows"]}
    last = int(site["metrics"][mu.METRIC]["meta"]["year"])
    try:
        snapshot = mu.build_snapshot(fetch or (lambda url: sdmx_csv(url, None)), current, local_units, last)
    except (mu.MicroUnitsError, KeyError, ValueError) as error:
        raise UpdateError(f"Serie micro unità: {error}") from error
    changes = Changes()
    for code, values in snapshot["series"].items():
        changes.note(f"{mu.METRIC} {code} {snapshot['years'][0]}", None, values[0])
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py asia-micro-units-history"}
    if not dry_run:
        save(ROOT / mu.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ MIM: serie di alunni, classi e tempo pieno

def update_mim_students_history(dry_run: bool, fetch=None) -> Changes:
    """Serie per anno scolastico di alunni, alunni per classe e tempo pieno; ultimo anno = valori pubblicati."""
    import school_history as sh

    site = load(SITE)
    current = {k: {r["code"]: r["value"] for r in site["metrics"][k]["rows"]} for k in sh.KEYS}
    last = int(re.search(r"(20\d\d)/\d\d", site["metrics"]["schoolStudents"]["meta"]["year"]).group(1))
    try:
        snapshot = sh.build_snapshot(fetch or probes.http_fetch, current, last)
    except (sh.SchoolError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie alunni MIM: {error}") from error
    changes = Changes()
    for key, towns in snapshot["series"].items():
        for code, values in towns.items():
            changes.note(f"{key} {code} {snapshot['schoolYears'][0]}", None, round(values[0], 4))
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py mim-students-history"}
    if not dry_run:
        save(ROOT / sh.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ Regione Toscana: serie dei servizi per la prima infanzia

def update_infancy_history(dry_run: bool, fetch=None) -> Changes:
    """Serie della ricettività potenziale per la prima infanzia; anno corrente = componenti pubblicati."""
    import infancy_history as ih

    site = load(SITE)
    metric = site["metrics"][ih.METRIC]
    last = int(metric["meta"]["year"][:4])
    current = {r["code"]: {k: r[k] for k in ("potentialCapacity", "children3to36Months")} for r in metric["rows"]}
    try:
        snapshot = ih.build_snapshot(fetch or probes.http_fetch, current, last)
    except (ih.InfancyError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie prima infanzia: {error}") from error
    changes = Changes()
    for code, values in snapshot["series"].items():
        changes.note(f"{ih.METRIC} {code} {snapshot['schoolYears'][0]}", None, round(values[0], 4))
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py toscana-infancy-history"}
    if not dry_run:
        save(ROOT / ih.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ MEF: confronto IMU seconda casa (Toscana)

def update_imu_benchmark(year: int, scope: str, dry_run: bool, fetch=None, reuse_lists: bool = False,
                         deadline: float | None = None) -> Changes:
    """Aliquota IMU di una seconda casa vuota dai prospetti MEF di ogni Comune dell'ambito; media pesata per i residenti."""
    import imu_benchmarks as imb
    import irpef_benchmarks as ib
    import probe_mef_fiscal as mef

    def get(url: str) -> bytes:
        # Istat (elenco dei Comuni, POSAS) con le attese lunghe del confronto IRPEF; i prospetti con il fetch MEF.
        if fetch:
            return fetch(url)
        return mef.fetch(url) if url.startswith(mef.BASE) else probes.http_fetch(url)
    try:
        if scope == "italia":
            # Nessuno scaricamento: unisce i quattro gruppi già acquisiti (stessi elenco Istat e POSAS).
            parts = {}
            for name in imb.ITALY_GROUPS:
                path = ROOT / imb.SNAPSHOT.format(year=year, scope=name)
                if not path.exists():
                    raise imb.ImuBenchmarkError(f"gruppo {name} non ancora acquisito ({path.name})")
                parts[name] = json.loads(path.read_text(encoding="utf-8"))
            snapshot = imb.combine(year, parts)
        else:
            path = ROOT / imb.SNAPSHOT.format(year=year, scope=scope)
            previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            snapshot = imb.build_snapshot(year, get, lambda raw: mef.pdf_text(raw)[0], scope=scope, previous=previous,
                                           reuse_lists=reuse_lists, deadline=imb.DEADLINE if deadline is None else deadline)
    except (imb.ImuBenchmarkError, ib.IrpefBenchmarkError, RuntimeError) as error:
        raise UpdateError(f"Confronto IMU: {error}") from error
    if snapshot["qualityGate"]["status"] != "PASS":
        raise UpdateError(f"Confronto IMU: {snapshot['qualityGate']['note']}")
    changes = Changes()
    b = snapshot["benchmark"]
    changes.note(f"{imb.METRIC} {scope} {year}", None, b["value"])
    changes.note(f"{imb.METRIC} {scope} Comuni letti", None, f"{b['municipalities']}/{b['municipalitiesTotal']} ({b['populationShare']:.1%})")
    import os
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py mef-imu-benchmark --year {year} --scope {scope}",
                                       "where": "runner GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else
                                       "fuori dalla CI: il MEF limita le richieste dai runner GitHub dopo circa 100 Comuni"
                                       + ("; elenchi Istat/POSAS dallo snapshot scaricato in CI" if reuse_lists else "")}
    if not dry_run:
        save(ROOT / imb.SNAPSHOT.format(year=year, scope=scope), snapshot)
    return changes


# ------------------------------------------------------------------ Ministero della Salute: serie delle farmacie

def update_pharmacy_history(dry_run: bool, fetch=None) -> Changes:
    """Sedi di farmacia al 31 dicembre 2019–2025 dal file ministeriale corrente; 2025 = conteggi pubblicati."""
    import pharmacy_history as ph

    get = fetch or (lambda url: probes.http_fetch("LEGACYTLS " + url))

    def check(url: str) -> bytes | None:
        try:
            return get(url)
        except probes.ProbeError as error:
            if error.reason == "not_found":
                return None
            raise

    published = ph.published_counts(load(ROOT / ph.PUBLISHED))
    try:
        snapshot = ph.build_snapshot(get, published, check)
    except (ph.PharmacyError, KeyError, ValueError, probes.ProbeError) as error:
        raise UpdateError(f"Serie farmacie: {error}") from error
    changes = Changes()
    for code, values in snapshot["counts"].items():
        changes.note(f"{ph.METRIC} {code} {snapshot['years'][0]}", None, values[0])
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py salute-pharmacies-history"}
    if not dry_run:
        save(ROOT / ph.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ MEF/Istat: serie dei contribuenti ogni 100 maggiorenni

def update_mef_taxpayers_history(dry_run: bool, fetch=None) -> Changes:
    """Serie per anno d'imposta dei contribuenti MEF su residenti 18+ (POSAS a due anni); ultimo anno = valore pubblicato."""
    import taxpayers_history as tx

    def fetcher(url: str) -> bytes:
        try:
            raw = (fetch or probes.http_fetch)(url)
        except probes.ProbeError as error:
            if error.reason == "not_found":
                raise tx.Unavailable(url) from error
            raise
        if not raw.startswith(b"PK"):
            raise tx.Unavailable(url)
        return raw

    site = load(SITE)
    metric = site["metrics"][tx.METRIC]
    last = int(re.search(r"a\.i\. (20\d\d)", metric["meta"]["year"]).group(1))
    current = {r["code"]: {k: r[k] for k in ("value", "taxpayers", "adultPopulation2026")} for r in metric["rows"]}
    try:
        snapshot = tx.build_snapshot(fetcher, current, last)
    except (tx.TaxpayersError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Serie contribuenti: {error}") from error
    changes = Changes()
    for code, values in snapshot["series"].items():
        changes.note(f"{tx.METRIC} {code} {snapshot['years'][0]}", None, round(values[0], 4))
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py mef-taxpayers-history"}
    if not dry_run:
        save(ROOT / tx.SNAPSHOT, snapshot)
    return changes


# ------------------------------------------------------------------ Istat: componenti per famiglia (serie)

def update_istat_famiglie(file: Path | None, dry_run: bool) -> Changes:
    """Serie comunale del numero medio di componenti per famiglia dal workbook «A misura di Comune · Famiglie»."""
    import household_size_history as hh

    raw = file.read_bytes() if file else probes.http_fetch(hh.URL)
    try:
        snapshot = hh.build_snapshot(raw)
    except (hh.HouseholdError, KeyError, ValueError) as error:
        raise UpdateError(f"Componenti per famiglia: {error}") from error
    path = f"{hh.SNAPSHOT_PREFIX}{snapshot['years'][-1]}.json"
    previous = load(ROOT / path) if (ROOT / path).exists() else None
    changes = Changes()
    for code, t in snapshot["towns"].items():
        before = previous["towns"][code]["size"][-1] if previous else None
        changes.note(f"{hh.METRIC} {t['town']}", None if before is None else round(before, 4), round(t["size"][-1], 4))
    snapshot["acquisitionEvidence"] = {"script": "scripts/update_source_data.py istat-famiglie"}
    if not dry_run:
        save(ROOT / path, snapshot)
    return changes


# ------------------------------------------------------------------ OpenBDAP: confronto Toscana/Italia dei rendiconti

def update_openbdap_benchmarks(year: int, dry_run: bool, oc_fetch=None) -> Changes:
    """Scrive lo snapshot dei benchmark Toscana/Italia dei rendiconti comunali (regola copertura ≥ 90% dei residenti)."""
    import openbdap_benchmarks as ob

    site = load(SITE)
    published, towns = {}, {}
    # Sei indicatori nascono in build dallo snapshot bilanci-v139: i valori pubblici vengono da lì.
    v139 = load(ROOT / "data/source-snapshots/bilanci-v139.json")["series"]
    code_of = {r["town"]: r["code"] for r in site["metrics"]["population"]["rows"]}
    for key in ob.METRICS:
        if key not in site["metrics"]:
            published[key] = {code_of[t]: dict(zip(p["years"], p["values"]))[year] for t, p in v139[key]["towns"].items()}
            continue
        metric = site["metrics"][key]
        if str(metric["meta"].get("year")) != str(year):
            raise UpdateError(f"Confronto bilanci: {key} pubblicato per il {metric['meta'].get('year')}, non per il {year}")
        published[key] = {}
        for row in metric["rows"]:
            series = dict(zip(row["series"]["years"], row["series"]["values"]))
            published[key][row["code"]] = series[year]
            towns[row["code"]] = row["town"]
    try:
        snapshot = ob.build_snapshot(year, oc_fetch or ob.fetch, published, towns)
    except (ob.BenchmarkError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Confronto bilanci {year}: {error}") from error
    path = ROOT / f"{ob.SNAPSHOT_PREFIX}{year}.json"
    old = load(path) if path.exists() else {"benchmarks": {}}
    changes = Changes()
    for key, scopes in snapshot["benchmarks"].items():
        for scope, entry in scopes.items():
            before = (old["benchmarks"].get(key, {}).get(scope) or {}).get("value")
            changes.note(f"{key} {scope}", None if before is None else round(before, 4), None if entry["value"] is None else round(entry["value"], 4))
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py openbdap-benchmarks --year {year}"}
    if not dry_run:
        save(path, snapshot)
    return changes


# ------------------------------------------------------------------ OpenCivitas: fabbisogni standard

def update_opencivitas_needs(year: int | None, folder: Path | None, dry_run: bool) -> Changes:
    """Fabbisogni standard (OpenCivitas): scrive lo snapshot dell'annualità indicata o dell'ultima pubblicata.

    Con `--dir` legge `pages/*.html`, `totale.csv` ed `enti.xlsx` già scaricati (prove locali).
    Gli indicatori entrano nel catalogo effettivo in build (`materialize_opencivitas_needs.py`).
    """
    import materialize_opencivitas_needs as mat
    import opencivitas_needs as oc

    site = load(SITE)
    old_path = None
    try:
        old_path = mat.latest_snapshot(ROOT)
    except RuntimeError:
        pass
    old = load(ROOT / old_path) if old_path else None
    try:
        if folder:
            pages = {int(p.stem): p.read_text(encoding="utf-8") for p in sorted((folder / "pages").glob("*.html"))}
        else:
            pages = {0: oc.fetch(oc.PAGE).decode("utf-8", "replace")}
            for n in range(1, oc.LIST_PAGES + 1):
                pages[n] = oc.fetch(oc.LIST_URL.format(page=n)).decode("utf-8", "replace")
        found = oc.discover(pages, year)
        if old and found["year"] < old["year"]:
            raise UpdateError(f"Fabbisogni standard: annualità {found['year']} precedente alla pubblicata {old['year']}")
        raw = (folder / "totale.csv").read_bytes() if folder else oc.fetch(found["dataUrl"])
        enti = (folder / "enti.xlsx").read_bytes() if folder else oc.fetch(found["entiUrl"])
        snapshot = oc.build_snapshot(found, raw, enti)
        pop_rows = site["metrics"]["population"]["rows"]
        mat.validate(snapshot, pop_rows)
    except (oc.NeedsError, RuntimeError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Fabbisogni standard: {error}") from error
    path = f"{oc.SNAPSHOT_PREFIX}{found['year']}.json"
    metrics = oc.build_metrics(snapshot, pop_rows, path)
    previous = oc.build_metrics(old, pop_rows, old_path) if old and old["year"] == found["year"] else {}
    changes = Changes()
    for key, metric in metrics.items():
        before = {r["code"]: round(r["value"], 4) for r in previous.get(key, {}).get("rows", [])}
        for row in metric["rows"]:
            changes.note(f"{key} {row['town']}", before.get(row["code"]), round(row["value"], 4))
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py opencivitas-needs --year {found['year']}"}
    if not dry_run:
        save(ROOT / path, snapshot)
    return changes


def aci_archive_url(year: int) -> str:
    page = probes.http_fetch("https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/").decode("utf-8", errors="replace")
    found = sorted(set(re.findall(rf"href=[\"']([^\"']*Autoritratto[-_]?{year}[-_]Parco[-_]veicolare\.zip)[\"']", page, flags=re.I)))
    if len(found) != 1:
        raise UpdateError(f"Parco veicolare ACI {year}: archivio non trovato una sola volta ({found})")
    return found[0]


def update_aci_vehicles(year: int, file: Path | None, dry_run: bool) -> Changes:
    """Parco autovetture ACI (motorizzazione, quota Euro 0–3) per un'edizione dell'Autoritratto, 7/7 dal pannello nativo."""
    from decimal import Decimal, ROUND_HALF_UP
    import acquire_a3_benchmark_aci_istat_annual as aci

    site = load(SITE)
    published = int(site["metrics"]["motorization"]["meta"]["year"])
    if year <= published:
        raise UpdateError(f"Parco veicolare: anno {year} non successivo al pubblicato {published}")
    url = str(file) if file else aci_archive_url(year)
    body = file.read_bytes() if file else probes.http_fetch(url)
    try:
        snapshot = aci.build_snapshot(body, site, year, url if not file else "https://aci.gov.it/" + file.name)
    except (RuntimeError, KeyError, zipfile.BadZipFile) as error:
        raise UpdateError(f"Parco veicolare {year}: {error}") from error
    path = f"data/source-snapshots/{aci.SNAPSHOT_PREFIX}{year}.json"
    rec = {r[0]: r for r in snapshot["records"]}
    proof = snapshot["municipalReconciliation"]
    pop = {r["code"]: r["value"] for r in site["metrics"]["population"]["rows"]}
    changes = Changes()
    weights = {}
    for key in ("motorization", "pollutingCars"):
        metric = site["metrics"][key]
        for row in metric["rows"]:
            counts = rec[proof[row["code"]]["nativeRow"]][4:]
            weights[row["code"]] = counts[-1]
            raw = Decimal(counts[-1]) / Decimal(pop[row["code"]]) * 1000 if key == "motorization" else Decimal(sum(counts[:4])) / Decimal(counts[-1]) * 100
            value = float(raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            changes.note(f"{key} {row['town']}", row["value"], value)
            row.update(value=value, benchmarkValue=value,
                       formatted=f"{it_number(value, 2)} ogni 1.000" if key == "motorization" else f"{it_number(value, 1)}%")
        b = snapshot["benchmarks"][key]
        metric["meta"].update(year=str(year), benchmark={"year": str(year), "tuscany": b["tuscany"], "italy": b["italy"],
                              "source": snapshot["publisher"], "url": snapshot["sourceUrl"], "sourceSnapshot": path, "note": snapshot["scope"]["note"]})
        for field in ("formula", "caveat"):
            metric["method"][field] = re.sub(rf"\b{published}\b", str(year), metric["method"][field])
    cars = sum(weights.values())
    site["metrics"]["motorization"]["aggregate"]["value"] = cars / sum(pop.values()) * 1000
    site["metrics"]["pollutingCars"]["aggregate"]["value"] = sum(r["value"] * weights[r["code"]] for r in site["metrics"]["pollutingCars"]["rows"]) / cars
    try:
        for key in ("motorization", "pollutingCars"):
            aci.validate_snapshot(site["metrics"][key], snapshot, site["metrics"]["population"])
    except RuntimeError as error:
        raise UpdateError(f"Parco veicolare {year}: {error}") from error
    snapshot["acquisitionEvidence"] = {"script": f"scripts/update_source_data.py aci-vehicles --year {year}"}
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot, compact=True)
    return changes


def update_ispra_soil(year: int, file: Path | None, dry_run: bool) -> Changes:
    """Consumo di suolo ISPRA (stock e flusso annuale) dall'edizione completa dell'anno successivo."""
    import update_ispra_soil as soil
    from openpyxl import load_workbook

    site = load(SITE)
    snapshot = load(soil.SNAPSHOT)
    published = snapshot["landUse"]["years"][-1]
    if year < published:
        raise UpdateError(f"Consumo di suolo: anno {year} precedente al pubblicato {published}")
    url = None if file else soil.edition_url(year)
    body = file.read_bytes() if file else soil.fetch(url)
    try:
        wb = load_workbook(io.BytesIO(body), read_only=True, data_only=True)
        land, change, bench = soil.build(wb, year, soil.populations(site))
    except (soil.SoilError, KeyError, ValueError) as error:
        raise UpdateError(f"Consumo di suolo {year}: {error}") from error
    changes = Changes()
    edition = f"Consumo di suolo, ecosistemi urbani e stato del territorio · edizione {year + 1} · dati comunali 2006–{year}"
    snapshot["landUse"], snapshot["landUseChange"] = land, change
    snapshot["sources"]["ispraSoil"].update(reference=edition, acquisition={
        "url": url or str(file), "sizeBytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    path = f"{soil.BENCH_PREFIX}{year}.json"
    bench_snapshot = {
        "schemaVersion": 2, "version": f"a3-ispra-soil-benchmark-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": "ISPRA — Consumo di suolo", "sourceProfileId": "ispra-consumo-suolo-2024", "candidateState": "ACQUIRED_CANDIDATE",
        "sourceUrl": soil.PAGE, "dataUrl": url or str(file),
        "qualityGate": {"status": "PASS", "publicReconciliation": "2 metrics × 7/7 PASS", "municipalSheet": f"Comuni_{year}",
                        "regionalSheet": f"Regioni_{year}", "italyAggregation": "official-row", "errors": []},
        "benchmarks": bench,
        "acquisitionEvidence": {"script": f"scripts/update_source_data.py ispra-soil --year {year}", "edition": edition},
    }
    for key, family, field, digits in (("landUse", land, "consumedPct", 2), ("landUseChange", change, "netHa", 2)):
        metric = site["metrics"][key]
        years = family["years"]
        for row in metric["rows"]:
            rows = family["municipalities"][row["town"]]["rows"]
            value = round(rows[str(year)][field], digits)
            changes.note(f"{key} {row['town']}", row["value"], value)
            row.update(value=value, benchmarkValue=value,
                       formatted=soil.fmt(value, 1, "%") if key == "landUse" else soil.fmt(value, 2, " ha"))
            if row.get("series"):
                row["series"] = {"years": years, "values": [rows[str(y)][field] for y in years]}
        b = bench[key]
        metric["meta"].update(year=str(year), benchmark={
            "year": str(year), "tuscany": b["tuscany"], "italy": b["italy"], "source": bench_snapshot["publisher"],
            "url": soil.PAGE, "sourceSnapshot": path,
            "note": "Benchmark A3 materializzato da artifact di acquisizione con quality gate metric-level PASS."})
        changes.note(f"{key} Toscana", None, b["tuscany"])
    if not dry_run:
        save(soil.SNAPSHOT, snapshot)
        save(SITE, site)
        save(ROOT / path, bench_snapshot)
    return changes


def update_omi_residential(semester: str, dry_run: bool, reader: Any = None, corrections: list[str] | None = None) -> Changes:
    """Quotazioni residenziali OMI di un semestre nuovo; il semestre pubblicato deve riprodursi identico dalla fonte.

    `corrections`: differenze del catalogo dalla fonte già riviste, come «Viareggio D2» (valori di una zona)
    o «Stazzema» (zonizzazione del Comune). Devono coincidere esattamente con quelle trovate: la fonte prevale
    e ogni correzione resta registrata nella fotografia.
    """
    import update_omi as omi

    site = load(SITE)
    metric = site["metrics"]["omiResidential"]
    try:
        published = omi.label_semester(metric["meta"]["year"])
        omi.semester_code(semester)
        if semester <= published:
            raise UpdateError(f"OMI: semestre {semester} non successivo al pubblicato {published}")
        if reader is None:
            session = omi.Session()
            available = omi.semesters(session)
            if semester not in available or published not in available:
                raise UpdateError(f"OMI: semestre {semester} o {published} non presente nella consultazione")
            codes = omi.town_codes(session)
            reader = lambda period: omi.read_semester(session, period, codes)  # noqa: E731
        raw_replay, raw_fresh = reader(published), reader(semester)
        replay, fresh = ({t: [z for z in zs if z.get("residential", True)] for t, zs in d.items()} for d in (raw_replay, raw_fresh))
    except omi.OmiError as error:
        raise UpdateError(f"OMI {semester}: {error}") from error
    rows = {r["town"]: r for r in metric["rows"]}
    if set(rows) != set(omi.TOWNS) or set(replay) != set(rows) or set(fresh) != set(rows):
        raise UpdateError("OMI: copertura dei Comuni non 7/7")
    same = lambda a, b: math.isclose(a, b, rel_tol=0, abs_tol=1e-9)  # noqa: E731
    found: dict[str, list[str]] = {}
    for town, row in rows.items():
        current = {z["code"]: z for z in row["zones"]}
        source = {z["code"]: z for z in replay[town]}
        if set(current) != set(source):
            found.setdefault(town, []).append(f"{town}: zone {sorted(current)} ≠ fonte {sorted(source)}")
        else:
            for c in current:
                if not same(current[c]["sale"], source[c]["sale"]):
                    found.setdefault(f"{town} {c}", []).append(f"{town} {c} sale: {current[c]['sale']} ≠ {source[c]['sale']}")
                # Il catalogo riporta la locazione al punto medio esatto o arrotondata al decimo: entrambe ammesse.
                if not (same(current[c]["rent"], source[c]["rent"]) or same(current[c]["rent"], source[c].get("rentRounded", source[c]["rent"]))):
                    found.setdefault(f"{town} {c}", []).append(f"{town} {c} rent: {current[c]['rent']} ≠ {source[c]['rent']}")
        # La zonizzazione del semestre nuovo deve coincidere con quella della fonte nel semestre pubblicato.
        if {z["code"] for z in fresh[town]} != set(source):
            found.setdefault(f"{town} zonizzazione {semester}", []).append(
                f"{town}: zonizzazione {semester} {sorted(z['code'] for z in fresh[town])} diversa da {sorted(source)}")
    accepted = set(corrections or [])
    unresolved = {k: v for k, v in found.items() if k not in accepted}
    unused = sorted(accepted - set(found))
    if unresolved or unused:
        lines = [m for v in unresolved.values() for m in v] + [f"correzione non trovata nella fonte: {k}" for k in unused]
        # Diagnostica: tutte le righe lette dalla fonte per le zone in disaccordo.
        for town, zones in raw_replay.items():
            for z in zones:
                if f"{town} {z['code']}" in unresolved or town in unresolved:
                    rows_text = "; ".join(f"{r['type']} {r['state']} {r['saleMin']}-{r['saleMax']}"
                                          + (f" / {r['rentMin']}-{r['rentMax']}" if "rentMin" in r else "") for r in z.get("rows", []))
                    lines.append(f"  fonte {town} {z['code']} ({z.get('sourceLabel', '')}): {rows_text or z.get('reason')}")
        raise UpdateError("OMI: la regola non riproduce il semestre pubblicato o le zone sono cambiate:\n  " + "\n  ".join(lines))
    changes = Changes()
    for town, row in rows.items():
        source = {z["code"]: z for z in fresh[town]}
        if town in accepted:  # zonizzazione corretta: zone ricostruite dalla fonte
            labels = {z["code"]: z.get("label") for z in row["zones"]}
            changes.note(f"{town} zone", sorted(labels), sorted(source))
            row["zones"] = [{"code": z["code"], "label": omi.zone_label(z), "sale": z["sale"], "rent": z["rent"]} for z in fresh[town]]
        else:
            for zone in row["zones"]:
                for field in ("sale", "rent"):
                    changes.note(f"{town} {zone['code']} {field}", zone[field], source[zone["code"]][field])
                    zone[field] = source[zone["code"]][field]
        for field in ("sale", "rent"):
            row[field + "Mean"] = math.fsum(z[field] for z in row["zones"]) / len(row["zones"])
        changes.note(f"{town} media vendita", row["value"], row["saleMean"])
        row.update(value=row["saleMean"], benchmarkValue=row["saleMean"])
    agg = metric["aggregate"]
    for field in ("saleMean", "rentMean"):
        agg[field] = math.fsum(r[field] for r in metric["rows"]) / len(metric["rows"])
    agg["value"] = agg["saleMean"]
    metric["meta"]["year"] = omi.semester_label(semester)
    path = f"data/source-snapshots/{omi.SNAPSHOT_PREFIX}{semester}.json"
    snapshot = {"schemaVersion": 1, "metric": "omiResidential", "semester": semester, "publishedReplayed": published,
                "source": metric["meta"]["source"], "sourceUrl": omi.BASE + "ricerca.htm", "province": omi.PROVINCE,
                "selection": {"type": omi.TYPE, "state": omi.STATE, "destination": "Residenziale",
                              "zoneValue": "punto medio min/max di compravendita e locazione",
                              "excludedZones": "zone senza la riga Abitazioni civili NORMALE"},
                "catalogCorrections": {k: found[k] for k in sorted(accepted)},
                "retrievedAt": date.today().isoformat(),
                "acquisitionEvidence": {"script": f"scripts/update_source_data.py omi-residential --semester {semester}"
                                        + "".join(f" --correction '{k}'" for k in sorted(accepted))},
                "zones": {omi.TOWNS[t]: raw_fresh[t] for t in sorted(raw_fresh)},
                "replay": {omi.TOWNS[t]: raw_replay[t] for t in sorted(raw_replay)}}
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot)
    return changes


# ------------------------------------------------------------------ MIM anagrafe scuole statali (sedi)

MIM_LEAF = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/"
MIM_CATALOG = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Scuole"
MIM_SNAPSHOT = "data/source-snapshots/mim-school-sites-{year}.json"


def mim_registry_name(year: int, catalog: bytes) -> str:
    """Nome del file dell'anagrafe statale per l'a.s. year/year+1, dalla pagina del catalogo MIM."""
    tag = f"{year}{(year + 1) % 100:02d}"
    names = sorted(set(re.findall(rf"SCUANAGRAFESTAT{tag}\d{{8}}\.csv", catalog.decode("utf-8", "replace"))))
    if not names:
        raise UpdateError(f"Anagrafe scuole: file statale dell'a.s. {year}/{(year + 1) % 100:02d} non presente nel catalogo MIM")
    return names[-1]


def mim_school_counts(body: bytes, year: int, towns: dict[str, str]) -> dict[str, Any]:
    """Codici scuola statali univoci per Comune (7/7), Toscana e Italia."""
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";" if text.split("\n", 1)[0].count(";") > text.split("\n", 1)[0].count(",") else ",")
    need = {"ANNOSCOLASTICO", "REGIONE", "PROVINCIA", "CODICESCUOLA", "DESCRIZIONECOMUNE"}
    if not need.issubset(reader.fieldnames or []):
        raise UpdateError("Anagrafe scuole: intestazioni MIM attese mancanti")
    tag = f"{year}{(year + 1) % 100:02d}"
    codes: dict[str, tuple[str, str, str]] = {}
    for row in reader:
        if row["ANNOSCOLASTICO"].strip() != tag:
            raise UpdateError(f"Anagrafe scuole: riga di un altro anno scolastico ({row['ANNOSCOLASTICO']})")
        code = row["CODICESCUOLA"].strip()
        info = (row["REGIONE"].strip().upper(), row["PROVINCIA"].strip().upper(), row["DESCRIZIONECOMUNE"].strip().upper())
        if not code or codes.get(code, info) != info:
            raise UpdateError(f"Anagrafe scuole: codice scuola vuoto o con attributi diversi ({code})")
        codes[code] = info
    municipal = {}
    for istat, name in towns.items():
        found = {c for c, (region, province, town) in codes.items() if region == "TOSCANA" and province == "LUCCA" and town == name}
        if not found:
            raise UpdateError(f"Anagrafe scuole: nessuna sede per {name}")
        municipal[istat] = len(found)
    return {"municipal": municipal, "tuscany": sum(1 for v in codes.values() if v[0] == "TOSCANA"), "italy": len(codes)}


def update_mim_schools(year: int, file: Path | None, dry_run: bool) -> Changes:
    """Sedi scolastiche (anagrafe MIM delle scuole statali) per l'anno scolastico year/year+1."""
    site = load(SITE)
    metric = site["metrics"]["schoolSites"]
    published = int(metric["meta"]["year"])
    if year < published:
        raise UpdateError(f"Sedi scolastiche: a.s. {year}/{(year + 1) % 100:02d} precedente al pubblicato {published}")
    if site["metrics"]["population"]["meta"]["year"] != "2026":
        raise UpdateError("Sedi scolastiche: popolazione pubblica non al 1° gennaio 2026")
    name = file.name if file is not None else mim_registry_name(year, fetch(MIM_CATALOG, None))
    url = MIM_LEAF + name
    body = fetch(url, file)
    towns = {r["code"]: r["town"].upper() for r in metric["rows"]}
    counts = mim_school_counts(body, year, towns)
    population = {r["code"]: r["value"] for r in site["metrics"]["population"]["rows"]}
    school_year = f"{year}/{(year + 1) % 100:02d}"
    changes = Changes()
    for row in metric["rows"]:
        value = counts["municipal"][row["code"]]
        changes.note(f"schoolSites {row['town']}", row["value"], value)
        row.update(value=value, formatted=it_number(value, 0), benchmarkValue=value)
        row["normalized"]["value"] = value / population[row["code"]] * 1000
    total = sum(r["value"] for r in metric["rows"])
    metric["aggregate"]["value"] = total
    metric["normalizedAggregate"]["value"] = total / sum(population[r["code"]] for r in metric["rows"]) * 1000
    path = MIM_SNAPSHOT.format(year=year)
    metric["meta"].update(year=str(year), source="Ministero dell'Istruzione e del Merito — Anagrafe scuole statali",
                          description=f"Codici scuola statali attivi nel Comune, anagrafe MIM a.s. {school_year} (dati al {name[-6:-4]}/{name[-8:-6]}/{name[-12:-8]}).")
    metric["method"].update(type="Elaborazione Osservatorio",
                            formula=f"Codici scuola univoci dell'anagrafe MIM delle scuole statali a.s. {school_year} per Comune; rapporto ogni 1.000 residenti al 1° gennaio 2026.",
                            caveat="Un codice scuola è un punto di erogazione (plesso o indirizzo), non un edificio; scuole paritarie escluse.")
    snapshot = {"schemaVersion": 1, "publisher": "Ministero dell'Istruzione e del Merito", "schoolYear": school_year,
                "sourceUrl": url, "sourceFile": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                "rule": "CODICESCUOLA univoci dell'anagrafe statale; Comune da REGIONE=TOSCANA, PROVINCIA=LUCCA, DESCRIZIONECOMUNE; paritarie escluse.",
                "municipal": counts["municipal"], "tuscany": counts["tuscany"], "italy": counts["italy"],
                "acquisitionEvidence": {"script": f"scripts/update_source_data.py mim-schools --year {year}", "catalogUrl": MIM_CATALOG}}
    changes.note("schoolSites anno", published, year)
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot)
    return changes


# ------------------------------------------------------------------ GAIA qualità dell'acqua potabile

GAIA_URL = "https://www.gaia-spa.it/analisiweb_v2/"
GAIA_TOWN = {"046005": "6", "046013": "19", "046018": "26", "046024": "33", "046028": "39", "046030": "41", "046033": "45"}
GAIA_SNAPSHOT = "data/source-snapshots/gaia-water-quality-{period}.json"
GAIA_CAVEAT = "Valori consigliati e limiti normativi sono mantenuti distinti. Le stringhe con < o > non vengono trasformate."


class _GaiaPage(html.parser.HTMLParser):
    """Titolo (h4), periodo (h6) e righe della tabella #campioni di una pagina località GAIA."""

    def __init__(self) -> None:
        super().__init__()
        self.title, self.period, self.rows = "", "", []
        self._tag, self._text, self._row, self._cell, self._hint = None, [], None, None, ""
        self._root, self._depth = None, 0  # elemento con id «campioni» (tabella o contenitore), come «#campioni tbody tr»

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("h4", "h6"):
            self._tag, self._text = tag, []
        if self._root is None and attrs.get("id") == "campioni":
            self._root, self._depth = tag, 1
            return
        if self._root and tag == self._root:
            self._depth += 1
        if self._root and tag == "tr":
            self._row = []
        elif self._row is not None and tag == "td":
            self._cell, self._hint = [], ""
        elif self._cell is not None and attrs.get("title") and not self._hint:
            self._hint = attrs["title"]

    def handle_endtag(self, tag):
        if tag == self._tag:
            text = re.sub(r"\s+", " ", "".join(self._text)).strip()
            if tag == "h4" and not self.title:
                self.title = text
            if tag == "h6" and "Periodo di riferimento" in text:
                self.period = re.sub(r"^Periodo di riferimento\s*:\s*", "", text, flags=re.I)
            self._tag = None
        elif tag == "td" and self._cell is not None:
            self._row.append((re.sub(r"\s+", " ", "".join(self._cell)).strip(), re.sub(r"\s+", " ", self._hint).strip()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if len(self._row) >= 4:
                self.rows.append(self._row)
            self._row = None
        if self._root and tag == self._root:
            self._depth -= 1
            if self._depth == 0:
                self._root = False

    def handle_data(self, data):
        if self._tag:
            self._text.append(data)
        if self._cell is not None:
            self._cell.append(data)


def gaia_label(period: str) -> str:
    """«2026-S1» → «1° semestre 2026»."""
    match = re.fullmatch(r"(20\d\d)-S([12])", period)
    if not match:
        raise UpdateError(f"GAIA: semestre non valido {period!r} (atteso AAAA-S1/S2)")
    return f"{match.group(2)}° semestre {match.group(1)}"


def gaia_order(label: str) -> tuple[int, int]:
    half, year = label.split("° semestre ")
    return int(year), int(half)


_GAIA_SESSION = None


def gaia_fetch(locality: dict[str, Any]) -> bytes:
    """Imposta la sessione GAIA sulla località e scarica la pagina dei valori medi (come l'acquisizione storica)."""
    _GAIA_SESSION.post(GAIA_URL + "php/ajax.inc.php", data={
        "codice_comune": GAIA_TOWN[locality["townCode"]], "codice_prelievo": locality["sampleCode"],
        "codice_prelievo1": locality["sampleCode2"], "codice_area": "1", "op": "set_session"}, timeout=30).raise_for_status()
    return gaia_get(locality["url"])


def gaia_get(url: str) -> bytes:
    global _GAIA_SESSION
    import requests
    if _GAIA_SESSION is None:
        _GAIA_SESSION = requests.Session()
        _GAIA_SESSION.headers.update({"User-Agent": "OsservatorioVersilia/aggiornamento (+https://osservatorioversilia.it)"})
    response = _GAIA_SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def gaia_index(body: bytes) -> dict[tuple[str, str], str]:
    """(codice_comune, codice_prelievo) → codice_prelievo1 dai pulsanti località dell'indice GAIA (area 1)."""
    found: dict[tuple[str, str], str] = {}
    for tag in re.findall(r"<[^>]*\bbtn_localita\b[^>]*>", body.decode("utf-8", "replace")):
        data = dict(re.findall(r'data-(codice_[a-z0-9]+)\s*=\s*"([^"]*)"', tag))
        if data.get("codice_area") == "1" and data.get("codice_comune") in GAIA_TOWN.values():
            found[(data["codice_comune"], data["codice_prelievo"])] = data.get("codice_prelievo1", "0")
    return found


def gaia_unit_fix(value: str, definition: dict[str, str]) -> str | None:
    """Valore in µg/L scritto nella colonna mg/L: oltre 10 volte il limite e, diviso per 1.000, entro il limite."""
    if definition["unit"] != "(mg/L)":
        return None
    try:
        number = float(value.replace(",", "."))
        limit = float(definition["reference"].replace(".", "").replace(",", "."))
    except ValueError:
        return None
    if number > 10 * limit and number / 1000 <= limit:
        return f"{number / 1000:.3f}"
    return None


def gaia_parse(body: bytes, label: str, definitions: list[dict[str, str]], where: str) -> tuple[str, list[str]]:
    page = _GaiaPage()
    page.feed(body.decode("utf-8", "replace"))
    if not page.title or page.title.strip("- ") == "" or "Notice</b>" in body.decode("utf-8", "replace"):
        raise UpdateError(f"GAIA {where}: località non impostata nella sessione GAIA (titolo {page.title!r})")
    if page.period.casefold() != label.casefold():
        raise UpdateError(f"GAIA {where}: {label} non presente (la pagina riporta {page.period!r})")
    if len(page.rows) != len(definitions):
        text = body.decode("utf-8", "replace")
        at = text.find("campioni")
        around = re.sub(r"\s+", " ", text[max(0, at - 300):at + 900])
        scripts = re.findall(r"""(?:url|src)\s*[:=]\s*["']([^"']+)""", text)[:12]
        raise UpdateError(f"GAIA {where}: {len(page.rows)} parametri, attesi {len(definitions)} "
                          f"(id campioni {'presente' if at >= 0 else 'assente'}, {text.count('<tr')} righe <tr>, {len(body)} byte; "
                          f"titolo {page.title!r}; intorno a campioni: {around!r}; script: {scripts})")
    for row, definition in zip(page.rows, definitions):
        got = {"name": row[0][0], "unit": row[1][0], "reference": row[3][0]}
        if got != {k: definition[k] for k in ("name", "unit", "reference")}:
            raise UpdateError(f"GAIA {where}: parametro cambiato {got} (pubblicato {definition['name']})")
    return page.title, [row[2][0] for row in page.rows]


def update_gaia_water(period: str, pages: Path | None, dry_run: bool) -> Changes:
    """Valori medi GAIA per le stesse 70 località e 17 parametri, semestre nuovo."""
    site = load(SITE)
    metric = site["metrics"]["drinkingWaterQuality"]
    label = gaia_label(period)
    published = metric["meta"]["year"]
    if gaia_order(label) < gaia_order(published):
        raise UpdateError(f"GAIA: {label} precedente al pubblicato {published}")
    definitions = metric["parameterDefinitions"]
    changes = Changes()
    # Il secondo codice di prelievo di una località può cambiare tra un semestre e l'altro
    # (nel 2026 Torcigliano, Pietrasanta, Minazzana, Farnocchia): si prende dall'indice GAIA,
    # la località resta la stessa (Comune e primo codice) e l'insieme deve restare identico.
    index_body = (pages / "index.html").read_bytes() if pages is not None else gaia_get(GAIA_URL)
    index = gaia_index(index_body)
    known = {(GAIA_TOWN[l["townCode"]], l["sampleCode"]) for r in metric["rows"] for l in r["localities"]}
    if set(index) != known:
        raise UpdateError(f"GAIA: località dell'indice diverse da quelle pubblicate "
                          f"(nuove {sorted(set(index) - known)}, mancanti {sorted(known - set(index))})")
    localities = []
    corrections: list[dict[str, str]] = []
    for row in metric["rows"]:
        for locality in row["localities"]:
            where = f"{row['town']} · {locality['name']}"
            second = index[(GAIA_TOWN[locality["townCode"]], locality["sampleCode"])]
            if second != locality["sampleCode2"]:
                changes.note(f"{where} · secondo codice", locality["sampleCode2"], second)
                locality.update(sampleCode2=second, url=f"{GAIA_URL}campioni/{locality['sampleCode']}/{second}")
            if pages is not None:
                body = (pages / f"{locality['sampleCode']}_{locality['sampleCode2']}.html").read_bytes()
            else:
                body = gaia_fetch(locality)
            title, values = gaia_parse(body, label, definitions, where)
            for i, definition in enumerate(definitions):
                fixed = gaia_unit_fix(values[i], definition)
                if fixed is not None:
                    corrections.append({"sampleCode": locality["sampleCode"], "locality": locality["name"], "parameter": definition["name"],
                                        "published": values[i], "converted": fixed})
                    values[i] = fixed
            if title and title != locality["title"]:
                changes.note(f"titolo {locality['sampleCode']}", locality["title"], title)
            for name, old, new in zip((d["name"] for d in definitions), locality["values"], values):
                changes.note(f"{where} · {name}", old, new)
            locality.update(title=title or locality["title"], period=label.replace("semestre", "Semestre"), values=values)
            localities.append(locality)
    path = GAIA_SNAPSHOT.format(period=period)
    extraction = json.dumps(localities, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    snapshot = {"schemaVersion": 1, "period": label, "acquiredAt": date.today().isoformat(),
                "sources": {"gaia": {"url": GAIA_URL, "extractionSha256": hashlib.sha256(extraction).hexdigest(),
                                     "rule": "Stesse 70 località e 17 parametri pubblicati; valori medi verbatim dalla pagina della località, salvo i valori in µg/L nella colonna mg/L convertiti (unitCorrections)."}},
                "drinkingWaterQuality": {"parameterDefinitions": definitions, "localities": localities},
                "unitCorrections": corrections,
                "acquisitionEvidence": {"script": f"scripts/update_source_data.py gaia-water --period {period}"}}
    changes.note("drinkingWaterQuality periodo", published, label)
    metric["meta"]["year"] = label
    metric["meta"]["sourceMeta"]["snapshot"] = path
    metric["meta"]["sourceMeta"]["unitCorrections"] = len(corrections)
    if corrections:
        names = sorted({c["parameter"] for c in corrections})
        changes.note("correzioni di unità", 0, len(corrections))
        metric["meta"]["sourceMeta"]["unitCorrectionNote"] = (
            f"{label[0].upper()}{label[1:]}: in {len(corrections)} valori ({', '.join(names)}) GAIA riporta il dato in µg/L nella colonna mg/L; "
            "convertiti in mg/L dividendo per 1.000. Elenco nello snapshot (unitCorrections).")
    else:
        metric["meta"]["sourceMeta"].pop("unitCorrectionNote", None)
    metric["method"]["caveat"] = " ".join(x for x in (GAIA_CAVEAT, metric["meta"]["sourceMeta"].get("unitCorrectionNote")) if x)
    metric["method"]["snapshot"] = path
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot)
    return changes


# ------------------------------------------------------------------ E.R.P. Lucca: morosità cumulata

ERP_PDF = "https://at.erplucca.it/upload/guido/1/estratto%20assemblea%20Soci%20Bilancio_{year}.pdf"
ERP_TOWNS = {"046005": r"Camaiore", "046013": r"Forte\s+dei\s+Marmi", "046018": r"Massarosa", "046024": r"Pietrasanta",
             "046028": r"Seravezza", "046030": r"Stazzema", "046033": r"Viareggio"}
_IT_AMOUNT = r"(\d{1,3}(?:\.\d{3})*,\d{2})"


def erp_amount(text: str) -> float:
    return float(text.replace(".", "").replace(",", "."))


def erp_pdf_text(body: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(body)).pages)


def erp_table(text: str, year: int) -> dict[str, tuple[float, float, float]]:
    """(emesso, morosità, % stampata) per Comune dal prospetto «COMUNI EMESSO dal 1/4/2004 al 31/12/AAAA MOROSITA’ %»."""
    flat = re.sub(r"\s+", " ", text)
    if not re.search(rf"EMESSO\s+dal\s+1/4/2004\s+al\s+31/12/{year}", flat, re.I):
        raise UpdateError(f"ERP Lucca {year}: intestazione del prospetto morosità per Comune non trovata")
    found = {}
    for code, name in ERP_TOWNS.items():
        hits = re.findall(rf"\b{name}\s+{_IT_AMOUNT}\s+{_IT_AMOUNT}\s+(\d{{1,2}},\d{{1,2}})\s*%", flat, re.I)
        if len(hits) != 1:
            raise UpdateError(f"ERP Lucca {year}: riga di {name.replace(chr(92) + 's+', ' ')} trovata {len(hits)} volte nel prospetto")
        issued, arrears, printed = erp_amount(hits[0][0]), erp_amount(hits[0][1]), float(hits[0][2].replace(",", "."))
        if issued <= 0 or arrears < 0 or abs(round(arrears / issued * 100, 2) - printed) > 0.011:
            raise UpdateError(f"ERP Lucca {year}: {code} percentuale stampata {printed} non riconcilia con gli importi")
        found[code] = (issued, arrears, printed)
    return found


def update_erp_arrears(year: int, file: Path | None, dry_run: bool) -> Changes:
    """Aggiunge l'esercizio year allo snapshot ERP Lucca e ricostruisce la metrica con lo stesso builder."""
    import math
    import materialize_erp_arrears_v125 as erp
    site = load(SITE)
    metric = site["metrics"]["erpArrears"]
    current_path = metric["meta"]["sourceMeta"]["snapshot"]
    snapshot = load(ROOT / current_path)
    years = snapshot["scope"]["years"]
    if year != years[-1] + 1:
        raise UpdateError(f"ERP Lucca: esercizio {year} non successivo all'ultimo pubblicato {years[-1]}")
    body = fetch(ERP_PDF.format(year=year), file)
    table = erp_table(erp_pdf_text(body), year)
    changes = Changes()
    for code, (issued, arrears, printed) in table.items():
        rate = round(arrears / issued * 100, 4)
        snapshot["rows"][code]["values"].append({"year": year, "issued": issued, "arrears": arrears, "rate": rate})
        changes.note(f"erpArrears {snapshot['rows'][code]['town']} {year}", "—", f"{round(rate, 2)}%")
    issued = round(math.fsum(v[0] for v in table.values()), 2)
    arrears = round(math.fsum(v[1] for v in table.values()), 2)
    snapshot["aggregate"]["values"].append({"year": year, "issued": issued, "arrears": arrears, "rate": round(arrears / issued * 100, 4)})
    snapshot["scope"]["years"] = years + [year]
    snapshot["sourceDocuments"].append({"year": year, "file": f"estratto assemblea Soci Bilancio_{year}.pdf",
                                        "sha256": hashlib.sha256(body).hexdigest()})
    snapshot["retrieved"] = date.today().isoformat()
    path = erp.snapshot_path(snapshot)
    site["metrics"]["erpArrears"] = erp.build_metric(snapshot)
    changes.note("erpArrears anno", years[-1], year)
    if not dry_run:
        save(SITE, site)
        save(ROOT / path, snapshot)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="updater", required=True)
    a = sub.add_parser("ars-legacy")
    a.add_argument("--metric", required=True, choices=sorted(load(ARS_LEGACY)["indicators"]))
    m = sub.add_parser("istat-mobility")
    m.add_argument("--year", type=int, required=True)
    for p in (a, m):
        p.add_argument("--file", type=Path)
    u = sub.add_parser("istat-asia")
    u.add_argument("--year", type=int, required=True)
    u.add_argument("--dir", type=Path, help="cartella con lu.csv, emp.csv e micro.csv già scaricati")
    t = sub.add_parser("istat-tourism")
    t.add_argument("--year", type=int, required=True)
    t.add_argument("--file", type=Path, help="archivio zip Istat già scaricato")
    v = sub.add_parser("aci-vehicles")
    v.add_argument("--year", type=int, required=True)
    v.add_argument("--file", type=Path, help="archivio ACI «Parco veicolare» già scaricato")
    o = sub.add_parser("ispra-soil")
    o.add_argument("--year", type=int, required=True)
    o.add_argument("--file", type=Path, help="foglio ISPRA Com_Prov_Reg_Naz già scaricato")
    q = sub.add_parser("omi-residential")
    q.add_argument("--semester", required=True, help="semestre nuovo, es. 2026-S1")
    q.add_argument("--correction", action="append", default=[],
                   help="differenza del catalogo dalla fonte già rivista: «Comune ZONA» o «Comune» (zonizzazione)")
    e = sub.add_parser("erp-arrears")
    e.add_argument("--year", type=int, required=True, help="esercizio di bilancio, es. 2025")
    e.add_argument("--file", type=Path, help="PDF «estratto assemblea Soci Bilancio_AAAA» già scaricato")
    w = sub.add_parser("gaia-water")
    w.add_argument("--period", required=True, help="semestre GAIA, es. 2026-S1")
    w.add_argument("--pages", type=Path, help="cartella con le pagine località già scaricate (CODICE_CODICE2.html)")
    k = sub.add_parser("mim-schools")
    k.add_argument("--year", type=int, required=True, help="primo anno dell'a.s., es. 2026 per 2026/27")
    k.add_argument("--file", type=Path, help="CSV SCUANAGRAFESTAT già scaricato (nome originale)")
    f = sub.add_parser("agcom-ftth")
    f.add_argument("--dir", type=Path, help="cartella con report.js e comuni.csv già scaricati")
    for p in (a, m, u, f, t, o, v, q, k, w, e):
        p.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("mef-fiscal-probe", help="sonda dei documenti MEF IRPEF/IMU/TARI (non modifica il catalogo)")
    s.add_argument("--year", type=int, required=True)
    g = sub.add_parser("source-probe", help="sonda della struttura di una pagina o di un file (non modifica il catalogo)")
    g.add_argument("--name", required=True)
    g.add_argument("--url", required=True)
    g.add_argument("--follow", help="espressione regolare dei collegamenti da analizzare")
    g.add_argument("--post", action="append", default=[], help="passo successivo URL::campi (POST, stessa sessione); ripetibile")
    g.add_argument("--match", help="CSV: espressione regolare delle righe da riportare (al posto dei Comuni della Versilia)")
    bb_p = sub.add_parser("bdi-branches", help="sportelli bancari Banca d'Italia (GIAVA)")
    bb_p.add_argument("--year", type=int, required=True, help="anno concluso, es. 2025 (sportelli al 31 dicembre)")
    bb_p.add_argument("--dir", type=Path, help="cartella con succursali.zip e localita.zip già scaricati")
    bb_p.add_argument("--dry-run", action="store_true")
    sub.add_parser("bdi-branches-probe", help="sonda degli sportelli Banca d'Italia (non modifica il catalogo)")
    vh_p = sub.add_parser("aci-vehicles-history", help="serie storica di motorizzazione e quota Euro 0–3 (archivi ACI)")
    vh_p.add_argument("--dry-run", action="store_true")
    sc2_p = sub.add_parser("siope-cash-benchmarks", help="confronto Toscana di incassi e saldo di cassa SIOPE per residente")
    sc2_p.add_argument("--year", type=int, required=True)
    sc2_p.add_argument("--dry-run", action="store_true")
    ir_p = sub.add_parser("mef-irpef-benchmarks", help="confronto Toscana/Italia dell'addizionale comunale IRPEF negli scenari di reddito")
    ir_p.add_argument("--year", type=int, required=True)
    ir_p.add_argument("--dry-run", action="store_true")
    ih_p = sub.add_parser("toscana-infancy-history", help="serie della ricettività potenziale per la prima infanzia")
    imu_p = sub.add_parser("mef-imu-benchmark", help="confronto IMU seconda casa dai prospetti MEF (Toscana o Italia)")
    imu_p.add_argument("--year", type=int, required=True)
    imu_p.add_argument("--scope", choices=("toscana", "italia-1", "italia-2", "italia-3", "italia-4", "italia"), default="toscana",
                       help="toscana; italia-1…4 = gruppi di regioni (una corsa ciascuno); italia = unione dei quattro gruppi")
    imu_p.add_argument("--dry-run", action="store_true")
    imu_p.add_argument("--reuse-lists", action="store_true", help="elenchi Istat/POSAS dallo snapshot del gruppo (lettura fuori dalla CI)")
    imu_p.add_argument("--deadline", type=float, help="secondi per i prospetti (predefinito 65 minuti)")
    idh_p = sub.add_parser("mef-income-distribution-history", help="serie delle quote di dichiaranti per fascia di reddito (file comunali MEF)")
    idh_p.add_argument("--dry-run", action="store_true")
    omh_p = sub.add_parser("omi-history", help="serie semestrale delle quotazioni OMI con le stesse zone del semestre pubblicato")
    omh_p.add_argument("--dry-run", action="store_true")
    omh_p.add_argument("--deadline", type=float, default=3000.0, help="secondi oltre i quali i Comuni restanti passano alla corsa successiva")
    sub.add_parser("openbdap-refresh", help="rendiconti OpenBDAP già pubblicati: applica le ritrasmissioni dei sette Comuni").add_argument("--dry-run", action="store_true")
    for name, text in (("ispra-waste-cost-history", "serie del costo del servizio rifiuti (ISPRA)"),
                       ("tourism-seasonality-history", "serie della stagionalità turistica (Regione Toscana)")):
        sub.add_parser(name, help=text).add_argument("--dry-run", action="store_true")
    irh_p = sub.add_parser("mef-irpef-history", help="serie dell'addizionale comunale IRPEF negli scenari di reddito (elenchi MEF)")
    irh_p.add_argument("--dry-run", action="store_true")
    ph_p = sub.add_parser("salute-pharmacies-history", help="serie delle farmacie ogni 1.000 residenti (Ministero della Salute)")
    ph_p.add_argument("--dry-run", action="store_true")
    ih_p.add_argument("--dry-run", action="store_true")
    mu_p = sub.add_parser("asia-micro-units-history", help="serie Istat ASIA-UL della quota di unità locali con 0–9 addetti")
    mu_p.add_argument("--dry-run", action="store_true")
    sc_p = sub.add_parser("mim-students-history", help="serie MIM di alunni, alunni per classe e tempo pieno della primaria")
    sc_p.add_argument("--dry-run", action="store_true")
    tx_p = sub.add_parser("mef-taxpayers-history", help="serie dei contribuenti MEF ogni 100 maggiorenni (MEF + Istat POSAS)")
    tx_p.add_argument("--dry-run", action="store_true")
    hh_p = sub.add_parser("istat-famiglie", help="serie comunale del numero medio di componenti per famiglia (Istat)")
    hh_p.add_argument("--file", type=Path, help="workbook 3-Famiglie.xlsx già scaricato")
    hh_p.add_argument("--dry-run", action="store_true")
    ob_p = sub.add_parser("openbdap-benchmarks", help="confronto Toscana/Italia dei rendiconti comunali OpenBDAP")
    ob_p.add_argument("--year", type=int, required=True)
    ob_p.add_argument("--dry-run", action="store_true")
    oc_p = sub.add_parser("opencivitas-needs", help="fabbisogni standard dei Comuni (OpenCivitas)")
    oc_p.add_argument("--year", type=int, help="annualità OpenCivitas, es. 2023 (predefinita: l'ultima pubblicata)")
    oc_p.add_argument("--dir", type=Path, help="cartella con pages/*.html, totale.csv ed enti.xlsx già scaricati")
    oc_p.add_argument("--dry-run", action="store_true")
    x = sub.add_parser("sdmx-probe", help="sonda di un flusso SDMX Istat (non modifica il catalogo)")
    x.add_argument("--name", required=True)
    x.add_argument("--flow", help="identificativo del flusso (oppure --find)")
    x.add_argument("--find", help="espressione regolare: elenca i flussi Istat corrispondenti")
    x.add_argument("--key", default="all")
    x.add_argument("--start")
    args = parser.parse_args()
    try:
        if args.updater == "bdi-branches":
            update_bdi_branches(args.year, args.dir, args.dry_run).report(f"Sportelli bancari {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "aci-vehicles-history":
            update_aci_vehicles_history(args.dry_run).report("Serie parco autovetture:")
        elif args.updater == "siope-cash-benchmarks":
            update_siope_cash_benchmarks(args.year, args.dry_run).report("Confronto cassa SIOPE:")
        elif args.updater == "mef-irpef-benchmarks":
            update_irpef_benchmarks(args.year, args.dry_run).report("Confronto addizionale IRPEF:")
        elif args.updater == "toscana-infancy-history":
            update_infancy_history(args.dry_run).report("Serie prima infanzia:")
        elif args.updater == "mef-imu-benchmark":
            update_imu_benchmark(args.year, args.scope, args.dry_run, reuse_lists=args.reuse_lists, deadline=args.deadline).report("Confronto IMU:")
        elif args.updater == "mef-income-distribution-history":
            update_income_distribution_history(args.dry_run).report("Serie fasce di reddito:")
        elif args.updater == "omi-history":
            update_omi_history(args.dry_run, deadline=args.deadline).report("Serie OMI:")
        elif args.updater == "openbdap-refresh":
            update_openbdap_refresh(args.dry_run).report("Rendiconti OpenBDAP:")
        elif args.updater == "ispra-waste-cost-history":
            update_waste_cost_history(args.dry_run).report("Serie costo rifiuti:")
        elif args.updater == "tourism-seasonality-history":
            update_seasonality_history(args.dry_run).report("Serie stagionalità:")
        elif args.updater == "mef-irpef-history":
            update_irpef_history(args.dry_run).report("Serie addizionale IRPEF:")
        elif args.updater == "salute-pharmacies-history":
            update_pharmacy_history(args.dry_run).report("Serie farmacie:")
        elif args.updater == "asia-micro-units-history":
            update_asia_micro_units_history(args.dry_run).report("Serie micro unità:")
        elif args.updater == "mim-students-history":
            update_mim_students_history(args.dry_run).report("Serie alunni MIM:")
        elif args.updater == "mef-taxpayers-history":
            update_mef_taxpayers_history(args.dry_run).report("Serie contribuenti:")
        elif args.updater == "istat-famiglie":
            update_istat_famiglie(args.file, args.dry_run).report("Componenti per famiglia:")
        elif args.updater == "openbdap-benchmarks":
            update_openbdap_benchmarks(args.year, args.dry_run, oc_fetch=None).report(f"Confronto bilanci {args.year}:")
        elif args.updater == "opencivitas-needs":
            update_opencivitas_needs(args.year, args.dir, args.dry_run).report(f"Fabbisogni standard{' ' + str(args.year) if args.year else ''}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "bdi-branches-probe":
            import probe_bdi_branches

            probe_bdi_branches.run()
        elif args.updater == "sdmx-probe":
            import probe_sdmx

            if args.find:
                probe_sdmx.find(args.name, args.find)
            else:
                probe_sdmx.run(args.name, args.flow, args.key, args.start)
        elif args.updater == "source-probe":
            import probe_source_files

            probe_source_files.run(args.name, args.url, args.follow, args.post, args.match)
        elif args.updater == "mef-fiscal-probe":
            import probe_mef_fiscal

            probe_mef_fiscal.run(args.year)
        elif args.updater == "aci-vehicles":
            update_aci_vehicles(args.year, args.file, args.dry_run).report(f"Parco veicolare {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "omi-residential":
            update_omi_residential(args.semester, args.dry_run, corrections=args.correction).report(f"Quotazioni OMI {args.semester}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "ispra-soil":
            update_ispra_soil(args.year, args.file, args.dry_run).report(f"Consumo di suolo {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "istat-tourism":
            update_istat_tourism(args.year, args.file, args.dry_run).report(f"Capacità ricettiva {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "erp-arrears":
            update_erp_arrears(args.year, args.file, args.dry_run).report(f"Morosità ERP {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "gaia-water":
            update_gaia_water(args.period, args.pages, args.dry_run).report(f"Acqua potabile GAIA {args.period}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "mim-schools":
            update_mim_schools(args.year, args.file, args.dry_run).report(f"Sedi scolastiche a.s. {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "agcom-ftth":
            update_agcom_ftth(args.dir, args.dry_run).report(f"AGCOM FTTH{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "ars-legacy":
            update_ars_legacy(args.metric, args.file, args.dry_run).report(f"ARS {args.metric}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "istat-asia":
            update_istat_asia(args.year, args.dir, args.dry_run).report(f"ASIA-UL {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        else:
            update_istat_mobility(args.year, args.file, args.dry_run).report(f"Mobilità residenziale {args.year}{' (prova a secco)' if args.dry_run else ''}:")
    except (UpdateError, probes.ProbeError) as error:
        print(f"Aggiornamento rifiutato: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
