/* Sorgente applicativo dell'Osservatorio Versilia. La build lo copia senza trasformazioni. */
(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', globalThis.__OV_SCRIPT_URL__ || script?.src || location.href);
  const app = document.getElementById('app');
  const pageType = document.body.dataset.page || 'home';
  const pageTheme = document.body.dataset.theme || '';
  const pageTown = document.body.dataset.town || '';

  const themeSvgPaths = {
    demografia: '<path d="M18 21a8 8 0 0 0-16 0"></path><circle cx="10" cy="8" r="5"></circle><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"></path>',
    economia: '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"></path><path d="M7 12h5"></path><path d="M15 9.4a4 4 0 1 0 0 5.2"></path>',
    lavoro: '<path d="M12 12h.01"></path><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"></path><path d="M22 13a18.15 18.15 0 0 1-20 0"></path><rect width="20" height="14" x="2" y="6" rx="2"></rect>',
    istruzione: '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"></path><path d="M22 10v6"></path><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"></path>',
    salute: '<path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"></path><path d="M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"></path>',
    mobilita: '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"></path><path d="M7 14h.01"></path><path d="M17 14h.01"></path><rect width="18" height="8" x="3" y="10" rx="2"></rect><path d="M5 18v2"></path><path d="M19 18v2"></path>',
    abitare: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"></path><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>',
    ambiente: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>',
    bilanci: '<path d="M3 22h18"></path><path d="M6 18v-7"></path><path d="M10 18v-7"></path><path d="M14 18v-7"></path><path d="M18 18v-7"></path><path d="M12 2 2 7h20Z"></path>',
    comunita: '<path d="M10 12h4"></path><path d="M10 8h4"></path><path d="M14 21v-3a2 2 0 0 0-4 0v3"></path><path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"></path><path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"></path>'
  };

  function themeIcon(theme, size = 26) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${themeSvgPaths[theme] || ''}</svg>`;
  }

  function mediaSrc(value) {
    const source = String(value || '');
    return /^(data:|https?:)/i.test(source) ? source : asset(source.replace(/^\//, ''));
  }


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
    foreignBornSoleProprietorShare: ['imprenditori stranieri', 'titolari nati all estero', 'ditte individuali'],
    innovationBusinessShare: ['innovazione', 'imprese innovative', 'settori innovativi'],
    employmentRate: ['occupati', 'lavoratori', 'occupazione'],
    unemploymentRate: ['disoccupati', 'senza lavoro', 'disoccupazione'],
    activityRate: ['forza lavoro', 'attivi', 'partecipazione'],
    femaleEmploymentRate: ['occupazione femminile', 'donne occupate', 'lavoro donne'],
    maleEmploymentRate: ['occupazione maschile', 'uomini occupati', 'lavoro uomini'],
    employmentGenderGap: ['divario di genere', 'gender gap', 'differenza occupazione donne uomini'],
    youthOtherStatus: ['giovani', '15 24 anni', 'altra condizione professionale', 'neet'],
    diplomaPlus: ['diplomati', 'titolo di studio', 'scuola superiore'],
    tertiary: ['laureati', 'laurea', 'università'],
    schoolSites: ['scuole', 'istituti scolastici'],
    schoolStudents: ['alunni', 'studenti', 'popolazione scolastica'],
    studentsPerClass: ['alunni per classe', 'dimensione classi', 'classi scolastiche'],
    primaryFullTimeShare: ['tempo pieno', 'scuola primaria', 'orario scolastico'],
    lifeExpectancy: ['speranza di vita', 'longevità', 'salute'],
    mortalityAll: ['mortalità', 'decessi', 'cause di morte'],
    chronicTotal: ['cronici', 'malattie croniche', 'patologie croniche'],
    disability064Per1000: ['disabilita', 'persone con disabilita', 'invalidita'],
    diabetes: ['diabete', 'malattie croniche'],
    dementia: ['demenza', 'alzheimer', 'non autosufficienza'],
    emergencyAccess: ['pronto soccorso', 'emergenza', 'accessi ps'],
    emsResponseTimeP75: ['118', 'ambulanza', 'tempo di soccorso', 'emergenza urgenza'],
    hospitalizedAll: ['ricoveri', 'ospedalizzazione', 'ospedale'],
    elderlyHomeCare: ['assistenza domiciliare', 'anziani', 'adi'],
    pharmaciesPer1000: ['farmacie', 'sanità'], hospitals: ['ospedali', 'posti letto', 'presidi'],
    outsideMunicipality: ['pendolari', 'lavoro fuori comune', 'spostamenti'],
    inboundCommuters: ['pendolari', 'entrata', 'flussi'], selfContainment: ['lavoro nel comune', 'autocontenimento'],
    roadInjuries: ['incidenti', 'feriti', 'sicurezza stradale'], motorization: ['auto', 'motorizzazione'],
    pollutingCars: ['auto inquinanti', 'euro 0', 'euro 3'], evPoints: ['ricarica', 'auto elettriche'],
    vacantHomes: ['case vuote', 'abitazioni non occupate'], singleHouseholds: ['persone sole', 'famiglie'],
    householdSize: ['componenti famiglia', 'nucleo familiare'],
    housingStockPer1000: ['patrimonio abitativo', 'abitazioni per residenti', 'case per abitante'],
    nonOccupiedHomesPer1000: ['case non occupate per residenti', 'abitazioni vuote', 'seconde case'],
    cohabitingHouseholds: ['famiglie coabitanti', 'coabitazione', 'disagio abitativo'],
    landUse: ['consumo di suolo', 'cementificazione'],
    landUseChange: ['nuovo suolo consumato'], recycling: ['raccolta differenziata', 'rifiuti'],
    wastePerResident: ['rifiuti pro capite', 'kg'], floodExposure: ['alluvione', 'rischio idraulico'],
    landslideExposure: ['frane', 'rischio geomorfologico'],
    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],
    currentRevenueAccruedPerResident: ['entrate correnti', 'accertamenti', 'risorse comunali'],
    currentExpenditureCommittedPerResident: ['spesa corrente', 'impegni', 'servizi comunali'],
    capitalExpenditureCommittedPerResident: ['investimenti', 'conto capitale', 'impegni capitale'],
    ownRevenueShare: ['entrate proprie', 'autonomia finanziaria', 'tributi e tariffe'],
    currentCollectionCapacity: ['riscossione', 'incassi competenza', 'capacita di riscossione'],
    currentPaymentCapacity: ['pagamenti competenza', 'capacita di pagamento', 'impegni pagati'],
    availableAdministrationResultPerResident: ['risultato di amministrazione', 'avanzo disponibile', 'disavanzo'],
    rigidExpenditureShare: ['spese rigide', 'personale e debito', 'rigidita bilancio'],
    educationMissionExpenditurePerResident: ['spesa istruzione', 'bilancio scuola', 'missione 04'],
    socialMissionExpenditurePerResident: ['spesa sociale', 'famiglia', 'missione 12'],
    environmentMissionExpenditurePerResident: ['spesa ambiente', 'territorio', 'missione 09'],
    mobilityMissionExpenditurePerResident: ['spesa mobilita', 'trasporti', 'missione 10'],
    cultureSportMissionExpenditurePerResident: ['spesa cultura', 'spesa sport', 'missioni 05 06'],
    tourismDevelopmentMissionExpenditurePerResident: ['spesa turismo', 'sviluppo economico', 'missioni 07 14'],
    thirdSector: ['associazioni', 'volontariato'],
    currentPayments: ['spesa corrente', 'pagamenti'], siopePayments: ['cassa', 'uscite'],
    publicWorks: ['opere pubbliche', 'cantieri'], pnrrFunding: ['pnrr', 'finanziamenti'],
    pnrrConcluded: ['pnrr', 'progetti conclusi'],
    share014: ['bambini', 'minori', 'under 15', '0 14'],
    populationChange: ['calo demografico', 'crescita popolazione', 'variazione residenti'],
    tourismSeasonality: ['stagionalita', 'estate', 'mesi turistici', 'pressione turistica'],
    foreignTourismShare: ['turisti stranieri', 'presenze estere', 'turismo internazionale'],
    commuterBalanceRate: ['saldo pendolare', 'lavoratori in entrata', 'lavoratori in uscita'],
    residualWaste: ['rifiuto residuo', 'indifferenziato', 'rifiuti non differenziati'],
    capitalPayments: ['investimenti', 'conto capitale', 'pagamenti capitale']
  };

  const html = (value) => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const route = (path = '') => new URL(String(path).replace(/^\//, ''), ROOT).href;
  const asset = (path = '') => route(path);
  const normalize = (value) => String(value ?? '').toLocaleLowerCase('it')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

  const number0 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 });
  const number1 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number2 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const currency0 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

  function formatValue(value, unit) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'n.d.';
    const v = Number(value);
    switch (unit) {
      case 'currency': return currency0.format(v);
      case 'millionCurrency': return `${number1.format(v)} mln €`;
      case 'percent': return `${number1.format(v)}%`;
      case 'percentagePoints': return `${number1.format(v)} p.p.`;
      case 'index': return number1.format(v);
      case 'decimal': return number2.format(v);
      case 'years': return `${number2.format(v)} anni`;
      case 'nights': return `${number2.format(v)} notti`;
      case 'people': return `${number0.format(v)} persone`;
      case 'studentsPerClass': return `${number1.format(v)} alunni/classe`;
      case 'minutes': return `${number1.format(v)} min`;
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

  function methodDisclosure(metric) {
    const method = metric.method || {};
    if (!method.formula && !method.type && !method.caveat) return '';
    return `<details class="method-disclosure"><summary><span>Metodo e comparabilità</span><small>Formula, natura del dato e criticità</small></summary><div class="method-disclosure-body"><dl><div><dt>Natura</dt><dd>${html(method.type || 'Dato ufficiale')}</dd></div><div><dt>Formula</dt><dd>${html(method.formula || 'Valore pubblicato dalla fonte.')}</dd></div><div><dt>Copertura</dt><dd>${html(method.coverage || '7/7')}</dd></div></dl>${method.caveat ? `<p><strong>Nota:</strong> ${html(method.caveat)}</p>` : ''}</div></details>`;
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
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg><span>Cerca</span><kbd>/</kbd>
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
          <span>7 comuni · ${Object.keys(data.themes).length} temi</span><span>v. dati ${html(data.version)}</span><span>aggiornato ${html(data.updated)}</span>
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

  function installTablist(root, onSelect) {
    if (!root) return;
    const tabs = [...root.querySelectorAll('[role="tab"]')];
    const activate = tab => {
      if (!tab) return;
      onSelect(tab.dataset.metric);
    };
    tabs.forEach(tab => {
      tab.addEventListener('click', () => activate(tab));
      tab.addEventListener('keydown', event => {
        const current = tabs.indexOf(tab);
        let next = current;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (current + 1) % tabs.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (current - 1 + tabs.length) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else return;
        event.preventDefault();
        tabs[next]?.focus();
        activate(tabs[next]);
      });
    });
  }

  function scrollActiveControl(root) {
    if (!root || (typeof window.matchMedia === 'function' && window.matchMedia('(min-width: 701px)').matches)) return;
    (window.requestAnimationFrame || window.setTimeout)(() => root.querySelector('.active')?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }));
  }

  async function shareCurrentPage(button) {
    const title = document.title;
    const url = location.href;
    try {
      if (navigator.share) await navigator.share({ title, url });
      else if (navigator.clipboard) {
        await navigator.clipboard.writeText(url);
        const previous = button.textContent;
        button.textContent = 'Link copiato';
        setTimeout(() => { button.textContent = previous; }, 1600);
      }
    } catch (error) {
      if (error?.name !== 'AbortError') console.warn('Condivisione non riuscita', error);
    }
  }

  function themeSections(theme) {
    if (Array.isArray(theme.sections) && theme.sections.length) return theme.sections;
    return [{ key: 'indicatori', label: 'Indicatori', description: '', metrics: theme.metrics || [] }];
  }

  function featuredMetrics(theme) {
    const candidates = Array.isArray(theme.featured) && theme.featured.length
      ? theme.featured
      : themeSections(theme).map(section => section.metrics[0]).filter(Boolean);
    return candidates.filter(key => theme.metrics.includes(key)).slice(0, 3);
  }

  function themeCard(theme) {
    const sections = themeSections(theme);
    return `<button type="button" data-theme="${html(theme.key)}" class="theme-card" aria-pressed="false">
      <span class="theme-number">${html(theme.number)}</span>
      <span class="theme-icon">${themeIcon(theme.key, 26)}</span>
      <strong>${html(theme.label)}</strong><span class="theme-question">${html(theme.question)}</span>
      <span class="theme-card-meta">${sections.length} ${sections.length === 1 ? 'sezione' : 'sezioni'} · ${theme.metrics.length} indicatori</span><i aria-hidden="true">→</i>
    </button>`;
  }

  function townCard(data, town) {
    const pop = data.metrics.population.rows.find(r => r.code === town.code);
    const income = data.metrics.income.rows.find(r => r.code === town.code);
    const employment = data.metrics.employmentRate.rows.find(r => r.code === town.code);
    return `<a href="${route(`comuni/${pop.slug}/`)}" class="town-card">
      <div class="town-card-head"><img alt="Stemma di ${html(town.name)}" src="${mediaSrc(data.crests[town.name])}"><span>Codice Istat ${html(town.code)}</span></div>
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
          <div class="hero-facts"><span>7 comuni</span><span>${Object.keys(data.themes).length} temi</span><span>${Object.keys(data.metrics).length} indicatori</span><span>Aggiornato ${html(data.updated)}</span></div></div>
        <figure class="hero-photo"><img alt="Il litorale di Viareggio con le Alpi Apuane sullo sfondo" src="${mediaSrc(data.heroImage || 'images/versilia-viareggio-apuane.jpg')}">
          <figcaption>Viareggio e Alpi Apuane · Foto di Carlo Pelagalli, <a href="https://commons.wikimedia.org/wiki/File:Wv_Versilia_banner.jpg" target="_blank" rel="noreferrer">CC BY-SA 3.0 ↗</a></figcaption></figure>
      </section>
      <section class="theme-section page-width" id="temi"><div class="section-heading"><div><span class="overline">Esplora per tema</span><h2>Da dove vuoi cominciare?</h2></div><p>La selezione aggiorna subito il confronto territoriale.</p></div>
        <div class="theme-grid">${themes.map(themeCard).join('')}</div></section>
      <section id="home-explorer" class="explorer-panel page-width" aria-live="polite"></section>
      <section class="towns-section page-width" id="comuni"><div class="section-heading"><div><span class="overline">Esplora per territorio</span><h2>Un profilo per ogni comune</h2></div><p>Indicatori, andamento storico e posizione nel contesto.</p></div>
        <div class="town-card-grid">${data.towns.map(t => townCard(data, t)).join('')}</div></section>
      <section class="method-section page-width" id="metodo"><div class="method-title"><span class="overline">Come leggere i dati</span><h2>Confronti trasparenti,<br>senza classifiche facili.</h2></div>
        <div class="method-list">
          <article><span>01</span><div><h3>Stesso perimetro</h3><p>Toscana e Italia compaiono solo quando anno, unità e definizione sono compatibili con il dato comunale.</p></div></article>
          <article><span>02</span><div><h3>Posizione, non giudizio</h3><p>La graduatoria dei sette comuni ordina il valore numerico: non assegna voti e non definisce da sola cosa sia “meglio”.</p></div></article>
          <article><span>03</span><div><h3>La scala conta</h3><p>Criminalità e altri dati non disponibili a livello comunale restano esplicitamente indicati come contesto provinciale.</p></div></article>
          <article><span>04</span><div><h3>Versione dichiarata</h3><p>Ogni indicatore mostra anno e fonte; la raccolta dati è pubblicata come versione ${html(data.version)}, aggiornata il ${html(data.updated)}.</p></div></article>
        </div></section>
      <section class="project-callout page-width" aria-labelledby="progetto-title"><div><span class="overline">Il progetto</span><h2 id="progetto-title">I dati pubblici, senza la caccia al tesoro.</h2></div>
        <div><p>Osservatorio Versilia nasce per riunire informazioni disperse tra portali, fogli di calcolo e pubblicazioni, rendendole leggibili e confrontabili senza perdere anno, definizione e fonte.</p><a class="text-link" href="${route('progetto/')}">Scopri chi lo cura e come lavoriamo <b>→</b></a></div></section>
      <section class="source-portals page-width" aria-label="Principali fonti istituzionali"><span class="overline">Principali fonti istituzionali</span><div>
        <a href="https://www.istat.it/" target="_blank" rel="noreferrer">Istat <span>↗</span></a>
        <a href="https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php" target="_blank" rel="noreferrer">MEF <span>↗</span></a>
        <a href="https://www.isprambiente.gov.it/" target="_blank" rel="noreferrer">ISPRA <span>↗</span></a>
        <a href="https://www.regione.toscana.it/statistiche" target="_blank" rel="noreferrer">Regione Toscana <span>↗</span></a>
        <a href="https://openbdap.rgs.mef.gov.it/" target="_blank" rel="noreferrer">BDAP <span>↗</span></a>
      </div></section>
    </main>`;

    let selectedTheme = 'demografia';
    let selectedMetric = featuredMetrics(data.themes[selectedTheme])[0] || data.themes[selectedTheme].metrics[0];
    const cards = [...document.querySelectorAll('.theme-card')];
    cards.forEach(card => card.addEventListener('click', () => {
      selectedTheme = card.dataset.theme;
      selectedMetric = featuredMetrics(data.themes[selectedTheme])[0] || data.themes[selectedTheme].metrics[0];
      cards.forEach(c => { c.classList.toggle('active', c === card); c.setAttribute('aria-pressed', c === card ? 'true' : 'false'); });
      renderHomeExplorer(data, selectedTheme, selectedMetric);
    }));
    cards[0]?.classList.add('active'); cards[0]?.setAttribute('aria-pressed', 'true');
    renderHomeExplorer(data, selectedTheme, selectedMetric);
  }

  function renderHomeExplorer(data, themeKey, metricKey) {
    const panel = document.getElementById('home-explorer');
    const theme = data.themes[themeKey];
    const keys = featuredMetrics(theme);
    if (!keys.includes(metricKey)) metricKey = keys[0] || theme.metrics[0];
    const metric = data.metrics[metricKey];
    panel.dataset.theme = themeKey;
    panel.innerHTML = `<div class="explorer-copy"><span class="overline">Confronto · ${html(theme.label)}</span><h2>${html(metric.meta.label)}</h2><p>${html(metric.meta.description)}</p>
      <div class="featured-metric-label">Indicatori chiave</div>
      <div class="metric-switch featured-switch" role="tablist" aria-label="Indicatori chiave">${keys.map(key => `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(data.metrics[key].meta.shortLabel)}</button>`).join('')}</div>
      <div class="explorer-stat"><span>${html(metric.aggregate.label)}</span><strong>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</strong><small>${html(metric.aggregate.note)}</small></div>
      <a class="source-link" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Apri la fonte originale <span aria-hidden="true">↗</span></a>
      <a href="${route(`confronta/${themeKey}/?indicatore=${metricKey}`)}" class="button-link">Esplora tutte le sezioni <span>→</span></a></div>
      <div class="explorer-chart"><div class="comparison-bars">${barRows(data, metricKey)}</div></div>`;
    installTablist(panel.querySelector('[role="tablist"]'), key => renderHomeExplorer(data, themeKey, key));
  }

  function metricControls(data, themeKey, metricKey, compact = true) {
    const theme = data.themes[themeKey];
    const groups = themeSections(theme);
    return `<div class="metric-switch metric-catalog ${compact ? 'compact-list' : ''}" role="tablist" aria-label="Indicatori di ${html(theme.label)}">${groups.map(section => `<section class="metric-group" data-section="${html(section.key)}">
      <div class="metric-group-heading"><strong>${html(section.label)}</strong>${section.description ? `<span>${html(section.description)}</span>` : ''}</div>
      <div class="metric-group-buttons">${section.metrics.map(key => `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(data.metrics[key].meta.shortLabel)}</button>`).join('')}</div>
    </section>`).join('')}</div>`;
  }

  function compareContextNav(data, activeTheme) {
    return `<nav class="compare-context-nav page-width" aria-label="Passa a un altro tema">
      <div class="context-nav-title"><small>Esplora</small><strong>Temi</strong></div>
      <div class="context-nav-links">${Object.values(data.themes).map(theme => `<a href="${route(`confronta/${theme.key}/?indicatore=${theme.metrics[0]}`)}" data-context-theme="${theme.key}" class="${theme.key === activeTheme ? 'active' : ''}" ${theme.key === activeTheme ? 'aria-current="page"' : ''}><small>${html(theme.number)}</small><span>${html(theme.label)}</span></a>`).join('')}</div>
    </nav>`;
  }

  function townContextNav(data, town, themeKey, metricKey) {
    const activeSlug = normalize(town.name).replaceAll(' ', '-');
    const townLinks = data.towns.map(item => {
      const slug = normalize(item.name).replaceAll(' ', '-');
      return `<a href="${route(`comuni/${slug}/?tema=${themeKey}&indicatore=${metricKey}`)}" data-town-link="${slug}" class="${slug === activeSlug ? 'active' : ''}" ${slug === activeSlug ? 'aria-current="page"' : ''}>${html(item.name)}</a>`;
    }).join('');
    const themeButtons = Object.values(data.themes).map(theme => `<button type="button" data-profile-theme="${theme.key}" class="${theme.key === themeKey ? 'active' : ''}">${themeIcon(theme.key, 15)}<span>${html(theme.number)}</span>${html(theme.label)}</button>`).join('');
    return `<div class="town-context-nav">
      <div class="context-nav-row"><div class="context-nav-title"><small>Esplora</small><strong>Comuni</strong></div><div class="context-nav-links">${townLinks}</div></div>
      <div class="theme-nav-shell">
        <button type="button" class="theme-nav-arrow theme-nav-arrow-prev" data-theme-scroll="prev" aria-label="Scorri ai temi precedenti"><span aria-hidden="true">‹</span></button>
        <nav class="theme-nav" aria-label="Temi della scheda">${themeButtons}</nav>
        <button type="button" class="theme-nav-arrow theme-nav-arrow-next" data-theme-scroll="next" aria-label="Scorri ai temi successivi"><span aria-hidden="true">›</span></button>
      </div>
    </div>`;
  }

  function updateTownContextLinks(data, themeKey, metricKey) {
    document.querySelectorAll('[data-town-link]').forEach(link => {
      link.href = route(`comuni/${link.dataset.townLink}/?tema=${themeKey}&indicatore=${metricKey}`);
    });
  }

  function installThemeScroller() {
    const shell = document.querySelector('.theme-nav-shell');
    const nav = shell?.querySelector('.theme-nav');
    if (!shell || !nav) return;

    const update = () => {
      const maxScroll = Math.max(0, nav.scrollWidth - nav.clientWidth);
      const canScroll = maxScroll > 4;
      const canScrollLeft = canScroll && nav.scrollLeft > 4;
      const canScrollRight = canScroll && nav.scrollLeft < maxScroll - 4;
      shell.classList.toggle('can-scroll-left', canScrollLeft);
      shell.classList.toggle('can-scroll-right', canScrollRight);
      const previous = shell.querySelector('[data-theme-scroll="prev"]');
      const next = shell.querySelector('[data-theme-scroll="next"]');
      if (previous) previous.disabled = !canScrollLeft;
      if (next) next.disabled = !canScrollRight;
    };

    shell.querySelectorAll('[data-theme-scroll]').forEach(button => button.addEventListener('click', () => {
      const direction = button.dataset.themeScroll === 'prev' ? -1 : 1;
      nav.scrollBy({ left: direction * Math.max(260, nav.clientWidth * .68), behavior: 'smooth' });
    }));
    nav.addEventListener('scroll', update, { passive: true });
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(nav);
    requestAnimationFrame(() => {
      nav.querySelector('.active')?.scrollIntoView({ block: 'nearest', inline: 'center' });
      requestAnimationFrame(update);
    });
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
      ${compareContextNav(data, themeKey)}
      <section class="topic-hero page-width" data-theme="${themeKey}"><div class="topic-symbol">${themeIcon(themeKey, 26)}<small>${html(theme.number)}</small></div>
        <div><span class="overline">Confronto territoriale</span><h1>${html(theme.label)}</h1><p>${html(theme.description)}</p></div></section>
      <section class="topic-dashboard page-width" data-theme="${themeKey}"><aside class="topic-controls">${metricControls(data, themeKey, metricKey, true)}<div id="compare-definition"></div></aside><div id="compare-bars"></div></section>
      <section id="compare-benchmark" class="page-width"></section>
      ${themeKey === 'mobilita' ? crimeMarkup(data) : ''}
      <section class="topic-town-links page-width"><div><span class="overline">Schede comunali</span><h2>Apri il territorio</h2></div><div>${data.towns.map(t => `<a href="${route(`comuni/${normalize(t.name).replaceAll(' ', '-')}/?tema=${themeKey}&indicatore=${metricKey}`)}"><span>${html(t.name)}</span><b>→</b></a>`).join('')}</div></section>
    </main>`;
    const update = key => {
      metricKey = key;
      history.replaceState(history.state, '', `?indicatore=${encodeURIComponent(key)}`);
      const tablist = document.querySelector('.topic-controls [role="tablist"]');
      tablist?.querySelectorAll('[role="tab"]').forEach(b => {
        const active = b.dataset.metric === key;
        b.classList.toggle('active', active);
        b.setAttribute('aria-selected', active ? 'true' : 'false');
        b.tabIndex = active ? 0 : -1;
      });
      renderCompareMetric(data, themeKey, key, false);
      scrollActiveControl(tablist);
    };
    installTablist(document.querySelector('.topic-controls [role="tablist"]'), update);
    renderCompareMetric(data, themeKey, metricKey, false);
    scrollActiveControl(document.querySelector('.topic-controls [role="tablist"]'));
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
        <small class="aggregate-note">${html(aggregate.note)}</small>${methodDisclosure(metric)}<div class="data-actions"><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div></div>`;
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
    const popValues = pop.series?.values || town.population || [];
    const populationChange = popValues.length > 1 ? ((popValues.at(-1) / popValues[0]) - 1) * 100 : 0;
    const employmentDifference = Number(employment.value) - Number(data.metrics.employmentRate.aggregate.value);
    const incomeDifference = (Number(income.value) / Number(data.metrics.income.aggregate.value) - 1) * 100;

    app.innerHTML = `<main class="page-width inner-page town-profile" data-theme="${themeKey}">
      <div class="breadcrumbs"><a href="${route('')}">Home</a><span>/</span><span>Comuni</span><span>/</span><strong>${html(town.name)}</strong></div>
      <header class="town-hero"><div class="town-identity"><img alt="Stemma di ${html(town.name)}" src="${mediaSrc(data.crests[town.name])}"><div><span class="overline">Profilo comunale · Istat ${html(town.code)}</span><h1>${html(town.name)}</h1><p>Numeri, tendenze e confronti per leggere il territorio nel suo contesto.</p></div></div>
        <dl class="town-headline-stats"><div><dt>Residenti · ${html(data.metrics.population.meta.year)}</dt><dd>${html(pop.formatted)}</dd></div><div><dt>Reddito medio · ${html(data.metrics.income.meta.year)}</dt><dd>${html(income.formatted)}</dd></div><div><dt>Occupazione · ${html(data.metrics.employmentRate.meta.year)}</dt><dd>${html(employment.formatted)}</dd></div></dl></header>
      <section class="town-brief" aria-labelledby="town-brief-title"><div><span class="overline">Sintesi</span><h2 id="town-brief-title">${html(town.name)} in breve</h2></div>
        <article><span>Popolazione dal ${html(pop.series?.years?.[0] || '2019')}</span><strong>${populationChange >= 0 ? 'In crescita' : 'In calo'}</strong><small>${html(number1.format(Math.abs(populationChange)))}% ${populationChange >= 0 ? 'in più' : 'in meno'}</small></article>
        <article><span>Occupazione 25–64</span><strong>${employmentDifference >= 0 ? 'Sopra' : 'Sotto'} la Versilia</strong><small>${html(number1.format(Math.abs(employmentDifference)))} punti di differenza</small></article>
        <article><span>Reddito medio</span><strong>${incomeDifference >= 0 ? 'Sopra' : 'Sotto'} la Versilia</strong><small>${html(number1.format(Math.abs(incomeDifference)))}% di differenza</small></article></section>
      ${townContextNav(data, town, themeKey, metricKey)}
      <section id="town-topic" class="town-topic" data-theme="${themeKey}"></section>
      <div id="town-context"></div>
    </main>`;

    const updateUrl = (theme, metric) => {
      const url = new URL(location.href);
      url.searchParams.set('tema', theme);
      url.searchParams.set('indicatore', metric);
      history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
    };
    const selectMetric = key => {
      metricKey = key;
      updateUrl(themeKey, metricKey);
      updateTownContextLinks(data, themeKey, metricKey);
      renderTownMetric(data, town, themeKey, metricKey, selectMetric);
    };
    const selectTheme = key => {
      themeKey = key;
      metricKey = data.themes[key].metrics[0];
      document.querySelector('main.town-profile').dataset.theme = key;
      document.querySelectorAll('[data-profile-theme]').forEach(button => button.classList.toggle('active', button.dataset.profileTheme === key));
      updateUrl(themeKey, metricKey);
      updateTownContextLinks(data, themeKey, metricKey);
      renderTownMetric(data, town, themeKey, metricKey, selectMetric);
      scrollActiveControl(document.querySelector('.theme-nav'));
    };
    document.querySelectorAll('[data-profile-theme]').forEach(button => button.addEventListener('click', () => selectTheme(button.dataset.profileTheme)));
    installThemeScroller();
    renderTownMetric(data, town, themeKey, metricKey, selectMetric);
    scrollActiveControl(document.querySelector('.theme-nav'));
  }

  function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect) {
    const theme = data.themes[themeKey];
    const metric = data.metrics[metricKey];
    const row = metric.rows.find(r => r.code === town.code);
    const ranked = metricRows(data, metricKey);
    const rank = ranked.findIndex(r => r.code === town.code) + 1;
    const container = document.getElementById('town-topic');
    container.dataset.theme = themeKey;
    const historical = Boolean(row.series?.values?.length);
    container.innerHTML = `<div class="town-topic-heading"><div><span class="overline">${html(theme.number)} · ${html(theme.label)}</span><h2>${html(theme.question)}</h2><p>${html(theme.description)}</p></div><a href="${route(`confronta/${themeKey}/?indicatore=${metricKey}`)}">Confronta i 7 comuni <span>→</span></a></div>
      <section class="town-indicator-selector" aria-labelledby="town-indicator-selector-title">
        <div class="town-indicator-selector-heading"><span id="town-indicator-selector-title" class="overline">Scegli l’indicatore</span><p>Le sezioni raccolgono tutti i dati disponibili per questo tema.</p></div>
        ${metricControls(data, themeKey, metricKey, false)}
      </section>
      <div class="town-metric-layout"><article class="town-metric-primary"><span>${html(metric.meta.label)}</span><strong>${html(formatValue(row.value, metric.meta.unit))}</strong><p>${html(metric.meta.description)}</p>
        ${row.normalized ? `<p class="normalized-companion"><b>${html(row.normalized.label)}:</b> ${html(formatValue(row.normalized.value, row.normalized.unit))}</p>` : ''}
        <div><span>${html(metric.meta.year)}</span><a class="inline-source-link" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte originale ↗</a></div></article>
        <aside class="versilia-position"><span class="overline">Ordine del valore</span><strong>${rank}<sup>°</sup> <small>su 7</small></strong><p>${html(interpretation(metric.meta))}</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</b></div></aside></div>
      ${methodDisclosure(metric)}
      <div class="data-actions town-data-actions"><button type="button" data-share>Condividi</button><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div>
      <section class="history-panel"><div class="panel-title"><div><span class="overline">${historical ? 'Andamento storico' : 'Confronto territoriale'}</span><h3>${historical ? `${html(metric.meta.shortLabel)} nel tempo` : html(metric.meta.label)}</h3></div><a class="source-pill" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${html(metric.meta.source)} ↗</a></div>
        ${historical ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : `<div class="comparison-bars">${barRows(data, metricKey, { selectedTown: normalize(town.name).replaceAll(' ', '-') })}</div>`}</section>
      ${deepDiveMarkup(data, town, themeKey)}
      ${townBenchmarkMarkup(metric, row, town)}`;

    const tablist = container.querySelector('[role="tablist"]');
    installTablist(tablist, onMetricSelect);
    container.querySelector('[data-share]')?.addEventListener('click', event => shareCurrentPage(event.currentTarget));
    container.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data, metricKey));
    container.querySelector('[data-print]')?.addEventListener('click', () => window.print());
    installChartInteractions(container);
    scrollActiveControl(tablist);

    const context = document.getElementById('town-context');
    context.innerHTML = themeKey === 'mobilita' ? crimeMarkup(data) : '';
    if (themeKey === 'mobilita') installCrimeInteractions(data);
  }

  function townBenchmarkMarkup(metric, row, town) {
    const b = metric.meta.benchmark;
    if (!b) return `<section class="benchmark-unavailable town-benchmark"><span class="overline">Confronto esterno</span><h2>Dato non perfettamente comparabile</h2><p>Per questo indicatore non è disponibile un confronto omogeneo con Toscana e Italia.</p></section>`;
    const localValue = row.benchmarkValue ?? row.value;
    return `<section class="town-benchmark"><div><div><span class="overline">Confronto omogeneo · ${html(b.year)}</span><h3>${html(town.name)}, Toscana${b.italy !== null && b.italy !== undefined ? ' e Italia' : ''}</h3></div><p>${html(b.note || '')}</p></div>
      <div class="town-benchmark-values"><article><span>${html(town.name)}</span><strong>${html(formatValue(localValue, metric.meta.unit))}</strong><small>Dato comunale riferito al ${html(b.year)}.</small></article><article><span>Toscana</span><strong>${html(formatValue(b.tuscany, metric.meta.unit))}</strong><small>${html(b.source)}</small></article>${b.italy !== null && b.italy !== undefined ? `<article><span>Italia</span><strong>${html(formatValue(b.italy, metric.meta.unit))}</strong><small>${html(b.source)}</small></article>` : ''}</div>
      <a class="benchmark-source" href="${html(b.url)}" target="_blank" rel="noreferrer">Apri la fonte del confronto ↗</a></section>`;
  }

  function seriesChart(series, unit, label = 'Serie storica') {
    const values = series.values.map(Number);
    const years = series.years;
    const rawMin = Math.min(...values), rawMax = Math.max(...values);
    const rawRange = rawMax - rawMin || Math.max(Math.abs(rawMax) * .08, 1);
    const min = rawMin - rawRange * .08;
    const max = rawMax + rawRange * .08;
    const range = max - min || 1;
    const width = 760, height = 260, left = 52, right = 28, top = 24, bottom = 38;
    const chartWidth = width - left - right, chartHeight = height - top - bottom;
    const pts = values.map((value, index) => ({
      x: left + index * chartWidth / Math.max(1, values.length - 1),
      y: top + (max - value) / range * chartHeight,
      value,
      year: years[index]
    }));
    const line = pts.map(point => `${point.x},${point.y}`).join(' ');
    const area = `${left},${height - bottom} ${line} ${width - right},${height - bottom}`;
    const grid = [0, .5, 1].map(fraction => {
      const y = top + fraction * chartHeight;
      return `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"/>`;
    }).join('');
    const points = pts.map(point => {
      const boxWidth = 198, boxHeight = 38;
      const boxX = Math.max(left - 8, Math.min(width - right - boxWidth, point.x - boxWidth / 2));
      const boxY = point.y < 72 ? point.y + 18 : point.y - 54;
      return `<g class="chart-point" tabindex="0" role="button" aria-label="${html(point.year)}: ${html(formatValue(point.value, unit))}">
        <circle class="chart-hit" cx="${point.x}" cy="${point.y}" r="17"></circle>
        <circle class="chart-dot" cx="${point.x}" cy="${point.y}" r="5"></circle>
        <g class="chart-tooltip"
hidden>
          <line class="chart-guide" x1="${point.x}" y1="${point.y}" x2="${point.x}" y2="${boxY < point.y ? boxY + boxHeight : boxY}"></line>
          <rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect>
          <text class="chart-tooltip-year" x="${boxX + 12}" y="${boxY + 14}">${html(point.year)}</text>
          <text class="chart-tooltip-value" x="${boxX + 12}" y="${boxY + 29}">${html(formatValue(point.value, unit))}</text>
        </g>
      </g>`;
    }).join('');
    return `<div class="chart-shell"><div class="trend-chart"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${html(label)}">
      ${grid}<polygon class="chart-area" points="${area}"/><polyline class="chart-line" points="${line}"/>${points}
      ${pts.map(point => `<text class="chart-label" x="${point.x}" y="${height - 10}" text-anchor="middle">${html(point.year)}</text>`).join('')}
      </svg></div></div>
      <div class="chart-a11y-table"><strong>${html(label)}</strong>${pts.map(point => `<span>${html(point.year)}: ${html(formatValue(point.value, unit))}</span>`).join('')}</div>`;
  }

  function installChartInteractions(root) {
    root.querySelectorAll('.trend-chart').forEach(chart => {
      const points = [...chart.querySelectorAll('.chart-point')];
      const hideAll = () => points.forEach(point => {
        point.classList.remove('active');
        const tooltip = point.querySelector('.chart-tooltip');
        if (tooltip) tooltip.setAttribute('hidden', '');
      });
      const show = point => {
        hideAll();
        point.classList.add('active');
        const tooltip = point.querySelector('.chart-tooltip');
        if (tooltip) tooltip.removeAttribute('hidden');
      };
      points.forEach((point, index) => {
        point.addEventListener('mouseenter', () => show(point));
        point.addEventListener('mouseleave', hideAll);
        point.addEventListener('focus', () => show(point));
        point.addEventListener('blur', hideAll);
        point.addEventListener('click', () => show(point));
        point.addEventListener('keydown', event => {
          if (event.key === 'Escape') { hideAll(); point.blur(); return; }
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
          event.preventDefault();
          let next = index;
          if (event.key === 'ArrowLeft') next = (index - 1 + points.length) % points.length;
          if (event.key === 'ArrowRight') next = (index + 1) % points.length;
          if (event.key === 'Home') next = 0;
          if (event.key === 'End') next = points.length - 1;
          points[next]?.focus();
        });
      });
      chart.addEventListener('mouseleave', hideAll);
    });
  }

  function deepDiveMarkup(data, town, themeKey) {
    const detail = data.details[town.code];
    if (!detail) return '';
    if (themeKey === 'salute') {
      const health = data.healthB?.[town.code];
      if (!health) return '';
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Salute e uso dei servizi</h3></div><p>Indicatori standardizzati o rapportati alla popolazione. Non rappresentano una valutazione della qualità dei servizi e vanno letti insieme a definizione, anno e fonte.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Speranza di vita</span><strong>${number2.format(health.lifeExpectancy)} anni</strong><small>Indicatore demografico-sanitario</small></article><article class="deep-fact"><span>Accessi al pronto soccorso</span><strong>${number2.format(health.emergencyAccess)}</strong><small>Ogni 100 residenti</small></article><article class="deep-fact"><span>Ricoverati</span><strong>${number2.format(health.hospitalizedAll)}</strong><small>Ogni 100 residenti</small></article><article class="deep-fact"><span>Assistenza domiciliare anziani</span><strong>${number2.format(health.elderlyHomeCare)}</strong><small>Ogni 100 anziani</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio sanitario</span><small>Patologie croniche e mortalità per causa</small></summary><div class="deep-columns"><div><h4>Patologie croniche selezionate</h4><ul class="deep-list deep-list--rates"><li><span>Diabete</span><span class="deep-list-value"><strong>${number2.format(health.diabetes)}</strong><small>ogni 1.000 residenti</small></span></li><li><span>Demenza</span><span class="deep-list-value"><strong>${number2.format(health.dementia)}</strong><small>ogni 1.000 residenti</small></span></li><li><span>Ipertensione</span><span class="deep-list-value"><strong>${number2.format(health.hypertension)}</strong><small>ogni 1.000 residenti</small></span></li><li><span>BPCO</span><span class="deep-list-value"><strong>${number2.format(health.copd)}</strong><small>ogni 1.000 residenti</small></span></li></ul></div><div><h4>Mortalità per causa</h4><ul class="deep-list deep-list--rates"><li><span>Tumori</span><span class="deep-list-value"><strong>${number2.format(health.mortalityTumors)}</strong><small>ogni 100.000 residenti</small></span></li><li><span>Malattie circolatorie</span><span class="deep-list-value"><strong>${number2.format(health.mortalityCirculatory)}</strong><small>ogni 100.000 residenti</small></span></li><li><span>Malattie respiratorie</span><span class="deep-list-value"><strong>${number2.format(health.mortalityRespiratory)}</strong><small>ogni 100.000 residenti</small></span></li></ul></div></div></details></section>`;
    }
    if (themeKey === 'economia') {
      const e = detail.economy;
      const maxWorkers = Math.max(...e.topSectors.map(s => s.workers), 1);
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Struttura economica</h3></div><p>Fasce di reddito, capacità ricettiva e principali settori per presenza locale. I valori derivano dalle stesse fonti richiamate negli indicatori.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Strutture ricettive</span><strong>${number0.format(e.tourismStructures)}</strong><small>Anno ${html(e.tourismYear)}</small></article><article class="deep-fact"><span>Posti letto</span><strong>${number0.format(e.tourismBeds)}</strong><small>Hotel e altre strutture</small></article><article class="deep-fact"><span>Dichiaranti</span><strong>${number0.format(town.taxpayers)}</strong><small>Anno ${html(e.incomeYear)}</small></article><article class="deep-fact"><span>Permanenza media</span><strong>${number2.format(town.tourism.averageStay)}</strong><small>Notti per arrivo</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio economico</span><small>Settori produttivi e fasce di reddito</small></summary><div class="deep-columns"><div><h4>Principali settori per addetti</h4><div class="deep-bar-list">${e.topSectors.map(s => `<div class="deep-bar-row"><div class="deep-bar-heading"><span>${html(s.label)}</span><span class="deep-bar-value"><strong>${number2.format(s.workers)}</strong><small>addetti</small></span></div><div class="deep-bar-track"><span style="width:${s.workers / maxWorkers * 100}%"></span></div><small>${number0.format(s.localUnits)} unità locali</small></div>`).join('')}</div></div>
        <div><h4>Dichiaranti per fascia di reddito</h4><ul class="deep-list deep-list--income">${e.incomeBands.map(b => `<li><span>${html(b.label)}</span><span class="deep-list-value"><strong>${number0.format(b.people)}</strong><small>dichiaranti</small></span></li>`).join('')}</ul></div></div></details></section>`;
    }
    if (themeKey === 'mobilita') {
      const m = detail.mobility;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Flussi e parco veicolare</h3></div><p>Pendolarismo rilevato dal censimento e consistenza del parco veicolare. Il saldo non misura la qualità della mobilità.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Escono dal comune</span><strong>${number0.format(m.outbound)}</strong><small>Pendolari · ${html(m.year)}</small></article><article class="deep-fact"><span>Entrano nel comune</span><strong>${number0.format(m.inbound)}</strong><small>Pendolari · ${html(m.year)}</small></article><article class="deep-fact"><span>Saldo</span><strong>${number0.format(m.balance)}</strong><small>Entrate meno uscite</small></article><article class="deep-fact"><span>Autocontenimento</span><strong>${number1.format(m.selfContainment)}%</strong><small>Lavora nello stesso comune</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra origini e destinazioni</span><small>Prime cinque relazioni di pendolarismo</small></summary><div class="deep-columns"><div><h4>Destinazioni principali</h4><ul class="deep-list deep-list--flows">${m.topDestinations.map(x => `<li><span>${html(x.name)}</span><span class="deep-list-value"><strong>${number0.format(x.people)}</strong><small>pendolari</small></span></li>`).join('')}</ul></div><div><h4>Origini principali</h4><ul class="deep-list deep-list--flows">${m.topOrigins.map(x => `<li><span>${html(x.name)}</span><span class="deep-list-value"><strong>${number0.format(x.people)}</strong><small>pendolari</small></span></li>`).join('')}</ul></div></div></details>
        <div class="deep-inline-note"><span>Autovetture registrate</span><strong>${number0.format(m.cars)}</strong><small>${number1.format(m.motorization)} auto ogni 1.000 residenti; ${number1.format(m.pollutingCars)}% nelle classi più inquinanti.</small></div></section>`;
    }
    if (themeKey === 'ambiente') {
      const e = detail.environment;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Pressioni ambientali</h3></div><p>Andamento dei rifiuti, incremento netto di suolo consumato ed esposizione della popolazione ai rischi territoriali.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Raccolta differenziata</span><strong>${number2.format(e.recycling.at(-1))}%</strong><small>${html(e.wasteYears.at(-1))}</small></article><article class="deep-fact"><span>Rifiuti per residente</span><strong>${number0.format(e.wasteKgPerResident.at(-1))} kg</strong><small>${html(e.wasteYears.at(-1))}</small></article><article class="deep-fact"><span>Nuovo suolo consumato</span><strong>${number2.format(e.landUseNetHa.reduce((sum, value) => sum + Number(value || 0), 0))} ha</strong><small>Somma degli intervalli disponibili</small></article><article class="deep-fact"><span>Intervalli ISPRA</span><strong>${number0.format(e.landIntervals.length)}</strong><small>Serie monitorata</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio dei rischi</span><small>Popolazione, famiglie ed edifici esposti</small></summary><div class="risk-grid"><article><span>Esposizione al rischio alluvioni</span><strong>${number0.format(e.flood.population)} persone</strong><dl><div><dt>Quota residenti</dt><dd>${number1.format(e.flood.populationPct)}%</dd></div><div><dt>Edifici</dt><dd>${number0.format(e.flood.buildings)}</dd></div></dl></article><article><span>Esposizione al rischio frane</span><strong>${number0.format(e.landslide.population)} persone</strong><dl><div><dt>Quota residenti</dt><dd>${number1.format(e.landslide.populationPct)}%</dd></div><div><dt>Edifici</dt><dd>${number0.format(e.landslide.buildings)}</dd></div></dl></article></div></details></section>`;
    }
    if (themeKey === 'comunita') {
      const g = detail.government;
      const completed = g.pnrrProjects ? g.pnrrConcluded / g.pnrrProjects * 100 : 0;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Cassa, opere e PNRR</h3></div><p>Pagamenti e incassi di cassa, valore delle opere monitorate e stato dei progetti PNRR censiti.</p></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio amministrativo</span><small>Cassa, opere monitorate e progetti PNRR</small></summary><div class="government-grid"><article><span>Pagamenti</span><strong>${currency0.format(g.payments)}</strong><small>Anno ${html(g.year)}</small></article><article><span>Incassi</span><strong>${currency0.format(g.receipts)}</strong><small>Saldo ${currency0.format(g.cashBalance)}</small></article><article><span>Opere monitorate</span><strong>${number0.format(g.publicWorks)}</strong><small>Valore ${currency0.format(g.publicWorksValue)}</small></article><article><span>Progetti PNRR conclusi</span><strong>${number0.format(g.pnrrConcluded)} su ${number0.format(g.pnrrProjects)}</strong><div class="progress-track"><span style="width:${completed}%"></span></div><p>${currency0.format(g.pnrrFunding)} di risorse assegnate.</p></article></div></details></section>`;
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
      ['2026.08.05-v1.6.0','5 agosto 2026','98 indicatori. Aggiunto il tema Bilanci comunali con rendiconto 2024–2025, capacità di riscossione e pagamento, risultato di amministrazione e spesa per missione.'],
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
        overlay.innerHTML = `<section class="search-dialog" role="dialog" aria-modal="true" aria-labelledby="search-title"><div class="search-dialog-head"><div><span class="overline">Esplora i dati</span><h2 id="search-title">Cerca un indicatore</h2></div><button type="button" data-close-search aria-label="Chiudi la ricerca"><span aria-hidden="true">×</span><span class="search-close-label">Chiudi</span></button></div><label class="search-field"><svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg><input type="search" placeholder="Prova: PIL, reati, disoccupati, farmacie…" autocomplete="off"></label><div class="search-results" aria-live="polite"></div><footer class="search-footer"><span><kbd>Esc</kbd> chiude</span><span>La ricerca porta al dato: non inventa corrispondenze.</span></footer></section>`;
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
