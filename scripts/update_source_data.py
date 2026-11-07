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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="updater", required=True)
    a = sub.add_parser("ars-legacy")
    a.add_argument("--metric", required=True, choices=sorted(load(ARS_LEGACY)["indicators"]))
    m = sub.add_parser("istat-mobility")
    m.add_argument("--year", type=int, required=True)
    for p in (a, m):
        p.add_argument("--file", type=Path)
        p.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.updater == "ars-legacy":
            update_ars_legacy(args.metric, args.file, args.dry_run).report(f"ARS {args.metric}{' (prova a secco)' if args.dry_run else ''}:")
        else:
            update_istat_mobility(args.year, args.file, args.dry_run).report(f"Mobilità residenziale {args.year}{' (prova a secco)' if args.dry_run else ''}:")
    except (UpdateError, probes.ProbeError) as error:
        print(f"Aggiornamento rifiutato: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
