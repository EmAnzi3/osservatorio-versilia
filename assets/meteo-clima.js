(() => {
  'use strict';

  const DATA_URL = '../../data/meteo-clima-poc.json';
  const townSelect = document.getElementById('climate-town');
  const chartRoot = document.getElementById('climate-chart');
  const summaryRoot = document.getElementById('climate-summary');
  const barsRoot = document.getElementById('climate-compare-bars');
  const tooltip = document.getElementById('climate-tooltip');
  const smoothToggle = document.getElementById('climate-smooth-toggle');
  const metricTabs = [...document.querySelectorAll('[data-metric]')];
  const chartTitle = document.getElementById('climate-chart-title');
  const chartUnit = document.getElementById('climate-chart-unit');
  const partialRoot = document.getElementById('climate-partial');

  const state = { town: 'Massarosa', metric: 'temperature', smooth: true, data: null };
  const meta = {
    temperature: { label: 'Temperatura media annua', short: 'Temperatura media', unit: '°C', decimals: 2 },
    precipitation: { label: 'Precipitazioni annue', short: 'Precipitazioni', unit: 'mm', decimals: 0 }
  };

  const fmt = (value, decimals = 1) => new Intl.NumberFormat('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

  function movingAverage(values, windowSize = 10) {
    return values.map((_, index) => {
      if (index < windowSize - 1) return null;
      const slice = values.slice(index - windowSize + 1, index + 1).filter(Number.isFinite);
      return slice.length === windowSize ? slice.reduce((a,b) => a+b, 0) / windowSize : null;
    });
  }

  function latestAnomaly(series, metric) {
    const latest = series.latestComplete[metric];
    const normal = series.normal1991_2020[metric];
    const delta = latest - normal;
    return { latest, normal, delta, percent: metric === 'precipitation' ? delta / normal * 100 : null };
  }

  function renderSummary() {
    const series = state.data.municipalities[state.town];
    const m = meta[state.metric];
    const a = latestAnomaly(series, state.metric);
    const deltaClass = a.delta > 0 ? 'positive' : a.delta < 0 ? 'negative' : '';
    const normalLabel = state.metric === 'temperature' ? `${fmt(a.normal,2)} ${m.unit}` : `${fmt(a.normal,0)} ${m.unit}`;
    const latestLabel = state.metric === 'temperature' ? `${fmt(a.latest,2)} ${m.unit}` : `${fmt(a.latest,0)} ${m.unit}`;
    const anomalyLabel = state.metric === 'temperature'
      ? `${a.delta >= 0 ? '+' : ''}${fmt(a.delta,2)} ${m.unit}`
      : `${a.delta >= 0 ? '+' : ''}${fmt(a.delta,0)} mm`;
    const anomalyNote = state.metric === 'temperature'
      ? 'Scarto del 2025 rispetto alla media climatica 1991–2020.'
      : `${a.percent >= 0 ? '+' : ''}${fmt(a.percent,1)}% rispetto alla media 1991–2020.`;
    summaryRoot.innerHTML = `
      <article class="climate-summary-card"><span>2025 · ${escapeHtml(state.town)}</span><strong>${latestLabel}</strong><small>Ultima annualità completa della serie.</small></article>
      <article class="climate-summary-card"><span>Media climatica 1991–2020</span><strong>${normalLabel}</strong><small>Riferimento trentennale calcolato sulla stessa serie territoriale.</small></article>
      <article class="climate-summary-card"><span>Anomalia 2025</span><strong class="${deltaClass}">${anomalyLabel}</strong><small>${anomalyNote}</small></article>`;
  }

  function renderChart() {
    const series = state.data.municipalities[state.town];
    const years = series.years;
    const values = series[state.metric];
    const smooth = movingAverage(values, 10);
    const width = 1040, height = 390, left = 64, right = 20, top = 31, bottom = 46;
    const plotW = width - left - right, plotH = height - top - bottom;
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    let padding = (rawMax - rawMin) * .10;
    if (!padding) padding = 1;
    let yMin = rawMin - padding, yMax = rawMax + padding;
    if (state.metric === 'precipitation') yMin = Math.max(0, yMin);
    const x = year => left + (year - years[0]) / (years.at(-1) - years[0]) * plotW;
    const y = value => top + (yMax - value) / (yMax - yMin) * plotH;
    const path = arr => arr.map((value,index) => Number.isFinite(value) ? `${index === 0 || !Number.isFinite(arr[index-1]) ? 'M' : 'L'}${x(years[index]).toFixed(1)},${y(value).toFixed(1)}` : '').join(' ');
    const ticks = Array.from({length:5},(_,i)=>yMin+(yMax-yMin)*i/4);
    const xTicks = [1950,1960,1970,1980,1990,2000,2010,2020,2025];
    const bands = state.data.provenance.map(seg => {
      const x1=x(seg.from), x2=x(seg.to + (seg.to < years.at(-1) ? 1 : 0));
      const cls=seg.class === 'INTERPOLATED_OBSERVATIONS' ? 'climate-source-band-lamma' : 'climate-source-band-era5';
      const short=seg.class === 'INTERPOLATED_OBSERVATIONS' ? 'LaMMA · interpolato' : 'ERA5-Land · rianalisi calibrata';
      return `<rect class="${cls}" x="${x1}" y="${top}" width="${Math.max(0,x2-x1)}" height="${plotH}"></rect><text class="climate-source-label" x="${x1+7}" y="${top+13}">${short}</text>`;
    }).join('');
    const grids=ticks.map(value=>`<line class="climate-grid-line" x1="${left}" x2="${width-right}" y1="${y(value)}" y2="${y(value)}"></line><text class="climate-axis-label" x="${left-10}" y="${y(value)+3}" text-anchor="end">${state.metric==='temperature'?fmt(value,1):fmt(value,0)}</text>`).join('');
    const labels=xTicks.map(year=>`<text class="climate-axis-label" x="${x(year)}" y="${height-14}" text-anchor="middle">${year}</text>`).join('');
    const points=values.map((value,index)=>`<circle class="climate-series-point" cx="${x(years[index])}" cy="${y(value)}" r="2.4"></circle><circle class="climate-series-hit" data-year="${years[index]}" data-value="${value}" cx="${x(years[index])}" cy="${y(value)}" r="8"></circle>`).join('');
    chartRoot.className = `climate-chart-wrap metric-${state.metric}`;
    chartRoot.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(meta[state.metric].label)} a ${escapeHtml(state.town)} dal 1950 al 2025">${bands}${grids}${labels}<path class="climate-series-line" d="${path(values)}"></path>${state.smooth?`<path class="climate-smooth-line" d="${path(smooth)}"></path>`:''}${points}</svg>`;
    chartTitle.textContent=meta[state.metric].label;
    chartUnit.textContent=meta[state.metric].unit;
    chartRoot.querySelectorAll('.climate-series-hit').forEach(hit=>{
      const show=e=>{
        const year=Number(hit.dataset.year), value=Number(hit.dataset.value);
        const prov=state.data.provenance.find(p=>year>=p.from&&year<=p.to);
        tooltip.innerHTML=`<span>${escapeHtml(state.town)} · ${year}</span><strong>${state.metric==='temperature'?fmt(value,2):fmt(value,0)} ${meta[state.metric].unit}</strong><small>${escapeHtml(prov?.label||'')}</small>`;
        tooltip.hidden=false;
        const px=Math.min(window.innerWidth-170,Math.max(8,e.clientX+12));
        const py=Math.min(window.innerHeight-75,Math.max(8,e.clientY+12));
        tooltip.style.left=`${px}px`;tooltip.style.top=`${py}px`;
      };
      hit.addEventListener('pointerenter',show);hit.addEventListener('pointermove',show);hit.addEventListener('pointerleave',()=>tooltip.hidden=true);
    });
  }

  function renderComparison() {
    const rows=Object.entries(state.data.municipalities).map(([town,series])=>({town,value:series.latestComplete[state.metric]})).sort((a,b)=>b.value-a.value);
    const min=Math.min(...rows.map(r=>r.value)), max=Math.max(...rows.map(r=>r.value));
    const span=Math.max(max-min,0.0001);
    barsRoot.closest('.climate-comparison').classList.toggle('metric-precipitation',state.metric==='precipitation');
    barsRoot.innerHTML=rows.map(row=>{
      const pct=12+(row.value-min)/span*88;
      const value=state.metric==='temperature'?`${fmt(row.value,2)} °C`:`${fmt(row.value,0)} mm`;
      return `<div class="climate-compare-row ${row.town===state.town?'active':''}"><button type="button" data-town="${escapeHtml(row.town)}">${escapeHtml(row.town)}</button><div class="climate-compare-track"><div class="climate-compare-fill" style="width:${pct.toFixed(1)}%"></div></div><strong class="climate-compare-value">${value}</strong></div>`;
    }).join('');
    barsRoot.querySelectorAll('[data-town]').forEach(button=>button.addEventListener('click',()=>setTown(button.dataset.town)));
  }

  function renderMethod() {
    const m=state.data.method;
    document.getElementById('method-spatial').textContent=m.spatial;
    document.getElementById('method-source').textContent='LaMMA resta la fonte primaria nel 1995–2015; ERA5-Land calibrato completa la serie prima e dopo questo intervallo.';
    document.getElementById('method-validation').textContent=m.validation;
    document.getElementById('method-temperature').textContent=m.temperature;
    document.getElementById('method-precipitation').textContent=m.precipitation;
    document.getElementById('climate-source-timeline').innerHTML=state.data.provenance.map(p=>`<div class="climate-source-segment ${p.class==='INTERPOLATED_OBSERVATIONS'?'lamma':'era5'}"><strong>${p.from}–${p.to} · ${escapeHtml(p.label)}</strong><span>${escapeHtml(p.source)}</span></div>`).join('');
  }

  function renderPartial() {
    const partial=state.data.coverage.partial;
    if(!partial){partialRoot.hidden=true;return;}
    partialRoot.hidden=false;
    partialRoot.innerHTML=`<span class="overline">Anno in corso · dato parziale</span><h2>${partial.year} fino al ${escapeHtml(partial.coverageEnd)}</h2><p>Il valore in corso non viene trattato come annualità completa e non entra nel confronto con i totali annuali. <strong>${escapeHtml(partial.note||'')}</strong></p>`;
  }

  function updateUrl(){const p=new URLSearchParams(location.search);p.set('comune',state.town);p.set('indicatore',state.metric);history.replaceState(null,'',`${location.pathname}?${p}`)}
  function setTown(town){if(!state.data.municipalities[town])return;state.town=town;townSelect.value=town;updateUrl();renderAll()}
  function setMetric(metric){if(!meta[metric])return;state.metric=metric;metricTabs.forEach(b=>{const on=b.dataset.metric===metric;b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')});updateUrl();renderAll()}
  function renderAll(){renderSummary();renderChart();renderComparison();renderPartial()}

  async function start(){
    const response=await fetch(DATA_URL,{cache:'no-store'});if(!response.ok)throw new Error(`Dati meteo: ${response.status}`);state.data=await response.json();
    const towns=Object.keys(state.data.municipalities);townSelect.innerHTML=towns.map(t=>`<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    const params=new URLSearchParams(location.search);const requestedTown=params.get('comune'),requestedMetric=params.get('indicatore');
    if(requestedTown&&state.data.municipalities[requestedTown])state.town=requestedTown;if(requestedMetric&&meta[requestedMetric])state.metric=requestedMetric;
    townSelect.value=state.town;metricTabs.forEach(b=>{const on=b.dataset.metric===state.metric;b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')});
    townSelect.addEventListener('change',()=>setTown(townSelect.value));metricTabs.forEach(b=>b.addEventListener('click',()=>setMetric(b.dataset.metric)));
    smoothToggle.addEventListener('click',()=>{state.smooth=!state.smooth;smoothToggle.classList.toggle('active',state.smooth);smoothToggle.setAttribute('aria-pressed',state.smooth?'true':'false');renderChart()});
    renderMethod();renderAll();
  }

  start().catch(error=>{console.error(error);chartRoot.innerHTML='<div class="app-error"><strong>Impossibile caricare la serie climatica.</strong><p>Il prototipo richiede un server web e il file dati POC.</p></div>'});
})();
