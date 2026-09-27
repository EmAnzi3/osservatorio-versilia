#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TOWN="camaiore"
EXPECTED=223
VIEWPORTS=(("desktop",1440,1100),("mobile",390,844))
FREEZE="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}"

def stable(page):
    page.evaluate("() => document.fonts.ready")
    page.wait_for_timeout(240)
    old=None; same=0
    for _ in range(12):
        cur=page.evaluate("""() => [document.documentElement.scrollHeight,
          document.querySelector('#town-topic')?.innerHTML.length||0,
          document.querySelector('#town-topic .history-panel')?.innerHTML.length||0,
          document.querySelectorAll('.topic-controls [data-metric]').length,
          document.querySelectorAll('.ux-view-shell').length].join('|')""")
        if cur==old:
            same+=1
            if same>=2: break
        else: old=cur; same=0
        page.wait_for_timeout(120)

def go(page,base,theme,metric=None):
    path=f"comuni/{TOWN}/?tema={theme}"+(f"&indicatore={metric}" if metric else "")
    page.goto(urljoin(base,path),wait_until="networkidle")
    page.add_style_tag(content=FREEZE)
    stable(page)

def discover(page,base):
    go(page,base,"demografia")
    themes=page.evaluate("() => [...new Set([...document.querySelectorAll('[data-profile-theme]')].map(x=>x.dataset.profileTheme).filter(Boolean))]")
    if not themes: raise AssertionError("Nessun tema comunale")
    out={}
    for theme in themes:
        go(page,base,theme)
        metrics=page.evaluate("() => [...new Set([...document.querySelectorAll('.topic-controls [data-metric]')].map(x=>x.dataset.metric).filter(Boolean))]")
        if not metrics: raise AssertionError(f"{theme}: nessun indicatore")
        out[theme]=metrics
    return out

def choose(page,metric):
    active=page.locator('.topic-controls [data-metric].active')
    if active.count()==1 and active.get_attribute("data-metric")==metric: return
    result=page.evaluate("""metric => {
      const m=[...document.querySelectorAll('.topic-controls [data-metric]')].filter(x=>x.dataset.metric===metric);
      if(m.length!==1)return m.length; m[0].click(); return true;
    }""",metric)
    if result is not True: raise AssertionError(f"Indicatore non selezionabile {metric}: {result}")
    page.wait_for_function("metric => document.querySelector('.topic-controls [data-metric].active')?.dataset.metric===metric",arg=metric)
    stable(page)

