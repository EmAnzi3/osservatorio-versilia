#!/usr/bin/env python3
"""Regressioni touch reali e interazioni responsive."""
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
    require(chevron.count() == 1, f"{label}: freccia mancante")
    require(chevron.is_visible(), f"{label}: freccia non visibile")
    box = chevron.bounding_box()
    require(bool(box and box["width"] >= 20 and box["height"] >= 20),
            f"{label}: freccia senza area visibile: {box}")
    style = chevron.evaluate(
        """element => {
          const style = getComputedStyle(element);
          return { opacity: style.opacity, visibility: style.visibility, color: style.color };
        }"""
    )
    require(style["opacity"] != "0" and style["visibility"] != "hidden",
            f"{label}: freccia nascosta via CSS: {style}")


def verify_mobile_heading_layout(
    heading: Locator,
    title_selector: str,
    description_selector: str,
    label: str,
) -> None:
    tools = heading.locator(":scope > .ux-section-tools")
    title = heading.locator(title_selector)
    description = heading.locator(description_selector)
    require(tools.count() == 1, f"{label}: strumenti fisarmonica mancanti")
    require(title.count() == 1, f"{label}: titolo sezione mancante")

    tools_box = tools.bounding_box()
    title_box = title.bounding_box()
    require(not rectangles_overlap(title_box, tools_box),
            f"{label}: titolo e strumenti si sovrappongono: titolo={title_box}, tools={tools_box}")

    if description.count() == 1 and description.is_visible():
        description_box = description.bounding_box()
        require(not rectangles_overlap(description_box, tools_box),
                f"{label}: descrizione e strumenti si sovrappongono: descrizione={description_box}, tools={tools_box}")
        if title_box and tools_box and description_box:
            first_row_bottom = max(
                title_box["y"] + title_box["height"],
                tools_box["y"] + tools_box["height"],
            )
            require(description_box["y"] >= first_row_bottom - 1,
                    f"{label}: descrizione non disposta sotto la prima riga")

    require_visible_chevron(heading, label)


def verify_indicator_scroll_containment(page: Page) -> None:
    headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
    system_heading = headings.filter(has_text="Sistema produttivo").first
    require(system_heading.count() == 1, "Economia mobile: intestazione Sistema produttivo non trovata")

    if system_heading.get_attribute("aria-expanded") != "true":
        system_heading.tap()
        page.wait_for_timeout(120)
    require(system_heading.get_attribute("aria-expanded") == "true",
            "Economia mobile: Sistema produttivo non si apre")

    group = system_heading.locator("xpath=..")
    buttons = group.locator(":scope > .metric-group-buttons")
    require(buttons.count() == 1 and buttons.is_visible(),
            "Economia mobile: riga indicatori di Sistema produttivo assente")

    before = page.evaluate(
        """() => {
          const heading = [...document.querySelectorAll('.topic-controls .metric-group-heading.ux-section-toggle')]
            .find(el => el.textContent.includes('Sistema produttivo'));
          const group = heading?.parentElement;
          const buttons = group?.querySelector(':scope > .metric-group-buttons');
          const tools = heading?.querySelector(':scope > .ux-section-tools');
          const hb = heading?.getBoundingClientRect();
          const tb = tools?.getBoundingClientRect();
          return {
            viewport: window.innerWidth,
            documentScrollWidth: document.documentElement.scrollWidth,
            bodyScrollWidth: document.body.scrollWidth,
            headingLeft: hb?.left ?? -1,
            headingRight: hb?.right ?? -1,
            toolsLeft: tb?.left ?? -1,
            toolsRight: tb?.right ?? -1,
            buttonsClientWidth: buttons?.clientWidth ?? 0,
            buttonsScrollWidth: buttons?.scrollWidth ?? 0,
            buttonsScrollLeft: buttons?.scrollLeft ?? -1
          };
        }"""
    )
    require(before["documentScrollWidth"] <= before["viewport"] + 1,
            f"Economia mobile: il documento scorre orizzontalmente: {before}")
    require(before["bodyScrollWidth"] <= before["viewport"] + 1,
            f"Economia mobile: il body si allarga oltre il viewport: {before}")
    require(before["headingLeft"] >= -1 and before["headingRight"] <= before["viewport"] + 1,
            f"Economia mobile: intestazione fuori viewport: {before}")
    require(before["toolsLeft"] >= -1 and before["toolsRight"] <= before["viewport"] + 1,
            f"Economia mobile: conteggio/freccia fuori viewport: {before}")
    require(before["buttonsScrollWidth"] > before["buttonsClientWidth"] + 20,
            f"Economia mobile: la riga lunga non ha un proprio overflow orizzontale: {before}")

    # Scorre soltanto la riga dei pill: la testata deve restare immobile.
    buttons.evaluate("el => { el.scrollLeft = el.scrollWidth; }")
    page.wait_for_timeout(100)
    after = page.evaluate(
        """() => {
          const heading = [...document.querySelectorAll('.topic-controls .metric-group-heading.ux-section-toggle')]
            .find(el => el.textContent.includes('Sistema produttivo'));
          const group = heading?.parentElement;
          const buttons = group?.querySelector(':scope > .metric-group-buttons');
          const tools = heading?.querySelector(':scope > .ux-section-tools');
          const hb = heading?.getBoundingClientRect();
          const tb = tools?.getBoundingClientRect();
          return {
            viewport: window.innerWidth,
            documentScrollWidth: document.documentElement.scrollWidth,
            headingLeft: hb?.left ?? -1,
            headingRight: hb?.right ?? -1,
            toolsLeft: tb?.left ?? -1,
            toolsRight: tb?.right ?? -1,
            buttonsScrollLeft: buttons?.scrollLeft ?? 0
          };
        }"""
    )
    require(after["buttonsScrollLeft"] > 20,
            f"Economia mobile: la riga indicatori non scorre autonomamente: {after}")
    require(after["documentScrollWidth"] <= after["viewport"] + 1,
            f"Economia mobile: lo scroll dei pill allarga il documento: {after}")
    require(abs(after["headingLeft"] - before["headingLeft"]) <= 1
            and abs(after["headingRight"] - before["headingRight"]) <= 1,
            f"Economia mobile: la testata si sposta insieme ai pill: prima={before}, dopo={after}")
    require(abs(after["toolsLeft"] - before["toolsLeft"]) <= 1
            and abs(after["toolsRight"] - before["toolsRight"]) <= 1,
            f"Economia mobile: conteggio/freccia si spostano insieme ai pill: prima={before}, dopo={after}")


