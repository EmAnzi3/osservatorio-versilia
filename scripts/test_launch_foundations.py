#!/usr/bin/env python3
"""Regression checks for public launch metadata, identity and social presence."""

from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "dist"
PUBLIC_CONTACT = "info@osservatorioversilia.it"
LEGACY_CONTACT = "contatti@osservatorioversilia.it"
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"
TWITTER_SITE = "@OssVersilia"
SOCIAL_PROFILES = (
    "https://www.facebook.com/osservatorioversilia",
    "https://www.instagram.com/osservatorioversilia/",
    "https://www.linkedin.com/company/osservatorioversilia",
    "https://x.com/OssVersilia",
)


def read(relative: str) -> str:
    path = DIST / relative
    assert path.exists(), f"File build mancante: {relative}"
    return path.read_text(encoding="utf-8")


def assert_one(text: str, token: str, path: Path) -> None:
    count = text.count(token)
    assert count == 1, f"Atteso un solo {token} in {path}, trovati {count}"


def assert_social_profiles(text: str, context: str) -> None:
    for url in SOCIAL_PROFILES:
        assert url in text, f"Profilo social mancante ({url}) in {context}"
    assert 'rel="me noreferrer"' in text, f"Rel dei profili social non coerente in {context}"
    assert 'target="_blank"' in text, f"Profili social non aperti come link esterni in {context}"


def is_noindex(text: str) -> bool:
    return 'name="robots" content="noindex' in text.lower()


def main() -> None:
    html_files = list(DIST.rglob("*.html"))
    assert html_files, "Nessuna pagina HTML nella build"

    social_pages = 0
    noindex_pages = 0
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        assert LEGACY_CONTACT not in text, f"Recapito legacy ancora presente: {path}"

        if path.name == "offline.html":
            assert is_noindex(text), "Fallback offline non marcato noindex"
            assert 'property="og:image"' not in text, "Il fallback offline non deve avere metadata social"
            noindex_pages += 1
            continue

        # Bozze e utility noindex non sono superfici social canoniche: possono
        # avere metadata parziali, ma non devono far fallire il contratto delle
        # pagine indicizzabili/pubblicabili.
        if is_noindex(text):
            noindex_pages += 1
            continue

        social_pages += 1
        for token in (
            'property="og:title"', 'property="og:description"', 'property="og:type"',
            'property="og:url"', 'property="og:site_name"', 'property="og:locale"',
            'property="og:image"', 'property="og:image:alt"', 'name="twitter:card"',
            'name="twitter:title"', 'name="twitter:description"', 'name="twitter:site"',
            'name="twitter:image"', 'name="twitter:image:alt"',
        ):
            assert_one(text, token, path)
        assert SOCIAL_IMAGE in text, f"Immagine social non canonica: {path}"
        assert 'name="twitter:card" content="summary_large_image"' in text, f"Twitter card mancante: {path}"
        assert f'name="twitter:site" content="{TWITTER_SITE}"' in text, f"Account X non dichiarato: {path}"

    home = read("index.html")
    assert 'data-social-placement="home"' in home, "Richiamo social assente dalla home"
    assert 'data-social-placement="footer"' in home, "Riferimenti social assenti dal footer della home"
    assert_social_profiles(home, "home")
    assert "assets/social-presence.css?v=20260816-v113" in home, "CSS social assente dalla home"
    assert "assets/social-presence.js?v=20260816-v113" in home, "JS social assente dalla home"

    project = read("progetto/index.html")
    assert "2026.08.14-v1.11.0" in project, "v1.11.0 assente dalla pagina progetto"
    assert "119 indicatori" in project, "Conteggio v1.11.0 assente dalla pagina progetto"
    assert PUBLIC_CONTACT in project, "Recapito pubblico assente dalla pagina progetto"
    assert 'data-social-placement="project"' in project, "Richiamo social assente dalla pagina progetto"
    assert 'data-social-placement="footer"' in project, "Riferimenti social assenti dal footer del progetto"
    assert_social_profiles(project, "pagina progetto")

    compare = read("confronta/demografia/index.html")
    assert 'data-social-placement="footer"' in compare, "Riferimenti social assenti da una pagina interna"
    assert 'data-social-placement="home"' not in compare, "Callout Home duplicato in una pagina interna"
    assert_social_profiles(compare, "footer pagina interna")

    feedback = read("segnala/index.html")
    assert PUBLIC_CONTACT in feedback, "Recapito pubblico assente dalla pagina segnala"

    bundle = read("assets/app-bundle.js")
    assert LEGACY_CONTACT not in bundle, "Recapito legacy ancora presente nel bundle"
    assert PUBLIC_CONTACT in bundle, "Recapito pubblico assente dal bundle"
    assert "2026.08.14-v1.11.0" in bundle, "v1.11.0 assente dal bundle"
    for url in SOCIAL_PROFILES:
        assert url not in bundle, f"Profilo social iniettato nel bundle invece che nell'asset dedicato: {url}"

    social_script = read("assets/social-presence.js")
    for url in SOCIAL_PROFILES:
        assert social_script.count(url) == 1, f"Profilo social non canonico o duplicato nell'asset: {url}"
    for placement in ("footer", "home", "project"):
        assert f'data-social-placement=\\"{placement}\\"' in social_script or f"data-social-placement=\"{placement}\"" in social_script, f"Blocco social {placement} assente dall'asset dedicato"
    assert 'meta[name="robots"][content*="noindex" i]' in social_script, "Le pagine noindex non sono escluse dall'enhancer social"

    social_css = read("assets/social-presence.css")
    assert ".social-callout" in social_css and ".footer-social" in social_css, "CSS social incompleto"
    assert "@media (max-width: 700px)" in social_css, "Regole mobile social assenti"

    print(
        f"OK: identità pubblica, release v1.11, presenza social e metadata Open Graph/X "
        f"verificati su {social_pages} pagine pubblicabili; {noindex_pages} pagine noindex escluse dal contratto social"
    )


if __name__ == "__main__":
    main()
