#!/usr/bin/env python3
"""Patch the generated SIOPE builder and tests for the verified 2019-2025 method."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILDER_PATH = ROOT / "build_siope_history.py"
TEST_PATH = ROOT / "test_siope_history_v160.py"

DOWNLOAD_REPLACEMENT = r'''def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
    import time as _time

    official_url = str(resource["url"]).replace("http://", "https://", 1)
    candidates = [official_url]
    if official_url.lower().endswith(".csv"):
        canonical = official_url[:-4]
        candidates.extend([canonical, canonical + "?format=csv"])
    errors = []
    for candidate in candidates:
        for attempt in range(1, 6):
            try:
                response = session.get(
                    candidate,
                    timeout=TIMEOUT,
                    headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8"},
                )
                response.raise_for_status()
                content = response.content
                content_type = str(response.headers.get("content-type") or "").casefold()
                prefix = content.lstrip()[:32].lower()
                rejected_kind = None
                if "application/json" in content_type or prefix.startswith((b"{", b"[")):
                    rejected_kind = "JSON/metadati"
                elif "text/html" in content_type or prefix.startswith(b"<html") or prefix.startswith(b"<!doctype"):
                    rejected_kind = "HTML"
                elif "application/pdf" in content_type or content.startswith(b"%PDF"):
                    rejected_kind = "PDF"
                if rejected_kind is not None:
                    preview = content[:500].decode("utf-8", errors="replace")
                    errors.append(
                        f"{candidate}: {rejected_kind} non utilizzabile come CSV, "
                        f"content-type={content_type!r}, {len(content)} byte, {preview!r}"
                    )
                    break

                sample = content[:200_000]
                plausible = False
                for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
                    try:
                        text = sample.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                    lines = [line for line in text.splitlines() if line.strip()]
                    if len(lines) >= 2 and any(
                        delimiter in "\n".join(lines[:5])
                        for delimiter in (";", ",", "\t", "|")
                    ):
                        plausible = True
                        break
                if len(content) >= 1_000 and plausible:
                    return content, candidate

                preview = content[:500].decode("utf-8", errors="replace")
                errors.append(
                    f"{candidate}: contenuto non tabellare, content-type={content_type!r}, "
                    f"{len(content)} byte, {preview!r}"
                )
                break
            except requests.RequestException as exc:
                errors.append(
                    f"{candidate}, tentativo {attempt}/5: {type(exc).__name__}: {exc}"
                )
                if attempt < 5:
                    _time.sleep(attempt * 3)
                    continue
                break
    raise RuntimeError(
        "Risorsa SIOPE non scaricabile come tabella tramite i dump CKAN ufficiali:\n"
        + "\n".join(errors)
    )

'''

DECODE_REPLACEMENT = r'''def decode_csv(content: bytes) -> tuple[str, str]:
    import gzip as _gzip
    import io as _io
    import zipfile as _zipfile

    data = content
    container = "raw"
    if data.startswith(b"\x1f\x8b"):
        data = _gzip.decompress(data)
        container = "gzip"
    elif data.startswith(b"PK\x03\x04"):
        with _zipfile.ZipFile(_io.BytesIO(data)) as archive:
            candidates = [
                item for item in archive.infolist()
                if not item.is_dir()
                and item.filename.lower().endswith((".csv", ".txt"))
            ]
            if not candidates:
                candidates = [item for item in archive.infolist() if not item.is_dir()]
            if not candidates:
                raise RuntimeError("Archivio SIOPE privo di file leggibili")
            selected = max(candidates, key=lambda item: item.file_size)
            data = archive.read(selected)
            container = f"zip:{selected.filename}"

    attempts = ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin-1"]
    diagnostics = []
    for encoding in attempts:
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError as exc:
            diagnostics.append(f"{encoding}: {exc}")
            continue
        sample = text[:20_000]
        printable = sum(character.isprintable() or character in "\r\n\t" for character in sample)
        ratio = printable / max(1, len(sample))
        first_lines = "\n".join(sample.splitlines()[:5])
        if (
            ratio >= 0.85
            and len(sample.splitlines()) >= 2
            and any(delimiter in first_lines for delimiter in (";", ",", "\t", "|"))
        ):
            return text, f"{container}+{encoding}"
        diagnostics.append(
            f"{encoding}: testo non plausibile, printable={ratio:.3f}, preview={first_lines[:180]!r}"
        )
    raise RuntimeError(
        "Codifica CSV SIOPE non riconosciuta; "
        f"magic={data[:16].hex()}, dimensione={len(data)}; "
        + " | ".join(diagnostics)
    )

'''

PARSE_REPLACEMENT = r'''def parse_dataset(content: bytes, year: int, movement: str) -> tuple[dict[str, dict], dict]:
    text, encoding = decode_csv(content)
    delimiter = choose_delimiter(text[:10000])
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise RuntimeError(f"CSV SIOPE {year}/{movement} senza intestazioni")
    headers = header_lookup(reader.fieldnames)
    fields = {
        "province": require_header(headers, "Codice Istat Provincia"),
        "commune": require_header(headers, "Codice Istat Comune"),
        "entity_type": require_header(headers, "Codice Tipologia Ente BDAP"),
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

        commune_digits = digits(row.get(fields["commune"]))
        if not commune_digits:
            continue
        if len(commune_digits) <= 3:
            code = province + commune_digits[-3:].zfill(3)
        else:
            code = commune_digits[-6:].zfill(6)
        town = code_to_town.get(code)
        if not town:
            continue

        entity_code = str(row.get(fields["entity_type"], "")).strip().upper()
        if entity_code != "CO":
            continue
        month_digits = digits(row.get(fields["month"]))
        if not month_digits.endswith(f"{year}12"):
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

'''

MAIN_REPLACEMENT = r'''def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))

    population_rows = data["metrics"]["population"]["rows"]
    population_by_town: dict[str, dict[int, float]] = {}
    for row in population_rows:
        town = str(row.get("town") or "")
        series = row.get("series") or {}
        years = [int(year) for year in series.get("years", [])]
        values = [float(value) for value in series.get("values", [])]
        if len(years) != len(values):
            raise RuntimeError(f"Serie demografica incoerente: {town}")
        population_by_town[town] = dict(zip(years, values))
    if set(population_by_town) != set(TOWN_CODES):
        raise RuntimeError(
            f"Copertura demografica non allineata ai Comuni: {sorted(population_by_town)}"
        )

    resident_population: dict[str, dict[int, float]] = {town: {} for town in TOWN_CODES}
    for town in TOWN_CODES:
        for flow_year in YEARS:
            reference_year = flow_year + 1
            value = population_by_town[town].get(reference_year)
            if value is None or value <= 0:
                raise RuntimeError(
                    f"Popolazione residente mancante per {town}: 1 gennaio {reference_year}"
                )
            resident_population[town][flow_year] = value

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
            raw[town][str(year)] = {
                "population_istat_siope": receipts["population"],
                "population_resident": resident_population[town][year],
                "population_reference_date": f"1 gennaio {year + 1}",
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

    def numerator(key: str, town: str, year: int) -> float:
        item = raw[town][str(year)]
        return {
            "siopePayments": item["cash_payments"],
            "currentPayments": item["current_payments"],
            "capitalPayments": item["capital_payments"],
            "cashReceiptsPerResident": item["cash_receipts"],
            "cashBalancePerResident": item["cash_balance"],
        }[key]

    def value(key: str, town: str, year: int) -> float:
        item = raw[town][str(year)]
        return numerator(key, town, year) / item["population_resident"]

    validation: dict[str, dict[str, dict[str, float | str]]] = {}
    legacy_keys = {
        "siopePayments",
        "cashReceiptsPerResident",
        "cashBalancePerResident",
    }
    for key in METRIC_KEYS:
        expected = current_values(data, key)
        validation[key] = {}
        for town in TOWN_CODES:
            calculated = value(key, town, 2025)
            embedded_population_value = (
                numerator(key, town, 2025) / raw[town]["2025"]["population_istat_siope"]
            )
            validation[key][town] = {
                "existing_2025": expected[town],
                "calculated_2025": calculated,
                "delta": calculated - expected[town],
                "previous_method_calculated_2025": embedded_population_value,
                "status": "matched_existing" if key in legacy_keys else "rebased_to_uniform_resident_population",
            }
            comparison_value = calculated if key in legacy_keys else embedded_population_value
            if not math.isclose(comparison_value, expected[town], rel_tol=1e-9, abs_tol=0.02):
                raise RuntimeError(
                    f"Validazione SIOPE 2025 fallita: {key}/{town}: "
                    f"{comparison_value} != {expected[town]}"
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
        "scope": "Movimenti cumulati SIOPE di dicembre 2019–2025 per i sette Comuni della Versilia.",
        "source": {
            "publisher": "Ragioneria generale dello Stato — BDAP Open Data / SIOPE",
            "catalogue_api": discovery["api"],
            "metadata": "SIOPE Movimenti cumulati mensili di Entrata e di Spesa",
            "population_source": "Istat — popolazione residente del sito",
            "resources": sources,
        },
        "selection_rules": {
            "region": "Toscana",
            "province_istat": "046",
            "entity_type_bdap": "CO",
            "municipalities": TOWN_CODES,
            "month": "dicembre (dato cumulato dal 1° gennaio)",
            "years": YEARS,
            "classification": "codice gestionale Enti Locali di quinto livello; Titolo 1 per pagamenti correnti, Titolo 2 per conto capitale",
            "denominator": "popolazione residente Istat al 1° gennaio dell’anno successivo al flusso contabile",
            "no_estimates": True,
        },
        "formulas": {
            "siopePayments": "pagamenti complessivi cumulati a dicembre / popolazione residente Istat al 1° gennaio dell’anno successivo",
            "currentPayments": "pagamenti cumulati a dicembre con Titolo CG 1 / popolazione residente Istat al 1° gennaio dell’anno successivo",
            "capitalPayments": "pagamenti cumulati a dicembre con Titolo CG 2 / popolazione residente Istat al 1° gennaio dell’anno successivo",
            "cashReceiptsPerResident": "incassi complessivi cumulati a dicembre / popolazione residente Istat al 1° gennaio dell’anno successivo",
            "cashBalancePerResident": "(incassi complessivi - pagamenti complessivi) / popolazione residente Istat al 1° gennaio dell’anno successivo",
        },
        "coverage": "7/7 per ogni annualità 2019–2025",
        "validation_2025": validation,
        "raw": raw,
        "metrics": metrics,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Serie SIOPE 2019–2025 costruite con denominatore demografico uniforme e validate sul 2025.")

'''


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        rf"(?ms)^def\s+{re.escape(name)}\s*\([^\n]*\)\s*(?:->\s*[^:]+)?\s*:\n.*?(?=^def\s+\w+\s*\()"
    )
    updated, count = pattern.subn(lambda _match: replacement, text, count=1)
    if count != 1:
        signature = next(
            (line for line in text.splitlines() if name in line),
            "firma non trovata",
        )
        raise RuntimeError(f"Funzione {name} non sostituita: {signature}")
    return updated


def replace_main(text: str, replacement: str) -> str:
    pattern = re.compile(
        r'(?ms)^def\s+main\s*\(\)\s*->\s*None\s*:\n.*?(?=^if __name__ == "__main__":)'
    )
    updated, count = pattern.subn(lambda _match: replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Funzione main del costruttore SIOPE non sostituita")
    return updated


def set_history_window(text: str, path: Path) -> str:
    original = text
    text = re.sub(r"range\(\s*2018\s*,\s*2026\s*\)", "range(2019, 2026)", text)
    text = re.sub(
        r"\[\s*2018\s*,\s*2019\s*,\s*2020\s*,\s*2021\s*,\s*2022\s*,\s*2023\s*,\s*2024\s*,\s*2025\s*\]",
        "[2019, 2020, 2021, 2022, 2023, 2024, 2025]",
        text,
    )
    text = re.sub(
        r"\(\s*2018\s*,\s*2019\s*,\s*2020\s*,\s*2021\s*,\s*2022\s*,\s*2023\s*,\s*2024\s*,\s*2025\s*\)",
        "(2019, 2020, 2021, 2022, 2023, 2024, 2025)",
        text,
    )
    text = re.sub(r"(?<!\d)2018\s*[–—-]\s*2025(?!\d)", "2019–2025", text)
    text = re.sub(
        r"(?m)^(\s*(?:START_YEAR|FIRST_YEAR|MIN_YEAR)\s*=\s*)2018\b",
        r"\g<1>2019",
        text,
    )
    text = re.sub(r"(?<!\d)2018(?!\d)", "2019", text)

    if text == original:
        raise RuntimeError(f"Periodo SIOPE non individuato in {path.name}")
    if re.search(r"(?<!\d)2018(?!\d)", text):
        raise RuntimeError(f"Riferimento residuo al 2018 in {path.name}")
    if re.search(r"2019\s*,\s*2019", text):
        raise RuntimeError(f"Duplicazione del 2019 introdotta in {path.name}")
    return text


def patch_builder() -> None:
    text = BUILDER_PATH.read_text(encoding="utf-8")
    text = replace_function(text, "download_csv", DOWNLOAD_REPLACEMENT)
    text = replace_function(text, "decode_csv", DECODE_REPLACEMENT)
    text = replace_function(text, "parse_dataset", PARSE_REPLACEMENT)
    text = set_history_window(text, BUILDER_PATH)
    text = replace_main(text, MAIN_REPLACEMENT)
    text = text.replace('"entity_type_bki": "CO"', '"entity_type_bdap": "CO"')
    if '"entity_type_bki"' in text:
        raise RuntimeError("Metadato SIOPE residuo riferito al tipo ente BKI")
    compile(text, str(BUILDER_PATH), "exec")
    BUILDER_PATH.write_text(text, encoding="utf-8")


def patch_test() -> None:
    text = TEST_PATH.read_text(encoding="utf-8")
    text = set_history_window(text, TEST_PATH)
    compile(text, str(TEST_PATH), "exec")
    TEST_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    patch_builder()
    patch_test()
    print("SIOPE 2019-2025 configurato con denominatore demografico annuale uniforme.")


if __name__ == "__main__":
    main()
