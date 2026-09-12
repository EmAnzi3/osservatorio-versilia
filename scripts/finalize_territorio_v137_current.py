#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'scripts'/'patch_territorio_v137_runtime.py'
M=ROOT/'scripts'/'materialize_territorio_v137.py'
V=ROOT/'scripts'/'verify_territorio_v137_dist.py'

def r(text,old,new,label,count=1):
    n=text.count(old)
    if n!=count: raise RuntimeError(f'{label}: attese {count}, trovate {n}')
    return text.replace(old,new)

def runtime():
    s=R.read_text(encoding='utf-8')
    s=r(s,"scale:'value' };\\n\", \"default territorio\"","scale:metric.meta.compositeType === 'protectedAreasProfile' ? 'percent' : 'value' };\\n\", \"default territorio\"",'default scale')
    s=r(s,"const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,part}; }\\n\", \"selezione territorio\"","const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),part}; }\\n\", \"selezione territorio\"",'selection scale')
    s=r(s,"const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\\n\", \"aggregato territorio\"","const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\\n\", \"aggregato territorio\"",'aggregate scale')
    old="const parts=metric.rows?.[0]?.parts || []; return `<div class=\\\"compare-view-controls territory-profile-controls\\\"><label class=\\\"compare-choice-select\\\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\\\"${html(part.key)}\\\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`; }\\n\", \"controlli territorio\""
    new="const parts=metric.rows?.[0]?.parts || []; const unitControls=metric.meta.compositeType === 'protectedAreasProfile' ? `<div><span class=\\\"compare-view-label\\\">Unità</span><div class=\\\"scale-switch compact\\\" role=\\\"group\\\" aria-label=\\\"Unità aree protette\\\"><button type=\\\"button\\\" data-composite-scale=\\\"percent\\\" class=\\\"${scale==='percent'?'active':''}\\\">%</button><button type=\\\"button\\\" data-composite-scale=\\\"hectares\\\" class=\\\"${scale==='hectares'?'active':''}\\\">ha</button></div></div>` : ''; return `<div class=\\\"compare-view-controls territory-profile-controls\\\"><label class=\\\"compare-choice-select\\\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\\\"${html(part.key)}\\\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label>${unitControls}</div>`; }\\n\", \"controlli territorio\""
    s=r(s,old,new,'unit controls')
    s=r(s,"<small>${html(metric.meta.year)}</small></article>","<small>${html(metric.meta.compositeType==='protectedAreasProfile'&&part.ha!==undefined?formatValue(part.ha,'hectares'):metric.meta.year)}</small></article>",'town ha detail')
    old="const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return `<div class=\\\"indicator-composite-table territory-indicator-comparison\\\"><div class=\\\"compare-chart-toolbar\\\">${compositeCompareControls(metric,choice,'value')}</div><div class=\\\"comparison-bars\\\" data-composite-choice=\\\"${html(choice)}\\\">${compositeCompareBarRows(data,metricKey,choice,'value')}</div></div>`; }\\n\""
    new="const view=arguments[4] || {choice:financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice,scale:metric.meta.compositeType==='protectedAreasProfile'?'percent':'value'}; return `<div class=\\\"indicator-composite-table territory-indicator-comparison\\\"><div class=\\\"compare-chart-toolbar\\\">${compositeCompareControls(metric,view.choice,view.scale)}</div><div class=\\\"comparison-bars\\\" data-composite-choice=\\\"${html(view.choice)}\\\" data-composite-scale=\\\"${html(view.scale)}\\\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`; }\\n\""
    s=r(s,old,new,'indicator view')
    s=r(s,"function territoryProfileIndicatorAsideMarkup(metric,choice) {\n    const selected=compositeCompareAggregate(metric,choice,'value');","function territoryProfileIndicatorAsideMarkup(metric,choice,scale='value') {\n    const selected=compositeCompareAggregate(metric,choice,scale);",'aside scale')
    s=r(s,"const initialTerritoryChoice = territoryProfile ? (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key) : null;\\n\", \"default scheda territorio\"","const initialTerritoryView = territoryProfile ? compositeCompareDefaults(metric) : null;\\n    const initialTerritoryChoice = initialTerritoryView?.choice || null;\\n\", \"default scheda territorio\"",'initial view')
    s=r(s,"indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)\", 1)","indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView, initialTerritoryView)\", 1)",'layout comparison')
    s=r(s,"territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : hydroRisk","territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice,initialTerritoryView?.scale || 'value') : hydroRisk",'layout aside')
    old="""        events = \"\"\"    if (territoryProfile) {
      const currentSection=document.querySelector('.indicator-current');
      const applyTerritoryChoice=choice=>{
        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');
        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');
        const historyHost=document.querySelector('[data-financial-indicator-history]');
        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,choice,initialHydroView);
        if(aggregateHost) aggregateHost.innerHTML=territoryProfileIndicatorAsideMarkup(metric,choice);
        if(historyHost) historyHost.innerHTML=territoryProfileHistoryTable(metric,choice);
      };
      currentSection?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-composite-component]');
        if(select&&currentSection.contains(select)) applyTerritoryChoice(select.value);
      });
    }
\"\"\""""
    new="""        events = \"\"\"    if (territoryProfile) {
      const currentSection=document.querySelector('.indicator-current');
      let territoryView={...initialTerritoryView};
      const renderTerritory=()=>{
        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');
        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');
        const historyHost=document.querySelector('[data-financial-indicator-history]');
        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,territoryView.choice,initialHydroView,territoryView);
        if(aggregateHost) aggregateHost.innerHTML=territoryProfileIndicatorAsideMarkup(metric,territoryView.choice,territoryView.scale);
        if(historyHost) historyHost.innerHTML=territoryProfileHistoryTable(metric,territoryView.choice);
      };
      currentSection?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-composite-component]');
        if(select&&currentSection.contains(select)){ territoryView={...territoryView,choice:select.value}; renderTerritory(); }
      });
      currentSection?.addEventListener('click',event=>{
        const button=event.target.closest('button[data-composite-scale]');
        if(button&&currentSection.contains(button)){ territoryView={...territoryView,scale:button.dataset.compositeScale}; renderTerritory(); }
      });
    }
\"\"\""""
    s=r(s,old,new,'interactions')
    R.write_text(s,encoding='utf-8')

