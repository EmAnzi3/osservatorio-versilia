#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

PAGE_URL = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"
JS_URL = "https://contoannuale.rgs.mef.gov.it/o/sogei-theme/js/formazione.js"
API = "https://contoannuale.rgs.mef.gov.it/o/sico-rest-APIs/sicoAPI"
TOWNS = {
    "Camaiore": "1348",
    "Forte dei Marmi": "3135",
    "Massarosa": "4177",
    "Pietrasanta": "5461",
    "Seravezza": "7010",
    "Stazzema": "7266",
    "Viareggio": "7967",
}


def compact(text: str, limit: int = 10000) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="it-IT",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        )
        page = context.new_page()
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)
        print("PAGE", page.title(), page.url)

        js_response = context.request.get(JS_URL, timeout=60000)
        js_text = js_response.text()
        print("JS_STATUS", js_response.status, "BYTES", len(js_text))
        print("JS_FILTER_LINES_BEGIN")
        for line in js_text.splitlines():
            low = line.lower()
            if any(token in low for token in ("istituzionefilters", "tipoistituzionefilters", "formazione?", "formazioneandamento", "selectbox")):
                print(compact(line, 12000))
        print("JS_FILTER_LINES_END")

        # Il sito usa convenzioni *Filters per i filtri. Proviamo la forma
        # osservata nel JS e stampiamo la risposta completa per Massarosa.
        def api_get(path: str, params: dict[str, str]):
            url = f"{API}/{path}?{urlencode(params)}"
            response = context.request.get(url, timeout=60000)
            print("API", response.status, url)
            body = response.text()
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                print("NON_JSON", compact(body, 4000))
                return None

        base = {"anno": "2024", "tipoIstituzioneFilters": "C"}
        massarosa = api_get("formazione", {**base, "istituzioneFilters": TOWNS["Massarosa"]})
        print("MASSAROSA", json.dumps(massarosa, ensure_ascii=False))
        andamento = api_get("formazioneAndamento", {"tipoIstituzioneFilters": "C", "istituzioneFilters": TOWNS["Massarosa"]})
        print("MASSAROSA_ANDAMENTO", json.dumps(andamento, ensure_ascii=False))

        print("TOWNS_2024_BEGIN")
        for town, code in TOWNS.items():
            data = api_get("formazione", {**base, "istituzioneFilters": code})
            print("TOWN", town, code, json.dumps(data, ensure_ascii=False))
        print("TOWNS_2024_END")

        # Verifica se il backend accetta più istituzioni in un'unica selezione,
        # utile per ottenere una media Versilia direttamente dalla fonte.
        codes = ",".join(TOWNS.values())
        combined = api_get("formazione", {**base, "istituzioneFilters": codes})
        print("VERSILIA_COMBINED_COMMA", json.dumps(combined, ensure_ascii=False))

        page.screenshot(path="rgs-formazione-probe.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