def state(page):
    return page.evaluate("""() => {
      const q=s=>document.querySelector(s), visible=e=>{if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>1&&r.height>1&&s.display!=='none'&&s.visibility!=='hidden'};
      const main=q('main.town-profile'), body=getComputedStyle(document.body);
      const standardToolbar=q('#town-topic>.history-panel.a5-shared-chart .ux-view-toolbar');
      const fallbackActions=q('#town-topic > .town-data-actions.a5-town-fallback-actions');
      const actions=q('#town-topic .town-data-actions');
      return {
        classes:main?[...main.classList].sort():[], theme:main?.dataset.theme||'',
        activeTheme:q('[data-profile-theme].active')?.dataset.profileTheme||'',
        activeMetric:q('.topic-controls [data-metric].active')?.dataset.metric||'',
        required:{
          hero:visible(q('.town-hero')),brief:visible(q('.town-brief')),nav:visible(q('.town-context-nav')),
          heading:visible(q('#town-topic>.town-topic-heading')),sidebar:visible(q('#town-topic>.topic-controls')),
          metricLayout:visible(q('#town-topic>.town-metric-layout')),
          chart:visible(q('#town-topic>.history-panel.a5-shared-chart')),
          toolbar:visible(standardToolbar) || visible(fallbackActions),
          exportActions:visible(actions?.querySelector('[data-download]')) && visible(actions?.querySelector('[data-print]'))
        },
        tokens:{
          accent:body.getPropertyValue('--ds-theme-accent').trim(),
          soft:body.getPropertyValue('--ds-theme-soft').trim(),
          line:body.getPropertyValue('--ds-theme-line').trim()
        },
        selected:[...document.querySelectorAll('#town-topic .bar-row.comparison-row.selected')].map(x=>(x.textContent||'').replace(/\\s+/g,' ').trim()),
        hero:{
          background:getComputedStyle(q('.town-hero')).backgroundImage,
          credit:(q('.town-hero-photo-credit')?.textContent||'').replace(/\\s+/g,' ').trim()
        },
        demographyPill:(()=>{const e=q('[data-profile-theme="demografia"]');if(!e)return null;const c=getComputedStyle(e);return {active:e.classList.contains('active'),background:c.backgroundColor,border:c.borderTopColor,color:c.color}})(),
        semantic:(()=>{
          const deep=q('#town-topic > .topic-deep-dive');
          const deepHeading=(deep?.querySelector('.deep-heading h3')?.textContent||'').trim();
          const deepSummary=(deep?.querySelector('details > summary')?.textContent||'').replace(/\\s+/g,' ').trim();
          return {
            incomeText:deepHeading==='Redditi dichiarati' || /Mostra le fasce di reddito/i.test(deepSummary),
            economyDeepDive:visible(deep),
            crimeContext:visible(q('#town-context .crime-context'))
          };
        })(),
        extras:(()=>{const topic=q('#town-topic');if(!topic)return[];const tr=topic.getBoundingClientRect();return [...topic.children].filter(e=>visible(e)&&!e.matches('.town-topic-heading,.topic-controls,.town-metric-layout,.history-panel,.town-benchmark-host,.town-post-benchmark-tools,.town-data-actions')).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,cls:e.className||'',width:r.width,topicWidth:tr.width,left:r.left,topicLeft:tr.left}})})(),
        currentViz:(()=>{
          const bars=q('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .comparison-bars');
          if(!bars)return null;
          const rows=[...bars.querySelectorAll(':scope > .bar-row')].map(el=>({
            value:el.getAttribute('data-viz-value')||'',
            unit:el.getAttribute('data-viz-unit')||'',
            label:(el.querySelector('strong')?.textContent||'').trim(),
            left:parseFloat(el.querySelector('.comparison-dot')?.style.left||'')
          }));
          return {
            contract:bars.dataset.visualContract||'',
            unit:bars.dataset.visualUnit||'',
            axis:(bars.querySelector(':scope > .comparison-axis')?.textContent||'').replace(/\\s+/g,' ').trim(),
            rows
          };
        })(),
        incomeDetail:(()=>{const e=q('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] > .a5-town-income-detail');if(!e)return null;const r=e.getBoundingClientRect();const first=e.querySelector('.income-bands-detail > .composite-town-detail > div')?.getBoundingClientRect();return {visible:visible(e),heading:(e.querySelector('.a5-income-context-heading h4')?.textContent||'').trim(),leftPad:first?first.left-r.left:null,rightPad:first?r.right-first.right:null}})(),
        overflow:{doc:[document.documentElement.scrollWidth,document.documentElement.clientWidth],body:[document.body.scrollWidth,document.body.clientWidth]}
      };
    }""")

