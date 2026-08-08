#!/usr/bin/env python3
"""Regressioni touch e interazioni responsive per confronti e schede comunali."""
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


def rectangles_overlap(first: dict | None, second: dict | None) -> bool:
    if not first or not second:
        return False
    return not (
        first["x"] + first["width"] <= second["x"] + 1
        or second["x"] + second["width"] <= first["x"] + 1
        or first["y"] + first["height"] <= second["y"] + 1
        or second["y"] + second["height"] <= first["y"] + 1
    )


def require_visible_chevron(heading: Locator, label: str) -> None:
    chevron = heading.locator(":scope > .ux-section-tools .ux-section-chevron")
    require(chevron.count() == 1 and chevron.is_visible(), f"{label}: freccia non visibile")
    box = chevron.bounding_box()
    require(bool(box and box["width"] >= 20 and box["height"] >= 20),
            f"{label}: freccia senza area utile: {box}")


def verify_heading_layout(heading: Locator, label: str) -> None:
    tools = heading.locator(":scope > .ux-section-tools")
    title = heading.locator(":scope > strong")
    description = heading.locator(":scope > span:not(.ux-section-tools)")
    require(tools.count() == 1 and title.count() == 1, f"{label}: struttura intestazione incompleta")
    tools_box = tools.bounding_box()
    title_box = title.bounding_box()
    require(not rectangles_overlap(title_box, tools_box), f"{label}: titolo sovrapposto agli strumenti")
    if description.count() == 1 and description.is_visible():
        require(not rectangles_overlap(description.bounding_box(), tools_box),
                f"{label}: descrizione sovrapposta agli strumenti")
    require_visible_chevron(heading, label)


def verify_touch_accordion(page: Page, selector: str, label: str) -> None:
    headings = page.locator(selector)
    require(headings.count() >= 2, f"{label}: servono almeno due sezioni")
    first_open = expanded_index(headings)
    require(first_open >= 0, f"{label}: nessuna sezione inizialmente aperta")
    target_index = closed_index(headings, first_open)
    require(target_index >= 0, f"{label}: nessuna sezione chiusa disponibile")
    initial = headings.nth(first_open)
    target = headings.nth(target_index)
    control = target.get_attribute("aria-controls")
    require(bool(control) and page.locator(f"#{control}").is_hidden(), f"{label}: target non inizialmente chiuso")
    target.tap()
    page.wait_for_timeout(100)
    require(target.get_attribute("aria-expanded") == "true", f"{label}: tap non apre la sezione")
    require(page.locator(f"#{control}").is_visible(), f"{label}: contenuto non visibile dopo il tap")
    require(initial.get_attribute("aria-expanded") == "false", f"{label}: la sezione precedente resta aperta")
    open_count = sum(1 for index in range(headings.count()) if headings.nth(index).get_attribute("aria-expanded") == "true")
    require(open_count == 1, f"{label}: attesa una sezione aperta, trovate {open_count}")


def verify_compare_mobile(page: Page, base: str) -> None:
    page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
    page.wait_for_selector(".topic-controls .metric-group-heading.ux-section-toggle")
    headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
    require(headings.count() >= 4, "Economia mobile: attese almeno quattro sottosezioni")
    for index in range(min(headings.count(), 4)):
        verify_heading_layout(headings.nth(index), f"Economia mobile, sezione {index + 1}")

    system_heading = headings.filter(has_text="Sistema produttivo").first
    require(system_heading.count() == 1, "Economia mobile: Sistema produttivo non trovato")
    if system_heading.get_attribute("aria-expanded") != "true":
        system_heading.tap()
        page.wait_for_timeout(100)
    buttons = system_heading.locator("xpath=..").locator(":scope > .metric-group-buttons")
    require(buttons.is_visible(), "Economia mobile: indicatori Sistema produttivo non visibili")
    before = page.evaluate("({viewport: innerWidth, doc: document.documentElement.scrollWidth, body: document.body.scrollWidth})")
    require(before["doc"] <= before["viewport"] + 1 and before["body"] <= before["viewport"] + 1,
            f"Economia mobile: overflow pagina {before}")
    require(buttons.evaluate("el => el.scrollWidth > el.clientWidth + 20"),
            "Economia mobile: la riga lunga degli indicatori non scorre autonomamente")
    buttons.evaluate("el => { el.scrollLeft = el.scrollWidth; }")
    require(buttons.evaluate("el => el.scrollLeft > 20"),
            "Economia mobile: impossibile scorrere gli indicatori")


def verify_town_mobile(page: Page, base: str) -> None:
    page.goto(base + "comuni/massarosa/?tema=economia&indicatore=income", wait_until="networkidle")
    page.wait_for_selector(".town-indicator-picker")
    require(page.locator(".town-context-nav .context-nav-row").count() == 0,
            "Scheda comunale mobile: la riga dei Comuni è stata reintrodotta")
    require(page.locator(".town-overview .ux-section-toggle").count() == 0,
            "Scheda comunale mobile: il Quadro del tema non deve essere una fisarmonica")
    require(page.locator(".town-overview .indicator-card-grid button:visible").count() >= 4,
            "Scheda comunale mobile: le carte del Quadro del tema non sono direttamente visibili")
    widths = page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
    require(widths["scroll"] <= widths["client"] + 1, f"Scheda comunale mobile: overflow {widths}")
    select = page.locator("[data-town-metric-select]")
    require(select.count() == 1 and select.is_visible(), "Scheda comunale mobile: selettore indicatore assente")
    select.select_option("businessValueAdded")
    page.wait_for_function("() => new URL(location.href).searchParams.get('indicatore') === 'businessValueAdded'")
    require(page.locator('.town-overview [data-indicator="businessValueAdded"]').count() == 0,
            "Scheda comunale mobile: indicatore selezionato duplicato nel quadro")


def verify_desktop_theme_scroll(page: Page, base: str) -> None:
    page.goto(base, wait_until="networkidle")
    page.wait_for_selector(".theme-card")
    page.wait_for_selector("#home-explorer")
    page.evaluate("window.scrollTo(0, 0)")
    page.locator(".theme-card").nth(1).click()
    page.wait_for_function(
        """() => {
          const target = document.getElementById('home-explorer');
          const header = document.getElementById('site-header-mount');
          const targetTop = target?.getBoundingClientRect().top ?? -1;
          const expectedTop = (header?.getBoundingClientRect().height || 70) + 12;
          return window.scrollY > 0 && Math.abs(targetTop - expectedTop) <= 6;
        }""",
        timeout=2500,
    )


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

        verify_compare_mobile(page, base)
        page.goto(base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident", wait_until="networkidle")
        page.wait_for_selector(".topic-controls .ux-section-toggle")
        verify_touch_accordion(page, ".topic-controls .ux-section-toggle", "Confronto Bilanci")
        verify_town_mobile(page, base)
        require(not errors, f"Errori JavaScript durante le interazioni touch: {errors}")
        context.close()

        desktop = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        desktop_page = desktop.new_page()
        desktop_errors: list[str] = []
        desktop_page.on("pageerror", lambda error: desktop_errors.append(str(error)))
        verify_desktop_theme_scroll(desktop_page, base)
        require(not desktop_errors, f"Errori JavaScript durante lo scroll desktop: {desktop_errors}")
        desktop.close()
        browser.close()

    print("Interazioni verificate: fisarmoniche dei confronti, Quadro comunale piatto, picker e responsive.")


if __name__ == "__main__":
    main()
