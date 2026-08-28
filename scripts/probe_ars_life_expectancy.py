#!/usr/bin/env python3
"""Temporary CI probe for the ARS life-expectancy browser data contract.

This file is intentionally diagnostic and will be removed before the PR is ready.
"""
from __future__ import annotations

import json
from playwright.sync_api import sync_playwright

URL = (
    "https://www.ars.toscana.it/banche-dati/"
    "dettaglio_indicatore-1290-speranza-vita-alla-nascita"
    "?dettaglio=ric_anno_geo_comuni&par_top_geografia=046033"
    "&provenienza=comuni_elenco_indicatori_sintesi"
)


def clip(text: str, limit: int = 12000) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def main() -> None:
    xhr_candidates: list[dict[str, str]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})

        def on_response(response) -> None:
            try:
                req = response.request
                ctype = response.headers.get("content-type", "")
                if req.resource_type in {"xhr", "fetch"} or any(
                    token in response.url.lower()
                    for token in ("ajax", "json", "indic", "dati", "query")
                ):
                    item = {
                        "status": str(response.status),
                        "type": req.resource_type,
                        "content_type": ctype,
                        "url": response.url,
                    }
                    if req.resource_type in {"xhr", "fetch"}:
                        try:
                            body = response.text()
                            item["body"] = clip(body, 5000)
                        except Exception as exc:  # diagnostic only
                            item["body_error"] = repr(exc)
                    xhr_candidates.append(item)
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(15000)

        print("=== TITLE ===")
        print(page.title())
        print("=== FINAL URL ===")
        print(page.url)
        print("=== SELECTS ===")
        selects = page.locator("select")
        for i in range(selects.count()):
            sel = selects.nth(i)
            try:
                payload = sel.evaluate(
                    """el => ({
                      id: el.id || '', name: el.name || '',
                      value: el.value,
                      outer: el.outerHTML.slice(0, 1200),
                      options: Array.from(el.options).map(o => ({text:o.textContent.trim(), value:o.value, selected:o.selected}))
                    })"""
                )
                print(json.dumps({"index": i, **payload}, ensure_ascii=False))
            except Exception as exc:
                print(json.dumps({"index": i, "error": repr(exc)}))

        print("=== BUTTONS/LINK-LIKE CONTROLS ===")
        controls = page.locator("button, a, input[type=button], input[type=radio], label")
        for i in range(min(controls.count(), 500)):
            el = controls.nth(i)
            try:
                info = el.evaluate(
                    """el => ({tag:el.tagName, id:el.id||'', cls:el.className||'',
                      text:(el.innerText||el.textContent||el.value||'').trim().replace(/\\s+/g,' ').slice(0,180),
                      href:el.href||'', value:el.value||'', checked:!!el.checked})"""
                )
                text = (info.get("text") or "").upper()
                if any(k in text for k in ("TOTALE", "MASCHI", "FEMMINE", "CSV", "EXCEL")):
                    print(json.dumps({"index": i, **info}, ensure_ascii=False))
            except Exception:
                pass

        print("=== TABLES ===")
        tables = page.locator("table")
        print(f"table_count={tables.count()}")
        for i in range(tables.count()):
            try:
                print(f"--- table {i} ---")
                print(clip(tables.nth(i).inner_text(), 8000))
            except Exception as exc:
                print(repr(exc))

        print("=== BODY RELEVANT LINES ===")
        body = page.locator("body").inner_text()
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        for line in lines:
            upper = line.upper()
            if any(k in upper for k in ("SPERANZA", "TOTALE", "MASCHI", "FEMMINE", "VIAREGGIO", "VERSILIA", "REGIONE TOSCANA")):
                print(line[:1000])

        print("=== XHR/FETCH CANDIDATES ===")
        for item in xhr_candidates:
            print(json.dumps(item, ensure_ascii=False))

        browser.close()


if __name__ == "__main__":
    main()
