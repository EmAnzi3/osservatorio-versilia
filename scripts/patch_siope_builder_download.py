#!/usr/bin/env python3
"""Replace the generated SIOPE downloader with a robust official-CKAN fallback."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).with_name("build_siope_history.py")

REPLACEMENT = r'''def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
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
                headers={"Accept": "text/csv,*/*;q=0.8"},
            )
            response.raise_for_status()
            content = response.content
            sample = content[:20_000]
            if (
                len(content) >= 1_000
                and b"\n" in sample
                and any(mark in sample for mark in (b";", b",", b"\t", b"|"))
            ):
                return content, candidate
            preview = content[:300].decode("utf-8", errors="replace")
            errors.append(
                f"{candidate}: risposta non CSV, {len(content)} byte, {preview!r}"
            )
        except requests.RequestException as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    raise RuntimeError(
        "Risorsa SIOPE non scaricabile tramite i dump CKAN ufficiali:\n"
        + "\n".join(errors)
    )

'''


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?ms)^def\s+download_csv\s*\([^\n]*\)\s*(?:->\s*[^:]+)?\s*:\n.*?(?=^def\s+\w+\s*\()"
    )
    updated, count = pattern.subn(lambda _match: REPLACEMENT, text, count=1)
    if count != 1:
        signature = next(
            (line for line in text.splitlines() if "download_csv" in line),
            "firma non trovata",
        )
        raise RuntimeError(f"Funzione download_csv non sostituita: {signature}")
    compile(updated, str(PATH), "exec")
    PATH.write_text(updated, encoding="utf-8")
    print("Downloader SIOPE sostituito con fallback CKAN ufficiale.")


if __name__ == "__main__":
    main()
