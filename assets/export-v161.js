(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const VERSION = '20260824-v116';
  let dataPromise = null;

  function loadData() {
    if (!dataPromise) {
      dataPromise = fetch(new URL(`data/site-data.json?v=${VERSION}`, ROOT))
        .then(response => {
          if (!response.ok) throw new Error(`Errore dati ${response.status}`);
          return response.json();
        });
    }
    return dataPromise;
  }

  function selectedMetric(data) {
    const requested = new URL(location.href).searchParams.get('indicatore');
    const active = document.querySelector('[data-metric].active')?.dataset.metric || '';
    const key = requested && data.metrics[requested] ? requested : active;
    return key && data.metrics[key] ? { key, metric: data.metrics[key] } : null;
  }

  function csvCell(value) {
    return `"${String(value ?? '').replaceAll('"', '""')}"`;
  }

  function saveCSV(key, lines) {
    const csv = '\ufeff' + lines.map(line => line.map(csvCell).join(';')).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const href = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = href;
    link.download = `osservatorio-versilia-${key}.csv`;
    link.click();
    URL.revokeObjectURL(href);
  }

  function historicalRows(metric, label) {
    const lines = [];
    metric.rows.forEach(row => {
      const exportedYears = new Set();
      const years = Array.isArray(row.series?.years) ? row.series.years : [];
      const values = Array.isArray(row.series?.values) ? row.series.values : [];
      years.forEach((year, index) => {
        const value = values[index];
        if (value === null || value === undefined || value === '') return;
        lines.push([row.town, row.code, label, year, value, metric.meta.unit, metric.sourceUrl]);
        exportedYears.add(String(year));
      });
      if (!exportedYears.has(String(metric.meta.year))) {
        lines.push([row.town, row.code, label, metric.meta.year, row.value, metric.meta.unit, metric.sourceUrl]);
      }
    });
    return lines;
  }

  function normalizedRows(metric) {
    const normalized = metric.meta.normalized;
    if (!normalized) return [];
    return metric.rows
      .filter(row => Number.isFinite(Number(row.normalized?.value)))
      .map(row => [
        row.town,
        row.code,
        normalized.label,
        metric.meta.year,
        row.normalized.value,
        normalized.unit,
        metric.sourceUrl
      ]);
  }

  async function exportSelectedMetric() {
    const data = await loadData();
    const selected = selectedMetric(data);
    if (!selected) throw new Error('Indicatore attivo non trovato');
    const normalized = Boolean(document.querySelector('[data-scale="normalized"].active'));
    const label = selected.metric.meta.label;
    const rows = normalized
      ? normalizedRows(selected.metric)
      : historicalRows(selected.metric, label);
    const lines = [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Valore', 'Unità', 'Fonte'], ...rows];
    saveCSV(selected.key, lines);
  }

  const printHiddenPanes = new Set();

  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('.ux-view-pane[hidden]').forEach(pane => {
      printHiddenPanes.add(pane);
      pane.hidden = false;
    });
  });

  window.addEventListener('afterprint', () => {
    printHiddenPanes.forEach(pane => { pane.hidden = true; });
    printHiddenPanes.clear();
  });

  document.addEventListener('click', event => {
    const button = event.target.closest?.('[data-download]');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    exportSelectedMetric().catch(error => {
      console.error('Esportazione CSV non riuscita', error);
      window.alert('Impossibile creare il CSV. Ricarica la pagina e riprova.');
    });
  }, true);
})();
