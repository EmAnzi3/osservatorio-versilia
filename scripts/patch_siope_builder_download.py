#!/usr/bin/env python3
"""Patch the generated SIOPE builder for current official CKAN dump formats."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).with_name("build_siope_history.py")

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
            if len(content) >= 1_000:
                return content, candidate
            preview = content[:300].decode("utf-8", errors="replace")
            errors.append(
                f"{candidate}: risposta troppo piccola, {len(content)} byte, {preview!r}"
            )
        except requests.RequestException as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    raise RuntimeError(
        "Risorsa SIOPE non scaricabile tramite i dump CKAN ufficiali:\n"
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


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_function(text, "download_csv", DOWNLOAD_REPLACEMENT)
    text = replace_function(text, "decode_csv", DECODE_REPLACEMENT)
    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")
    print("Downloader e decoder SIOPE aggiornati per i dump CKAN ufficiali.")


if __name__ == "__main__":
    main()