def validate(s,theme,metric,key,fail):
    classes=set(s["classes"])
    if not {"a5-town-pilot","a5-editorial-pilot"}<=classes: fail.append({"key":key,"kind":"a5-shell","classes":s["classes"]})
    if s["theme"]!=theme or s["activeTheme"]!=theme: fail.append({"key":key,"kind":"theme-state","state":s})
    if s["activeMetric"]!=metric: fail.append({"key":key,"kind":"metric-state","active":s["activeMetric"]})
    missing=[k for k,v in s["required"].items() if not v]
    if missing: fail.append({"key":key,"kind":"missing-surface","surfaces":missing})
    missing_tokens=[k for k,v in s["tokens"].items() if not v]
    if missing_tokens: fail.append({"key":key,"kind":"missing-theme-token","tokens":missing_tokens})
    for name,dims in s["overflow"].items():
        if dims[0]>dims[1]+2: fail.append({"key":key,"kind":"horizontal-overflow","surface":name,"dims":dims})
    if s["selected"] and not any("Camaiore" in x for x in s["selected"]):
        fail.append({"key":key,"kind":"selected-row","rows":s["selected"]})
    hero=s.get("hero") or {}
    if "Camaiore_-_Chiesa_di_Santo_Stefano" not in hero.get("background","") or "Passeggiata a mare" in hero.get("credit",""):
        fail.append({"key":key,"kind":"camaiore-hero","hero":hero})
    pill=s.get("demographyPill") or {}
    expected_bg="rgb(184, 75, 52)" if theme=="demografia" else "rgb(251, 233, 227)"
    if pill.get("background")!=expected_bg:
        fail.append({"key":key,"kind":"demography-pill-color","theme":theme,"pill":pill,"expectedBackground":expected_bg})
    semantic=s.get("semantic") or {}
    if theme=="economia" and metric!="incomeDistribution" and semantic.get("incomeText"):
        fail.append({"key":key,"kind":"income-context-leak"})
    if theme=="economia" and metric!="incomeDistribution" and semantic.get("economyDeepDive"):
        fail.append({"key":key,"kind":"economy-deep-dive-leak"})
    if theme=="sicurezza" and semantic.get("crimeContext"):
        fail.append({"key":key,"kind":"crime-context-leak"})
    for extra in s.get("extras") or []:
        if extra["width"] < extra["topicWidth"]*0.90 or abs(extra["left"]-extra["topicLeft"])>10:
            fail.append({"key":key,"kind":"misplaced-renderer-block","extra":extra})
    viz=s.get("currentViz")
    if viz and viz.get("rows"):
        if viz.get("contract")!="rendered":
            fail.append({"key":key,"kind":"visual-contract-not-rendered","viz":viz})
        units={row.get("unit","") for row in viz["rows"] if row.get("unit","")}
        if len(units)>1:
            fail.append({"key":key,"kind":"mixed-rendered-units","units":sorted(units)})
        numeric=[]
        for row in viz["rows"]:
            try: value=float(row.get("value",""))
            except (TypeError,ValueError): continue
            left=row.get("left")
            if isinstance(left,(int,float)):
                numeric.append((value,left))
        numeric.sort()
        if any(numeric[i][1] > numeric[i+1][1] + 0.3 for i in range(len(numeric)-1)):
            fail.append({"key":key,"kind":"value-position-mismatch","pairs":numeric})
        suffix={"currency":"€","percent":"%","years":"anni","eurPerResident":"€/ab.","eurm2":"€/m²","rentm2":"€/m²"}.get(viz.get("unit"))
        if suffix and suffix not in viz.get("axis",""):
            fail.append({"key":key,"kind":"axis-unit-mismatch","unit":viz.get("unit"),"axis":viz.get("axis")})
    if metric=="incomeDistribution":
        viz=s.get("currentViz") or {}
        if viz.get("unit")!="currency" or "€" not in viz.get("axis","") or "%" in viz.get("axis",""):
            fail.append({"key":key,"kind":"income-summary-scale","viz":viz})
        detail=s.get("incomeDetail") or {}
        if not detail.get("visible") or "fascia di reddito" not in detail.get("heading","").lower():
            fail.append({"key":key,"kind":"income-detail-placement","detail":detail})
        if detail.get("leftPad") is not None and (detail["leftPad"]<18 or detail.get("rightPad",0)<18):
            fail.append({"key":key,"kind":"income-detail-padding","detail":detail})

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--base",required=True);ap.add_argument("--report-dir",required=True);args=ap.parse_args()
    folder=Path(args.report_dir);folder.mkdir(parents=True,exist_ok=True);fail=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        d=browser.new_page(viewport={"width":1440,"height":1100});contract=discover(d,args.base);d.close()
        total=sum(map(len,contract.values()));unique=len({m for ms in contract.values() for m in ms})
        if total!=EXPECTED or unique!=EXPECTED:
            fail.append({"key":"catalog","kind":"metric-contract","expected":EXPECTED,"total":total,"unique":unique,"counts":{k:len(v) for k,v in contract.items()}})
        first_theme=next(iter(contract))
        review_metrics={"ageDistribution","incomeDistribution","roadSafety","slowMobilityTrekking","bathingWaterQuality","climateTemperatureTrend50y","financialDebtProfile"}
        for vp,w,h in VIEWPORTS:
            page=browser.new_page(viewport={"width":w,"height":h});errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
            for theme,metrics in contract.items():
                go(page,args.base,theme,metrics[0])
                page.locator("#town-topic").screenshot(path=str(folder/f"review-{vp}-{theme}.png"),animations="disabled")
                if theme==first_theme:
                    page.locator(".town-hero").screenshot(path=str(folder/f"hero-{vp}.png"),animations="disabled")
                for metric in metrics:
                    choose(page,metric);validate(state(page),theme,metric,f"{vp}:{theme}:{metric}",fail)
                    if metric in review_metrics:
                        page.locator("#town-topic").screenshot(path=str(folder/f"review-{vp}-{theme}-{metric}.png"),animations="disabled")
            if errors: fail.append({"key":vp,"kind":"page-errors","errors":errors})
            page.close()
        browser.close()
    report={"town":TOWN,"themes":list(contract),"themeMetricCounts":{k:len(v) for k,v in contract.items()},"metricStatesPerViewport":total,"uniqueMetricCount":unique,"failureCount":len(fail),"failures":fail}
    (folder/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (folder/"summary.txt").write_text(f"A5 Camaiore rollout\nthemes={len(contract)}\nmetric_states_per_viewport={total}\nunique_metrics={unique}\nfailures={len(fail)}\n",encoding="utf-8")
    if fail: raise SystemExit(f"A5 Camaiore rollout FAILED: {len(fail)} problemi\n"+json.dumps(fail[:12],ensure_ascii=False,indent=2))
    print(f"A5 Camaiore rollout OK: {len(contract)} temi, {total} stati/viewport, {unique} indicatori unici.")

if __name__=="__main__": main()
