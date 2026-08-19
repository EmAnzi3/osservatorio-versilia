(() => {
  'use strict';

  const ROOT = new URL('../', document.currentScript?.src || location.href);
  const DATA_URL = new URL('data/meteo-clima-poc.json', ROOT);
  const MINMAX_URL = new URL('data/meteo-clima-minmax-poc.json', ROOT);
  const STATUS_URL = new URL('data/source-monitor-state.json', ROOT);
  const METRICS = {
    temperature: { label: 'Temperatura media annua', unit: '°C', decimals: 2, dataset: 'climate' },
    tmin: { label: 'Temperatura minima media annua', unit: '°C', decimals: 2, dataset: 'minmax' },
    tmax: { label: 'Temperatura massima media annua', unit: '°C', decimals: 2, dataset: 'minmax' },
    precipitation: { label: 'Precipitazioni annue', unit: 'mm', decimals: 0, dataset: 'climate' }
  };
  const STATUS_KEYS = {
    temperature: 'climateTemperatureTrend50y',
    precipitation: 'climatePrecipitationTrend50y',
    tmin: 'climateTminTrend',
    tmax: 'climateTmaxTrend'
  };
  const fmt = (value, decimals = 1) => new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    useGrouping: 'always'
  }).format(Number(value));
  const signed = (value, decimals = 1) => `${Number(value) > 0 ? '+' : ''}${fmt(value, decimals)}`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;' }[c]));
  const slug = value => String(value || '').toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const state = { town: 'Massarosa', metric: 'temperature', climate: null, minmax: null, status: null };

  function sourceFor(metric) {
    return METRICS[metric].dataset === 'minmax' ? state.minmax : state.climate;
  }
  function seriesFor(town, metric) {
    const series = sourceFor(metric).municipalities[town];
    return { years: series.years.map(Number), values: series[metric].map(Number) };
  }
  function trend(years, values, from = 1975, to = 2025) {
    const points = years.map((year, i) => ({ year:Number(year), value:Number(values[i]) }))
      .filter(p => p.year >= from && p.year <= to && Number.isFinite(p.value));
    const mx = points.reduce((s,p)=>s+p.year,0)/points.length;
    const my = points.reduce((s,p)=>s+p.value,0)/points.length;
    const den = points.reduce((s,p)=>s+(p.year-mx)**2,0);
    const slope = points.reduce((s,p)=>s+(p.year-mx)*(p.value-my),0)/den;
    const intercept = my - slope * mx;
    return { from, to, slope, perDecade:slope*10, start:intercept+slope*from, end:intercept+slope*to, delta:slope*(to-from) };
  }
  function latestYear(metric) {
    const years = Object.values(sourceFor(metric).municipalities)[0].years.map(Number);
    return Math.max(...years);
  }
  function valueAt(town, metric, year) {
    const { years, values } = seriesFor(town, metric);
    return values[years.indexOf(year)];
  }
  function versiliaSimple(metric, year) {
    const towns = Object.keys(sourceFor(metric).municipalities);
    return towns.reduce((s,t)=>s+valueAt(t,metric,year),0)/towns.length;
  }
  function formatValue(value, metric) {
    const meta = METRICS[metric];
    return `${fmt(value, meta.decimals)} ${meta.unit}`;
  }

  function renderControls() {
    const town = document.getElementById('climate-town');
    town.innerHTML = Object.keys(state.climate.municipalities).sort((a,b)=>a.localeCompare(b,'it'))
      .map(name => `<option value="${esc(name)}" ${name===state.town?'selected':''}>${esc(name)}</option>`).join('');
    town.addEventListener('change', () => { state.town = town.value; render(); });
    document.querySelectorAll('[data-climate-metric]').forEach(button => button.addEventListener('click', () => {
      state.metric = button.dataset.climateMetric;
      render();
    }));
  }

  function renderHeadline() {
    const latest = latestYear(state.metric);
    const current = valueAt(state.town, state.metric, latest);
    const { years, values } = seriesFor(state.town, state.metric);
    const tr = trend(years, values, 1975, latest);
    document.getElementById('climate-current-value').textContent = formatValue(current, state.metric);
    document.getElementById('climate-current-label').textContent = `${state.town} · ultimo anno completo ${latest}`;
    const trendValue = state.metric === 'precipitation'
      ? `${signed(tr.delta / Math.abs(tr.start) * 100, 1)}%`
      : `${signed(tr.delta, 2)} °C`;
    document.getElementById('climate-trend-value').textContent = trendValue;
    document.getElementById('climate-trend-label').textContent = `variazione stimata dal trend lineare 1975–${latest}`;
    const mean = versiliaSimple(state.metric, latest);
    document.getElementById('climate-versilia-value').textContent = formatValue(mean, state.metric);
    document.getElementById('climate-versilia-label').textContent = `media semplice dei sette Comuni · ${latest}`;
  }

  function chartMarkup() {
    const { years, values } = seriesFor(state.town, state.metric);
    const fromIndex = years.findIndex(y => y >= 1975);
    const ys = years.slice(fromIndex), vs = values.slice(fromIndex);
    const width=1000,height=380,left=62,right=24,top=25,bottom=46;
    const min=Math.min(...vs),max=Math.max(...vs),pad=(max-min||1)*.1,yMin=state.metric==='precipitation'?Math.max(0,min-pad):min-pad,yMax=max+pad;
    const x=(year)=>left+(year-ys[0])/(ys.at(-1)-ys[0])*(width-left-right);
    const y=(value)=>top+(yMax-value)/(yMax-yMin)*(height-top-bottom);
    const path=vs.map((v,i)=>`${i?'L':'M'}${x(ys[i]).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const tr=trend(ys,vs,1975,ys.at(-1));
    const ticks=[0,.25,.5,.75,1].map(f=>yMin+(yMax-yMin)*f);
    const grids=ticks.map(v=>`<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" class="climate-grid"></line><text x="${left-10}" y="${y(v)+4}" text-anchor="end">${esc(formatValue(v,state.metric))}</text>`).join('');
    const labels=ys.filter((year,i)=>i===0||i===ys.length-1||year%10===0).map(year=>`<text x="${x(year)}" y="${height-14}" text-anchor="middle">${year}</text>`).join('');
    const points=vs.map((v,i)=>`<circle cx="${x(ys[i])}" cy="${y(v)}" r="3"><title>${esc(state.town)} · ${ys[i]}: ${esc(formatValue(v,state.metric))}</title></circle>`).join('');
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(METRICS[state.metric].label)} a ${esc(state.town)} dal 1975 al ${ys.at(-1)}">${grids}${labels}<path class="climate-line" d="${path}"></path><line class="climate-trend" x1="${x(1975)}" y1="${y(tr.start)}" x2="${x(ys.at(-1))}" y2="${y(tr.end)}"></line>${points}</svg>`;
  }

  function renderChart() {
    document.getElementById('climate-chart-title').textContent = `${METRICS[state.metric].label} · ${state.town}`;
    document.getElementById('climate-chart').innerHTML = chartMarkup();
  }

  function renderTowns() {
    const latest = latestYear(state.metric);
    const mean = versiliaSimple(state.metric, latest);
    const towns = Object.keys(sourceFor(state.metric).municipalities).sort((a,b)=>a.localeCompare(b,'it'));
    document.getElementById('climate-town-list').innerHTML = towns.map(town => {
      const value=valueAt(town,state.metric,latest),delta=value-mean;
      return `<a href="../../comuni/${slug(town)}/?tema=ambiente&indicatore=${encodeURIComponent(STATUS_KEYS[state.metric])}"><span>${esc(town)}</span><strong>${esc(formatValue(value,state.metric))}</strong><small>${delta===0?'in linea con':delta>0?'sopra':'sotto'} la media semplice Versilia di ${esc(formatValue(Math.abs(delta),state.metric))}</small></a>`;
    }).join('');
  }

  function renderStatus() {
    const key = STATUS_KEYS[state.metric];
    const item = state.status?.metrics?.[key];
    const checked = item?.checkedAt ? new Date(item.checkedAt).toLocaleDateString('it-IT') : 'non disponibile';
    document.getElementById('climate-status').innerHTML = `<strong>${esc(item?.publishedPeriod || latestYear(state.metric))}</strong><span>periodo pubblicato</span><strong>${esc(checked)}</strong><span>ultimo controllo registrato</span><a href="../../stato-dati/">Apri Stato dei dati →</a>`;
  }

  function renderMethod() {
    const method = state.metric === 'tmin' || state.metric === 'tmax'
      ? 'Serie ERA5-Land continua 1975–2025. LaMMA è usato come riferimento di livello; le osservazioni SIR validate sono un controllo indipendente del comportamento temporale. Non è una temperatura misurata in un singolo punto del Comune.'
      : 'Ricostruzione territoriale comunale da prodotti grigliati LaMMA ed ERA5-Land. La serie pubblicata non equivale a una stazione meteo comunale. In questa bozza resta in corso l’audit per verificare una possibile serie ERA5-Land continua anche per temperatura media e precipitazioni.';
    document.getElementById('climate-method-copy').textContent = method;
  }

  function render() {
    document.querySelectorAll('[data-climate-metric]').forEach(button => {
      const active = button.dataset.climateMetric === state.metric;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    renderHeadline(); renderChart(); renderTowns(); renderStatus(); renderMethod();
  }

  Promise.all([
    fetch(DATA_URL).then(r=>{if(!r.ok)throw new Error(`Climate ${r.status}`);return r.json();}),
    fetch(MINMAX_URL).then(r=>{if(!r.ok)throw new Error(`Minmax ${r.status}`);return r.json();}),
    fetch(STATUS_URL).then(r=>{if(!r.ok)throw new Error(`Status ${r.status}`);return r.json();})
  ]).then(([climate,minmax,status])=>{
    state.climate=climate; state.minmax=minmax; state.status=status;
    renderControls(); render();
  }).catch(error=>{
    console.error(error);
    document.getElementById('climate-workspace').innerHTML='<div class="app-error"><strong>Dati climatici non disponibili.</strong><p>Ricarica la pagina o consulta Stato dei dati.</p></div>';
  });
})();
