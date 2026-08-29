(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const HOTFIX_VERSION = '20260829-v124-water-ui1';
  const toolkit = window.OVUXHistory;
  if (!toolkit) return;
  const LIBRARY_HISTORY_KEYS = new Set(['libraryLoansPerResident','libraryActiveBorrowersPer100','libraryWeeklyOpeningHours']);

  let scheduled = false;
  const wiredShells = new WeakSet();
  const dataPromise = fetch(new URL(`data/site-data.json?v=${HOTFIX_VERSION}`, ROOT))
    .then(response => {
      if (!response.ok) throw new Error(`Errore dati ${response.status}`);
      return response.json();
    })
    .catch(error => {
      console.warn('Vista storica non disponibile', error);
      return null;
    });

  function safeStorageGet(key) {
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  }

  function selectedMetric(data) {
    const urlKey = new URL(location.href).searchParams.get('indicatore');
    const activeKey = document.querySelector('[data-metric].active')?.dataset.metric || '';
    const key = urlKey && data.metrics[urlKey] ? urlKey : activeKey;
    return key && data.metrics[key] ? { key, metric: { ...data.metrics[key], key } } : null;
  }

  function wireShell(shell, storageKey, selectedTown, allowClear) {
    if (!shell || wiredShells.has(shell)) return;
    wiredShells.add(shell);
    const historyButton = shell.querySelector('[data-view-mode="history"]');
    const historyAvailable = Boolean(historyButton && !historyButton.disabled);
    toolkit.wireViewShell(shell, storageKey, historyAvailable);
    toolkit.wireHistorySelection(shell, selectedTown, allowClear);
  }

  function wireLibraryTownTooltips(shell) {
  if (!shell || shell.dataset.libraryTownTooltipsWired === '1') return;
  shell.dataset.libraryTownTooltipsWired = '1';
  shell.querySelectorAll('[data-view-pane="history"] .trend-chart').forEach(chart => {
    const points = [...chart.querySelectorAll('.chart-point')];
    if (!points.length) return;
    const hideAll = () => points.forEach(point => {
      point.classList.remove('active');
      point.querySelector('.chart-tooltip')?.setAttribute('hidden', '');
    });
    const show = point => {
      hideAll();
      point.classList.add('active');
      point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
    };
    points.forEach((point, index) => {
      point.addEventListener('mouseenter', () => show(point));
      point.addEventListener('mouseleave', hideAll);
      point.addEventListener('focus', () => show(point));
      point.addEventListener('blur', hideAll);
      point.addEventListener('click', () => show(point));
      point.addEventListener('keydown', event => {
        if (event.key === 'Escape') { hideAll(); point.blur(); return; }
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        let next = index;
        if (event.key === 'ArrowLeft') next = (index - 1 + points.length) % points.length;
        if (event.key === 'ArrowRight') next = (index + 1) % points.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = points.length - 1;
        points[next]?.focus();
      });
    });
    chart.addEventListener('mouseleave', hideAll);
  });
}

  function historyMetric(metric) {
    if (metric?.meta?.key === 'income' && metric.rows?.some(row => row.longSeries?.years?.length)) {
      return { ...metric, meta:{...metric.meta,label:metric.meta.longHistoryLabel || 'Reddito imponibile medio · serie lunga',unit:'currency'}, rows:metric.rows.map(row=>({...row,series:row.longSeries || row.series})) };
    }
    if (metric?.meta?.key === 'incomeVsInflation' && metric.inflationSeries?.years?.length) {
      const reference = metric.inflationSeries;
      return {
        ...metric,
        meta: { ...metric.meta, label: 'Redditi nominali vs inflazione', unit: 'percent' },
        rows: [
          ...metric.rows.map(row => ({ ...row, realSeries: row.realSeries || row.series, series: row.nominalSeries || row.series })),
          {
            town: reference.label || 'Inflazione · NIC Italia',
            slug: 'inflazione-nic-italia',
            value: Number(reference.values?.at(-1)),
            formatted: '',
            series: reference,
            normalized: null,
            benchmarkValue: Number(reference.values?.at(-1)),
          },
        ],
      };
    }
    return metric;
  }

  function renderHistoryMarkup(metric, series, selectedTown) {
    const markup = toolkit.historicalChartMarkup(metric, series, selectedTown);
    if (metric?.meta?.detailGroup === 'coast' && metric.aggregate?.series?.years?.length) {
      return markup
        .replace('Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.', 'Quattro Comuni costieri più l’aggregato ufficiale Versilia; i Comuni non costieri restano n.a. e non entrano nello storico.')
        .replace('confronto storico dei sette comuni', 'confronto storico dei quattro Comuni costieri e della Versilia')
        .replace('aria-label="Comuni"', 'aria-label="Territori costieri e Versilia"');
    }
    if (metric?.meta?.compositeType === 'sexBreakdown') {
      return markup
        .replace('Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.', 'Sette Comuni più l’aggregato ufficiale Versilia; sono mostrati solo gli anni omogenei della fonte ARS.')
        .replace('confronto storico dei sette comuni', 'confronto storico dei sette Comuni e della Versilia')
        .replace('aria-label="Comuni"', 'aria-label="Territori"');
    }
    if (metric?.meta?.key !== 'incomeVsInflation' || !metric.inflationSeries?.years?.length) return markup;
    const referenceLabel = toolkit.escapeHtml(metric.inflationSeries.label || 'Inflazione · NIC Italia');
    return markup
      .replace(
        'Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.',
        'Redditi nominali e inflazione sono riportati alla stessa base 2016 = 0%. I tooltip mostrano anche la variazione reale, calcolata come rapporto tra indice del reddito e indice dei prezzi.'
      )
      .replace(
        /<g class="ux-series-group [^"]*" data-history-town="inflazione-nic-italia" style="--series-color:[^"]+">/,
        '<g class="ux-inflation-reference" style="--series-color:var(--ink)">'
      )
      .replace(
        /<button type="button" data-history-select="inflazione-nic-italia"[^>]*>[^<]*<\/button>/,
        `<span class="ux-history-reference"><i aria-hidden="true"></i>${referenceLabel}</span>`
      );
  }

  function libraryHistoryChartMarkup(metric, selectedTown = '') {
    const colors = ['#0f5c6e', '#b56843', '#64743d', '#855b7b', '#b88a1c', '#4e7096', '#914d47'];
    const rows = (metric?.rows || []).map((row, index) => {
      const years = row.series?.years || [];
      const values = row.series?.values || [];
      const points = years.map((year, pointIndex) => ({
        year: Number(year),
        value: values[pointIndex] === null || values[pointIndex] === undefined || values[pointIndex] === '' ? null : Number(values[pointIndex])
      })).filter(point => Number.isFinite(point.year) && Number.isFinite(point.value));
      return { town: row.town, slug: row.slug || '', color: colors[index % colors.length], points };
    });
    const plotted = rows.filter(row => row.points.length);
    const years = [...new Set(plotted.flatMap(row => row.points.map(point => point.year)))].sort((a, b) => a - b);
    if (!plotted.length || years.length < 2) {
      return '<div class="ux-history-unavailable"><strong>Serie storica non disponibile</strong><p>Non risultano almeno due annualità osservate.</p></div>';
    }

    const values = plotted.flatMap(row => row.points.map(point => point.value));
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    const padding = (rawMax - rawMin || Math.max(Math.abs(rawMax) * .1, 1)) * .08;
    let min = rawMin - padding, max = rawMax + padding;
    if (rawMin >= 0 && min < 0) min = 0;
    const range = max - min || 1;
    const width = 920, height = 390;
    const left = metric.meta.unit === 'per100' ? 132 : 78, right = 30, top = 26, bottom = 52;
    const chartWidth = width - left - right, chartHeight = height - top - bottom;
    const firstYear = years[0], lastYear = years.at(-1), yearRange = Math.max(1, lastYear - firstYear);
    const x = year => left + (year - firstYear) / yearRange * chartWidth;
    const y = value => top + (max - value) / range * chartHeight;
    const numeric = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const valueText = value => {
      const formatted = numeric.format(value);
      if (metric.meta.unit === 'hours') return `${formatted} ore`;
      if (metric.meta.unit === 'per100') return `${formatted} ogni 100`;
      return formatted;
    };

    const ticks = [0, .25, .5, .75, 1].map(fraction => {
      const value = max - fraction * range;
      const py = top + fraction * chartHeight;
      return `<line class="ux-history-grid" x1="${left}" y1="${py}" x2="${width-right}" y2="${py}"></line><text class="ux-history-axis-label" x="${left-10}" y="${py+4}" text-anchor="end">${toolkit.escapeHtml(valueText(value))}</text>`;
    }).join('');
    const yearStep = Math.max(1, Math.ceil(years.length / 9));
    const yearLabels = years.map((year, index) => {
      if (!(index % yearStep === 0 || index === years.length - 1 || year === 2020)) return '';
      const label = year === 2020 ? '2020*' : String(year);
      return `<text class="ux-history-axis-label${year === 2020 ? ' library-pandemic-axis' : ''}" x="${x(year)}" y="${height-16}" text-anchor="middle">${toolkit.escapeHtml(label)}</text>`;
    }).join('');

    const groups = plotted.map(row => {
      const byYear = new Map(row.points.map(point => [point.year, point.value]));
      const segments = [];
      let current = [];
      years.forEach(year => {
        if (byYear.has(year)) current.push({ year, value: byYear.get(year) });
        else if (current.length) {
          segments.push(current);
          current = [];
        }
      });
      if (current.length) segments.push(current);
      const lines = segments.map(segment => segment.length >= 2
        ? `<polyline class="ux-series-line" points="${segment.map(point => `${x(point.year)},${y(point.value)}`).join(' ')}"></polyline>`
        : '').join('');
      const points = row.points.map(point => {
        const px = x(point.year), py = y(point.value), boxWidth = 230, boxHeight = 50;
        const boxX = Math.max(left - 8, Math.min(width - right - boxWidth, px - boxWidth / 2));
        const boxY = py < boxHeight + 28 ? py + 18 : py - boxHeight - 16;
        const formatted = valueText(point.value);
        const aria = `${row.town} · ${point.year}: ${formatted}`;
        return `<g class="chart-point" tabindex="0" role="button" aria-label="${toolkit.escapeHtml(aria)}"><circle class="chart-hit" cx="${px}" cy="${py}" r="13"></circle><circle class="chart-dot ux-series-point" cx="${px}" cy="${py}" r="4"></circle><g class="chart-tooltip" hidden><line class="chart-guide" x1="${px}" y1="${py}" x2="${px}" y2="${boxY < py ? boxY + boxHeight : boxY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+16}">${toolkit.escapeHtml(`${row.town} · ${point.year}`)}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+36}">${toolkit.escapeHtml(formatted)}</text></g></g>`;
      }).join('');
      return `<g class="ux-series-group ${row.slug === selectedTown ? 'is-selected' : ''}" data-history-town="${toolkit.escapeHtml(row.slug)}" style="--series-color:${row.color}">${lines}${points}</g>`;
    }).join('');

    const legend = rows.map(row => {
      if (!row.points.length) return `<span class="ux-history-reference is-unavailable">${toolkit.escapeHtml(row.town)} · n.d.</span>`;
      const start = row.points[0], end = row.points.at(-1);
      return `<button type="button" data-history-select="${toolkit.escapeHtml(row.slug)}" data-town="${toolkit.escapeHtml(row.town)}" data-start="${start.value}" data-end="${end.value}" data-start-year="${start.year}" data-end-year="${end.year}" aria-pressed="${row.slug === selectedTown}" style="--series-color:${row.color}">${toolkit.escapeHtml(row.town)}</button>`;
    }).join('');
    const note = years.includes(2020)
      ? 'Gli anni senza dato restano vuoti e non vengono interpolati. * 2020: anno pandemico anomalo.'
      : 'Gli anni senza dato restano vuoti e non vengono interpolati.';
    return `<div class="ux-history-card library-history-chart"><div class="ux-history-head"><div><strong>Andamento ${firstYear}–${lastYear}</strong><span>Una linea per Comune; tooltip sui valori osservati e vuoti dove il dato manca.</span></div><span>${toolkit.escapeHtml(metric.meta.source)}</span></div><div class="ux-history-scroll"><div class="ux-history-chart ${selectedTown ? 'has-selection' : ''}" data-unit="${toolkit.escapeHtml(metric.meta.unit)}"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${toolkit.escapeHtml(`${metric.meta.label}: confronto storico`)}">${ticks}${groups}${yearLabels}</svg></div></div><p class="ux-history-scroll-hint">Scorri il grafico orizzontalmente per leggere l’intera serie.</p><div class="ux-history-legend" aria-label="Comuni">${legend}</div><p class="aggregate-note">${toolkit.escapeHtml(note)}</p></div>`;
  }

  function enhanceCompare(data) {
    if (document.body.dataset.page !== 'compare') return;
    const target = document.getElementById('compare-bars');
    if (!target || !target.innerHTML.trim()) return;

    const selectedTown = safeStorageGet('ov-history-town') || '';
    const selected = selectedMetric(data);
    if (!selected) return;
    const existingShell = target.querySelector(':scope > .ux-view-shell');
    if (LIBRARY_HISTORY_KEYS.has(selected.key)) {
      if (existingShell) {
        wireShell(existingShell, 'ov-compare-view', selectedTown, true);
        return;
      }
      document.querySelector('#compare-tools .library-history-detail')?.remove();
      const currentMarkup = target.innerHTML;
      const historyMarkup = libraryHistoryChartMarkup(selected.metric, selectedTown);
      const note = 'Lo storico usa lo stesso linguaggio grafico degli altri indicatori: una linea per Comune, tooltip sui valori osservati e vuoti espliciti dove il dato manca.';
      target.innerHTML = toolkit.viewShellMarkup(currentMarkup, historyMarkup, true, note);
      wireShell(target.querySelector('.ux-view-shell'), 'ov-compare-view', selectedTown, true);
      return;
    }

    if (existingShell) {
      wireShell(existingShell, 'ov-compare-view', selectedTown, true);
      return;
    }

    const normalized = Boolean(document.querySelector('[data-scale="normalized"].active'));
    const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null;
    const historyView = historyMetric(selectedChoice ? compositeChoiceMetric(selected.metric, selectedChoice) : selected.metric);
    const series = normalized ? null : withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));
    const historyAvailable = Boolean(series);
    const currentMarkup = target.innerHTML;
    const historyMarkup = renderHistoryMarkup(historyView, series, selectedTown);
    const note = normalized
      ? 'La vista storica è disponibile sulla scala assoluta, perché le serie normalizzate non sono presenti per tutti gli anni.'
      : historyAvailable && selected.metric?.meta?.key === 'incomeVsInflation'
        ? selected.metric.historyPresentation?.note
        : historyAvailable && selected.metric?.meta?.key === 'income'
          ? selected.metric.meta.longHistoryNote
          : historyAvailable
            ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
            : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    target.innerHTML = toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note);
    wireShell(target.querySelector('.ux-view-shell'), 'ov-compare-view', selectedTown, true);
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
  const formatterWithGrouping = options => {
    const formatter = new Intl.NumberFormat('it-IT', { ...options, useGrouping: 'always' });
    return { format: value => forceItalianGrouping(formatter.format(value), value) };
  };
  const percent1 = formatterWithGrouping({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number1 = formatterWithGrouping({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number3 = formatterWithGrouping({ minimumFractionDigits: 3, maximumFractionDigits: 3 });
  const euro0 = formatterWithGrouping({ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
  const whole0 = formatterWithGrouping({ maximumFractionDigits: 0 });

  function compositeChoiceMetric(metric, choice) {
    if (!['distribution','omi','stock','securityMeasures','sexBreakdown'].includes(metric?.meta?.compositeType)) return metric;
    const clone = { ...metric, meta: { ...metric.meta }, rows: metric.rows.map(row => ({ ...row })), aggregate:metric.aggregate ? { ...metric.aggregate } : metric.aggregate };
    if (metric.meta.compositeType === 'sexBreakdown') {
      const selected = choice || metric.meta.defaultSex || 'totale';
      const option = (metric.meta.sexOptions || []).find(item=>item.key===selected);
      clone.meta.label = option ? `${metric.meta.label} · ${option.label}` : metric.meta.label;
      clone.meta.benchmark = metric.meta.benchmarksBySex?.[selected] || metric.meta.benchmark;
      clone.rows = metric.rows.map(row => {
        const part=(row.parts || []).find(item=>item.key===selected) || row.parts?.[0] || {};
        return { ...row, value:part.value, formatted:part.formatted || row.formatted, series:part.series || row.series };
      });
      const aggregatePart=(metric.aggregate?.parts || []).find(item=>item.key===selected) || metric.aggregate?.parts?.[0] || {};
      clone.aggregate = { ...metric.aggregate, value:aggregatePart.value, formatted:aggregatePart.formatted, series:aggregatePart.series, label:`Versilia · ${aggregatePart.label || option?.label || ''}` };
      return clone;
    }
    if (metric.meta.compositeType === 'securityMeasures') {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const template = metric.rows?.[0]?.parts?.[index] || metric.aggregate?.parts?.[index] || {};
      const unit = template.unit || metric.meta.unit;
      clone.meta.unit = unit;
      clone.meta.label = template.label || metric.meta.label;
      clone.rows = metric.rows.map(row => {
        const part = row.parts?.[index] || {};
        const rawValue = part.value;
        const value = rawValue === null || rawValue === undefined || rawValue === '' ? undefined : Number(rawValue);
        let formatted = 'n.d.';
        if (Number.isFinite(value)) {
          if (unit === 'currency') formatted = `${number1.format(value)} €`;
          else if (unit === 'currency2') formatted = `${number1.format(value)} €`;
          else if (unit === 'eurliter') formatted = `${number3.format(value)} €/l`;
          else if (unit === 'eurPerResident') formatted = `${number1.format(value)} €/ab`;
          else if (unit === 'percent') formatted = `${percent1.format(value)}%`;
          else if (unit === 'per1000') formatted = `${number1.format(value)} ogni 1.000`;
          else if (unit === 'per100') formatted = `${number1.format(value)} ogni 100`;
          else if (unit === 'per10k') formatted = `${number1.format(value)} ogni 10.000`;
          else formatted = number1.format(value);
        }
        const series = row.componentSeries?.[part.selectorLabel || template.selectorLabel] || row.componentSeries?.[template.selectorLabel] || row.series;
        return { ...row, value, formatted, series };
      });
      return clone;
    }
    if (metric.meta.compositeType === 'stock') {
      const count = choice === 'count';
      clone.meta.unit = count ? 'number' : 'percent';
      clone.meta.label = count ? 'Residenti di cittadinanza straniera' : 'Quota di residenti stranieri';
      clone.rows = metric.rows.map(row => {
        const value = Number(count ? row.count : row.value);
        const formatted = !Number.isFinite(value) ? 'n.d.' : count ? whole0.format(value) : `${percent1.format(value)}%`;
        return { ...row, value, formatted };
      });
      return clone;
    }
    if (metric.meta.compositeType === 'omi') {
      const rent = choice === 'rent';
      clone.meta.unit = rent ? 'rentm2' : 'eurm2';
      clone.meta.label = rent ? 'Affitto medio comunale OMI' : 'Vendita media comunale OMI';
      clone.rows = metric.rows.map(row => {
        const value = Number(rent ? row.rentMean : row.saleMean);
        const formatted = !Number.isFinite(value) ? 'n.d.' : rent ? `${number1.format(value)} €/m²/mese` : `${whole0.format(value)} €/m²`;
        return { ...row, value, formatted };
      });
      return clone;
    }
    if (choice === 'summary') {
      const unit = metric.meta.summaryUnit || metric.meta.unit;
      clone.meta.unit = unit;
      clone.meta.label = metric.meta.summaryLabel || metric.aggregate?.summaryLabel || metric.meta.label;
      clone.rows = metric.rows.map(row => {
        const value = Number(row.summaryValue);
        const formatted = !Number.isFinite(value) ? 'n.d.'
          : unit === 'currency' ? euro0.format(value)
            : unit === 'years' ? `${number1.format(value)} anni`
              : String(value);
        return { ...row, value, formatted };
      });
      return clone;
    }
    const index = Number(String(choice || '').replace('part-', ''));
    if (!Number.isInteger(index) || index < 0) return clone;
    clone.meta.unit = 'percent';
    clone.meta.label = metric.aggregate?.parts?.[index]?.label || metric.rows?.[0]?.parts?.[index]?.label || metric.meta.label;
    clone.rows = metric.rows.map(row => {
      const value = Number(row.parts?.[index]?.value);
      return { ...row, value, formatted: Number.isFinite(value) ? `${percent1.format(value)}%` : 'n.d.' };
    });
    return clone;
  }

  function refreshTownCompositeCurrent(metric, shell, selectedTown, choice) {
    if (!shell || !['distribution','omi','stock','securityMeasures','sexBreakdown'].includes(metric?.meta?.compositeType)) return;
    const currentPane = shell.querySelector('[data-view-pane="current"]');
    if (!currentPane) return;
    const resolvedChoice = choice || (metric?.meta?.compositeType === 'omi' ? 'sale' : metric?.meta?.compositeType === 'stock' ? 'share' : metric?.meta?.compositeType === 'securityMeasures' ? 'part-0' : 'summary');
    if (currentPane.dataset.compositeChoice === resolvedChoice) return;
    const viewMetric = compositeChoiceMetric(metric, resolvedChoice);
    currentPane.innerHTML = toolkit.comparisonBarsMarkup(viewMetric, selectedTown);
    currentPane.dataset.compositeChoice = resolvedChoice;
  }

  function currentCompositeChoice() {
    return document.querySelector('select[data-composite-choice]')?.value || document.querySelector('select[data-composite-component]')?.value || 'summary';
  }

  function withOfficialVersiliaSeries(metric, series) {
    const includesOfficialAggregate = metric?.meta?.compositeType === 'sexBreakdown'
      || metric?.meta?.detailGroup === 'coast';
    if (!series || !includesOfficialAggregate || !metric.aggregate?.series?.years?.length) return series;
    const map = new Map(metric.aggregate.series.years.map((year,index)=>[String(year),Number(metric.aggregate.series.values?.[index])]));
    if (!series.years.every(year=>Number.isFinite(map.get(String(year))))) return series;
    return { ...series, rows:[...series.rows,{ town:'Versilia', slug:'versilia', color:'var(--ink)', map:new Map(), realMap:new Map(), values:series.years.map(year=>map.get(String(year))), realSeries:null }] };
  }

  function enhanceTown(data) {
    if (document.body.dataset.page !== 'town') return;
    const panel = document.querySelector('.history-panel');
    if (!panel) return;

    const selectedTown = document.body.dataset.town || '';
    const selected = selectedMetric(data);
    if (!selected) return;
    const existingShell = panel.querySelector('.ux-view-shell');
    if (LIBRARY_HISTORY_KEYS.has(selected.key)) {
      if (existingShell) {
        wireShell(existingShell, 'ov-town-view', selectedTown, false);
        wireLibraryTownTooltips(existingShell);
        return;
      }
      const row = selected.metric.rows?.find(item => (item.slug || '') === selectedTown);
      const historyAvailable = Boolean(row?.series?.years?.length);
      const title = panel.querySelector(':scope > .panel-title');
      const historyMarkup = historyAvailable
        ? [...panel.children].filter(child => child !== title).map(child => child.outerHTML).join('')
        : '<div class="ux-history-unavailable"><strong>Serie storica non disponibile</strong><p>Per questo Comune non risultano osservazioni storiche nel monitoraggio regionale.</p></div>';
      const currentMarkup = toolkit.comparisonBarsMarkup(selected.metric, selectedTown);
      const note = historyAvailable
        ? 'Lo storico del Comune termina all’ultima osservazione ufficiale disponibile; nessun valore mancante viene stimato o trascinato.'
        : 'Per questo Comune il monitoraggio regionale non rende disponibile una serie storica.';
      panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>Valore attuale e andamento</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}`;
      const shell = panel.querySelector('.ux-view-shell');
      wireShell(shell, 'ov-town-view', selectedTown, false);
      wireLibraryTownTooltips(shell);
      return;
    }
    if (existingShell) {
      wireShell(existingShell, 'ov-town-view', selectedTown, false);
      refreshTownCompositeCurrent(selected.metric, existingShell, selectedTown, currentCompositeChoice());
      return;
    }

    const fixedDetail = panel.querySelector('.composite-fixed-detail')?.outerHTML || '';
    const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null;
    const historyView = historyMetric(selectedChoice ? compositeChoiceMetric(selected.metric, selectedChoice) : selected.metric);
    const selectedRow = historyView.rows?.find(row => (row.slug || '') === selectedTown);
    const series = selectedRow?.notApplicable
      ? null
      : withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));
    const historyAvailable = Boolean(series);
    const viewMetric = compositeChoiceMetric(selected.metric, currentCompositeChoice());
    const currentMarkup = toolkit.comparisonBarsMarkup(viewMetric, selectedTown);
    const historyMarkup = renderHistoryMarkup(historyView, series, selectedTown);
    const note = historyAvailable && selected.metric?.meta?.key === 'incomeVsInflation'
      ? selected.metric.historyPresentation?.note
      : historyAvailable && selected.metric?.meta?.key === 'income'
        ? selected.metric.meta.longHistoryNote
        : selectedRow?.notApplicable
          ? 'Questo Comune non ha costa marina: lo storico non è applicabile e resta n.a.'
          : historyAvailable
            ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
            : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>Valore attuale e andamento</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}${fixedDetail}`;
    wireShell(panel.querySelector('.ux-view-shell'), 'ov-town-view', selectedTown, false);
  }

  function enhance(data) {
    if (!data) return;
    enhanceCompare(data);
    enhanceTown(data);
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      dataPromise.then(enhance);
    });
  }

  window.addEventListener('ov:composite-choice', event => {
    if (document.body.dataset.page !== 'town') return;
    dataPromise.then(data => {
      if (!data) return;
      const metricKey = event.detail?.metricKey;
      const metric = metricKey && data.metrics[metricKey] ? { ...data.metrics[metricKey], key: metricKey } : null;
      const shell = document.querySelector('.history-panel .ux-view-shell');
      if (!metric || !shell) return;
      const choice = event.detail?.choice || 'summary';
      refreshTownCompositeCurrent(metric, shell, document.body.dataset.town || '', choice);
      if (metric.meta?.compositeType === 'sexBreakdown') {
        const selectedTown = document.body.dataset.town || '';
        const historyView = historyMetric(compositeChoiceMetric(metric, choice));
        const series = withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));
        const pane = shell.querySelector('[data-view-pane="history"]');
        if (pane) {
          pane.innerHTML = renderHistoryMarkup(historyView, series, selectedTown);
          toolkit.wireHistorySelection(shell, selectedTown, false);
        }
      }
    });
  });

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  schedule();
})();
