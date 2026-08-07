#!/usr/bin/env python3
"""Regressioni touch reali per fisarmoniche e interazioni mobile."""
from __future__ import annotations

import contextlib
import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 16; SM-S942B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36"
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
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


def expanded_index(headings: Locator) -> int:
    for index in range(headings.count()):
        if headings.nth(index).get_attribute("aria-expanded") == "true":
            return index
    return -1


def closed_index(headings: Locator, exclude: int) -> int:
    for index in range(headings.count()):
        if index != exclude and headings.nth(index).get_attribute("aria-expanded") == "false":
            return index
    return -1


def verify_touch_accordion(page: Page, selector: str, label: str) -> None:
    headings = page.locator(selector)
    require(headings.count() >= 2, f"{label}: servono almeno due sezioni")

    first_open = expanded_index(headings)
    require(first_open >= 0, f"{label}: nessuna sezione inizialmente aperta")
    target_index = closed_index(headings, first_open)
    require(target_index >= 0, f"{label}: nessuna seconda sezione chiusa disponibile")

    initial = headings.nth(first_open)
    target = headings.nth(target_index)
    target_control = target.get_attribute("aria-controls")
    require(bool(target_control), f"{label}: aria-controls mancante")
    require(page.locator(f"#{target_control}").is_hidden(), f"{label}: sezione target non inizialmente chiusa")

    target.scroll_into_view_if_needed()
    target.tap()
    page.wait_for_timeout(80)

    require(target.get_attribute("aria-expanded") == "true",
            f"{label}: il tap non apre la sezione selezionata")
    require(page.locator(f"#{target_control}").is_visible(),
            f"{label}: il contenuto della sezione selezionata resta nascosto")
    require(initial.get_attribute("aria-expanded") == "false",
            f"{label}: su mobile la sezione precedente non viene chiusa")
    require(headings.locator('[aria-expanded="true"]').count() == 0,
            f"{label}: selettore annidato inatteso")

    open_count = sum(
        1 for index in range(headings.count())
        if headings.nth(index).get_attribute("aria-expanded") == "true"
    )
    require(open_count == 1, f"{label}: attese una sola sezione aperta, trovate {open_count}")

    # Un secondo tap deve richiudere proprio la sezione appena aperta.
    target.tap()
    page.wait_for_timeout(80)
    require(target.get_attribute("aria-expanded") == "false",
            f"{label}: il secondo tap non richiude la sezione")
    require(page.locator(f"#{target_control}").is_hidden(),
            f"{label}: il contenuto resta visibile dopo la chiusura")


def main() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent=ANDROID_UA,
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2,
        )
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        page.goto(
            base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident",
            wait_until="networkidle",
        )
        page.wait_for_selector(".topic-controls .ux-section-toggle")
        verify_touch_accordion(
            page,
            ".topic-controls .ux-section-toggle",
            "Confronto Bilanci",
        )

        page.goto(
            base + "comuni/massarosa/?tema=demografia&indicatore=population",
            wait_until="networkidle",
        )
        page.wait_for_selector(".indicator-groups .ux-section-toggle")
        verify_touch_accordion(
            page,
            ".indicator-groups .ux-section-toggle",
            "Scheda comunale",
        )

        require(not errors, f"Errori JavaScript durante le interazioni touch: {errors}")
        context.close()
        browser.close()

    print("Interazioni mobile verificate: i tap aprono e chiudono la sezione corretta su confronto e scheda comunale.")


if __name__ == "__main__":
    main()
