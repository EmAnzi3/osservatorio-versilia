#!/usr/bin/env python3
"""Patch runtime v1.38 per i quattro indicatori INVALSI.

Si applica dopo patch_territorio_v137_runtime.py e riusa la grammatica dei
profili territoriali, sostituendo l'aggregato Versilia con i benchmark ufficiali
Toscana/Italia e preservando gli n.d. senza trasformarli in zero.
"""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP00=ROOT/'assets/app-parts/00.txt'; APP03=ROOT/'assets/app-parts/03.txt'; APP05=ROOT/'assets/app-parts/05.txt'
VISUAL=ROOT/'assets/visual-grammar.js'; UXCORE=ROOT/'assets/ux-history-core.js'; UXH=ROOT/'assets/ux-history.js'
SENTINEL='invalsiCompareDetailMarkup'


def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'v1.38 runtime: {label}: attesa 1 occorrenza, trovate {n}')
    return text.replace(old,new,1)


def all_(text,old,new,label):
    n=text.count(old)
    if n<1: raise RuntimeError(f'v1.38 runtime: {label}: nessuna occorrenza')
    return text.replace(old,new)


def block(text,name):
    start=text.find(f'  function {name}(')
    if start<0: raise RuntimeError(f'v1.38 runtime: funzione {name} non trovata')
    end=text.find('\n  function ',start+3)
    if end<0: end=len(text)
    return start,end,text[start:end]


def patch(text,name,fn):
    a,b,src=block(text,name); out=fn(src)
    if out==src: raise RuntimeError(f'v1.38 runtime: funzione {name} non modificata')
    return text[:a]+out+text[b:]


def line(text,needle,fn,label):
    rows=text.splitlines(keepends=True); hits=[i for i,r in enumerate(rows) if needle in r]
    if len(hits)!=1: raise RuntimeError(f'v1.38 runtime: {label}: attesa 1 riga, trovate {len(hits)}')
    i=hits[0]; new=fn(rows[i])
    if new==rows[i]: raise RuntimeError(f'v1.38 runtime: {label}: riga invariata')
    rows[i]=new; return ''.join(rows)


def after(text,needle,addition,label): return line(text,needle,lambda r:r+addition,label)