def verify_mobile_accordion_layout(page: Page, base: str) -> None:
    page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
    page.wait_for_selector(".topic-controls .metric-group-heading.ux-section-toggle")
    headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
    require(headings.count() >= 4, "Economia mobile: attese almeno quattro sottosezioni")

    for index in range(min(headings.count(), 4)):
        verify_mobile_heading_layout(
            headings.nth(index),
            ":scope > strong",
            ":scope > span:not(.ux-section-tools)",
            f"Economia mobile, sezione {index + 1}",
        )

    verify_indicator_scroll_containment(page)

    first_open = expanded_index(headings)
    target_index = closed_index(headings, first_open)
    require(target_index >= 0, "Economia mobile: nessuna sezione chiusa da aprire")
    target = headings.nth(target_index)
    target.tap()
    page.wait_for_timeout(100)
    require(target.get_attribute("aria-expanded") == "true",
            "Economia mobile: la sezione scelta non risulta aperta")
    require_visible_chevron(target, "Economia mobile, freccia dopo apertura")

    page.goto(
        base + "comuni/massarosa/?tema=economia&indicatore=income",
        wait_until="networkidle",
    )
    page.wait_for_selector(".metric-catalog .metric-group-heading.ux-section-toggle")
    town_headings = page.locator(".metric-catalog .metric-group-heading.ux-section-toggle")
    for index in range(min(town_headings.count(), 4)):
        verify_mobile_heading_layout(
            town_headings.nth(index),
            ":scope > strong",
            ":scope > span:not(.ux-section-tools)",
            f"Scheda Massarosa mobile, sezione {index + 1}",
        )


def verify_desktop_theme_scroll(page: Page, base: str) -> None:
    page.goto(base, wait_until="networkidle")
    page.wait_for_selector(".theme-card")
    page.wait_for_selector("#home-explorer")
    page.evaluate("window.scrollTo(0, 0)")

    # Il click su una tematica deve portare il pannello dei grafici subito
    # sotto l'header anche su desktop, come già avviene su smartphone.
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
    geometry = page.evaluate(
        """() => {
          const target = document.getElementById('home-explorer');
          const header = document.getElementById('site-header-mount');
          return {
            scrollY: window.scrollY,
            targetTop: target?.getBoundingClientRect().top ?? -1,
            expectedTop: (header?.getBoundingClientRect().height || 70) + 12
          };
        }"""
    )
    require(geometry["scrollY"] > 0, "Desktop: il click sulla tematica non scorre la pagina")
    require(abs(geometry["targetTop"] - geometry["expectedTop"]) <= 6,
            f"Desktop: pannello grafici non allineato sotto l'header: {geometry}")


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

        verify_mobile_accordion_layout(page, base)

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
        page.wait_for_selector(".metric-catalog .ux-section-toggle")
        verify_touch_accordion(
            page,
            ".metric-catalog .ux-section-toggle",
            "Scheda comunale",
        )

        require(not errors, f"Errori JavaScript durante le interazioni touch: {errors}")
        context.close()

        desktop = browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        desktop_page = desktop.new_page()
        desktop_errors: list[str] = []
        desktop_page.on("pageerror", lambda error: desktop_errors.append(str(error)))
        verify_desktop_theme_scroll(desktop_page, base)
        require(not desktop_errors, f"Errori JavaScript durante lo scroll desktop: {desktop_errors}")
        desktop.close()
        browser.close()

    print("Interazioni verificate: fisarmoniche mobili contenute nel viewport, scroll dei soli indicatori e salto temi desktop attivo.")


if __name__ == "__main__":
    main()
