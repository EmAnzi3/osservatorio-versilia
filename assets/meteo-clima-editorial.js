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
    const width=1000,height=410,left=88,right=30,top=28,bottom=72;
    const min=Math.min(...vs),max=Math.max(...vs),pad=(max-min||1)*.1;
    const yMin=state.metric==='precipitation'?Math.max(0,min-pad):min-pad,yMax=max+pad;
    const chartWidth=width-left-right,chartHeight=height-top-bottom;
    const x=(year)=>left+(year-ys[0])/(ys.at(-1)-ys[0])*chartWidth;
    const y=(value)=>top+(yMax-value)/(yMax-yMin)*chartHeight;
    const pts=vs.map((value,index)=>({year:ys[index],value,x:x(ys[index]),y:y(value)}));
    const line=pts.map(point=>`${point.x},${point.y}`).join(' ');
    const area=`${left},${height-bottom} ${line} ${width-right},${height-bottom}`;
    const tr=trend(ys,vs,1975,ys.at(-1));
    const ticks=[0,.25,.5,.75,1].map(f=>yMax-f*(yMax-yMin));
    const grids=ticks.map(v=>`<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" class="chart-grid climate-grid"></line><text class="climate-axis-label" x="${left-12}" y="${y(v)+4}" text-anchor="end">${esc(formatValue(v,state.metric))}</text>`).join('');
    const labels=ys.filter((year,i)=>i===0||i===ys.length-1||year%10===0).map(year=>`<text class="chart-label climate-axis-label" x="${x(year)}" y="${height-bottom+28}" text-anchor="middle">${year}</text>`).join('');
    const points=pts.map(point=>{
      const boxWidth=238,boxHeight=42;
      const boxX=Math.max(left-8,Math.min(width-right-boxWidth,point.x-boxWidth/2));
      const boxY=point.y<78?point.y+18:point.y-58;
      return `<g class="chart-point climate-chart-point" tabindex="0" role="button" aria-label="${esc(state.town)} · ${point.year}: ${esc(formatValue(point.value,state.metric))}"><circle class="chart-hit" cx="${point.x}" cy="${point.y}" r="17"></circle><circle class="chart-dot" cx="${point.x}" cy="${point.y}" r="5"></circle><g class="chart-tooltip" hidden><line class="chart-guide" x1="${point.x}" y1="${point.y}" x2="${point.x}" y2="${boxY<point.y?boxY+boxHeight:boxY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+15}">${esc(state.town)} · ${point.year}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+31}">${esc(formatValue(point.value,state.metric))}</text></g></g>`;
    }).join('');
    return `<div class="chart-shell"><div class="trend-chart climate-trend-chart"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(METRICS[state.metric].label)} a ${esc(state.town)} dal 1975 al ${ys.at(-1)}">${grids}<line class="climate-axis-line" x1="${left}" y1="${top}" x2="${left}" y2="${height-bottom}"></line><line class="climate-axis-line" x1="${left}" y1="${height-bottom}" x2="${width-right}" y2="${height-bottom}"></line><polygon class="chart-area climate-area" points="${area}"></polygon><polyline class="chart-line climate-line" points="${line}"></polyline><line class="climate-trend" x1="${x(1975)}" y1="${y(tr.start)}" x2="${x(ys.at(-1))}" y2="${y(tr.end)}"></line>${points}${labels}<text class="climate-axis-title" transform="translate(20 ${top+chartHeight/2}) rotate(-90)" text-anchor="middle">${esc(METRICS[state.metric].unit)}</text><text class="climate-axis-title" x="${left+chartWidth/2}" y="${height-12}" text-anchor="middle">Anno</text></svg></div></div><div class="chart-a11y-table"><strong>${esc(METRICS[state.metric].label)} · ${esc(state.town)}</strong>${pts.map(point=>`<span>${point.year}: ${esc(formatValue(point.value,state.metric))}</span>`).join('')}</div>`;
  }

  function installChartInteractions(root) {
    root.querySelectorAll('.trend-chart').forEach(chart => {
      if (chart.dataset.climateInteractions === 'true') return;
      chart.dataset.climateInteractions = 'true';
      const points = [...chart.querySelectorAll('.chart-point')];
      const hideAll = () => points.forEach(point => {
        point.classList.remove('active');
        point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
      });
      const show = point => {
        hideAll();
        point.classList.add('active');
        point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
      };
      points.forEach((point,index) => {
        point.addEventListener('mouseenter',()=>show(point));
        point.addEventListener('mouseleave',hideAll);
        point.addEventListener('focus',()=>show(point));
        point.addEventListener('blur',hideAll);
        point.addEventListener('click',()=>show(point));
        point.addEventListener('keydown',event=>{
          if(event.key==='Escape'){hideAll();point.blur();return;}
          if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
          event.preventDefault();
          let next=index;
          if(event.key==='ArrowLeft')next=(index-1+points.length)%points.length;
          if(event.key==='ArrowRight')next=(index+1)%points.length;
          if(event.key==='Home')next=0;
          if(event.key==='End')next=points.length-1;
          points[next]?.focus();
        });
      });
      chart.addEventListener('mouseleave',hideAll);
    });
  }

  function renderChart() {
    document.getElementById('climate-chart-title').textContent = `${METRICS[state.metric].label} · ${state.town}`;
    const host=document.getElementById('climate-chart');
    host.innerHTML = chartMarkup();
    installChartInteractions(host);
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
