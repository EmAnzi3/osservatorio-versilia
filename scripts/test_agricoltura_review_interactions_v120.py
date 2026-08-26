#!/usr/bin/env python3
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass


def main() -> None:
    if not DIST.exists():
        raise SystemExit("dist/ non esiste: eseguire prima build_static_brand.py")

    handler = partial(QuietHandler, directory=str(DIST))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})

            # 1) Lo switch, ora collocato nel box del grafico, deve essere realmente interattivo.
            page.goto(f"{base}/confronta/ambiente/?indicatore=agriculturalUsedArea", wait_until="networkidle")
            page.wait_for_selector('#compare-bars button[data-scale="normalized"]')
            raw = page.locator('#compare-bars button[data-scale="raw"]')
            normalized = page.locator('#compare-bars button[data-scale="normalized"]')
            assert "active" in (raw.get_attribute("class") or ""), "Valore assoluto non attivo all'apertura"
            normalized.click()
            page.wait_for_function("document.querySelector('#compare-bars button[data-scale=\"normalized\"]')?.classList.contains('active')")
            heading = page.locator("#compare-definition h2").inner_text().strip()
            assert "Quota" in heading and "superficie comunale" in heading, heading
            first_value = page.locator("#compare-bars .bar-row strong").first.inner_text().strip()
            assert "%" in first_value, f"Lettura rapportata non applicata: {first_value}"
            raw.click()
            page.wait_for_function("document.querySelector('#compare-bars button[data-scale=\"raw\"]')?.classList.contains('active')")
            first_value_raw = page.locator("#compare-bars .bar-row strong").first.inner_text().strip()
            assert "ha" in first_value_raw, f"Ritorno al valore assoluto non applicato: {first_value_raw}"

            # 2) Profilo colture comunale: quota sul totale Versilia della coltura, non scarto dalla media.
            page.goto(f"{base}/comuni/pietrasanta/?tema=ambiente&indicatore=cropProfile", wait_until="networkidle")
            selector = page.locator("select[data-composite-choice]")
            selector.select_option(label="Vite")
            page.wait_for_function("document.querySelector('[data-composite-primary-label]')?.textContent.trim() === 'Vite'")
            panel = page.locator(".composite-versilia-position")
            overline = panel.locator(".overline").inner_text().strip()
            assert overline == "Quota sul totale Versilia", overline
            headline = panel.locator("[data-composite-delta]").evaluate("el => el.childNodes[0].textContent.trim()")
            assert headline == "16,25%", f"Quota Vite Pietrasanta attesa 16,25%, trovata {headline}"
            aggregate = panel.locator("[data-composite-aggregate-value]").inner_text().strip()
            assert aggregate == "24,37 ha", f"Totale Vite Versilia atteso 24,37 ha, trovato {aggregate}"

            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    print("OK: switch assoluto/rapportato e quota comunale colture sul totale Versilia verificati in browser.")


if __name__ == "__main__":
    main()
