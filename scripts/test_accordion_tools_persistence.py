#!/usr/bin/env python3
"""Verifica che conteggi e frecce delle fisarmoniche non spariscano dopo i tap."""
from __future__ import annotations

import contextlib
import os
import re
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

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


def assert_tools(page: Page, label: str) -> None:
    headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
    require(headings.count() >= 4, f"{label}: intestazioni insufficienti")
    for index in range(headings.count()):
        heading = headings.nth(index)
        tools = heading.locator(":scope > .ux-section-tools")
        chevron = tools.locator(".ux-section-chevron")
        require(tools.count() == 1, f"{label}: strumenti mancanti nella sezione {index + 1}")
        require(tools.is_visible(), f"{label}: strumenti invisibili nella sezione {index + 1}")
        require(chevron.count() == 1 and chevron.is_visible(),
                f"{label}: freccia invisibile nella sezione {index + 1}")
        style = tools.evaluate(
            """element => {
              const style = getComputedStyle(element);
              return { display: style.display, opacity: style.opacity, visibility: style.visibility };
            }"""
        )
        require(style["display"] != "none" and style["opacity"] != "0" and style["visibility"] != "hidden",
                f"{label}: strumenti nascosti via CSS nella sezione {index + 1}: {style}")


def main() -> None:
    rendered = (DIST / "confronta" / "economia" / "index.html").read_text(encoding="utf-8")
    require(
        re.search(r"assets/ux-accordion\.js\?v=\d{8}-(?:\d+|v\d+)", rendered) is not None,
        "Il build non forza il caricamento versionato di ux-accordion.js",
    )

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
        page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
        page.wait_for_selector(".topic-controls .metric-group-heading.ux-section-toggle")
        assert_tools(page, "stato iniziale")

        # Ripete aperture e chiusure su sezioni diverse, aspettando abbastanza
        # da intercettare anche eventuali rimpiazzi asincroni delle intestazioni.
        for step, index in enumerate((1, 2, 3, 0, 1), start=1):
            headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
            target = headings.nth(index)
            target.scroll_into_view_if_needed()
            target.tap()
            page.wait_for_timeout(1100)
            assert_tools(page, f"dopo il tap {step}")

        # Anche la selezione di un indicatore dentro la sezione aperta non deve
        # far perdere conteggio o freccia dalle intestazioni.
        open_heading = page.locator('.topic-controls .metric-group-heading[aria-expanded="true"]').first
        if open_heading.count() == 1:
            control = open_heading.get_attribute("aria-controls")
            if control:
                button = page.locator(f"#{control} button").first
                if button.count() == 1:
                    button.tap()
                    page.wait_for_timeout(1100)
                    assert_tools(page, "dopo la selezione di un indicatore")

        require(not errors, f"Errori JavaScript durante il test: {errors}")
        context.close()
        browser.close()

    print("Persistenza fisarmoniche verificata: conteggi e frecce restano visibili dopo interazioni ripetute.")


if __name__ == "__main__":
    main()
