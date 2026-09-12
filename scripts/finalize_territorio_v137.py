#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'scripts' / 'patch_territorio_v137_runtime.py'
MATERIALIZER = ROOT / 'scripts' / 'materialize_territorio_v137.py'
VERIFY = ROOT / 'scripts' / 'verify_territorio_v137_dist.py'


def once(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f'{label}: attese {expected} occorrenze, trovate {count}')
    return text.replace(old, new)


def finalize_runtime() -> None:
    source = RUNTIME.read_text(encoding='utf-8')

    source = once(
        source,
        r"    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:'value' };\n",
        r"    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:metric.meta.compositeType === 'protectedAreasProfile' ? 'percent' : 'value' };\n",
        'default protected scale',
    )
    source = once(
        source,
        r"    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,part}; }\n",
        r"    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),part}; }\n",
        'protected selection scale',
    )
    source = once(
        source,
        r"    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\n",
        r"    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\n",
        'protected aggregate scale',
    )
    source = once(
        source,
        r'''    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; return `<div class=\"compare-view-controls territory-profile-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\"${html(part.key)}\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`; }\n''',
        r'''    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; const unitControls=metric.meta.compositeType === 'protectedAreasProfile' ? `<div><span class=\"compare-view-label\">Unità</span><div class=\"scale-switch compact\" role=\"group\" aria-label=\"Unità aree protette\"><button type=\"button\" data-composite-scale=\"percent\" class=\"${scale==='percent'?'active':''}\">%</button><button type=\"button\" data-composite-scale=\"hectares\" class=\"${scale==='hectares'?'active':''}\">ha</button></div></div>` : ''; return `<div class=\"compare-view-controls territory-profile-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\"${html(part.key)}\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label>${unitControls}</div>`; }\n''',
        'protected unit controls',
    )
    source = once(
        source,
        r"<small>${html(metric.meta.year)}</small></article>",
        r"<small>${html(metric.meta.compositeType==='protectedAreasProfile'&&part.ha!==undefined?formatValue(part.ha,'hectares'):metric.meta.year)}</small></article>",
        'protected town hectare detail',
    )
    source = once(
        source,
        r'''    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return `<div class=\"indicator-composite-table territory-indicator-comparison\"><div class=\"compare-chart-toolbar\">${compositeCompareControls(metric,choice,'value')}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(choice)}\">${compositeCompareBarRows(data,metricKey,choice,'value')}</div></div>`; }\n''',
        r'''    if (isTerritoryProfileType(metric)) { const view=arguments[4] || {choice:financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice,scale:metric.meta.compositeType==='protectedAreasProfile'?'percent':'value'}; return `<div class=\"indicator-composite-table territory-indicator-comparison\"><div class=\"compare-chart-toolbar\">${compositeCompareControls(metric,view.choice,view.scale)}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(view.choice)}\" data-composite-scale=\"${html(view.scale)}\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`; }\n''',
        'indicator protected view',
    )
    source = once(
        source,
        "  function territoryProfileIndicatorAsideMarkup(metric,choice) {\n    const selected=compositeCompareAggregate(metric,choice,'value');",
        "  function territoryProfileIndicatorAsideMarkup(metric,choice,scale='value') {\n    const selected=compositeCompareAggregate(metric,choice,scale);",
        'indicator aside scale',
    )
    source = once(
        source,
        r"    const initialTerritoryChoice = territoryProfile ? (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key) : null;\n",
        r"    const initialTerritoryView = territoryProfile ? compositeCompareDefaults(metric) : null;\n    const initialTerritoryChoice = initialTerritoryView?.choice || null;\n",
        'indicator default view',
    )
    source = once(
        source,
        'indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)',
        'indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView, initialTerritoryView)',
        'indicator layout scale',
    )
    source = once(
        source,
        'territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice)',
        "territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice,initialTerritoryView?.scale || 'value')",
        'indicator aggregate scale',
    )

    old_events = """        events = \"\"\"    if (territoryProfile) {
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
    new_events = """        events = \"\"\"    if (territoryProfile) {
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
    source = once(source, old_events, new_events, 'indicator protected interactions')
    RUNTIME.write_text(source, encoding='utf-8')


