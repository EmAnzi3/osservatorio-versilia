#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import probe_scuola_mim as probe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "massarosa_school_detail.json"


def candidate_urls(code: str):
    base = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
    for school_year, date in probe.DISTRIBUTIONS:
        yield f"{base}{code}{school_year}{date}.csv"


probe.candidate_urls = candidate_urls

SELECTED_FIELDS = {
    "sicurezza": [
        "CERTIFICATOSEGNALAZIONEAGIBILITA",
        "CERTIFICATOPREVENZIONEINCENDI",
        "SCIAANTINCENDIO",
        "ATTESTAZIONERINNOVOPERIODICOCONFORMITAANTINCENDIO",
        "DOCUMENTOVALUTAZIONERISCHI",
        "PIANOEVACUAZIONE",
    ],
    "accessibilita": [
        "ACCORGIMENTISUPERAMENTOBARRIEREARCHITETTONICHE",
        "ACCESSODAESTERNOCONRAMPE",
        "SCALEANORMA",
        "ASCENSORETRASPORTODISABILI",
        "SERVOSCALAPIATTAFORMAELEVATRICE",
        "SERVIZIIGIENICISPECIFICINORMADISABILI",
        "PORTELARGHEZZAMINIMA",
        "PERCORSIINTERNI",
        "PERCORSIESTERNI",
    ],
    "eta": ["PERIODORIFERIMENTOCOSTRUZIONE"],
}


def values_by_building(rows, building_field, wanted_buildings, fields):
    grouped = defaultdict(lambda: defaultdict(set))
    for row in rows:
        building = str(row.get(building_field, "")).strip()
        if building not in wanted_buildings:
            continue
        for field in fields:
            if field in row:
                grouped[building][field].add(probe.clean_value(row.get(field, "")))
    result = {}
    for building in wanted_buildings:
        result[building] = {
            field: sorted(grouped[building].get(field, {"<VUOTO>"}))
            for field in fields
        }
    return result


def main():
    parsed = {}
    downloaded = {}
    for name, code in probe.DATASETS.items():
        url, raw = probe.download_dataset(code)
        headers, rows = probe.parse_csv(raw)
        parsed[name] = {"headers": headers, "rows": rows}
        downloaded[name] = url

    ana_headers = parsed["anagrafica"]["headers"]
    ana_rows = parsed["anagrafica"]["rows"]
    building_field = probe.find_header(ana_headers, ("CodiceEdificio", "Codice Edificio"))
    school_field = probe.find_header(ana_headers, ("CodiceScuola", "Codice Scuola"), required=False)
    street_type = probe.find_header(ana_headers, ("TipologiaIndirizzo",), required=False)
    street_name = probe.find_header(ana_headers, ("DenominazioneIndirizzo",), required=False)
    street_no = probe.find_header(ana_headers, ("NumeroCivico",), required=False)
    cap_field = probe.find_header(ana_headers, ("CAP",), required=False)

    buildings = defaultdict(lambda: {"schoolCodes": set(), "addresses": set()})
    for row in ana_rows:
        if probe.town_from_row(row, ana_headers) != "Massarosa":
            continue
        building = str(row.get(building_field, "")).strip()
        if not building:
            continue
        if school_field and row.get(school_field):
            buildings[building]["schoolCodes"].add(row[school_field].strip())
        address = " ".join(
            part for part in [
                row.get(street_type, "").strip() if street_type else "",
                row.get(street_name, "").strip() if street_name else "",
                row.get(street_no, "").strip() if street_no else "",
                row.get(cap_field, "").strip() if cap_field else "",
            ] if part
        )
        if address:
            buildings[building]["addresses"].add(address)

    wanted = sorted(buildings)
    details = {
        building: {
            "buildingCode": building,
            "schoolCodes": sorted(buildings[building]["schoolCodes"]),
            "addresses": sorted(buildings[building]["addresses"]),
        }
        for building in wanted
    }

    for dataset, fields in SELECTED_FIELDS.items():
        headers = parsed[dataset]["headers"]
        rows = parsed[dataset]["rows"]
        bfield = probe.find_header(headers, ("CodiceEdificio", "Codice Edificio"))
        actual_fields = [field for field in fields if field in headers]
        values = values_by_building(rows, bfield, set(wanted), actual_fields)
        for building in wanted:
            details[building][dataset] = values[building]

    output = {
        "source": "MIM Anagrafe Edilizia Scolastica 2024/25",
        "downloaded": downloaded,
        "town": "Massarosa",
        "buildingCount": len(wanted),
        "buildings": [details[b] for b in wanted],
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Massarosa: {len(wanted)} edifici; dettaglio scritto in {OUT.name}")


if __name__ == "__main__":
    main()
