#!/usr/bin/env python3
"""Regression visuale: le intestazioni a fisarmonica non devono sovrapporre testo e strumenti."""
from __future__ import annotations

import contextlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import socket
import threading
from typing import Iterable

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path) -> Iterable[str]:
    old = Path.cwd()
    os.chdir(directory)
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
        os.chdir(old)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def overlaps(a: dict | None, b: dict | None, tolerance: float = 0.5) -> bool:
    if not a or not b:
        return False
    return not (
        a["x"] + a["width"] <= b["x"] + tolerance
        or b["x"] + b["width"] <= a["x"] + tolerance
        or a["y"] + a["height"] <= b["y"] + tolerance
        or b["y"] + b["height"] <= a["y"] + tolerance
    )


def check_headings(page, label: str) -> int:
    headings = page.locator(".metric-group-heading.ux-section-toggle")
    count = headings.count()
    for index in range(count):
        heading = headings.nth(index)
        title = heading.locator(":scope > strong")
        description = heading.locator(":scope > span:not(.ux-section-tools)")
        tools = heading.locator(":scope > .ux-section-tools")
        if not tools.count():
            continue
        tools_box = tools.bounding_box()
        if title.count():
            require(not overlaps(title.bounding_box(), tools_box),
                    f"Titolo sovrapposto a contatore/chevron in {label}: {heading.inner_text()!r}")
        if description.count():
            require(not overlaps(description.bounding_box(), tools_box),
                    f"Descrizione sovrapposta a contatore/chevron in {label}: {heading.inner_text()!r}")
    return count


def main() -> None:
    compare_pages = sorted(path.parent.name for path in (DIST / "confronta").glob("*/index.html"))
    town_pages = sorted(path.parent.name for path in (DIST / "comuni").glob("*/index.html"))
    require(compare_pages and town_pages, "Pagine di confronto/comunali non trovate")

    tested_headings = 0
    tested_pages = 0
    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1680, "height": 1000})

        for theme in compare_pages:
            page.goto(base + f"confronta/{theme}/", wait_until="networkidle")
            count = check_headings(page, f"confronta/{theme}")
            if count:
                tested_pages += 1
                tested_headings += count

        for town in town_pages:
            for theme in ("mobilita", "sicurezza"):
                page.goto(base + f"comuni/{town}/?tema={theme}", wait_until="networkidle")
                count = check_headings(page, f"comuni/{town}?tema={theme}")
                if count:
                    tested_pages += 1
                    tested_headings += count

        require(tested_pages > 0 and tested_headings > 0,
                "Il test non ha trovato alcuna pagina con fisarmoniche da verificare")

        page.goto(base + "confronta/mobilita/?indicatore=slowMobilityRoutes", wait_until="networkidle")
        slow = page.locator('[data-section="mobilita-lenta"]')
        require(slow.count() == 1 and slow.is_visible(),
                "Mobilità lenta deve essere una sezione della fisarmonica standard")
        require(page.locator('[data-percorsi-quick], [data-percorsi-stats]').count() == 0,
                "Non devono esistere box Percorsi paralleli alla grammatica degli indicatori")

        page.goto(base + "confronta/sicurezza/?indicatore=roadInjuries", wait_until="networkidle")
        require(page.locator(".crime-context").count() == 1,
                "Criminalità deve vivere nel tema Sicurezza e territorio")

        browser.close()

    print(
        f"Fisarmoniche verificate: {tested_headings} intestazioni su {tested_pages} pagine; "
        "nessuna sovrapposizione e nuova architettura coerente."
    )


if __name__ == "__main__":
    main()
