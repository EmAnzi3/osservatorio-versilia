#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

TOWNS = ("viareggio", "massarosa")
METRICS = (
    "population",
    "ageDistribution",
    "oldAgeIndex",
    "dependencyIndices",
    "foreignResidents",
    "internalResidentialMobility",
    "foreignResidentialMobility",
    "totalResidentialMobility",
    "naturalDemographicDynamics",
    "populationChange",
)
VIEWPORTS = (
    ("desktop", 1440, 1100),
    ("mobile", 390, 844),
)
LOCK_REGIONS = (
    ("context-nav", ".town-context-nav"),
    ("sidebar", "#town-topic > .topic-controls"),
    ("toolbar", "#town-topic > .history-panel.a5-shared-chart .ux-view-toolbar"),
)

FREEZE_STYLE = """
*,*::before,*::after {
  animation:none !important;
  transition:none !important;
  caret-color:transparent !important;
  scroll-behavior:auto !important;
}
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture(page):
    return page.evaluate(
        """() => {
          const q = s => document.querySelector(s);
          const rect = el => {
            if (!el) return null;
            const r=el.getBoundingClientRect();
            return {
              x:+r.x.toFixed(1), y:+r.y.toFixed(1),
              width:+r.width.toFixed(1), height:+r.height.toFixed(1),
              top:+r.top.toFixed(1), bottom:+r.bottom.toFixed(1)
            };
          };
          const pack = el => {
            if (!el) return null;
            const s=getComputedStyle(el);
            return {
              rect:rect(el),
              display:s.display,
              visibility:s.visibility,
              opacity:s.opacity,
              color:s.color,
              backgroundColor:s.backgroundColor,
              borderColor:s.borderColor,
              borderRadius:s.borderRadius,
              padding:s.padding,
              margin:s.margin,
              gap:s.gap,
              gridTemplateColumns:s.gridTemplateColumns,
              fontSize:s.fontSize,
              fontWeight:s.fontWeight,
              lineHeight:s.lineHeight,
              overflowX:s.overflowX,
              overflowY:s.overflowY,
            };
          };
          const navActive=[...document.querySelectorAll('.town-context-nav .context-nav-links a.active')];
          const metricActive=q('#town-topic .topic-controls [data-metric].active');
          const toolbar=q('#town-topic > .history-panel.a5-shared-chart .ux-view-toolbar');
          const topic=q('#town-topic');
          const main=q('main.a5-town-pilot');
          return {
            main: {
              classes: main ? [...main.classList].sort() : [],
              theme: main?.dataset.theme || '',
              rect:rect(main)
            },
            active: {
              nav: navActive.map(el => ({
                text:(el.textContent||'').trim(),
                style:pack(el)
              })),
              metric: metricActive ? {
                key:metricActive.dataset.metric || '',
                text:(metricActive.textContent||'').trim(),
                style:pack(metricActive)
              } : null
            },
            layout: {
              app:pack(q('#app')),
              hero:pack(q('.town-hero')),
              brief:pack(q('.town-brief')),
              contextNav:pack(q('.town-context-nav')),
              topic:pack(topic),
              sidebar:pack(q('#town-topic > .topic-controls')),
              metricLayout:pack(q('#town-topic > .town-metric-layout')),
              primary:pack(q('#town-topic .town-metric-primary')),
              position:pack(q('#town-topic .versilia-position')),
              chart:pack(q('#town-topic > .history-panel.a5-shared-chart')),
              toolbar:pack(toolbar),
              benchmark:pack(q('#town-topic > .town-benchmark-host')),
              tools:pack(q('#town-topic > .town-post-benchmark-tools')),
            },
            structure: {
              topicChildren:[...(topic?.children||[])].map(el => ({
                tag:el.tagName,
                classes:[...el.classList].sort()
              })),
              toolbarChildren:[...(toolbar?.children||[])].map(el => ({
                tag:el.tagName,
                classes:[...el.classList].sort(),
                text:(el.textContent||'').trim().replace(/\\s+/g,' ')
              })),
              actionTexts:[...(toolbar?.querySelectorAll('.town-data-actions > *')||[])].map(el =>
                (el.textContent||'').trim().replace(/\\s+/g,' ')
              ),
              toolbarSelects:toolbar?.querySelectorAll('select').length || 0,
              bodyOverflow:Math.max(0,document.documentElement.scrollWidth-window.innerWidth),
              topicOverflow:topic?Math.max(0,topic.scrollWidth-topic.clientWidth):0,
            }
          };
        }"""
    )


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--current-base", required=True)
    parser.add_argument("--baseline-base", required=True)
    parser.add_argument("--report-dir", required=True)
    args=parser.parse_args()

    current=args.current_base.rstrip("/") + "/"
    baseline=args.baseline_base.rstrip("/") + "/"
    report_dir=Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    failures=[]
    checked=0

    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        base_page=browser.new_page()
        cur_page=browser.new_page()
        for name,width,height in VIEWPORTS:
            base_page.set_viewport_size({"width":width,"height":height})
            cur_page.set_viewport_size({"width":width,"height":height})

            for town in TOWNS:
                for metric in METRICS:
                    rel=f"comuni/{town}/?tema=demografia&indicatore={metric}"
                    key=f"{name}-{town}-{metric}"
                    for page,root in ((base_page,baseline),(cur_page,current)):
                        page.goto(urljoin(root,rel), wait_until="networkidle")
                        page.wait_for_selector('main.a5-town-pilot[data-theme="demografia"]')
                        page.evaluate("() => document.fonts.ready")
                        page.add_style_tag(content=FREEZE_STYLE)
                        page.wait_for_timeout(80)

                    base_state=capture(base_page)
                    cur_state=capture(cur_page)
                    checked += 1

                    # Fixed golden semantics: 2 active nav pills + 1 active metric, all opaque.
                    for side,state in (("baseline",base_state),("current",cur_state)):
                        if len(state["active"]["nav"]) != 2:
                            failures.append({"key":key,"kind":f"{side}-active-nav-count","value":state["active"]["nav"]})
                        metric_state=state["active"]["metric"]
                        if not metric_state:
                            failures.append({"key":key,"kind":f"{side}-active-metric-missing"})
                        for item in state["active"]["nav"] + ([metric_state] if metric_state else []):
                            style=item["style"]
                            if style["opacity"] != "1":
                                failures.append({"key":key,"kind":f"{side}-active-opacity","value":item})
                            if style["backgroundColor"] == "rgba(0, 0, 0, 0)":
                                failures.append({"key":key,"kind":f"{side}-active-transparent","value":item})

                    if base_state != cur_state:
                        failures.append({
                            "key":key,
                            "kind":"computed-state-diff",
                            "baseline":base_state,
                            "current":cur_state,
                        })

                    # Full rendered page is part of the immutable golden contract.
                    # Same browser, same runner, same viewport: any pixel drift is a
                    # regression until explicitly approved and the golden baseline is moved.
                    base_full=base_page.screenshot(full_page=True, animations="disabled")
                    cur_full=cur_page.screenshot(full_page=True, animations="disabled")
                    if base_full != cur_full:
                        if len([f for f in failures if f.get("kind") == "full-page-visual-diff"]) < 12:
                            bpath=report_dir/f"{key}-full-baseline.png"
                            cpath=report_dir/f"{key}-full-current.png"
                            bpath.write_bytes(base_full)
                            cpath.write_bytes(cur_full)
                            baseline_image=bpath.name
                            current_image=cpath.name
                        else:
                            baseline_image=None
                            current_image=None
                        failures.append({
                            "key":key,
                            "kind":"full-page-visual-diff",
                            "baselineSha256":digest(base_full),
                            "currentSha256":digest(cur_full),
                            "baselineImage":baseline_image,
                            "currentImage":current_image,
                        })

                    for region_name,selector in LOCK_REGIONS:
                        b=base_page.locator(selector)
                        c=cur_page.locator(selector)
                        if b.count()!=1 or c.count()!=1:
                            failures.append({
                                "key":key,"kind":"region-missing","region":region_name,
                                "baselineCount":b.count(),"currentCount":c.count()
                            })
                            continue
                        bp=b.screenshot()
                        cp=c.screenshot()
                        if bp != cp:
                            bpath=report_dir/f"{key}-{region_name}-baseline.png"
                            cpath=report_dir/f"{key}-{region_name}-current.png"
                            bpath.write_bytes(bp)
                            cpath.write_bytes(cp)
                            failures.append({
                                "key":key,
                                "kind":"visual-region-diff",
                                "region":region_name,
                                "baselineSha256":digest(bp),
                                "currentSha256":digest(cp),
                                "baselineImage":bpath.name,
                                "currentImage":cpath.name,
                            })

        browser.close()

    summary={
        "baseline_commit":"7eadda666118f2450290a3b1c6edb93f061b7c7b",
        "checked_surfaces":checked,
        "towns":list(TOWNS),
        "metrics":list(METRICS),
        "viewports":[{"name":n,"width":w,"height":h} for n,w,h in VIEWPORTS],
        "locked_regions":[r for r,_ in LOCK_REGIONS],
        "failure_count":len(failures),
        "failures":failures,
    }
    (report_dir/"report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("baseline_commit","checked_surfaces","failure_count")},ensure_ascii=False))
    if failures:
        for item in failures[:30]:
            print(f"FAIL {item['key']} · {item['kind']}" + (f" · {item.get('region')}" if item.get("region") else ""))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
