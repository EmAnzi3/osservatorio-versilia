#!/usr/bin/env python3
"""Smoke browser per le due card Demanio marittimo v1.27.0."""
from __future__ import annotations
import argparse
from playwright.sync_api import sync_playwright

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base",required=True); args=ap.parse_args()
    base=args.base.rstrip("/")+"/"
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={"width":390,"height":844})
        page.goto(base+"confronta/ambiente/?indicatore=maritimeConcessions", wait_until="networkidle")
        page.get_by_text("Concessioni demaniali marittime", exact=True).first.wait_for()
        page.get_by_text("Turistico-ricreative", exact=True).first.wait_for()
        page.goto(base+"comuni/massarosa/?tema=ambiente&indicatore=maritimeConcessions", wait_until="networkidle")
        page.get_by_text("Indicatore non applicabile", exact=True).wait_for()
        page.goto(base+"comuni/viareggio/?tema=ambiente&indicatore=maritimeConcessionFeesDue", wait_until="networkidle")
        page.get_by_text("Canoni demaniali dovuti", exact=True).first.wait_for()
        page.get_by_text("Dovuto totale", exact=True).wait_for()
        browser.close()
    print("Browser Demanio marittimo: selector, n.a. e dettaglio comunale verificati.")

if __name__=="__main__": main()
