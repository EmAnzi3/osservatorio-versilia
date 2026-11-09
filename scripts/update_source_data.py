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
    python scripts/update_source_data.py source-probe --name NOME --url URL [--follow REGEX]

Con `--dry-run` mostra le differenze senza scrivere. I server GitHub raggiungono
fonti che altrove non rispondono: il workflow «Aggiorna dati dalla fonte» esegue
questi comandi e committa il risultato sul ramo della PR.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
    if year <= published:
        raise UpdateError(f"Consumo di suolo: anno {year} non successivo al pubblicato {published}")
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
    f = sub.add_parser("agcom-ftth")
    f.add_argument("--dir", type=Path, help="cartella con report.js e comuni.csv già scaricati")
    for p in (a, m, u, f, t, o, v):
        p.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("mef-fiscal-probe", help="sonda dei documenti MEF IRPEF/IMU/TARI (non modifica il catalogo)")
    s.add_argument("--year", type=int, required=True)
    g = sub.add_parser("source-probe", help="sonda della struttura di una pagina o di un file (non modifica il catalogo)")
    g.add_argument("--name", required=True)
    g.add_argument("--url", required=True)
    g.add_argument("--follow", help="espressione regolare dei collegamenti da analizzare")
    args = parser.parse_args()
    try:
        if args.updater == "source-probe":
            import probe_source_files

            probe_source_files.run(args.name, args.url, args.follow)
        elif args.updater == "mef-fiscal-probe":
            import probe_mef_fiscal

            probe_mef_fiscal.run(args.year)
        elif args.updater == "aci-vehicles":
            update_aci_vehicles(args.year, args.file, args.dry_run).report(f"Parco veicolare {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "ispra-soil":
            update_ispra_soil(args.year, args.file, args.dry_run).report(f"Consumo di suolo {args.year}{' (prova a secco)' if args.dry_run else ''}:")
        elif args.updater == "istat-tourism":
            update_istat_tourism(args.year, args.file, args.dry_run).report(f"Capacità ricettiva {args.year}{' (prova a secco)' if args.dry_run else ''}:")
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
