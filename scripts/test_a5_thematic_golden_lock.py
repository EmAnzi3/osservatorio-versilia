#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, math, re
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urljoin
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

FREEZE="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}#compare-territori .topic-town-card-media img{visibility:hidden!important}"
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
    page.evaluate("() => window.scrollTo(0,0)")
    raw=page.evaluate("""() => {
      const q=s=>document.querySelector(s), rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(v=>+v.toFixed(1))},
      pack=e=>{if(!e)return null;const s=getComputedStyle(e);return {rect:rect(e),display:s.display,visibility:s.visibility,opacity:s.opacity,color:s.color,background:s.backgroundColor,border:s.borderColor,radius:s.borderRadius,padding:s.padding,margin:s.margin,gap:s.gap,grid:s.gridTemplateColumns,fontSize:s.fontSize,fontWeight:s.fontWeight,lineHeight:s.lineHeight,overflowX:s.overflowX,overflowY:s.overflowY}};
      const resource=img=>{const raw=img.getAttribute('src')||'';try{const url=new URL(raw,location.href);return url.origin===location.origin?url.pathname+url.search+url.hash:raw}catch{return raw}};
      const main=q('main.a5-editorial-pilot'), metric=q('.topic-controls [data-metric].active'), theme=q('.compare-context-nav [data-context-theme].active'), chart=q('#compare-bars');
      return {
        main:{theme:main?.dataset.theme||'',classes:main?[...main.classList].sort():[]},
        active:{theme:theme?.dataset.contextTheme||'',metric:metric?.dataset.metric||'',metricStyle:pack(metric),themeStyle:pack(theme)},
        layout:{nav:pack(q('.compare-context-nav')),topic:pack(q('.topic-hero')),sidebar:pack(q('#compare-workspace>.topic-controls')),workspace:pack(q('#compare-workspace')),chart:pack(chart),toolbar:pack(q('#compare-bars .ux-view-toolbar')),benchmark:pack(q('#compare-benchmark')),tools:pack(q('#compare-tools')),territories:pack(q('#compare-territori'))},
        structure:{themes:[...document.querySelectorAll('[data-context-theme]')].map(x=>x.dataset.contextTheme),metrics:[...document.querySelectorAll('.topic-controls [data-metric]')].map(x=>x.dataset.metric),groups:[...document.querySelectorAll('.topic-controls .metric-group')].map(x=>[x.dataset.section||'',x.querySelectorAll('[data-metric]').length]),children:[...(main?.children||[])].map(x=>[x.tagName,x.id||'', [...x.classList].sort().join(' ')]),chart:[chart?.querySelectorAll('svg').length||0,chart?.querySelectorAll('canvas').length||0,chart?.querySelectorAll('button').length||0,chart?.querySelectorAll('details').length||0],territoryImages:[...document.querySelectorAll('#compare-territori .topic-town-card-media img')].map(img=>[resource(img),img.getAttribute('alt')||''])},
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
    page.evaluate("() => window.scrollTo(0,0)")
    box=loc.bounding_box()
    if not box or box["width"]<2 or box["height"]<2: return None,{"count":1,"rendered":False}
    try:
        return loc.screenshot(animations="disabled"),{"count":1,"box":box}
    finally:
        # Locator screenshots scroll; never leak that viewport into the next state/capture.
        page.evaluate("() => window.scrollTo(0,0)")

def history_view_state(page):
    return page.evaluate("""() => {
      const shell=document.querySelector('#compare-bars .ux-view-shell');
      const button=shell?.querySelector('[data-view-mode="history"]');
      const pane=shell?.querySelector('[data-view-pane="history"]');
      const text=(pane?.textContent || '').trim();
      return {
        buttonExists:Boolean(button),
        paneExists:Boolean(pane),
        disabled:Boolean(button?.disabled),
        svgCount:pane?.querySelectorAll('svg').length || 0,
        canvasCount:pane?.querySelectorAll('canvas').length || 0,
        unavailable:Boolean(
          pane?.querySelector('.ux-history-unavailable')
          || /serie storica non disponibile/i.test(text)
        ),
        contentLength:text.length,
        lineRows:[...pane?.querySelectorAll('.ux-history-chart svg .ux-series-group[data-history-town]')||[]].map(group=>({
          town:group.dataset.historyTown,labels:[...group.querySelectorAll('.chart-point')].map(point=>point.getAttribute('aria-label'))
        })),
        twoPointRows:[...pane?.querySelectorAll('.ux-two-point-chart .ux-two-point-row[data-history-town]')||[]].map(row=>({
          town:row.dataset.historyTown,
          years:[...row.querySelectorAll('.ux-two-point-value small')].map(x=>x.textContent.trim()),
          values:[...row.querySelectorAll('.ux-two-point-value strong')].map(x=>x.textContent.trim())
        })),
      };
    }""")


def source_checked_history(before,after,sources):
    from test_a5_camaiore_full_golden_lock import unchanged_current_rows
    if not unchanged_current_rows(before,after): return None
    observations={}; common=None
    previous={row.get("town"):row for row in before.get("rows",[])}
    for row in after.get("rows",[]):
        series=row.get("series") or {}; years=series.get("years",[]); values=series.get("values",[])
        if (len(years)<2 or len(years)!=len(values) or len(set(map(str,years)))!=len(years)
                or not all(type(value) in (int,float) and math.isfinite(value) for value in values)
                or series.get("sourceSnapshot") not in sources): return None
        if not all(str(year).isdigit() for year in years):
            # ARS publishes native rolling multi-year periods, preserved verbatim.
            # Only this frozen source and its baseline legacy observations qualify.
            path="data/source-snapshots/ars-a3-5-legacy-history.json"
            native=sources.get(path,{}); source=native.get("indicators",{}).get(after.get("meta",{}).get("key"),{})
            legacy=previous.get(row.get("town"),{}).get("a3History",{})
            if not (series.get("sourceSnapshot")==path and native.get("publisher")=="ARS Toscana"
                and all(re.fullmatch(r"[0-9]{4}-[0-9]{4}",str(year)) for year in years)
                and list(map(str,years))==source.get("periods")==legacy.get("periods")
                and values==source.get("values",{}).get(row.get("town"))==legacy.get("values")
                and series.get("sourceUrl")==source.get("exportUrl")==legacy.get("sourceUrl")
                and legacy.get("sourceSnapshot")==path):return None
        period=set(map(str,years)); common=period if common is None else common & period
        observations[row["town"]]=dict(zip(map(str,years),values))
    return observations if len(observations)==7 and len(common or [])>=2 else None


def two_point_observations_match(dom,observations):
    rows=dom.get("twoPointRows",[])
    if len(rows)!=7 or not observations: return False
    expected={town.lower().replace(" ","-"):values for town,values in observations.items()}
    if len({row["town"] for row in rows})!=7 or {row["town"] for row in rows}!=set(expected):return False
    for row in rows:
        if len(row["years"])!=2 or len(row["values"])!=2 or len(set(row["years"]))!=2:return False
        for year,text in zip(row["years"],row["values"]):
            match=re.search(r"-?[\d.]+(?:,\d+)?",text)
            if year not in expected[row["town"]] or not match:return False
            token=match.group(); decimals=len(token.split(",")[1]) if "," in token else 0
            value=float(token.replace(".","").replace(",","."))
            if abs(value-expected[row["town"]][year])>0.5*10**(-decimals)+1e-8:return False
    return True


def line_observations_match(dom,observations):
    rows=dom.get("lineRows",[])
    expected={town.lower().replace(" ","-"):(town,values) for town,values in (observations or {}).items()}
    if len(rows)!=7 or len({row["town"] for row in rows})!=7 or {row["town"] for row in rows}!=set(expected):return False
    for row in rows:
        town,values=expected[row["town"]];seen=set()
        for label in row["labels"]:
            match=re.fullmatch(re.escape(town)+r" · ([0-9]{4}(?:-[0-9]{4})?): (.*)",label or "")
            if not match:return False
            year,text=match.groups(); numeric=re.search(r"-?[\d.]+(?:,\d+)?",text)
            if year not in values or year in seen or not numeric:return False
            seen.add(year);token=numeric.group();decimals=len(token.split(",")[1]) if "," in token else 0
            value=float(token.replace(".","").replace(",","."))
            if abs(value-values[year])>0.5*10**(-decimals)+1e-8:return False
        if seen!=set(values):return False
    return True


def preserved_history_extension(before,observations):
    if not observations:return False
    extended=False
    for row in before.get("rows",[]):
        series=row.get("series") or {}; years=series.get("years",[]); values=series.get("values",[])
        if len(years)<2 or len(years)!=len(values) or len(set(map(str,years)))!=len(years):return False
        current=observations.get(row.get("town"),{})
        for year,value in zip(map(str,years),values):
            if type(value) not in (int,float) or not math.isfinite(value) or year not in current or not math.isclose(value,current[year],abs_tol=1e-9,rel_tol=0):return False
        extended=extended or len(current)>len(years)
    return len(before.get("rows",[]))==7 and extended


def verified_history_upgrade(baseline_state,current_state,baseline_page,current_page,observations,extension=False):
    before=history_view_state(baseline_page); after=history_view_state(current_page)
    if not (
        before["buttonExists"] and before["paneExists"]
        and (before["disabled"] or (extension and not before["unavailable"]))
        and after["buttonExists"] and after["paneExists"] and not after["disabled"]
        and observations
        and (line_observations_match(after,observations) or two_point_observations_match(after,observations))
        and not after["unavailable"] and after["contentLength"] > 0
    ):
        return False, {}

    if extension and not line_observations_match(after,observations):return False, {}

    normalized=json.loads(json.dumps(current_state))
    normalized["structure"]["chart"]=baseline_state["structure"]["chart"]
    if normalized != baseline_state:
        return False, {}
    return True, {"baseline":before,"current":after}


def set_history_disabled(page,disabled):
    return page.evaluate("""disabled => {
      const button=document.querySelector('#compare-bars .ux-view-shell [data-view-mode="history"]');
      if (!button) return false;
      button.disabled=disabled;
      return true;
    }""", disabled)


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
        stable(page)
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

def verify_thematic_benchmark(page, selector, metric):
    """Validate actual enriched cards and their source before capture normalization."""
    benchmark=metric["meta"]["benchmark"]
    aggregate=metric.get("aggregate", {})
    if not isinstance(aggregate,dict) or not aggregate.get("label") or not isinstance(aggregate.get("value"),(int,float)):
        raise AssertionError("New thematic benchmark has no native public aggregate")
    label=aggregate["label"]
    for prefix in ("Valore ","Media ","Quota ","Tasso "):
        label=label.replace(prefix,"",1)
    cards=[{"label":label,"value":aggregate["value"]},
           {"label":"Toscana","value":benchmark["tuscany"]}]
    if benchmark.get("italy") is not None: cards.append({"label":"Italia","value":benchmark["italy"]})
    result=page.locator(selector).evaluate("""(host, expected) => {
      const cards=[...host.querySelectorAll('.benchmark-card')];
      const numeric=text=>{const match=String(text).match(/-?[\\d.]+(?:,\\d+)?/);
        return match?Number(match[0].replaceAll('.','').replace(',','.')):null;};
      const observations=cards.map((card,i)=>{
        const value=card.querySelector('strong'), label=card.querySelector('span');
        const text=value?.textContent||'', actual=numeric(text), wanted=expected.cards[i];
        const decimals=(text.match(/,(\\d+)/)||[])[1]?.length||0;
        const rect=card.getBoundingClientRect(), valueRect=value?.getBoundingClientRect();
        return {text,label:label?.textContent.trim(),valid:Boolean(wanted && label?.textContent.trim()===wanted.label
          && actual!==null && Math.abs(actual-wanted.value)<=.5*Math.pow(10,-decimals)+1e-8
          && rect.width>0 && rect.height>0 && valueRect && valueRect.right<=rect.right+.5)};
      });
      return {ok:Boolean(host.querySelector('.benchmark-section') && !host.querySelector('[style]') && cards.length===expected.cards.length
        && observations.every(x=>x.valid)
        && host.querySelector('.overline')?.textContent.trim()===`Confronto omogeneo · ${expected.year}`
        && host.querySelector('.benchmark-note a')?.getAttribute('href')===expected.url
        && cards.slice(1).every(card=>card.querySelector('small')?.textContent===expected.source)),observations};
    }""",{"cards":cards,"year":str(benchmark["year"]),"url":benchmark["url"],"source":benchmark["source"]})
    if not result["ok"]: raise AssertionError(f"Invalid acquired thematic benchmark: {result}")
    return result



def definition_fingerprint(loc):
    return loc.evaluate("""host=>[host,...host.querySelectorAll('*')].map(node=>{
      const style=getComputedStyle(node);
      return {tag:node.tagName,classes:[...node.classList].sort(),
        style:Object.fromEntries(['display','position','fontFamily','fontSize','fontWeight','fontStyle','lineHeight','letterSpacing','color','backgroundColor','borderColor','borderRadius','padding','margin','gap','transform','overflowX','overflowY'].map(key=>[key,style[key]]))};})""")

@contextmanager
def corrected_tourism_metadata(a,b,before,after,catalog,sources):
    # Two source-certified annotations changed after the frozen UI checkpoint.
    # The native levels stay frozen; this is a capture fixture, never public data.
    key=after.get("meta",{}).get("key"); fields={"tourismBedsPer1000":("beds","Posti letto"),"tourismStructuresPer1000":("structures","Strutture ricettive")}
    restorations=[]; additions=[]
    try:
        if key in fields:
            from test_a5_camaiore_full_golden_lock import unchanged_current_rows
            meta=after["meta"]; evidence=meta.get("sourceMeta",{}); native=sources.get(evidence.get("snapshot"),{})
            population=catalog.get("population",{}); popmeta=population.get("meta",{}); poppath=evidence.get("populationSnapshot")
            current_year=str(native.get("referenceYear")); popyear=str(popmeta.get("year")); numerator,noun=fields[key]
            expected_description=f"{noun} Istat {current_year} ogni 1.000 residenti al 1° gennaio {popyear}."
            expected_source="Istat — capacità degli esercizi ricettivi / popolazione residente"
            eligible=(unchanged_current_rows(before,after) and meta.get("label")==before["meta"].get("label")
                and meta.get("unit")=="per1000" and str(meta.get("year"))==current_year
                and meta.get("description")==expected_description and meta.get("source")==expected_source
                and after.get("sourceUrl")==native.get("sourceUrl")
                and meta.get("benchmark",{}).get("sourceSnapshot")==evidence.get("snapshot")
                and native.get("qualityGate",{}).get("status")=="PASS"
                and poppath in sources and native.get("population",{}).get("sourceSnapshot")==poppath
                and str(native.get("population",{}).get("year"))==popyear
                and popmeta.get("benchmark",{}).get("sourceSnapshot")==poppath)
            if not eligible:raise AssertionError(f"Uncertified tourism metadata correction {key}")
            counts=native.get("municipalReconciliation",{}); denominators={row["code"]:row["value"] for row in population.get("rows",[])}
            if len(counts)!=7 or len(denominators)!=7 or set(counts)!={row["code"] for row in after["rows"]}:raise AssertionError("Incomplete native tourism reconciliation")
            for row in after["rows"]:
                count=counts[row["code"]].get(numerator);denominator=denominators.get(row["code"])
                if (type(count) not in (int,float) or type(denominator) not in (int,float) or denominator<=0
                    or not math.isclose(row["value"],count/denominator*1000,rel_tol=0,abs_tol=1e-9)):
                    raise AssertionError("Native tourism level mismatch")
            selector="#compare-definition > .indicator-definition"; cur=b.locator(selector); base=a.locator(selector)
            if cur.count()!=1 or base.count()!=1:raise AssertionError("Missing tourism definition")
            actual=cur.evaluate("""host=>({label:host.querySelector('h2')?.textContent.trim(),description:host.querySelector('p')?.textContent.trim(),
              year:[...host.querySelectorAll('dl>div')].find(row=>row.querySelector('dt')?.textContent.trim()==='Anno')?.querySelector('dd')?.textContent.trim(),
              source:host.querySelector('dl a')?.textContent.trim(),url:host.querySelector('dl a')?.getAttribute('href'),inline:Boolean(host.querySelector('[style]'))})""")
            if actual!={"label":meta["label"],"description":expected_description,"year":current_year,"source":expected_source+" ↗","url":after["sourceUrl"],"inline":False}:
                raise AssertionError(f"Incorrect native tourism metadata DOM {actual}")
            if definition_fingerprint(base)!=definition_fingerprint(cur):raise AssertionError("Tourism metadata structure/CSS changed")
            fields=[("p",False),("dl>div:has(dt:text-is('Anno'))>dd",False),("dl a",True)]
            for field,link in fields:
                current_node=cur.locator(field); baseline_node=base.locator(field)
                if current_node.count()!=1 or baseline_node.count()!=1 or current_node.evaluate("node=>node.childElementCount") or baseline_node.evaluate("node=>node.childElementCount"):
                    raise AssertionError("Tourism annotation must preserve leaf-node structure")
                restorations.append((current_node,current_node.text_content(),current_node.get_attribute("href") if link else None,link))
                current_node.evaluate("(node,text)=>node.textContent=text",baseline_node.text_content())
                if link:current_node.evaluate("(node,href)=>node.setAttribute('href',href)",baseline_node.get_attribute("href"))
            additions.append({"kind":"source-certified-metadata-correction","snapshot":evidence["snapshot"]})
        yield additions
    finally:
        for node,text,href,link in reversed(restorations):
            node.evaluate("(node,text)=>node.textContent=text",text)
            if link:node.evaluate("(node,href)=>href===null?node.removeAttribute('href'):node.setAttribute('href',href)",href)


@contextmanager
def corrected_native_descriptions(a,b,before,after,catalog,sources):
    # Four pre-existing source annotations were clarified without changing levels.
    # Capture changes only the validated description leaf; current DOM stays intact.
    key=after.get("meta",{}).get("key"); keys={"pharmaciesPer1000","selfContainment","outboundCommutersRate","inboundCommutersRate"}
    restore=None; additions=[]
    try:
        if key in keys:
            from test_a5_camaiore_full_golden_lock import unchanged_current_rows
            meta=after["meta"]; benchmark=meta.get("benchmark",{}); path=benchmark.get("sourceSnapshot"); native=sources.get(path,{})
            year=str(native.get("benchmarks",{}).get(key,{}).get("year")); popyear=str(native.get("population",{}).get("year"))
            expected={
                "pharmaciesPer1000":f"Farmacie aperte al pubblico al 31 dicembre {year} secondo gli intervalli di validità ministeriali, incluse succursali e dispensari, rapportate ai residenti al 1° gennaio {popyear}.",
                "selfContainment":f"Quota dei pendolari residenti per lavoro il cui Comune di lavoro coincide con quello di residenza, secondo la matrice Istat {year}.",
                "outboundCommutersRate":f"Residenti che lavorano fuori Comune, rapportati alla popolazione. Il rapporto usa la popolazione residente al 1° gennaio {popyear}.",
                "inboundCommutersRate":f"Lavoratori provenienti da altri Comuni, rapportati alla popolazione. Il rapporto usa la popolazione residente al 1° gennaio {popyear}."}[key]
            preserved=all(meta.get(field)==before["meta"].get(field) for field in ("label","unit","year","source")) and (after.get("sourceUrl")==before.get("sourceUrl") or (key=="selfContainment" and after.get("sourceUrl")==native.get("sourceUrl")))
            gate=native.get("qualityGate",{})
            proof=(native.get("referenceDate")==year+"-12-31" and gate.get("publicReconciliation")=="7/7 at public two decimals"
                and "incluse ordinarie, succursali, dispensari e dispensari stagionali" in native.get("scope",{}).get("note","")
                and "data_inizio_validita" in native.get("source",{}).get("validityRule","")
                if key=="pharmaciesPer1000" else key in gate.get("public7of7",[])
                and year=="2021" and "Autocontenimento: flussi interni al Comune / (flussi interni + flussi in uscita)" in native.get("scope",{}).get("note","")
                and "popolazione pubblica al 1° gennaio 2026" in native.get("scope",{}).get("note",""))
            if not (unchanged_current_rows(before,after) and preserved and proof and gate.get("status")=="PASS"
                and str(meta.get("year"))==year and popyear==str(catalog["population"]["meta"]["year"])
                and meta.get("description")==expected and benchmark.get("url")==native.get("sourceUrl")):
                raise AssertionError(f"Uncertified native description correction {key}")
            selector="#compare-definition > .indicator-definition";base=a.locator(selector);cur=b.locator(selector)
            if base.count()!=1 or cur.count()!=1 or definition_fingerprint(base)!=definition_fingerprint(cur):
                raise AssertionError("Native description structure/CSS changed")
            if cur.locator("dl a").count()!=1 or cur.locator("dl a").get_attribute("href")!=after.get("sourceUrl"):
                raise AssertionError("Native description source link mismatch")
            node=cur.locator("p");old=base.locator("p")
            if node.count()!=1 or old.count()!=1 or node.evaluate("n=>n.childElementCount") or old.evaluate("n=>n.childElementCount") or node.inner_text()!=expected:
                raise AssertionError("Invalid native description DOM")
            restore=(node,node.text_content());node.evaluate("(n,text)=>n.textContent=text",old.text_content())
            additions.append({"kind":"source-certified-description-correction","snapshot":path})
        yield additions
    finally:
        if restore:restore[0].evaluate("(n,text)=>n.textContent=text",restore[1])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--current-base",required=True); ap.add_argument("--baseline-base",required=True); ap.add_argument("--config",required=True); ap.add_argument("--report-dir",required=True); args=ap.parse_args()
    from test_a5_camaiore_full_golden_lock import load_enrichment_evidence, screenshot_enrichment_normalization
    cfg=json.loads(Path(args.config).read_text()); folder=Path(args.report_dir); folder.mkdir(parents=True,exist_ok=True); fail=[]; allowed_history_upgrades=[]; allowed_enrichments=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        request=p.request.new_context()
        baseline_metrics,current_metrics,source_evidence=load_enrichment_evidence(request,args.baseline_base,args.current_base)
        for metric in current_metrics.values():
            for row in metric.get("rows",[]):
                path=(row.get("series") or {}).get("sourceSnapshot")
                if path and path not in source_evidence:
                    if not path.startswith("data/source-snapshots/") or ".." in path: raise AssertionError("Unsafe historical evidence path")
                    response=request.get(urljoin(args.current_base,path))
                    if not response.ok:raise AssertionError(f"Missing frozen history source {path}")
                    source_evidence[path]=response.json()
        request.dispose()
        @contextmanager
        def normalization(a,b,metric):
            with corrected_tourism_metadata(a,b,baseline_metrics[metric],current_metrics[metric],current_metrics,source_evidence) as metadata, corrected_native_descriptions(a,b,baseline_metrics[metric],current_metrics[metric],current_metrics,source_evidence) as descriptions:
                with screenshot_enrichment_normalization(a,b,baseline_metrics[metric],current_metrics[metric],source_evidence,
                    benchmark_selector="#compare-benchmark",note_selector="#compare-bars .ux-view-shell > .ux-view-note",
                    benchmark_verifier=verify_thematic_benchmark,diagnostic_dir=folder) as additions:
                    yield metadata+descriptions+additions
        d=browser.new_page(viewport={"width":1440,"height":1100}); contract=discover(d,args.baseline_base,cfg["seed_theme"]); current=discover(d,args.current_base,cfg["seed_theme"]); d.close()
        if contract!=current: fail.append({"key":"catalog","kind":"theme-metric-contract","baseline":contract,"current":current})
        for vp in cfg["viewports"]:
            a=browser.new_page(viewport={"width":vp["width"],"height":vp["height"]}); b=browser.new_page(viewport={"width":vp["width"],"height":vp["height"]}); aerr=[]; berr=[]
            a.on("pageerror",lambda e:aerr.append(str(e))); b.on("pageerror",lambda e:berr.append(str(e)))
            for theme,metrics in contract.items():
                path=f"confronta/{theme}/?indicatore={metrics[0]}"; go(a,args.baseline_base,path); go(b,args.current_base,path)
                with normalization(a,b,metrics[0]):
                    for rn,sel in THEME_REGIONS: region(a,b,sel,f"{vp['name']}:{theme}:theme:{rn}",fail,folder,cfg["channel_threshold"],cfg["pixel_tolerance"])
                for metric in metrics:
                    choose(a,metric); choose(b,metric); key=f"{vp['name']}:{theme}:{metric}"
                    with normalization(a,b,metric) as additions:
                        allowed_enrichments.extend({"key":key,**item} for item in additions)
                        sa=state(a); sb=state(b)

                        history_upgrade=False; history_detail={}
                        if sa!=sb:
                            history_upgrade,history_detail=verified_history_upgrade(sa,sb,a,b,source_checked_history(baseline_metrics[metric],current_metrics[metric],source_evidence),
                                preserved_history_extension(baseline_metrics[metric],source_checked_history(baseline_metrics[metric],current_metrics[metric],source_evidence)))
                            if history_upgrade:
                                allowed_history_upgrades.append({"key":key,**history_detail})
                            else:
                                fail.append({"key":key,"kind":"state-diff","baseline":sa,"current":sb})
                        if sb["main"]["theme"]!=theme or sb["active"]["metric"]!=metric: fail.append({"key":key,"kind":"active-state","state":sb["active"],"theme":sb["main"]["theme"]})
                        if len(sb["structure"].get("territoryImages") or []) != 7:
                            fail.append({"key":key,"kind":"territory-images-contract","images":sb["structure"].get("territoryImages")})
                        overflow(sa,sb,key,fail)
                        for rn,sel in METRIC_REGIONS:
                            if history_upgrade and rn=="workspace":
                                note_selector="#compare-bars .ux-view-shell > .ux-view-note"
                                old_note=a.locator(note_selector).inner_text(); new_note=b.locator(note_selector).inner_text()
                                replace_note=(old_note=="Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni."
                                    and new_note=="Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.")
                                baseline_disabled=history_detail["baseline"]["disabled"]
                                current_disabled=history_detail["current"]["disabled"]
                                set_history_disabled(b,baseline_disabled)
                                try:
                                    if replace_note:b.locator(note_selector).evaluate("(node,text)=>node.textContent=text",old_note)
                                    region(a,b,sel,f"{key}:{rn}",fail,folder,cfg["channel_threshold"],cfg["pixel_tolerance"])
                                finally:
                                    if replace_note:b.locator(note_selector).evaluate("(node,text)=>node.textContent=text",new_note)
                                    set_history_disabled(b,current_disabled)
                            else:
                                region(a,b,sel,f"{key}:{rn}",fail,folder,cfg["channel_threshold"],cfg["pixel_tolerance"])
            if aerr: fail.append({"key":vp["name"],"kind":"baseline-page-errors","errors":aerr})
            if berr: fail.append({"key":vp["name"],"kind":"current-page-errors","errors":berr})
            a.close(); b.close()
        browser.close()
    total=sum(map(len,contract.values())); unique=len({m for ms in contract.values() for m in ms})
    report={"baseline":cfg["baseline"],"themes":list(contract),"themeMetricCounts":{k:len(v) for k,v in contract.items()},"metricStatesPerViewport":total,"uniqueMetricCount":unique,"viewports":cfg["viewports"],"allowedHistoryUpgrades":allowed_history_upgrades,"allowedSourceEnrichments":allowed_enrichments,"failureCount":len(fail),"failures":fail}
    (folder/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    (folder/"summary.txt").write_text(f"A5 thematic golden lock\nbaseline={cfg['baseline']}\nthemes={len(contract)}\nmetric_states_per_viewport={total}\nunique_metrics={unique}\nallowed_history_upgrades={len(allowed_history_upgrades)}\nfailures={len(fail)}\n")
    if fail: raise SystemExit(f"A5 thematic golden lock FAILED: {len(fail)} regressioni\n"+json.dumps(fail[:6],ensure_ascii=False,indent=2))
    print(f"A5 thematic golden lock OK: {len(contract)} temi, {total} stati/viewport, {unique} indicatori unici.")

if __name__=="__main__": main()
