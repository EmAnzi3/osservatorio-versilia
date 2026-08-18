(() => {
  'use strict';

  function rootPrefix() {
    const script = document.currentScript;
    if (!script?.src) return '../';
    return new URL('../', script.src).href;
  }

  function formatDate(value) {
    if (!value) return 'Non ancora registrato';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('it-IT', {
      day: 'numeric', month: 'long', year: 'numeric'
    }).format(date);
  }

  function installFilters() {
    const table = document.querySelector('.data-status-table');
    if (!table) return;
    const theme = document.querySelector('[data-status-theme]');
    const status = document.querySelector('[data-status-filter]');
    const visible = document.querySelector('[data-status-visible]');
    const rows = [...table.querySelectorAll('tbody tr')];
    const update = () => {
      let count = 0;
      rows.forEach(row => {
        const show = (!theme?.value || row.dataset.theme === theme.value)
          && (!status?.value || row.dataset.status === status.value);
        row.hidden = !show;
        if (show) count += 1;
      });
      if (visible) visible.textContent = `${count} indicatori visibili`;
    };
    theme?.addEventListener('change', update);
    status?.addEventListener('change', update);
    update();
  }

  function nextReleaseText(release) {
    if (!release || typeof release !== 'object' || !release.value) return '';
    return String(release.value);
  }

  async function enhanceIndicator() {
    const metricKey = document.body?.dataset?.metric;
    if (!metricKey) return;
    let payload;
    try {
      const response = await fetch(new URL('data/data-status.json', rootPrefix()), { cache: 'no-store' });
      if (!response.ok) return;
      payload = await response.json();
    } catch (_error) {
      return;
    }
    const metric = payload.metrics?.find?.(item => item.key === metricKey);
    if (!metric) return;

    const grid = document.querySelector('.indicator-governance-grid');
    const list = grid?.querySelector('dl');
    if (!list) return;
    if (!list.querySelector('[data-data-status-row]')) {
      const period = document.createElement('div');
      period.dataset.dataStatusRow = 'period';
      period.innerHTML = `<dt>Periodo pubblicato</dt><dd>${metric.publishedPeriod || '—'}</dd>`;
      const state = document.createElement('div');
      state.dataset.dataStatusRow = 'state';
      state.innerHTML = `<dt>Stato del dato</dt><dd><span class="status-badge status-${metric.statusTone}">${metric.statusLabel}</span><small class="indicator-status-note">${metric.statusDescription}</small></dd>`;
      list.prepend(state);
      list.prepend(period);
    }

    [...list.querySelectorAll('dt')].forEach(dt => {
      const text = dt.textContent.trim();
      if (text === 'Ultimo controllo della fonte') {
        dt.textContent = 'Ultimo controllo Osservatorio';
        const dd = dt.nextElementSibling;
        if (dd) dd.textContent = formatDate(metric.lastChecked);
      }
      if (text === 'Prossimo aggiornamento atteso') {
        const dd = dt.nextElementSibling;
        const next = nextReleaseText(metric.nextExpectedRelease);
        if (next) {
          dt.textContent = 'Prossimo rilascio atteso';
          if (dd) dd.textContent = next;
        } else {
          dt.textContent = 'Cadenza indicativa';
          if (dd) dd.textContent = metric.cadenceNote || 'Non determinabile';
        }
      }
    });
  }

  function run() {
    installFilters();
    enhanceIndicator();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
  else run();
})();
