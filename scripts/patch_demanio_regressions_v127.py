#!/usr/bin/env python3
"""Aggancia i test v1.27 ai regression gate Costa e mare già presenti in CI."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/test_costa_mare_v123.py"
BROWSER = ROOT / "scripts/test_costa_mare_v123_browser.py"


def patch_wrapper() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    if "import test_demanio_marittimo_v127 as demanio" not in text:
        text = text.replace(
            "import test_costa_mare_v123_legacy as legacy\n",
            "import test_costa_mare_v123_legacy as legacy\nimport test_demanio_marittimo_v127 as demanio\n",
            1,
        )
    marker = "    legacy.assert_registry_and_ui(legacy_compatible_view(data))\n"
    addition = marker + "    if version_tuple(data.get(\"version\")) >= (1, 27, 0):\n        demanio.main()\n"
    if "demanio.main()" not in text:
        if marker not in text:
            raise RuntimeError("Costa data regression marker non trovato")
        text = text.replace(marker, addition, 1)
    WRAPPER.write_text(text, encoding="utf-8")


def patch_browser() -> None:
    text = BROWSER.read_text(encoding="utf-8")
    constants = 'NOT_APPLICABLE = ("Massarosa", "Seravezza", "Stazzema")\n'
    if "DEMANIO_METRICS =" not in text:
        if constants not in text:
            raise RuntimeError("Costanti Costa browser non trovate")
        text = text.replace(
            constants,
            constants + 'DEMANIO_METRICS = ("maritimeConcessions", "maritimeConcessionFeesDue")\n',
            1,
        )

    marker = "\ndef assert_towns(page: Page, base: str, mobile: bool) -> None:\n"
    function = '''
def assert_demanio(page: Page, base: str, mobile: bool) -> None:
    page.goto(
        urljoin(base, "confronta/ambiente/?indicatore=maritimeConcessions"),
        wait_until="networkidle",
    )
    page.wait_for_timeout(500)
    for key in DEMANIO_METRICS:
        open_metric(page, key)
        no_overflow(page, f"{key}/confronto")
        assert_applicability(page, key)
        assert_detail(page, key, mobile)
        selector = page.locator("#compare-bars select[data-composite-component]:visible")
        assert selector.count() == 1 and selector.locator("option").count() == 2, key
        if key == "maritimeConcessions":
            aria = visible_bar(page, "Viareggio").get_attribute("aria-label") or ""
            assert "359" in aria, aria
            selector.select_option("part-1")
            page.wait_for_timeout(220)
            aria = visible_bar(page, "Viareggio").get_attribute("aria-label") or ""
            assert "174" in aria, aria
            detail = page.locator("#compare-bars .coast-detail:visible").inner_text()
            assert "Licenze" in detail and "Atti formali" in detail
        else:
            aria = visible_bar(page, "Viareggio").get_attribute("aria-label") or ""
            assert "2.669.422" in aria, aria
            selector.select_option("part-1")
            page.wait_for_timeout(220)
            aria = visible_bar(page, "Viareggio").get_attribute("aria-label") or ""
            assert "1.704.536" in aria, aria
            detail = page.locator("#compare-bars .coast-detail:visible").inner_text()
            assert "Dovuto totale" in detail and "Canone minimo" in detail

    for key in DEMANIO_METRICS:
        page.goto(
            urljoin(base, f"comuni/massarosa/?tema=ambiente&indicatore={key}"),
            wait_until="networkidle",
        )
        page.wait_for_timeout(300)
        primary = page.locator("#town-topic .town-metric-primary strong").first.inner_text().strip().lower()
        assert primary == "n.a.", f"{key}: Massarosa non è n.a. ({primary})"
        applicability = page.locator("#town-topic .coast-not-applicable")
        assert applicability.count() == 1 and "non applicabile" in applicability.inner_text().lower()

'''
    if "def assert_demanio(" not in text:
        if marker not in text:
            raise RuntimeError("Costa browser regression marker non trovato")
        text = text.replace(marker, function + marker, 1)

    desktop_marker = "        assert_towns(desktop.new_page(), base, mobile=False)\n"
    if "assert_demanio(desktop.new_page()" not in text:
        if desktop_marker not in text:
            raise RuntimeError("Desktop browser marker non trovato")
        text = text.replace(
            desktop_marker,
            desktop_marker + "        assert_demanio(desktop.new_page(), base, mobile=False)\n",
            1,
        )
    mobile_marker = "        assert_towns(mobile.new_page(), base, mobile=True)\n"
    if "assert_demanio(mobile.new_page()" not in text:
        if mobile_marker not in text:
            raise RuntimeError("Mobile browser marker non trovato")
        text = text.replace(
            mobile_marker,
            mobile_marker + "        assert_demanio(mobile.new_page(), base, mobile=True)\n",
            1,
        )
    BROWSER.write_text(text, encoding="utf-8")


def main() -> None:
    patch_wrapper()
    patch_browser()
    print("Regression gate Demanio v1.27 agganciati ai test Costa e mare.")


if __name__ == "__main__":
    main()
