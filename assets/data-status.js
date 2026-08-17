(() => {
  'use strict';

  const script = document.currentScript;
  const DATA_URL = new URL('../data/data-status.json', script.src);
  const STATUS_URL = new URL('../stato-dati/', script.src);
  const esc = value => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const slugify = value => String(value || '').toLocaleLowerCase('it')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const dateLabel = value => {
    if (!value) return 'Non ancora registrato';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat('it-IT', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
  };

  const nextReleaseLabel = item => {
    const next = item?.nextExpectedRelease;
    if (!next?.value) return '';
    if (next.precision === 'month' && /^\d{4}-\d{2}$/.test(next.value)) {
      const [year, month] = next.value.split('-').map(Number);
      return new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1, 1));
    }
    return next.value;
  };

  const badge = item => `<span class="data-status-badge is-${esc(item.statusSeverity || 'neutral')}"><span aria-hidden="true"></span>${esc(item.statusLabel)}</span>`;

  async function loadPayload() {
    const response = await fetch(DATA_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Stato dati non disponibile: ${response.status}`);
    return response.json();
  }

  function enhanceIndicator(payload) {
    const metricKey = document.body.dataset.metric;
    const item = payload.metrics?.[metricKey];
    const section = document.querySelector('.indicator-method');
    if (!item || !section || section.querySelector('.data-update-card')) return;

    const next = nextReleaseLabel(item);
    const card = document.createElement('section');
    card.className = 'data-update-card';
    card.setAttribute('aria-labelledby', 'data-update-title');
    card.innerHTML = `
      <div class="data-update-card-head">
        <div><span class="overline">Affidabilità</span><h3 id="data-update-title">Aggiornamento del dato</h3></div>
        ${badge(item)}
      </div>
      <dl>
        <div><dt>Periodo pubblicato</dt><dd>${esc(item.publishedPeriod || '—')}</dd></div>
        <div><dt>Ultimo controllo Osservatorio</dt><dd>${esc(dateLabel(item.checkedAt))}</dd></div>
        <div><dt>Frequenza della fonte</dt><dd>${esc(item.frequencyLabel || 'Non determinabile')}</dd></div>
        ${next ? `<div><dt>Prossimo rilascio atteso</dt><dd>${esc(next)}</dd></div>` : ''}
      </dl>
      <p>${esc(item.statusDescription || '')}</p>
      ${item.status === 'verification_required' ? '<p class="data-status-note">“Verifica necessaria” non significa che il dato sia obsoleto: indica che il nuovo sistema non dispone ancora di un’evidenza sufficiente sull’ultimo periodo pubblicato dalla fonte.</p>' : ''}
      <a class="data-status-link" href="${esc(STATUS_URL.href)}">Vedi lo stato di tutti i dati <span aria-hidden="true">→</span></a>`;

    const heading = section.querySelector('.section-heading');
    if (heading) heading.insertAdjacentElement('afterend', card);
    else section.prepend(card);

    section.querySelectorAll('dt').forEach(dt => {
      if (dt.textContent.trim() === 'Prossimo aggiornamento atteso') dt.textContent = 'Cadenza indicativa della fonte';
      if (dt.textContent.trim() === 'Ultimo controllo della fonte') dt.textContent = 'Ultimo controllo tecnico della fonte';
    });
  }

  function summaryCard(label, value, detail) {
    return `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)}</small></article>`;
  }

  function renderStatusPage(payload) {
    const root = document.getElementById('data-status-app');
    if (!root) return;
    const items = Object.values(payload.metrics || {});
    const themes = [...new Set(items.map(item => item.theme).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'it'));
    const statuses = payload.statuses || {};
    const counts = payload.summary?.statusCounts || {};

    root.innerHTML = `
      <section class="data-status-summary" aria-label="Sintesi dello stato dei dati">
        ${summaryCard('Indicatori', payload.summary?.metricCount ?? items.length, 'catalogo complessivo')}
        ${summaryCard('Controllati', payload.summary?.checkedMetricCount ?? 0, 'con controllo fonte registrato')}
        ${summaryCard('Ultimo dato disponibile', counts.current ?? 0, 'periodo confermato')}
        ${summaryCard('Da verificare', (counts.new_release_to_review || 0) + (counts.verification_required || 0), 'rilasci o attualità da controllare')}
        ${summaryCard('Fonti con problemi', counts.source_unavailable ?? 0, 'temporaneamente non verificabili')}
      </section>
      <section class="data-status-controls" aria-label="Filtri">
        <label>Tematica<select id="status-theme"><option value="">Tutte</option>${themes.map(theme => `<option value="${esc(theme)}">${esc(theme.charAt(0).toUpperCase() + theme.slice(1))}</option>`).join('')}</select></label>
        <label>Stato<select id="status-state"><option value="">Tutti</option>${Object.entries(statuses).map(([key, meta]) => `<option value="${esc(key)}">${esc(meta.publicLabel || meta.label || key)}</option>`).join('')}</select></label>
        <label class="data-status-search">Cerca<input id="status-query" type="search" placeholder="Nome indicatore…" autocomplete="off"></label>
      </section>
      <p class="data-status-count" id="status-count" aria-live="polite"></p>
      <div class="data-status-list" id="status-list"></div>`;

    const theme = root.querySelector('#status-theme');
    const state = root.querySelector('#status-state');
    const query = root.querySelector('#status-query');
    const list = root.querySelector('#status-list');
    const count = root.querySelector('#status-count');

    const update = () => {
      const needle = query.value.trim().toLocaleLowerCase('it');
      const filtered = items
        .filter(item => !theme.value || item.theme === theme.value)
        .filter(item => !state.value || item.status === state.value)
        .filter(item => !needle || `${item.label} ${item.publisher} ${item.publishedPeriod}`.toLocaleLowerCase('it').includes(needle))
        .sort((a, b) => (a.theme || '').localeCompare(b.theme || '', 'it') || (a.label || '').localeCompare(b.label || '', 'it'));
      count.textContent = `${filtered.length} indicatori mostrati su ${items.length}`;
      list.innerHTML = filtered.map(item => {
        const href = `../indicatori/${slugify(item.label)}/`;
        const next = nextReleaseLabel(item);
        return `<article class="data-status-row" data-status="${esc(item.status)}" data-theme="${esc(item.theme)}">
          <div class="data-status-row-main"><span class="data-status-theme">${esc(item.theme || '')}</span><h2><a href="${esc(href)}">${esc(item.label || item.metricKey)}</a></h2><p>${esc(item.publisher || '')}</p></div>
          <div class="data-status-row-period"><span>Periodo</span><strong>${esc(item.publishedPeriod || '—')}</strong></div>
          <div class="data-status-row-state">${badge(item)}<small>Controllo: ${esc(dateLabel(item.checkedAt))}</small></div>
          <details><summary>Dettagli aggiornamento</summary><dl>
            <div><dt>Frequenza</dt><dd>${esc(item.frequencyLabel || 'Non determinabile')}</dd></div>
            <div><dt>Cadenza indicativa</dt><dd>${esc(item.releaseCadenceLabel || 'Non determinabile')}</dd></div>
            ${next ? `<div><dt>Prossimo rilascio atteso</dt><dd>${esc(next)}</dd></div>` : ''}
            <div><dt>Stato della fonte</dt><dd>${esc(item.sourceStatus === 'reachable' ? 'Raggiungibile' : item.sourceStatus === 'unavailable' ? 'Non raggiungibile al controllo' : 'Non controllata')}</dd></div>
          </dl><p>${esc(item.statusDescription || '')}</p></details>
        </article>`;
      }).join('') || '<div class="data-status-empty"><strong>Nessun indicatore corrisponde ai filtri.</strong></div>';
    };

    [theme, state, query].forEach(control => control.addEventListener(control.tagName === 'INPUT' ? 'input' : 'change', update));
    update();
  }

  loadPayload().then(payload => {
    if (document.body.dataset.page === 'indicator') enhanceIndicator(payload);
    if (document.body.dataset.page === 'data-status') renderStatusPage(payload);
  }).catch(error => {
    console.error(error);
    const root = document.getElementById('data-status-app');
    if (root) root.innerHTML = '<div class="data-status-empty"><strong>Impossibile caricare lo stato dei dati.</strong><p>Riprova più tardi oppure consulta la fonte dell’indicatore.</p></div>';
  });
})();
