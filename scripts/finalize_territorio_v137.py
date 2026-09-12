#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'scripts'/'patch_territorio_v137_runtime.py'
MATERIALIZER=ROOT/'scripts'/'materialize_territorio_v137.py'
VERIFY=ROOT/'scripts'/'verify_territorio_v137_dist.py'


def once(text,old,new,label,expected=1):
    n=text.count(old)
    if n!=expected:
        raise RuntimeError(f'{label}: attese {expected} occorrenze, trovate {n}')
    return text.replace(old,new)


def finalize_runtime():
    s=RUNTIME.read_text(encoding='utf-8')
    pairs=[
      (
       "        return insert_after_line(b, \"function compositeCompareDefaults(metric)\", \"    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:'value' };\\n\", \"default territorio\")",
       "        return insert_after_line(b, \"function compositeCompareDefaults(metric)\", \"    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:metric.meta.compositeType === 'protectedAreasProfile' ? 'percent' : 'value' };\\n\", \"default territorio\")",
       'default protected scale'),
      (
       "        return insert_after_line(b, \"function compositeCompareSelection(metric, row, choice\", \"    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,part}; }\\n\", \"selezione territorio\")",
       "        return insert_after_line(b, \"function compositeCompareSelection(metric, row, choice\", \"    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),part}; }\\n\", \"selezione territorio\")",
       'protected selection scale'),
      (
       "        return insert_after_line(b, \"function compositeCompareAggregate(metric, choice\", \"    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\\n\", \"aggregato territorio\")",
       "        return insert_after_line(b, \"function compositeCompareAggregate(metric, choice\", \"    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\\n\", \"aggregato territorio\")",
       'protected aggregate scale'),
      (
       "        return insert_after_line(b, \"function compositeCompareControls(metric, choice\", \"    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; return `<div class=\\\"compare-view-controls territory-profile-controls\\\"><label class=\\\"compare-choice-select\\\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\\\"${html(part.key)}\\\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`; }\\n\", \"controlli territorio\")",
       "        return insert_after_line(b, \"function compositeCompareControls(metric, choice\", \"    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; const unitControls=metric.meta.compositeType === 'protectedAreasProfile' ? `<div><span class=\\\"compare-view-label\\\">Unità</span><div class=\\\"scale-switch compact\\\" role=\\\"group\\\" aria-label=\\\"Unità aree protette\\\"><button type=\\\"button\\\" data-composite-scale=\\\"percent\\\" class=\\\"${scale==='percent'?'active':''}\\\">%</button><button type=\\\"button\\\" data-composite-scale=\\\"hectares\\\" class=\\\"${scale==='hectares'?'active':''}\\\">ha</button></div></div>` : ''; return `<div class=\\\"compare-view-controls territory-profile-controls\\\"><label class=\\\"compare-choice-select\\\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\\\"${html(part.key)}\\\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label>${unitControls}</div>`; }\\n\", \"controlli territorio\")",
       'protected unit controls'),
      (
       "            \"      return `<div class=\\\"composite-town-mobility territory-profile-town\\\">${parts.map(part=>`<article class=\\\"${part.key===(metric.meta.defaultView||parts[0]?.key)?'balance':''}\\\"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>${histories}`;\\n\"",
       "            \"      return `<div class=\\\"composite-town-mobility territory-profile-town\\\">${parts.map(part=>`<article class=\\\"${part.key===(metric.meta.defaultView||parts[0]?.key)?'balance':''}\\\"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.compositeType==='protectedAreasProfile'&&part.ha!==undefined?formatValue(part.ha,'hectares'):metric.meta.year)}</small></article>`).join('')}</div>${histories}`;\\n\"",
       'protected town hectare detail'),
      (
       "        addition = \"    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return `<div class=\\\"indicator-composite-table territory-indicator-comparison\\\"><div class=\\\"compare-chart-toolbar\\\">${compositeCompareControls(metric,choice,'value')}</div><div class=\\\"comparison-bars\\\" data-composite-choice=\\\"${html(choice)}\\\">${compositeCompareBarRows(data,metricKey,choice,'value')}</div></div>`; }\\n\"",
       "        addition = \"    if (isTerritoryProfileType(metric)) { const view=arguments[4] || {choice:financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice,scale:metric.meta.compositeType==='protectedAreasProfile'?'percent':'value'}; return `<div class=\\\"indicator-composite-table territory-indicator-comparison\\\"><div class=\\\"compare-chart-toolbar\\\">${compositeCompareControls(metric,view.choice,view.scale)}</div><div class=\\\"comparison-bars\\\" data-composite-choice=\\\"${html(view.choice)}\\\" data-composite-scale=\\\"${html(view.scale)}\\\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`; }\\n\"",
       'indicator protected view'),
      (
       "  function territoryProfileIndicatorAsideMarkup(metric,choice) {\n    const selected=compositeCompareAggregate(metric,choice,'value');",
       "  function territoryProfileIndicatorAsideMarkup(metric,choice,scale='value') {\n    const selected=compositeCompareAggregate(metric,choice,scale);",
       'indicator aside scale'),
      (
       "        b = insert_after_line(b, \"const initialHydroAggregate =\", \"    const initialTerritoryChoice = territoryProfile ? (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key) : null;\\n\", \"default scheda territorio\")",
       "        b = insert_after_line(b, \"const initialHydroAggregate =\", \"    const initialTerritoryView = territoryProfile ? compositeCompareDefaults(metric) : null;\\n    const initialTerritoryChoice = initialTerritoryView?.choice || null;\\n\", \"default scheda territorio\")",
       'indicator default view'),
      (
       "            line = line.replace(\"indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)\", \"indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)\", 1)\n            line = line.replace(\": hydroRisk ? `<span>${html(initialHydroAggregate.label)}\", \": territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : hydroRisk ? `<span>${html(initialHydroAggregate.label)}\", 1)",
       "            line = line.replace(\"indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)\", \"indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView, initialTerritoryView)\", 1)\n            line = line.replace(\": hydroRisk ? `<span>${html(initialHydroAggregate.label)}\", \": territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice,initialTerritoryView?.scale || 'value') : hydroRisk ? `<span>${html(initialHydroAggregate.label)}\", 1)",
       'indicator layout scale'),
    ]
    for old,new,label in pairs:
        s=once(s,old,new,label)

    old_event="""        events = \"\"\"    if (territoryProfile) {
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
    new_event="""        events = \"\"\"    if (territoryProfile) {
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
    s=once(s,old_event,new_event,'indicator protected interactions')
    RUNTIME.write_text(s,encoding='utf-8')


