#!/usr/bin/env python3
"""Build reproducible SIOPE cash-flow histories for the seven Versilia municipalities."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
DATA_PATH = ROOT / "data" / "site-data.json"
DISCOVERY_PATH = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
OUT_PATH = ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json"
YEARS = list(range(2018, 2026))
TOWN_CODES = {
    "Camaiore": "046005",
    "Forte dei Marmi": "046013",
    "Massarosa": "046018",
    "Pietrasanta": "046024",
    "Seravezza": "046028",
    "Stazzema": "046030",
    "Viareggio": "046033",
}
METRIC_KEYS = [
    "siopePayments",
    "currentPayments",
    "capitalPayments",
    "cashReceiptsPerResident",
    "cashBalancePerResident",
]
TIMEOUT = 240


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def digits(value: object) -> str:
    return "".join(re.findall(r"\d", str(value or "")))


def parse_number(value: object) -> float:
    text = str(value or "").strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return 0.0
    text = text.replace("€", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    return float(text)


def decode_csv(content: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = content.decode(encoding)
            if "Codice" in text[:5000] or "CODICE" in text[:5000]:
                return text, encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Codifica CSV SIOPE non riconosciuta")


def choose_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,|\t").delimiter
    except csv.Error:
        counts = {delimiter: sample.count(delimiter) for delimiter in (";", ",", "|", "\t")}
        return max(counts, key=counts.get)


def header_lookup(fieldnames: list[str]) -> dict[str, str]:
    return {norm(name): name for name in fieldnames if name is not None}


def require_header(headers: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        key = norm(alias)
        if key in headers:
            return headers[key]
    for alias in aliases:
        words = set(norm(alias).split())
        matches = [original for key, original in headers.items() if words <= set(key.split())]
        if len(matches) == 1:
            return matches[0]
    raise RuntimeError(f"Colonna SIOPE assente: {aliases}; disponibili: {sorted(headers)}")


def csv_resource(package: dict) -> dict:
    resources = [
        item for item in package.get("resources", [])
        if str(item.get("mimetype", "")).casefold() == "text/csv"
        or str(item.get("format", "")).casefold() == "csv"
    ]
    resources = [item for item in resources if "datastore/dump" in str(item.get("url", ""))]
    if len(resources) != 1:
        raise RuntimeError(f"Risorsa CSV non univoca per {package.get('title')}: {resources}")
    return resources[0]


def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
    official_url = str(resource["url"]).replace("http://", "https://", 1)
    response = session.get(official_url, timeout=TIMEOUT)
    response.raise_for_status()
    content = response.content
    if len(content) < 1000 or b"<html" in content[:500].lower():
        raise RuntimeError(f"Risposta CSV non valida: {official_url}, {len(content)} byte")
    return content, official_url


def title_number(value: object, expected_flag: str) -> int | None:
    compact = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    if compact.startswith(expected_flag):
        compact = compact[len(expected_flag):]
    match = re.search(r"([1-9])", compact)
    return int(match.group(1)) if match else None


def parse_dataset(content: bytes, year: int, movement: str) -> tuple[dict[str, dict], dict]:
    text, encoding = decode_csv(content)
    delimiter = choose_delimiter(text[:10000])
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise RuntimeError(f"CSV SIOPE {year}/{movement} senza intestazioni")
    headers = header_lookup(reader.fieldnames)
    fields = {
        "province": require_header(headers, "Codice Istat Provincia"),
        "commune": require_header(headers, "Codice Istat Comune"),
        "entity_bki": require_header(headers, "Codice Tipologia Ente BKI"),
        "entity_name": require_header(headers, "Descrizione Ente BDAP"),
        "month": require_header(headers, "Anno/Mese Calendario", "AnnoMese Calendario"),
        "movement": require_header(headers, "Tipologia del Movimento", "Flag Tipologia Classificazione"),
        "title": require_header(headers, "Codice Titolo CG"),
        "detail": require_header(headers, "Codice Gestionale Enti Locali"),
        "population": require_header(headers, "Popolazione ISTAT"),
        "amount": require_header(headers, "Importo cumulato"),
    }
    code_to_town = {code: town for town, code in TOWN_CODES.items()}
    expected_flag = "E" if movement == "entrata" else "S"
    totals: dict[str, dict] = {
        town: {"population_values": set(), "total": 0.0, "current": 0.0, "capital": 0.0, "rows": 0}
        for town in TOWN_CODES
    }
    seen: set[tuple[str, str]] = set()
    selected = 0
    for row in reader:
        province = digits(row.get(fields["province"]))[-3:].zfill(3)
        if province != "046":
            continue
        code = digits(row.get(fields["commune"]))[-6:].zfill(6)
        town = code_to_town.get(code)
        if not town:
            continue
        entity_code = str(row.get(fields["entity_bki"], "")).strip().upper()
        if entity_code != "CO":
            continue
        month_digits = digits(row.get(fields["month"]))
        if not month_digits.endswith(f"{year}12") and month_digits != f"{year}12":
            continue
        flag = str(row.get(fields["movement"], "")).strip().upper()
        if expected_flag not in flag:
            continue
        detail = str(row.get(fields["detail"], "")).strip()
        key = (town, detail)
        if key in seen:
            raise RuntimeError(f"Riga SIOPE duplicata {year}/{movement}: {town}, {detail}")
        seen.add(key)
        amount = parse_number(row.get(fields["amount"]))
        population = int(round(parse_number(row.get(fields["population"]))))
        if population <= 0 or not math.isfinite(amount):
            raise RuntimeError(f"Valore SIOPE non valido {year}/{movement}: {town}")
        title = title_number(row.get(fields["title"]), expected_flag)
        totals[town]["population_values"].add(population)
        totals[town]["total"] += amount
        totals[town]["rows"] += 1
        if movement == "spesa" and title == 1:
            totals[town]["current"] += amount
        if movement == "spesa" and title == 2:
            totals[town]["capital"] += amount
        selected += 1

    result: dict[str, dict] = {}
    for town, values in totals.items():
        if values["rows"] == 0:
            raise RuntimeError(f"Copertura SIOPE assente {year}/{movement}: {town}")
        if len(values["population_values"]) != 1:
            raise RuntimeError(
                f"Popolazione SIOPE non univoca {year}/{movement}/{town}: {values['population_values']}"
            )
        result[town] = {
            "population": next(iter(values["population_values"])),
            "total": values["total"],
            "current": values["current"],
            "capital": values["capital"],
            "selected_rows": values["rows"],
        }
    return result, {
        "encoding": encoding,
        "delimiter": delimiter,
        "headers": reader.fieldnames,
        "mapped_fields": fields,
        "selected_rows": selected,
    }


def current_values(data: dict, key: str) -> dict[str, float]:
    return {row["town"]: float(row["value"]) for row in data["metrics"][key]["rows"]}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
        "Accept": "text/csv,*/*;q=0.8",
    })
    raw: dict[str, dict[str, dict]] = {town: {} for town in TOWN_CODES}
    sources: dict[str, dict] = {}
    for year in YEARS:
        yearly: dict[str, dict[str, dict]] = {}
        for movement in ("entrata", "spesa"):
            label = f"{movement}-{year}-toscana"
            package = discovery["datasets"][label]
            resource = csv_resource(package)
            content, url = download_csv(session, resource)
            parsed, audit = parse_dataset(content, year, movement)
            yearly[movement] = parsed
            sources[label] = {
                "package_id": package["id"],
                "package_title": package["title"],
                "url": url,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "audit": audit,
            }
        for town in TOWN_CODES:
            receipts = yearly["entrata"][town]
            payments = yearly["spesa"][town]
            if receipts["population"] != payments["population"]:
                raise RuntimeError(
                    f"Popolazione Entrata/Spesa diversa {year}/{town}: "
                    f"{receipts['population']} != {payments['population']}"
                )
            population = receipts["population"]
            raw[town][str(year)] = {
                "population_istat_siope": population,
                "cash_receipts": receipts["total"],
                "cash_payments": payments["total"],
                "current_payments": payments["current"],
                "capital_payments": payments["capital"],
                "cash_balance": receipts["total"] - payments["total"],
                "selected_rows": {
                    "entrata": receipts["selected_rows"],
                    "spesa": payments["selected_rows"],
                },
            }

    def value(key: str, town: str, year: int) -> float:
        item = raw[town][str(year)]
        pop = item["population_istat_siope"]
        numerator = {
            "siopePayments": item["cash_payments"],
            "currentPayments": item["current_payments"],
            "capitalPayments": item["capital_payments"],
            "cashReceiptsPerResident": item["cash_receipts"],
            "cashBalancePerResident": item["cash_balance"],
        }[key]
        return numerator / pop

    validation: dict[str, dict[str, dict[str, float]]] = {}
    for key in METRIC_KEYS:
        expected = current_values(data, key)
        validation[key] = {}
        for town in TOWN_CODES:
            calculated = value(key, town, 2025)
            delta = calculated - expected[town]
            validation[key][town] = {
                "existing_2025": expected[town],
                "calculated_2025": calculated,
                "delta": delta,
            }
            if not math.isclose(calculated, expected[town], rel_tol=1e-9, abs_tol=0.02):
                raise RuntimeError(
                    f"Validazione SIOPE 2025 fallita: {key}/{town}: "
                    f"{calculated} != {expected[town]} (delta {delta})"
                )

    metrics = {
        key: {
            "coverage": "7/7",
            "years": YEARS,
            "values": {
                town: {str(year): value(key, town, year) for year in YEARS}
                for town in TOWN_CODES
            },
        }
        for key in METRIC_KEYS
    }
    payload = {
        "version": "siope-history-v1.6.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Movimenti cumulati SIOPE di dicembre 2018–2025 per i sette Comuni della Versilia.",
        "source": {
            "publisher": "Ragioneria generale dello Stato — BDAP Open Data / SIOPE",
            "catalogue_api": discovery["api"],
            "metadata": "SIOPE Movimenti cumulati mensili di Entrata e di Spesa",
            "resources": sources,
        },
        "selection_rules": {
            "region": "Toscana",
            "province_istat": "046",
            "entity_type_bki": "CO",
            "municipalities": TOWN_CODES,
            "month": "dicembre (dato cumulato dal 1° gennaio)",
            "years": YEARS,
            "classification": "codice gestionale Enti Locali di quinto livello; Titolo 1 per pagamenti correnti, Titolo 2 per conto capitale",
            "no_estimates": True,
        },
        "formulas": {
            "siopePayments": "pagamenti complessivi cumulati a dicembre / popolazione ISTAT SIOPE",
            "currentPayments": "pagamenti cumulati a dicembre con Titolo CG 1 / popolazione ISTAT SIOPE",
            "capitalPayments": "pagamenti cumulati a dicembre con Titolo CG 2 / popolazione ISTAT SIOPE",
            "cashReceiptsPerResident": "incassi complessivi cumulati a dicembre / popolazione ISTAT SIOPE",
            "cashBalancePerResident": "(incassi complessivi - pagamenti complessivi) / popolazione ISTAT SIOPE",
        },
        "coverage": "7/7 per ogni annualità 2018–2025",
        "validation_2025": validation,
        "raw": raw,
        "metrics": metrics,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Serie SIOPE 2018–2025 costruite e validate sul dato 2025 esistente (7/7).")


if __name__ == "__main__":
    main()
