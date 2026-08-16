#!/usr/bin/env python3
"""Patch frontend surfaces for validated cost metrics and long income history."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP00=ROOT/'assets/app-parts/00.txt';APP03=ROOT/'assets/app-parts/03.txt';APP05=ROOT/'assets/app-parts/05.txt';UX=ROOT/'assets/ux-history.js'

def once(text,old,new,label):
    if new in text:return text
    if old not in text:raise RuntimeError(f'patch missing: {label}')
    return text.replace(old,new,1)

def app00():
    text=APP00.read_text(encoding='utf-8')
    insertions=[('tariStandardHousehold',"['tari', 'tariffa rifiuti', 'tassa rifiuti', '3 persone', '100 mq']",'municipalIrpef'),('municipalImuStandard',"['imu', 'seconda casa', 'seconda abitazione', 'aliquota imu']",'tariStandardHousehold'),('fuelPrices',"['benzina', 'gasolio', 'diesel', 'carburante', 'prezzo carburanti']",'pollutingCars'),('wasteServiceCost',"['costo rifiuti', 'ctotab', 'igiene urbana', 'costo servizio rifiuti']",'wastePerResident')]
    for key,terms,anchor in insertions:
        if f'    {key}:' in text:continue
        pos=text.find(f'    {anchor}:')
        if pos<0:raise RuntimeError(f'search synonym anchor missing: {anchor}')
        end=text.find('\n',pos);text=text[:end+1]+f'    {key}: {terms},\n'+text[end+1:]
    if 'const currency2 =' not in text:text=once(text,"  const number2 = italianFormatter({ minimumFractionDigits: 2, maximumFractionDigits: 2 });\n  const currency0 = italianFormatter({ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });","  const number2 = italianFormatter({ minimumFractionDigits: 2, maximumFractionDigits: 2 });\n  const number3 = italianFormatter({ minimumFractionDigits: 3, maximumFractionDigits: 3 });\n  const currency0 = italianFormatter({ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });\n  const currency2 = italianFormatter({ style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 2 });",'formatters')
    if "case 'currency2'" not in text:text=once(text,"      case 'currency': return currency0.format(v);","      case 'currency': return currency0.format(v);\n      case 'currency2': return currency2.format(v);",'currency2')
    if "case 'eurliter'" not in text:text=once(text,"      case 'rentm2': return `${number1.format(v)} €/m²/mese`;","      case 'rentm2': return `${number1.format(v)} €/m²/mese`;\n      case 'eurliter': return `${number3.format(v)} €/l`;\n      case 'eurPerResident': return `${number2.format(v)} €/ab`;",'fuel/waste units')
    APP00.write_text(text,encoding='utf-8')

def ux():
    text=UX.read_text(encoding='utf-8')
    helper="""\n  function historyMetric(metric) {\n    if (metric?.meta?.key !== 'income' || !metric.rows?.some(row => row.longSeries?.years?.length)) return metric;\n    return { ...metric, meta:{...metric.meta,label:metric.meta.longHistoryLabel || 'Reddito imponibile medio · serie lunga',unit:'currency'}, rows:metric.rows.map(row=>({...row,series:row.longSeries || row.series})) };\n  }\n"""
    if 'function historyMetric(metric)' not in text:text=once(text,'\n  function enhanceCompare(data) {',helper+'\n  function enhanceCompare(data) {','history helper')
    if 'const historyView = historyMetric(selected.metric);' not in text:
        text=once(text,'    const series = normalized ? null : toolkit.comparableSeries(selected.metric);','    const historyView = historyMetric(selected.metric);\n    const series = normalized ? null : toolkit.comparableSeries(historyView);','compare history');text=once(text,'    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);','    const historyMarkup = toolkit.historicalChartMarkup(historyView, series, selectedTown);','compare markup')
    compare_old="""    const note = normalized\n      ? 'La vista storica è disponibile sulla scala assoluta, perché le serie normalizzate non sono presenti per tutti gli anni.'\n      : historyAvailable\n        ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'\n        : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    compare_new="""    const note = normalized\n      ? 'La vista storica è disponibile sulla scala assoluta, perché le serie normalizzate non sono presenti per tutti gli anni.'\n      : historyAvailable && selected.metric?.meta?.key === 'income'\n        ? selected.metric.meta.longHistoryNote\n        : historyAvailable\n          ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'\n          : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    if compare_old in text:text=text.replace(compare_old,compare_new,1)
    if text.count('const historyView = historyMetric(selected.metric);')<2:
        text=once(text,'    const series = toolkit.comparableSeries(selected.metric);\n    const historyAvailable = Boolean(series);','    const historyView = historyMetric(selected.metric);\n    const series = toolkit.comparableSeries(historyView);\n    const historyAvailable = Boolean(series);','town history');text=once(text,'    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);','    const historyMarkup = toolkit.historicalChartMarkup(historyView, series, selectedTown);','town markup')
    town_old="""    const note = historyAvailable\n      ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'\n      : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    town_new="""    const note = historyAvailable && selected.metric?.meta?.key === 'income'\n      ? selected.metric.meta.longHistoryNote\n      : historyAvailable\n        ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'\n        : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    if town_old in text:text=text.replace(town_old,town_new,1)
    UX.write_text(text,encoding='utf-8')

