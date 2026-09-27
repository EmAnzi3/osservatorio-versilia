#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

FREEZE="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}"
THEME_REGIONS=(("hero",".compare-showcase-hero"),("nav",".compare-context-nav"),("topic",".topic-hero"),("territories","#compare-territori"))
METRIC_REGIONS=(("workspace","#compare-workspace"),("pyramid","#compare-demographic-pyramid"),("benchmark","#compare-benchmark"),("tools","#compare-tools"))

def sha(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()

def stable(page):
    page.evaluate("() => document.fonts.ready")
    page.wait_for_timeout(300)
    old=None; same=0
    for _ in range(18):
        cur=page.evaluate("""() => [document.documentElement.scrollHeight,
          document.querySelector('main.a5-editorial-pilot')?.innerHTML.length||0,
          document.querySelector('#compare-bars')?.innerHTML.length||0,
          document.querySelector('#compare-benchmark')?.innerHTML.length||0,
          document.querySelector('#compare-tools')?.innerHTML.length||0,
          document.querySelectorAll('.topic-controls [data-metric]').length].join('|')""")
        if cur==old:
            same+=1
            if same>=3: break
        else: old=cur; same=0
        page.wait_for_timeout(180)
    page.evaluate("() => window.scrollTo(0,0)")

def go(page,base,path):
    page.goto(urljoin(base,path),wait_until="networkidle")
    page.add_style_tag(content=FREEZE)
    stable(page)

def discover(page,base,seed):
    go(page,base,f"confronta/{seed}/")
    themes=page.evaluate("() => [...new Set([...document.querySelectorAll('[data-context-theme]')].map(x=>x.dataset.contextTheme).filter(Boolean))]")
    if not themes: raise AssertionError("Nessun tema scoperto nella baseline")
    out={}
    for theme in themes:
        go(page,base,f"confronta/{theme}/")
        if page.locator("main.a5-editorial-pilot").get_attribute("data-theme")!=theme:
            raise AssertionError(f"{theme}: shell A5 assente")
        metrics=page.evaluate("() => [...new Set([...document.querySelectorAll('.topic-controls [data-metric]')].map(x=>x.dataset.metric).filter(Boolean))]")
        if not metrics: raise AssertionError(f"{theme}: nessun indicatore")
        out[theme]=metrics
    return out

def state(page):
    raw=page.evaluate("""() => {
      const q=s=>document.querySelector(s), rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(v=>+v.toFixed(1))},
      pack=e=>{if(!e)return null;const s=getComputedStyle(e);return {rect:rect(e),display:s.display,visibility:s.visibility,opacity:s.opacity,color:s.color,background:s.backgroundColor,border:s.borderColor,radius:s.borderRadius,padding:s.padding,margin:s.margin,gap:s.gap,grid:s.gridTemplateColumns,fontSize:s.fontSize,fontWeight:s.fontWeight,lineHeight:s.lineHeight,overflowX:s.overflowX,overflowY:s.overflowY}};
      const main=q('main.a5-editorial-pilot'), metric=q('.topic-controls [data-metric].active'), theme=q('.compare-context-nav [data-context-theme].active'), chart=q('#compare-bars');
      return {
        main:{theme:main?.dataset.theme||'',classes:main?[...main.classList].sort():[]},
        active:{theme:theme?.dataset.contextTheme||'',metric:metric?.dataset.metric||'',metricStyle:pack(metric),themeStyle:pack(theme)},
        layout:{nav:pack(q('.compare-context-nav')),topic:pack(q('.topic-hero')),sidebar:pack(q('#compare-workspace>.topic-controls')),workspace:pack(q('#compare-workspace')),chart:pack(chart),toolbar:pack(q('#compare-bars .ux-view-toolbar')),benchmark:pack(q('#compare-benchmark')),tools:pack(q('#compare-tools')),territories:pack(q('#compare-territori'))},
        structure:{themes:[...document.querySelectorAll('[data-context-theme]')].map(x=>x.dataset.contextTheme),metrics:[...document.querySelectorAll('.topic-controls [data-metric]')].map(x=>x.dataset.metric),groups:[...document.querySelectorAll('.topic-controls .metric-group')].map(x=>[x.dataset.section||'',x.querySelectorAll('[data-metric]').length]),children:[...(main?.children||[])].map(x=>[x.tagName,x.id||'', [...x.classList].sort().join(' ')]),chart:[chart?.querySelectorAll('svg').length||0,chart?.querySelectorAll('canvas').length||0,chart?.querySelectorAll('button').length||0,chart?.querySelectorAll('details').length||0]},
        overflow:{doc:[document.documentElement.scrollWidth,document.documentElement.clientWidth],body:[document.body.scrollWidth,document.body.clientWidth],workspace:q('#compare-workspace')?[q('#compare-workspace').scrollWidth,q('#compare-workspace').clientWidth]:null,chart:chart?[chart.scrollWidth,chart.clientWidth]:null},
      };
    }""")
    return raw

def diff_pixels(a,b,threshold):
    x=Image.open(io.BytesIO(a)).convert("RGB"); y=Image.open(io.BytesIO(b)).convert("RGB")
    if x.size!=y.size: return {"sameSize":False,"ratio":1.0,"a":x.size,"b":y.size}
    d=ImageChops.difference(x,y); total=x.size[0]*x.size[1]
    changed=sum(1 for p in d.getdata() if max(p)>threshold)
    return {"sameSize":True,"ratio":changed/total if total else 0.0,"changed":changed,"total":total}

def shot(page,selector):
    loc=page.locator(selector)
    if loc.count()!=1: return None,{"count":loc.count()}
    box=loc.bounding_box()
    if not box or box["width"]<2 or box["height"]<2: return None,{"count":1,"box":box}
    return loc.screenshot(animations="disabled"),{"count":1,"box":box}

def region(a,b,selector,key,fail,folder,threshold,tolerance):
    ai,am=shot(a,selector); bi,bm=shot(b,selector)
    if ai is None or bi is None:
        if am!=bm: fail.append({"key":key,"kind":"region-presence","selector":selector,"baseline":am,"current":bm})
        return
    d=diff_pixels(ai,bi,threshold)
    if (not d["sameSize"]) or d["ratio"]>tolerance:
        names=[None,None]
        if sum(x.get("kind")=="visual-diff" for x in fail)<12:
            safe=key.replace("/","_").replace(":","_")
            pa=folder/f"{safe}-baseline.png"; pb=folder/f"{safe}-current.png"
            pa.write_bytes(ai); pb.write_bytes(bi); names=[pa.name,pb.name]
        fail.append({"key":key,"kind":"visual-diff","selector":selector,"pixelDiff":d,"baselineSha256":sha(ai),"currentSha256":sha(bi),"baselineImage":names[0],"currentImage":names[1]})

def choose(page,metric):
    active=page.locator('.topic-controls [data-metric].active')
    if active.count()==1 and active.get_attribute("data-metric")==metric:
        return
    selected=page.evaluate("""metric => {
      const matches=[...document.querySelectorAll('.topic-controls [data-metric]')]
        .filter(el => el.dataset.metric === metric);
      if (matches.length !== 1) return matches.length;
      // Native HTMLElement.click() intentionally bypasses Playwright's visibility
      // precondition. The lock must traverse the complete metric catalog even when
      // responsive/sidebar CSS places a valid tab outside the visible scroll area.
      matches[0].click();
      return true;
    }""", metric)
    if selected is not True:
        raise AssertionError(f"Indicatore non selezionabile: {metric} (matches={selected})")
    page.wait_for_function(
        """metric => document.querySelector('.topic-controls [data-metric].active')?.dataset.metric === metric""",
        arg=metric,
    )
    stable(page)

def overflow(baseline,current,key,fail):
    for name in sorted(set(baseline["overflow"]) | set(current["overflow"])):
        before=baseline["overflow"].get(name)
        after=current["overflow"].get(name)
        if not before or not after:
            continue
        before_excess=max(0,before[0]-before[1])
        after_excess=max(0,after[0]-after[1])
        if after_excess>before_excess+2:
            fail.append({
                "key":key,
                "kind":"horizontal-overflow-regression",
                "surface":name,
                "baselineExcess":before_excess,
                "currentExcess":after_excess,
                "baseline":before,
                "current":after,
            })

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--current-base",required=True); ap.add_argument("--baseline-base",required=True); ap.add_argument("--config",required=True); ap.add_argument("--report-dir",required=True); args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text()); folder=Path(args.report_dir); folder.mkdir(parents=True,exist_ok=True); fail=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        d=browser.new_page(viewport={"width":1440,"height":1100}); contract=discover(d,args.baseline_base,cfg["seed_theme"]); current=discover(d,args.current_base,cfg["seed_theme"]); d.close()
        if contract!=current: fail.append({"key":"catalog","kind":"theme-metric-contract","baseline":contract,"current":current})
        for vp in cfg["viewports"]:
            a=browser.new_page(viewport={"width":vp["width"],"height":vp["height"]}); b=browser.new_page(viewport={"width":vp["width"],"height":vp["height"]}); aerr=[]; berr=[]
            a.on("pageerror",lambda e:aerr.append(str(e))); b.on("pageerror",lambda e:berr.append(str(e)))
            for theme,metrics in contract.items():
                path=f"confronta/{theme}/?indicatore={metrics[0]}"; go(a,args.baseline_base,path); go(b,args.current_base,path)
                for rn,sel in THEME_REGIONS: region(a,b,sel,f"{vp['name']}:{theme}:theme:{rn}",fail,folder,cfg["channel_threshold"],cfg["pixel_tolerance"])
                for metric in metrics:
                    choose(a,metric); choose(b,metric); key=f"{vp['name']}:{theme}:{metric}"; sa=state(a); sb=state(b)
                    if sa!=sb: fail.append({"key":key,"kind":"state-diff","baseline":sa,"current":sb})
                    if sb["main"]["theme"]!=theme or sb["active"]["metric"]!=metric: fail.append({"key":key,"kind":"active-state","state":sb["active"],"theme":sb["main"]["theme"]})
                    overflow(sa,sb,key,fail)
                    for rn,sel in METRIC_REGIONS: region(a,b,sel,f"{key}:{rn}",fail,folder,cfg["channel_threshold"],cfg["pixel_tolerance"])
            if aerr: fail.append({"key":vp["name"],"kind":"baseline-page-errors","errors":aerr})
            if berr: fail.append({"key":vp["name"],"kind":"current-page-errors","errors":berr})
            a.close(); b.close()
        browser.close()
    total=sum(map(len,contract.values())); unique=len({m for ms in contract.values() for m in ms})
    report={"baseline":cfg["baseline"],"themes":list(contract),"themeMetricCounts":{k:len(v) for k,v in contract.items()},"metricStatesPerViewport":total,"uniqueMetricCount":unique,"viewports":cfg["viewports"],"failureCount":len(fail),"failures":fail}
    (folder/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    (folder/"summary.txt").write_text(f"A5 thematic golden lock\nbaseline={cfg['baseline']}\nthemes={len(contract)}\nmetric_states_per_viewport={total}\nunique_metrics={unique}\nfailures={len(fail)}\n")
    if fail: raise SystemExit(f"A5 thematic golden lock FAILED: {len(fail)} regressioni\n"+json.dumps(fail[:6],ensure_ascii=False,indent=2))
    print(f"A5 thematic golden lock OK: {len(contract)} temi, {total} stati/viewport, {unique} indicatori unici.")

if __name__=="__main__": main()
