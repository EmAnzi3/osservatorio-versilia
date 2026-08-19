(() => {
  'use strict';

  const MAIN_URL = '../../data/meteo-clima-poc.json';
  const MINMAX_URL = '../../data/meteo-clima-minmax-poc.json';
  const STATUS_URL = '../../data/data-status.json';
  const TREND_START = 1975;

  const CONFIG = {
    temperature: {
      canonicalKey: 'climateTemperatureTrend50y', dataset: 'main', seriesKey: 'temperature',
      label: 'Temperatura media annua', short: 'Temperatura media', unit: '°C', decimals: 2,
      sourceLabel: 'LaMMA + Copernicus ERA5-Land'
    },
    tmin: {
      canonicalKey: 'climateTminTrend', dataset: 'minmax', seriesKey: 'tmin',
      label: 'Temperatura minima media annua', short: 'Minima media', unit: '°C', decimals: 2,
      sourceLabel: 'Copernicus ERA5-Land · riferimento LaMMA/SIR'
    },
    tmax: {
      canonicalKey: 'climateTmaxTrend', dataset: 'minmax', seriesKey: 'tmax',
      label: 'Temperatura massima media annua', short: 'Massima media', unit: '°C', decimals: 2,
      sourceLabel: 'Copernicus ERA5-Land · riferimento LaMMA/SIR'
    },
    precipitation: {
      canonicalKey: 'climatePrecipitationTrend50y', dataset: 'main', seriesKey: 'precipitation',
      label: 'Precipitazioni annue', short: 'Precipitazioni', unit: 'mm', decimals: 0,
      sourceLabel: 'LaMMA + Copernicus ERA5-Land'
    }
  };

  const townSelect = document.getElementById('climate-town');
  const chartRoot = document.getElementById('climate-chart');
  const summaryRoot = document.getElementById('climate-summary');
  const compareRoot = document.getElementById('climate-compare-bars');
  const tooltip = document.getElementById('climate-tooltip');
  const smoothToggle = document.getElementById('climate-smooth-toggle');
  const metricTabs = [...document.querySelectorAll('[data-metric]')];
  const chartTitle = document.getElementById('climate-chart-title');
  const chartUnit = document.getElementById('climate-chart-unit');
  const trendNote = document.getElementById('climate-trend-note');
  const methodSource = document.getElementById('method-source');
  const methodValidation = document.getElementById('method-validation');
  const methodSpatial = document.getElementById('method-spatial');
  const statusSection = document.getElementById('climate-status');
  const statusList = document.getElementById('climate-status-list');

  const state = { town: 'Massarosa', metric: 'temperature', smooth: true, main: null, minmax: null, status: null };
  const nf = new Map();
  const formatter = decimals => {
    if (!nf.has(decimals)) nf.set(decimals, new Intl.NumberFormat('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }));
    return nf.get(decimals);
  };
  const fmt = (value, decimals = 1) => formatter(decimals).format(Number(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c]));
  const signed = (value, decimals = 1, suffix = '') => `${Number(value) > 0 ? '+' : ''}${fmt(value, decimals)}${suffix}`;

  function datasetFor(config = CONFIG[state.metric]) {
    return config.dataset === 'minmax' ? state.minmax : state.main;
  }

  function seriesFor(town = state.town, config = CONFIG[state.metric]) {
    return datasetFor(config)?.municipalities?.[town] || null;
  }

  function latestYear(series) {
    return Number(series?.latestComplete?.year || series?.years?.at(-1));
  }

  function currentValue(series, config = CONFIG[state.metric]) {
    const explicit = series?.latestComplete?.[config.seriesKey];
    if (Number.isFinite(Number(explicit))) return Number(explicit);
    return Number(series?.[config.seriesKey]?.at(-1));
  }

  function movingAverage(values, windowSize = 10) {
    return values.map((_, index) => {
      if (index < windowSize - 1) return null;
      const slice = values.slice(index - windowSize + 1, index + 1).map(Number).filter(Number.isFinite);
      return slice.length === windowSize ? slice.reduce((sum, value) => sum + value, 0) / windowSize : null;
    });
  }

  function linearTrend(years, values, start = TREND_START, end = Number(years.at(-1))) {
    const points = years.map((year, index) => ({ year: Number(year), value: Number(values[index]) }))
      .filter(point => point.year >= start && point.year <= end && Number.isFinite(point.value));
    if (points.length < 3) return null;
    const meanX = points.reduce((sum, point) => sum + point.year, 0) / points.length;
    const meanY = points.reduce((sum, point) => sum + point.value, 0) / points.length;
    const denominator = points.reduce((sum, point) => sum + (point.year - meanX) ** 2, 0);
    if (!denominator) return null;
    const slope = points.reduce((sum, point) => sum + (point.year - meanX) * (point.value - meanY), 0) / denominator;
    const intercept = meanY - slope * meanX;
    const fitted = points.map(point => intercept + slope * point.year);
    const ssTot = points.reduce((sum, point) => sum + (point.value - meanY) ** 2, 0);
    const ssRes = points.reduce((sum, point, index) => sum + (point.value - fitted[index]) ** 2, 0);
    const startValue = intercept + slope * start;
    const endValue = intercept + slope * end;
    return {
      start, end, slope, intercept, startValue, endValue,
      delta: endValue - startValue,
      perDecade: slope * 10,
      percent: startValue !== 0 ? (endValue - startValue) / Math.abs(startValue) * 100 : null,
      r2: ssTot > 0 ? Math.max(0, 1 - ssRes / ssTot) : 0
    };
  }

  function sourceSegments(config, years) {
    if (config.dataset === 'main') return state.main?.provenance || [];
    return (state.minmax?.sourcePeriods || []).map(period => ({
      from: period.from,
      to: period.to,
      class: period.class,
      label: 'ERA5-Land · rianalisi calibrata',
      source: period.detail
    })).filter(period => period.to >= years[0] && period.from <= years.at(-1));
  }

  function sourceForYear(year, config, years) {
    return sourceSegments(config, years).find(item => year >= item.from && year <= item.to);
  }

  function formatValue(value, config = CONFIG[state.metric]) {
    return config.unit === 'mm' ? `${fmt(value, 0)} mm` : `${fmt(value, config.decimals)} °C`;
  }

  function renderFacts() {
    const mainFrom = Number(state.main.coverage.complete.from);
    const mainTo = Number(state.main.coverage.complete.to);
    const trendTo = Math.min(mainTo, Number(state.minmax?.coverage?.to || mainTo));
    document.getElementById('climate-complete-coverage').textContent = `${mainFrom}–${mainTo}`;
    document.getElementById('climate-trend-coverage').textContent = `${TREND_START}–${trendTo}`;
    document.getElementById('climate-latest-year').textContent = String(trendTo);
  }

  function renderSummary() {
    const config = CONFIG[state.metric];
    const series = seriesFor();
    if (!series) return;
    const end = latestYear(series);
    const trend = linearTrend(series.years, series[config.seriesKey], TREND_START, end);
    if (!trend) return;
    const current = currentValue(series, config);
    const trendValue = config.unit === 'mm' ? signed(trend.percent, 1, '%') : signed(trend.delta, 2, ' °C');
    const paceValue = config.unit === 'mm' ? signed(trend.perDecade, 0, ' mm') : signed(trend.perDecade, 2, ' °C');
    const trendDetail = config.unit === 'mm'
      ? `${signed(trend.delta, 0, ' mm')} lungo la retta di tendenza.`
      : `Differenza stimata dalla retta ai due estremi.`;
    summaryRoot.innerHTML = `
      <article class="climate-summary-card climate-summary-primary"><span>Ultimo anno completo · ${end}</span><strong>${esc(formatValue(current, config))}</strong><small>Valore territoriale comunale pubblicato.</small></article>
      <article class="climate-summary-card"><span>Trend ${TREND_START}–${end}</span><strong>${esc(trendValue)}</strong><small>${esc(trendDetail)}</small></article>
      <article class="climate-summary-card"><span>Ritmo del trend</span><strong>${esc(paceValue)}</strong><small>Variazione media della retta per decennio.</small></article>`;
    const interpretation = config.unit === 'mm'
      ? `Le precipitazioni restano molto variabili da un anno all'altro: R² ${fmt(trend.r2, 2)}.`
      : `La retta spiega circa il ${fmt(trend.r2 * 100, 0)}% della variabilità nella finestra considerata.`;
    trendNote.innerHTML = `<strong>${esc(state.town)}:</strong> il trend ${TREND_START}–${end} di ${esc(config.short.toLowerCase())} è ${esc(trendValue)}. <span>${esc(interpretation)} È una sintesi descrittiva, non un test di significatività.</span>`;
  }

  function renderChart() {
    const config = CONFIG[state.metric];
    const series = seriesFor();
    if (!series) return;
    const years = series.years.map(Number);
    const values = series[config.seriesKey].map(Number);
    const smooth = movingAverage(values, 10);
    const end = latestYear(series);
    const trend = linearTrend(years, values, TREND_START, end);
    const width = 1040, height = 410, left = 68, right = 22, top = 31, bottom = 48;
    const plotW = width - left - right, plotH = height - top - bottom;
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    const pad = Math.max((rawMax - rawMin) * .10, config.unit === 'mm' ? 50 : .3);
    const yMin = config.unit === 'mm' ? Math.max(0, rawMin - pad) : rawMin - pad;
    const yMax = rawMax + pad;
    const x = year => left + (year - years[0]) / (years.at(-1) - years[0]) * plotW;
    const y = value => top + (yMax - value) / (yMax - yMin) * plotH;
    const path = arr => arr.map((value, index) => Number.isFinite(value)
      ? `${index === 0 || !Number.isFinite(arr[index - 1]) ? 'M' : 'L'}${x(years[index]).toFixed(1)},${y(value).toFixed(1)}` : '').join(' ');
    const ticks = Array.from({ length: 5 }, (_, index) => yMin + (yMax - yMin) * index / 4);
    const grids = ticks.map(value => `<line class="climate-grid-line" x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}"></line><text class="climate-axis-label" x="${left - 10}" y="${y(value) + 3}" text-anchor="end">${config.unit === 'mm' ? fmt(value, 0) : fmt(value, 1)}</text>`).join('');
    const candidates = [years[0], 1960, 1970, 1975, 1980, 1990, 2000, 2010, 2020, end];
    const xTicks = [...new Set(candidates.filter(year => year >= years[0] && year <= end))];
    const labels = xTicks.map(year => `<text class="climate-axis-label" x="${x(year)}" y="${height - 14}" text-anchor="middle">${year}</text>`).join('');
    const segments = sourceSegments(config, years);
    const bands = segments.map(segment => {
      const from = Math.max(segment.from, years[0]);
      const to = Math.min(segment.to, end);
      const x1 = x(from), x2 = x(to + (to < end ? 1 : 0));
      const cls = segment.class === 'INTERPOLATED_OBSERVATIONS' ? 'climate-source-band-lamma' : 'climate-source-band-era5';
      return `<rect class="${cls}" x="${x1}" y="${top}" width="${Math.max(0, x2 - x1)}" height="${plotH}"></rect>`;
    }).join('');
    const points = values.map((value, index) => `<circle class="climate-series-point" cx="${x(years[index])}" cy="${y(value)}" r="2.4"></circle><circle class="climate-series-hit" data-index="${index}" cx="${x(years[index])}" cy="${y(value)}" r="9"></circle>`).join('');
    const trendLine = trend ? `<line class="climate-trend-line" x1="${x(TREND_START)}" y1="${y(trend.startValue)}" x2="${x(end)}" y2="${y(trend.endValue)}"></line>` : '';
    const boundary = years[0] < TREND_START ? `<line class="climate-trend-boundary" x1="${x(TREND_START)}" x2="${x(TREND_START)}" y1="${top}" y2="${height - bottom}"></line>` : '';
    chartRoot.className = `climate-chart-wrap metric-${state.metric}`;
    chartRoot.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(config.label)} a ${esc(state.town)} dal ${years[0]} al ${end}">${bands}${grids}${boundary}${labels}<path class="climate-series-line" d="${path(values)}"></path>${state.smooth ? `<path class="climate-smooth-line" d="${path(smooth)}"></path>` : ''}${trendLine}${points}</svg>`;
    chartTitle.textContent = config.label;
    chartUnit.textContent = config.unit;

    chartRoot.querySelectorAll('.climate-series-hit').forEach(hit => {
      const show = event => {
        const index = Number(hit.dataset.index);
        const year = years[index], value = values[index];
        const source = sourceForYear(year, config, years);
        tooltip.innerHTML = `<span>${esc(state.town)} · ${year}</span><strong>${esc(formatValue(value, config))}</strong><small>${esc(source?.label || config.sourceLabel)}</small>`;
        tooltip.hidden = false;
        tooltip.style.left = `${Math.min(window.innerWidth - 190, Math.max(8, event.clientX + 12))}px`;
        tooltip.style.top = `${Math.min(window.innerHeight - 85, Math.max(8, event.clientY + 12))}px`;
      };
      hit.addEventListener('pointerenter', show);
      hit.addEventListener('pointermove', show);
      hit.addEventListener('pointerleave', () => { tooltip.hidden = true; });
    });
  }

  function renderComparison() {
    const config = CONFIG[state.metric];
    const dataset = datasetFor(config);
    const rows = Object.entries(dataset.municipalities).map(([town, series]) => {
      const end = latestYear(series);
      const trend = linearTrend(series.years, series[config.seriesKey], TREND_START, end);
      const value = config.unit === 'mm' ? trend.percent : trend.delta;
      return { town, value, absolute: trend.delta };
    }).sort((a, b) => a.town.localeCompare(b.town, 'it'));
    const values = rows.map(row => row.value);
    const min = Math.min(...values), max = Math.max(...values), span = Math.max(max - min, .0001);
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const meanPosition = (mean - min) / span * 100;
    compareRoot.closest('.climate-comparison').classList.toggle('metric-precipitation', config.unit === 'mm');
    compareRoot.innerHTML = `<div class="climate-compare-legend"><span><i class="climate-compare-dot"></i>Comune</span><span><i class="climate-compare-mean"></i>Media semplice dei 7 trend</span></div>${rows.map(row => {
      const position = (row.value - min) / span * 100;
      const value = config.unit === 'mm' ? signed(row.value, 1, '%') : signed(row.value, 2, ' °C');
      const title = config.unit === 'mm' ? `${signed(row.absolute, 0, ' mm')} lungo il trend` : 'Variazione stimata del trend';
      return `<div class="climate-compare-row ${row.town === state.town ? 'active' : ''}" title="${esc(title)}"><button type="button" data-town="${esc(row.town)}">${esc(row.town)}</button><div class="climate-compare-track" style="--mean:${meanPosition.toFixed(2)}%;--value:${position.toFixed(2)}%"><i class="climate-compare-marker"></i></div><strong class="climate-compare-value">${esc(value)}</strong></div>`;
    }).join('')}`;
    compareRoot.querySelectorAll('[data-town]').forEach(button => button.addEventListener('click', () => setTown(button.dataset.town)));
  }

  function renderMethod() {
    const config = CONFIG[state.metric];
    if (config.dataset === 'minmax') {
      methodSpatial.textContent = 'Media territoriale comunale con pesatura frazionaria delle celle sulla superficie amministrativa.';
      methodSource.textContent = 'Serie ERA5-Land continua nel tempo; LaMMA è usato come riferimento del livello con un offset comunale costante, senza correggere la pendenza.';
      methodValidation.textContent = 'Le osservazioni SIR disponibili sono un controllo indipendente del comportamento temporale: supportano la scelta metodologica, ma non trasformano la rianalisi in un dato osservato comunale.';
    } else {
      methodSpatial.textContent = state.main.method.spatial;
      methodSource.textContent = `${state.main.method[config.seriesKey]} La serie oggi pubblicata usa LaMMA nel periodo comune e ERA5-Land calibrato fuori dall’overlap; il candidato omogeneo è sottoposto a audit separato prima di qualunque sostituzione.`;
      methodValidation.textContent = `${state.main.method.validation} Il confronto è evidenza di coerenza temporale, non una certificazione assoluta del livello comunale.`;
    }
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('it-IT', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
  }

  function renderStatus() {
    if (!state.status?.metrics || !statusList || !statusSection) return;
    const byKey = new Map(state.status.metrics.map(item => [item.key, item]));
    const rows = Object.values(CONFIG).map(config => byKey.get(config.canonicalKey)).filter(Boolean);
    if (rows.length !== 4) return;
    statusList.innerHTML = rows.map(item => `<article><span>${esc(item.label)}</span><strong>${esc(item.publishedPeriod || '—')}</strong><small>${esc(item.statusLabel)} · controllo ${esc(formatDate(item.lastChecked))}</small><a href="../ambiente/?indicatore=${encodeURIComponent(item.key)}">Apri indicatore →</a></article>`).join('');
    statusSection.hidden = false;
  }

  function updateUrl() {
    const params = new URLSearchParams(location.search);
    params.set('comune', state.town);
    params.set('indicatore', state.metric);
    history.replaceState(null, '', `${location.pathname}?${params}${location.hash}`);
  }

  function setTown(town) {
    if (!state.main.municipalities[town]) return;
    state.town = town;
    townSelect.value = town;
    updateUrl();
    renderAll();
  }

  function setMetric(metric) {
    if (!CONFIG[metric]) return;
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
    renderMethod();
  }

  async function start() {
    const [mainResponse, minmaxResponse, statusResponse] = await Promise.all([
      fetch(MAIN_URL, { cache: 'no-store' }),
      fetch(MINMAX_URL, { cache: 'no-store' }),
      fetch(STATUS_URL, { cache: 'no-store' }).catch(() => null)
    ]);
    if (!mainResponse.ok || !minmaxResponse.ok) throw new Error('Dataset climatici non disponibili');
    state.main = await mainResponse.json();
    state.minmax = await minmaxResponse.json();
    if (statusResponse?.ok) state.status = await statusResponse.json();

    const towns = Object.keys(state.main.municipalities).sort((a, b) => a.localeCompare(b, 'it'));
    townSelect.innerHTML = towns.map(town => `<option value="${esc(town)}">${esc(town)}</option>`).join('');
    const params = new URLSearchParams(location.search);
    const requestedTown = params.get('comune');
    const requestedMetric = params.get('indicatore');
    if (requestedTown && state.main.municipalities[requestedTown]) state.town = requestedTown;
    if (requestedMetric && CONFIG[requestedMetric]) state.metric = requestedMetric;
    townSelect.value = state.town;
    metricTabs.forEach(button => {
      const active = button.dataset.metric === state.metric;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.addEventListener('click', () => setMetric(button.dataset.metric));
    });
    townSelect.addEventListener('change', () => setTown(townSelect.value));
    smoothToggle.addEventListener('click', () => {
      state.smooth = !state.smooth;
      smoothToggle.classList.toggle('active', state.smooth);
      smoothToggle.setAttribute('aria-pressed', state.smooth ? 'true' : 'false');
      renderChart();
    });
    renderFacts();
    renderStatus();
    renderAll();
  }

  start().catch(error => {
    console.error(error);
    chartRoot.innerHTML = '<div class="app-error"><strong>Impossibile caricare la serie climatica.</strong><p>Verifica i dataset pubblicati e riprova.</p></div>';
  });
})();
