#!/usr/bin/env python3
from __future__ import annotations
import argparse
from playwright.sync_api import sync_playwright


def main():
 p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8123/');a=p.parse_args()
 with sync_playwright() as pw:
  b=pw.chromium.launch();page=b.new_page()
  for width,height in ((1440,1000),(390,844)):
   page.set_viewport_size({'width':width,'height':height});page.goto(a.base+'opportunita-preview/',wait_until='domcontentloaded');page.locator('[data-opportunity-preview]').wait_for()
   total=int(page.locator('[data-opportunity-preview]').get_attribute('data-total-opportunities') or 0);assert total>=11
   assert page.locator('.op-overview-grid .op-stat').count()==4;assert page.locator('.op-overview-grid .op-stat-icon svg').count()==4
   bg=page.locator('.op-overview-shell').evaluate("e=>getComputedStyle(e).backgroundImage");assert 'linear-gradient' in bg
   assert page.locator('.op-monitor-source').count()>=8;assert page.locator('.op-source-favicon').count()>=1;assert page.locator('[data-op-source-quick]').count()>=2
   embedded=page.locator('img.op-source-favicon[src^="data:image/"]')
   assert embedded.count()>=3
   for i in range(embedded.count()):
    assert embedded.nth(i).evaluate('img=>img.complete && img.naturalWidth>0')
   assert not page.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth')
   q=page.locator('[data-op-source-quick]').first;sid=q.get_attribute('data-op-source-quick');q.click();page.wait_for_timeout(80);assert page.locator('[data-op-source]').input_value()==sid;assert q.get_attribute('aria-pressed')=='true'
   page.locator('[data-op-reset]').click();page.locator('[data-op-search]').fill('parcheggi');page.wait_for_timeout(80);assert page.locator('[data-opportunity-card]:not([hidden])').count()>=1
   text=page.locator('body').inner_text();assert 'Quality gate' not in text and 'Da verificare' not in text
  b.close()
 print('Opportunity preview v0.3 browser checks passed.')
if __name__=='__main__':main()
