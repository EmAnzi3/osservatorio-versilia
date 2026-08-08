#!/usr/bin/env python3
"""Mobile regression checks with the town-profile v2 interaction model."""
from __future__ import annotations

import os

from playwright.sync_api import Page, sync_playwright

import test_mobile_interactions as legacy


def require(condition: bool, message: str) -> None:
    legacy.require(condition, message)


def verify_compare_mobile_layout(page: Page, base: str) -> None:
    page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
    page.wait_for_selector(".topic-controls .metric-group-heading.ux-section-toggle")
    headings = page.locator(".topic-controls .metric-group-heading.ux-section-toggle")
    require(headings.count() >= 4, "Economia mobile: attese almeno quattro sottosezioni")

    for index in range(min(headings.count(), 4)):
        legacy.verify_mobile_heading_layout(
            headings.nth(index),
            ":scope > strong",
            ":scope > span:not(.ux-section-tools)",
            f"Economia mobile, sezione {index + 1}",
        )

    legacy.verify_indicator_scroll_containment(page)

    first_open = legacy.expanded_index(headings)
    target_index = legacy.closed_index(headings, first_open)
    require(target_index >= 0, "Economia mobile: nessuna sezione chiusa da aprire")
    target = headings.nth(target_index)
    target.tap()
    page.wait_for_timeout(100)
    require(target.get_attribute("aria-expanded") == "true",
            "Economia mobile: la sezione scelta non risulta aperta")
    legacy.require_visible_chevron(target, "Economia mobile, freccia dopo apertura")


def verify_town_v2_mobile(page: Page, base: str) -> None:
    page.goto(
        base + "comuni/massarosa/?tema=economia&indicatore=income",
        wait_until="networkidle",
    )
    page.wait_for_selector("#town-topic.town-layout-v2 .town-v2-picker")

    require(page.locator(".town-v2-picker").count() == 1,
            "Scheda comunale v2: selettore indicatore mancante o duplicato")
    require(page.locator(".town-v2-source-controls").evaluate("el => getComputedStyle(el).display") == "none",
            "Scheda comunale v2: il vecchio catalogo superiore è ancora visibile")

    groups = page.locator(".town-v2-overview .indicator-group")
    require(groups.count() >= 4, "Scheda comunale v2: quadro del tema incompleto")
    require(page.locator(".town-v2-overview .ux-section-toggle").count() == 0,
            "Scheda comunale v2: il quadro del tema è ancora una fisarmonica")
    for index in range(groups.count()):
        cards = groups.nth(index).locator(":scope > .indicator-card-grid")
        require(cards.count() == 1 and cards.is_visible(),
                f"Scheda comunale v2: gruppo {index + 1} non direttamente consultabile")

    picker = page.locator(".town-v2-picker")
    picker.locator("summary").tap()
    require(picker.get_attribute("open") is not None,
            "Scheda comunale v2: il picker non si apre con tap")
    choice = page.locator('[data-town-v2-metric="businessValueAdded"]')
    require(choice.count() == 1, "Scheda comunale v2: indicatore nel picker non trovato")
    choice.tap()
    page.wait_for_function(
        "() => new URLSearchParams(location.search).get('indicatore') === 'businessValueAdded'"
    )
    page.wait_for_selector('.town-v2-picker[data-active-metric="businessValueAdded"]')

    widths = page.evaluate(
        "({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})"
    )
    require(widths["scroll"] <= widths["client"] + 1,
            f"Scheda comunale v2: overflow orizzontale {widths}")


def main() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with legacy.server(legacy.DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent=legacy.ANDROID_UA,
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2,
        )
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        verify_compare_mobile_layout(page, base)

        page.goto(
            base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident",
            wait_until="networkidle",
        )
        page.wait_for_selector(".topic-controls .ux-section-toggle")
        legacy.verify_touch_accordion(
            page,
            ".topic-controls .ux-section-toggle",
            "Confronto Bilanci",
        )

        verify_town_v2_mobile(page, base)
        require(not errors, f"Errori JavaScript durante le interazioni touch: {errors}")
        context.close()

        desktop = browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        desktop_page = desktop.new_page()
        desktop_errors: list[str] = []
        desktop_page.on("pageerror", lambda error: desktop_errors.append(str(error)))
        legacy.verify_desktop_theme_scroll(desktop_page, base)
        require(not desktop_errors, f"Errori JavaScript durante lo scroll desktop: {desktop_errors}")
        desktop.close()
        browser.close()

    print("Interazioni verificate: fisarmoniche confronto, picker comunale v2, quadro tema e scroll desktop.")


if __name__ == "__main__":
    main()
