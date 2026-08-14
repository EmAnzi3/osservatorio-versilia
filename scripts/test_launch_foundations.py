#!/usr/bin/env python3
"""Regression checks for public launch metadata and identity."""

from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "dist"
PUBLIC_CONTACT = "info@osservatorioversilia.it"
LEGACY_CONTACT = "contatti@osservatorioversilia.it"
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"


def read(relative: str) -> str:
    path = DIST / relative
    assert path.exists(), f"File build mancante: {relative}"
    return path.read_text(encoding="utf-8")


def main() -> None:
    html_files = list(DIST.rglob("*.html"))
    assert html_files, "Nessuna pagina HTML nella build"

    social_pages = 0
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        assert LEGACY_CONTACT not in text, f"Recapito legacy ancora presente: {path}"

        if path.name == "offline.html":
            assert 'name="robots" content="noindex,nofollow"' in text, "Fallback offline non marcato noindex"
            assert 'property="og:image"' not in text, "Il fallback offline non deve avere metadata social"
            continue

        social_pages += 1
        assert 'property="og:image"' in text, f"og:image mancante: {path}"
        assert SOCIAL_IMAGE in text, f"Immagine social non canonica: {path}"
        assert 'name="twitter:card" content="summary_large_image"' in text, f"Twitter card mancante: {path}"

    project = read("progetto/index.html")
    assert "2026.08.14-v1.11.0" in project, "v1.11.0 assente dalla pagina progetto"
    assert "119 indicatori" in project, "Conteggio v1.11.0 assente dalla pagina progetto"
    assert PUBLIC_CONTACT in project, "Recapito pubblico assente dalla pagina progetto"

    feedback = read("segnala/index.html")
    assert PUBLIC_CONTACT in feedback, "Recapito pubblico assente dalla pagina segnala"

    bundle = read("assets/app-bundle.js")
    assert LEGACY_CONTACT not in bundle, "Recapito legacy ancora presente nel bundle"
    assert PUBLIC_CONTACT in bundle, "Recapito pubblico assente dal bundle"
    assert "2026.08.14-v1.11.0" in bundle, "v1.11.0 assente dal bundle"

    print(f"OK: identità pubblica, release v1.11 e social metadata verificati su {social_pages} pagine; fallback offline noindex")


if __name__ == "__main__":
    main()
