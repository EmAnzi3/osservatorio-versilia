(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const colors = ['#0f5c6e', '#b56843', '#64743d', '#855b7b', '#b88a1c', '#4e7096', '#914d47'];
  const formatters = new Map();
  let shellCounter = 0;

  function storageGet(key) {
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  }

  function storageSet(key, value) {
    try {
      sessionStorage.setItem(key, value);
    } catch {
      // Controls remain functional when storage is unavailable.
    }
  }

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

  function forceItalianGrouping(formatted, value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || Math.abs(numeric) < 1000) return formatted;
    const text = String(formatted);
    const match = text.match(/^([−-]?)(\d+)(.*)$/);
    if (!match) return formatted;
    const [, sign, integer, suffix] = match;
    if (integer.length <= 3) return formatted;
    return `${sign}${integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}${suffix}`;
  }

  function formatNumber(value, decimals = 1) {
    return forceItalianGrouping(formatter(decimals).format(value), value);
  }

  function formatValue(value, unit) {
    if (value === null || value === undefined || value === '') return 'n.d.';
    const number = Number(value);
    if (!Number.isFinite(number)) return 'n.d.';
    switch (unit) {
      case 'percent': return `${formatNumber(number, 1)}%`;
      case 'percentagePoints': return `${formatNumber(number, 1)}%`;
      case 'currency': return `${formatNumber(number, 0)} €`;
      case 'currency2': return `${formatNumber(number, 2)} €`;
      case 'eurliter': return `${formatNumber(number, 3)} €/l`;
      case 'eurPerResident': return `${formatNumber(number, 2)} €/ab`;
      case 'euro': return `${formatNumber(number, 0)} €`;
      case 'euroPerResident': return `${formatNumber(number, 0)} € / residente`;
      case 'millionEuro': return `${formatNumber(number, 1)} mln €`;
      case 'per1000': return `${formatNumber(number, 1)} ogni 1.000`;
      case 'per10k': return `${formatNumber(number, 1)} ogni 10.000`;
      case 'index': return formatNumber(number, 1);
      case 'minutes': return `${formatNumber(number, 1)} min`;
      case 'years': return `${formatNumber(number, 1)} anni`;
      case 'kg': return `${formatNumber(number, 0)} kg`;
      case 'hectares': return `${formatNumber(number, 2)} ha`;
      case 'nights': return `${formatNumber(number, 2)} notti`;
      case 'people': return `${formatNumber(number, 0)} persone`;
      case 'studentsPerClass': return `${formatNumber(number, 1)} alunni/classe`;
      case 'per100': return `${formatNumber(number, 2)} ogni 100`;
      case 'per100k': return `${formatNumber(number, 2)} ogni 100.000`;
      case 'eurm2': return `${formatNumber(number, 0)} €/m²`;
      case 'rentm2': return `${formatNumber(number, 1)} €/m²/mese`;
      case 'number': return formatNumber(number, 0);
      default: return formatNumber(number, Number.isInteger(number) ? 0 : 1);
    }
  }

  function comparableSeries(metric) {
    if (!metric?.rows?.length) return null;
    const applicableRows = metric.rows.filter(row => !row?.notApplicable);
    if (!applicableRows.length) return null;
    const rows = applicableRows.map((row, index) => {
      const years = row.series?.years || [];
      const values = row.series?.values || [];
      const map = new Map();
      years.forEach((year, yearIndex) => {
        const value = Number(values[yearIndex]);
        if (Number.isFinite(value)) map.set(String(year), value);
      });
      const realMap = new Map();
      (row.realSeries?.years || []).forEach((year, yearIndex) => {
        const value = Number(row.realSeries?.values?.[yearIndex]);
        if (Number.isFinite(value)) realMap.set(String(year), value);
      });
      return {
        town: row.town,
        slug: row.slug || slug(row.town),
        color: colors[index % colors.length],
        map,
        realMap
      };
    });
    if (rows.some(row => row.map.size < 2)) return null;
    let years = [...rows[0].map.keys()].filter(year => rows.every(row => row.map.has(year)));
    years = years.sort((a, b) => Number(a) - Number(b));
    if (years.length < 2) return null;
    return {
      years,
      rows: rows.map(row => ({
        ...row,
        values: years.map(year => row.map.get(year)),
        realSeries: row.realMap.size
          ? { years, values: years.map(year => row.realMap.get(year) ?? null) }
          : null
      }))
    };
  }

  function summaryMarkup(button, unit) {
    if (!button) return 'Seleziona un comune dalla legenda per evidenziarlo e leggere la variazione.';
    const start = Number(button.dataset.start);
    const end = Number(button.dataset.end);
    const delta = end - start;
    const variation = deltaMarkup(start, end, unit);
    return `<strong>${escapeHtml(button.dataset.town)}</strong>: ${escapeHtml(button.dataset.startYear)} ${escapeHtml(formatValue(start, unit))} → ${escapeHtml(button.dataset.endYear)} ${escapeHtml(formatValue(end, unit))}. Variazione: <strong>${escapeHtml(variation)}</strong>.`;
  }

  function deltaMarkup(start, end, unit, compact = false) {
    const delta = end - start;
    const sign = delta > 0 ? '+' : '';
    if (unit === 'percent' || unit === 'percentagePoints') {
      return `${sign}${formatNumber(delta, 1)}%`;
    }
    if (compact || start <= 0) return `${sign}${formatValue(delta, unit)}`;
    const relative = delta / start * 100;
    return `${sign}${formatValue(delta, unit)} · ${relative > 0 ? '+' : ''}${formatNumber(relative, 1)}%`;
  }

  function historyPointMarkup({ x, y, value, year, town, unit, width, left, right, primaryText = '', detailLines = [] }) {
    const boxWidth = detailLines.length ? 310 : 210;
    const boxHeight = detailLines.length ? 90 : 50;
    const boxX = Math.max(left - 8, Math.min(width - right - boxWidth, x - boxWidth / 2));
    const boxY = y < boxHeight + 28 ? y + 18 : y - boxHeight - 16;
    const valueText = primaryText || formatValue(value, unit);
    const label = [`${town} · ${year}: ${valueText}`, ...detailLines].join('. ');
    const details = detailLines.map((line, index) => `<text class="chart-tooltip-detail" x="${boxX + 12}" y="${boxY + 53 + index * 17}">${escapeHtml(line)}</text>`).join('');
    return `<g class="chart-point" tabindex="0" role="button" aria-label="${escapeHtml(label)}">
      <circle class="chart-hit" cx="${x}" cy="${y}" r="13"></circle>
      <circle class="chart-dot ux-series-point" cx="${x}" cy="${y}" r="4"></circle>
      <g class="chart-tooltip" hidden>
        <line class="chart-guide" x1="${x}" y1="${y}" x2="${x}" y2="${boxY < y ? boxY + boxHeight : boxY}"></line>
        <rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect>
        <text class="chart-tooltip-year" x="${boxX + 12}" y="${boxY + 14}">${escapeHtml(`${town} · ${year}`)}</text>
        <text class="chart-tooltip-value" x="${boxX + 12}" y="${boxY + 34}">${escapeHtml(valueText)}</text>
        ${details}
      </g>
    </g>`;
  }

  function wireHistoryTooltips(chart) {
    if (!chart || chart.dataset.ovTooltipWired === '1') return;
    chart.dataset.ovTooltipWired = '1';
    const points = [...chart.querySelectorAll('.chart-point')];
    const hideAll = () => points.forEach(point => {
      point.classList.remove('active');
      point.querySelector('.chart-tooltip')?.setAttribute('hidden', '');
    });
    const show = point => {
      if (point.classList.contains('is-tooltip-disabled')) return;
      hideAll();
      point.classList.add('active');
      point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
    };
    const navigablePoints = () => points.filter(point => !point.classList.contains('is-tooltip-disabled') && point.tabIndex >= 0);
    points.forEach(point => {
      point.addEventListener('mouseenter', () => show(point));
      point.addEventListener('mouseleave', hideAll);
      point.addEventListener('focus', () => show(point));
      point.addEventListener('blur', hideAll);
      point.addEventListener('click', () => show(point));
      point.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
          hideAll();
          point.blur();
          return;
        }
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const available = navigablePoints();
        if (!available.length) return;
        const current = Math.max(0, available.indexOf(point));
        let next = current;
        if (event.key === 'ArrowLeft') next = (current - 1 + available.length) % available.length;
        if (event.key === 'ArrowRight') next = (current + 1) % available.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = available.length - 1;
        available[next]?.focus();
      });
    });
    chart.addEventListener('mouseleave', hideAll);
  }

  function twoPointChartMarkup(metric, series, selectedSlug = '') {
    const rows = [...series.rows].sort((a, b) => a.town.localeCompare(b.town, 'it'));
    const values = rows.flatMap(row => row.values);
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    const range = rawMax - rawMin || 1;
    const position = value => ((value - rawMin) / range * 100).toFixed(3);
    const startYear = series.years[0];
    const endYear = series.years[1];

    const rowMarkup = rows.map(row => {
      const start = Number(row.values[0]);
      const end = Number(row.values[1]);
      const startPosition = Number(position(start));
      const endPosition = Number(position(end));
      const lineStart = Math.min(startPosition, endPosition);
      const lineWidth = Math.max(Math.abs(endPosition - startPosition), .8);
      return `<button type="button" class="ux-two-point-row ux-series-group ${row.slug === selectedSlug ? 'is-selected' : ''}" data-history-town="${escapeHtml(row.slug)}" style="--series-color:${row.color};--start:${startPosition}%;--end:${endPosition}%;--line-start:${lineStart}%;--line-width:${lineWidth}%" aria-label="${escapeHtml(`${row.town}: ${startYear} ${formatValue(start, metric.meta.unit)}, ${endYear} ${formatValue(end, metric.meta.unit)}, variazione ${deltaMarkup(start, end, metric.meta.unit, true)}`)}"><span class="ux-two-point-town"><i aria-hidden="true"></i>${escapeHtml(row.town)}</span><span class="ux-two-point-value ux-two-point-start"><small>${escapeHtml(startYear)}</small><strong>${escapeHtml(formatValue(start, metric.meta.unit))}</strong></span><span class="ux-two-point-track" aria-hidden="true"><i></i><b class="start"></b><b class="end"></b></span><span class="ux-two-point-value ux-two-point-end"><small>${escapeHtml(endYear)}</small><strong>${escapeHtml(formatValue(end, metric.meta.unit))}</strong></span><span class="ux-two-point-delta">${escapeHtml(deltaMarkup(start, end, metric.meta.unit, true))}</span></button>`;
    }).join('');

    return `<div class="ux-two-point-chart" data-unit="${escapeHtml(metric.meta.unit)}"><div class="ux-two-point-heading" aria-hidden="true"><span>Comune</span><span>${escapeHtml(startYear)}</span><span>Passaggio</span><span>${escapeHtml(endYear)}</span><span>Variazione</span></div>${rowMarkup}</div>`;
  }

  function historicalChartMarkup(metric, series, selectedSlug = '') {
    if (!series) return '<div class="ux-history-unavailable"><strong>Serie storica non disponibile</strong><p>Servono almeno due anni omogenei e comuni a tutti e sette i territori.</p></div>';

    const legend = series.rows.map(row => `<button type="button" data-history-select="${escapeHtml(row.slug)}" data-town="${escapeHtml(row.town)}" data-start="${row.values[0]}" data-end="${row.values.at(-1)}" data-start-year="${escapeHtml(series.years[0])}" data-end-year="${escapeHtml(series.years.at(-1))}" aria-pressed="${row.slug === selectedSlug}" style="--series-color:${row.color}">${escapeHtml(row.town)}</button>`).join('');
    const isTwoPoint = series.years.length === 2;
    const modeLabel = isTwoPoint
      ? `Confronto a due punti ${series.years[0]}–${series.years[1]}`
      : `Andamento ${series.years[0]}–${series.years.at(-1)}`;
    let chartMarkup;

    if (isTwoPoint) {
      chartMarkup = twoPointChartMarkup(metric, series, selectedSlug);
    } else {
      const width = 920, height = 390, left = ['per100','per1000','per10k','per100k'].includes(metric.meta.unit) ? 132 : 78, right = 30, top = 26, bottom = 52;
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
        const inflationMap = metric?.meta?.key === 'incomeVsInflation' && metric.inflationSeries?.years?.length
          ? new Map(metric.inflationSeries.years.map((year, index) => [String(year), metric.inflationSeries.values[index]]))
          : null;
        const realMap = row.realSeries?.years?.length
          ? new Map(row.realSeries.years.map((year, index) => [String(year), row.realSeries.values[index]]))
          : null;
        const signedPercent = raw => {
          const numeric = Number(raw);
          if (!Number.isFinite(numeric)) return 'n.d.';
          return `${numeric > 0 ? '+' : ''}${formatValue(numeric, 'percent')}`;
        };
        const circles = row.values.map((value, index) => {
          const year = series.years[index];
          const isIncomeInflation = metric?.meta?.key === 'incomeVsInflation';
          const isInflationReference = isIncomeInflation && row.slug === 'inflazione-nic-italia';
          const primaryText = isInflationReference
            ? `Inflazione: ${signedPercent(value)}`
            : isIncomeInflation
              ? `Reddito nominale: ${signedPercent(value)}`
              : '';
          const detailLines = isIncomeInflation && !isInflationReference
            ? [
                `Inflazione: ${signedPercent(inflationMap?.get(String(year)))}`,
                `Variazione reale: ${signedPercent(realMap?.get(String(year)))}`,
              ]
            : [];
          return historyPointMarkup({
            x: x(index),
            y: y(value),
            value,
            year,
            town: row.town,
            unit: metric.meta.unit,
            width,
            left,
            right,
            primaryText,
            detailLines
          });
        }).join('');
        return `<g class="ux-series-group ${row.slug === selectedSlug ? 'is-selected' : ''}" data-history-town="${escapeHtml(row.slug)}" style="--series-color:${row.color}"><polyline class="ux-series-line" points="${points}"></polyline>${circles}</g>`;
      }).join('');

      chartMarkup = `<div class="ux-history-scroll"><div class="ux-history-chart ${selectedSlug ? 'has-selection' : ''}" data-unit="${escapeHtml(metric.meta.unit)}"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(`${metric.meta.label}: confronto storico dei sette comuni`)}">${ticks}${zero}${paths}${yearLabels}</svg></div></div><p class="ux-history-scroll-hint">Scorri il grafico orizzontalmente per leggere l’intera serie.</p>`;
    }

    return `<div class="ux-history-card"><div class="ux-history-head"><div><strong>${escapeHtml(modeLabel)}</strong><span>${isTwoPoint ? 'Confronto diretto tra le due annualità disponibili, in ordine alfabetico e senza graduatorie.' : 'Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.'}</span></div><span>${escapeHtml(metric.meta.source)}</span></div>${chartMarkup}<div class="ux-history-legend" aria-label="Comuni">${legend}</div><div class="ux-history-summary" aria-live="polite">${summaryMarkup(null, metric.meta.unit)}</div></div>`;
  }

  function comparisonBarsMarkup(metric, selectedSlug = '') {
    const finiteValue = value => value === null || value === undefined || value === '' ? null : (Number.isFinite(Number(value)) ? Number(value) : null);
    const rows = [...metric.rows].sort((a, b) => {
      const av = finiteValue(a.value), bv = finiteValue(b.value);
      if (av === null && bv === null) return String(a.town).localeCompare(String(b.town), 'it');
      if (av === null) return 1;
      if (bv === null) return -1;
      return bv - av;
    });
    const values = rows.map(row => finiteValue(row.value)).filter(value => value !== null);
    const focusedFuel = metric.meta.unit === 'eurliter' && values.length > 0;
    let min, max;
    if (focusedFuel) {
      const rawMin = Math.min(...values), rawMax = Math.max(...values);
      const spread = rawMax - rawMin;
      const padding = Math.max(0.005, spread * 0.25);
      min = Math.floor((rawMin - padding) * 1000) / 1000;
      max = Math.ceil((rawMax + padding) * 1000) / 1000;
      if (max <= min) max = min + 0.010;
    } else {
      min = Math.min(0, ...values);
      max = Math.max(0, ...values);
    }
    const range = max - min || 1;
    const zero = focusedFuel ? 0 : (0 - min) / range * 100;

    const markup = rows.map((row, index) => {
      const value = finiteValue(row.value);
      const rowSlug = row.slug || slug(row.town);
      const href = new URL(`comuni/${rowSlug}/?tema=${encodeURIComponent(metric.meta.theme)}&indicatore=${encodeURIComponent(metric.key || '')}`, ROOT).href;
      if (value === null) {
        return `<a class="ux-bar-row missing ${rowSlug === selectedSlug ? 'selected' : ''}" href="${href}"><span class="ux-bar-rank">—</span><span class="ux-bar-town">${escapeHtml(row.town)}</span><span class="ux-bar-track"></span><strong>n.d.</strong></a>`;
      }
      const valuePosition = (value - min) / range * 100;
      const start = focusedFuel ? 0 : (value >= 0 ? zero : valuePosition);
      const width = focusedFuel ? Math.max(1, valuePosition) : Math.max(1, Math.abs(value) / range * 100);
      return `<a class="ux-bar-row ${rowSlug === selectedSlug ? 'selected' : ''}" href="${href}"><span class="ux-bar-rank">${index + 1}</span><span class="ux-bar-town">${escapeHtml(row.town)}</span><span class="ux-bar-track">${focusedFuel ? '' : `<span class="ux-bar-zero" style="left:${zero}%"></span>`}<span class="ux-bar-fill" style="left:${start}%;width:${width}%"></span></span><strong>${escapeHtml(row.formatted || formatValue(value, metric.meta.unit))}</strong></a>`;
    }).join('');
    const note = focusedFuel ? `<p class="comparison-note">Scala adattata all’intervallo dei prezzi: non parte da zero, così le differenze di pochi centesimi restano leggibili.</p>` : '';
    return `<div class="ux-comparison-bars">${markup}</div>${note}`;
  }

  function wireHistorySelection(shell, initialSlug, allowClear) {
    const chart = shell.querySelector('.ux-history-chart, .ux-two-point-chart');
    if (!chart) return;
    wireHistoryTooltips(chart.matches('.ux-history-chart') ? chart : null);
    const buttons = [...shell.querySelectorAll('[data-history-select]')];
    const groups = [...shell.querySelectorAll('[data-history-town]')];
    const summary = shell.querySelector('.ux-history-summary');
    const unit = chart.dataset.unit;

    const select = (requested, userInitiated = true) => {
      const current = buttons.find(button => button.getAttribute('aria-pressed') === 'true')?.dataset.historySelect || '';
      const selected = userInitiated && allowClear && requested === current ? '' : requested;
      chart.classList.toggle('has-selection', Boolean(selected));
      groups.forEach(group => group.classList.toggle('is-selected', group.dataset.historyTown === selected));
      chart.querySelectorAll('.chart-point').forEach(point => {
        const owner = point.closest('[data-history-town]');
        const enabled = !selected || owner?.dataset.historyTown === selected;
        point.classList.toggle('is-tooltip-disabled', !enabled);
        point.style.pointerEvents = enabled ? '' : 'none';
        point.tabIndex = enabled ? 0 : -1;
        if (!enabled) {
          point.classList.remove('active');
          point.querySelector('.chart-tooltip')?.setAttribute('hidden', '');
        }
      });
      buttons.forEach(button => button.setAttribute('aria-pressed', button.dataset.historySelect === selected ? 'true' : 'false'));
      if (summary) summary.innerHTML = summaryMarkup(buttons.find(button => button.dataset.historySelect === selected), unit);
      if (selected) storageSet('ov-history-town', selected);
    };

    buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.historySelect)));
    groups.forEach(group => group.addEventListener('click', () => select(group.dataset.historyTown)));
    select(initialSlug || '', false);
  }

  function viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note) {
    const shellId = `ux-view-${++shellCounter}`;
    return `<div class="ux-view-shell" data-view-shell="${shellId}"><div class="ux-view-toolbar"><div class="ux-view-toolbar-copy"><strong>Come vuoi leggere l’indicatore?</strong><span>Fotografia dell’ultimo anno oppure confronto dell’andamento tra i sette comuni.</span></div><div class="ux-view-toggle" role="tablist" aria-label="Vista dell’indicatore"><button id="${shellId}-tab-current" type="button" role="tab" aria-controls="${shellId}-current" data-view-mode="current">Valore attuale</button><button id="${shellId}-tab-history" type="button" role="tab" aria-controls="${shellId}-history" data-view-mode="history" ${historyAvailable ? '' : 'disabled'}>Storico</button></div></div>${note ? `<p class="ux-view-note">${escapeHtml(note)}</p>` : ''}<div id="${shellId}-current" class="ux-view-pane" role="tabpanel" aria-labelledby="${shellId}-tab-current" data-view-pane="current">${currentMarkup}</div><div id="${shellId}-history" class="ux-view-pane" role="tabpanel" aria-labelledby="${shellId}-tab-history" data-view-pane="history">${historyMarkup}</div></div>`;
  }

  function wireViewShell(shell, storageKey, historyAvailable, preferred = 'current') {
    const buttons = [...shell.querySelectorAll('[data-view-mode]')];
    const panes = [...shell.querySelectorAll('[data-view-pane]')];
    const stored = storageGet(storageKey);
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
      storageSet(storageKey, mode);
    };

    buttons.forEach((button, index) => {
      button.addEventListener('click', () => activate(button.dataset.viewMode));
      button.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const enabled = buttons.filter(item => !item.disabled);
        const currentIndex = Math.max(0, enabled.indexOf(button));
        const nextIndex = event.key === 'Home' ? 0
          : event.key === 'End' ? enabled.length - 1
            : (currentIndex + (event.key === 'ArrowRight' ? 1 : -1) + enabled.length) % enabled.length;
        const next = enabled[nextIndex];
        activate(next.dataset.viewMode);
        next.focus();
      });
    });
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
