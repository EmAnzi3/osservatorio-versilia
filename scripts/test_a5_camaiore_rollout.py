#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TOWN=os.environ.get("A5_TOWN","camaiore")
TOWN_META={
  "camaiore":{"name":"Camaiore","heroBg":"Pontile_di_Lido_di_Camaiore","heroCredit":"Pontile di Lido di Camaiore"},
  "pietrasanta":{"name":"Pietrasanta","heroBg":"Veduta_di_piazza_duomo","heroCredit":"Piazza Duomo"},
  "seravezza":{"name":"Seravezza","heroBg":"Palazzo_Mediceo_a_Seravezza","heroCredit":"Palazzo Mediceo"},
  "forte-dei-marmi":{"name":"Forte dei Marmi","heroBg":"Pontile_Forte_dei_Marmi","heroCredit":"Pontile"},
  "stazzema":{"name":"Stazzema","heroBg":"Stazzema.JPG","heroCredit":"Stazzema"}
}
if TOWN not in TOWN_META:
    raise SystemExit(f"A5_TOWN non supportato: {TOWN}")
TOWN_NAME=TOWN_META[TOWN]["name"]
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
      const specialToolbar=q('#town-topic>.history-panel.a5-shared-chart > .a5-special-renderer-toolbar');
      const fallbackActions=q('#town-topic > .town-data-actions.a5-town-fallback-actions');
      const actions=standardToolbar?.querySelector(':scope > .data-actions')
        || specialToolbar?.querySelector(':scope > .data-actions')
        || fallbackActions
        || q('#town-topic .town-data-actions');
      return {
        classes:main?[...main.classList].sort():[], theme:main?.dataset.theme||'',
        activeTheme:q('[data-profile-theme].active')?.dataset.profileTheme||'',
        activeMetric:q('.topic-controls [data-metric].active')?.dataset.metric||'',
        required:{
          hero:visible(q('.town-hero')),brief:visible(q('.town-brief')),nav:visible(q('.town-context-nav')),
          heading:visible(q('#town-topic>.town-topic-heading')),sidebar:visible(q('#town-topic>.topic-controls')),
          metricLayout:visible(q('#town-topic>.town-metric-layout')),
          chart:visible(q('#town-topic>.history-panel.a5-shared-chart')),
          toolbar:visible(standardToolbar) || visible(specialToolbar) || visible(fallbackActions),
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
        primaryTitle:(()=>{
          const e=q('#town-topic .town-metric-primary > .a5-primary-label, #town-topic .town-metric-primary > .composite-primary-label');
          return e ? {visible:visible(e),text:(e.textContent||'').trim()} : null;
        })(),
        compositeSelector:(()=>{
          const e=q('#town-topic .town-metric-primary > .composite-read-selector');
          if(!e || !visible(e)) return null;
          const select=e.querySelector('select');
          const label=e.querySelector(':scope > span');
          const parent=e.closest('.town-metric-primary');
          const c=getComputedStyle(e), s=select?getComputedStyle(select):null;
          const er=e.getBoundingClientRect(), pr=parent?.getBoundingClientRect();
          const lr=label?.getBoundingClientRect(), sr=select?.getBoundingClientRect();
          const pc=parent?getComputedStyle(parent):null;
          const contentRight=pr && pc ? pr.right-parseFloat(pc.paddingRight||'0') : null;
          const resolveColor=value=>{
            const probe=document.createElement('i');
            probe.style.color=value;
            document.body.append(probe);
            const out=getComputedStyle(probe).color;
            probe.remove();
            return out;
          };
          return {
            background:c.backgroundColor,
            border:c.borderTopColor,
            selectBackground:s?.backgroundColor||'',
            selectBorder:s?.borderTopColor||'',
            rightGap:contentRight!==null?Math.round((contentRight-er.right)*10)/10:null,
            height:Math.round(er.height*10)/10,
            selectHeight:sr?Math.round(sr.height*10)/10:null,
            labelCenterDelta:lr&&sr?Math.round(Math.abs((lr.top+lr.height/2)-(sr.top+sr.height/2))*10)/10:null,
            expectedSoft:resolveColor(getComputedStyle(document.body).getPropertyValue('--ds-theme-soft').trim()),
            expectedLine:resolveColor(getComputedStyle(document.body).getPropertyValue('--ds-theme-line').trim()),
            expectedAccent:resolveColor(getComputedStyle(document.body).getPropertyValue('--ds-theme-accent').trim())
          };
        })(),
        demographyPill:(()=>{const e=q('[data-profile-theme="demografia"]');if(!e)return null;const c=getComputedStyle(e);return {active:e.classList.contains('active'),background:c.backgroundColor,border:c.borderTopColor,color:c.color}})(),
        semantic:(()=>{
          const deep=q('#town-topic .topic-deep-dive');
          const deepHeading=(deep?.querySelector('.deep-heading h3')?.textContent||'').trim();
          const deepSummary=(deep?.querySelector('details > summary')?.textContent||'').replace(/\\s+/g,' ').trim();
          return {
            incomeText:deepHeading==='Redditi dichiarati' || /Mostra le fasce di reddito/i.test(deepSummary),
            economyDeepDive:visible(deep),
            crimeContext:visible(q('#town-context .crime-context')),
            redundantCompositeDetail:visible(q('#town-topic > .composite-fixed-detail.a5-town-extra-context, #town-topic .history-panel.a5-shared-chart > .composite-fixed-detail.a5-town-extra-context')),
            selectorDrivenDuplicate:(()=>{
              const select=q('#town-topic .town-metric-primary > .composite-read-selector select[data-composite-choice]');
              const fixed=q('#town-topic .history-panel.a5-shared-chart > .composite-fixed-detail, #town-topic .history-panel.a5-shared-chart [data-view-pane="current"] > .composite-fixed-detail');
              const cardHost=fixed?.querySelector(':scope > .composite-town-mobility');
              if(!select || !cardHost || !visible(fixed)) return false;
              const norm=value=>String(value||'').toLocaleLowerCase('it').replace(/\\s+/g,' ').trim();
              const cards=[...cardHost.querySelectorAll(':scope > article')];
              const opts=[...select.options].map(o=>norm(o.textContent));
              const labels=cards.map(card=>norm(card.querySelector(':scope > span')?.textContent));
              const notes=cards.map(card=>norm(card.querySelector(':scope > small')?.textContent));
              const periodOnly=notes.every(note=>!note || (/\\b(19|20)\\d{2}\\b/.test(note) && !/dichiarant|dipendent|persone|resident|zone|record|localit/.test(note)));
              const labelsEquivalent=opts.length===labels.length && opts.every(label=>labels.some(card=>card===label||card.includes(label)||label.includes(card)));
              return opts.length>0 && opts.length===cards.length && (labelsEquivalent||periodOnly);
            })(),
            demographicHistoryDuplicate:visible(q('#town-topic .history-panel.a5-shared-chart > .composite-fixed-detail .demographic-history')),
            communityPnrrDeepDive:visible(deep) && deepHeading==='Cassa, opere e PNRR',
            legacyLibraryCurrent:visible(q('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .ux-comparison-bars > .ux-bar-row')),
            economicScope:(()=>{
              const e=q('#town-topic .town-metric-primary > .economic-scope-control');
              const parent=e?.closest('.town-metric-primary');
              const select=e?.querySelector('select[data-economic-scope]');
              const er=e?.getBoundingClientRect(), sr=select?.getBoundingClientRect(), pr=parent?.getBoundingClientRect();
              const pc=parent?getComputedStyle(parent):null;
              const contentRight=pr&&pc?pr.right-parseFloat(pc.paddingRight||'0'):null;
              return {
                inPrimary:visible(e),
                inChart:visible(q('#town-topic .history-panel.a5-shared-chart > .economic-scope-control')),
                rightGap:er&&contentRight!==null?Math.round((contentRight-er.right)*10)/10:null,
                selectVisible:visible(select),
                selectWidth:sr?Math.round(sr.width*10)/10:null,
                selectHeight:sr?Math.round(sr.height*10)/10:null,
                selectedText:(select?.selectedOptions?.[0]?.textContent||'').trim()
              };
            })(),
            healthRedundantDetail:visible(q('#town-topic .composite-fixed-detail .health-sex-detail, #town-topic .composite-fixed-detail .health-demographic-detail, #town-topic .composite-fixed-detail .demographic-history')),
            hydroRiskDeepDive:visible(deep) && /Dettaglio del rischio|Pressioni ambientali/i.test((deep.textContent||'')),
            inlineDetail:(()=>{
              const fixed=q('#town-topic .history-panel.a5-shared-chart > .composite-fixed-detail.a5-town-inline-detail');
              return {visible:visible(fixed),parentChart:Boolean(fixed?.parentElement?.matches('.history-panel.a5-shared-chart'))};
            })(),
            waterDetail:(()=>{
              const d=q('#town-topic .water-quality-town-disclosure');
              const icon=d?.querySelector(':scope > summary > i');
              return {exists:Boolean(d),open:Boolean(d?.open),iconVisible:visible(icon)};
            })(),
            specialView:(()=>{
              const tb=q('#town-topic .history-panel.a5-shared-chart > .a5-special-renderer-toolbar');
              return {
                toolbar:visible(tb),
                current:Boolean(tb?.querySelector('[data-view-mode="current"]')),
                history:Boolean(tb?.querySelector('[data-view-mode="history"]')),
                historyDisabled:Boolean(tb?.querySelector('[data-view-mode="history"]')?.disabled)
              };
            })(),
            financialDetachedHistory:visible(q('#town-topic > .financial-profile-history, #town-topic > .composite-fixed-detail .financial-profile-history, #town-topic .a5-town-extra-context .financial-profile-history')),
            financialShell:{
              shell:visible(q('#town-topic .history-panel.a5-shared-chart > .ux-view-shell')),
              current:visible(q('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .comparison-bars')),
              historyButton:Boolean(q('#town-topic .history-panel.a5-shared-chart [data-view-mode="history"]')),
              historyChart:Boolean(q('#town-topic .history-panel.a5-shared-chart [data-view-pane="history"] .ux-history-chart, #town-topic .history-panel.a5-shared-chart [data-view-pane="history"] .ux-two-point-chart'))
            }
          };
        })(),
        additionalInfoPlacement:(()=>{
          const topic=q('#town-topic');
          const chart=q('#town-topic > .history-panel.a5-shared-chart');
          const benchmark=q('#town-topic > .town-benchmark-host');
          const tools=q('#town-topic > .town-post-benchmark-tools');
          if(!topic||!chart)return null;
          const children=[...topic.children];
          const chartIndex=children.indexOf(chart);
          const benchmarkIndex=children.indexOf(benchmark);
          const toolsIndex=children.indexOf(tools);
          const stray=children.slice(chartIndex+1).filter(e=>visible(e)&&!e.matches('.town-benchmark-host,.town-post-benchmark-tools,.town-data-actions')).map(e=>({tag:e.tagName,cls:e.className||'',text:(e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,100)}));
          const inline=[...chart.querySelectorAll(':scope > .a5-town-inline-info, :scope > .composite-fixed-detail.a5-town-inline-detail, :scope > .a5-town-income-detail')].filter(visible);
          return {chartIndex,benchmarkIndex,toolsIndex,stray,inlineCount:inline.length};
        })(),
        extras:(()=>{const topic=q('#town-topic');if(!topic)return[];const tr=topic.getBoundingClientRect();return [...topic.children].filter(e=>visible(e)&&!e.matches('.town-topic-heading,.topic-controls,.town-metric-layout,.history-panel,.town-benchmark-host,.town-post-benchmark-tools,.town-data-actions')).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,cls:e.className||'',width:r.width,topicWidth:tr.width,left:r.left,topicLeft:tr.left}})})(),
        currentViz:(()=>{
          const bars=q('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .comparison-bars, #town-topic .history-panel.a5-shared-chart [data-ov-climate-pane="current"] .comparison-bars');
          if(!bars)return null;
          const numberFromLabel=text=>{
            const match=String(text||'').match(/-?[\\d.]+(?:,\\d+)?/);
            if(!match)return null;
            const value=Number(match[0].replaceAll('.','').replace(',','.'));
            return Number.isFinite(value)?value:null;
          };
          const visibleUnit=text=>{
            const value=String(text||'');
            if(value.includes('€/ab.'))return 'eurPerResident';
            if(value.includes('€/m²')||value.includes('€ /m²'))return 'eurArea';
            if(value.includes('€/l')||value.includes('€ /l'))return 'eurLiter';
            if(value.includes('€'))return 'currency';
            if(value.includes('%'))return 'percent';
            if(/ogni\\s+1\\.000/i.test(value))return 'per1000';
            if(/ogni\\s+100/i.test(value))return 'per100';
            if(/\\banni\\b/i.test(value))return 'years';
            if(value.includes('°C'))return 'celsius';
            if(/\\bmm\\b/i.test(value))return 'mm';
            if(/\\/10\\b/.test(value))return 'decile';
            if(/\\/20\\b/.test(value))return 'ventile';
            return '';
          };
          const rows=[...bars.querySelectorAll(':scope > .bar-row')].map(el=>{
            const label=(el.querySelector('strong')?.textContent||'').trim();
            return {
              value:el.getAttribute('data-viz-value')||'',
              unit:el.getAttribute('data-viz-unit')||'',
              label,
              displayValue:numberFromLabel(label),
              displayUnit:visibleUnit(label),
              left:parseFloat(el.querySelector('.comparison-dot')?.style.left||'')
            };
          });
          const axis=(bars.querySelector(':scope > .comparison-axis')?.textContent||'').replace(/\\s+/g,' ').trim();
          return {
            contract:bars.dataset.visualContract||'',
            unit:bars.dataset.visualUnit||'',
            axis,
            axisVisibleUnit:visibleUnit(axis),
            rows
          };
        })(),
        incomeDetail:(()=>{const e=q('#town-topic .history-panel.a5-shared-chart > .a5-town-income-detail');if(!e)return null;const r=e.getBoundingClientRect();const first=e.querySelector('.income-bands-detail > .composite-town-detail > div')?.getBoundingClientRect();return {visible:visible(e),heading:(e.querySelector('.a5-income-context-heading h4')?.textContent||'').trim(),leftPad:first?first.left-r.left:null,rightPad:first?r.right-first.right:null}})(),
        overflow:{doc:[document.documentElement.scrollWidth,document.documentElement.clientWidth],body:[document.body.scrollWidth,document.body.clientWidth]}
      };
    }""")



def climate_layout_response(page,metric,key,fail):
    targets={"climateTemperatureTrend50y","climatePrecipitationTrend50y","climateTminTrend","climateTmaxTrend"}
    if metric not in targets:
        return
    shell=page.locator('#town-topic .history-panel.a5-shared-chart [data-ov-climate-shell^="town-"]')
    if shell.count()!=1:
        fail.append({"key":key,"kind":"climate-shell-missing"})
        return
    for mode in ("current","history"):
        button=shell.locator(f'[data-ov-climate-view="{mode}"]')
        if button.count()!=1:
            fail.append({"key":key,"kind":"climate-view-button-missing","mode":mode})
            continue
        button.click()
        stable(page)
        geometry=page.evaluate("""mode => {
          const shell=document.querySelector('#town-topic .history-panel.a5-shared-chart [data-ov-climate-shell^="town-"]');
          const pane=shell?.querySelector(`[data-ov-climate-pane="${mode}"]`);
          const content=mode==='current'
            ? pane?.querySelector('.comparison-bars[data-a5-climate-current="true"]')
            : pane?.querySelector('.ov-climate-town-history');
          if(!pane||!content)return null;
          const pr=pane.getBoundingClientRect(), cr=content.getBoundingClientRect(), pc=getComputedStyle(pane);
          return {
            paddingLeft:parseFloat(pc.paddingLeft||'0'),
            paddingRight:parseFloat(pc.paddingRight||'0'),
            leftInset:Math.round((cr.left-pr.left)*10)/10,
            rightInset:Math.round((pr.right-cr.right)*10)/10,
            scrollWidth:pane.scrollWidth,
            clientWidth:pane.clientWidth
          };
        }""",mode)
        if not geometry:
            fail.append({"key":key,"kind":"climate-pane-content-missing","mode":mode})
            continue
        if geometry["paddingLeft"]<10 or geometry["paddingRight"]<10 or geometry["leftInset"]<8 or geometry["rightInset"]<8:
            fail.append({"key":key,"kind":"climate-edge-spacing","mode":mode,"geometry":geometry})
        if geometry["scrollWidth"]>geometry["clientWidth"]+2:
            fail.append({"key":key,"kind":"climate-pane-overflow","mode":mode,"geometry":geometry})
    lollipop=page.evaluate("""() => {
      const pane=document.querySelector('#town-topic .history-panel.a5-shared-chart [data-ov-climate-pane="current"]');
      const bars=pane?.querySelector('.comparison-bars[data-a5-climate-current="true"]');
      if(!bars)return null;
      return {
        legacy:Boolean(pane.querySelector('.ov-climate-current-list')),
        rows:bars.querySelectorAll(':scope > .bar-row').length,
        dots:bars.querySelectorAll(':scope > .bar-row .comparison-dot').length,
        references:bars.querySelectorAll(':scope > .bar-row .comparison-reference').length,
        legend:Boolean(bars.querySelector(':scope > .comparison-legend')),
        axis:Boolean(bars.querySelector(':scope > .comparison-axis')),
        contract:bars.dataset.visualContract||'',
        unit:bars.dataset.visualUnit||''
      };
    }""")
    expected_unit="mm" if metric=="climatePrecipitationTrend50y" else "°C"
    if not lollipop or lollipop.get("legacy") or lollipop.get("rows")!=7 or lollipop.get("dots")!=7 or lollipop.get("references")!=7 or not lollipop.get("legend") or not lollipop.get("axis") or lollipop.get("contract")!="rendered" or lollipop.get("unit")!=expected_unit:
        fail.append({"key":key,"kind":"climate-current-not-standard-lollipop","lollipop":lollipop,"expectedUnit":expected_unit})
    current=shell.locator('[data-ov-climate-view="current"]')
    if current.count()==1:
        current.click()
        stable(page)

def selector_graph_response(page,metric,key,fail):
    targets={
      "employmentRate","unemploymentRate","activityRate","diplomaPlus","tertiary",
      "hypertensionPrevalence","copdPrevalence","ischemicHeartDiseasePrevalence",
      "heartFailurePrevalence","priorStrokePrevalence","diabetes","dementia",
      "cropProfile","financialDebtProfile"
    }
    if metric not in targets:
        return
    before=page.evaluate("""() => {
      const chart=document.querySelector('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .comparison-bars');
      const select=document.querySelector('#town-topic .town-metric-primary [data-demographic-town-age], #town-topic .town-metric-primary select[data-composite-choice]');
      const signature=chart ? [...chart.querySelectorAll(':scope > .bar-row')].map(row=>[
        row.querySelector(':scope > strong')?.textContent||'',
        row.querySelector('.comparison-dot')?.style.left||'',
        row.getAttribute('aria-label')||''
      ].join('~')).join('|') : '';
      return {signature,value:select?.value||'',options:select?[...select.options].map(o=>o.value):[]};
    }""")
    if not before["signature"] or len(before["options"])<2:
        fail.append({"key":key,"kind":"selector-graph-test-unavailable","state":before})
        return
    changed=False
    for option in before["options"]:
        if option==before["value"]:
            continue
        page.evaluate("""value => {
          const select=document.querySelector('#town-topic .town-metric-primary [data-demographic-town-age], #town-topic .town-metric-primary select[data-composite-choice]');
          if(!select)return;
          select.value=value;
          select.dispatchEvent(new Event('change',{bubbles:true}));
        }""",option)
        stable(page)
        after=page.evaluate("""() => {
          const chart=document.querySelector('#town-topic .history-panel.a5-shared-chart [data-view-pane="current"] .comparison-bars');
          return chart ? [...chart.querySelectorAll(':scope > .bar-row')].map(row=>[
            row.querySelector(':scope > strong')?.textContent||'',
            row.querySelector('.comparison-dot')?.style.left||'',
            row.getAttribute('aria-label')||''
          ].join('~')).join('|') : '';
        }""")
        if after and after!=before["signature"]:
            changed=True
            break
    if not changed:
        fail.append({"key":key,"kind":"selector-does-not-update-current-graph","metric":metric})

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
    if s["selected"] and not any(TOWN_NAME in x for x in s["selected"]):
        fail.append({"key":key,"kind":"selected-row","town":TOWN_NAME,"rows":s["selected"]})
    hero=s.get("hero") or {}
    hero_meta=TOWN_META[TOWN]
    if hero_meta["heroBg"] not in hero.get("background","") or hero_meta["heroCredit"] not in hero.get("credit",""):
        fail.append({"key":key,"kind":"municipal-hero","town":TOWN,"hero":hero})
    title=s.get("primaryTitle")
    if theme!="demografia" and (not title or not title.get("visible") or not title.get("text")):
        fail.append({"key":key,"kind":"missing-primary-title","title":title})
    selector=s.get("compositeSelector")
    if theme!="demografia" and selector:
        if selector.get("background")!=selector.get("expectedSoft") or selector.get("border")!=selector.get("expectedLine") or selector.get("selectBorder")!=selector.get("expectedAccent"):
            fail.append({"key":key,"kind":"composite-selector-theme-color","selector":selector})
        if selector.get("rightGap") is not None and abs(selector["rightGap"])>2:
            fail.append({"key":key,"kind":"composite-selector-right-align","selector":selector})
        if not key.startswith("mobile:") and selector.get("labelCenterDelta") is not None and selector["labelCenterDelta"]>2:
            fail.append({"key":key,"kind":"selector-label-misaligned","selector":selector})
        if key.startswith("mobile:") and (selector.get("height",0)>90 or selector.get("selectHeight",0)>42):
            fail.append({"key":key,"kind":"selector-mobile-oversize","selector":selector})
    pill=s.get("demographyPill") or {}
    expected_bg="rgb(184, 75, 52)" if theme=="demografia" else "rgb(251, 233, 227)"
    if pill.get("background")!=expected_bg:
        fail.append({"key":key,"kind":"demography-pill-color","theme":theme,"pill":pill,"expectedBackground":expected_bg})
    semantic=s.get("semantic") or {}
    if theme=="economia" and metric!="incomeDistribution" and semantic.get("incomeText"):
        fail.append({"key":key,"kind":"income-context-leak"})
    if theme=="economia" and semantic.get("economyDeepDive"):
        fail.append({"key":key,"kind":"economy-deep-dive-leak"})
    if theme=="sicurezza" and semantic.get("crimeContext"):
        fail.append({"key":key,"kind":"crime-context-leak"})
    if semantic.get("selectorDrivenDuplicate"):
        fail.append({"key":key,"kind":"selector-driven-redundant-detail"})
    if semantic.get("demographicHistoryDuplicate"):
        fail.append({"key":key,"kind":"duplicate-demographic-history"})
    pnrr_expected=theme=="comunita" and metric in {"pnrrFunding","pnrrConcluded"}
    if bool(semantic.get("communityPnrrDeepDive")) != pnrr_expected:
        fail.append({"key":key,"kind":"pnrr-detail-scope","expected":pnrr_expected,"actual":semantic.get("communityPnrrDeepDive")})
    if metric in {"libraryLoansPerResident","libraryActiveBorrowersPer100","libraryWeeklyOpeningHours"} and semantic.get("legacyLibraryCurrent"):
        fail.append({"key":key,"kind":"library-current-not-lollipop"})
    economic_scope_metrics={"businessTurnover","businessValueAdded","labourProductivity","turnoverPerPersonEmployed","valueAddedTurnoverShare","averageGrossRemunerationPerEmployee","labourCost","grossOperatingMargin"}
    scope=semantic.get("economicScope") or {}
    if metric in economic_scope_metrics and (not scope.get("inPrimary") or scope.get("inChart")):
        fail.append({"key":key,"kind":"economic-scope-placement","scope":scope})
    if metric in economic_scope_metrics and not key.startswith("mobile:") and scope.get("rightGap") is not None and abs(scope["rightGap"])>2:
        fail.append({"key":key,"kind":"economic-scope-right-align","scope":scope})
    if metric in economic_scope_metrics and key.startswith("mobile:") and (
        not scope.get("selectVisible")
        or not scope.get("selectedText")
        or (scope.get("selectWidth") or 0) < 120
        or (scope.get("selectHeight") or 0) < 30
    ):
        fail.append({"key":key,"kind":"economic-scope-mobile-unusable","scope":scope})
    health_metrics={
      "lifeExpectancy","mortalityAll","mortalityCancer","mortalityCirculatory","mortalityRespiratory",
      "hypertensionPrevalence","copdPrevalence","ischemicHeartDiseasePrevalence","heartFailurePrevalence",
      "priorStrokePrevalence","diabetes","dementia","emergencyAccess","elderlyHomeCare",
      "permanentRsaAssisted","specialistVisits7Psr","diagnosticImagingServices"
    }
    if metric in health_metrics and semantic.get("healthRedundantDetail"):
        fail.append({"key":key,"kind":"health-redundant-detail"})
    if metric in {"landslideExposure","floodExposure"} and semantic.get("hydroRiskDeepDive"):
        fail.append({"key":key,"kind":"hydro-risk-redundant-deep-dive"})
    inline_metrics={"landCoverProfile","landslideExposure","floodExposure","drinkingWaterQuality","remediationProceedings"}
    if metric in inline_metrics:
        inline=semantic.get("inlineDetail") or {}
        if not inline.get("visible") or not inline.get("parentChart"):
            fail.append({"key":key,"kind":"special-detail-detached","inline":inline})
    if metric=="drinkingWaterQuality":
        water=semantic.get("waterDetail") or {}
        if not water.get("exists") or not water.get("open") or not water.get("iconVisible"):
            fail.append({"key":key,"kind":"water-detail-default-state","water":water})
    if metric=="extractiveProduction":
        special=semantic.get("specialView") or {}
        if not all(special.get(name) for name in ("toolbar","current","history","historyDisabled")):
            fail.append({"key":key,"kind":"extractive-view-switch","special":special})
    if metric=="financialDebtProfile" and semantic.get("financialDetachedHistory"):
        fail.append({"key":key,"kind":"financial-detached-history"})
    if metric=="financialDebtProfile":
        financial=semantic.get("financialShell") or {}
        if not all(financial.get(name) for name in ("shell","current","historyButton","historyChart")):
            fail.append({"key":key,"kind":"financial-standard-shell","financial":financial})
    placement=s.get("additionalInfoPlacement") or {}
    if theme in {"mobilita","abitare","ambiente","comunita"}:
        if placement.get("stray"):
            fail.append({"key":key,"kind":"additional-info-after-benchmark-tools","placement":placement})
        chart_index=placement.get("chartIndex")
        benchmark_index=placement.get("benchmarkIndex")
        tools_index=placement.get("toolsIndex")
        if isinstance(benchmark_index,int) and benchmark_index>=0 and isinstance(chart_index,int) and benchmark_index<=chart_index:
            fail.append({"key":key,"kind":"benchmark-before-chart","placement":placement})
        if isinstance(tools_index,int) and tools_index>=0:
            anchor=benchmark_index if isinstance(benchmark_index,int) and benchmark_index>=0 else chart_index
            if isinstance(anchor,int) and tools_index<=anchor:
                fail.append({"key":key,"kind":"method-before-benchmark-or-chart","placement":placement})
    v4_additional_info_metrics={
      "outsideMunicipality","inboundCommuters","commuterBalance","selfContainment",
      "commuterBalanceRate","outboundCommutersRate","inboundCommutersRate",
      "scheduledTplTripsPer1000","activeTplAccessPoints","tplServiceSpan",
      "omiResidential","erpArrears",
      "altitudeProfile","forestCoverIndex",
      "bathingWaterQuality","bathingNonCompliantSamples","blueFlagBeaches","shorelineDynamics",
      "rigidDefenceProtectedCoast","maritimeConcessions","maritimeConcessionFeesDue",
      "extractiveSites","extractiveProduction","extractivePlanning",
      "pnrrFunding","pnrrConcluded"
    }
    if metric in v4_additional_info_metrics and (placement.get("inlineCount") or 0)<1:
        fail.append({"key":key,"kind":"v4-additional-info-not-inline","placement":placement})
    for extra in s.get("extras") or []:
        if extra["width"] < extra["topicWidth"]*0.90 or abs(extra["left"]-extra["topicLeft"])>10:
            fail.append({"key":key,"kind":"misplaced-renderer-block","extra":extra})
    viz=s.get("currentViz")
    if viz and viz.get("rows"):
        rendered_units={row.get("unit","") for row in viz["rows"] if row.get("unit","")}
        if len(rendered_units)>1:
            fail.append({"key":key,"kind":"mixed-rendered-units","units":sorted(rendered_units)})
        numeric=[]
        for row in viz["rows"]:
            value=row.get("displayValue")
            left=row.get("left")
            if isinstance(value,(int,float)) and isinstance(left,(int,float)):
                numeric.append((float(value),float(left)))
        numeric.sort()
        if any(numeric[i][1] > numeric[i+1][1] + 0.3 for i in range(len(numeric)-1)):
            fail.append({"key":key,"kind":"visible-value-position-mismatch","pairs":numeric,"viz":viz})
        visible_units={row.get("displayUnit","") for row in viz["rows"] if row.get("displayUnit","")}
        axis_visible=viz.get("axisVisibleUnit","")
        if len(visible_units)>1:
            fail.append({"key":key,"kind":"mixed-visible-units","units":sorted(visible_units),"viz":viz})
        elif visible_units and axis_visible and next(iter(visible_units))!=axis_visible:
            fail.append({"key":key,"kind":"visible-axis-unit-mismatch","rowUnit":next(iter(visible_units)),"axisUnit":axis_visible,"viz":viz})
        suffix={"currency":"€","percent":"%","years":"anni","eurPerResident":"€/ab.","eurm2":"€/m²","rentm2":"€/m²"}.get(viz.get("unit"))
        if viz.get("contract")=="rendered" and suffix and suffix not in viz.get("axis",""):
            fail.append({"key":key,"kind":"axis-unit-mismatch","unit":viz.get("unit"),"axis":viz.get("axis")})
    if metric=="incomeDistribution":
        viz=s.get("currentViz") or {}
        if viz.get("contract")!="rendered" or viz.get("unit")!="currency" or "€" not in viz.get("axis","") or "%" in viz.get("axis",""):
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
        review_metrics={"ageDistribution","incomeDistribution","roadSafety","slowMobilityTrekking","bathingWaterQuality","lifeExpectancy","landCoverProfile","landslideExposure","floodExposure","climateTemperatureTrend50y","climatePrecipitationTrend50y","climateTminTrend","climateTmaxTrend","outsideMunicipality","scheduledTplTripsPer1000","omiResidential","erpArrears","altitudeProfile","forestCoverIndex","bathingWaterQuality","extractiveProduction","pnrrFunding","drinkingWaterQuality","remediationProceedings","extractiveProduction","financialDebtProfile"}
        for vp,w,h in VIEWPORTS:
            page=browser.new_page(viewport={"width":w,"height":h});errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
            for theme,metrics in contract.items():
                go(page,args.base,theme,metrics[0])
                page.locator("#town-topic").screenshot(path=str(folder/f"review-{vp}-{theme}.png"),animations="disabled")
                if theme==first_theme:
                    page.locator(".town-hero").screenshot(path=str(folder/f"hero-{vp}.png"),animations="disabled")
                for metric in metrics:
                    choose(page,metric)
                    key=f"{vp}:{theme}:{metric}"
                    validate(state(page),theme,metric,key,fail)
                    selector_graph_response(page,metric,key,fail)
                    climate_layout_response(page,metric,key,fail)
                    if metric in review_metrics:
                        page.locator("#town-topic").screenshot(path=str(folder/f"review-{vp}-{theme}-{metric}.png"),animations="disabled")
            if errors: fail.append({"key":vp,"kind":"page-errors","errors":errors})
            page.close()
        browser.close()
    report={"town":TOWN,"themes":list(contract),"themeMetricCounts":{k:len(v) for k,v in contract.items()},"metricStatesPerViewport":total,"uniqueMetricCount":unique,"failureCount":len(fail),"failures":fail}
    (folder/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (folder/"summary.txt").write_text(f"A5 municipal rollout · {TOWN_NAME}\nthemes={len(contract)}\nmetric_states_per_viewport={total}\nunique_metrics={unique}\nfailures={len(fail)}\n",encoding="utf-8")
    if fail: raise SystemExit(f"A5 municipal rollout {TOWN_NAME} FAILED: {len(fail)} problemi\n"+json.dumps(fail[:12],ensure_ascii=False,indent=2))
    print(f"A5 municipal rollout {TOWN_NAME} OK: {len(contract)} temi, {total} stati/viewport, {unique} indicatori unici.")

if __name__=="__main__": main()
