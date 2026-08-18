(() => {
  'use strict';

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

  function readIndicatorStatus() {
    const node = document.getElementById('ov-indicator-status');
    if (!node) return null;
    try {
      return JSON.parse(node.textContent || 'null');
    } catch (_error) {
      return null;
    }
  }

  function row(label, value, kind = '') {
    const div = document.createElement('div');
    if (kind) div.dataset.dataStatusRow = kind;
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = label;
    if (kind === 'state') {
      const badge = document.createElement('span');
      badge.className = `status-badge status-${value.statusTone}`;
      badge.textContent = value.statusLabel;
      const note = document.createElement('small');
      note.className = 'indicator-status-note';
      note.textContent = value.statusDescription;
      dd.append(badge, note);
    } else {
      dd.textContent = value;
    }
    div.append(dt, dd);
    return div;
  }

  function applyIndicatorStatus(metric) {
    if (!metric) return false;
    const list = document.querySelector('.indicator-governance-grid dl');
    if (!list) return false;

    if (!list.querySelector('[data-data-status-row="period"]')) {
      list.prepend(row('Periodo pubblicato', metric.publishedPeriod || '—', 'period'));
    }
    if (!list.querySelector('[data-data-status-row="state"]')) {
      const period = list.querySelector('[data-data-status-row="period"]');
      const state = row('Stato del dato', metric, 'state');
      period?.after(state);
    }

    [...list.querySelectorAll('dt')].forEach(dt => {
      const dd = dt.nextElementSibling;
      if (!dd) return;
      if (dt.textContent.trim() === 'Ultimo controllo della fonte') {
        dt.textContent = 'Ultimo controllo Osservatorio';
      }
      if (dt.textContent.trim() === 'Ultimo controllo Osservatorio' && dd.textContent !== metric.lastCheckedLabel) {
        dd.textContent = metric.lastCheckedLabel;
      }
      if (dt.textContent.trim() === 'Prossimo aggiornamento atteso') {
        dt.textContent = metric.nextExpectedRelease ? 'Prossimo rilascio atteso' : 'Cadenza indicativa';
      }
      if (dt.textContent.trim() === 'Prossimo rilascio atteso' && metric.nextExpectedRelease) {
        const value = String(metric.nextExpectedRelease.value || '');
        if (value && dd.textContent !== value) dd.textContent = value;
      }
      if (dt.textContent.trim() === 'Cadenza indicativa') {
        const value = metric.cadenceNote || 'Non determinabile';
        if (dd.textContent !== value) dd.textContent = value;
      }
    });
    return true;
  }

  function installIndicatorPersistence() {
    const metric = readIndicatorStatus();
    if (!metric) return;
    let scheduled = false;
    const apply = () => {
      scheduled = false;
      applyIndicatorStatus(metric);
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      queueMicrotask(apply);
    };
    apply();
    const app = document.getElementById('app');
    if (app) new MutationObserver(schedule).observe(app, { childList: true, subtree: true });
  }

  function start() {
    installFilters();
    installIndicatorPersistence();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
