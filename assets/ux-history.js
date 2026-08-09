(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const HOTFIX_VERSION = '20260806-2';
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

  function enhanceTown(data) {
    if (document.body.dataset.page !== 'town') return;
    const panel = document.querySelector('.history-panel');
    if (!panel) return;

    const selectedTown = document.body.dataset.town || '';
    const existingShell = panel.querySelector('.ux-view-shell');
    if (existingShell) {
      wireShell(existingShell, 'ov-town-view', selectedTown, false);
      return;
    }

    const selected = selectedMetric(data);
    if (!selected) return;

    const series = toolkit.comparableSeries(selected.metric);
    const historyAvailable = Boolean(series);
    const currentMarkup = toolkit.comparisonBarsMarkup(selected.metric, selectedTown);
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

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  schedule();
})();
