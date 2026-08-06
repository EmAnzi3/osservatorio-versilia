(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const toolkit = window.OVUXHistory;
  if (!toolkit) return;

  let scheduled = false;
  const dataPromise = fetch(new URL('data/site-data.json', ROOT))
    .then(response => {
      if (!response.ok) throw new Error(`Errore dati ${response.status}`);
      return response.json();
    })
    .catch(error => {
      console.warn('Vista storica non disponibile', error);
      return null;
    });

  function selectedMetric(data) {
    const key = new URL(location.href).searchParams.get('indicatore');
    return key && data.metrics[key] ? { key, metric: { ...data.metrics[key], key } } : null;
  }

  function enhanceCompare(data) {
    if (document.body.dataset.page !== 'compare') return;
    const target = document.getElementById('compare-bars');
    if (!target || target.querySelector(':scope > .ux-view-shell') || !target.innerHTML.trim()) return;
    const selected = selectedMetric(data);
    if (!selected) return;

    const normalized = Boolean(document.querySelector('[data-scale="normalized"].active'));
    const series = normalized ? null : toolkit.comparableSeries(selected.metric);
    const historyAvailable = Boolean(series);
    const currentMarkup = target.innerHTML;
    const selectedTown = sessionStorage.getItem('ov-history-town') || '';
    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);
    const note = normalized
      ? 'La vista storica è disponibile sulla scala assoluta, perché le serie normalizzate non sono presenti per tutti gli anni.'
      : historyAvailable
        ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
        : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    target.innerHTML = toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note);
    const shell = target.querySelector('.ux-view-shell');
    toolkit.wireViewShell(shell, 'ov-compare-view', historyAvailable);
    toolkit.wireHistorySelection(shell, selectedTown, true);
  }

  function enhanceTown(data) {
    if (document.body.dataset.page !== 'town') return;
    const panel = document.querySelector('.history-panel');
    if (!panel || panel.querySelector('.ux-view-shell')) return;
    const selected = selectedMetric(data);
    if (!selected) return;

    const selectedTown = document.body.dataset.town || '';
    const series = toolkit.comparableSeries(selected.metric);
    const historyAvailable = Boolean(series);
    const currentMarkup = toolkit.comparisonBarsMarkup(selected.metric, selectedTown);
    const historyMarkup = toolkit.historicalChartMarkup(selected.metric, series, selectedTown);
    const note = historyAvailable
      ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
      : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';

    panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>${toolkit.escapeHtml(selected.metric.meta.label)}</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}`;
    const shell = panel.querySelector('.ux-view-shell');
    toolkit.wireViewShell(shell, 'ov-town-view', historyAvailable);
    toolkit.wireHistorySelection(shell, selectedTown, false);
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
