#!/usr/bin/env python3
"""Patch the generated SIOPE builder and tests for official CKAN dump formats."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILDER_PATH = ROOT / "build_siope_history.py"
TEST_PATH = ROOT / "test_siope_history_v160.py"

DOWNLOAD_REPLACEMENT = r'''def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
    official_url = str(resource["url"]).replace("http://", "https://", 1)
    candidates = [official_url]
    if official_url.lower().endswith(".csv"):
        canonical = official_url[:-4]
        candidates.extend([canonical, canonical + "?format=csv"])
    errors = []
    for candidate in candidates:
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
                continue

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
        except requests.RequestException as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
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


def set_history_window(text: str, path: Path) -> str:
    """Shift every generated SIOPE expectation from 2018–2025 to 2019–2025."""
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
    print("SIOPE 2019-2025 configurato con codici comunali e tipo ente BDAP corretti.")


if __name__ == "__main__":
    main()