def finalize_materializer() -> None:
    source = MATERIALIZER.read_text(encoding='utf-8')
    source = once(source, 'Totale protetto (unione)', 'Totale tutele considerate (unione)', 'total label', 2)
    source = once(
        source,
        "Superficie ricadente nelle aree protette e nei siti Natura 2000 della Regione Toscana. Il totale e' l'unione geometrica delle tutele e non la somma delle categorie sovrapposte.",
        "Superficie interessata dalle tutele naturalistiche considerate nei layer ufficiali regionali. Il totale e' l'unione geometrica delle tutele considerate e non la somma delle categorie sovrapposte.",
        'description',
    )
    source = once(
        source,
        '"compositeType": "protectedAreasProfile", "defaultView": "total",',
        '"compositeType": "protectedAreasProfile", "defaultView": "total", "selectorLabel": "Tutela",',
        'selector',
    )
    source = once(
        source,
        '"label": "Versilia · territorio protetto", "note": "Totale su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."',
        '"label": "Versilia · tutele considerate", "note": "Totale delle tutele considerate su geometrie dissolte: le sovrapposizioni tra categorie sono conteggiate una sola volta."',
        'aggregate',
    )
    source = once(
        source,
        '"formula": "Totale = area(unione geometrica delle tutele ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."',
        '"formula": "Totale considerato = area(unione geometrica delle tutele considerate ∩ Comune). Quota = totale / superficie comunale × 100.", "caveat": "Le categorie possono sovrapporsi e non vanno sommate. Le ANPIL sono mostrate separatamente come livello storico/transitorio: dopo la L.R. Toscana 30/2015 non vanno equiparate automaticamente al sistema regionale vigente delle aree protette, in attesa delle verifiche e riclassificazioni previste. I riferimenti temporali dei layer restano distinti e sono documentati nello snapshot."',
        'legal caveat',
    )
    MATERIALIZER.write_text(source, encoding='utf-8')


def write_verifier() -> None:
    VERIFY.write_text('''#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("dist/data/site-data.json")
if not p.exists():
    raise SystemExit("dist/data/site-data.json mancante")
d = json.loads(p.read_text(encoding="utf-8"))
metrics = d.get("metrics", {})
if len(metrics) != 203:
    raise SystemExit(f"catalogo finale {len(metrics)}, attesi 203")
expected = {"landUse", "landUseChange", "protectedNaturalAreas", "managedReticulumLength", "roadNetworkProfile"}
if not expected.issubset(metrics):
    raise SystemExit(f"metriche v1.37 mancanti: {sorted(expected - set(metrics))}")
towns = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
for key in expected:
    rows = metrics[key].get("rows", [])
    if [r.get("town") for r in rows] != towns:
        raise SystemExit(f"{key}: copertura/ordine non 7/7")
if d.get("version") != "v1.37.0":
    raise SystemExit(f"versione finale inattesa: {d.get('version')}")
road = metrics["roadNetworkProfile"]
if abs(float(road["aggregate"]["value"]) - 2029.655081) > 1e-6:
    raise SystemExit("roadNetworkProfile: aggregato km inatteso")
hydro = metrics["managedReticulumLength"]
hydro_parts = {x["key"]: x for x in hydro["aggregate"]["parts"]}
if abs(float(hydro_parts["managed"]["value"]) - 745.041751) > 1e-6:
    raise SystemExit("reticolo gestito: regressione aggregato")
land = metrics["landUse"]
cam = next(r for r in land["rows"] if r["town"] == "Camaiore")
if cam["seriesByView"]["sqmPerResident"]["years"] != [2019, 2020, 2021, 2022, 2023, 2024]:
    raise SystemExit("landUse: anni pro capite inattesi")
for row in land["rows"]:
    parts = {p["key"]: p for p in row["parts"]}
    if parts["hectares"].get("unit") != "hectares":
        raise SystemExit(f"landUse: unità ettari non canonica per {row['town']}")
change = metrics["landUseChange"]
for row in change["rows"]:
    if any(p.get("unit") != "hectares" for p in row["parts"]):
        raise SystemExit(f"landUseChange: unità ettari non canonica per {row['town']}")
protected = metrics["protectedNaturalAreas"]
if protected["meta"].get("selectorLabel") != "Tutela":
    raise SystemExit("aree protette: selectorLabel mancante")
if "ANPIL" not in protected.get("method", {}).get("caveat", ""):
    raise SystemExit("aree protette: caveat ANPIL mancante")
for row in protected["rows"]:
    if not row.get("municipalAreaHa", 0) > 0:
        raise SystemExit(f"aree protette: area comunale non valida per {row['town']}")
    for part in row.get("parts", []):
        if part.get("unit") != "percent" or part.get("ha") is None or float(part["ha"]) < 0:
            raise SystemExit(f"aree protette: doppia unità incompleta per {row['town']}/{part.get('key')}")
    total = next(p for p in row["parts"] if p["key"] == "total")
    if float(total["ha"]) > float(row["municipalAreaHa"]) + 1e-5:
        raise SystemExit(f"aree protette: unione > area comunale per {row['town']}")
print("canonical-dist-metrics", len(metrics))
print("road-versilia-km", road["aggregate"]["value"])
print("reticulum-managed-versilia-km", hydro_parts["managed"]["value"])
print("protected-dual-unit", "ok")
''', encoding='utf-8')


if __name__ == '__main__':
    finalize_runtime()
    finalize_materializer()
    write_verifier()
    print('Finalizzazione v1.37 applicata sul sorgente runtime corrente.')