def app03():
    text=APP03.read_text(encoding='utf-8'); line="      ${themeKey === 'economia' ? incomeInflationMarkup(data) : ''}\n"
    if line.strip() not in text:text=once(text,"      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}\n","      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}\n"+line,'economy context')
    text=text.replace('<span class="bar-rank">${index+1}</span><span class="bar-town">','<span class="bar-rank">${row.displayValue === null || row.displayValue === undefined ? \'—\' : index+1}</span><span class="bar-town">',1)
    text=text.replace('style="width:${Math.max(1.5,Math.abs(Number(row.displayValue)||0)/max*100)}%"','style="width:${row.displayValue === null || row.displayValue === undefined ? 0 : Math.max(1.5,Math.abs(Number(row.displayValue)||0)/max*100)}%"',1)
    APP03.write_text(text,encoding='utf-8')

def app05():
    text=APP05.read_text(encoding='utf-8')
    fn=r'''
  function incomeInflationMarkup(data) {
    const c=data.incomeInflationContext;if(!c?.years?.length)return '';
    const w=720,h=300,l=52,r=18,t=22,b=42,all=[...c.incomeIndex,...c.priceIndex,...c.realIncomeIndex].map(Number).filter(Number.isFinite),min=Math.floor(Math.min(...all,98)-2),max=Math.ceil(Math.max(...all,102)+2);
    const x=i=>l+(w-l-r)*i/Math.max(1,c.years.length-1),y=v=>t+(h-t-b)*(max-Number(v))/Math.max(1,max-min),path=values=>values.map((v,i)=>`${i?'L':'M'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' '),ticks=[...new Set([min,100,110,120,max].filter(v=>v>=min&&v<=max))].sort((a,b)=>a-b);
    const grid=ticks.map(v=>`<g><line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".12"></line><text x="${l-10}" y="${y(v)+4}" text-anchor="end" class="chart-label chart-y-label">${html(number0.format(v))}</text></g>`).join(''),labels=c.years.map((year,i)=>(i%2===0||i===c.years.length-1)?`<text x="${x(i)}" y="${h-14}" text-anchor="middle" class="chart-label">${html(year)}</text>`:'').join('');
    return `<section class="crime-context page-width income-inflation-context" id="redditi-prezzi"><div class="crime-context-copy"><span class="overline">Contesto · redditi e costo della vita</span><h2>Quanto della crescita dei redditi resta dopo l’inflazione?</h2><p>Confronto tra imponibile medio dichiarato nei sette comuni e NIC della Toscana, entrambi riportati a <strong>${html(c.base)}</strong>.</p><div class="crime-stats"><article><span>Imponibile medio</span><strong>+${html(number1.format(c.nominalGrowthPercent))}%</strong><small>2016–2024</small></article><article><span>Prezzi NIC Toscana</span><strong>+${html(number1.format(c.priceGrowthPercent))}%</strong><small>2016–2024</small></article><article><span>A prezzi costanti</span><strong>+${html(number1.format(c.realGrowthPercent))}%</strong><small>imponibile medio</small></article></div><p class="brain-drain-note">${html(c.note)}</p><div><a class="source-pill" href="${html(c.incomeSourceUrl)}" target="_blank" rel="noreferrer">Fonte redditi · MEF ↗</a> <a class="source-pill" href="${html(c.priceSourceUrl)}" target="_blank" rel="noreferrer">Fonte prezzi · Toscana/Istat ↗</a></div></div><div class="crime-context-data"><h3>Redditi e prezzi · ${html(c.base)}</h3><div class="composite-legend"><span>━ ${html(c.incomeLabel)}</span><span>┅ ${html(c.priceLabel)}</span><span>┈ ${html(c.realLabel)}</span></div><div class="trend-chart"><svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Confronto redditi e prezzi dal 2016 al 2024">${grid}${labels}<path d="${path(c.incomeIndex)}" fill="none" stroke="currentColor" stroke-width="3.4"></path><path d="${path(c.priceIndex)}" fill="none" stroke="currentColor" stroke-width="2.8" stroke-dasharray="10 7" opacity=".72"></path><path d="${path(c.realIncomeIndex)}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-dasharray="2 6" opacity=".9"></path>${c.incomeIndex.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="3.5" fill="currentColor"><title>${html(c.years[i])}: ${html(number1.format(v))}</title></circle>`).join('')}</svg></div><p class="brain-drain-note">Il NIC è regionale <strong>Toscana</strong>: non è il dato della Provincia di Lucca né quello del Comune di Lucca. “A prezzi costanti” è un’elaborazione sull’imponibile medio, non sul reddito disponibile delle famiglie.</p></div></section>`;
  }
'''
    if 'function incomeInflationMarkup(data)' not in text:text=once(text,'\n  function brainDrainMarkup(data) {','\n'+fn+'\n  function brainDrainMarkup(data) {','income inflation markup')
    text=text.replace("    const historicalRows = metric.rows.filter(row => row.series?.years?.length && row.series?.values?.length);","    const seriesFor = row => metric.meta.key === 'income' && row.longSeries?.years?.length ? row.longSeries : row.series;\n    const historicalRows = metric.rows.filter(row => seriesFor(row)?.years?.length && seriesFor(row)?.values?.length);",1)
    text=text.replace('    const years = [...new Set(historicalRows.flatMap(row => row.series.years))].sort((a, b) => Number(a) - Number(b));','    const years = [...new Set(historicalRows.flatMap(row => seriesFor(row).years))].sort((a, b) => Number(a) - Number(b));',1)
    text=text.replace('      const values = new Map(row.series.years.map((year, index) => [String(year), row.series.values[index]]));','      const series = seriesFor(row);\n      const values = new Map(series.years.map((year, index) => [String(year), series.values[index]]));',1)
    text=text.replace("formatValue(values.get(String(year)), metric.meta.unit)","formatValue(values.get(String(year)), metric.meta.key === 'income' ? 'currency' : metric.meta.unit)",1)
    marker='    return `<div class="indicator-table-scroll"><table class="indicator-history-table">';replacement='''    return `${metric.meta.key === 'income' ? `<p class="brain-drain-note">${html(metric.meta.longHistoryNote)}</p>` : ''}<div class="indicator-table-scroll"><table class="indicator-history-table">'''
    if marker in text and 'metric.meta.longHistoryNote' not in text:text=text.replace(marker,replacement,1)
    APP05.write_text(text,encoding='utf-8')

def main():app00();ux();app03();app05();print('Frontend costi/fiscalità/redditi patched')
if __name__=='__main__':main()
