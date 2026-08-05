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
            prefix = content.lstrip()[:32].casefold()
            rejected_kind = None
            if "application/json" in content_type or prefix.startswith((b"{", b"[", b'"')):
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
    text = set_history_window(text, BUILDER_PATH)
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
    print("SIOPE configurato e validato sintatticamente per il periodo 2019-2025.")


if __name__ == "__main__":
    main()
