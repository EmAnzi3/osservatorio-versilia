(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const HOTFIX_VERSION = '20260814-4';
  const toolkit = window.OVUXHistory;
  if (!toolkit) return;

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

  function enhanceCompare(data) {
    if (document.body.dataset.page !== 'compare') return;
    const target = document.getElementById('compare-bars');
    if (!target || !target.innerHTML.trim()) return;

    const selectedTown = safeStorageGet('ov-history-town') || '';
    const existingShell = target.querySelector(':scope > .ux-view-shell');
    if (existingShell) {
      wireShell(existingShell, 'ov-compare-view', selectedTown, true);
      return;
    }

    const selected = selectedMetric(data);
    if (!selected) return;

    const normalized = Boolean(document.querySelector('[data-scale="normalized"].active'));
    const series = normalized ? null : toolkit.comparableSeries(selected.metric);
    const historyAvailable = Boolean(series);
    const currentMarkup = target.innerHTML;
    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);
    const note = normalized
      ? 'La vista storica è disponibile sulla scala assoluta, perché le serie normalizzate non sono presenti per tutti gli anni.'
      : historyAvailable
        ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
        : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    target.innerHTML = toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note);
    wireShell(target.querySelector('.ux-view-shell'), 'ov-compare-view', selectedTown, true);
  }

  const percent1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const euro0 = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

  function compositeChoiceMetric(metric, choice) {
    if (metric?.meta?.compositeType !== 'distribution') return metric;
    const clone = { ...metric, meta: { ...metric.meta }, rows: metric.rows.map(row => ({ ...row })) };
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
    if (!shell || metric?.meta?.compositeType !== 'distribution') return;
    const currentPane = shell.querySelector('[data-view-pane="current"]');
    if (!currentPane) return;
    const resolvedChoice = choice || 'summary';
    if (currentPane.dataset.compositeChoice === resolvedChoice) return;
    const viewMetric = compositeChoiceMetric(metric, resolvedChoice);
    currentPane.innerHTML = toolkit.comparisonBarsMarkup(viewMetric, selectedTown);
    currentPane.dataset.compositeChoice = resolvedChoice;
  }

  function currentCompositeChoice() {
    return document.querySelector('[data-composite-choice]')?.value || 'summary';
  }

  function enhanceTown(data) {
    if (document.body.dataset.page !== 'town') return;
    const panel = document.querySelector('.history-panel');
    if (!panel) return;

    const selectedTown = document.body.dataset.town || '';
    const selected = selectedMetric(data);
    if (!selected) return;
    const existingShell = panel.querySelector('.ux-view-shell');
    if (existingShell) {
      wireShell(existingShell, 'ov-town-view', selectedTown, false);
      refreshTownCompositeCurrent(selected.metric, existingShell, selectedTown, currentCompositeChoice());
      return;
    }

    const series = toolkit.comparableSeries(selected.metric);
    const historyAvailable = Boolean(series);
    const viewMetric = compositeChoiceMetric(selected.metric, currentCompositeChoice());
    const currentMarkup = toolkit.comparisonBarsMarkup(viewMetric, selectedTown);
    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);
    const note = historyAvailable
      ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
      : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>Valore attuale e andamento</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}`;
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
      refreshTownCompositeCurrent(metric, shell, document.body.dataset.town || '', event.detail?.choice || 'summary');
    });
  });

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  schedule();
})();
