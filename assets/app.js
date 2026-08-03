(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', script.src);
  const app = document.getElementById('app');
  const pageType = document.body.dataset.page || 'home';
  const pageTheme = document.body.dataset.theme || '';
  const pageTown = document.body.dataset.town || '';

  const themeIcons = {
    demografia: '◉', economia: '€', lavoro: '▣', istruzione: '◆', salute: '♥',
    mobilita: '↔', abitare: '⌂', ambiente: '♧', comunita: '▦'
  };

  const searchSynonyms = {
    population: ['abitanti', 'residenti', 'popolazione'],
    oldAgeIndex: ['anziani', 'invecchiamento', 'vecchiaia'],
    share65: ['anziani', 'over 65', 'terza età'],
    income: ['redditi', 'stipendi', 'irpef', 'dichiarazioni'],
    incomeUnder15k: ['redditi bassi', 'povertà', 'dichiaranti'],
    businessValueAdded: ['pil', 'ricchezza', 'produzione', 'economia locale'],
    labourProductivity: ['produttività', 'efficienza', 'valore per lavoratore'],
    industryValueAddedShare: ['industria', 'manifattura', 'produzione industriale'],
    industryWorkerShare: ['operai', 'occupati industria', 'addetti industria'],
    localUnits: ['imprese', 'aziende', 'attività economiche'],
    microUnits: ['pmi', 'piccole imprese', 'microimprese'],
    employmentRate: ['occupati', 'lavoratori', 'occupazione'],
    unemploymentRate: ['disoccupati', 'senza lavoro', 'disoccupazione'],
    activityRate: ['forza lavoro', 'attivi', 'partecipazione'],
    diplomaPlus: ['diplomati', 'titolo di studio', 'scuola superiore'],
    tertiary: ['laureati', 'laurea', 'università'],
    schoolSites: ['scuole', 'istituti scolastici'],
    lifeExpectancy: ['speranza di vita', 'longevità', 'salute'],
    mortalityAll: ['mortalità', 'decessi', 'cause di morte'],
    chronicTotal: ['cronici', 'malattie croniche', 'patologie croniche'],
    diabetes: ['diabete', 'malattie croniche'],
    dementia: ['demenza', 'alzheimer', 'non autosufficienza'],
    emergencyAccess: ['pronto soccorso', 'emergenza', 'accessi ps'],
    hospitalizedAll: ['ricoveri', 'ospedalizzazione', 'ospedale'],
    elderlyHomeCare: ['assistenza domiciliare', 'anziani', 'adi'],
    pharmaciesPer1000: ['farmacie', 'sanità'], hospitals: ['ospedali', 'posti letto', 'presidi'],
    outsideMunicipality: ['pendolari', 'lavoro fuori comune', 'spostamenti'],
    inboundCommuters: ['pendolari', 'entrata', 'flussi'], selfContainment: ['lavoro nel comune', 'autocontenimento'],
    roadInjuries: ['incidenti', 'feriti', 'sicurezza stradale'], motorization: ['auto', 'motorizzazione'],
    pollutingCars: ['auto inquinanti', 'euro 0', 'euro 3'], evPoints: ['ricarica', 'auto elettriche'],
    vacantHomes: ['case vuote', 'abitazioni non occupate'], singleHouseholds: ['persone sole', 'famiglie'],
    householdSize: ['componenti famiglia', 'nucleo familiare'], landUse: ['consumo di suolo', 'cementificazione'],
    landUseChange: ['nuovo suolo consumato'], recycling: ['raccolta differenziata', 'rifiuti'],
    wastePerResident: ['rifiuti pro capite', 'kg'], floodExposure: ['alluvione', 'rischio idraulico'],
    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],
    currentPayments: ['spesa corrente', 'pagamenti'], siopePayments: ['cassa', 'uscite'],
    publicWorks: ['opere pubbliche', 'cantieri'], pnrrFunding: ['pnrr', 'finanziamenti'],
    pnrrConcluded: ['pnrr', 'progetti conclusi']
  };

  const html = (value) => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const route = (path = '') => new URL(String(path).replace(/^\//, ''), ROOT).href;
  const asset = (path = '') => route(path);
  const normalize = (value) => String(value ?? '').toLocaleLowerCase('it')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

  const number0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 });
  const number1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number2 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const currency0 = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

  function formatValue(value, unit) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'n.d.';
    const v = Number(value);
    switch (unit) {
      case 'currency': return currency0.format(v);
      case 'millionCurrency': return `${number1.format(v)} mln €`;
      case 'percent': return `${number1.format(v)}%`;
      case 'index': return number1.format(v);
      case 'decimal': return number2.format(v);
      case 'years': return `${number2.format(v)} anni`;
      case 'per100': return `${number2.format(v)} ogni 100`;
      case 'per10k': return `${number1.format(v)} ogni 10.000`;
      case 'per1000': return `${number2.format(v)} ogni 1.000`;
      case 'per100k': return `${number2.format(v)} ogni 100.000`;
      case 'kg': return `${number0.format(v)} kg`;
      case 'hectares': return `${number2.format(v)} ha`;
      default: return number0.format(v);
    }
  }

  function interpretation(metric) {
    if (metric.polarity === 'positive') return 'Per questo indicatore un valore più alto è generalmente favorevole, ma non basta da solo a valutare il territorio.';
    if (metric.polarity === 'negative') return 'Per questo indicatore un valore più basso è generalmente favorevole: il primo posto indica quindi il valore più alto, non il risultato migliore.';
    return 'L’ordine descrive soltanto il valore numerico e non esprime un giudizio di qualità.';
  }

  function headerMarkup(data) {
    return `
      <a class="skip-link" href="#app">Vai al contenuto</a>
      <header class="site-header">
        <div class="site-header-inner">
          <a href="${route('')}" class="site-brand" aria-label="Osservatorio Versilia, torna alla home">
            <span class="site-brand-mark">O</span>
            <span class="site-brand-copy"><strong>Osservatorio Versilia</strong><small>Versilia in numeri</small></span>
          </a>
          <div class="site-header-actions">
            <nav aria-label="Navigazione principale">
              <a href="${route('#temi')}">Temi</a>
              <a href="${route('#comuni')}">Comuni</a>
              <a href="${route('progetto/')}">Il progetto</a>
              <a href="${route('segnala/')}">Segnala</a>
            </nav>
            <button class="global-search-trigger" type="button" aria-haspopup="dialog" aria-expanded="false">
              <span aria-hidden="true">⌕</span><span>Cerca</span><kbd>/</kbd>
            </button>
          </div>
        </div>
      </header>`;
  }

  function footerMarkup(data) {
    return `
      <footer class="site-footer">
        <div class="footer-about"><strong>Osservatorio Versilia</strong>
          <p>Un punto di accesso indipendente ai dati pubblici dei sette comuni della Versilia.</p>
          <p class="footer-disclaimer">Non è un sito istituzionale e non rappresenta gli enti citati.</p>
        </div>
        <nav class="footer-links" aria-label="Informazioni sul progetto">
          <a href="${route('progetto/')}">Il progetto</a>
          <a href="${route('progetto/#metodo')}">Metodo</a>
          <a href="${route('progetto/#licenza')}">Licenza</a>
          <a href="${route('progetto/#versioni')}">Versioni dei dati</a>
          <a href="${route('segnala/')}">Segnala un dato</a>
          <a href="mailto:contatti@osservatorioversilia.it">Contatti</a>
        </nav>
        <div class="footer-note">
          <span>7 comuni · 9 temi</span><span>v. dati ${html(data.version)}</span><span>aggiornato ${html(data.updated)}</span>
        </div>
      </footer>`;
  }

  function mountShell(data) {
    document.getElementById('site-header-mount').innerHTML = headerMarkup(data);
    document.getElementById('site-footer-mount').innerHTML = footerMarkup(data);
    installSearch(data);
  }

  function metricRows(data, metricKey, normalized = false) {
    const metric = data.metrics[metricKey];
    return metric.rows.map(row => ({
      ...row,
      displayValue: normalized && row.normalized ? row.normalized.value : row.value,
      displayUnit: normalized && row.normalized ? row.normalized.unit : metric.meta.unit
    })).sort((a, b) => (b.displayValue ?? -Infinity) - (a.displayValue ?? -Infinity));
  }

  function barRows(data, metricKey, options = {}) {
    const normalized = Boolean(options.normalized);
    const selectedTown = options.selectedTown || '';
    const rows = metricRows(data, metricKey, normalized);
    const max = Math.max(...rows.map(r => Number(r.displayValue) || 0), 0.0001);
    return rows.map((row, index) => {
      const query = new URLSearchParams({ tema: data.metrics[metricKey].meta.theme, indicatore: metricKey });
      const href = route(`comuni/${row.slug}/?${query}`);
      return `<a href="${href}" class="bar-row ${row.slug === selectedTown ? 'selected' : ''}" aria-label="${html(row.town)}: ${html(formatValue(row.displayValue, row.displayUnit))}">
        <span class="bar-rank">${index + 1}</span><span class="bar-town">${html(row.town)}</span>
        <span class="bar-track"><span class="bar-fill" style="width:${Math.max(1.5, (Number(row.displayValue) || 0) / max * 100)}%"></span>
          <span class="bar-hover-label">${html(row.town)} · ${html(formatValue(row.displayValue, row.displayUnit))}</span></span>
        <strong>${html(formatValue(row.displayValue, row.displayUnit))}</strong>
      </a>`;
    }).join('');
  }

  function themeCard(theme) {
    return `<button type="button" data-theme="${html(theme.key)}" class="theme-card" aria-pressed="false">
      <span class="theme-number">${html(theme.number)}</span>
      <span class="theme-icon"><span class="theme-icon-static" aria-hidden="true">${themeIcons[theme.key]}</span></span>
      <strong>${html(theme.label)}</strong><span class="theme-question">${html(theme.question)}</span><i aria-hidden="true">→</i>
    </button>`;
  }

  function townCard(data, town) {
    const pop = data.metrics.population.rows.find(r => r.code === town.code);
    const income = data.metrics.income.rows.find(r => r.code === town.code);
    const employment = data.metrics.employmentRate.rows.find(r => r.code === town.code);
    return `<a href="${route(`comuni/${pop.slug}/`)}" class="town-card">
      <div class="town-card-head"><img alt="Stemma di ${html(town.name)}" src="${asset(data.crests[town.name].replace(/^\//, ''))}"><span>Codice Istat ${html(town.code)}</span></div>
      <h3>${html(town.name)}</h3><dl>
        <div><dt>Residenti</dt><dd>${html(pop.formatted)}</dd></div>
        <div><dt>Reddito medio</dt><dd>${html(income.formatted)}</dd></div>
        <div><dt>Occupazione</dt><dd>${html(employment.formatted)}</dd></div>
      </dl><span class="text-link">Apri la scheda <b>→</b></span>
    </a>`;
  }

  function renderHome(data) {
    const themes = Object.values(data.themes);
    app.innerHTML = `<main>
      <section class="home-hero page-width">
        <div class="hero-copy"><span class="overline">Osservatorio civico · Versilia storica</span><h1>La Versilia,<br>comune per comune.</h1>
          <p class="hero-deck">Dati pubblici per capire come cambiano popolazione, lavoro, servizi, ambiente e qualità della vita nei sette comuni del territorio.</p></div>
        <div class="hero-intro"><span class="overline">Cosa puoi fare</span><p>Confronta i comuni su un tema oppure apri la scheda di un territorio per leggere numeri, andamento storico e posizione rispetto alla Versilia, alla Toscana e all’Italia.</p>
          <div class="hero-facts"><span>7 comuni</span><span>9 temi</span><span>51 indicatori</span><span>Aggiornato ${html(data.updated)}</span></div></div>
        <figure class="hero-photo"><img alt="Il litorale di Viareggio con le Alpi Apuane sullo sfondo" src="${'https://versilia-in-numeri.decent-raven-1888.chatgpt.site/versilia-viareggio-apuane.jpg'}">
          <figcaption>Viareggio e Alpi Apuane · Foto di Carlo Pelagalli, <a href="https://commons.wikimedia.org/wiki/File:Wv_Versilia_banner.jpg" target="_blank" rel="noreferrer">CC BY-SA 3.0 ↗</a></figcaption></figure>
      </section>
      <section class="theme-section page-width" id="temi"><div class="section-heading"><div><span class="overline">Esplora per tema</span><h2>Da dove vuoi cominciare?</h2></div><p>La selezione aggiorna subito il confronto territoriale.</p></div>
        <div class="theme-grid">${themes.map(themeCard).join('')}</div></section>
      <section id="home-explorer" class="explorer-panel page-width" aria-live="polite"></section>
      <section class="towns-section page-width" id="comuni"><div class="section-heading"><div><span class="overline">Esplora per territorio</span><h2>Un profilo per ogni comune</h2></div><p>Indicatori, andamento storico e posizione nel contesto.</p></div>
        <div class="town-card-grid">${data.towns.map(t => townCard(data, t)).join('')}</div></section>
      <section class="method-section page-width"><div class="method-title"><span class="overline">Metodo trasparente</span><h2>Numeri leggibili,<br>senza farli parlare più del dovuto.</h2></div>
        <div class="method-list">
          <article><span>01</span><div><h3>Fonte sempre visibile</h3><p>Ogni indicatore rimanda al produttore del dato e indica anno, unità e definizione.</p></div></article>
          <article><span>02</span><div><h3>Confronti omogenei</h3><p>Toscana e Italia compaiono soltanto quando periodo e perimetro statistico sono compatibili.</p></div></article>
          <article><span>03</span><div><h3>Nessuna pagella automatica</h3><p>Posizioni e distanze descrivono valori numerici, non giudizi politici o di qualità.</p></div></article>
        </div></section>
      <section class="project-callout page-width"><div><span class="overline">Un progetto civico indipendente</span><h2>Le fonti sono istituzionali. L’osservatorio non lo è.</h2></div>
        <div><p>Osservatorio Versilia riunisce dati pubblici dispersi, ne esplicita i limiti e mantiene sempre il collegamento alla fonte originaria.</p><a class="text-link" href="${route('progetto/')}">Scopri metodo e licenza <b>→</b></a></div></section>
      <section class="source-portals page-width"><strong>Fonti principali</strong><div><a href="https://www.istat.it/" target="_blank" rel="noreferrer">Istat ↗</a><a href="https://www.regione.toscana.it/statistiche" target="_blank" rel="noreferrer">Regione Toscana ↗</a><a href="https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php" target="_blank" rel="noreferrer">MEF ↗</a><a href="https://www.ars.toscana.it/" target="_blank" rel="noreferrer">ARS Toscana ↗</a></div></section>
    </main>`;

    let selectedTheme = 'demografia';
    let selectedMetric = data.themes[selectedTheme].metrics[0];
    const cards = [...document.querySelectorAll('.theme-card')];
    cards.forEach(card => card.addEventListener('click', () => {
      selectedTheme = card.dataset.theme;
      selectedMetric = data.themes[selectedTheme].metrics[0];
      cards.forEach(c => { c.classList.toggle('active', c === card); c.setAttribute('aria-pressed', c === card ? 'true' : 'false'); });
      renderHomeExplorer(data, selectedTheme, selectedMetric);
    }));
    cards[0]?.classList.add('active'); cards[0]?.setAttribute('aria-pressed', 'true');
    renderHomeExplorer(data, selectedTheme, selectedMetric);
  }

  function renderHomeExplorer(data, themeKey, metricKey) {
    const panel = document.getElementById('home-explorer');
    const theme = data.themes[themeKey];
    const metric = data.metrics[metricKey];
    panel.dataset.theme = themeKey;
    panel.innerHTML = `<div class="explorer-copy"><span class="overline">Confronto · ${html(theme.label)}</span><h2>${html(metric.meta.label)}</h2><p>${html(metric.meta.description)}</p>
      <div class="metric-switch">${theme.metrics.map(key => `<button type="button" data-metric="${key}" class="${key === metricKey ? 'active' : ''}">${html(data.metrics[key].meta.shortLabel)}</button>`).join('')}</div>
      <div class="explorer-stat"><span>${html(metric.aggregate.label)}</span><strong>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</strong><small>${html(metric.aggregate.note)}</small></div>
      <a class="source-link" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Apri la fonte originale <span aria-hidden="true">↗</span></a>
      <a href="${route(`confronta/${themeKey}/?indicatore=${metricKey}`)}" class="button-link">Apri il confronto completo <span>→</span></a></div>
      <div class="explorer-chart"><div class="comparison-bars">${barRows(data, metricKey)}</div></div>`;
    panel.querySelectorAll('[data-metric]').forEach(button => button.addEventListener('click', () => renderHomeExplorer(data, themeKey, button.dataset.metric)));
  }

  function metricControls(data, themeKey, metricKey) {
    const theme = data.themes[themeKey];
    return `<div class="metric-switch compact-list" role="tablist" aria-label="Indicatore">${theme.metrics.map(key => `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}">${html(data.metrics[key].meta.shortLabel)}</button>`).join('')}</div>
      <select class="metric-select-mobile" aria-label="Seleziona indicatore">${theme.metrics.map(key => `<option value="${key}" ${key === metricKey ? 'selected' : ''}>${html(data.metrics[key].meta.label)}</option>`).join('')}</select>`;
  }

  function renderCompare(data) {
    const themeKey = pageTheme || Object.keys(data.themes)[0];
    const theme = data.themes[themeKey];
    if (!theme) return renderNotFound();
    const params = new URLSearchParams(location.search);
    let metricKey = params.get('indicatore');
    if (!theme.metrics.includes(metricKey)) metricKey = theme.metrics[0];
    app.innerHTML = `<main class="inner-page" data-theme="${themeKey}">
      <div class="breadcrumbs page-width"><a href="${route('')}">Home</a><span>›</span><strong>${html(theme.label)}</strong></div>
      <section class="topic-hero page-width" data-theme="${themeKey}"><div class="topic-symbol"><span class="theme-icon-static" aria-hidden="true">${themeIcons[themeKey]}</span><small>${html(theme.number)}</small></div>
        <div><span class="overline">Confronto territoriale</span><h1>${html(theme.label)}</h1><p>${html(theme.description)}</p></div></section>
      <section class="topic-dashboard page-width" data-theme="${themeKey}"><aside class="topic-controls">${metricControls(data, themeKey, metricKey)}<div id="compare-definition"></div></aside><div id="compare-bars"></div></section>
      <section id="compare-benchmark" class="page-width"></section>
      ${themeKey === 'mobilita' ? crimeMarkup(data) : ''}
      <section class="topic-town-links page-width"><div><span class="overline">Schede comunali</span><h2>Apri il territorio</h2></div><div>${data.towns.map(t => `<a href="${route(`comuni/${normalize(t.name).replaceAll(' ', '-')}/?tema=${themeKey}&indicatore=${metricKey}`)}"><span>${html(t.name)}</span><b>→</b></a>`).join('')}</div></section>
    </main>`;
    const update = key => {
      metricKey = key;
      history.replaceState(history.state, '', `?indicatore=${encodeURIComponent(key)}`);
      document.querySelectorAll('[data-metric]').forEach(b => { b.classList.toggle('active', b.dataset.metric === key); b.setAttribute('aria-selected', b.dataset.metric === key ? 'true' : 'false'); });
      const select = document.querySelector('.metric-select-mobile'); if (select) select.value = key;
      renderCompareMetric(data, themeKey, key, false);
    };
    document.querySelectorAll('[data-metric]').forEach(b => b.addEventListener('click', () => update(b.dataset.metric)));
    document.querySelector('.metric-select-mobile')?.addEventListener('change', e => update(e.target.value));
    renderCompareMetric(data, themeKey, metricKey, false);
    installCrimeInteractions(data);
  }

  function renderCompareMetric(data, themeKey, metricKey, normalized) {
    const metric = data.metrics[metricKey];
    const def = document.getElementById('compare-definition');
    const bars = document.getElementById('compare-bars');
    const benchmark = document.getElementById('compare-benchmark');
    const hasNormalized = metric.rows.some(r => r.normalized);
    const aggregate = normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;
    const unit = normalized && metric.meta.normalized ? metric.meta.normalized.unit : metric.meta.unit;
    def.innerHTML = `${hasNormalized ? `<div class="scale-switch" role="group" aria-label="Scala"><button type="button" data-scale="raw" class="${normalized ? '' : 'active'}">Valore assoluto</button><button type="button" data-scale="normalized" class="${normalized ? 'active' : ''}">Rapportato</button></div>` : ''}
      <div class="indicator-definition"><h2>${html(normalized && metric.meta.normalized ? metric.meta.normalized.label : metric.meta.label)}</h2><p>${html(normalized && metric.meta.normalized ? metric.meta.normalized.description : metric.meta.description)}</p>
        <dl><div><dt>Anno</dt><dd>${html(metric.meta.year)}</dd></div><div><dt>Fonte</dt><dd><a href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">${html(metric.meta.source)} ↗</a></dd></div><div><dt>${html(aggregate.label)}</dt><dd>${html(formatValue(aggregate.value, unit))}</dd></div></dl>
        <small class="aggregate-note">${html(aggregate.note)}</small><div class="data-actions"><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div></div>`;
    bars.innerHTML = `<div class="topic-bars"><div class="comparison-bars">${barRows(data, metricKey, { normalized })}</div></div>`;
    def.querySelectorAll('[data-scale]').forEach(button => button.addEventListener('click', () => renderCompareMetric(data, themeKey, metricKey, button.dataset.scale === 'normalized')));
    def.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data, metricKey, normalized));
    def.querySelector('[data-print]')?.addEventListener('click', () => window.print());
    benchmark.innerHTML = benchmarkMarkup(metric, aggregate, unit, null);
  }

  function benchmarkMarkup(metric, aggregate, unit, localRow) {
    const b = metric.meta.benchmark;
    if (!b) return `<section class="benchmark-unavailable"><span class="overline">Confronto esterno</span><h2>Dato non perfettamente comparabile</h2><p>Per questo indicatore non è disponibile un confronto omogeneo con Toscana e Italia. Il sito evita di affiancare valori con perimetri o anni incompatibili.</p></section>`;
    const firstLabel = localRow ? localRow.town : aggregate.label.replace('Valore ', '').replace('Media ', '').replace('Quota ', '').replace('Tasso ', '');
    const firstValue = localRow ? (localRow.benchmarkValue ?? localRow.value) : aggregate.value;
    return `<section class="benchmark-section"><div class="section-heading compact"><div><span class="overline">Confronto omogeneo · ${html(b.year)}</span><h2>Territorio, Toscana${b.italy !== null && b.italy !== undefined ? ' e Italia' : ''}</h2></div></div>
      <div class="benchmark-grid"><article class="benchmark-card benchmark-local"><span>${html(firstLabel)}</span><strong>${html(formatValue(firstValue, unit))}</strong><small>${localRow ? `Dato comunale riferito al ${html(b.year)}.` : html(aggregate.note)}</small></article>
      <article class="benchmark-card"><span>Toscana</span><strong>${html(formatValue(b.tuscany, unit))}</strong><small>${html(b.source)}</small></article>
      ${b.italy !== null && b.italy !== undefined ? `<article class="benchmark-card"><span>Italia</span><strong>${html(formatValue(b.italy, unit))}</strong><small>${html(b.source)}</small></article>` : ''}</div>
      <p class="benchmark-note">${html(b.note || '')} <a href="${html(b.url)}" target="_blank" rel="noreferrer">Apri la fonte ↗</a></p></section>`;
  }

  function downloadMetricCSV(data, metricKey, normalized = false) {
    const metric = data.metrics[metricKey];
    const rows = metricRows(data, metricKey, normalized);
    const label = normalized && metric.meta.normalized ? metric.meta.normalized.label : metric.meta.label;
    const lines = [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Valore', 'Unità', 'Fonte']];
    rows.forEach(row => lines.push([row.town, row.code, label, metric.meta.year, row.displayValue, row.displayUnit, metric.sourceUrl]));
    const csv = '\ufeff' + lines.map(line => line.map(cell => `"${String(cell ?? '').replaceAll('"', '""')}"`).join(';')).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `osservatorio-versilia-${metricKey}.csv`; a.click(); URL.revokeObjectURL(a.href);
  }

  function findTown(data, slug) {
    return data.towns.find(t => normalize(t.name).replaceAll(' ', '-') === slug);
  }

  function renderTown(data) {
    const town = findTown(data, pageTown);
    if (!town) return renderNotFound();
    const params = new URLSearchParams(location.search);
    let themeKey = params.get('tema') || 'demografia';
    if (!data.themes[themeKey]) themeKey = 'demografia';
    let metricKey = params.get('indicatore');
    if (!data.themes[themeKey].metrics.includes(metricKey)) metricKey = data.themes[themeKey].metrics[0];
    const pop = data.metrics.population.rows.find(r => r.code === town.code);
    const income = data.metrics.income.rows.find(r => r.code === town.code);
    const employment = data.metrics.employmentRate.rows.find(r => r.code === town.code);
    app.innerHTML = `<main class="inner-page" data-theme="${themeKey}">
      <div class="breadcrumbs page-width"><a href="${route('')}">Home</a><span>›</span><strong>${html(town.name)}</strong></div>
      <section class="town-hero page-width"><div class="town-identity"><img alt="Stemma di ${html(town.name)}" src="${asset(data.crests[town.name].replace(/^\//, ''))}"><div><span class="overline">Profilo comunale · Codice Istat ${html(town.code)}</span><h1>${html(town.name)}</h1><p>Dati pubblici, confronti territoriali e serie storiche disponibili.</p></div></div>
        <dl class="town-headline-stats"><div><dt>Residenti</dt><dd>${html(pop.formatted)}</dd></div><div><dt>Reddito medio</dt><dd>${html(income.formatted)}</dd></div><div><dt>Occupazione</dt><dd>${html(employment.formatted)}</dd></div></dl></section>
      <section class="town-brief page-width"><div><span class="overline">In sintesi</span><h2>Tre coordinate del territorio</h2></div>
        <article><span>Età media</span><strong>${html(number1.format(town.averageAge))} anni</strong><small>Dato demografico sintetico.</small></article>
        <article><span>Presenze turistiche 2025</span><strong>${html(number0.format(town.tourism.presences2025))}</strong><small>Notti nelle strutture ricettive.</small></article>
        <article><span>Raccolta differenziata 2024</span><strong>${html(number2.format(town.governance.services.recycling2024))}%</strong><small>Quota dei rifiuti raccolta separatamente.</small></article></section>
      <nav class="theme-nav page-width" aria-label="Temi del profilo">${Object.values(data.themes).map(theme => `<a data-theme="${theme.key}" class="${theme.key === themeKey ? 'active' : ''}" href="${route(`comuni/${pageTown}/?tema=${theme.key}&indicatore=${theme.metrics[0]}`)}"><span>${themeIcons[theme.key]}</span>${html(theme.label)}</a>`).join('')}</nav>
      <section id="town-topic" class="town-topic page-width" data-theme="${themeKey}"></section>
      ${themeKey === 'mobilita' ? crimeMarkup(data) : ''}
    </main>`;
    renderTownMetric(data, town, themeKey, metricKey);
    installCrimeInteractions(data);
  }

  function renderTownMetric(data, town, themeKey, metricKey) {
    const theme = data.themes[themeKey];
    const metric = data.metrics[metricKey];
    const row = metric.rows.find(r => r.code === town.code);
    const ranked = metricRows(data, metricKey);
    const rank = ranked.findIndex(r => r.code === town.code) + 1;
    const container = document.getElementById('town-topic');
    container.innerHTML = `<div class="town-topic-heading"><div><span class="overline">${html(theme.label)} · ${html(metric.meta.year)}</span><h2>${html(metric.meta.label)}</h2><p>${html(metric.meta.description)}</p></div><div class="data-actions"><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div></div>
      <div class="town-metric-layout"><article class="town-metric-primary"><span>Valore di ${html(town.name)}</span><strong>${html(formatValue(row.value, metric.meta.unit))}</strong><p>${html(metric.meta.description)}</p>
        ${row.normalized ? `<div class="normalized-companion"><b>${html(row.normalized.label)}: ${html(formatValue(row.normalized.value, row.normalized.unit))}</b><br>${html(row.normalized.description)}</div>` : ''}
        <div><span>Anno ${html(metric.meta.year)} · ${html(metric.meta.source)}</span><a class="inline-source-link" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte originale ↗</a></div></article>
        <aside class="versilia-position"><span>Posizione nella Versilia</span><strong>${rank}<sup>°</sup> <small>valore più alto su 7</small></strong><p>${html(interpretation(metric.meta))}</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</b></div></aside></div>
      ${row.series ? `<section class="history-panel"><div class="panel-title"><div><span class="overline">Serie storica</span><h3>Come cambia nel tempo</h3></div></div>${seriesChart(row.series, metric.meta.unit)}</section>` : ''}
      <section class="all-indicators"><div class="section-heading compact"><div><span class="overline">Tutti gli indicatori · ${html(theme.label)}</span><h3>Scegli un altro dato</h3></div></div>
        <div class="indicator-card-grid">${theme.metrics.map(key => indicatorCard(data, town, themeKey, key, metricKey)).join('')}</div></section>
      ${deepDiveMarkup(data, town, themeKey)}
      ${townBenchmarkMarkup(metric, row, town)}`;
    container.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data, metricKey));
    container.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  }

  function townBenchmarkMarkup(metric, row, town) {
    const b = metric.meta.benchmark;
    if (!b) return `<section class="benchmark-unavailable town-benchmark"><span class="overline">Confronto esterno</span><h2>Dato non perfettamente comparabile</h2><p>Per questo indicatore non è disponibile un confronto omogeneo con Toscana e Italia.</p></section>`;
    const localValue = row.benchmarkValue ?? row.value;
    return `<section class="town-benchmark"><div><div><span class="overline">Confronto omogeneo · ${html(b.year)}</span><h3>${html(town.name)}, Toscana${b.italy !== null && b.italy !== undefined ? ' e Italia' : ''}</h3></div><p>${html(b.note || '')}</p></div>
      <div class="town-benchmark-values"><article><span>${html(town.name)}</span><strong>${html(formatValue(localValue, metric.meta.unit))}</strong><small>Dato comunale riferito al ${html(b.year)}.</small></article><article><span>Toscana</span><strong>${html(formatValue(b.tuscany, metric.meta.unit))}</strong><small>${html(b.source)}</small></article>${b.italy !== null && b.italy !== undefined ? `<article><span>Italia</span><strong>${html(formatValue(b.italy, metric.meta.unit))}</strong><small>${html(b.source)}</small></article>` : ''}</div>
      <a class="benchmark-source" href="${html(b.url)}" target="_blank" rel="noreferrer">Apri la fonte del confronto ↗</a></section>`;
  }

  function indicatorCard(data, town, themeKey, key, activeKey) {
    const metric = data.metrics[key]; const row = metric.rows.find(r => r.code === town.code);
    return `<a class="indicator-card ${key === activeKey ? 'active' : ''}" href="${route(`comuni/${pageTown}/?tema=${themeKey}&indicatore=${key}`)}"><span>${html(metric.meta.year)}</span><strong>${html(metric.meta.shortLabel)}</strong><b>${html(row.formatted)}</b></a>`;
  }

  function seriesChart(series, unit) {
    const values = series.values.map(Number); const years = series.years;
    const min = Math.min(...values), max = Math.max(...values); const range = max - min || 1;
    const width = 720, height = 250, padX = 42, padY = 34;
    const pts = values.map((v, i) => ({ x: padX + i * (width - padX * 2) / Math.max(1, values.length - 1), y: padY + (max - v) / range * (height - padY * 2), v, year: years[i] }));
    const line = pts.map(p => `${p.x},${p.y}`).join(' ');
    const area = `${padX},${height - padY} ${line} ${width - padX},${height - padY}`;
    const grid = [0, .5, 1].map(frac => { const y = padY + frac * (height - padY * 2); return `<line class="chart-grid" x1="${padX}" y1="${y}" x2="${width - padX}" y2="${y}"/>`; }).join('');
    return `<div class="chart-shell"><div class="trend-chart"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Serie storica">
      ${grid}<polygon class="chart-area" points="${area}"/><polyline class="chart-line" points="${line}"/>
      ${pts.map((p, i) => `<circle class="chart-dot" cx="${p.x}" cy="${p.y}" r="4"/><text class="chart-label" x="${p.x}" y="${height - 8}" text-anchor="middle">${html(p.year)}</text>${i === pts.length - 1 ? `<text class="chart-value" x="${p.x}" y="${Math.max(14, p.y - 12)}" text-anchor="end">${html(formatValue(p.v, unit))}</text>` : ''}`).join('')}</svg></div></div>
      <table class="chart-a11y-table"><thead><tr><th>Anno</th><th>Valore</th></tr></thead><tbody>${pts.map(p => `<tr><td>${html(p.year)}</td><td>${html(formatValue(p.v, unit))}</td></tr>`).join('')}</tbody></table>`;
  }

  function deepDiveMarkup(data, town, themeKey) {
    const detail = data.details[town.code];
    if (!detail) return '';
    if (themeKey === 'economia') {
      const e = detail.economy;
      const maxWorkers = Math.max(...e.topSectors.map(s => s.workers), 1);
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Struttura economica</h3></div><p>Fasce di reddito, capacità ricettiva e principali settori per presenza locale. I valori derivano dalle stesse fonti richiamate negli indicatori.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Strutture ricettive</span><strong>${number0.format(e.tourismStructures)}</strong><small>Anno ${html(e.tourismYear)}</small></article><article class="deep-fact"><span>Posti letto</span><strong>${number0.format(e.tourismBeds)}</strong><small>Hotel e altre strutture</small></article><article class="deep-fact"><span>Dichiaranti</span><strong>${number0.format(town.taxpayers)}</strong><small>Anno ${html(e.incomeYear)}</small></article><article class="deep-fact"><span>Permanenza media</span><strong>${number2.format(town.tourism.averageStay)}</strong><small>Notti per arrivo</small></article></div>
        <div class="deep-columns"><div><h4>Principali settori per addetti</h4><div class="deep-bar-list">${e.topSectors.map(s => `<div class="deep-bar-row"><div><span>${html(s.label)}</span><strong>${number2.format(s.workers)}</strong></div><div class="deep-bar-track"><span style="width:${s.workers / maxWorkers * 100}%"></span></div><small>${number0.format(s.localUnits)} unità locali</small></div>`).join('')}</div></div>
        <div><h4>Dichiaranti per fascia di reddito</h4><ul class="deep-list">${e.incomeBands.map(b => `<li><span>${html(b.label)}</span><strong>${number0.format(b.people)}</strong></li>`).join('')}</ul></div></div></section>`;
    }
    if (themeKey === 'mobilita') {
      const m = detail.mobility;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Flussi e parco veicolare</h3></div><p>Pendolarismo rilevato dal censimento e consistenza del parco veicolare. Il saldo non misura la qualità della mobilità.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Escono dal comune</span><strong>${number0.format(m.outbound)}</strong><small>Pendolari · ${html(m.year)}</small></article><article class="deep-fact"><span>Entrano nel comune</span><strong>${number0.format(m.inbound)}</strong><small>Pendolari · ${html(m.year)}</small></article><article class="deep-fact"><span>Saldo</span><strong>${number0.format(m.balance)}</strong><small>Entrate meno uscite</small></article><article class="deep-fact"><span>Autocontenimento</span><strong>${number1.format(m.selfContainment)}%</strong><small>Lavora nello stesso comune</small></article></div>
        <div class="deep-columns"><div><h4>Destinazioni principali</h4><ul class="deep-list">${m.topDestinations.map(x => `<li><span>${html(x.name)}</span><strong>${number0.format(x.people)}</strong></li>`).join('')}</ul></div><div><h4>Origini principali</h4><ul class="deep-list">${m.topOrigins.map(x => `<li><span>${html(x.name)}</span><strong>${number0.format(x.people)}</strong></li>`).join('')}</ul></div></div>
        <div class="deep-inline-note"><span>Autovetture registrate</span><strong>${number0.format(m.cars)}</strong><small>${number1.format(m.motorization)} auto ogni 1.000 residenti; ${number1.format(m.pollutingCars)}% nelle classi più inquinanti.</small></div></section>`;
    }
    if (themeKey === 'ambiente') {
      const e = detail.environment;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Pressioni ambientali</h3></div><p>Andamento dei rifiuti, incremento netto di suolo consumato ed esposizione della popolazione ai rischi territoriali.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Raccolta differenziata</span><strong>${number2.format(e.recycling.at(-1))}%</strong><small>${html(e.wasteYears.at(-1))}</small></article><article class="deep-fact"><span>Rifiuti per residente</span><strong>${number0.format(e.wasteKgPerResident.at(-1))} kg</strong><small>${html(e.wasteYears.at(-1))}</small></article><article class="deep-fact"><span>Nuovo suolo consumato</span><strong>${number2.format(e.landUseNetHa.reduce((sum, value) => sum + Number(value || 0), 0))} ha</strong><small>Somma degli intervalli disponibili</small></article><article class="deep-fact"><span>Intervalli ISPRA</span><strong>${number0.format(e.landIntervals.length)}</strong><small>Serie monitorata</small></article></div>
        <div class="risk-grid"><article><span>Esposizione al rischio alluvioni</span><strong>${number0.format(e.flood.population)} persone</strong><dl><div><dt>Quota residenti</dt><dd>${number1.format(e.flood.populationPct)}%</dd></div><div><dt>Edifici</dt><dd>${number0.format(e.flood.buildings)}</dd></div></dl></article><article><span>Esposizione al rischio frane</span><strong>${number0.format(e.landslide.population)} persone</strong><dl><div><dt>Quota residenti</dt><dd>${number1.format(e.landslide.populationPct)}%</dd></div><div><dt>Edifici</dt><dd>${number0.format(e.landslide.buildings)}</dd></div></dl></article></div></section>`;
    }
    if (themeKey === 'comunita') {
      const g = detail.government;
      const completed = g.pnrrProjects ? g.pnrrConcluded / g.pnrrProjects * 100 : 0;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Cassa, opere e PNRR</h3></div><p>Pagamenti e incassi di cassa, valore delle opere monitorate e stato dei progetti PNRR censiti.</p></div>
        <div class="government-grid"><article><span>Pagamenti</span><strong>${currency0.format(g.payments)}</strong><small>Anno ${html(g.year)}</small></article><article><span>Incassi</span><strong>${currency0.format(g.receipts)}</strong><small>Saldo ${currency0.format(g.cashBalance)}</small></article><article><span>Opere monitorate</span><strong>${number0.format(g.publicWorks)}</strong><small>Valore ${currency0.format(g.publicWorksValue)}</small></article><article><span>Progetti PNRR conclusi</span><strong>${number0.format(g.pnrrConcluded)} su ${number0.format(g.pnrrProjects)}</strong><div class="progress-track"><span style="width:${completed}%"></span></div><p>${currency0.format(g.pnrrFunding)} di risorse assegnate.</p></article></div></section>`;
    }
    return '';
  }

  function crimeMarkup(data) {
    return `<section class="crime-context page-width" id="criminalita"><div class="crime-context-copy"><span class="overline">Contesto sovracomunale</span><h2>Criminalità e delitti denunciati</h2><p>Il dato non è disponibile in forma omogenea per comune. Viene quindi mostrato per Provincia di Lucca, Toscana e Italia, senza attribuirlo ai singoli territori.</p><a class="source-pill" href="https://www.istat.it/" target="_blank" rel="noreferrer">Fonte Istat ↗</a></div>
      <div class="crime-context-data"><div class="crime-tabs">${['total','theft','burglary','fraud'].map((k, i) => `<button type="button" class="${i === 0 ? 'active' : ''}" data-crime="${k}">${{total:'Totale',theft:'Furti',burglary:'In abitazione',fraud:'Truffe e frodi'}[k]}</button>`).join('')}</div><div id="crime-data"></div></div></section>`;
  }

  function installCrimeInteractions(data) {
    const root = document.querySelector('.crime-context'); if (!root) return;
    const update = key => {
      root.querySelectorAll('[data-crime]').forEach(b => b.classList.toggle('active', b.dataset.crime === key));
      const labels = { total:'Delitti denunciati', theft:'Furti denunciati', burglary:'Furti in abitazione', fraud:'Truffe e frodi informatiche' };
      document.getElementById('crime-data').innerHTML = `<h3>${labels[key]} · ${html(data.crime.year)}</h3><div class="crime-stats">${data.crime.areas.map(area => `<article><span>${html(area.name)}</span><strong>${number1.format(area.values[key])}</strong><small>ogni 100.000 abitanti</small></article>`).join('')}</div>`;
    };
    root.querySelectorAll('[data-crime]').forEach(b => b.addEventListener('click', () => update(b.dataset.crime)));
    update('total');
  }

  function renderProject(data) {
    const sources = [
      ['Istat','https://www.istat.it/'],['Istat — Frame SBS Territoriale',data.businessSource],['Eurostat','https://ec.europa.eu/eurostat/'],['Regione Toscana','https://www.regione.toscana.it/statistiche'],['Ministero dell’economia e delle finanze','https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'],['ARS Toscana — La salute dei comuni',data.arsSource],['ISPRO — Registro di mortalità regionale','https://www.ispro.toscana.it/registro-mortalita-regionale-rmr'],['ISPRA','https://www.isprambiente.gov.it/'],['BDAP','https://openbdap.rgs.mef.gov.it/'],['SIOPE','https://www.siope.it/'],['Italia Domani — Open data PNRR','https://www.italiadomani.gov.it/it/catalogo-open-data.html'],['ANAC — Open data','https://dati.anticorruzione.it/opendata'],['Cruscotto Italia — AgID','https://cruscotto-italia.dati.gov.it/']
    ];
    const versions = [
      ['2026.08.3','2 agosto 2026','51 indicatori. Ampliata la salute con speranza di vita, mortalità, cronicità, pronto soccorso, ricoveri e assistenza domiciliare, usando tassi comunali e aggregati ufficiali ARS Toscana.'],
      ['2026.08.2','2 agosto 2026','43 indicatori. Aggiunti valore aggiunto delle unità locali, produttività per addetto e quote dell’industria, con confronti omogenei Toscana–Italia e perimetro distinto dal PIL.'],
      ['2026.08.1','2 agosto 2026','39 indicatori e nuovi approfondimenti comunali su struttura economica, pendolarismo reale, pressioni ambientali, cassa pubblica, opere, PNRR e contratti.'],
      ['2026.08','agosto 2026','7 comuni, 9 temi e 27 indicatori con fonti dirette, confronti ponderati, valori normalizzati ed esportazione CSV.'],
      ['2026.07','luglio 2026','Prima raccolta strutturata e prototipo delle viste comparative e comunali.']
    ];
    app.innerHTML = `<main class="editorial-page"><section class="editorial-hero page-width"><span class="overline">Il progetto</span><h1>Un solo posto per capire la Versilia.</h1><p>I dati pubblici esistono, ma spesso sono dispersi tra portali, allegati e fogli di calcolo. Osservatorio Versilia li riunisce, li spiega e li rende confrontabili senza nasconderne limiti e provenienza.</p></section>
      <section class="project-story page-width"><div><span class="section-number">01</span><h2>Perché nasce</h2></div><div class="prose"><p>Per trovare un numero comunale non dovrebbe essere necessario conoscere decine di banche dati, interpretare formati diversi o ricostruire ogni volta il significato di una voce.</p><p>Il progetto è ideato e curato da <strong>Emanuele Anzilotti</strong> con un obiettivo semplice: offrire un punto di accesso chiaro ai dati che aiutano a leggere Massarosa e gli altri comuni della Versilia storica.</p></div></section>
      <section class="independence-note page-width" aria-label="Natura del progetto"><div><span class="overline">Un progetto civico indipendente</span><h2>Le fonti sono istituzionali.<br>L’osservatorio non lo è.</h2></div><p>Osservatorio Versilia non rappresenta Comuni, Provincia, Regione, Istat o altri enti citati. Le amministrazioni e gli istituti produttori restano la fonte autorevole dei dati; eventuali errori di trascrizione, elaborazione o interpretazione sono responsabilità del progetto.</p></section>
      <section class="method-detail page-width" id="metodo"><div class="section-heading"><div><span class="section-number">02</span><h2>Il metodo</h2></div><p>Cinque regole per evitare confronti solo apparentemente precisi.</p></div><ol class="principles-grid">
        ${[['Scala certa','Un dato entra nelle schede comunali solo quando è davvero disponibile a quel livello territoriale.'],['Contesto visibile','Anno, unità, definizione e fonte accompagnano sempre il numero.'],['Confronti omogenei','Toscana e Italia compaiono soltanto quando perimetro e periodo sono compatibili.'],['Aggregazioni dichiarate','Totali e medie della Versilia indicano come sono stati calcolati, incluse le ponderazioni.'],['Nessun voto','Posizioni e distanze descrivono i valori: non diventano pagelle o giudizi politici automatici.']].map((x,i)=>`<li><span>0${i+1}</span><h3>${x[0]}</h3><p>${x[1]}</p></li>`).join('')}</ol></section>
      <section class="source-directory page-width"><div><span class="section-number">03</span><h2>Le fonti</h2></div><div><p>Ogni indicatore rimanda alla propria fonte. Tra i principali produttori e portali utilizzati:</p><ul>${sources.map(([name,url])=>`<li><a href="${html(url)}" target="_blank" rel="noreferrer">${html(name)} <span>↗</span></a></li>`).join('')}</ul></div></section>
      <section class="license-section page-width" id="licenza"><div><span class="section-number">04</span><h2>Licenza e riuso</h2></div><div class="prose"><p>Salvo diversa indicazione, testi, elaborazioni e visualizzazioni originali di Osservatorio Versilia sono disponibili con licenza <a href="https://creativecommons.org/licenses/by/4.0/deed.it" target="_blank" rel="noreferrer">CC BY 4.0</a>: possono essere condivisi e adattati citando la fonte.</p><p>Dati, stemmi, fotografie e materiali di terzi mantengono le condizioni d’uso e le licenze indicate dai rispettivi titolari. Per un uso ufficiale o amministrativo va sempre consultata la fonte originaria.</p></div></section>
      <section class="versions-section page-width" id="versioni"><div><span class="section-number">05</span><h2>Versioni dei dati</h2></div><div class="version-list">${versions.map(v=>`<article><div><strong>${v[0]}</strong><time>${v[1]}</time></div><p>${v[2]}</p></article>`).join('')}<p class="update-policy">Le correzioni puntuali possono essere pubblicate subito; gli aggiornamenti organici ricevono un nuovo numero di versione e una data visibile in tutto il sito.</p></div></section>
      <section class="contact-panel page-width"><div><span class="overline">Manca qualcosa?</span><h2>Un osservatorio migliora anche grazie alle segnalazioni.</h2></div><div><p>Puoi indicare un errore, una fonte più recente o proporre un nuovo indicatore comunale verificabile.</p><a class="button-link" href="${route('segnala/')}">Invia una segnalazione</a><a class="plain-contact" href="mailto:contatti@osservatorioversilia.it">contatti@osservatorioversilia.it</a></div></section>
    </main>`;
  }

  function renderFeedback(data) {
    app.innerHTML = `<main class="editorial-page"><section class="editorial-hero compact page-width"><span class="overline">Segnala</span><h1>Un dato da correggere o aggiungere?</h1><p>Indica l’informazione, il territorio e possibilmente una fonte verificabile. Il modulo prepara un’email nel programma di posta del dispositivo: non salva dati sul sito.</p></section>
      <section class="feedback-layout page-width"><aside><span class="overline">Prima di inviare</span><h2>Più dettagli dai, più semplice sarà verificare.</h2><ul><li>Indica il comune o se riguarda tutta la Versilia.</li><li>Scrivi il nome dell’indicatore o del tema.</li><li>Allega nel testo un link alla fonte istituzionale.</li><li>Spiega con precisione cosa non torna.</li></ul><p>Puoi anche scrivere direttamente a <a href="mailto:contatti@osservatorioversilia.it">contatti@osservatorioversilia.it</a>.</p></aside>
        <form class="feedback-form"><div class="form-row"><label>Tipo di segnalazione<select name="category" required><option value="" disabled selected>Seleziona</option><option>Errore o dato da correggere</option><option>Nuovo indicatore</option><option>Fonte o dato più recente</option><option>Suggerimento sul sito</option></select></label><label>Comune o territorio<select name="town" required>${['Tutta la Versilia',...data.towns.map(t=>t.name)].map(x=>`<option>${html(x)}</option>`).join('')}</select></label></div>
        <label>Indicatore o tema<input name="indicator" placeholder="Es. popolazione residente, viabilità, istruzione"></label><label>Link alla fonte<input name="source" type="url" inputmode="url" placeholder="https://…"></label><label>Cosa vuoi segnalare?<textarea name="message" rows="7" required placeholder="Descrivi il dato, l’errore o il suggerimento con le informazioni utili per verificarlo."></textarea></label>
        <div class="form-row"><label>Nome <span>(facoltativo)</span><input name="name" autocomplete="name"></label><label>Email <span>(facoltativa)</span><input name="email" type="email" autocomplete="email"></label></div><div class="form-submit"><button type="submit">Prepara l’email</button><p>Il modulo non salva né invia dati: apre il programma di posta del tuo dispositivo con un messaggio già compilato.</p></div><p class="form-status" role="status" hidden>Email preparata. Se non si è aperto nulla, scrivi a contatti@osservatorioversilia.it.</p></form></section></main>`;
    const form = document.querySelector('.feedback-form');
    form.addEventListener('submit', event => {
      event.preventDefault(); const fd = new FormData(form);
      const category = String(fd.get('category') || ''), town = String(fd.get('town') || '');
      const subject = `[Osservatorio Versilia] ${category} · ${town}`;
      const body = [`Tipo: ${category}`,`Comune/territorio: ${town}`,`Indicatore o tema: ${fd.get('indicator') || 'non specificato'}`,`Fonte proposta: ${fd.get('source') || 'non specificata'}`,'',String(fd.get('message') || ''),'',`Nome: ${fd.get('name') || 'non indicato'}`,`Email: ${fd.get('email') || 'non indicata'}`].join('\n');
      document.querySelector('.form-status').hidden = false;
      location.href = `mailto:contatti@osservatorioversilia.it?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
  }

  function installSearch(data) {
    const trigger = document.querySelector('.global-search-trigger');
    const categories = ['Indicatori comunali','Contesti sovracomunali','Temi','Comuni'];
    const items = [
      ...Object.entries(data.metrics).map(([key,m]) => ({ id:`metric-${key}`, label:m.meta.label, description:`${data.themes[m.meta.theme].label} · ${m.meta.year} · ${m.meta.description}`, category:'Indicatori comunali', href:route(`confronta/${m.meta.theme}/?indicatore=${key}`), badge:data.themes[m.meta.theme].label, keywords:normalize([m.meta.label,m.meta.shortLabel,m.meta.description,m.meta.source,data.themes[m.meta.theme].label,...(searchSynonyms[key]||[])].join(' ')) })),
      { id:'context-crime', label:'Criminalità e delitti denunciati', description:'Provincia di Lucca, Toscana e Italia · 2024. Il dato non è disponibile in forma omogenea per comune.', category:'Contesti sovracomunali', href:route('confronta/mobilita/#criminalita'), badge:'Dato provinciale', keywords:normalize('criminalità reati delitti furti truffe sicurezza provincia lucca') },
      ...Object.values(data.themes).map(t => ({ id:`theme-${t.key}`, label:t.label, description:`${t.question} ${t.description}`, category:'Temi', href:route(`confronta/${t.key}/`), badge:`${t.metrics.length} indicatori`, keywords:normalize(`${t.label} ${t.question} ${t.description}`) })),
      ...data.towns.map(t => ({ id:`town-${t.code}`, label:t.name, description:`Profilo comunale · codice Istat ${t.code}`, category:'Comuni', href:route(`comuni/${normalize(t.name).replaceAll(' ','-')}/`), badge:'Comune', keywords:normalize(`${t.name} comune territorio codice Istat ${t.code}`) }))
    ];
    const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','metric-roadInjuries','context-crime']);
    let overlay = null, historyPushed = false;

    function resultMarkup(query) {
      const q = normalize(query); const words = q.split(' ').filter(Boolean);
      let results = q ? items.filter(item => words.every(word => item.keywords.includes(word) || normalize(item.label).includes(word))) : items.filter(item => suggested.has(item.id));
      results = results.sort((a,b) => {
        const al = normalize(a.label), bl = normalize(b.label); const score = x => x === q ? 0 : x.startsWith(q) ? 1 : x.includes(q) ? 2 : 3;
        return score(al)-score(bl) || a.label.localeCompare(b.label,'it');
      }).slice(0,14);
      if (!results.length) return `<div class="search-empty"><strong>Nessun risultato</strong><p>Prova un termine più generale oppure cerca il tema o il nome del comune.</p></div>`;
      return `${!q ? '<p class="search-hint">Ricerche suggerite</p>' : ''}${categories.map(category => {
        const group = results.filter(item => item.category === category); if (!group.length) return '';
        return `<div class="search-group"><h3>${category}</h3>${group.map(item => `<a href="${item.href}" data-search-result><span><strong>${html(item.label)}</strong><small>${html(item.description)}</small></span><b>${html(item.badge)}</b></a>`).join('')}</div>`;
      }).join('')}`;
    }

    function finalizeClose() {
      if (!overlay) return; overlay.hidden = true; trigger.setAttribute('aria-expanded','false'); document.body.classList.remove('search-open'); historyPushed = false;
    }
    function closeSearch() { if (!overlay || overlay.hidden) return; if (historyPushed) history.back(); else finalizeClose(); }
    function openSearch() {
      if (!overlay) {
        overlay = document.createElement('div'); overlay.className = 'search-overlay'; overlay.hidden = true;
        overlay.innerHTML = `<section class="search-dialog" role="dialog" aria-modal="true" aria-labelledby="search-title"><div class="search-dialog-head"><div><span class="overline">Esplora i dati</span><h2 id="search-title">Cerca un indicatore</h2></div><button type="button" data-close-search aria-label="Chiudi la ricerca"><span aria-hidden="true">×</span><span class="search-close-label">Chiudi</span></button></div><label class="search-field"><span aria-hidden="true">⌕</span><input type="search" placeholder="Prova: PIL, reati, disoccupati, farmacie…" autocomplete="off"></label><div class="search-results" aria-live="polite"></div><footer class="search-footer"><span><kbd>Esc</kbd> chiude</span><span>La ricerca porta al dato: non inventa corrispondenze.</span></footer></section>`;
        document.body.appendChild(overlay);
        const input = overlay.querySelector('input'), results = overlay.querySelector('.search-results');
        const update = () => { results.innerHTML = resultMarkup(input.value); results.querySelectorAll('[data-search-result]').forEach(a => a.addEventListener('click', () => { historyPushed = false; finalizeClose(); })); };
        input.addEventListener('input', update); overlay.querySelector('[data-close-search]').addEventListener('click', closeSearch);
        overlay.addEventListener('mousedown', e => { if (e.target === overlay) closeSearch(); }); update();
      }
      overlay.hidden = false; trigger.setAttribute('aria-expanded','true'); document.body.classList.add('search-open');
      history.pushState({ ...(history.state || {}), __versiliaSearch: true }, '', location.href); historyPushed = true;
      setTimeout(() => overlay.querySelector('input')?.focus(), 0);
    }
    trigger.addEventListener('click', openSearch);
    window.addEventListener('popstate', () => { if (overlay && !overlay.hidden) finalizeClose(); });
    window.addEventListener('keydown', e => {
      const target = e.target; const typing = target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.isContentEditable;
      if ((e.key === '/' && !typing) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')) { e.preventDefault(); openSearch(); }
      if (e.key === 'Escape' && overlay && !overlay.hidden) { e.preventDefault(); closeSearch(); }
    });
  }

  function renderNotFound() {
    app.innerHTML = `<main class="editorial-page"><section class="editorial-hero compact page-width"><span class="overline">Pagina non trovata</span><h1>Questo indirizzo non esiste.</h1><p>Torna alla pagina iniziale oppure usa la ricerca per aprire un indicatore o un comune.</p><a class="button-link" href="${route('')}">Torna alla home</a></section></main>`;
  }

  async function start() {
    try {
      const response = await fetch(asset('data/site-data.json'));
      if (!response.ok) throw new Error(`Errore ${response.status}`);
      const data = await response.json();
      mountShell(data);
      if (pageType === 'home') renderHome(data);
      else if (pageType === 'compare') renderCompare(data);
      else if (pageType === 'town') renderTown(data);
      else if (pageType === 'project') renderProject(data);
      else if (pageType === 'feedback') renderFeedback(data);
      else renderNotFound();
    } catch (error) {
      console.error(error);
      app.innerHTML = `<div class="app-error"><strong>Impossibile caricare i dati.</strong><p>Controlla che il sito sia aperto tramite un server web e non direttamente come file locale.</p></div>`;
    }
  }

  start();
})();
