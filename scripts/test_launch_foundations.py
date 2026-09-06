#!/usr/bin/env python3
"""Regression checks for public launch metadata, identity and social presence."""

import contextlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import socket
import threading

from build_static_safe import UX_ASSET_VERSION

DIST = Path(__file__).resolve().parents[1] / "dist"
PUBLIC_CONTACT = "info@osservatorioversilia.it"
LEGACY_CONTACT = "contatti@osservatorioversilia.it"
SOCIAL_IMAGE = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"
TWITTER_SITE = "@OssVersilia"
SOCIAL_ASSET_VERSION = UX_ASSET_VERSION
SOCIAL_PROFILES = (
    "https://www.facebook.com/osservatorioversilia",
    "https://www.instagram.com/osservatorioversilia/",
    "https://www.linkedin.com/company/osservatorioversilia",
    "https://x.com/OssVersilia",
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def local_server():
    old_cwd = Path.cwd()
    os.chdir(DIST)
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        httpd = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
    finally:
        os.chdir(old_cwd)


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


def browser_social_checks_at(base: str) -> None:
    from playwright.sync_api import sync_playwright

    base = base.rstrip("/") + "/"
    cases = (
        ("", "home", ".home-hero"),
        ("progetto/", "project", ".editorial-page"),
        ("confronta/demografia/", None, ".topic-hero"),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1365, "height": 900})

        for relative, callout_name, ready_selector in cases:
            page.goto(base + relative, wait_until="domcontentloaded")
            page.locator(ready_selector).wait_for(timeout=15000)
            footer = page.locator('[data-social-placement="footer"]')
            footer.wait_for(timeout=10000)
            assert footer.count() == 1, f"Footer social duplicato in {relative or 'home'}"
            assert footer.locator("a.social-profile-link").count() == 4, f"Profili footer incompleti in {relative or 'home'}"
            for url in SOCIAL_PROFILES:
                assert footer.locator(f'a[href="{url}"]').count() == 1, f"Link {url} assente dal footer runtime"

            if callout_name:
                callout = page.locator(f'[data-social-placement="{callout_name}"]')
                callout.wait_for(timeout=10000)
                assert callout.count() == 1, f"Callout {callout_name} duplicato"
                assert callout.locator("a.social-profile-link").count() == 4, f"Profili incompleti nel callout {callout_name}"
            else:
                assert page.locator('[data-social-placement="home"], [data-social-placement="project"]').count() == 0, "Callout editoriale presente su pagina interna"

            page.wait_for_timeout(250)
            assert page.locator('[data-social-placement="footer"]').count() == 1, f"Footer social instabile in {relative or 'home'}"

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(base, wait_until="domcontentloaded")
        mobile.locator(".home-hero").wait_for(timeout=15000)
        mobile_callout = mobile.locator('[data-social-placement="home"]')
        mobile_callout.wait_for(timeout=10000)
        fits = mobile_callout.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        assert fits, "Il callout social genera overflow orizzontale su mobile"
        assert mobile_callout.locator("a.social-profile-link").count() == 4, "Profili social mobile incompleti"

        page.goto(base + "confronta/meteo-clima/", wait_until="domcontentloaded")
        assert page.locator('[data-social-placement]').count() == 0, "La bozza Meteo noindex non deve ricevere riferimenti social"

        browser.close()


def browser_social_checks() -> None:
    configured_base = os.environ.get("OV_TEST_BASE")
    if configured_base:
        browser_social_checks_at(configured_base)
        return
    with local_server() as base:
        browser_social_checks_at(base)


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
    assert f"assets/social-presence.css?v={SOCIAL_ASSET_VERSION}" in home, "CSS social assente dalla home"
    assert f"assets/social-presence.js?v={SOCIAL_ASSET_VERSION}" in home, "JS social assente dalla home"

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
    assert 'data-social-placement="footer"' in social_script, "Blocco footer assente dall'asset social"
    assert "callout('home')" in social_script, "Callout Home assente dall'asset social"
    assert "callout('project')" in social_script, "Callout Progetto assente dall'asset social"
    assert 'meta[name="robots"][content*="noindex" i]' in social_script, "Le pagine noindex non sono escluse dall'enhancer social"
    assert "new MutationObserver(enhance)" in social_script, "L'enhancer social non protegge i riferimenti dai rerender runtime"

    social_css = read("assets/social-presence.css")
    assert ".social-callout" in social_css and ".footer-social" in social_css, "CSS social incompleto"
    assert "@media (max-width: 700px)" in social_css, "Regole mobile social assenti"

    browser_social_checks()

    print(
        f"OK: identità pubblica, release v1.11, presenza social e metadata Open Graph/X "
        f"verificati in statico e browser su {social_pages} pagine pubblicabili; "
        f"{noindex_pages} pagine noindex escluse dal contratto social"
    )


if __name__ == "__main__":
    main()