def finalize_materializer():
    s=MATERIALIZER.read_text(encoding='utf-8')
    s=once(s,'Totale protetto (unione)','Totale tutele considerate (unione)','total label',2)
    s=once(s,"Superficie ricadente nelle aree protette e nei siti Natura 2000 della Regione Toscana. Il totale e' l'unione geometrica delle tutele e non la somma delle categorie sovrapposte.","Superficie interessata dalle tutele naturalistiche considerate nei layer ufficiali regionali. Il totale e' l'unione geometrica delle tutele considerate e non la somma delle categorie sovrapposte.",'description')
    s=once(s,'"compositeType": "protectedAreasProfile", "defaultView": "total",','"compositeType": "protectedAreasProfile", "defaultView": "total", "selectorLabel": "Tutela",','selector')
    s=once(s,'"label": "Versilia · territorio protetto", "note": "Totale su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."','"label": "Versilia · tutele considerate", "note": "Totale delle tutele considerate su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."','aggregate')
    s=once(s,'"formula": "Totale = area(unione geometrica delle tutele ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."','"formula": "Totale considerato = area(unione geometrica delle tutele considerate ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. Le ANPIL sono mostrate separatamente come livello storico/transitorio: dopo la L.R. Toscana 30/2015 non vanno equiparate automaticamente al sistema regionale vigente delle aree protette, in attesa delle verifiche e riclassificazioni previste. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."','legal caveat')
    MATERIALIZER.write_text(s,encoding='utf-8')


