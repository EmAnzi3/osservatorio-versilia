(() => {
  'use strict';

  const loader = document.currentScript;
  if (!loader) return;

  const page = document.body.dataset.page || '';
  const relevant = location.pathname.includes('/percorsi/') || page === 'town' || (page === 'compare' && document.body.dataset.theme === 'mobilita');
  if (!relevant) return;

  const statsUrl = new URL('../percorsi/data/site_stats.json', loader.src);
  const mapBaseUrl = new URL('../percorsi/', loader.src);
  const modeMeta = {
    trekking: { label: 'Trekking', color: '#176b4a' },
    cammino: { label: 'Cammini', color: '#6e4ab5' },
    bicycle: { label: 'Bici', color: '#117b93' },
    mtb: { label: 'MTB', color: '#315b9d' }
  };

  const statsPromise = fetch(statsUrl, { cache: 'no-store' }).then(response => {
    if (!response.ok) throw new Error(`Statistiche Percorsi non disponibili: ${response.status}`);
    return response.json();
  });

  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[char]));

  function mapUrl(municipality = '') {
    const url = new URL(mapBaseUrl);
    if (municipality) url.searchParams.set('comune', municipality);
    return url.href;
  }

  function modePills(byMode) {
    return Object.entries(modeMeta)
      .filter(([key]) => Number(byMode?.[key] || 0) > 0)
      .map(([key, meta]) => `<span><i style="background:${meta.color}"></i>${esc(meta.label)} ${Number(byMode[key])}</span>`)
      .join('');
  }

  function compareQuick(stats) {
    const v = stats.versilia;
    return `<aside class="slow-mobility-quick" data-percorsi-quick="versilia" aria-label="Percorsi e mobilità lenta">
      <div class="slow-mobility-quick-copy"><span>Mobilità lenta</span><strong>${Number(v.routes)} percorsi · ${Math.round(Number(v.km))} km</strong><small>Sentieri, cammini e ciclovie verificati nei 7 Comuni.</small></div>
      <div class="slow-mobility-quick-actions"><a href="#percorsi-statistiche">Statistiche</a><a href="${mapUrl()}">Mappa →</a></div>
    </aside>`;
  }

  function compareSection(stats) {
    const rows = Object.values(stats.municipalities)
      .sort((a, b) => a.name.localeCompare(b.name, 'it'))
      .map(item => `<tr>
        <th scope="row">${esc(item.name)}</th>
        <td class="route-count">${Number(item.routes)}</td>
        <td><div class="slow-mobility-mode-list">${modePills(item.by_mode)}</div></td>
        <td><a href="${mapUrl(item.name)}">Vedi sulla mappa →</a></td>
      </tr>`).join('');
    const v = stats.versilia;
    return `<section id="percorsi-statistiche" class="slow-mobility-overview page-width" data-percorsi-stats="versilia">
      <div class="slow-mobility-heading">
        <div><span class="overline">Mobilità lenta</span><h2>Percorsi, cammini e ciclovie della Versilia</h2><p>Una lettura statistica del patrimonio cartografico già verificato, affiancata alla mappa interattiva e ai download delle tracce.</p></div>
        <a class="slow-mobility-link" href="${mapUrl()}">Esplora la cartografia <span aria-hidden="true">→</span></a>
      </div>
      <div class="slow-mobility-summary">
        <article class="slow-mobility-stat primary"><strong>${Number(v.routes)}</strong><span>percorsi pubblici</span></article>
        <article class="slow-mobility-stat primary"><strong>${Math.round(Number(v.km))}</strong><span>km di tracce nei 7 Comuni</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode.trekking)}</strong><span>Trekking</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode.cammino)}</strong><span>Cammini</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode.bicycle)}</strong><span>Bici</span></article>
        <article class="slow-mobility-stat"><strong>${Number(v.by_mode.mtb)}</strong><span>MTB</span></article>
      </div>
      <div class="slow-mobility-table-wrap">
        <table class="slow-mobility-table">
          <thead><tr><th>Comune</th><th>Percorsi</th><th>Tipologia</th><th>Cartografia</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <p class="slow-mobility-note">${esc(stats.definition.municipality_count_note)} ${esc(stats.definition.municipality_km_note)}</p>
    </section>`;
  }

  function townSection(stats, slug) {
    const item = stats.municipalities?.[slug];
    if (!item) return '';
    const modeCards = Object.entries(modeMeta)
      .filter(([key]) => Number(item.by_mode?.[key] || 0) > 0)
      .map(([key, meta]) => `<article><strong>${Number(item.by_mode[key])}</strong><span>${esc(meta.label)}</span></article>`)
      .join('');
    return `<section class="slow-mobility-town" data-percorsi-stats="town">
      <div class="slow-mobility-heading">
        <div><span class="overline">Mobilità lenta</span><h3>Percorsi e mobilità lenta</h3><p>Tracce pubbliche verificate che attraversano il territorio di ${esc(item.name)}.</p></div>
        <a class="slow-mobility-link" href="${mapUrl(item.name)}">Apri ${esc(item.name)} sulla mappa <span aria-hidden="true">→</span></a>
      </div>
      <div class="slow-mobility-town-grid">
        <div class="slow-mobility-town-total"><strong>${Number(item.routes)}</strong><span>percorsi pubblici che attraversano il Comune</span></div>
        <div class="slow-mobility-town-modes">${modeCards}</div>
      </div>
      <p class="slow-mobility-note">Il conteggio considera ogni percorso una sola volta nel Comune. I chilometri comunali saranno pubblicati solo dopo l’intersezione con i confini amministrativi ufficiali.</p>
    </section>`;
  }

  function syncCompare(stats) {
    if (document.body.dataset.page !== 'compare' || document.body.dataset.theme !== 'mobilita') return;
    const main = document.querySelector('main[data-theme="mobilita"]');
    if (!main) return;

    if (!main.querySelector('[data-percorsi-quick="versilia"]')) {
      const catalog = main.querySelector('.topic-controls .metric-catalog');
      if (catalog) catalog.insertAdjacentHTML('afterend', compareQuick(stats));
    }

    if (!main.querySelector('[data-percorsi-stats="versilia"]')) {
      const tools = main.querySelector('#compare-tools');
      const dashboard = main.querySelector('.topic-dashboard');
      if (tools) tools.insertAdjacentHTML('afterend', compareSection(stats));
      else if (dashboard) dashboard.insertAdjacentHTML('afterend', compareSection(stats));
    }
  }

  function syncTown(stats) {
    if (document.body.dataset.page !== 'town') return;
    const main = document.querySelector('main.town-profile');
    if (!main) return;
    const topic = document.getElementById('town-topic');
    if (!topic) return;
    const existing = topic.querySelector('[data-percorsi-stats="town"]');
    if (main.dataset.theme !== 'mobilita') {
      existing?.remove();
      return;
    }
    if (existing) return;
    const markup = townSection(stats, document.body.dataset.town || '');
    if (!markup) return;

    /* Il riepilogo comunale deve essere visibile nel flusso principale,
       subito dopo il catalogo indicatori e prima del dato selezionato. */
    const catalog = topic.querySelector(':scope > .metric-switch.metric-catalog');
    const primary = topic.querySelector(':scope > .town-metric-layout');
    if (catalog) catalog.insertAdjacentHTML('afterend', markup);
    else if (primary) primary.insertAdjacentHTML('beforebegin', markup);
    else topic.insertAdjacentHTML('afterbegin', markup);
  }

  function syncMapDeepLink() {
    if (!location.pathname.includes('/percorsi/')) return;
    const municipality = new URLSearchParams(location.search).get('comune');
    if (!municipality) return;
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      const select = document.getElementById('municipality');
      if (select && [...select.options].some(option => option.value === municipality)) {
        select.value = municipality;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        clearInterval(timer);
      } else if (attempts >= 80) {
        clearInterval(timer);
      }
    }, 100);
  }

  function boot() {
    syncMapDeepLink();
    statsPromise.then(stats => {
      const sync = () => {
        syncCompare(stats);
        syncTown(stats);
      };
      sync();
      const root = document.getElementById('app') || document.body;
      new MutationObserver(sync).observe(root, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-theme'] });
      window.addEventListener('popstate', sync);
    }).catch(error => console.warn('[Percorsi Versilia]', error));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
