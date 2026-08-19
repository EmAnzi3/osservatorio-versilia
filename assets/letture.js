(() => {
  'use strict';
  const ROOT = new URL('../', document.currentScript?.src || location.href);
  const URLS = {
    config: new URL('data/letture.json', ROOT),
    data: new URL('data/site-data.json', ROOT),
    registry: new URL('data/source-registry.json', ROOT),
    state: new URL('data/source-monitor-state.json', ROOT)
  };
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const slug = value => String(value || '').toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const date = value => value ? new Date(value).toLocaleDateString('it-IT') : 'non disponibile';
  const metricHref = (key, metric) => new URL(`confronta/${metric?.meta?.theme || ''}/?indicatore=${encodeURIComponent(key)}`, ROOT).href;

  function displayValue(row) {
    if (!row) return '—';
    for (const key of ['formatted','display','labelValue']) if (row[key] !== undefined && row[key] !== null && String(row[key]).trim()) return String(row[key]);
    if (row.value === undefined || row.value === null || row.value === '') return '—';
    if (typeof row.value === 'number') return new Intl.NumberFormat('it-IT',{maximumFractionDigits:2,useGrouping:'always'}).format(row.value);
    return String(row.value);
  }

  function townName(row) {
    return row?.town || row?.municipality || row?.name || row?.comune || '';
  }

  function rows(metric) {
    return Array.isArray(metric?.rows) ? metric.rows.filter(row => townName(row))
      .sort((a,b)=>townName(a).localeCompare(townName(b),'it')) : [];
  }

  function statusFor(key, state, metric) {
    const operational = state?.metrics?.[key] || {};
    return {
      period: operational.publishedPeriod || metric?.meta?.year || '',
      checked: operational.checkedAt || state?.checkedAt || '',
      status: operational.status || ''
    };
  }

  function metricMarkup(key, metric, state) {
    if (!metric) return `<article class="reading-metric"><div><h3>${esc(key)}</h3><p>Indicatore non disponibile nel catalogo canonico.</p></div></article>`;
    const meta = metric.meta || {};
    const st = statusFor(key,state,metric);
    const list = rows(metric);
    const values = list.length ? `<div class="reading-values">${list.map(row=>`<div><span>${esc(townName(row))}</span><strong>${esc(displayValue(row))}</strong></div>`).join('')}</div>` : '';
    const preview = list.length
      ? `<strong>${list.length}/7</strong><span>valori comunali nel catalogo</span>`
      : metric?.dataStorage?.type === 'external-climate'
        ? `<strong>serie esterna</strong><span>storico climatico separato dal catalogo inline</span>`
        : `<strong>—</strong><span>nessuna riga comunale da mostrare</span>`;
    const description = meta.definition || meta.description || metric.description || '';
    return `<article class="reading-metric" data-reading-metric="${esc(key)}">
      <div><h3><a href="${metricHref(key,metric)}">${esc(meta.label || key)} →</a></h3><p>${esc(description)}</p></div>
      <div class="reading-metric-period"><strong>${esc(st.period || '—')}</strong><span>periodo pubblicato · stato ${esc(st.status || 'non classificato')}</span></div>
      <div class="reading-metric-preview">${preview}<span>ultimo controllo ${esc(date(st.checked))}</span></div>
      ${values}
    </article>`;
  }

  function detail(item, payload) {
    const { data, state } = payload;
    const metrics = item.metrics.map(key => metricMarkup(key, data.metrics?.[key], state)).join('');
    const themes = (item.themes || []).map(key => data.themes?.[key]?.label || key).join(' · ');
    const special = item.specialHref ? `<div class="reading-special"><p>Questa Lettura ha anche un approfondimento dedicato che usa gli stessi indicatori climatici e resta in bozza finché l’audit metodologico non è chiuso.</p><a href="${new URL(item.specialHref.replace(/^\//,''),ROOT).href}">Apri Meteo e clima →</a></div>` : '';
    return `<section class="reading-hero page-width"><div class="breadcrumbs"><a href="${new URL('letture/',ROOT).href}">Letture</a><span>›</span><strong>${esc(item.title)}</strong></div><span class="overline">${esc(themes)} · lettura guidata · bozza non indicizzata</span><h1>${esc(item.title)}</h1><p>Una lettura costruita esclusivamente su indicatori già presenti nell’Osservatorio. Valori, periodi e stato delle fonti non sono duplicati in questa pagina.</p><div class="reading-question"><span>Domanda</span><strong>${esc(item.question)}</strong></div></section>
    <section class="reading-answer"><div class="page-width reading-answer-grid"><span>Risposta breve</span><p>${esc(item.answer)}</p></div></section>
    <section class="reading-metrics page-width"><div class="reading-section-head"><div><span class="overline">Dato → confronto</span><h2>Gli indicatori che sostengono la lettura</h2></div><p>Ogni blocco mantiene visibile il proprio periodo. Quando esistono righe comunali, i sette Comuni sono mostrati in ordine alfabetico e senza graduatorie.</p></div><div class="reading-metric-list">${metrics}</div>${special}</section>
    <section class="reading-context"><div class="page-width"><div class="reading-section-head"><div><span class="overline">Contesto → interpretazione</span><h2>Cosa possiamo dire e dove fermarci</h2></div><p>La Lettura mette in relazione fenomeni distinti senza trasformare correlazioni o contemporaneità in rapporti causali.</p></div><div class="reading-context-grid"><article><h3>Cosa possiamo leggere</h3><p>${esc(item.answer)}</p></article><article><h3>Cosa non possiamo concludere</h3><p>${esc(item.caution)}</p></article></div><p class="reading-status-note">Stato generale delle fonti registrato il ${esc(date(state?.checkedAt))}. Per dettaglio, frequenza e controlli consulta <a href="${new URL('stato-dati/',ROOT).href}">Stato dei dati</a>.</p></div></section>`;
  }

  function index(config) {
    const cards = config.items.map((item,index)=>`<a class="reading-card" href="${new URL(`letture/${item.slug}/`,ROOT).href}"><span>Lettura ${String(index+1).padStart(2,'0')}</span><h2>${esc(item.title)}</h2><p>${esc(item.question)}</p><b>Apri la lettura →</b></a>`).join('');
    return `<section class="reading-hero page-width"><span class="overline">Osservatorio Versilia · nuovo livello editoriale · bozza</span><h1>Letture</h1><p>${esc(config.description)}</p><div class="reading-question"><span>Principio</span><strong>Dato → confronto → contesto → interpretazione. Mai il contrario.</strong></div></section><section class="reading-catalog page-width"><div class="reading-section-head"><div><span class="overline">Primo catalogo</span><h2>Sette domande, gli stessi dati</h2></div><p>Queste pagine non modificano il conteggio degli indicatori e non sostituiscono i confronti o le schede comunali.</p></div><div class="reading-cards">${cards}</div></section>`;
  }

  Promise.all(Object.values(URLS).map(url=>fetch(url).then(response=>{if(!response.ok) throw new Error(`${url.pathname}: ${response.status}`); return response.json();})))
    .then(([config,data,registry,state])=>{
      const app=document.getElementById('reading-app');
      const reading=document.body.dataset.reading || '';
      if (!reading) { app.innerHTML=index(config); return; }
      const item=config.items.find(candidate=>candidate.slug===reading);
      if (!item) throw new Error(`Lettura non configurata: ${reading}`);
      // Registry is deliberately fetched even when not rendered directly: it is part of the canonical contract
      // and keeps the reading renderer dependent on the same three authorities as Stato dei dati.
      if (!registry?.schemaVersion) throw new Error('Source registry non valido');
      app.innerHTML=detail(item,{data,state,registry});
    })
    .catch(error=>{
      console.error(error);
      document.getElementById('reading-app').innerHTML='<div class="app-error"><strong>Lettura non disponibile.</strong><p>I dati canonici necessari non sono stati caricati.</p></div>';
    });
})();