def write_verifier():
    VERIFY.write_text('''#!/usr/bin/env python3
import json, math
from pathlib import Path
p=Path("dist/data/site-data.json")
if not p.exists(): raise SystemExit("dist/data/site-data.json mancante")
d=json.loads(p.read_text(encoding="utf-8")); metrics=d.get("metrics",{})
if len(metrics)!=203: raise SystemExit(f"catalogo finale {len(metrics)}, attesi 203")
expected={"landUse","landUseChange","protectedNaturalAreas","managedReticulumLength","roadNetworkProfile"}
if not expected.issubset(metrics): raise SystemExit(f"metriche v1.37 mancanti: {sorted(expected-set(metrics))}")
towns=["Camaiore","Forte dei Marmi","Massarosa","Pietrasanta","Seravezza","Stazzema","Viareggio"]
for key in expected:
    if [r.get("town") for r in metrics[key].get("rows",[])]!=towns: raise SystemExit(f"{key}: copertura/ordine non 7/7")
if d.get("version")!="v1.37.0": raise SystemExit(f"versione finale inattesa: {d.get('version')}")
def close(actual,expected,label,tol=1e-6):
    if not math.isfinite(float(actual)) or abs(float(actual)-expected)>tol: raise SystemExit(f"{label}: {actual}, atteso {expected}")
road=metrics["roadNetworkProfile"]; close(road["aggregate"]["value"],2029.655081,"road Versilia km")
close(next(x for x in road["aggregate"]["parts"] if x["key"]=="density")["value"],5.689283,"road Versilia density")
hydro=metrics["managedReticulumLength"]; hp={x["key"]:x for x in hydro["aggregate"]["parts"]}
close(hp["full"]["value"],1200.261175,"reticolo complessivo Versilia km"); close(hp["managed"]["value"],745.041751,"reticolo gestito Versilia km")
land=metrics["landUse"]; lp={x["key"]:x for x in land["aggregate"]["parts"]}
close(lp["percent"]["value"],15.601285,"suolo Versilia percent",1e-5); close(lp["hectares"]["value"],5562.1,"suolo Versilia ha")
if lp["hectares"]["unit"]!="hectares": raise SystemExit("landUse hectares: unità canonica mancante")
cam=next(r for r in land["rows"] if r["town"]=="Camaiore")
if cam["seriesByView"]["sqmPerResident"]["years"] != [2019,2020,2021,2022,2023,2024]: raise SystemExit("landUse: anni pro capite inattesi")
change=metrics["landUseChange"]
for part in change["aggregate"]["parts"]:
    if part["unit"]!="hectares": raise SystemExit("landUseChange: unità ettari non canonica")
close(change["aggregate"]["value"],2.24,"consumo suolo netto Versilia 2024")
protected=metrics["protectedNaturalAreas"]
if protected["meta"].get("selectorLabel")!="Tutela": raise SystemExit("protected: selectorLabel mancante")
for source in [*protected["rows"],protected["aggregate"]]:
    for part in source.get("parts",[]):
        if part.get("unit")!="percent": raise SystemExit("protected: percent unit inattesa")
        ha=part.get("ha")
        if ha is None or not math.isfinite(float(ha)) or float(ha)<0: raise SystemExit("protected: ettari mancanti/non validi")
close(protected["aggregate"]["value"],48.045890,"protected Versilia percent",1e-5); close(protected["aggregate"]["parts"][0]["ha"],17140.399808,"protected Versilia ha")
for key in expected:
    for row in metrics[key]["rows"]:
        for part in row.get("parts",[]):
            if part.get("unit")=="ha": raise SystemExit(f"{key}: unità legacy ha residua")
print("canonical-dist-metrics",len(metrics)); print("road-versilia-km",road["aggregate"]["value"]); print("reticulum-managed-versilia-km",hp["managed"]["value"]); print("protected-versilia-ha",protected["aggregate"]["parts"][0]["ha"])
''',encoding='utf-8')


if __name__=='__main__':
    finalize_runtime(); finalize_materializer(); write_verifier(); print('Finalizzazione v1.37 applicata.')
