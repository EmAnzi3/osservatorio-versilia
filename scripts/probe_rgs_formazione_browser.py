#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from playwright.sync_api import sync_playwright

URL = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"


def compact(text: str, limit: int = 8000) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def main() -> None:
    interesting = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="it-IT",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        )
        page = context.new_page()

        def on_response(response):
            url = response.url
            ctype = (response.headers.get("content-type") or "").lower()
            low = url.lower()
            if any(token in low for token in ("formaz", "api", "rest", "ajax", "filter", "chart", "graph", "table", "query", "sico")):
                record = {"status": response.status, "url": url, "contentType": ctype}
                if "json" in ctype:
                    try:
                        record["body"] = compact(response.text(), 2500)
                    except Exception as exc:  # pragma: no cover - diagnostics only
                        record["bodyError"] = repr(exc)
                interesting.append(record)

        page.on("response", on_response)
        print("NAVIGATE", URL)
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)
        print("TITLE", page.title())
        print("URL_FINAL", page.url)
        print("BUTTONS", json.dumps(page.locator("button").all_inner_texts(), ensure_ascii=False))
        print("SELECTS", json.dumps(page.locator("select").evaluate_all("els => els.map(e => ({name:e.name,id:e.id,aria:e.getAttribute('aria-label'),html:e.outerHTML.slice(0,800)}))"), ensure_ascii=False))
        print("INPUTS", json.dumps(page.locator("input").evaluate_all("els => els.map(e => ({type:e.type,name:e.name,id:e.id,placeholder:e.placeholder,aria:e.getAttribute('aria-label'),value:e.value}))"), ensure_ascii=False))

        # Esplora i due filtri necessari per arrivare al Comune. Non assumiamo
        # una struttura DOM specifica: se il sito cambia, il probe continua a
        # produrre diagnostica utile invece di inventare dati.
        for label in ("Tipo Istituzione", "Istituzione"):
            try:
                button = page.get_by_role("button", name=label, exact=True)
                if button.count() and button.first.is_visible():
                    button.first.click(timeout=10000)
                    page.wait_for_timeout(1200)
                    print(f"AFTER_{label.upper().replace(' ', '_')}", compact(page.locator("body").inner_text(), 12000))
                    if label == "Tipo Istituzione":
                        comuni = page.get_by_text("COMUNI", exact=True)
                        if comuni.count() and comuni.first.is_visible():
                            comuni.first.click(timeout=10000)
                            page.wait_for_timeout(1500)
                            print("SELECTED_COMUNI")
                    else:
                        visible_inputs = page.locator("input:visible")
                        for i in range(visible_inputs.count()):
                            inp = visible_inputs.nth(i)
                            try:
                                placeholder = (inp.get_attribute("placeholder") or "").lower()
                                aria = (inp.get_attribute("aria-label") or "").lower()
                                if any(token in placeholder + " " + aria for token in ("cerca", "search", "filtr")):
                                    inp.fill("Massarosa")
                                    page.wait_for_timeout(1000)
                                    break
                            except Exception:
                                pass
                        massarosa = page.get_by_text("MASSAROSA", exact=True)
                        if not massarosa.count():
                            massarosa = page.get_by_text("Massarosa", exact=True)
                        if massarosa.count() and massarosa.first.is_visible():
                            massarosa.first.click(timeout=10000)
                            page.wait_for_timeout(2500)
                            print("SELECTED_MASSAROSA")
            except Exception as exc:
                print("FILTER_ERROR", label, repr(exc))

        print("BODY_FINAL", compact(page.locator("body").inner_text(), 16000))
        print("NETWORK_BEGIN")
        for record in interesting:
            print(json.dumps(record, ensure_ascii=False))
        print("NETWORK_END")
        page.screenshot(path="rgs-formazione-probe.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