def materializer():
    s=M.read_text(encoding='utf-8')
    s=r(s,'Totale protetto (unione)','Totale tutele considerate (unione)','total label',2)
    s=r(s,"Superficie ricadente nelle aree protette e nei siti Natura 2000 della Regione Toscana. Il totale e' l'unione geometrica delle tutele e non la somma delle categorie sovrapposte.","Superficie interessata dalle tutele naturalistiche considerate nei layer ufficiali regionali. Il totale e' l'unione geometrica delle tutele considerate e non la somma delle categorie sovrapposte.",'description')
    s=r(s,'"compositeType": "protectedAreasProfile", "defaultView": "total",','"compositeType": "protectedAreasProfile", "defaultView": "total", "selectorLabel": "Tutela",','selector')
    s=r(s,'"label": "Versilia · territorio protetto", "note": "Totale su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."','"label": "Versilia · tutele considerate", "note": "Totale delle tutele considerate su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."','aggregate')
    s=r(s,'"formula": "Totale = area(unione geometrica delle tutele ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."','"formula": "Totale considerato = area(unione geometrica delle tutele considerate ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. Le ANPIL sono mostrate separatamente come livello storico/transitorio: dopo la L.R. Toscana 30/2015 non vanno equiparate automaticamente al sistema regionale vigente delle aree protette, in attesa delle verifiche e riclassificazioni previste. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."','legal caveat')
    M.write_text(s,encoding='utf-8')

def verifier():
    V.write_text('''#!/usr/bin/env python3
import json,math
from pathlib import Path
p=Path("dist/data/site-data.json")
if not p.exists(): raise SystemExit("dist/data/site-data.json mancante")
d=json.loads(p.read_text(encoding="utf-8")); m=d.get("metrics",{})
if len(m)!=203: raise SystemExit(f"catalogo finale {len(m)}, attesi 203")
keys={"landUse","landUseChange","protectedNaturalAreas","managedReticulumLength","roadNetworkProfile"}; towns=["Camaiore","Forte dei Marmi","Massarosa","Pietrasanta","Seravezza","Stazzema","Viareggio"]
if not keys.issubset(m): raise SystemExit("metriche v1.37 mancanti")
for k in keys:
    if [x.get("town") for x in m[k].get("rows",[])]!=towns: raise SystemExit(f"{k}: copertura non 7/7")
if d.get("version")!="v1.37.0": raise SystemExit("versione finale inattesa")
def close(a,e,l,t=1e-6):
    if not math.isfinite(float(a)) or abs(float(a)-e)>t: raise SystemExit(f"{l}: {a} atteso {e}")
road=m["roadNetworkProfile"]; close(road["aggregate"]["value"],2029.655081,"road km"); close(next(x for x in road["aggregate"]["parts"] if x["key"]=="density")["value"],5.689283,"road density")
h=m["managedReticulumLength"]; hp={x["key"]:x for x in h["aggregate"]["parts"]}; close(hp["full"]["value"],1200.261175,"hydro full"); close(hp["managed"]["value"],745.041751,"hydro managed")
land=m["landUse"]; lp={x["key"]:x for x in land["aggregate"]["parts"]}; close(lp["percent"]["value"],15.601285,"land %",1e-5); close(lp["hectares"]["value"],5562.1,"land ha");
if lp["hectares"]["unit"]!="hectares": raise SystemExit("landUse unit hectares mancante")
cam=next(x for x in land["rows"] if x["town"]=="Camaiore")
if cam["seriesByView"]["sqmPerResident"]["years"]!=[2019,2020,2021,2022,2023,2024]: raise SystemExit("anni pro capite inattesi")
change=m["landUseChange"]; close(change["aggregate"]["value"],2.24,"land change")
if any(x["unit"]!="hectares" for x in change["aggregate"]["parts"]): raise SystemExit("landUseChange unit non canonica")
prot=m["protectedNaturalAreas"]
if prot["meta"].get("selectorLabel")!="Tutela": raise SystemExit("protected selector mancante")
for src in [*prot["rows"],prot["aggregate"]]:
    for part in src.get("parts",[]):
        if part.get("unit")!="percent" or part.get("ha") is None or float(part["ha"])<0: raise SystemExit("protected payload non valido")
close(prot["aggregate"]["value"],48.045890,"protected %",1e-5); close(prot["aggregate"]["parts"][0]["ha"],17140.399808,"protected ha")
for k in keys:
    for row in m[k]["rows"]:
        for part in row.get("parts",[]):
            if part.get("unit")=="ha": raise SystemExit(f"{k}: unità legacy ha")
print("canonical-dist-metrics",len(m)); print("road-versilia-km",road["aggregate"]["value"]); print("protected-versilia-ha",prot["aggregate"]["parts"][0]["ha"])
''',encoding='utf-8')

if __name__=='__main__':
    runtime(); materializer(); verifier(); print('Finalizzazione corrente v1.37 applicata.')
