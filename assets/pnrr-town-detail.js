(() => {
  'use strict';

  const escapeHtml = value => String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

  const number0 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 });
  const number1 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const money0 = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', useGrouping: 'always', maximumFractionDigits: 0 });
  const money2 = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', useGrouping: 'always', minimumFractionDigits: 2, maximumFractionDigits: 2 });

  let dataPromise = null;
  let scheduled = false;

  function dataUrl() {
    return new URL('../../data/site-data.json', location.href).href;
  }

  function loadData() {
    if (!dataPromise) {
      dataPromise = fetch(dataUrl(), { cache: 'no-store' }).then(response => {
        if (!response.ok) throw new Error(`PNRR data ${response.status}`);
        return response.json();
      });
    }
    return dataPromise;
  }

  function statusClass(status) {
    if (status === 'Collaudo completato') return 'is-complete';
    if (status === 'Lavori in esecuzione') return 'is-execution';
    if (status === 'Contratto stipulato' || status === 'Stipula in corso') return 'is-contract';
    return 'is-progress';
  }

  function generalMarkup(deep) {
    const totals = deep.totals;
    const works = deep.physicalWorks;
    const concludedPercent = totals.concluded / totals.projects * 100;
    return `<section class="pnrr-general-context page-width" data-pnrr-general-context="true" aria-labelledby="pnrr-general-title">
      <div class="pnrr-context-heading">
        <div><span class="overline">Approfondimento territoriale</span><h2 id="pnrr-general-title">Dentro il PNRR</h2></div>
        <p>Il quadro PNRR dei sette Comuni, distinto dalle opere pubbliche complessive censite in BDAP-MOP.</p>
      </div>
      <div class="pnrr-context-grid">
        <article><span>Progetti PNRR</span><strong>${number0.format(totals.projects)}</strong><small>PNRR / PNRR-PNC · PNC puro escluso</small></article>
        <article><span>Fase 5 · conclusione</span><strong>${number0.format(totals.concluded)}</strong><small>${number1.format(concludedPercent)}% · macrofase ReGiS</small></article>
        <article><span>Quota PNRR</span><strong>${money0.format(totals.funding)}</strong><small>finanziamento censito, non spesa effettuata</small></article>
        <article><span>Opere fisiche</span><strong>${number0.format(works.count)}</strong><small>classificate come lavori/opere nel dataset regionale</small></article>
      </div>
      <div class="pnrr-context-actions"><a class="button-link" href="../../pnrr/">Apri tutte le 22 opere e gli stati <span aria-hidden="true">→</span></a></div>
    </section>`;
  }

  function workMarkup(work) {
    return `<article class="pnrr-town-work">
      <div class="pnrr-town-work-heading"><span class="pnrr-town-state ${statusClass(work.status)}">${escapeHtml(work.status)}</span><h4>${escapeHtml(work.title)}</h4></div>
      <dl><div><dt>CUP</dt><dd>${escapeHtml(work.cup)}</dd></div><div><dt>Quota PNRR</dt><dd>${escapeHtml(money2.format(work.funding))}</dd></div></dl>
    </article>`;
  }

  function townMarkup(town, works) {
    const concludedPercent = town.concluded / town.projects * 100;
    const worksMarkup = works.length
      ? `<div class="pnrr-town-works"><div class="pnrr-town-works-heading"><span class="overline">Opere fisiche</span><h4>${works.length === 1 ? 'Opera individuata' : `${works.length} opere individuate`}</h4></div>${works.map(workMarkup).join('')}</div>`
      : `<div class="pnrr-town-empty"><strong>Nessuna opera fisica nel sottoinsieme selezionato.</strong><p>Il Comune può comunque essere soggetto attuatore di servizi, acquisti o altri progetti PNRR.</p></div>`;

    return `<section class="topic-deep-dive pnrr-town-detail" data-pnrr-town-detail="true">
      <div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>PNRR a ${escapeHtml(town.town)}</h3></div><p>Progetti con il Comune come soggetto attuatore nella fotografia Regione Toscana dell'11 agosto 2026.</p></div>
      <div class="pnrr-town-summary-grid">
        <article><span>Progetti</span><strong>${number0.format(town.projects)}</strong><small>PNRR / PNRR-PNC</small></article>
        <article><span>Fase 5</span><strong>${number0.format(town.concluded)}</strong><small>${number1.format(concludedPercent)}% dei progetti</small></article>
        <article><span>Quota PNRR</span><strong>${money0.format(town.funding)}</strong><small>finanziamento censito</small></article>
        <article><span>Opere fisiche</span><strong>${number0.format(works.length)}</strong><small>con stato ReGiS di dettaglio</small></article>
      </div>
      ${worksMarkup}
      <div class="pnrr-town-note"><p><strong>Perimetri distinti.</strong> Le opere pubbliche BDAP-MOP sono un indicatore separato e comprendono interventi non PNRR. Qui compaiono soltanto i progetti PNRR validati con Regione Toscana.</p><a href="../../pnrr/">Apri il quadro Versilia e tutte le 22 opere <span aria-hidden="true">→</span></a></div>
    </section>`;
  }

  function townSlug() {
    const parts = location.pathname.split('/').filter(Boolean);
    const index = parts.indexOf('comuni');
    return index >= 0 ? parts[index + 1] || '' : '';
  }

  function isCommunityTownView() {
    return Boolean(document.querySelector('main[data-theme="comunita"]'));
  }

  function enhanceGeneral(data) {
    if (!location.pathname.includes('/confronta/comunita/')) return;
    if (document.querySelector('[data-pnrr-general-context="true"]')) return;
    const anchor = document.querySelector('#compare-benchmark') || document.querySelector('.topic-dashboard');
    const deep = data.pnrrDeepDive;
    if (!anchor || !deep) return;
    anchor.insertAdjacentHTML('afterend', generalMarkup(deep));
  }

  function enhanceTown(data) {
    if (!location.pathname.includes('/comuni/') || !isCommunityTownView()) return;
    if (document.querySelector('[data-pnrr-town-detail="true"]')) return;

    const oldSection = [...document.querySelectorAll('.topic-deep-dive')].find(section =>
      section.textContent?.includes('Cassa, opere e PNRR')
    );
    if (!oldSection) return;

    const slug = townSlug();
    const metricRow = data.metrics?.pnrrFunding?.rows?.find(row => row.slug === slug);
    const deepTown = data.pnrrDeepDive?.towns?.find(row => String(row.code) === String(metricRow?.code));
    if (!deepTown) return;
    const works = (data.pnrrDeepDive?.physicalWorks?.works || []).filter(work => work.town === deepTown.town);
    oldSection.outerHTML = townMarkup(deepTown, works);
  }

  async function enhance() {
    scheduled = false;
    try {
      const data = await loadData();
      enhanceGeneral(data);
      enhanceTown(data);
    } catch (error) {
      console.warn('PNRR town detail enhancer:', error);
    }
  }

  function scheduleEnhance() {
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(enhance);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleEnhance, { once: true });
  } else {
    scheduleEnhance();
  }
  new MutationObserver(scheduleEnhance).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('popstate', scheduleEnhance);
})();
