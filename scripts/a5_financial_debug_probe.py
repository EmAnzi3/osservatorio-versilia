#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def snapshot(page, choice: str, stage: str) -> None:
    payload = page.evaluate(
        """({choice,stage}) => {
          const topic=document.getElementById('town-topic');
          const chart=topic?.querySelector(':scope > .history-panel.a5-shared-chart');
          const histories=[...topic.querySelectorAll('[data-financial-profile-history]')].map((node,index)=>{
            const rect=node.getBoundingClientRect();
            const style=getComputedStyle(node);
            const fixed=node.closest('.composite-fixed-detail');
            const points=[...node.querySelectorAll('.chart-point')];
            const last=points.at(-1);
            const tooltip=last?.querySelector('.chart-tooltip');
            const tooltipStyle=tooltip ? getComputedStyle(tooltip) : null;
            return {
              index,
              visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
              rect:[rect.x,rect.y,rect.width,rect.height],
              fixedClass:fixed?.className || null,
              fixedInChart:Boolean(fixed && chart?.contains(fixed)),
              parentClass:node.parentElement?.className || null,
              points:points.length,
              lastPointConnected:Boolean(last?.isConnected),
              lastPointIsActive:document.activeElement === last,
              tooltipHidden:tooltip?.hasAttribute('hidden') ?? null,
              tooltipDisplay:tooltipStyle?.display || null,
              tooltipVisibility:tooltipStyle?.visibility || null,
              tooltipOpacity:tooltipStyle?.opacity || null,
              tooltipRect:tooltip ? (()=>{const r=tooltip.getBoundingClientRect(); return [r.x,r.y,r.width,r.height]})() : null,
            };
          });
          return {
            choice,stage,
            town:document.body.dataset.town,
            mainClass:document.querySelector('main.town-profile')?.className || null,
            histories,
            financialDetails:topic?.querySelectorAll('[data-financial-profile-detail]').length || 0,
            fixedDetails:topic?.querySelectorAll('.composite-fixed-detail').length || 0,
            activeTag:document.activeElement?.tagName || null,
            activeClass:document.activeElement?.getAttribute?.('class') || null,
            activeAria:document.activeElement?.getAttribute?.('aria-label') || null,
          };
        }""",
        {"choice": choice, "stage": stage},
    )
    print("FINANCIAL_DEBUG " + json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args=parser.parse_args()
    base=args.base.rstrip("/") + "/"

    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1000})
        page.goto(urljoin(base,"comuni/camaiore/?tema=bilanci&indicatore=financialDebtProfile"), wait_until="networkidle")
        selector=page.locator("#town-topic select[data-composite-choice]")
        selector.wait_for()
        for choice in ("part-0","part-1","part-2"):
            selector=page.locator("#town-topic select[data-composite-choice]")
            selector.select_option(choice)
            page.wait_for_timeout(100)
            snapshot(page,choice,"before-focus")
            point=page.locator("#town-topic [data-financial-profile-history] .chart-point").last
            print(f"FINANCIAL_DEBUG locator_count choice={choice} count={page.locator('#town-topic [data-financial-profile-history] .chart-point').count()}", flush=True)
            point.focus()
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            snapshot(page,choice,"after-focus")
        browser.close()


if __name__ == "__main__":
    main()
