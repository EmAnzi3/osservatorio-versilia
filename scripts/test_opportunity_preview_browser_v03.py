#!/usr/bin/env python3
from __future__ import annotations
import argparse
from playwright.sync_api import sync_playwright


def main():
 p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8123/');a=p.parse_args()
 with sync_playwright() as pw:
  b=pw.chromium.launch();page=b.new_page()
  for width,height in ((1440,1000),(390,844)):
   page.set_viewport_size({'width':width,'height':height});page.goto(a.base+'opportunita-preview/',wait_until='domcontentloaded');root=page.locator('[data-opportunity-preview]');root.wait_for()
   total=int(root.get_attribute('data-total-opportunities') or 0);cards=page.locator('[data-opportunity-card]');assert total==cards.count() and total>0
   assert page.locator('.op-overview-grid .op-stat').count()==4;assert page.locator('.op-overview-grid .op-stat-icon svg').count()==4
   bg=page.locator('.op-overview-shell').evaluate("e=>getComputedStyle(e).backgroundImage");assert 'linear-gradient' in bg
   monitor=page.locator('.op-monitor-source');assert monitor.count()>0
   assert page.locator('.op-source-favicon').count()>=1
   local=page.locator('img.op-source-favicon[src*="/assets/source-icons/"]')
   assert local.count()>=1
   page.wait_for_function("""() => [...document.querySelectorAll('img.op-source-favicon[src*="/assets/source-icons/"]')].every(img => img.complete && img.naturalWidth > 0)""",timeout=5000)
   assert not page.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth')
   body=page.locator('body').inner_text()
   assert body.count('Patti Attuazione Sicurezza Urbana. Sistemi di Videosorveglianza. DM 2026') + body.count('Videosorveglianza - D.M. 2026') <= 1
   quick=page.locator('[data-op-source-quick]')
   if quick.count():
    q=quick.first;sid=q.get_attribute('data-op-source-quick');q.click();page.wait_for_timeout(80);assert page.locator('[data-op-source]').input_value()==sid;assert q.get_attribute('aria-pressed')=='true'
   page.locator('[data-op-reset]').click()
   first_title=cards.first.locator('h3').inner_text().strip();assert first_title
   page.locator('[data-op-search]').fill(first_title);page.wait_for_timeout(80);assert page.locator('[data-opportunity-card]:not([hidden])').count()>=1
   page.locator('[data-op-reset]').click();assert page.locator('[data-opportunity-card]:not([hidden])').count()==total
   text=page.locator('body').inner_text();assert 'Quality gate' not in text and 'Da verificare' not in text
  b.close()
 print('Opportunity preview v0.3 browser checks passed.')
if __name__=='__main__':main()
