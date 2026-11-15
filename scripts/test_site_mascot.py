#!/usr/bin/env python3
"""Versilia, la mascotte che invita a Chiedi: presente in tutte le pagine pubbliche
(tranne Chiedi, offline e noindex), discreta, chiudibile e che porta la domanda a Chiedi."""
from __future__ import annotations

import argparse
import functools
import http.server
import re
import threading
from pathlib import Path

from inject_site_mascot import excluded

ROOT = Path(__file__).resolve().parents[1]


def static(dist: Path) -> int:
    pages = 0
    for path in sorted(dist.rglob("*.html")):
        rel = path.relative_to(dist).as_posix()
        text = path.read_text(encoding="utf-8")
        scripts = re.findall(r'<script src="([^"]*assets/mascotte\.js\?v=[0-9a-f]{10})" defer></script>', text)
        styles = re.findall(r'<link rel="stylesheet" href="([^"]*assets/mascotte\.css\?v=[0-9a-f]{10})">', text)
        if excluded(rel, text):
            assert not scripts and not styles, f"mascot_on_excluded_page:{rel}"
            continue
        assert len(scripts) == 1 and len(styles) == 1, f"mascot_missing_or_duplicated:{rel}"
        for ref in scripts + styles:
            assert (path.parent / ref.split("?")[0]).resolve().is_file(), f"mascot_asset_unresolved:{rel}:{ref}"
        pages += 1
    assert pages >= 100, f"mascot_pages_too_few:{pages}"
    for page in ("index.html", "comuni/massarosa/index.html", "dossier/index.html", "stato-dati/index.html"):
        assert "assets/mascotte.js" in (dist / page).read_text(encoding="utf-8"), f"mascot_missing:{page}"
    assert "assets/mascotte.js" not in (dist / "chiedi/index.html").read_text(encoding="utf-8"), "mascot_on_chiedi"
    for asset in ("assets/mascotte/versilia-160.webp", "assets/mascotte/versilia-320.webp"):
        size = (dist / asset).stat().st_size
        assert 1_000 < size < 60_000, f"mascot_image_size:{asset}:{size}"
    js = (dist / "assets/mascotte.js").read_text(encoding="utf-8")
    for marker in ("Ciao, sono Versilia!", "Cosa vuoi sapere sul nostro territorio?", "Non mostrare più", "min-width: 720px"):
        assert marker in js, f"mascot_marker_missing:{marker}"
    css = (dist / "assets/mascotte.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion:reduce" in css and "@media print" in css, "mascot_motion_or_print_rule_missing"
    return pages


def browser(dist: Path) -> None:
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(dist)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # Computer: saluto automatico una volta per visita, chiusura, domanda portata a Chiedi.
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "comuni/massarosa/")
            page.wait_for_selector("#vm-bubble:not([hidden])", timeout=8000)
            assert page.evaluate("document.activeElement?.id") != "vm-input", "mascot_steals_focus"
            box = page.locator("#vm-bubble").bounding_box()
            assert box and box["x"] + box["width"] <= 1280 and box["y"] >= 0, f"mascot_bubble_off_screen:{box}"
            # Nessun elemento della pagina (barre fisse, intestazione) deve coprire fumetto o mascotte.
            for y in (0, 450, 900, 1800, 3600):
                page.evaluate(f"scrollTo(0, {y})")
                page.wait_for_timeout(120)
                covered = page.evaluate("""() => {
                    const out = [];
                    for (const el of document.querySelectorAll('#vm-bubble, .vm-avatar')) {
                      const r = el.getBoundingClientRect();
                      for (let i = 1; i < 6; i++) for (let j = 1; j < 6; j++) {
                        const x = r.left + r.width * i / 6, y = r.top + r.height * j / 6;
                        const hit = document.elementFromPoint(x, y);
                        if (hit && !hit.closest('#versilia-mascot')) out.push(`${Math.round(x)},${Math.round(y)}:${hit.className || hit.tagName}`);
                      }
                    }
                    return out; }""")
                assert not covered, f"mascot_covered_at_scroll_{y}:{covered[:3]}"
            page.evaluate("scrollTo(0, 0)")
            page.keyboard.press("Tab")
            page.click(".vm-close")
            assert page.locator("#vm-bubble").is_hidden(), "mascot_close_failed"
            page.goto(base + "comuni/viareggio/")
            page.wait_for_selector(".vm-avatar")
            page.wait_for_timeout(3500)
            assert page.locator("#vm-bubble").is_hidden(), "mascot_greets_twice_per_visit"
            page.click(".vm-avatar")
            assert page.evaluate("document.activeElement?.id") == "vm-input", "mascot_input_not_focused"
            page.keyboard.press("Escape")
            assert page.locator("#vm-bubble").is_hidden(), "mascot_escape_failed"
            page.click(".vm-avatar")
            page.fill("#vm-input", "reddito a Camaiore")
            page.keyboard.press("Enter")
            page.wait_for_selector("#ask-log .ask-reply", timeout=30000)
            reply = page.locator("#ask-log .ask-reply").first.text_content() or ""
            assert "Camaiore" in reply and "€" in reply, f"mascot_question_not_answered:{reply}"
            assert "q=" not in page.url, f"mascot_query_left_in_url:{page.url}"
            assert page.locator("#versilia-mascot").count() == 0, "mascot_on_chiedi_runtime"
            assert not errors, errors
            page.close()
            # Telefono: niente saluto automatico, nessuno scorrimento orizzontale, «Non mostrare più» persiste.
            phone = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True).new_page()
            phone.goto(base + "comuni/viareggio/")
            phone.wait_for_selector(".vm-avatar")
            phone.wait_for_timeout(3500)
            assert phone.locator("#vm-bubble").is_hidden(), "mascot_autoopens_on_phone"
            phone.tap(".vm-avatar")
            box = phone.locator("#vm-bubble").bounding_box()
            assert box and box["x"] >= 0 and box["x"] + box["width"] <= 390, f"mascot_bubble_off_phone:{box}"
            assert phone.evaluate("document.documentElement.scrollWidth <= innerWidth"), "mascot_horizontal_scroll"
            phone.tap(".vm-hide")
            phone.reload()
            phone.wait_for_timeout(1200)
            assert phone.locator("#versilia-mascot").count() == 0, "mascot_hide_not_remembered"
            # Movimento ridotto: nessuna animazione.
            calm = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce").new_page()
            calm.goto(base + "index.html")
            calm.wait_for_selector(".vm-avatar")
            names = calm.evaluate("[...document.querySelectorAll('.vm, .vm-avatar')].map(e => getComputedStyle(e).animationName)")
            assert all(name == "none" for name in names), f"mascot_animates_with_reduced_motion:{names}"
            browser.close()
    finally:
        server.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default=str(ROOT / "dist"))
    args = parser.parse_args()
    dist = Path(args.dist)
    pages = static(dist)
    browser(dist)
    print(f"Mascotte Versilia PASS: {pages} pagine, saluto una volta per visita (solo schermi larghi), "
          "chiusura, Esc, «Non mostrare più», domanda portata a Chiedi, telefono e movimento ridotto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
