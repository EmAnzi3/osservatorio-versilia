#!/usr/bin/env python3
"""Materializza lo storico ARS 2008–2022 della speranza di vita, per sesso.

La sorgente è l'export ufficiale ARS dell'indicatore 1290. Il comando normale
usa esclusivamente lo snapshot versionato; --refresh-source aggiorna lo snapshot
dallo ZIP ufficiale e ne registra le impronte SHA-256.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "ars-life-expectancy-1290-2008-2022.json"
HISTORY_DOC = ROOT / "docs" / "copertura-serie-storiche.md"

INDICATOR_URL = (
    "https://www.ars.toscana.it/banche-dati/"
    "dettaglio_indicatore-1290-speranza-vita-alla-nascita"
    "?dettaglio=ric_anno_geo_comuni&par_top_geografia=046033"
    "&provenienza=comuni_elenco_indicatori_sintesi"
)
EXPORT_URL = "https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=1290"
SNAPSHOT_REF = "data/source-snapshots/ars-life-expectancy-1290-2008-2022.json"
PROFILE = "ars-toscana-mixed"
YEARS = list(range(2008, 2023))
SEXES = ("totale", "maschi", "femmine")
SEX_LABELS = {"totale": "Totale", "maschi": "Maschi", "femmine": "Femmine"}
GEOGRAPHIES = {
    "046005": {"arsCode": "46005", "name": "Camaiore"},
    "046013": {"arsCode": "46013", "name": "Forte Dei Marmi"},
    "046018": {"arsCode": "46018", "name": "Massarosa"},
    "046024": {"arsCode": "46024", "name": "Pietrasanta"},
    "046028": {"arsCode": "46028", "name": "Seravezza"},
    "046030": {"arsCode": "46030", "name": "Stazzema"},
    "046033": {"arsCode": "46033", "name": "Viareggio"},
    "VERSILIA": {"arsCode": "202M", "name": "Versilia"},
    "TOSCANA": {"arsCode": "90", "name": "Regione Toscana"},
}
EXPECTED_CSV_SHA256 = "ba1d0e9580eedf4a9b495032bb0fde70afc1b8ec14aae3752c7c7da847ba51f3"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_number(raw: str) -> float:
    text = str(raw or "").strip().replace(".", "").replace(",", ".")
    return float(text)


def download_snapshot() -> dict:
    request = urllib.request.Request(
        EXPORT_URL,
        headers={
            "User-Agent": "OsservatorioVersilia-source-audit/1.0",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        outer = response.read()
    zip_sha = hashlib.sha256(outer).hexdigest()
    with zipfile.ZipFile(io.BytesIO(outer)) as archive:
        csv_name = next((name for name in archive.namelist() if name.lower().endswith(".csv")), None)
        if not csv_name:
            raise RuntimeError("Export ARS 1290: dati.csv non trovato nello ZIP")
        raw_csv = archive.read(csv_name)
    csv_sha = hashlib.sha256(raw_csv).hexdigest()
    if csv_sha != EXPECTED_CSV_SHA256:
        raise RuntimeError(f"Export ARS 1290 cambiato: SHA dati.csv {csv_sha}")
    text = raw_csv.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    required = {
        "id_indicatore", "anno", "codice_geografia", "geografia",
        "misura_grezza", "sesso"
    }
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError(f"Tracciato ARS inatteso: {reader.fieldnames}")

    ars_to_key = {meta["arsCode"]: key for key, meta in GEOGRAPHIES.items()}
    matrix: dict[str, dict[str, dict[int, float]]] = {
        key: {sex: {} for sex in SEXES} for key in GEOGRAPHIES
    }
    matched = 0
    for row in reader:
        code = str(row.get("codice_geografia") or "").strip()
        sex = str(row.get("sesso") or "").strip().lower()
        try:
            year = int(row.get("anno") or 0)
        except ValueError:
            continue
        if code not in ars_to_key or sex not in SEXES or year not in YEARS:
            continue
        if str(row.get("id_indicatore") or "").strip() != "1290":
            continue
        key = ars_to_key[code]
        if year in matrix[key][sex]:
            raise RuntimeError(f"Duplicato ARS: {key} {sex} {year}")
        matrix[key][sex][year] = parse_number(row["misura_grezza"])
        matched += 1

    expected_rows = len(GEOGRAPHIES) * len(SEXES) * len(YEARS)
    if matched != expected_rows:
        raise RuntimeError(f"Righe ARS attese {expected_rows}, trovate {matched}")
    for key in GEOGRAPHIES:
        for sex in SEXES:
            if sorted(matrix[key][sex]) != YEARS:
                raise RuntimeError(f"Serie incompleta ARS: {key} {sex}")

    return {
        "schemaVersion": 1,
        "retrieved": "2026-08-28",
        "indicator": {
            "id": 1290,
            "label": "Speranza di vita alla nascita",
            "indicatorUrl": INDICATOR_URL,
            "exportUrl": EXPORT_URL,
        },
        "source": {
            "publisher": "ARS Toscana / ISPRO",
            "zipSha256": zip_sha,
            "csvMember": csv_name,
            "csvSha256": csv_sha,
            "csvEncoding": "utf-8-sig",
            "delimiter": ";",
            "headers": reader.fieldnames,
        },
        "scope": {
            "years": YEARS,
            "sexes": list(SEXES),
            "geographies": GEOGRAPHIES,
            "expectedRows": expected_rows,
            "coverage": "7/7",
        },
        "series": {
            key: {
                sex: [matrix[key][sex][year] for year in YEARS]
                for sex in SEXES
            }
            for key in GEOGRAPHIES
        },
    }


def validate_snapshot(snapshot: dict, site: dict) -> None:
    if snapshot.get("indicator", {}).get("id") != 1290:
        raise RuntimeError("Snapshot ARS: indicatore diverso da 1290")
    if snapshot.get("source", {}).get("csvSha256") != EXPECTED_CSV_SHA256:
        raise RuntimeError("Snapshot ARS: hash dati.csv inatteso")
    scope = snapshot.get("scope", {})
    if scope.get("years") != YEARS or tuple(scope.get("sexes", [])) != SEXES:
        raise RuntimeError("Snapshot ARS: anni o sessi inattesi")
    town_codes = {town["code"] for town in site["towns"]}
    if town_codes != {key for key in GEOGRAPHIES if key.startswith("046")}:
        raise RuntimeError("Snapshot ARS: perimetro comunale diverso dai 7 Comuni canonici")
    expected = len(GEOGRAPHIES) * len(SEXES) * len(YEARS)
    if scope.get("expectedRows") != expected:
        raise RuntimeError("Snapshot ARS: conteggio righe non riconciliato")
    for geo in GEOGRAPHIES:
        for sex in SEXES:
            values = snapshot.get("series", {}).get(geo, {}).get(sex, [])
            if len(values) != len(YEARS) or not all(isinstance(value, (int, float)) for value in values):
                raise RuntimeError(f"Snapshot ARS incompleto: {geo} {sex}")


def rounded_series(snapshot: dict, geo: str, sex: str) -> dict:
    return {
        "years": YEARS,
        "values": [round(float(value) + 1e-12, 2) for value in snapshot["series"][geo][sex]],
    }


def current_value(snapshot: dict, geo: str, sex: str) -> float:
    return rounded_series(snapshot, geo, sex)["values"][-1]


def part(snapshot: dict, geo: str, sex: str) -> dict:
    value = current_value(snapshot, geo, sex)
    return {
        "key": sex,
        "label": SEX_LABELS[sex],
        "selectorLabel": SEX_LABELS[sex],
        "value": value,
        "formatted": f"{value:.1f}".replace(".", ",") + " anni",
        "unit": "years",
        "series": rounded_series(snapshot, geo, sex),
    }


def benchmark(snapshot: dict, sex: str) -> dict:
    return {
        "year": "2022",
        "tuscany": current_value(snapshot, "TOSCANA", sex),
        "source": "ARS Toscana — La salute dei comuni",
        "url": INDICATOR_URL,
        "note": "Comune, Zona Versilia e Toscana condividono fonte, anno e metodo di calcolo. Il riferimento nazionale non è esposto perché non proviene dalla stessa tavola ARS.",
    }


def apply_site(site: dict, snapshot: dict) -> None:
    validate_snapshot(snapshot, site)
    metric = site["metrics"]["lifeExpectancy"]
    meta = metric["meta"]
    meta["compositeType"] = "sexBreakdown"
    meta["selectorLabel"] = "Sesso"
    meta["defaultSex"] = "totale"
    meta["sexOptions"] = [{"key": sex, "label": SEX_LABELS[sex]} for sex in SEXES]
    meta["benchmark"] = benchmark(snapshot, "totale")
    meta["benchmarksBySex"] = {sex: benchmark(snapshot, sex) for sex in SEXES}
    meta["sourceMeta"] = {
        "publisher": "ARS Toscana / ISPRO",
        "snapshot": SNAPSHOT_REF,
        "note": "Export ufficiale ARS dell'indicatore 1290; serie 2008–2022 per Totale, Maschi e Femmine.",
    }

    for row in metric["rows"]:
        code = row["code"]
        parts = [part(snapshot, code, sex) for sex in SEXES]
        total = parts[0]
        if round(float(row["value"]), 2) != total["value"]:
            raise RuntimeError(f"{row['town']}: il totale 2022 storico non coincide col valore corrente")
        row["value"] = total["value"]
        row["formatted"] = total["formatted"]
        row["series"] = total["series"]
        row["parts"] = parts

    aggregate_parts = [part(snapshot, "VERSILIA", sex) for sex in SEXES]
    if round(float(metric["aggregate"]["value"]), 2) != aggregate_parts[0]["value"]:
        raise RuntimeError("Versilia: il totale 2022 storico non coincide col valore corrente")
    metric["aggregate"].update({
        "value": aggregate_parts[0]["value"],
        "formatted": aggregate_parts[0]["formatted"],
        "label": "Valore ARS Versilia",
        "note": "Aggregato Zona Versilia pubblicato direttamente da ARS Toscana con lo stesso metodo del dato comunale; non è una media calcolata dall'Osservatorio.",
        "series": aggregate_parts[0]["series"],
        "parts": aggregate_parts,
    })
    metric["sourceUrl"] = INDICATOR_URL
    metric["sourceUrls"] = {
        "indicator": INDICATOR_URL,
        "export": EXPORT_URL,
    }
    metric["history"] = {
        "years": YEARS,
        "coverage": "7/7",
        "sexes": list(SEXES),
        "source": "ARS Toscana — indicatore 1290",
        "aggregateType": "official-source",
        "aggregateLabel": "Zona Versilia",
        "note": "Serie ufficiale 2008–2022. Totale, Maschi e Femmine sono pubblicati da ARS per tutti i sette Comuni; la Zona Versilia è l'aggregato ufficiale della fonte.",
    }
    metric["method"] = {
        "type": "Dato ufficiale ARS Toscana",
        "formula": "Valore pubblicato da ARS Toscana per l'indicatore 1290 “Speranza di vita alla nascita”, senza trasformazioni statistiche dell'Osservatorio.",
        "caveat": "Serie 2008–2022 con distinzione Totale, Maschi e Femmine. I valori comunali, della Zona Versilia e della Toscana provengono dallo stesso export ufficiale. Nessun valore è interpolato, stimato o ricostruito da medie comunali.",
        "coverage": "7/7",
        "snapshot": SNAPSHOT_REF,
    }


def apply_registry(registry: dict) -> None:
    profile = registry["sourceProfiles"][PROFILE]
    profile["acquisitionMethod"] = "Download dell'export ufficiale ARS per indicatore; snapshot con impronta SHA-256 e valori comunali/territoriali conservati senza stime."
    for url in (INDICATOR_URL, EXPORT_URL):
        registry.setdefault("sourceProfileByUrl", {})[url] = PROFILE
        registry.setdefault("sourceUrlProfiles", {})[url] = PROFILE
    registry.setdefault("metricOverrides", {})["lifeExpectancy"] = {"profile": PROFILE}


def apply_history_doc() -> None:
    marker = "## Speranza di vita ARS v1.22.0"
    text = HISTORY_DOC.read_text(encoding="utf-8")
    if marker in text:
        return
    text += (
        "\n\n## Speranza di vita ARS v1.22.0\n\n"
        "L'indicatore `lifeExpectancy` usa l'export ufficiale ARS Toscana dell'indicatore 1290. "
        "La serie è completa 2008–2022 per tutti i sette Comuni e per i tre sessi esposti dalla fonte: "
        "Totale, Maschi e Femmine. La Zona Versilia e la Toscana sono lette direttamente dallo stesso export; "
        "l'aggregato Versilia non è una media dei valori comunali. Lo snapshot conserva l'impronta SHA-256 di `dati.csv`. "
        "L'ultimo punto 2022 deve coincidere con il valore corrente già pubblicato. Nessuna interpolazione o stima è ammessa.\n"
    )
    HISTORY_DOC.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-source", action="store_true")
    args = parser.parse_args()

    if args.refresh_source:
        snapshot = download_snapshot()
        save(SNAPSHOT_PATH, snapshot)
    elif not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"Snapshot mancante: {SNAPSHOT_PATH}; usare --refresh-source")

    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    snapshot = load(SNAPSHOT_PATH)
    apply_site(site, snapshot)
    apply_registry(registry)
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    apply_history_doc()
    print("Speranza di vita ARS materializzata: 2008–2022, Totale/Maschi/Femmine, copertura 7/7, Zona Versilia ufficiale.")


if __name__ == "__main__":
    main()
