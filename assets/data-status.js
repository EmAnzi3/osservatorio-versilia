(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', script?.src || location.href);
  const statusHref = new URL('stato-dati/', ROOT).href;

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

    if (table.dataset.statusFiltersInstalled !== 'true') {
      theme?.addEventListener('change', update);
      status?.addEventListener('change', update);
      table.dataset.statusFiltersInstalled = 'true';
    }
    update();
  }

  function loadSocialPresence() {
    if (document.body.dataset.page !== 'status') return;
    if (document.querySelector('script[data-status-social-presence]')) return;
    const social = document.createElement('script');
    social.src = new URL('assets/social-presence.js?v=20260816-v113', ROOT).href;
    social.async = false;
    social.dataset.statusSocialPresence = 'true';
    document.head.append(social);
  }

  function loadNativeRuntime() {
    if (document.body.dataset.page !== 'status') return;
    if (document.querySelector('script[data-status-native-runtime]')) return;
    const source = document.body.dataset.statusAppBundle;
    if (!source) return;
    const runtime = document.createElement('script');
    runtime.src = new URL(source, location.href).href;
    runtime.async = false;
    runtime.dataset.statusNativeRuntime = 'true';
    runtime.addEventListener('load', () => {
      installFilters();
      ensureNavigationLinks();
    }, { once: true });
    document.head.append(runtime);
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

  function makeStatusLink(label, placement) {
    const link = document.createElement('a');
    link.href = statusHref;
    link.textContent = label;
    link.dataset.dataStatusNav = placement;
    return link;
  }

  function ensureNavigationLinks() {
    const headerNav = document.querySelector('.site-header-actions nav[aria-label="Navigazione principale"]');
    if (headerNav && !headerNav.querySelector('[data-data-status-nav="header"]')) {
      const link = makeStatusLink('Stato dati', 'header');
      const project = [...headerNav.querySelectorAll('a')].find(item => item.textContent.trim() === 'Il progetto');
      if (project) project.after(link);
      else headerNav.append(link);
    }

    const footerNav = document.querySelector('.site-footer .footer-links');
    if (footerNav && !footerNav.querySelector('[data-data-status-nav="footer"]')) {
      const link = makeStatusLink('Stato dei dati', 'footer');
      const project = [...footerNav.querySelectorAll('a')].find(item => item.textContent.trim() === 'Il progetto');
      if (project) project.after(link);
      else footerNav.prepend(link);
    }
  }

  function installNavigationPersistence() {
    let scheduled = false;
    const apply = () => {
      scheduled = false;
      ensureNavigationLinks();
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      queueMicrotask(apply);
    };
    apply();
    new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
  }

  function start() {
    installFilters();
    installIndicatorPersistence();
    installNavigationPersistence();
    loadSocialPresence();
    loadNativeRuntime();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
