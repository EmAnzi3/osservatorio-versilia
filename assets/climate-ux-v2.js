(() => {
  'use strict';

  const loader = document.currentScript;
  const ROOT = new URL('../', loader?.src || location.href);
  const COLORS = ['#0f5c6e', '#b56843', '#64743d', '#855b7b', '#b88a1c', '#4e7096', '#914d47'];
  const KEYS = new Set([
    'climateTemperatureTrend50y',
    'climatePrecipitationTrend50y',
    'climateTminTrend',
    'climateTmaxTrend'
  ]);

  const configs = {
    climateTemperatureTrend50y: {
      label: 'Temperatura media annua', shortLabel: 'Temperatura media', seriesKey: 'temperature',
      unit: 'celsius', latestYear: 2025, trendFrom: 1975, trendTo: 2025,
      source: 'LaMMA + Copernicus ERA5-Land', sourceUrl: 'https://dati.lamma.toscana.it/',
      description: 'Temperatura media del territorio comunale nell’ultimo anno completo disponibile (2025).',
      explanation: 'Ogni valore è la temperatura media dell’intero anno sul territorio comunale. Non misura l’aumento climatico: quello è mostrato separatamente nello storico dalla linea di trend 1975–2025.'
    },
    climatePrecipitationTrend50y: {
      label: 'Precipitazioni annue', shortLabel: 'Precipitazioni annue', seriesKey: 'precipitation',
      unit: 'mm', latestYear: 2025, trendFrom: 1975, trendTo: 2025,
      source: 'LaMMA + Copernicus ERA5-Land', sourceUrl: 'https://dati.lamma.toscana.it/',
      description: 'Totale delle precipitazioni sul territorio comunale nell’ultimo anno completo disponibile (2025).',
      explanation: 'Ogni valore è il totale annuo di precipitazione. Le forti oscillazioni tra un anno e l’altro sono normali; la linea di trend 1975–2025 serve a leggere la direzione di fondo.'
    },
    climateTminTrend: {
      label: 'Temperatura minima media annua', shortLabel: 'Temperatura minima media', seriesKey: 'tmin',
      unit: 'celsius', latestYear: 2015, trendFrom: 1995, trendTo: 2015,
      source: 'Consorzio LaMMA — raster giornalieri 1 km', sourceUrl: 'https://dati.lamma.toscana.it/',
      description: 'Media annua delle temperature minime giornaliere sul territorio comunale nell’ultimo anno omogeneo disponibile (2015).',
      explanation: 'Non è la temperatura più bassa raggiunta nell’anno. È la media delle temperature minime di ciascun giorno; la serie omogenea disponibile copre il 1995–2015.'
    },
    climateTmaxTrend: {
      label: 'Temperatura massima media annua', shortLabel: 'Temperatura massima media', seriesKey: 'tmax',
      unit: 'celsius', latestYear: 2015, trendFrom: 1995, trendTo: 2015,
      source: 'Consorzio LaMMA — raster giornalieri 1 km', sourceUrl: 'https://dati.lamma.toscana.it/',
      description: 'Media annua delle temperature massime giornaliere sul territorio comunale nell’ultimo anno omogeneo disponibile (2015).',
      explanation: 'Non è la temperatura più alta raggiunta nell’anno. È la media delle temperature massime di ciascun giorno; la serie omogenea disponibile copre il 1995–2015.'
    }
  };

  const fmt1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const fmt2 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmt0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 });
  const escapeHtml = value => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const slug = value => String(value || '').toLocaleLowerCase('it').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const formatValue = (value, unit) => unit === 'mm'
    ? `${fmt0.format(Number(value))} mm`
    : `${fmt2.format(Number(value))} °C`;
  const formatSigned = (value, unit) => `${Number(value) > 0 ? '+' : ''}${formatValue(value, unit)}`;

  function linearTrend(years, values, fromYear, toYear) {
    const pairs = years.map((year, index) => ({ year: Number(year), value: Number(values[index]) }))
      .filter(item => item.year >= fromYear && item.year <= toYear && Number.isFinite(item.value));
    if (pairs.length < 2) return null;
    const mx = pairs.reduce((sum, item) => sum + item.year, 0) / pairs.length;
    const my = pairs.reduce((sum, item) => sum + item.value, 0) / pairs.length;
    const den = pairs.reduce((sum, item) => sum + (item.year - mx) ** 2, 0);
    if (!den) return null;
    const slope = pairs.reduce((sum, item) => sum + (item.year - mx) * (item.value - my), 0) / den;
    const intercept = my - slope * mx;
    const start = intercept + slope * fromYear;
    const end = intercept + slope * toYear;
    return { fromYear, toYear, start, end, delta: end - start, perDecade: slope * 10, percent: start ? (end - start) / start * 100 : null };
  }

  function injectStyles() {
    if (document.getElementById('ov-climate-v2-style')) return;
    const style = document.createElement('style');
    style.id = 'ov-climate-v2-style';
    style.textContent = `
      .ov-climate-v2-active .versilia-position{display:none!important}
      .ov-climate-v2-active .town-metric-layout{grid-template-columns:minmax(0,1fr)!important}
      .ov-climate-current-list{display:grid;gap:10px}
      .ov-climate-current-row{display:grid;grid-template-columns:minmax(120px,180px) minmax(160px,1fr) minmax(90px,auto);gap:12px;align-items:center;color:inherit;text-decoration:none;padding:7px 0}
      .ov-climate-current-row .town{font-size:12px;font-weight:720}.ov-climate-current-row strong{font-family:var(--font-geist-mono),monospace;font-size:12px;text-align:right}
      .ov-climate-current-track{position:relative;height:9px;border-radius:999px;background:color-mix(in srgb,var(--ink) 7%,transparent)}
      .ov-climate-current-track i{position:absolute;top:50%;width:11px;height:11px;margin:-5.5px 0 0 -5.5px;border-radius:50%;background:var(--theme-color,#4f8162)}
      .ov-climate-view-note{margin:0 0 14px;color:var(--muted);font-size:11px;line-height:1.55}
      .ov-climate-history{display:grid;gap:14px}.ov-climate-history-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.ov-climate-history-head strong{display:block;font-size:13px}.ov-climate-history-head span{display:block;color:var(--muted);font-size:10px;line-height:1.45;margin-top:4px;max-width:680px}
      .ov-climate-chart-scroll{overflow-x:auto}.ov-climate-chart{min-width:720px}.ov-climate-chart svg{display:block;width:100%;height:auto;overflow:visible}
      .ov-climate-grid{stroke:color-mix(in srgb,var(--ink) 10%,transparent);stroke-width:1}.ov-climate-axis{fill:var(--muted);font-size:10px;font-family:var(--font-geist-mono),monospace}
      .ov-climate-annual{fill:none;stroke:var(--ink);stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;opacity:.75}.ov-climate-point{fill:var(--surface,#fffaf1);stroke:var(--ink);stroke-width:1.5}
      .ov-climate-trend{stroke:var(--theme-color,#4f8162);stroke-width:3;stroke-dasharray:9 7;stroke-linecap:round}
      .ov-climate-key{display:flex;flex-wrap:wrap;gap:12px 22px;color:var(--muted);font-size:10px}.ov-climate-key span{display:inline-flex;align-items:center;gap:7px}.ov-climate-key i{width:27px;border-top:2px solid var(--ink)}.ov-climate-key i.trend{border-top-style:dashed;border-top-color:var(--theme-color,#4f8162)}
      .ov-climate-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid color-mix(in srgb,var(--ink) 12%,transparent);padding-top:12px}.ov-climate-summary article{padding:4px 16px 4px 0;border-right:1px solid color-mix(in srgb,var(--ink) 10%,transparent)}.ov-climate-summary article+article{padding-left:16px}.ov-climate-summary article:last-child{border-right:0}.ov-climate-summary span,.ov-climate-summary small{display:block;color:var(--muted);font-size:9px;line-height:1.45}.ov-climate-summary strong{display:block;margin:6px 0 2px;font:700 20px var(--font-geist-mono),monospace}
      .ov-climate-compare-lines .series{fill:none;stroke:var(--series-color);stroke-width:2;opacity:.48}.ov-climate-compare-lines .trend{stroke:var(--series-color);stroke-width:2;stroke-dasharray:8 7;opacity:.28}.ov-climate-compare-lines.has-selection g:not(.selected) .series{opacity:.1}.ov-climate-compare-lines.has-selection g:not(.selected) .trend{opacity:.04}.ov-climate-compare-lines.has-selection g.selected .series{opacity:1;stroke-width:2.8}.ov-climate-compare-lines.has-selection g.selected .trend{opacity:1;stroke-width:3}
      .ov-climate-legend{display:flex;flex-wrap:wrap;gap:7px}.ov-climate-legend button{border:1px solid color-mix(in srgb,var(--ink) 14%,transparent);border-radius:999px;padding:7px 10px;background:transparent;color:var(--muted);font-size:10px}.ov-climate-legend button::before{content:'';display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--series-color);margin-right:6px}.ov-climate-legend button[aria-pressed=true]{color:var(--ink);border-color:var(--series-color);background:color-mix(in srgb,var(--series-color) 8%,transparent)}
      .ov-climate-selection-summary{min-height:38px;border-top:1px solid color-mix(in srgb,var(--ink) 10%,transparent);padding-top:11px;color:var(--muted);font-size:11px}.ov-climate-selection-summary strong{color:var(--ink)}
      @media(max-width:700px){.ov-climate-current-row{grid-template-columns:minmax(95px,125px) minmax(90px,1fr)}.ov-climate-current-row strong{grid-column:1/3;justify-self:end}.ov-climate-summary{grid-template-columns:1fr}.ov-climate-summary article,.ov-climate-summary article+article{padding:9px 0;border-right:0;border-bottom:1px solid color-mix(in srgb,var(--ink) 10%,transparent)}.ov-climate-summary article:last-child{border-bottom:0}.ov-climate-history-head{flex-direction:column}}
    `;
    document.head.appendChild(style);
  }

  async function loadData() {
    const [site, climate, minmax] = await Promise.all([
      fetch(new URL('data/site-data.json', ROOT)).then(r => r.json()),
      fetch(new URL('data/meteo-clima-poc.json', ROOT)).then(r => r.json()),
      fetch(new URL('data/meteo-clima-minmax-poc.json', ROOT)).then(r => r.json())
    ]);
    return { site, climate, minmax };
  }

  function rowsFor(data, key) {
    const cfg = configs[key];
    const source = key === 'climateTminTrend' || key === 'climateTmaxTrend' ? data.minmax : data.climate;
    return Object.entries(source.municipalities).map(([town, series]) => {
      const values = series[cfg.seriesKey];
      const latestIndex = series.years.findIndex(y => Number(y) === cfg.latestYear);
      const latest = Number(values[latestIndex >= 0 ? latestIndex : values.length - 1]);
      const trend = linearTrend(series.years, values, cfg.trendFrom, cfg.trendTo);
      return { town, slug: slug(town), years: series.years.map(Number), values: values.map(Number), value: latest, trend };
    }).sort((a, b) => a.town.localeCompare(b.town, 'it'));
  }

  function currentListMarkup(rows, cfg, selectedSlug = '') {
    const values = rows.map(r => r.value);
    const min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
    return `<div class="ov-climate-current-list">${rows.map(row => {
      const pos = (row.value - min) / range * 100;
      const href = new URL(`comuni/${row.slug}/?tema=ambiente&indicatore=${encodeURIComponent(currentKey())}`, ROOT).href;
      return `<a class="ov-climate-current-row ${row.slug === selectedSlug ? 'selected' : ''}" href="${href}"><span class="town">${escapeHtml(row.town)}</span><span class="ov-climate-current-track"><i style="left:${pos.toFixed(2)}%"></i></span><strong>${escapeHtml(formatValue(row.value, cfg.unit))}</strong></a>`;
    }).join('')}</div>`;
  }

  function chartScale(allValues, width = 920, height = 390) {
    const left = 78, right = 30, top = 28, bottom = 55;
    const rawMin = Math.min(...allValues), rawMax = Math.max(...allValues);
    const padding = (rawMax - rawMin || Math.max(Math.abs(rawMax) * .1, 1)) * .1;
    const min = rawMin - padding, max = rawMax + padding, range = max - min || 1;
    return { width, height, left, right, top, bottom, min, max, range,
      y: value => top + (max - value) / range * (height - top - bottom) };
  }

  function gridMarkup(scale, cfg) {
    const chartHeight = scale.height - scale.top - scale.bottom;
    return [0, .25, .5, .75, 1].map(f => {
      const y = scale.top + f * chartHeight;
      const value = scale.max - f * scale.range;
      return `<line class="ov-climate-grid" x1="${scale.left}" y1="${y}" x2="${scale.width - scale.right}" y2="${y}"></line><text class="ov-climate-axis" x="${scale.left - 10}" y="${y + 4}" text-anchor="end">${escapeHtml(formatValue(value, cfg.unit))}</text>`;
    }).join('');
  }

  function yearLabels(years, x, height) {
    const target = years.length > 40 ? 8 : 6;
    const step = Math.max(1, Math.ceil((years.length - 1) / target));
    return years.map((year, i) => (i === 0 || i === years.length - 1 || i % step === 0)
      ? `<text class="ov-climate-axis" x="${x(i)}" y="${height - 17}" text-anchor="middle">${year}</text>` : '').join('');
  }

  function townHistoryMarkup(row, cfg) {
    const all = [...row.values, row.trend.start, row.trend.end].filter(Number.isFinite);
    const scale = chartScale(all);
    const chartWidth = scale.width - scale.left - scale.right;
    const x = i => scale.left + i * chartWidth / Math.max(1, row.years.length - 1);
    const line = row.values.map((v, i) => `${x(i)},${scale.y(v)}`).join(' ');
    const points = row.values.map((v, i) => `<circle class="ov-climate-point" cx="${x(i)}" cy="${scale.y(v)}" r="3"><title>${row.years[i]}: ${escapeHtml(formatValue(v, cfg.unit))}</title></circle>`).join('');
    const startIndex = Math.max(0, row.years.findIndex(y => y >= cfg.trendFrom));
    let endIndex = row.years.findIndex(y => y >= cfg.trendTo); if (endIndex < 0) endIndex = row.years.length - 1;
    const pct = cfg.unit === 'mm' && Number.isFinite(row.trend.percent) ? `${row.trend.percent > 0 ? '+' : ''}${fmt1.format(row.trend.percent)}%` : '';
    return `<div class="ov-climate-history"><div class="ov-climate-history-head"><div><strong>${escapeHtml(row.town)} · ${escapeHtml(cfg.label)}</strong><span>${escapeHtml(cfg.explanation)}</span></div><span>Fonte: ${escapeHtml(cfg.source)}</span></div><div class="ov-climate-key"><span><i></i>Valore annuale</span><span><i class="trend"></i>Trend lineare ${cfg.trendFrom}–${cfg.trendTo}</span></div><div class="ov-climate-chart-scroll"><div class="ov-climate-chart"><svg viewBox="0 0 ${scale.width} ${scale.height}" role="img" aria-label="${escapeHtml(`${cfg.label} a ${row.town}: serie annuale e trend`)}">${gridMarkup(scale, cfg)}<polyline class="ov-climate-annual" points="${line}"></polyline><line class="ov-climate-trend" x1="${x(startIndex)}" y1="${scale.y(row.trend.start)}" x2="${x(endIndex)}" y2="${scale.y(row.trend.end)}"></line>${points}${yearLabels(row.years, x, scale.height)}</svg></div></div><div class="ov-climate-summary"><article><span>Ultimo dato disponibile · ${cfg.latestYear}</span><strong>${escapeHtml(formatValue(row.value, cfg.unit))}</strong></article><article><span>Variazione del trend · ${cfg.trendFrom}–${cfg.trendTo}</span><strong>${escapeHtml(formatSigned(row.trend.delta, cfg.unit))}</strong>${pct ? `<small>${escapeHtml(pct)} sul livello stimato iniziale</small>` : ''}</article><article><span>Trend medio per decennio</span><strong>${escapeHtml(formatSigned(row.trend.perDecade, cfg.unit))}</strong></article></div></div>`;
  }

  function compareHistoryMarkup(rows, cfg) {
    const years = rows[0].years;
    const all = rows.flatMap(r => [...r.values, r.trend.start, r.trend.end]);
    const scale = chartScale(all);
    const chartWidth = scale.width - scale.left - scale.right;
    const x = i => scale.left + i * chartWidth / Math.max(1, years.length - 1);
    const groups = rows.map((row, index) => {
      const line = row.values.map((v, i) => `${x(i)},${scale.y(v)}`).join(' ');
      const startIndex = Math.max(0, years.findIndex(y => y >= cfg.trendFrom));
      let endIndex = years.findIndex(y => y >= cfg.trendTo); if (endIndex < 0) endIndex = years.length - 1;
      return `<g data-climate-series="${row.slug}" style="--series-color:${COLORS[index % COLORS.length]}"><polyline class="series" points="${line}"><title>${escapeHtml(row.town)}</title></polyline><line class="trend" x1="${x(startIndex)}" y1="${scale.y(row.trend.start)}" x2="${x(endIndex)}" y2="${scale.y(row.trend.end)}"><title>Trend ${escapeHtml(row.town)} ${cfg.trendFrom}–${cfg.trendTo}</title></line></g>`;
    }).join('');
    const legend = rows.map((row, index) => `<button type="button" data-climate-select="${row.slug}" aria-pressed="false" style="--series-color:${COLORS[index % COLORS.length]}">${escapeHtml(row.town)}</button>`).join('');
    return `<div class="ov-climate-history"><div class="ov-climate-history-head"><div><strong>Andamento storico dei sette comuni</strong><span>${escapeHtml(cfg.explanation)} Seleziona un comune nella legenda per metterne in evidenza serie e trend. I comuni sono in ordine alfabetico.</span></div><span>Fonte: ${escapeHtml(cfg.source)}</span></div><div class="ov-climate-key"><span><i></i>Valore annuale</span><span><i class="trend"></i>Trend lineare ${cfg.trendFrom}–${cfg.trendTo}</span></div><div class="ov-climate-chart-scroll"><div class="ov-climate-chart ov-climate-compare-lines"><svg viewBox="0 0 ${scale.width} ${scale.height}">${gridMarkup(scale, cfg)}${groups}${yearLabels(years, x, scale.height)}</svg></div></div><div class="ov-climate-legend">${legend}</div><div class="ov-climate-selection-summary">Seleziona un comune per leggere la variazione del trend.</div></div>`;
  }

  function viewShellMarkup(currentMarkup, historyMarkup, note, id) {
    return `<div class="ux-view-shell" data-ov-climate-shell="${id}"><div class="ux-view-toolbar"><div class="ux-view-toolbar-copy"><strong>Come vuoi leggere l’indicatore?</strong><span>Ultimo dato omogeneo disponibile oppure andamento nel tempo.</span></div><div class="ux-view-toggle" role="tablist"><button type="button" role="tab" data-ov-climate-view="current">Valore attuale</button><button type="button" role="tab" data-ov-climate-view="history">Storico</button></div></div><p class="ov-climate-view-note">${escapeHtml(note)}</p><div data-ov-climate-pane="current">${currentMarkup}</div><div data-ov-climate-pane="history">${historyMarkup}</div></div>`;
  }

  function wireShell(shell, storageKey, rows, cfg) {
    if (!shell || shell.dataset.ovClimateWired === '1') return;
    shell.dataset.ovClimateWired = '1';
    const buttons = [...shell.querySelectorAll('[data-ov-climate-view]')];
    const panes = [...shell.querySelectorAll('[data-ov-climate-pane]')];
    const activate = mode => {
      buttons.forEach(b => { const active = b.dataset.ovClimateView === mode; b.classList.toggle('active', active); b.setAttribute('aria-selected', active); b.tabIndex = active ? 0 : -1; });
      panes.forEach(p => { p.hidden = p.dataset.ovClimatePane !== mode; });
      try { sessionStorage.setItem(storageKey, mode); } catch {}
    };
    buttons.forEach(b => b.addEventListener('click', () => activate(b.dataset.ovClimateView)));
    let initial = 'current'; try { initial = sessionStorage.getItem(storageKey) || 'current'; } catch {}
    activate(initial === 'history' ? 'history' : 'current');

    const chart = shell.querySelector('.ov-climate-compare-lines');
    const summary = shell.querySelector('.ov-climate-selection-summary');
    shell.querySelectorAll('[data-climate-select]').forEach(button => button.addEventListener('click', () => {
      const requested = button.dataset.climateSelect;
      const selected = button.getAttribute('aria-pressed') === 'true' ? '' : requested;
      shell.querySelectorAll('[data-climate-select]').forEach(b => b.setAttribute('aria-pressed', b.dataset.climateSelect === selected ? 'true' : 'false'));
      chart?.classList.toggle('has-selection', Boolean(selected));
      chart?.querySelectorAll('[data-climate-series]').forEach(g => g.classList.toggle('selected', g.dataset.climateSeries === selected));
      if (!summary) return;
      if (!selected) { summary.textContent = 'Seleziona un comune per leggere la variazione del trend.'; return; }
      const row = rows.find(r => r.slug === selected);
      const pct = cfg.unit === 'mm' && Number.isFinite(row.trend.percent) ? ` · ${row.trend.percent > 0 ? '+' : ''}${fmt1.format(row.trend.percent)}%` : '';
      summary.innerHTML = `<strong>${escapeHtml(row.town)}</strong> · trend ${cfg.trendFrom}–${cfg.trendTo}: <strong>${escapeHtml(formatSigned(row.trend.delta, cfg.unit))}</strong> (${escapeHtml(formatSigned(row.trend.perDecade, cfg.unit))} per decennio${escapeHtml(pct)}).`;
    }));
  }

  function patchMetricButtons() {
    for (const [key, cfg] of Object.entries(configs)) {
      document.querySelectorAll(`[data-metric="${key}"]`).forEach(button => { if (button.textContent.trim() !== cfg.shortLabel) button.textContent = cfg.shortLabel; });
    }
  }

  function patchMethod(cfg) {
    const details = document.querySelector('.method-disclosure');
    if (!details) return;
    details.innerHTML = `<summary><span>Metodo e comparabilità</span><small>Definizione, serie e tendenza</small></summary><div class="method-disclosure-body"><dl><div><dt>Natura</dt><dd>Ricostruzione territoriale validata</dd></div><div><dt>Valore principale</dt><dd>${escapeHtml(cfg.description)}</dd></div><div><dt>Storico</dt><dd>Valori annuali; trend lineare ${cfg.trendFrom}–${cfg.trendTo} mostrato separatamente.</dd></div></dl><p><strong>Come leggere il dato:</strong> ${escapeHtml(cfg.explanation)}</p></div>`;
  }

  function patchCompare(data, key) {
    const cfg = configs[key], rows = rowsFor(data, key);
    const def = document.getElementById('compare-definition');
    const target = document.getElementById('compare-bars');
    if (!def || !target) return;
    const avg = rows.reduce((sum, r) => sum + r.value, 0) / rows.length;
    def.innerHTML = `<div class="indicator-definition"><h2>${escapeHtml(cfg.label)}</h2><p>${escapeHtml(cfg.description)}</p><dl><div><dt>Anno</dt><dd>${cfg.latestYear}</dd></div><div><dt>Fonte</dt><dd><a href="${cfg.sourceUrl}" target="_blank" rel="noreferrer">${escapeHtml(cfg.source)} ↗</a></dd></div><div><dt>Media semplice dei 7 comuni</dt><dd>${escapeHtml(formatValue(avg, cfg.unit))}</dd></div></dl><small class="aggregate-note">${escapeHtml(cfg.explanation)}</small></div>`;
    const marker = `compare-${key}`;
    if (target.querySelector(`[data-ov-climate-shell="${marker}"]`)) return;
    target.innerHTML = viewShellMarkup(currentListMarkup(rows, cfg), compareHistoryMarkup(rows, cfg), `${cfg.description} “Valore attuale” indica l’ultimo anno omogeneo disponibile; “Storico” mostra l’evoluzione e il trend. Nessuna graduatoria.`, marker);
    wireShell(target.querySelector('[data-ov-climate-shell]'), 'ov-climate-compare-view', rows, cfg);
    const benchmark = document.getElementById('compare-benchmark'); if (benchmark) benchmark.hidden = true;
    patchMethod(cfg);
  }

  function patchTown(data, key) {
    const cfg = configs[key], rows = rowsFor(data, key);
    const name = document.querySelector('.town-hero h1')?.textContent?.trim();
    const row = rows.find(r => r.town === name || r.slug === document.body.dataset.town) || rows[0];
    const profile = document.querySelector('main.town-profile'); if (!profile) return;
    profile.classList.add('ov-climate-v2-active');
    const primary = profile.querySelector('.town-metric-primary');
    if (primary) primary.innerHTML = `<strong>${escapeHtml(formatValue(row.value, cfg.unit))}</strong><p>${escapeHtml(cfg.description)}</p><div><span>${cfg.latestYear}</span><a class="inline-source-link" href="${cfg.sourceUrl}" target="_blank" rel="noreferrer">Fonte originale ↗</a></div>`;
    const position = profile.querySelector('.versilia-position'); if (position) position.hidden = true;
    const benchmark = profile.querySelector('.town-benchmark'); if (benchmark) benchmark.hidden = true;
    const deep = profile.querySelector('.topic-deep-dive'); if (deep) deep.hidden = true;
    const panel = profile.querySelector('.history-panel');
    if (panel) {
      const marker = `town-${key}-${row.slug}`;
      if (!panel.querySelector(`[data-ov-climate-shell="${marker}"]`)) {
        panel.innerHTML = `<div class="panel-title"><div><span class="overline">Lettura climatica</span><h3>Valore disponibile e andamento storico</h3></div><a class="source-pill" href="${cfg.sourceUrl}" target="_blank" rel="noreferrer">Fonte ${escapeHtml(cfg.source)} ↗</a></div>${viewShellMarkup(currentListMarkup(rows, cfg, row.slug), townHistoryMarkup(row, cfg), `${cfg.description} Il confronto territoriale è in ordine alfabetico e senza classifiche; nello storico vedi solo ${row.town}, con anni leggibili e linea di trend.`, marker)}`;
        wireShell(panel.querySelector('[data-ov-climate-shell]'), 'ov-climate-town-view', rows, cfg);
      }
    }
    patchMethod(cfg);
  }

  function currentKey() {
    return new URL(location.href).searchParams.get('indicatore') || '';
  }

  let data = null;
  let scheduled = false;
  function sync() {
    patchMetricButtons();
    const key = currentKey();
    const climate = KEYS.has(key);
    if (!climate || !data) {
      document.querySelector('main.town-profile')?.classList.remove('ov-climate-v2-active');
      return;
    }
    if (document.body.dataset.page === 'compare' && document.body.dataset.theme === 'ambiente') patchCompare(data, key);
    if (document.body.dataset.page === 'town') patchTown(data, key);
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => requestAnimationFrame(() => { scheduled = false; sync(); }));
  }

  injectStyles();
  document.addEventListener('click', event => {
    if (event.target.closest('[data-metric],[data-profile-theme],[data-scale]')) schedule();
  }, true);
  document.addEventListener('keydown', event => {
    if (['Enter', ' ', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key) && event.target.closest('[data-metric],[data-profile-theme]')) schedule();
  }, true);

  loadData().then(result => { data = result; schedule(); }).catch(error => console.warn('Climate UX v2 non disponibile', error));
  schedule();
})();
