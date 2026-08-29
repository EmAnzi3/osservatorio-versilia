#!/usr/bin/env python3
"""Gate browser per aggregati e confronti di Investimenti e opere."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright


EXPECTED_COMPARE = {
    "publicWorks": ("1.409", "2.659"),
    "pnrrFunding": ("231", "306"),
    "pnrrConcluded": ("73,3%", "74,1%"),
}


def no_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def open_metric(page: Page, key: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f"Indicatore mancante: {key}"
    if not button.is_visible():
        group = button.locator(
            "xpath=ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' metric-group ')][1]"
        )
        assert group.count() == 1
        group.locator(":scope > .metric-group-heading").click()
        page.wait_for_timeout(150)
    button.click()
    page.wait_for_timeout(330)
    assert f"indicatore={key}" in page.url


def assert_compare(page: Page, base: str) -> None:
    page.goto(
        urljoin(base, "confronta/comunita/?indicatore=publicWorks"),
        wait_until="networkidle",
    )
    page.wait_for_timeout(600)
    assert "Investimenti e opere" in page.locator("body").inner_text()
    for key, (expected, forbidden) in EXPECTED_COMPARE.items():
        open_metric(page, key)
        no_overflow(page, f"confronto/{key}")
        definition = page.locator("#compare-definition").inner_text()
        assert expected in definition, f"{key}: aggregato canonico assente ({definition})"
        assert forbidden not in definition, f"{key}: ricompare la media semplice errata ({definition})"
        rows = page.locator("#compare-bars .bar-row:visible")
        assert rows.count() == 7
        legend = page.locator("#compare-bars .comparison-legend:visible")
        assert legend.count() == 1
        legend_text = legend.inner_text()
        if key == "publicWorks":
            assert "Valore pro capite Versilia" in legend_text
        elif key == "pnrrFunding":
            assert "Versilia · risorse PNRR per residente" in legend_text
        else:
            assert "Versilia · 74 su 101" in legend_text


def assert_town_position(
    page: Page,
    base: str,
    key: str,
    expected: tuple[str, ...],
    forbidden: tuple[str, ...],
) -> None:
    page.goto(
        urljoin(base, f"comuni/massarosa/?tema=comunita&indicatore={key}"),
        wait_until="networkidle",
    )
    page.wait_for_timeout(620)
    no_overflow(page, f"Massarosa/{key}")
    panel = page.locator("#town-topic .versilia-position")
    assert panel.count() == 1
    text = " ".join(panel.inner_text().split())
    folded = text.casefold()
    for token in expected:
        assert token.casefold() in folded, f"{key}: manca {token!r} in {text!r}"
    for token in forbidden:
        assert token.casefold() not in folded, f"{key}: confronto errato ancora presente ({text})"


def assert_towns(page: Page, base: str) -> None:
    assert_town_position(
        page,
        base,
        "publicWorks",
        ("Rispetto al valore Versilia", "0,0 €", "in linea", "Valore pro capite Versilia", "1.409"),
        ("−47", "+47", "2.659"),
    )
    assert_town_position(
        page,
        base,
        "pnrrFunding",
        ("Rispetto al valore Versilia", "+42,4 €", "Versilia · risorse PNRR per residente", "231"),
        ("−10", "+10", "306"),
    )
    assert_town_position(
        page,
        base,
        "pnrrConcluded",
        ("Rispetto alla quota Versilia", "+17,6 punti", "Versilia · 74 su 101", "73,3%"),
        ("+16,8", "74,1%"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width, height, mobile in ((1440, 1000, False), (390, 844, True)):
            context = browser.new_context(
                viewport={"width": width, "height": height}, is_mobile=mobile
            )
            assert_compare(context.new_page(), base)
            assert_towns(context.new_page(), base)
            context.close()
        browser.close()

    print("Browser Investimenti e opere: aggregati Versilia e scarti euro/p.p. verificati desktop/mobile.")


if __name__ == "__main__":
    main()
