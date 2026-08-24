#!/usr/bin/env python3
"""Audit riproducibile del lotto Scuola sull'Open Data MIM.

Scarica le distribuzioni 2024/25 dell'Anagrafe dell'Edilizia Scolastica,
ricostruisce l'appartenenza degli edifici ai sette Comuni della Versilia e
produce un report per valutare senza ambiguita' i candidati del lotto:
- agibilita / sicurezza antincendio;
- accessibilita / barriere architettoniche;
- palestra e mensa;
- periodo di costruzione;
- raggiungibilita con TPL / scuolabus.

Il probe NON modifica data/site-data.json e non interpreta i valori mancanti
come NO. Serve a congelare schema, copertura e denominatori prima della
materializzazione nel catalogo pubblico.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "school_probe_report.json"
OUT_MD = ROOT / "school_probe_report.md"

TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]

DATASETS = {
    "anagrafica": "EDIANAGRAFESTA2021",
    "sicurezza": "EDICONSICUREZZASTA2021",
    "accessibilita": "EDISUPBARARCSTA2021",
    "spazi": "EDIAMBFUNZSTA2021",
    "eta": "EDIETAORIGINESTA2021",
    "collegamenti": "EDICOLLEGAMENTISTA2021",
}

# Le pagine ufficiali MIM indicano per il 2024/25 dati al 06/08/2025.
# Manteniamo fallback espliciti per rendere il probe leggibile anche se il
# naming del file cambia o una distribuzione viene ripubblicata.
DISTRIBUTIONS = [
    ("202425", "20250806"),
    ("202425", "20250714"),
    ("202324", "20250714"),
    ("202223", "20230731"),
]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def get_bytes(url: str) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0 (+https://osservatorioversilia.it)",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def candidate_urls(code: str):
    base = f"https://dati.istruzione.it/opendata/opendata/catalog/{code}"
    for school_year, date in DISTRIBUTIONS:
        yield f"{base}/{code}{school_year}{date}.csv"


def download_dataset(code: str) -> tuple[str, bytes]:
    errors = []
    for url in candidate_urls(code):
        try:
            raw = get_bytes(url)
        except (HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{url} -> {exc}")
            continue
        # Un 200 con pagina HTML non e' una distribuzione CSV valida.
        head = raw[:300].lower()
        if b"<html" in head or b"<!doctype" in head:
            errors.append(f"{url} -> risposta HTML")
            continue
        if len(raw) < 100:
            errors.append(f"{url} -> file troppo piccolo ({len(raw)} byte)")
            continue
        return url, raw
    raise RuntimeError("Nessuna distribuzione MIM scaricabile per " + code + "\n" + "\n".join(errors))


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def parse_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = decode(raw)
    sample = text[:10000]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        delim = ";"
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rows = [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in reader]
    return list(reader.fieldnames or []), rows


def find_header(headers: list[str], aliases: tuple[str, ...], required: bool = True) -> str | None:
    by_norm = {norm(h): h for h in headers}
    for alias in aliases:
        n = norm(alias)
        if n in by_norm:
            return by_norm[n]
    for h in headers:
        nh = norm(h)
        if any(norm(a) in nh for a in aliases):
            return h
    if required:
        raise RuntimeError(f"Campo non trovato. Attesi {aliases}; headers={headers}")
    return None


def town_from_row(row: dict[str, str], headers: list[str]) -> str | None:
    town_headers = [h for h in headers if "comune" in norm(h)]
    for h in town_headers:
        v = norm(row.get(h, ""))
        for town in TOWNS:
            if v == norm(town):
                return town
    # fallback: talvolta descrizione/localita' contiene il Comune insieme ad altro testo
    for h in town_headers:
        v = norm(row.get(h, ""))
        for town in TOWNS:
            if norm(town) and norm(town) in v:
                return town
    return None


def clean_value(value: str) -> str:
    value = str(value or "").strip()
    return value if value else "<VUOTO>"


def summarize_field(records: list[dict[str, str]], field: str) -> dict:
    counts = Counter(clean_value(r.get(field, "")) for r in records)
    return {k: counts[k] for k in sorted(counts)}


def aggregate_by_building(rows: list[dict[str, str]], building_field: str, town_by_building: dict[str, str]):
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        building = str(row.get(building_field, "")).strip()
        if building and building in town_by_building:
            grouped[building].append(row)
    by_town: dict[str, list[tuple[str, list[dict[str, str]]]]] = {town: [] for town in TOWNS}
    for building, records in grouped.items():
        by_town[town_by_building[building]].append((building, records))
    return grouped, by_town


def main() -> None:
    downloaded = {}
    parsed = {}
    for name, code in DATASETS.items():
        url, raw = download_dataset(code)
        headers, rows = parse_csv(raw)
        if not rows:
            raise RuntimeError(f"{name}: dataset vuoto")
        downloaded[name] = {"code": code, "url": url, "bytes": len(raw), "rows": len(rows)}
        parsed[name] = {"headers": headers, "rows": rows}
        print(f"{name}: {len(rows):,} righe · {len(raw):,} byte · {url}")

    ana_headers = parsed["anagrafica"]["headers"]
    ana_rows = parsed["anagrafica"]["rows"]
    ana_building = find_header(ana_headers, ("CodiceEdificio", "Codice Edificio"))

    town_by_building: dict[str, str] = {}
    ana_hits = Counter()
    duplicate_towns = defaultdict(set)
    for row in ana_rows:
        town = town_from_row(row, ana_headers)
        if not town:
            continue
        building = str(row.get(ana_building, "")).strip()
        if not building:
            continue
        ana_hits[town] += 1
        duplicate_towns[building].add(town)
        town_by_building[building] = town

    conflicts = {b: sorted(v) for b, v in duplicate_towns.items() if len(v) > 1}
    if conflicts:
        raise RuntimeError(f"Edifici associati a piu' Comuni: {conflicts}")
    missing_towns = [town for town in TOWNS if ana_hits[town] == 0]
    if missing_towns:
        raise RuntimeError(f"Anagrafica senza edifici per: {missing_towns}")

    report: dict = {
        "schoolYearTarget": "2024/25",
        "source": "MIM - Portale Unico dei Dati della Scuola / Anagrafe dell'Edilizia Scolastica",
        "downloaded": downloaded,
        "anagrafica": {
            "headers": ana_headers,
            "buildingField": ana_building,
            "versiliaBuildingRows": dict(ana_hits),
            "uniqueVersiliaBuildings": len(town_by_building),
        },
        "datasets": {},
    }

    for name in ("sicurezza", "accessibilita", "spazi", "eta", "collegamenti"):
        headers = parsed[name]["headers"]
        rows = parsed[name]["rows"]
        building_field = find_header(headers, ("CodiceEdificio", "Codice Edificio"))
        grouped, by_town = aggregate_by_building(rows, building_field, town_by_building)
        excluded = {
            norm(building_field),
            norm(find_header(headers, ("AnnoScolastico", "Anno Scolastico"), required=False) or ""),
            norm(find_header(headers, ("CodiceScuola", "Codice Scuola"), required=False) or ""),
        }
        value_fields = [h for h in headers if norm(h) not in excluded]

        item = {
            "headers": headers,
            "buildingField": building_field,
            "matchedUniqueBuildings": len(grouped),
            "coverageByTown": {town: len(by_town[town]) for town in TOWNS},
            "fields": {},
            "conflicts": [],
        }

        for field in value_fields:
            field_summary = {"byTown": {}, "allVersilia": {}}
            flat_records = []
            for town in TOWNS:
                town_records = []
                for building, recs in by_town[town]:
                    vals = {clean_value(r.get(field, "")) for r in recs}
                    if len(vals) > 1:
                        item["conflicts"].append({"town": town, "building": building, "field": field, "values": sorted(vals)})
                    # Una riga per edificio per evitare di pesare due volte gli edifici condivisi da piu' PES.
                    representative = dict(recs[0])
                    representative[field] = sorted(vals)[0] if vals else "<VUOTO>"
                    town_records.append(representative)
                    flat_records.append(representative)
                field_summary["byTown"][town] = summarize_field(town_records, field)
            field_summary["allVersilia"] = summarize_field(flat_records, field)
            item["fields"][field] = field_summary
        report["datasets"][name] = item

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Probe lotto Scuola - MIM",
        "",
        f"Anno scolastico target: **{report['schoolYearTarget']}**",
        f"Edifici Versilia univoci da anagrafica: **{report['anagrafica']['uniqueVersiliaBuildings']}**",
        "",
        "## Copertura per Comune",
        "",
        "| Dataset | " + " | ".join(TOWNS) + " |",
        "|---|" + "---:|" * len(TOWNS),
    ]
    for name, item in report["datasets"].items():
        lines.append("| " + name + " | " + " | ".join(str(item["coverageByTown"][t]) for t in TOWNS) + " |")

    for name, item in report["datasets"].items():
        lines += ["", f"## {name}", "", "Campi: `" + "`, `".join(item["headers"]) + "`", ""]
        for field, summary in item["fields"].items():
            lines.append(f"### {field}")
            for town in TOWNS:
                bits = ", ".join(f"{k}={v}" for k, v in summary["byTown"][town].items())
                lines.append(f"- **{town}**: {bits or 'nessun record'}")
            lines.append("")
        if item["conflicts"]:
            lines.append(f"Conflitti edificio/campo: **{len(item['conflicts'])}** (vedi JSON).")
        else:
            lines.append("Conflitti edificio/campo: **0**.")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report scritto: {OUT_JSON.name}, {OUT_MD.name}")
    print("SCHOOL_PROBE_OK")


if __name__ == "__main__":
    main()
