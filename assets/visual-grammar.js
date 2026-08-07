(() => {
  'use strict';

  const scriptUrl = document.currentScript?.src || new URL('assets/visual-grammar.js', document.baseURI).href;
  const dataUrl = new URL('../data/site-data.json', scriptUrl).href;
  const number1 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number0 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 });
  let data = null;
  let scheduled = false;

  function metricKeyFor(root) {
    const home = root.closest?.('#home-explorer');
    const dashboard = root.closest?.('.topic-dashboard');
    const townTopic = root.closest?.('#town-topic');
    const local = home || dashboard || townTopic;
    const active = local?.querySelector('[data-metric].active, [data-metric][aria-selected="true"]');
    if (active?.dataset.metric) return active.dataset.metric;
    return new URLSearchParams(location.search).get('indicatore');
  }

  function normalizedFor(root) {
    const dashboard = root.closest?.('.topic-dashboard');
    return Boolean(dashboard?.querySelector('[data-scale="normalized"].active'));
  }

  function townRow(metric, townName) {
    return metric?.rows?.find(row => row.town === townName) || null;
  }

  function valueFor(row, metric, normalized) {
    if (!row) return null;
    return normalized && row.normalized ? row.normalized.value : row.value;
  }

  function unitFor(row, metric, normalized) {
    if (normalized && row?.normalized) return row.normalized.unit;
    if (normalized && metric?.meta?.normalized) return metric.meta.normalized.unit;
    return metric?.meta?.unit || '';
  }

  function aggregateFor(metric, normalized) {
    return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;
  }

  function finite(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function formatAxis(value, unit) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return 'n.d.';
    const n = Number(value);
    const abs = Math.abs(n);
    const formatted = abs >= 100 ? number0.format(n) : number1.format(n);
    if (unit === '%') return `${formatted}%`;
    if (unit === '€' || unit === '€/ab.') return `${formatted} €`;
    return unit ? `${formatted} ${unit}` : formatted;
  }

  function scaleFor(values, aggregateValue, unit) {
    const numeric = values.map(finite).filter(value => value !== null);
    const reference = finite(aggregateValue);
    if (reference !== null) numeric.push(reference);
    if (!numeric.length) return { min: 0, max: 1, kind: 'absolute' };

    const allPercent = unit === '%' && numeric.every(value => value >= 0 && value <= 100);
    if (allPercent) return { min: 0, max: 100, kind: 'percent' };

    let min = Math.min(...numeric);
    let max = Math.max(...numeric);
    if (min >= 0) {
      min = 0;
      max = max === 0 ? 1 : max * 1.05;
      return { min, max, kind: 'absolute' };
    }
    if (max <= 0) {
      max = 0;
      min = min === 0 ? -1 : min * 1.05;
      return { min, max, kind: 'signed' };
    }
    const padding = (max - min) * 0.06 || 1;
    return { min: min - padding, max: max + padding, kind: 'signed' };
  }

  function position(value, scale) {
    const n = finite(value);
    if (n === null) return null;
    const span = scale.max - scale.min || 1;
    return Math.max(0, Math.min(100, ((n - scale.min) / span) * 100));
  }

  function deltaFor(metric, row) {
    const local = finite(row?.value);
    const aggregate = finite(metric?.aggregate?.value);
    if (local === null || aggregate === null) {
      return { headline: 'n.d.', direction: 'confronto non disponibile', compact: 'confronto non disponibile' };
    }

    if (metric.meta.unit === '%') {
      const diff = local - aggregate;
      if (Math.abs(diff) < 0.05) return { headline: '0,0 punti', direction: 'in linea', compact: 'in linea con Versilia' };
      const sign = diff > 0 ? '+' : '−';
      const abs = number1.format(Math.abs(diff));
      return {
        headline: `${sign}${abs} punti`,
        direction: diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
        compact: `${sign}${abs} p.p. vs Versilia`,
      };
    }

    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
        compact: 'confronto con Versilia',
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return { headline: '0,0%', direction: 'in linea', compact: 'in linea con Versilia' };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: relative > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
      compact: `${sign}${abs}% vs Versilia`,
    };
  }

  function enhanceComparison(container) {
    if (!data || !container?.isConnected) return;
    const metricKey = metricKeyFor(container);
    const metric = data.metrics?.[metricKey];
    if (!metric) return;

    const normalized = normalizedFor(container);
    const aggregate = aggregateFor(metric, normalized);
    const rows = [...container.querySelectorAll(':scope > .bar-row')];
    if (!rows.length) return;

    const mapped = rows.map(rowEl => {
      const townName = rowEl.querySelector('.bar-town')?.textContent?.trim();
      const row = townRow(metric, townName);
      return { rowEl, row, value: valueFor(row, metric, normalized) };
    });
    const firstRow = mapped.find(item => item.row)?.row;
    const unit = unitFor(firstRow, metric, normalized);
    const scale = scaleFor(mapped.map(item => item.value), aggregate?.value, unit);
    const referencePosition = position(aggregate?.value, scale);
    const zeroPosition = position(0, scale) ?? 0;
    const signature = [metricKey, normalized ? 'n' : 'r', aggregate?.value, unit, ...mapped.map(item => item.value)].join('|');
    if (container.dataset.visualGrammarSignature === signature && container.querySelector(':scope > .comparison-legend')) return;
    container.dataset.visualGrammarSignature = signature;
    container.dataset.viz = scale.kind === 'percent' ? 'percent-dotplot' : scale.kind === 'signed' ? 'signed-dotplot' : 'lollipop';

    container.querySelector(':scope > .comparison-legend')?.remove();
    container.querySelector(':scope > .comparison-axis')?.remove();
    container.querySelector(':scope > .comparison-note')?.remove();

    const legend = document.createElement('div');
    legend.className = 'comparison-legend';
    legend.innerHTML = `<span><i class="comparison-legend-dot" aria-hidden="true"></i>Comune</span><span><i class="comparison-legend-reference" aria-hidden="true"></i>${aggregate?.label || 'Versilia'}</span>`;
    container.prepend(legend);

    mapped.forEach(({ rowEl, row, value }) => {
      rowEl.querySelector('.bar-rank')?.remove();
      rowEl.classList.add('comparison-row');
      const track = rowEl.querySelector('.bar-track');
      if (!track) return;
      const x = position(value, scale);
      if (x === null) {
        const missing = '<span class="comparison-missing">Dato non disponibile</span>';
        if (track.innerHTML !== missing) track.innerHTML = missing;
        rowEl.classList.add('missing');
        return;
      }
      rowEl.classList.remove('missing');
      const stemLeft = Math.min(zeroPosition, x);
      const stemWidth = Math.abs(x - zeroPosition);
      const markup = `
        <span class="comparison-axis-line" aria-hidden="true"></span>
        ${scale.kind === 'signed' ? `<span class="comparison-zero" style="left:${zeroPosition}%" aria-hidden="true"></span>` : ''}
        ${referencePosition !== null ? `<span class="comparison-reference" style="left:${referencePosition}%" aria-hidden="true"></span>` : ''}
        <span class="comparison-stem" style="left:${stemLeft}%;width:${stemWidth}%" aria-hidden="true"></span>
        <span class="comparison-dot" style="left:${x}%" aria-hidden="true"></span>`;
      if (track.innerHTML !== markup) track.innerHTML = markup;
      if (row) {
        rowEl.setAttribute('aria-label', `${row.town}: ${formatAxis(value, unit)}; ${aggregate?.label || 'Versilia'}: ${formatAxis(aggregate?.value, unit)}`);
      }
    });

    const axis = document.createElement('div');
    axis.className = 'comparison-axis';
    axis.innerHTML = `<span>${formatAxis(scale.min, unit)}</span><span>${scale.kind === 'percent' ? 'scala 0–100%' : scale.kind === 'signed' ? 'lo zero è evidenziato' : 'scala con origine a zero'}</span><span>${formatAxis(scale.max, unit)}</span>`;
    container.append(axis);

    const note = document.createElement('p');
    note.className = 'comparison-note';
    note.textContent = 'I comuni sono ordinati per valore per facilitare il confronto. L’ordine non esprime merito o qualità.';
    container.append(note);
  }

  function enhanceTownPosition() {
    if (!data) return;
    const panel = document.querySelector('.versilia-position');
    const townName = document.querySelector('.town-identity h1')?.textContent?.trim();
    if (!panel || !townName) return;
    const metricKey = metricKeyFor(panel);
    const metric = data.metrics?.[metricKey];
    const row = townRow(metric, townName);
    if (!metric || !row) return;

    const delta = deltaFor(metric, row);
    const signature = `${metricKey}|${delta.headline}|${delta.direction}`;
    if (panel.dataset.visualGrammarSignature === signature) return;
    panel.dataset.visualGrammarSignature = signature;
    const overline = panel.querySelector('.overline');
    const strong = panel.querySelector(':scope > strong');
    if (overline && overline.textContent !== 'Rispetto alla Versilia') overline.textContent = 'Rispetto alla Versilia';
    const strongMarkup = `${delta.headline}<small>${delta.direction}</small>`;
    if (strong && strong.innerHTML !== strongMarkup) strong.innerHTML = strongMarkup;
  }

  function enhanceIndicatorCards() {
    if (!data) return;
    const townName = document.querySelector('.town-identity h1')?.textContent?.trim();
    if (!townName) return;
    document.querySelectorAll('.indicator-card-grid button[data-indicator]').forEach(button => {
      const metric = data.metrics?.[button.dataset.indicator];
      const row = townRow(metric, townName);
      const small = button.querySelector('small');
      if (!metric || !row || !small) return;
      const delta = deltaFor(metric, row);
      const text = `${metric.meta.year} · ${delta.compact}`;
      if (small.textContent !== text) small.textContent = text;
    });
  }

  function reviseCopy() {
    document.querySelectorAll('.method-list h3').forEach(heading => {
      if (heading.textContent.trim() === 'Posizione, non giudizio') {
        heading.textContent = 'Differenze, non podi';
        const paragraph = heading.nextElementSibling;
        if (paragraph) paragraph.textContent = 'I comuni possono essere ordinati per valore per facilitare la lettura, ma il sito evidenzia distanze e contesto, non posizioni ordinali.';
      }
    });

    document.querySelectorAll('.principles-grid h3').forEach(heading => {
      if (heading.textContent.trim() === 'Nessun voto') {
        const paragraph = heading.nextElementSibling;
        const text = 'Distanze e confronti descrivono i valori: non diventano pagelle, podi o giudizi politici automatici.';
        if (paragraph && paragraph.textContent !== text) paragraph.textContent = text;
      }
    });

    const intro = document.querySelector('.hero-intro p');
    if (intro?.textContent.includes('posizione rispetto alla Versilia')) {
      intro.textContent = intro.textContent.replace('posizione rispetto alla Versilia', 'confronto con la Versilia');
    }
    const townsIntro = document.querySelector('.towns-section .section-heading > p');
    if (townsIntro?.textContent.includes('posizione nel contesto')) {
      townsIntro.textContent = townsIntro.textContent.replace('posizione nel contesto', 'confronto nel contesto');
    }
  }

  function enhance() {
    scheduled = false;
    if (!data) return;
    document.querySelectorAll('.comparison-bars').forEach(enhanceComparison);
    enhanceTownPosition();
    enhanceIndicatorCards();
    reviseCopy();
  }

  function scheduleEnhance() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(enhance);
  }

  const observer = new MutationObserver(scheduleEnhance);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'aria-selected'] });

  fetch(dataUrl, { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw new Error(`Dati non disponibili (${response.status})`);
      return response.json();
    })
    .then(payload => {
      data = payload;
      enhance();
    })
    .catch(error => console.warn('Grammatica visuale non applicata:', error));
})();
