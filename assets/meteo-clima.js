(() => {
  'use strict';

  const DATA_URL = '../../data/meteo-clima-poc.json';
  const MINMAX_URL = '../../data/meteo-clima-minmax-poc.json';
  const TREND_START = 1975;
  const TREND_END = 2025;

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
  const trendNoteRoot = document.getElementById('climate-trend-note');
  const minmaxSection = document.getElementById('temperature-min-max');
  const minmaxChartRoot = document.getElementById('climate-minmax-chart');
  const minmaxSummaryRoot = document.getElementById('climate-minmax-summary');

  const state = { town: 'Massarosa', metric: 'temperature', smooth: true, data: null, minmax: null };
  const meta = {
    temperature: { label: 'Temperatura media annua', short: 'Temperatura media', unit: '°C', decimals: 2 },
    precipitation: { label: 'Precipitazioni annue', short: 'Precipitazioni', unit: 'mm', decimals: 0 }
  };

  const fmt = (value, decimals = 1) => new Intl.NumberFormat('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c]));
  const signed = (value, decimals = 1) => `${value >= 0 ? '+' : ''}${fmt(value, decimals)}`;

  function movingAverage(values, windowSize = 10) {
    return values.map((_, index) => {
      if (index < windowSize - 1) return null;
      const slice = values.slice(index - windowSize + 1, index + 1).filter(Number.isFinite);
      return slice.length === windowSize ? slice.reduce((a, b) => a + b, 0) / windowSize : null;
    });
  }

  function linearTrend(years, values, start = TREND_START, end = TREND_END) {
    const points = years.map((year, index) => ({ year: Number(year), value: Number(values[index]) }))
      .filter(point => point.year >= start && point.year <= end && Number.isFinite(point.value));
    if (points.length < 3) return null;
    const meanX = points.reduce((sum, point) => sum + point.year, 0) / points.length;
    const meanY = points.reduce((sum, point) => sum + point.value, 0) / points.length;
    const numerator = points.reduce((sum, point) => sum + (point.year - meanX) * (point.value - meanY), 0);
    const denominator = points.reduce((sum, point) => sum + (point.year - meanX) ** 2, 0);
    if (!denominator) return null;
    const slope = numerator / denominator;
    const intercept = meanY - slope * meanX;
    const fitted = points.map(point => intercept + slope * point.year);
    const ssTot = points.reduce((sum, point) => sum + (point.value - meanY) ** 2, 0);
    const ssRes = points.reduce((sum, point, index) => sum + (point.value - fitted[index]) ** 2, 0);
    const r2 = ssTot > 0 ? Math.max(0, 1 - ssRes / ssTot) : 0;
    const startValue = intercept + slope * start;
    const endValue = intercept + slope * end;
    const delta = endValue - startValue;
    return { start, end, slope, intercept, delta, perDecade: slope * 10, startValue, endValue, percent: startValue !== 0 ? delta / Math.abs(startValue) * 100 : null, r2 };
  }

  function latestAnomaly(series, metric) {
    const latest = series.latestComplete[metric];
    const normal = series.normal1991_2020[metric];
    const delta = latest - normal;
    return { latest, normal, delta, percent: metric === 'precipitation' ? delta / normal * 100 : null };
  }

  function selectedTrend() {
    const series = state.data.municipalities[state.town];
    return linearTrend(series.years, series[state.metric]);
  }

  function renderSummary() {
    const series = state.data.municipalities[state.town];
    const trend = selectedTrend();
    const anomaly = latestAnomaly(series, state.metric);
    if (!trend) return;

    let trendValue, trendNote, paceValue, paceNote, anomalyValue, anomalyNote;
    if (state.metric === 'temperature') {
      trendValue = `${signed(trend.delta, 2)} °C`;
      trendNote = `Variazione stimata dalla retta di tendenza tra ${TREND_START} e ${TREND_END}.`;
      paceValue = `${signed(trend.perDecade, 2)} °C`;
      paceNote = 'Ritmo medio del trend per decennio.';
      anomalyValue = `${signed(anomaly.delta, 2)} °C`;
      anomalyNote = `2025 rispetto alla media climatica 1991–2020 (${fmt(anomaly.normal, 2)} °C).`;
    } else {
      trendValue = `${signed(trend.percent, 1)}%`;
      trendNote = `${signed(trend.delta, 0)} mm lungo il trend ${TREND_START}–${TREND_END}.`;
      paceValue = `${signed(trend.perDecade, 0)} mm`;
      paceNote = 'Ritmo medio del trend per decennio; la variabilità annuale resta elevata.';
      anomalyValue = `${signed(anomaly.percent, 1)}%`;
      anomalyNote = `${signed(anomaly.delta, 0)} mm nel 2025 rispetto alla media 1991–2020 (${fmt(anomaly.normal, 0)} mm).`;
    }

    const direction = trend.delta > 0 ? 'trend-up' : trend.delta < 0 ? 'trend-down' : '';
    summaryRoot.innerHTML = `
      <article class="climate-summary-card climate-summary-primary"><span>Trend ${TREND_START}–${TREND_END} · 50 anni</span><strong class="${direction}">${trendValue}</strong><small>${trendNote}</small></article>
      <article class="climate-summary-card"><span>Ritmo del trend</span><strong>${paceValue}</strong><small>${paceNote}</small></article>
      <article class="climate-summary-card"><span>2025 vs 1991–2020</span><strong>${anomalyValue}</strong><small>${anomalyNote}</small></article>`;

    const confidence = state.metric === 'temperature'
      ? `La retta di tendenza spiega circa il ${fmt(trend.r2 * 100, 0)}% della variabilità nella finestra di 50 anni.`
      : `La pioggia oscilla molto da un anno all'altro: il trend descrive la direzione di fondo, non la singola annualità (R² ${fmt(trend.r2, 2)}).`;
    trendNoteRoot.innerHTML = `<strong>${escapeHtml(state.town)}:</strong> ${state.metric === 'temperature'
      ? `il trend ${TREND_START}–${TREND_END} equivale a ${signed(trend.delta, 2)} °C in 50 anni.`
      : `il trend ${TREND_START}–${TREND_END} equivale a ${signed(trend.percent, 1)}% (${signed(trend.delta, 0)} mm) in 50 anni.`} <span>${confidence}</span>`;
  }

  function renderChart() {
    const series = state.data.municipalities[state.town];
    const years = series.years;
    const values = series[state.metric];
    const smooth = movingAverage(values, 10);
    const trend = linearTrend(years, values);
    const width = 1040, height = 410, left = 64, right = 20, top = 31, bottom = 48;
    const plotW = width - left - right, plotH = height - top - bottom;
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    let padding = (rawMax - rawMin) * .10;
    if (!padding) padding = 1;
    let yMin = rawMin - padding, yMax = rawMax + padding;
    if (state.metric === 'precipitation') yMin = Math.max(0, yMin);
    const x = year => left + (year - years[0]) / (years.at(-1) - years[0]) * plotW;
    const y = value => top + (yMax - value) / (yMax - yMin) * plotH;
    const path = arr => arr.map((value, index) => Number.isFinite(value) ? `${index === 0 || !Number.isFinite(arr[index - 1]) ? 'M' : 'L'}${x(years[index]).toFixed(1)},${y(value).toFixed(1)}` : '').join(' ');
    const ticks = Array.from({ length: 5 }, (_, i) => yMin + (yMax - yMin) * i / 4);
    const xTicks = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2025];
    const bands = state.data.provenance.map(seg => {
      const x1 = x(seg.from), x2 = x(seg.to + (seg.to < years.at(-1) ? 1 : 0));
      const cls = seg.class === 'INTERPOLATED_OBSERVATIONS' ? 'climate-source-band-lamma' : 'climate-source-band-era5';
      const short = seg.class === 'INTERPOLATED_OBSERVATIONS' ? 'LaMMA · interpolato' : 'ERA5-Land · rianalisi calibrata';
      return `<rect class="${cls}" x="${x1}" y="${top}" width="${Math.max(0, x2 - x1)}" height="${plotH}"></rect><text class="climate-source-label" x="${x1 + 7}" y="${top + 13}">${short}</text>`;
    }).join('');
    const grids = ticks.map(value => `<line class="climate-grid-line" x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}"></line><text class="climate-axis-label" x="${left - 10}" y="${y(value) + 3}" text-anchor="end">${state.metric === 'temperature' ? fmt(value, 1) : fmt(value, 0)}</text>`).join('');
    const labels = xTicks.map(year => `<text class="climate-axis-label" x="${x(year)}" y="${height - 14}" text-anchor="middle">${year}</text>`).join('');
    const points = values.map((value, index) => `<circle class="climate-series-point" cx="${x(years[index])}" cy="${y(value)}" r="2.4"></circle><circle class="climate-series-hit" data-year="${years[index]}" data-value="${value}" cx="${x(years[index])}" cy="${y(value)}" r="8"></circle>`).join('');
    const trendPath = trend ? `<line class="climate-trend-line" x1="${x(TREND_START)}" y1="${y(trend.startValue)}" x2="${x(TREND_END)}" y2="${y(trend.endValue)}"></line>` : '';
    const trendMarker = `<line class="climate-trend-boundary" x1="${x(TREND_START)}" x2="${x(TREND_START)}" y1="${top}" y2="${height - bottom}"></line>`;

    chartRoot.className = `climate-chart-wrap metric-${state.metric}`;
    chartRoot.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(meta[state.metric].label)} a ${escapeHtml(state.town)} dal 1950 al 2025">${bands}${grids}${trendMarker}${labels}<path class="climate-series-line" d="${path(values)}"></path>${state.smooth ? `<path class="climate-smooth-line" d="${path(smooth)}"></path>` : ''}${trendPath}${points}</svg>`;
    chartTitle.textContent = meta[state.metric].label;
    chartUnit.textContent = meta[state.metric].unit;

    chartRoot.querySelectorAll('.climate-series-hit').forEach(hit => {
      const show = event => {
        const year = Number(hit.dataset.year), value = Number(hit.dataset.value);
        const prov = state.data.provenance.find(p => year >= p.from && year <= p.to);
        tooltip.innerHTML = `<span>${escapeHtml(state.town)} · ${year}</span><strong>${state.metric === 'temperature' ? fmt(value, 2) : fmt(value, 0)} ${meta[state.metric].unit}</strong><small>${escapeHtml(prov?.label || '')}</small>`;
        tooltip.hidden = false;
        const px = Math.min(window.innerWidth - 170, Math.max(8, event.clientX + 12));
        const py = Math.min(window.innerHeight - 75, Math.max(8, event.clientY + 12));
        tooltip.style.left = `${px}px`;
        tooltip.style.top = `${py}px`;
      };
      hit.addEventListener('pointerenter', show);
      hit.addEventListener('pointermove', show);
      hit.addEventListener('pointerleave', () => { tooltip.hidden = true; });
    });
  }

  function renderComparison() {
    const rows = Object.entries(state.data.municipalities).map(([town, series]) => {
      const trend = linearTrend(series.years, series[state.metric]);
      const value = state.metric === 'temperature' ? trend.delta : trend.percent;
      return { town, value, absolute: trend.delta };
    }).sort((a, b) => b.value - a.value);
    const min = Math.min(...rows.map(row => row.value)), max = Math.max(...rows.map(row => row.value));
    const span = Math.max(max - min, 0.0001);
    barsRoot.closest('.climate-comparison').classList.toggle('metric-precipitation', state.metric === 'precipitation');
    barsRoot.innerHTML = rows.map(row => {
      const pct = 18 + (row.value - min) / span * 82;
      const value = state.metric === 'temperature' ? `${signed(row.value, 2)} °C` : `${signed(row.value, 1)}%`;
      const title = state.metric === 'temperature' ? 'Variazione stimata del trend in 50 anni' : `${signed(row.absolute, 0)} mm lungo il trend`;
      return `<div class="climate-compare-row ${row.town === state.town ? 'active' : ''}" title="${escapeHtml(title)}"><button type="button" data-town="${escapeHtml(row.town)}">${escapeHtml(row.town)}</button><div class="climate-compare-track"><div class="climate-compare-fill" style="width:${pct.toFixed(1)}%"></div></div><strong class="climate-compare-value">${value}</strong></div>`;
    }).join('');
    barsRoot.querySelectorAll('[data-town]').forEach(button => button.addEventListener('click', () => setTown(button.dataset.town)));
  }

  function minMaxPath(years, values, x, y) {
    return values.map((value, index) => `${index === 0 ? 'M' : 'L'}${x(years[index]).toFixed(1)},${y(value).toFixed(1)}`).join(' ');
  }

  function renderMinMax() {
    if (!state.minmax || state.metric !== 'temperature') {
      minmaxSection.hidden = true;
      return;
    }
    const series = state.minmax.municipalities[state.town];
    if (!series) {
      minmaxSection.hidden = true;
      return;
    }
    minmaxSection.hidden = false;
    const minTrend = linearTrend(series.years, series.tmin, 1975, 2025);
    const maxTrend = linearTrend(series.years, series.tmax, 1975, 2025);
    minmaxSummaryRoot.innerHTML = `
      <article><span>Minime · trend 1975–2025</span><strong>${signed(minTrend.delta, 2)} °C</strong><small>Media annua delle temperature minime giornaliere territoriali.</small></article>
      <article><span>Massime · trend 1975–2025</span><strong>${signed(maxTrend.delta, 2)} °C</strong><small>Media annua delle temperature massime giornaliere territoriali.</small></article>`;

    const years = series.years;
    const all = [...series.tmin, ...series.tmax];
    const width = 1040, height = 330, left = 64, right = 20, top = 26, bottom = 46;
    const plotW = width - left - right, plotH = height - top - bottom;
    const rawMin = Math.min(...all), rawMax = Math.max(...all);
    const padding = Math.max((rawMax - rawMin) * .08, .4);
    const yMin = rawMin - padding, yMax = rawMax + padding;
    const x = year => left + (year - years[0]) / (years.at(-1) - years[0]) * plotW;
    const y = value => top + (yMax - value) / (yMax - yMin) * plotH;
    const ticks = Array.from({ length: 4 }, (_, i) => yMin + (yMax - yMin) * i / 3);
    const grids = ticks.map(value => `<line class="climate-grid-line" x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}"></line><text class="climate-axis-label" x="${left - 10}" y="${y(value) + 3}" text-anchor="end">${fmt(value, 1)}</text>`).join('');
    const xTicks = [1975, 1985, 1995, 2005, 2015, 2025].map(year => `<text class="climate-axis-label" x="${x(year)}" y="${height - 14}" text-anchor="middle">${year}</text>`).join('');
    const sourceBoundaries = [1995, 2015].map(year => `<line class="climate-trend-boundary" x1="${x(year)}" x2="${x(year)}" y1="${top}" y2="${height - bottom}"></line>`).join('');
    minmaxChartRoot.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Temperature minime e massime medie annue a ${escapeHtml(state.town)} dal 1975 al 2025">${grids}${sourceBoundaries}${xTicks}<path class="climate-min-line" d="${minMaxPath(years, series.tmin, x, y)}"></path><path class="climate-max-line" d="${minMaxPath(years, series.tmax, x, y)}"></path>${series.tmin.map((value, index) => `<circle class="climate-min-point" cx="${x(years[index])}" cy="${y(value)}" r="3"></circle>`).join('')}${series.tmax.map((value, index) => `<circle class="climate-max-point" cx="${x(years[index])}" cy="${y(value)}" r="3"></circle>`).join('')}</svg>`;
  }

  function renderMethod() {
    const method = state.data.method;
    document.getElementById('method-spatial').textContent = method.spatial;
    document.getElementById('method-source').textContent = 'LaMMA resta la fonte primaria nel 1995–2015; ERA5-Land calibrato completa la serie prima e dopo questo intervallo.';
    document.getElementById('method-validation').textContent = method.validation;
    document.getElementById('method-temperature').textContent = method.temperature;
    document.getElementById('method-precipitation').textContent = method.precipitation;
    document.getElementById('climate-source-timeline').innerHTML = state.data.provenance.map(p => `<div class="climate-source-segment ${p.class === 'INTERPOLATED_OBSERVATIONS' ? 'lamma' : 'era5'}"><strong>${p.from}–${p.to} · ${escapeHtml(p.label)}</strong><span>${escapeHtml(p.source)}</span></div>`).join('');
  }

  function renderPartial() {
    const partial = state.data.coverage.partial;
    if (!partial) { partialRoot.hidden = true; return; }
    partialRoot.hidden = false;
    partialRoot.innerHTML = `<span class="overline">Anno in corso · dato parziale</span><h2>${partial.year} fino al ${escapeHtml(partial.coverageEnd)}</h2><p>Il valore in corso non viene trattato come annualità completa e non entra nel confronto con i totali annuali. <strong>${escapeHtml(partial.note || '')}</strong></p>`;
  }

  function updateUrl() {
    const params = new URLSearchParams(location.search);
    params.set('comune', state.town);
    params.set('indicatore', state.metric);
    history.replaceState(null, '', `${location.pathname}?${params}${location.hash}`);
  }

  function setTown(town) {
    if (!state.data.municipalities[town]) return;
    state.town = town;
    townSelect.value = town;
    updateUrl();
    renderAll();
  }

  function setMetric(metric) {
    if (!meta[metric]) return;
    state.metric = metric;
    metricTabs.forEach(button => {
      const active = button.dataset.metric === metric;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    updateUrl();
    renderAll();
  }

  function renderAll() {
    renderSummary();
    renderChart();
    renderComparison();
    renderMinMax();
    renderPartial();
  }

  async function start() {
    const [mainResponse, minmaxResponse] = await Promise.all([
      fetch(DATA_URL, { cache: 'no-store' }),
      fetch(MINMAX_URL, { cache: 'no-store' }).catch(() => null)
    ]);
    if (!mainResponse.ok) throw new Error(`Dati meteo: ${mainResponse.status}`);
    state.data = await mainResponse.json();
    if (minmaxResponse?.ok) state.minmax = await minmaxResponse.json();

    const towns = Object.keys(state.data.municipalities);
    townSelect.innerHTML = towns.map(town => `<option value="${escapeHtml(town)}">${escapeHtml(town)}</option>`).join('');
    const params = new URLSearchParams(location.search);
    const requestedTown = params.get('comune');
    const requestedMetric = params.get('indicatore');
    if (requestedTown && state.data.municipalities[requestedTown]) state.town = requestedTown;
    if (requestedMetric && meta[requestedMetric]) state.metric = requestedMetric;
    townSelect.value = state.town;
    metricTabs.forEach(button => {
      const active = button.dataset.metric === state.metric;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    townSelect.addEventListener('change', () => setTown(townSelect.value));
    metricTabs.forEach(button => button.addEventListener('click', () => setMetric(button.dataset.metric)));
    smoothToggle.addEventListener('click', () => {
      state.smooth = !state.smooth;
      smoothToggle.classList.toggle('active', state.smooth);
      smoothToggle.setAttribute('aria-pressed', state.smooth ? 'true' : 'false');
      renderChart();
    });
    renderMethod();
    renderAll();
  }

  start().catch(error => {
    console.error(error);
    chartRoot.innerHTML = '<div class="app-error"><strong>Impossibile caricare la serie climatica.</strong><p>La bozza richiede un server web locale e i file dati POC.</p></div>';
  });
})();
