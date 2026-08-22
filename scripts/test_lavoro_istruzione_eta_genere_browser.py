#!/usr/bin/env python3
from __future__ import annotations
import argparse
from playwright.sync_api import sync_playwright

KEYS=[("lavoro","employmentRate"),("lavoro","unemploymentRate"),("lavoro","activityRate"),("istruzione","diplomaPlus"),("istruzione","tertiary")]

def req(cond,msg):
    if not cond: raise AssertionError(msg)

def no_overflow(page,label):
    values=page.evaluate("() => ({w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})")
    req(max(values["doc"],values["body"])<=values["w"]+2,f"Overflow {label}: {values}")

def compare(page,base,theme,key):
    page.goto(f"{base}confronta/{theme}/?indicatore={key}",wait_until="networkidle")
    page.wait_for_selector("select[data-demographic-age]")
    age=page.locator("select[data-demographic-age]"); gender=page.locator("select[data-demographic-gender]")
    req(age.count()==1 and gender.count()==1,f"{key}: filtri doppi assenti")
    req(age.locator("option").count()==6,f"{key}: attese 6 fasce")
    req(gender.locator("option").count()==3,f"{key}: attesi 3 generi")
    req(page.locator("#compare-bars .bar-row").count()==7,f"{key}: confronto non 7/7")
    before=page.locator("#compare-bars").inner_text()
    gender.select_option("women")
    page.wait_for_function("() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice?.endsWith('|women')")
    after=page.locator("#compare-bars").inner_text()
    req(before!=after,f"{key}: filtro genere non cambia il confronto")
    age.select_option("25-49")
    page.wait_for_function("() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === '25-49|women'")
    req(page.locator("#compare-bars .bar-row").count()==7,f"{key}: filtro età×genere perde Comuni")
    no_overflow(page,f"compare/{key}")

def town(page,base,theme,key):
    page.goto(f"{base}comuni/massarosa/?tema={theme}&indicatore={key}",wait_until="networkidle")
    age=page.locator("select[data-demographic-town-age]"); gender=page.locator("select[data-demographic-town-gender]")
    req(age.count()==1 and gender.count()==1,f"{key}: filtri scheda comunale assenti")
    req(page.locator(".demographic-matrix tbody tr").count()==6,f"{key}: matrice età incompleta")
    req(page.locator(".demographic-matrix thead th").count()==4,f"{key}: matrice genere incompleta")
    initial=page.locator("[data-composite-primary-value]").inner_text()
    gender.select_option("women")
    page.wait_for_timeout(100)
    changed=page.locator("[data-composite-primary-value]").inner_text()
    req(initial!=changed,f"{key}: selezione donne non aggiorna valore")
    age.select_option("50-64")
    page.wait_for_timeout(100)
    req("50–64" in page.locator(".composite-versilia-position").inner_text(),f"{key}: benchmark Versilia non segue età")
    req(page.locator(".town-benchmark").count()==0,f"{key}: benchmark esterno fisso non deve apparire con filtro dinamico")
    if key=="employmentRate":
        gender.select_option("women"); age.select_option("25-64"); page.wait_for_timeout(100)
        req("64,9" in page.locator("[data-composite-primary-value]").inner_text(),"Massarosa occupazione donne 25–64 inattesa")
    no_overflow(page,f"town/{key}")

def run(base):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for viewport in ({"width":1440,"height":1000},{"width":390,"height":844}):
            ctx=browser.new_context(viewport=viewport); page=ctx.new_page()
            for theme,key in KEYS:
                compare(page,base,theme,key); town(page,base,theme,key)
            page.goto(f"{base}confronta/lavoro/?indicatore=employmentRate",wait_until="networkidle")
            body=page.locator("body").inner_text()
            req("Occupazione femminile" not in body and "Occupazione maschile" not in body,"Indicatori duplicati di genere ancora nella navigazione")
            ctx.close()
        browser.close()
    print("Lavoro/Istruzione età×genere browser: 5 indicatori OK desktop/mobile, doppi filtri 7/7, nessun overflow.")

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--base",default="http://127.0.0.1:8123/"); a=p.parse_args(); run(a.base.rstrip("/")+"/")
