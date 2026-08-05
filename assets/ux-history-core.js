(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const colors = ['#0f5c6e', '#b56843', '#64743d', '#855b7b', '#b88a1c', '#4e7096', '#914d47'];
  const formatters = new Map();

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function slug(value) {
    return String(value || '').toLocaleLowerCase('it')
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  function formatter(decimals = 1) {
    const key = String(decimals);
    if (!formatters.has(key)) {
      formatters.set(key, new Intl.NumberFormat('it-IT', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
        useGrouping: 'always'
      }));
    }
    return formatters.get(key);
  }

  function formatValue(value, unit) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 'n.d.';
    switch (unit) {
      case 'percent': return `${formatter(1).format(number)}%`;
      case 'percentagePoints': return `${formatter(1).format(number)} p.p.`;
      case 'euro': return `${formatter(0).format(number)} €`;
      case 'euroPerResident': return `${formatter(0).format(number)} € / residente`;
      case 'millionEuro': return `${formatter(1).format(number)} mln €`;
      case 'per1000': return `${formatter(1).format(number)} ogni 1.000`;
      case 'minutes': return `${formatter(1).format(number)} min`;
      case 'years': return `${formatter(1).format(number)} anni`;
      case 'kg': return `${formatter(0).format(number)} kg`;
      case 'hectares': return `${formatter(2).format(number)} ha`;
      case 'number': return formatter(0).format(number);
      default: return formatter(Number.isInteger(number) ? 0 : 1).format(number);
    }
  }

  function comparableSeries(metric) {
    if (!metric?.rows?.length) return null;
    const rows = metric.rows.map((row, index) => {
      const years = row.series?.years || [];
      const values = row.series?.values || [];
      const map = new Map();
      years.forEach((year, yearIndex) => {
        const value = Number(values[yearIndex]);
        if (Number.isFinite(value)) map.set(String(year), value);
      });
      return {
        town: row.town,
        slug: row.slug || slug(row.town),
        color: colors[index % colors.length],
        map
      };
    });
    if (rows.some(row => row.map.size < 2)) return null;
    let years = [...rows[0].map.keys()].filter(year => rows.every(row => row.map.has(year)));
    years = years.sort((a, b) => Number(a) - Number(b));
    if (years.length < 2) return null;
    return {
      years,
      rows: rows.map(row => ({ ...row, values: years.map(year => row.map.get(year)) }))
    };
  }

  function summaryMarkup(button, unit) {
    if (!button) return 'Seleziona un comune dalla legenda per evidenziarlo e leggere la variazione.';
    const start = Number(button.dataset.start);
    const end = Number(button.dataset.end);
    const delta = end - start;
    const sign = delta > 0 ? '+' : '';
    let variation;
    if (unit === 'percent' || unit === 'percentagePoints') {
      variation = `${sign}${formatter(1).format(delta)} p.p.`;
    } else if (start > 0) {
      const relative = delta / start * 100;
      variation = `${sign}${formatValue(delta, unit)} · ${relative > 0 ? '+' : ''}${formatter(1).format(relative)}%`;
    } else {
      variation = `${sign}${formatValue(delta, unit)}`;
    }
    return `<strong>${escapeHtml(button.dataset.town)}</strong>: ${escapeHtml(button.dataset.startYear)} ${escapeHtml(formatValue(start, unit))} → ${escapeHtml(button.dataset.endYear)} ${escapeHtml(formatValue(end, unit))}. Variazione: <strong>${escapeHtml(variation)}</strong>.`;
  }

  function historicalChartMarkup(metric, series, selectedSlug = '') {
    if (!series) return '<div class="ux-history-unavailable"><strong>Serie storica non disponibile</strong><p>Servono almeno due anni omogenei e comuni a tutti e sette i territori.</p></div>';

    const width = 920, height = 390, left = 78, right = 30, top = 26, bottom = 52;
    const chartWidth = width - left - right, chartHeight = height - top - bottom;
    const allValues = series.rows.flatMap(row => row.values);
    const rawMin = Math.min(...allValues), rawMax = Math.max(...allValues);
    const padding = (rawMax - rawMin || Math.max(Math.abs(rawMax) * .1, 1)) * .08;
    let min = rawMin - padding, max = rawMax + padding;
    if (rawMin >= 0 && min < 0) min = 0;
    if (rawMax <= 0 && max > 0) max = 0;
    const range = max - min || 1;
    const x = index => left + index * chartWidth / Math.max(1, series.years.length - 1);
    const y = value => top + (max - value) / range * chartHeight;

    const ticks = [0, .25, .5, .75, 1].map(fraction => {
      const value = max - fraction * range;
      const py = top + fraction * chartHeight;
      return `<line class="ux-history-grid" x1="${left}" y1="${py}" x2="${width - right}" y2="${py}"></line><text class="ux-history-axis-label" x="${left - 10}" y="${py + 4}" text-anchor="end">${escapeHtml(formatValue(value, metric.meta.unit))}</text>`;
    }).join('');

    const zero = min < 0 && max > 0
      ? `<line class="ux-history-zero" x1="${left}" y1="${y(0)}" x2="${width - right}" y2="${y(0)}"></line>`
      : '';
    const yearStep = Math.max(1, Math.ceil(series.years.length / 9));
    const yearLabels = series.years.map((year, index) => index % yearStep === 0 || index === series.years.length - 1
      ? `<text class="ux-history-axis-label" x="${x(index)}" y="${height - 16}" text-anchor="middle">${escapeHtml(year)}</text>`
      : '').join('');

    const paths = series.rows.map(row => {
      const points = row.values.map((value, index) => `${x(index)},${y(value)}`).join(' ');
      const circles = row.values.map((value, index) => `<circle class="ux-series-point" cx="${x(index)}" cy="${y(value)}" r="4"><title>${escapeHtml(`${row.town} · ${series.years[index]}: ${formatValue(value, metric.meta.unit)}`)}</title></circle>`).join('');
      return `<g class="ux-series-group ${row.slug === selectedSlug ? 'is-selected' : ''}" data-history-town="${escapeHtml(row.slug)}" style="--series-color:${row.color}"><polyline class="ux-series-line" points="${points}"><title>${escapeHtml(row.town)}</title></polyline>${circles}</g>`;
    }).join('');

    const legend = series.rows.map(row => `<button type="button" data-history-select="${escapeHtml(row.slug)}" data-town="${escapeHtml(row.town)}" data-start="${row.values[0]}" data-end="${row.values.at(-1)}" data-start-year="${escapeHtml(series.years[0])}" data-end-year="${escapeHtml(series.years.at(-1))}" aria-pressed="${row.slug === selectedSlug}" style="--series-color:${row.color}">${escapeHtml(row.town)}</button>`).join('');
    const modeLabel = series.years.length === 2 ? `Confronto ${series.years[0]}–${series.years[1]}` : `Andamento ${series.years[0]}–${series.years.at(-1)}`;

    return `<div class="ux-history-card"><div class="ux-history-head"><div><strong>${escapeHtml(modeLabel)}</strong><span>Una linea per comune; sono mostrati solo gli anni disponibili per tutti e sette.</span></div><span>${escapeHtml(metric.meta.source)}</span></div><div class="ux-history-scroll"><div class="ux-history-chart ${selectedSlug ? 'has-selection' : ''}" data-unit="${escapeHtml(metric.meta.unit)}"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(`${metric.meta.label}: confronto storico dei sette comuni`)}">${ticks}${zero}${paths}${yearLabels}</svg></div></div><div class="ux-history-legend" aria-label="Comuni">${legend}</div><div class="ux-history-summary" aria-live="polite">${summaryMarkup(null, metric.meta.unit)}</div></div>`;
  }

  function comparisonBarsMarkup(metric, selectedSlug = '') {
    const rows = [...metric.rows].sort((a, b) => Number(b.value) - Number(a.value));
    const values = rows.map(row => Number(row.value)).filter(Number.isFinite);
    const min = Math.min(0, ...values), max = Math.max(0, ...values);
    const range = max - min || 1;
    const zero = (0 - min) / range * 100;

    return `<div class="ux-comparison-bars">${rows.map((row, index) => {
      const value = Number(row.value);
      const start = value >= 0 ? zero : (value - min) / range * 100;
      const width = Math.max(1, Math.abs(value) / range * 100);
      const rowSlug = row.slug || slug(row.town);
      const href = new URL(`comuni/${rowSlug}/?tema=${encodeURIComponent(metric.meta.theme)}&indicatore=${encodeURIComponent(metric.key || '')}`, ROOT).href;
      return `<a class="ux-bar-row ${rowSlug === selectedSlug ? 'selected' : ''}" href="${href}"><span class="ux-bar-rank">${index + 1}</span><span class="ux-bar-town">${escapeHtml(row.town)}</span><span class="ux-bar-track"><span class="ux-bar-zero" style="left:${zero}%"></span><span class="ux-bar-fill" style="left:${start}%;width:${width}%"></span></span><strong>${escapeHtml(row.formatted || formatValue(value, metric.meta.unit))}</strong></a>`;
    }).join('')}</div>`;
  }

  function wireHistorySelection(shell, initialSlug, allowClear) {
    const chart = shell.querySelector('.ux-history-chart');
    if (!chart) return;
    const buttons = [...shell.querySelectorAll('[data-history-select]')];
    const groups = [...shell.querySelectorAll('[data-history-town]')];
    const summary = shell.querySelector('.ux-history-summary');
    const unit = chart.dataset.unit;

    const select = requested => {
      const current = buttons.find(button => button.getAttribute('aria-pressed') === 'true')?.dataset.historySelect || '';
      const selected = allowClear && requested === current ? '' : requested;
      chart.classList.toggle('has-selection', Boolean(selected));
      groups.forEach(group => group.classList.toggle('is-selected', group.dataset.historyTown === selected));
      buttons.forEach(button => button.setAttribute('aria-pressed', button.dataset.historySelect === selected ? 'true' : 'false'));
      if (summary) summary.innerHTML = summaryMarkup(buttons.find(button => button.dataset.historySelect === selected), unit);
      if (selected) sessionStorage.setItem('ov-history-town', selected);
    };

    buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.historySelect)));
    groups.forEach(group => group.addEventListener('click', () => select(group.dataset.historyTown)));
    select(initialSlug || '');
  }

  function viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note) {
    return `<div class="ux-view-shell"><div class="ux-view-toolbar"><div class="ux-view-toolbar-copy"><strong>Come vuoi leggere l’indicatore?</strong><span>Fotografia dell’ultimo anno oppure confronto dell’andamento tra i sette comuni.</span></div><div class="ux-view-toggle" role="tablist" aria-label="Vista dell’indicatore"><button type="button" role="tab" data-view-mode="current">Valore attuale</button><button type="button" role="tab" data-view-mode="history" ${historyAvailable ? '' : 'disabled'}>Storico</button></div></div>${note ? `<p class="ux-view-note">${escapeHtml(note)}</p>` : ''}<div class="ux-view-pane" data-view-pane="current">${currentMarkup}</div><div class="ux-view-pane" data-view-pane="history">${historyMarkup}</div></div>`;
  }

  function wireViewShell(shell, storageKey, historyAvailable, preferred = 'current') {
    const buttons = [...shell.querySelectorAll('[data-view-mode]')];
    const panes = [...shell.querySelectorAll('[data-view-pane]')];
    const stored = sessionStorage.getItem(storageKey);
    const initial = (stored === 'history' || preferred === 'history') && historyAvailable ? 'history' : 'current';

    const activate = mode => {
      if (mode === 'history' && !historyAvailable) return;
      buttons.forEach(button => {
        const active = button.dataset.viewMode === mode;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', active ? 'true' : 'false');
        button.tabIndex = active ? 0 : -1;
      });
      panes.forEach(pane => { pane.hidden = pane.dataset.viewPane !== mode; });
      sessionStorage.setItem(storageKey, mode);
    };

    buttons.forEach(button => button.addEventListener('click', () => activate(button.dataset.viewMode)));
    activate(initial);
  }

  window.OVUXHistory = {
    comparableSeries,
    historicalChartMarkup,
    comparisonBarsMarkup,
    wireHistorySelection,
    viewShellMarkup,
    wireViewShell,
    escapeHtml
  };
})();