def main():
    a00=APP00.read_text(); a03=APP03.read_text(); a05=APP05.read_text(); vg=VISUAL.read_text(); uc=UXCORE.read_text(); uh=UXH.read_text()
    joined=a00+a03+a05+vg+uc+uh
    if SENTINEL in joined:
        for token in ('invalsiProfile','invalsi_score','nationalBenchmark','data-invalsi-national-reference'):
            if token not in joined: raise RuntimeError('v1.38 runtime: patch parziale')
        print('Renderer INVALSI v1.38 già applicato.'); return
    if 'territoryProfileTypes' not in a03: raise RuntimeError('v1.38 runtime: patch territorio v1.37 non applicata')

    # Formato WLE.
    a00=all_(a00,"      case 'index': return number1.format(v);\n","      case 'index': return number1.format(v);\n      case 'invalsi_score': return number1.format(v);\n",'formatter WLE')

    # INVALSI riusa i componenti profile v1.37.
    a03=once(a03,"const territoryProfileTypes = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']);","const territoryProfileTypes = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile','invalsiProfile']);",'profilo INVALSI')
    a03=patch(a03,'compositeCompareAggregate',lambda b:once(b,"label:`Versilia · ${part.label || metric.meta.label}`","label:metric.meta.compositeType==='invalsiProfile'?`${metric.aggregate?.label||'Toscana'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",'label Toscana compare'))
    a03=patch(a03,'compositeSelectionAggregate',lambda b:once(b,"return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};","return {label:metric.meta.compositeType==='invalsiProfile'?`${metric.aggregate?.label||'Toscana'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};",'label Toscana town'))

    helpers=r'''
  function invalsiPart(source,choice){ return (source?.parts||[]).find(p=>p.key===choice)||source?.parts?.[0]||{}; }
  function invalsiBenchmarks(metric,choice){
    if(metric?.meta?.compositeType!=='invalsiProfile') return '';
    const t=invalsiPart(metric.aggregate,choice), i=invalsiPart(metric.nationalBenchmark,choice), unit=t.unit||i.unit||metric.meta.unit;
    return `<div class="composite-town-detail invalsi-benchmark-detail"><div><span>Toscana</span><b>${html(formatValue(t.value,unit))}</b><small>benchmark regionale · ${html(t.academicYear||metric.meta.year)}</small></div><div><span>Italia</span><b>${html(formatValue(i.value,i.unit||unit))}</b><small>benchmark nazionale · ${html(i.academicYear||metric.meta.year)}</small></div></div>`;
  }
  function invalsiLevelRow(label,detail){
    const labels=detail?.labels||[], values=detail?.values||[];
    if(!labels.length||labels.length!==values.length||values.some(v=>v===null||v===undefined||!Number.isFinite(Number(v)))) return `<article class="income-band-town-detail"><h4>${html(label)}</h4><p class="aggregate-note">n.d.</p></article>`;
    return `<article class="income-band-town-detail"><h4>${html(label)}</h4>${compositeStackMarkup(labels.map((x,n)=>({label:x,value:Number(values[n])})),{ariaLabel:`Livelli di competenza · ${label}`})}</article>`;
  }
  function invalsiCompareDetailMarkup(metric,choice){
    if(metric?.meta?.compositeType!=='invalsiProfile') return '';
    const benchmark=invalsiBenchmarks(metric,choice);
    if(metric.meta.invalsiDetail!=='competence') return `<details class="detail-disclosure invalsi-benchmark-disclosure"><summary><span>Benchmark ufficiali</span><small>Toscana e Italia · stessa prova</small></summary>${benchmark}<p class="aggregate-note">Benchmark letti direttamente dallo stesso open data INVALSI; nessuna media Versilia viene ricostruita.</p></details>`;
    const towns=(metric.rows||[]).map(r=>invalsiLevelRow(r.town,r.invalsiLevelsByView?.[choice])).join('');
    const refs=invalsiLevelRow('Toscana',metric.aggregate?.invalsiLevelsByView?.[choice])+invalsiLevelRow('Italia',metric.nationalBenchmark?.invalsiLevelsByView?.[choice]);
    return `<details class="detail-disclosure invalsi-levels-detail" open><summary><span>Distribuzione nei livelli</span><small>lettura selezionata · %</small></summary>${benchmark}<div class="invalsi-level-list">${towns}${refs}</div><p class="aggregate-note">Categorie INVALSI/QCER della prova selezionata. Gli n.d. restano n.d.; nessuna stima.</p></details>`;
  }

'''
    a03=once(a03,'  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {\n',helpers+'  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {\n','helper INVALSI')
    def compare(b):
        b=once(b,'const note = isTerritoryProfileType(compositeType) ? `<p class="composite-compare-note">Scegli la lettura dal selettore. Ogni vista conserva la propria unità e il proprio metodo di aggregazione Versilia.</p>` : (','const note = compositeType===\'invalsiProfile\' ? `<p class="composite-compare-note">Scegli classe e prova. Il confronto usa Toscana e Italia; nessuna media Versilia viene calcolata.</p>` : isTerritoryProfileType(compositeType) ? `<p class="composite-compare-note">Scegli la lettura dal selettore. Ogni vista conserva la propria unità e il proprio metodo di aggregazione Versilia.</p>` : (','nota compare')
        return after(b,"if (compositeType === 'financialProfile') installChartInteractions(bars);","      if(compositeType==='invalsiProfile') bars.insertAdjacentHTML('beforeend',invalsiCompareDetailMarkup(metric,view.choice));\n",'dettaglio compare')
    a03=patch(a03,'renderCompareMetric',compare)

    # La posizione comunale deve distinguere null da zero.
    new_position=r'''  function updateTerritoryProfileTownPosition(metric,row,choice,position) {
    if(!position||!isTerritoryProfileType(metric)) return;
    const selected=compositeSelectionOptions(metric,row).find(o=>o.key===choice)||compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice), raw=selected?.value, rawRef=agg?.value;
    const local=raw===null||raw===undefined||raw===''?NaN:Number(raw), total=rawRef===null||rawRef===undefined||rawRef===''?NaN:Number(rawRef), unit=selected?.unit||metric.meta.unit;
    const overline=position.querySelector('.overline'), deltaEl=position.querySelector('[data-composite-delta]'), noteEl=position.querySelector('p'), aggLabel=position.querySelector('[data-composite-aggregate-label]'), aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(metric.meta.compositeType==='invalsiProfile'){
      const diff=Number.isFinite(local)&&Number.isFinite(total)?local-total:null, national=invalsiPart(metric.nationalBenchmark,choice);
      if(overline) overline.textContent='Scostamento dalla Toscana';
      if(deltaEl) deltaEl.innerHTML=diff===null?'n.d.<small>confronto non disponibile</small>':`${html(formatValue(diff,unit))}<small>rispetto alla Toscana</small>`;
      if(noteEl) noteEl.textContent=`Italia: ${formatValue(national.value,national.unit||unit)}. Il Comune identifica il plesso, non la residenza dello studente.`;
    } else {
      const additive=['hectares','km'].includes(unit);
      if(additive){ const share=Number.isFinite(local)&&Number.isFinite(total)&&total!==0?local/total*100:null; if(overline) overline.textContent='Quota sul totale Versilia'; if(deltaEl) deltaEl.innerHTML=share===null?'n.d.<small>quota non disponibile</small>':`${html(number1.format(share))}%<small>del totale Versilia</small>`; if(noteEl) noteEl.textContent='Quota del valore comunale sul totale dei sette Comuni per la lettura selezionata.'; }
      else { const diff=Number.isFinite(local)&&Number.isFinite(total)?local-total:null; if(overline) overline.textContent='Scostamento dal valore Versilia'; if(deltaEl) deltaEl.innerHTML=diff===null?'n.d.<small>confronto non disponibile</small>':`${html(formatValue(diff,unit))}<small>rispetto al valore Versilia</small>`; if(noteEl) noteEl.textContent='Scostamento numerico dal valore aggregato Versilia; non è un giudizio di qualità.'; }
    }
    if(aggLabel) aggLabel.textContent=agg.label; if(aggValue) aggValue.textContent=agg.formatted;
  }
'''
    x,y,_=block(a03,'updateTerritoryProfileTownPosition'); a03=a03[:x]+new_position+a03[y:]

    # Pagine indicatore: benchmark e selector storico Toscana/Italia.
    a05=patch(a05,'indicatorComparisonTable',lambda b:once(b,'${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`; }','${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${metric.meta.compositeType===\'invalsiProfile\'?invalsiCompareDetailMarkup(metric,view.choice):\'\'}</div>`; }','dettaglio indicatore'))
    a05=patch(a05,'territoryProfileHistoryChart',lambda b:once(b,"const options=[{key:'__versilia',label:'Versilia',source:metric.aggregate},...(metric.rows||[]).map(row=>({key:String(row.code||row.slug||row.town),label:row.town,source:row}))];","const options=metric.meta.compositeType==='invalsiProfile'?[{key:'__toscana',label:metric.aggregate?.label||'Toscana',source:metric.aggregate},{key:'__italia',label:metric.nationalBenchmark?.label||'Italia',source:metric.nationalBenchmark},...(metric.rows||[]).map(row=>({key:String(row.code||row.slug||row.town),label:row.town,source:row}))]:[{key:'__versilia',label:'Versilia',source:metric.aggregate},...(metric.rows||[]).map(row=>({key:String(row.code||row.slug||row.town),label:row.town,source:row}))];",'selector storico'))
    a05=patch(a05,'territoryProfileIndicatorAsideMarkup',lambda b:after(b,"function territoryProfileIndicatorAsideMarkup(metric,choice,scale='value')","    if(metric.meta.compositeType==='invalsiProfile'){const t=invalsiPart(metric.aggregate,choice),i=invalsiPart(metric.nationalBenchmark,choice),u=t.unit||i.unit||metric.meta.unit;return `<span>Toscana · ${html(t.label||metric.meta.label)}</span><strong>${html(formatValue(t.value,u))}</strong><p>Italia: ${html(formatValue(i.value,i.unit||u))}. Stessa prova e annualità.</p>`;}\n",'aside benchmark'))

    # Visual grammar: scala funzionale e doppio riferimento ufficiale.
    vg=once(vg,"    'primaryFullTimeShare',\n","    'primaryFullTimeShare',\n    'invalsiResults',\n    'invalsiCompetence',\n    'invalsiImplicitDispersion',\n    'invalsiAcademicExcellence',\n",'scope funzionale')
    vg=patch(vg,'unitKind',lambda b:after(b,"const token = String(unit || '').trim().toLowerCase();","    if(token==='invalsi_score') return 'invalsi-score';\n",'unit WLE'))
    vg=patch(vg,'formatAxis',lambda b:after(b,'const kind = unitKind(unit);',"    if(kind==='invalsi-score') return number1.format(n);\n",'asse WLE'))
    vg=all_(vg,"'roadNetworkProfile'].includes(type)","'roadNetworkProfile','invalsiProfile'].includes(type)",'visual profile')
    vg=patch(vg,'compositeAggregateFor',lambda b:once(b,"label:`Versilia · ${part.label || metric.meta.label}`","label:type==='invalsiProfile'?`${metric.aggregate?.label||'Toscana'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",'visual Toscana'))
    def compare_vg(b):
        b=after(b,'const aggregate = compositeAggregate || aggregateFor(metric, normalized);',"    const np=metric.meta?.compositeType==='invalsiProfile'?((metric.nationalBenchmark?.parts||[]).find(p=>p.key===container.dataset.compositeChoice)||metric.nationalBenchmark?.parts?.[0]||{}):null;\n    const nv=finite(np?.value), nl=metric.nationalBenchmark?.label||'Italia';\n",'Italia value')
        b=line(b,'const scale = scaleFor(',lambda r:r.replace('scaleFor(mapped.map(item => item.value), aggregate?.value, unit)',"scaleFor([...mapped.map(item=>item.value),...(nv===null?[]:[nv])],aggregate?.value,unit)"),'scala Italia')
        b=after(b,'const referencePosition = position(aggregate?.value, scale);','    const nationalReferencePosition=position(nv,scale);\n','pos Italia')
        b=line(b,'const signature = [metricKey',lambda r:r.replace('aggregate?.value, unit','aggregate?.value, nv, unit'),'signature Italia')
        b=line(b,'legend.innerHTML =',lambda r:'    legend.innerHTML = `<span><i class="comparison-legend-dot" aria-hidden="true"></i>Comune</span><span><i class="comparison-legend-reference" aria-hidden="true"></i>${aggregate?.label||\'Versilia\'}</span>${nv===null?\'\':`<span><i class="comparison-legend-reference" style="opacity:.45" aria-hidden="true"></i>${nl}</span>`}`;\n','legend Italia')
        b=once(b,'${referencePosition !== null ? `<span class="comparison-reference" style="left:${referencePosition}%" aria-hidden="true"></span>` : \'\'}\n','${referencePosition !== null ? `<span class="comparison-reference" style="left:${referencePosition}%" aria-hidden="true"></span>` : \'\'}\n        ${nationalReferencePosition !== null ? `<span class="comparison-reference comparison-reference-national" data-invalsi-national-reference style="left:${nationalReferencePosition}%;opacity:.45" aria-hidden="true"></span>` : \'\'}\n','marker Italia')
        b=line(b,"if (row) rowEl.setAttribute('aria-label'",lambda r:r.replace("`${row.town}: ${formatAxis(value, unit)}; ${aggregate?.label || 'Versilia'}: ${formatAxis(aggregate?.value, unit)}`","`${row.town}: ${formatAxis(value,unit)}; ${aggregate?.label||'Versilia'}: ${formatAxis(aggregate?.value,unit)}${nv===null?'':`; ${nl}: ${formatAxis(nv,unit)}`}`"),'aria Italia')
        return b
    vg=patch(vg,'enhanceComparison',compare_vg)

    # Storico: null non è zero; per INVALSI si usano i Comuni con dato corrente.
    uc=once(uc,"      case 'index': return formatNumber(number, 1);\n","      case 'index': return formatNumber(number, 1);\n      case 'invalsi_score': return formatNumber(number, 1);\n",'history WLE')
    def comparable(b):
        b=once(b,'        const value = Number(values[yearIndex]);\n        if (Number.isFinite(value)) map.set(String(year), value);',"        const rawValue=values[yearIndex];\n        if(rawValue===null||rawValue===undefined||rawValue==='') return;\n        const value=Number(rawValue);\n        if(Number.isFinite(value)) map.set(String(year),value);",'null history')
        b=once(b,'        const value = Number(row.realSeries?.values?.[yearIndex]);\n        if (Number.isFinite(value)) realMap.set(String(year), value);',"        const rawValue=row.realSeries?.values?.[yearIndex];\n        if(rawValue===null||rawValue===undefined||rawValue==='') return;\n        const value=Number(rawValue);\n        if(Number.isFinite(value)) realMap.set(String(year),value);",'null real history')
        old='    if (rows.some(row => row.map.size < 2)) return null;\n    let years = [...rows[0].map.keys()].filter(year => rows.every(row => row.map.has(year)));\n    years = years.sort((a, b) => Number(a) - Number(b));\n    if (years.length < 2) return null;\n    return {\n      years,\n      rows: rows.map(row => ({'
        new="    const latest=[...new Set(rows.flatMap(r=>[...r.map.keys()]))].sort((a,b)=>Number(a)-Number(b)).at(-1);\n    const selected=metric.meta?.allowPartialHistory?rows.filter(r=>r.map.size>=2&&(!latest||r.map.has(latest))):rows;\n    if(!selected.length||(!metric.meta?.allowPartialHistory&&selected.some(r=>r.map.size<2))) return null;\n    let years=[...selected[0].map.keys()].filter(y=>selected.every(r=>r.map.has(y))).sort((a,b)=>Number(a)-Number(b));\n    if(years.length<2) return null;\n    return {years,rows:selected.map(row=>({"
        return once(b,old,new,'partial history')
    uc=patch(uc,'comparableSeries',comparable)

    # UX storico collettivo: abilita selector profilo e aggiunge Toscana/Italia.
    uh=once(uh,"const TERRITORY_PROFILE_HISTORY_TYPES = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']);","const TERRITORY_PROFILE_HISTORY_TYPES = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile','invalsiProfile']);",'history type')
    uh=all_(uh,"'roadNetworkProfile']","'roadNetworkProfile','invalsiProfile']",'history lists')
    uh=patch(uh,'compositeChoiceMetric',lambda b:once(b,"clone.aggregate={ ...metric.aggregate, value:aggregatePart.value, label:`Versilia · ${aggregatePart.label || metric.meta.label}`, series:metric.aggregate?.seriesByView?.[selected] || null };\n    return clone;","clone.aggregate={...metric.aggregate,value:aggregatePart.value,label:metric.meta.compositeType==='invalsiProfile'?`${metric.aggregate?.label||'Toscana'} · ${aggregatePart.label||metric.meta.label}`:`Versilia · ${aggregatePart.label||metric.meta.label}`,series:metric.aggregate?.seriesByView?.[selected]||null};\n    if(metric.meta.compositeType==='invalsiProfile'){const n=(metric.nationalBenchmark?.parts||[]).find(p=>p.key===selected)||metric.nationalBenchmark?.parts?.[0]||{};clone.nationalBenchmark={...metric.nationalBenchmark,value:n.value,label:`${metric.nationalBenchmark?.label||'Italia'} · ${n.label||metric.meta.label}`,series:metric.nationalBenchmark?.seriesByView?.[selected]||null};}\n    return clone;",'choice refs'))
    def official(b):
        add=r'''    if(series&&metric?.meta?.compositeType==='invalsiProfile'){
      const ref=(src,label,slug,color)=>{if(!src?.series?.years?.length)return null;const m=new Map(src.series.years.map((y,i)=>[String(y),src.series.values?.[i]]));if(!series.years.every(y=>{const v=m.get(String(y));return v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v));}))return null;return {town:label,slug,color,map:new Map(),realMap:new Map(),values:series.years.map(y=>Number(m.get(String(y)))),realSeries:null};};
      const refs=[ref(metric.aggregate,metric.aggregate?.label||'Toscana','toscana','var(--ink)'),ref(metric.nationalBenchmark,metric.nationalBenchmark?.label||'Italia','italia','var(--muted)')].filter(Boolean);return {...series,rows:[...series.rows,...refs]};
    }
'''
        return after(b,'function withOfficialVersiliaSeries(metric, series)',add,'official refs')
    uh=patch(uh,'withOfficialVersiliaSeries',official)
    uh=patch(uh,'renderHistoryMarkup',lambda b:after(b,'const markup = toolkit.historicalChartMarkup(metric, series, selectedTown);',"    if(metric?.meta?.compositeType==='invalsiProfile') return markup.replace('Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.','Comuni con dato corrente più Toscana e Italia; nessun valore mancante viene interpolato.').replace('confronto storico dei sette comuni','confronto storico INVALSI con Toscana e Italia').replace('aria-label=\"Comuni\"','aria-label=\"Comuni e benchmark INVALSI\"');\n",'copy history'))

    APP00.write_text(a00); APP03.write_text(a03); APP05.write_text(a05); VISUAL.write_text(vg); UXCORE.write_text(uc); UXH.write_text(uh)
    print('Renderer INVALSI v1.38 applicato: Toscana/Italia, livelli e storico senza media Versilia.')


if __name__=='__main__': main()
