(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', globalThis.__OV_SCRIPT_URL__ || script?.src || location.href);
  const app = document.getElementById('app');
  const pageType = document.body.dataset.page || 'home';
  const pageTheme = document.body.dataset.theme || '';
  const pageTown = document.body.dataset.town || '';
  const pageMetric = document.body.dataset.metric || '';

  const themeSvgPaths = {
    demografia: '<path d="M18 21a8 8 0 0 0-16 0"></path><circle cx="10" cy="8" r="5"></circle><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"></path>',
    economia: '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"></path><path d="M7 12h5"></path><path d="M15 9.4a4 4 0 1 0 0 5.2"></path>',
    lavoro: '<path d="M12 12h.01"></path><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"></path><path d="M22 13a18.15 18.15 0 0 1-20 0"></path><rect width="20" height="14" x="2" y="6" rx="2"></rect>',
    istruzione: '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"></path><path d="M22 10v6"></path><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"></path>',
    salute: '<path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"></path><path d="M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"></path>',
    mobilita: '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"></path><path d="M7 14h.01"></path><path d="M17 14h.01"></path><rect width="18" height="8" x="3" y="10" rx="2"></rect><path d="M5 18v2"></path><path d="M19 18v2"></path>',
    sicurezza: '<path d=\"M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3z\"></path><path d=\"m9 12 2 2 4-4\"></path>',
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
    income: ['redditi', 'stipendi', 'irpef', 'dichiarazioni'],
    incomeDistribution: ['fasce reddito', 'redditi bassi', 'irpef', 'dichiaranti', 'oltre 55000'],
    municipalIrpef: ['addizionale comunale', 'irpef comunale', 'aliquota irpef', 'fiscalità locale', 'tasse comunali'],
    tariStandardHousehold: ['tari', 'tariffa rifiuti', 'tassa rifiuti', '3 persone', '100 mq'],
    municipalImuStandard: ['imu', 'seconda casa', 'seconda abitazione', 'aliquota imu'],
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
    fuelPrices: ['benzina', 'gasolio', 'diesel', 'carburante', 'prezzo carburanti'],
    vacantHomes: ['case vuote', 'abitazioni non occupate'], singleHouseholds: ['persone sole', 'famiglie'],
    householdSize: ['componenti famiglia', 'nucleo familiare'],
    housingStockPer1000: ['patrimonio abitativo', 'abitazioni per residenti', 'case per abitante'],
    nonOccupiedHomesPer1000: ['case non occupate per residenti', 'abitazioni vuote', 'seconde case'],
    cohabitingHouseholds: ['famiglie coabitanti', 'coabitazione', 'disagio abitativo'],
    erpArrears: ['morosità erp', 'edilizia residenziale pubblica', 'erp lucca', 'affitti erp', 'canoni non incassati'],
    landUse: ['consumo di suolo', 'cementificazione'],
    landUseChange: ['nuovo suolo consumato'], recycling: ['raccolta differenziata', 'rifiuti'],
    wastePerResident: ['rifiuti pro capite', 'kg'], floodExposure: ['alluvione', 'rischio idraulico'],
    wasteServiceCost: ['costo rifiuti', 'ctotab', 'igiene urbana', 'costo servizio rifiuti'],
    landslideExposure: ['frane', 'rischio geomorfologico'],
    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],
    agriculturalFarms: ['aziende agricole', 'imprese agricole', 'censimento agricoltura'],
    agriculturalUsedArea: ['sau', 'superficie agricola utilizzata', 'ettari agricoli'],
    averageAgriculturalFarmSize: ['dimensione aziende agricole', 'ettari per azienda', 'azienda con sau'],
    cropProfile: ['colture', 'seminativi', 'olivo', 'olive', 'vite', 'pascoli'],
    irrigatedAgriculturalArea: ['irrigazione', 'superficie irrigata', 'sau irrigata'],
    bathingWaterQuality: ['balneazione', 'qualità acque', 'mare', 'aree eccellenti'],
    bathingNonCompliantSamples: ['balneazione', 'campioni non conformi', 'escherichia coli', 'enterococchi'],
    blueFlagBeaches: ['bandiera blu', 'spiagge', 'mare', 'fee'],
    shorelineDynamics: ['erosione', 'avanzamento', 'litorale', 'costa'],
    rigidDefenceProtectedCoast: ['costa protetta', 'opere rigide', 'difesa costiera'],
    maritimeConcessions: ['concessioni demaniali', 'demanio marittimo', 'balneari', 'turistico ricreative', 'sid'],
    maritimeConcessionFeesDue: ['canoni demaniali', 'canone dovuto', 'demanio marittimo', 'sid', 'balneari'],
    extractiveSites: ['cave', 'cava', 'rtcave', 'attività estrattive', 'marmo', 'lapideo', 'siti estrattivi'],
    extractiveProduction: ['produzione cave', 'volume estratto', 'marmo estratto', 'materiale estratto', 'prc'],
    extractivePlanning: ['giacimenti', 'giacimenti potenziali', 'aree contigue di cava', 'acc', 'piano regionale cave', 'prc'],
    waterNetworkLosses: ['perdite idriche', 'rete idrica', 'acquedotto', 'acqua immessa'],
    drinkingWaterQuality: ['acqua potabile', 'qualità acqua', 'gaia', 'nitrati', 'durezza'],
    remediationProceedings: ['bonifiche', 'sisbon', 'siti contaminati', 'iter attivi', 'iter chiusi'],
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
    ageDistribution: ['fasce eta', 'giovani', 'anziani', 'eta media', '0 14', '15 19', '20 34', '35 49', '50 64', '65 79', '80 plus', 'fasce di età', 'struttura popolazione'],
    internalResidentialMobility: ['trasferimenti di residenza', 'iscritti da altri comuni', 'cancellati verso altri comuni', 'saldo migratorio interno', 'iscritti', 'cancellati', 'mobilità residenziale'],
    foreignResidentialMobility: ['immigrazione', 'emigrazione', 'estero', 'iscritti dall estero', 'cancellati per l estero', 'saldo migratorio estero'],
    totalResidentialMobility: ['mobilità complessiva', 'trasferimenti di residenza', 'saldo migratorio complessivo', 'iscritti', 'cancellati'],
    foreignResidents: ['stranieri', 'popolazione straniera', 'cittadinanza', 'residenti stranieri', 'immigrazione'],
    omiResidential: ['immobiliare', 'omi', 'prezzi case', 'prezzo mq', 'vendita', 'affitto', 'canone', 'locazione'],
    populationChange: ['calo demografico', 'crescita popolazione', 'variazione residenti'],
    tourismSeasonality: ['stagionalita', 'estate', 'mesi turistici', 'pressione turistica'],
    foreignTourismShare: ['turisti stranieri', 'presenze estere', 'turismo internazionale'],
    commuterBalanceRate: ['saldo pendolare', 'lavoratori in entrata', 'lavoratori in uscita'],
    residualWaste: ['rifiuto residuo', 'indifferenziato', 'rifiuti non differenziati'],
    roadSafety: ['incidenti', 'sicurezza stradale', 'mortalità', 'lesività', 'feriti'],
    roadFinesPerResident: ['multe', 'sanzioni', 'codice della strada', 'autovelox'],
    securityMissionExpenditurePerResident: ['ordine pubblico', 'sicurezza', 'missione 03', 'spesa sicurezza'],
    capitalPayments: ['investimenti', 'conto capitale', 'pagamenti capitale']
  };

  const html = (value) => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const route = (path = '') => new URL(String(path).replace(/^\//, ''), ROOT).href;
  const asset = (path = '') => route(path);
  const normalize = (value) => String(value ?? '').toLocaleLowerCase('it')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const indicatorSlug = (metric) => normalize(metric?.meta?.label).replaceAll(' ', '-');
  const indicatorHref = (metric) => route(`indicatori/${indicatorSlug(metric)}/`);

  const forceItalianGrouping = (formatted, value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || Math.abs(numeric) < 1000) return formatted;
    const match = String(formatted).match(/^([−-]?)(\d+)(.*)$/);
    if (!match) return formatted;
    const [, sign, integer, suffix] = match;
    if (integer.length <= 3) return formatted;
    return `${sign}${integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}${suffix}`;
  };
  const italianFormatter = options => {
    const formatter = new Intl.NumberFormat('it-IT', { ...options, useGrouping: 'always' });
    return { format: value => forceItalianGrouping(formatter.format(value), value) };
  };
  const number0 = italianFormatter({ maximumFractionDigits: 0 });
  const number1 = italianFormatter({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number2 = italianFormatter({ minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const number3 = italianFormatter({ minimumFractionDigits: 3, maximumFractionDigits: 3 });
  const currency0 = italianFormatter({ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
  const currency2 = italianFormatter({ style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function formatValue(value, unit) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'n.d.';
    const v = Number(value);
    switch (unit) {
      case 'currency': return currency0.format(v);
      case 'currency2': return currency2.format(v);
      case 'millionCurrency': return `${number1.format(v)} mln €`;
      case 'percent': return `${number1.format(v)}%`;
      case '%': return `${number2.format(v)}%`;
      case 'percent2': return `${number2.format(v)}%`;
      case 'percentagePoints': return `${number1.format(v)}%`;
      case 'index': return number1.format(v);
      case 'decimal': return number2.format(v);
      case 'years': return `${number2.format(v)} anni`;
      case 'hours': return `${number2.format(v)} h`;
      case 'nights': return `${number2.format(v)} notti`;
      case 'people': return `${number0.format(v)} persone`;
      case 'studentsPerClass': return `${number1.format(v)} alunni/classe`;
      case 'minutes': return `${number1.format(v)} min`;
      case 'per100': return `${number2.format(v)} ogni 100`;
      case 'per10k': return `${number1.format(v)} ogni 10.000`;
      case 'per1000': return `${number2.format(v)} ogni 1.000`;
      case 'per100k': return `${number2.format(v)} ogni 100.000`;
      case 'eurm2': return `${number0.format(v)} €/m²`;
      case 'rentm2': return `${number1.format(v)} €/m²/mese`;
      case 'eurliter': return `${number3.format(v)} €/l`;
      case 'eurPerResident': return `${number2.format(v)} €/ab`;
      case 'kg': return `${number0.format(v)} kg`;
      case 'hectares': return `${number2.format(v)} ha`;
      case 'cubicMetres': return `${number0.format(v)} m³`;
      case 'hectaresPerFarm': return `${number2.format(v)} ha/azienda`;
      case 'km': return `${number2.format(v)} km`;
      case 'kmIntervention': return `${number2.format(v)} km-intervento`;
      default: return number0.format(v);
    }
  }

  function formatMetricRowValue(row, value, unit) {
    if (row?.notApplicable) return 'n.a.';
    return formatValue(value, unit);
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
              <a href="${route('opportunita/')}">Opportunità</a>
              <a href="${route('progetto/')}">Il progetto</a>
              <a href="${route('stato-dati/')}" data-data-status-nav="header">Stato dati</a>
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
          <a href="${route('stato-dati/')}" data-data-status-nav="footer">Stato dei dati</a>
          <a href="${route('opportunita/')}">Opportunità</a>
          <a href="${route('progetto/#metodo')}">Metodo</a>
          <a href="${route('progetto/#licenza')}">Licenza</a>
          <a href="${route('progetto/#versioni')}">Versioni dei dati</a>
          <a href="${route('segnala/')}">Segnala un dato</a>
          <a href="mailto:info@osservatorioversilia.it">Contatti</a>
        </nav>
        <div class="footer-note">
          <span>7 comuni · ${Object.keys(data.themes).length} temi</span><span>v. dati ${html(data.version)}</span><span>aggiornato ${html(data.updated)}</span>
        </div>
      </footer>`;
  }
 function mountShell(data) {
    const headerMount = document.getElementById('site-header-mount');
    if (!headerMount) throw new Error('Mount header canonico assente');
    headerMount.innerHTML = headerMarkup(data);
    const footerMount = document.getElementById('site-footer-mount');
    if (footerMount) footerMount.innerHTML = footerMarkup(data);
    installSearch(data);
  }

  function metricRows(data, metricKey, normalized = false) {
    const metric = data.metrics[metricKey];
    const distribution = metric.meta.compositeType === 'distribution';
    return metric.rows.map(row => ({
      ...row,
      displayValue: normalized && row.normalized ? row.normalized.value : (distribution && row.summaryValue !== undefined ? row.summaryValue : row.value),
      displayUnit: normalized && row.normalized ? row.normalized.unit : (distribution && metric.meta.summaryUnit ? metric.meta.summaryUnit : metric.meta.unit)
    })).sort((a, b) => (b.displayValue ?? -Infinity) - (a.displayValue ?? -Infinity));
  }

  function barRows(data, metricKey, options = {}) {
    const normalized = Boolean(options.normalized);
    const selectedTown = options.selectedTown || '';
    const rows = metricRows(data, metricKey, normalized);
    const max = Math.max(...rows.map(r => Number(r.displayValue) || 0), 0.0001);
    return rows.map((row, index) => {
      const query = new URLSearchParams({ tema: data.metrics[metricKey].meta.theme, indicatore: metricKey });
      const rowSlug = row.slug || normalize(row.town).replaceAll(' ', '-');
      const href = route(`comuni/${rowSlug}/?${query}`);
      const missing = row.displayValue === null || row.displayValue === undefined;
      const formatted = formatMetricRowValue(row, row.displayValue, row.displayUnit);
      return `<a href="${href}" class="bar-row ${rowSlug === selectedTown ? 'selected' : ''}" aria-label="${html(row.town)}: ${html(formatted)}">
        <span class="bar-rank">${missing ? '—' : index + 1}</span><span class="bar-town">${html(row.town)}</span>
        <span class="bar-track"><span class="bar-fill" style="width:${missing ? 0 : Math.max(1.5, (Number(row.displayValue) || 0) / max * 100)}%"></span>
          <span class="bar-hover-label">${html(row.town)} · ${html(formatted)}</span></span>
        <strong>${html(formatted)}</strong>
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
      <section class="project-callout page-width opportunity-home-callout" aria-labelledby="opportunita-home-title">
        <div><span class="overline">Opportunità per il territorio</span><h2 id="opportunita-home-title">Radar Opportunità</h2></div>
        <div><p>Bandi, avvisi, incentivi e programmi utili ai Comuni della Versilia, raccolti da fonti pubbliche e accompagnati dal rimando alla fonte ufficiale.</p><a class="text-link" href="${route('opportunita/')}">Esplora le opportunità <b>→</b></a></div></section>
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
    const labelCounts = theme.metrics.reduce((counts, key) => {
      const label = data.metrics[key].meta.shortLabel;
      counts[label] = (counts[label] || 0) + 1;
      return counts;
    }, {});
    return `<div class="metric-switch metric-catalog ${compact ? 'compact-list' : ''}" role="tablist" aria-label="Indicatori di ${html(theme.label)}">${groups.map(section => `<section class="metric-group" data-section="${html(section.key)}">
      <div class="metric-group-heading"><strong>${html(section.label)}</strong>${compact && section.description ? `<span>${html(section.description)}</span>` : ''}</div>
      <div class="metric-group-buttons">${section.metrics.map(key => { const meta = data.metrics[key].meta; const label = labelCounts[meta.shortLabel] > 1 ? meta.label : meta.shortLabel; return `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(label)}</button>`; }).join('')}</div>
    </section>`).join('')}</div>`;
  }

  function groupedIndicatorCards(data, town, themeKey, activeKey) {
    const theme = data.themes[themeKey];
    return themeSections(theme).map(section => `<section class="indicator-group" data-section="${html(section.key)}">
      <div class="indicator-group-heading"><div><span class="overline">Sezione</span><h4>${html(section.label)}</h4></div><p>${html(section.description || '')}</p></div>
      <div class="indicator-card-grid">${section.metrics.map(key => indicatorCard(data, town, themeKey, key, activeKey)).join('')}</div>
    </section>`).join('');
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
      <nav class="theme-nav" aria-label="Temi della scheda">${themeButtons}</nav>
    </div>`;
  }

  function updateTownContextLinks(data, themeKey, metricKey) {
    document.querySelectorAll('[data-town-link]').forEach(link => {
      link.href = route(`comuni/${link.dataset.townLink}/?tema=${themeKey}&indicatore=${metricKey}`);
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
      <section id="compare-demographic-pyramid" class="compare-demographic-pyramid page-width"></section>
      <section id="compare-benchmark" class="page-width"></section>
      ${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}
      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}
      <section id="compare-tools" class="compare-post-benchmark-tools page-width"></section>
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

  function erpArrearsDetailMarkup(metric, row) {
    if (metric?.meta?.key !== 'erpArrears' || !row?.accounting) return '';
    const detail = row.accounting;
    return `<details class="detail-disclosure erp-arrears-detail"><summary><span>Dettaglio contabile ${html(String(detail.year))}</span><small>valori cumulati · E.R.P. Lucca</small></summary><div class="composite-town-detail"><div><span>Importi emessi cumulati</span><b>${html(formatValue(detail.issued,'currency2'))}</b><small>denominatore del rapporto</small></div><div><span>Morosità cumulata</span><b>${html(formatValue(detail.arrears,'currency2'))}</b><small>somme non ancora incassate</small></div></div><p class="aggregate-note">La percentuale è ricalcolata dagli importi sopra indicati; non viene usata la percentuale stampata nel prospetto sorgente quando non riconcilia.</p></details>`;
  }

  function compositePartLegend(metric) {
    const parts = metric.rows?.[0]?.parts || metric.aggregate?.parts || [];
    return `<div class="composite-legend">${parts.map((part, index) => `<span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span>`).join('')}</div>`;
  }

  function compositeSummary(metric, row) {
    const value = row?.summaryValue;
    const unit = metric.meta.summaryUnit || metric.meta.unit;
    return {
      label: metric.meta.summaryLabel || 'Valore di sintesi',
      value,
      unit,
      formatted: value === null || value === undefined ? 'n.d.' : (unit === 'years' ? `${number1.format(value)} anni` : formatValue(value, unit))
    };
  }

  function compositeAggregateSummary(metric) {
    const value = metric.aggregate?.summaryValue;
    const unit = metric.meta.summaryUnit || metric.meta.unit;
    return {
      label: metric.aggregate?.summaryLabel || metric.meta.summaryLabel || metric.aggregate?.label || 'Versilia',
      value,
      unit,
      formatted: value === null || value === undefined ? 'n.d.' : (unit === 'years' ? `${number1.format(value)} anni` : formatValue(value, unit))
    };
  }

  function compositeSegmentMarkup(part, index, options = {}) {
    const value = Math.max(0, Number(part.value) || 0);
    const countLabel = options.countLabel || '';
    const sizeClass = value < 3.5 ? ' label-tiny' : value < 6 ? ' label-narrow' : '';
    return `<span class="composite-segment part-${index}${sizeClass}" role="listitem" tabindex="0" style="width:${value}%" aria-label="${html(part.label)}: ${html(number1.format(value))}%${countLabel && part.count !== undefined ? ` · ${html(number0.format(part.count))} ${html(countLabel)}` : ''}">
      <b aria-hidden="true">${html(number1.format(value))}%</b>
      <span class="bar-hover-label">${html(part.label)} · ${html(number1.format(value))}%</span>
    </span>`;
  }

  function compositeStackMarkup(parts, options = {}) {
    return `<div class="composite-stack ${options.town ? 'composite-stack-town' : ''}" role="list" aria-label="${html(options.ariaLabel || 'Distribuzione percentuale')}">${parts.map((part,index)=>compositeSegmentMarkup(part,index,options)).join('')}</div>`;
  }

  function agePyramidTooltipMarkup({boxX,boxY,guideX,guideY,label,value}) {
    const boxWidth = 208, boxHeight = 40;
    const targetY = boxY < guideY ? boxY + boxHeight : boxY;
    return `<g class="chart-tooltip" hidden><line class="chart-guide" x1="${guideX}" y1="${guideY}" x2="${guideX}" y2="${targetY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+15}">${html(label)}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+31}">${html(number0.format(value))} residenti</text></g>`;
  }

  function agePyramidMarkup(metric, row) {
    const pyramid = row?.ageSexPyramid;
    if (metric.meta.key !== 'ageDistribution' || !pyramid?.displayBands?.length) return '';
    const bands = [...pyramid.displayBands].reverse();
    const max = Math.max(...bands.flatMap(item => [Number(item.men)||0, Number(item.women)||0]), 1);
    const niceMax = Math.ceil(max / 250) * 250 || max;
    const center = 430, gap = 42, maxWidth = 300, rowHeight = 25, top = 74, bottom = 54;
    const height = top + bands.length * rowHeight + bottom;
    const axisTicks = [niceMax, Math.round(niceMax/2), 0, Math.round(niceMax/2), niceMax];
    const tickXs = [center-gap-maxWidth, center-gap-maxWidth/2, center, center+gap+maxWidth/2, center+gap+maxWidth];
    const axis = tickXs.map((x,index)=>`<g class="age-pyramid-axis"><line x1="${x}" y1="${top-16}" x2="${x}" y2="${height-bottom+10}"/><text x="${x}" y="${height-22}" text-anchor="middle">${html(number0.format(axisTicks[index]))}</text></g>`).join('');
    const rows = bands.map((item,index)=>{
      const y = top + index * rowHeight;
      const men = Number(item.men)||0;
      const women = Number(item.women)||0;
      const menWidth = men / niceMax * maxWidth;
      const womenWidth = women / niceMax * maxWidth;
      const tooltipY = y < 112 ? y + 22 : y - 46;
      const menBoxX = Math.max(8, center-gap-menWidth-218);
      const womenBoxX = Math.min(644, center+gap+womenWidth+10);
      const menLabel = `${item.label} · Uomini`;
      const womenLabel = `${item.label} · Donne`;
      return `<g class="age-pyramid-row"><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(menLabel)}: ${html(number0.format(men))} residenti"><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="17" rx="3" class="age-pyramid-men"></rect>${agePyramidTooltipMarkup({boxX:menBoxX,boxY:tooltipY,guideX:center-gap-menWidth,guideY:y+8.5,label:menLabel,value:men})}</g><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(womenLabel)}: ${html(number0.format(women))} residenti"><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="17" rx="3" class="age-pyramid-women"></rect>${agePyramidTooltipMarkup({boxX:womenBoxX,boxY:tooltipY,guideX:center+gap+womenWidth,guideY:y+8.5,label:womenLabel,value:women})}</g><text x="${center}" y="${y+13}" text-anchor="middle">${html(item.label)}</text></g>`;
    }).join('');
    return `<details class="detail-disclosure age-pyramid-detail"><summary><span>${html(metric.meta.pyramidLabel || 'Piramide per età e sesso')}</span><small>${html(String(pyramid.year))} · asse X in residenti</small></summary><div class="age-pyramid-body"><div class="trend-chart age-pyramid-trend"><svg class="age-pyramid-chart" viewBox="0 0 860 ${height}" role="img" aria-label="Piramide per età e sesso di ${html(row.town)}"><text x="215" y="32" text-anchor="middle" class="age-pyramid-title">Uomini</text><text x="645" y="32" text-anchor="middle" class="age-pyramid-title">Donne</text><text x="430" y="54" text-anchor="middle" class="age-pyramid-unit">Scala: residenti per classe d’età</text>${axis}<line x1="${center-gap}" y1="${top-22}" x2="${center-gap}" y2="${height-bottom+10}" class="age-pyramid-center"/><line x1="${center+gap}" y1="${top-22}" x2="${center+gap}" y2="${height-bottom+10}" class="age-pyramid-center"/>${rows}<text x="430" y="${height-4}" text-anchor="middle" class="age-pyramid-unit">residenti</text></svg></div><p class="aggregate-note age-pyramid-note">Classi quinquennali costruite dal dettaglio POSAS per singola età e sesso.</p></div></details>`;
  }

  function foreignOriginsListMarkup(title, items, note) {
    return `<section class="income-band-town-detail foreign-origin-section"><h4>${html(title)}</h4><div class="composite-town-detail">${(items||[]).map(item=>`<div><span>${html(item.label)}</span><b>${html(number0.format(item.count))}</b><small>${item.share === null || item.share === undefined ? '' : `${html(number1.format(item.share))}%`} ${html(note)}</small></div>`).join('')}</div></section>`;
  }

  function foreignOriginsMarkup(metric, source, scope = 'town') {
    const detail = source?.foreignOrigins || source;
    if (metric.meta.key !== 'foreignResidents' || !detail) return '';
    const title = scope === 'compare' ? 'Versilia · cittadinanze e paesi esteri di nascita' : 'Principali cittadinanze e paesi di nascita';
    const caption = scope === 'compare' ? `${html(String(detail.year))} · somma dei 7 comuni` : `${html(String(detail.year))} · Istat RCS`;
    return `<details class="detail-disclosure foreign-origins-detail ${scope === 'compare' ? 'compare-foreign-origins' : ''}"><summary><span>${html(title)}</span><small>${caption}</small></summary><div class="foreign-origin-body">${foreignOriginsListMarkup('Cittadinanze straniere più numerose',detail.citizenshipTop,'dei residenti stranieri')}${foreignOriginsListMarkup('Paesi esteri di nascita più frequenti',detail.birthCountryTop,'dei residenti nati all’estero')}</div><p class="aggregate-note foreign-origins-note">Cittadinanza e paese di nascita sono due distribuzioni separate: Istat RCS non pubblica il loro incrocio. Nel confronto Versilia i valori sono somme comunali riordinate sul totale.</p></details>`;
  }

  function foreignOriginsCompareMarkup(metric) {
    return foreignOriginsMarkup(metric, metric.aggregate?.foreignOrigins, 'compare');
  }

  function installAgePyramidDelegation(root) {
    if (!root || root.dataset.agePyramidDelegated === '1') return;
    root.dataset.agePyramidDelegated = '1';
    const chartFor = target => target?.closest?.('.age-pyramid-trend');
    const pointFor = target => target?.closest?.('.age-pyramid-point');
    const hide = chart => {
      if (!chart) return;
      chart.querySelectorAll('.age-pyramid-point').forEach(point => {
        point.classList.remove('active');
        point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
      });
    };
    const show = point => {
      const chart = point?.closest('.age-pyramid-trend');
      if (!point || !chart) return;
      hide(chart);
      point.classList.add('active');
      point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
    };
    root.addEventListener('pointerover', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('pointerout', event => {
      const chart = chartFor(event.target);
      if (!chart || chart.contains(event.relatedTarget)) return;
      hide(chart);
    });
    root.addEventListener('focusin', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('focusout', event => {
      const chart = chartFor(event.target);
      if (!chart || chart.contains(event.relatedTarget)) return;
      hide(chart);
    });
    root.addEventListener('click', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('keydown', event => {
      const point = pointFor(event.target);
      if (!point || !root.contains(point)) return;
      const chart = point.closest('.age-pyramid-trend');
      const points = [...chart.querySelectorAll('.age-pyramid-point')];
      const index = points.indexOf(point);
      if (event.key === 'Escape') { hide(chart); point.blur(); return; }
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === 'ArrowLeft') next = (index - 1 + points.length) % points.length;
      if (event.key === 'ArrowRight') next = (index + 1) % points.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = points.length - 1;
      points[next]?.focus();
    });
  }
  /* data-age-pyramid-delegated */

  function omiZoneTableMarkup(row, compact = false) {
    const zones = row?.zones || [];
    return `<div class="omi-zone-table-wrap ${compact ? 'compact' : ''}"><table class="omi-zone-table"><thead><tr><th>Zona OMI</th><th>Area</th><th>Vendita</th><th>Affitto</th></tr></thead><tbody>${zones.map(zone => `<tr><td><b>${html(zone.code)}</b></td><td>${html(zone.label)}</td><td>${html(formatValue(zone.sale,'eurm2'))}</td><td>${html(formatValue(zone.rent,'rentm2'))}</td></tr>`).join('')}</tbody></table></div>`;
  }


  function waterQualityTableMarkup(metric, locality) {
    const defs = metric.parameterDefinitions || [];
    return `<div class="water-quality-table-wrap"><table class="water-quality-table"><thead><tr><th>Parametro</th><th>Unità</th><th>Valore medio pubblicato</th><th>Limite / riferimento</th></tr></thead><tbody>${defs.map((def,index)=>`<tr><td><b>${html(def.name)}</b></td><td>${html(def.unit)}</td><td><strong>${html(locality.values?.[index] ?? 'n.d.')}</strong></td><td>${html(def.reference || '—')}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function waterQualityNumericValue(raw) {
    const text=String(raw ?? '').trim();
    if(!text || /[<>]/.test(text)) return null;
    const value=Number(text.replace(',','.'));
    return Number.isFinite(value) ? value : null;
  }

  function waterQualityCensoredLimit(raw) {
    const match=String(raw ?? '').trim().match(/^<\s*([0-9]+(?:[.,][0-9]+)?)/);
    if(!match) return null;
    const value=Number(match[1].replace(',','.'));
    return Number.isFinite(value) ? value : null;
  }

  function waterQualityChartSeries(row, parameterIndex) {
    const samples=(row.localities||[]).map(locality=>{
      const raw=String(locality.values?.[parameterIndex] ?? 'n.d.').trim();
      return {raw,numeric:waterQualityNumericValue(raw),censoredLimit:waterQualityCensoredLimit(raw)};
    });
    const numeric=samples.filter(item=>item.numeric!==null).sort((a,b)=>a.numeric-b.numeric);
    const censored=samples.filter(item=>item.censoredLimit!==null);
    const censoredLabels=[...new Set(censored.map(item=>item.raw))];
    const minimum=numeric[0]||null,maximum=numeric.at(-1)||null;
    const censorLimit=censored.length?Math.max(...censored.map(item=>item.censoredLimit)):null;
    const rangeLabel=minimum
      ? `${minimum.raw}${minimum.numeric===maximum.numeric?'':` – ${maximum.raw}`}${censored.length?' · presenti valori < soglia':''}`
      : (censoredLabels.length?censoredLabels.join(' · '):'n.d.');
    return {row,minimum,maximum,censorLimit,hasCensored:Boolean(censored.length),rangeLabel};
  }

  function waterQualityChartDomain(series) {
    const numeric=series.flatMap(item=>[item.minimum?.numeric,item.maximum?.numeric,item.censorLimit]).filter(value=>Number.isFinite(value));
    if(!numeric.length) return {minimum:0,maximum:1};
    let minimum=Math.min(...numeric),maximum=Math.max(...numeric);
    if(!series.some(item=>item.minimum)) minimum=Math.min(0,minimum);
    if(maximum<=minimum) {
      const padding=Math.max(Math.abs(maximum)*.05,.1);
      minimum=Math.max(0,minimum-padding);
      maximum+=padding;
    }
    return {minimum,maximum};
  }

  function waterQualityChartPosition(value,domain) {
    if(!Number.isFinite(value)) return 0;
    return Math.max(0,Math.min(100,(value-domain.minimum)/(domain.maximum-domain.minimum)*100));
  }

  function waterQualityChartNumber(value) {
    return new Intl.NumberFormat('it-IT',{maximumFractionDigits:3}).format(value);
  }

  function drinkingWaterQualityCompareMarkup(data, metricKey, parameterIndex=0) {
    const metric=data.metrics[metricKey],defs=metric.parameterDefinitions||[];
    const safeIndex=Math.max(0,Math.min(defs.length-1,Number(parameterIndex)||0)),def=defs[safeIndex]||{};
    const series=[...metric.rows].sort((a,b)=>a.town.localeCompare(b.town,'it')).map(row=>waterQualityChartSeries(row,safeIndex));
    const domain=waterQualityChartDomain(series),midpoint=(domain.minimum+domain.maximum)/2;
    const rows=series.map(item=>{
      const q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});
      const start=waterQualityChartPosition(item.minimum?.numeric,domain),end=waterQualityChartPosition(item.maximum?.numeric,domain);
      const censor=waterQualityChartPosition(item.censorLimit,domain);
      const numericMark=item.minimum
        ? (item.minimum.numeric===item.maximum.numeric
          ? `<i class="water-quality-range-point" style="left:${start}%"></i>`
          : `<i class="water-quality-range-segment" style="left:${start}%;width:${Math.max(1,end-start)}%"><b></b><b></b></i>`)
        : '';
      const censoredMark=item.hasCensored
        ? (item.minimum
          ? `<i class="water-quality-censored-marker" style="left:${censor}%"></i>`
          : `<i class="water-quality-censored-band" style="width:${Math.max(2,censor)}%"></i>`)
        : '';
      return `<a class="water-quality-range-row" role="listitem" href="${route(`comuni/${item.row.slug}/?${q}`)}" aria-label="${html(item.row.town)}: ${html(item.rangeLabel)} ${html(def.unit||'')}"><strong>${html(item.row.town)}</strong><span class="water-quality-range-track" aria-hidden="true">${numericMark}${censoredMark}</span><span class="water-quality-range-values">${html(item.rangeLabel)}<small>${html(def.unit||'')}</small></span><em>Apri la scheda →</em></a>`;
    }).join('');
    return `<div class="water-quality-compare-shell"><div class="water-quality-compare-controls"><label class="water-quality-selector"><span>Parametro</span><select data-water-quality-parameter-compare>${defs.map((item,index)=>`<option value="${index}" ${index===safeIndex?'selected':''}>${html(item.name)}</option>`).join('')}</select></label><dl class="water-quality-parameter-meta"><div><dt>Unità</dt><dd>${html(def.unit||'—')}</dd></div><div><dt>Limite / riferimento GAIA</dt><dd>${html(def.reference||'—')}</dd></div><div><dt>Periodo</dt><dd>${html(metric.meta.year)}</dd></div></dl></div><div class="water-quality-range-chart" role="list" aria-label="Confronto comunale per ${html(def.name)}"><div class="water-quality-range-axis" aria-hidden="true"><span>Comune</span><span class="water-quality-range-scale"><i style="left:0">${html(waterQualityChartNumber(domain.minimum))}</i><i style="left:50%">${html(waterQualityChartNumber(midpoint))}</i><i style="left:100%">${html(waterQualityChartNumber(domain.maximum))}</i></span><span>Minimo – massimo</span><span></span></div>${rows}</div><p class="composite-compare-note">Ogni riga rappresenta un Comune. La linea collega il minimo e il massimo osservati nelle sue località; il punto indica un valore unico. Il tratteggio segnala valori pubblicati da GAIA con “&lt;”, che non vengono trasformati in numeri. Il dettaglio delle singole località è disponibile soltanto nelle schede comunali.</p></div>`;
  }

  function waterQualitySelectedMarkup(metric,row,localityIndex=0,parameterIndex=0) {
    const localities=row.localities||[],defs=metric.parameterDefinitions||[];
    const safeLocality=Math.max(0,Math.min(localities.length-1,Number(localityIndex)||0));
    const safeParameter=Math.max(0,Math.min(defs.length-1,Number(parameterIndex)||0));
    const locality=localities[safeLocality],def=defs[safeParameter];
    if(!locality||!def) return '<p>Dato non disponibile.</p>';
    const value=String(locality.values?.[safeParameter] ?? 'n.d.');
    return `<article class="water-quality-parameter-card"><div class="water-quality-card-head"><div><span class="overline">Parametro selezionato</span><h4>${html(def.name)}</h4></div><a class="source-pill" href="${html(locality.url)}" target="_blank" rel="noreferrer">GAIA ↗</a></div><div class="water-quality-card-value"><strong>${html(value)}</strong><span>${html(def.unit||'')}</span></div><dl><div><dt>Località GAIA</dt><dd>${html(locality.name)}</dd></div><div><dt>Periodo</dt><dd>${html(locality.period||metric.meta.year)}</dd></div><div><dt>Limite / riferimento</dt><dd>${html(def.reference||'—')}</dd></div><div><dt>Valore</dt><dd>Media pubblicata da GAIA</dd></div></dl>${def.description?`<details class="water-quality-description"><summary><span>Come si legge il parametro</span><b aria-hidden="true"></b></summary><p>${html(def.description)}</p></details>`:''}</article><details class="water-quality-all-parameters"><summary><span>Mostra tutti i ${defs.length} parametri</span><b aria-hidden="true"></b></summary>${waterQualityTableMarkup(metric,locality)}</details>`;
  }

  function drinkingWaterQualityTownMarkup(metric,row) {
    const localities=row.localities||[],defs=metric.parameterDefinitions||[];
    if(!localities.length||!defs.length) return '<p>Dato non disponibile.</p>';
    return `<div class="water-quality-town"><details class="water-quality-town-disclosure"><summary><span><b>Consulta i valori per località</b><small>${html(number0.format(localities.length))} località GAIA · ${html(number0.format(defs.length))} parametri</small></span><i aria-hidden="true"></i></summary><div class="water-quality-town-disclosure-body"><div class="water-quality-town-controls"><label class="water-quality-selector"><span>Località GAIA</span><select data-water-quality-locality>${localities.map((locality,index)=>`<option value="${index}">${html(locality.name)}</option>`).join('')}</select></label><label class="water-quality-selector"><span>Parametro</span><select data-water-quality-parameter-town>${defs.map((def,index)=>`<option value="${index}">${html(def.name)}</option>`).join('')}</select></label></div><div data-water-quality-selected>${waterQualitySelectedMarkup(metric,row,0,0)}</div></div></details></div>`;
  }

  function remediationPartValue(source,key) {
    return Number(source?.parts?.find(item=>item.key===key)?.value)||0;
  }

  function remediationCompareMarkup(data,metricKey,view='active') {
    const metric=data.metrics[metricKey],selected=view==='closed'?'closed':'active';
    const rows=[...metric.rows].sort((a,b)=>remediationPartValue(b,selected)-remediationPartValue(a,selected));
    return `<div class="remediation-shell remediation-compare-shell"><div class="remediation-compare-controls"><label class="remediation-selector"><span>Ordina per</span><select data-remediation-compare-view><option value="active" ${selected==='active'?'selected':''}>Iter attivi</option><option value="closed" ${selected==='closed'?'selected':''}>Iter chiusi</option></select></label><p>Conteggi SISBON, non percentuali. Entrambi gli stati restano visibili.</p></div><div class="remediation-compare-list">${rows.map(row=>{const active=remediationPartValue(row,'active'),closed=remediationPartValue(row,'closed'),q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a class="remediation-compare-row" href="${route(`comuni/${row.slug}/?${q}`)}"><strong>${html(row.town)}</strong><span class="remediation-count-pair"><span class="remediation-count remediation-count-active ${selected==='active'?'selected':''}"><small>Iter attivi</small><b>${html(number0.format(active))}</b></span><span class="remediation-count remediation-count-closed ${selected==='closed'?'selected':''}"><small>Iter chiusi</small><b>${html(number0.format(closed))}</b></span></span><em>Apri il dettaglio →</em></a>`;}).join('')}</div><p class="composite-compare-note">Procedimenti univoci per codice regionale. Un procedimento non equivale automaticamente a un sito attualmente contaminato.</p></div>`;
  }

  function signedNumber(value,percent=false) {
    const numeric=Number(value)||0,abs=Math.abs(numeric),formatted=Number.isInteger(abs)?number0.format(abs):number1.format(abs);
    return `${numeric>0?'+':numeric<0?'−':''}${formatted}${percent?'%':''}`;
  }

  function remediationBenchmarkMarkup(metric,row,view='active') {
    const selected=view==='closed'?'closed':'active',local=remediationPartValue(row,selected),total=remediationPartValue(metric.aggregate,selected);
    const towns=Math.max(1,metric.rows?.length||7),mean=total/towns,difference=local-mean,deviation=mean?difference/mean*100:0;
    return `<section class="remediation-benchmark" data-remediation-benchmark><span class="overline">Benchmark comunale</span><h4>Rispetto alla media dei Comuni della Versilia</h4><div><article><span>${html(row.town)}</span><strong>${html(number0.format(local))}</strong></article><article><span>Media dei ${towns} Comuni</span><strong>${html(number1.format(mean))}</strong></article><article><span>Differenza</span><strong>${html(signedNumber(difference))}</strong></article><article><span>Scostamento</span><strong>${html(signedNumber(deviation,true))}</strong></article></div><p>Base del confronto: ${html(number0.format(total))} ${selected==='active'?'iter attivi':'iter chiusi'} ÷ ${towns} Comuni.</p></section>`;
  }

  function remediationTownMarkup(metric,row) {
    const active=remediationPartValue(row,'active'),closed=remediationPartValue(row,'closed');
    return `<div class="remediation-shell remediation-town"><div class="remediation-summary"><article class="active"><span>Iter attivi</span><strong>${html(number0.format(active))}</strong></article><article class="closed"><span>Iter chiusi</span><strong>${html(number0.format(closed))}</strong></article></div><label class="remediation-selector"><span>Mostra i procedimenti</span><select data-remediation-town-view><option value="active">Iter attivi</option><option value="closed">Iter chiusi</option></select></label><div data-remediation-benchmark-host>${remediationBenchmarkMarkup(metric,row,'active')}</div><div class="remediation-procedure-list">${(row.procedures||[]).map(item=>`<details data-remediation-status="${html(item.status)}" ${item.status==='closed'?'hidden':''}><summary><span><b>${html(item.id)}</b> · ${html(item.name)}</span><i aria-hidden="true"></i></summary><dl><div><dt>Codice regionale</dt><dd>${html(item.id)}</dd></div><div><dt>Denominazione sito</dt><dd>${html(item.name)}</dd></div><div><dt>Indirizzo / localizzazione</dt><dd>${html(item.address||'n.d.')}</dd></div><div><dt>Stato contaminazione</dt><dd>${html(item.contamination||'n.d.')}</dd></div><div><dt>Stato procedimento</dt><dd>${html(item.procedureState||'n.d.')}</dd></div></dl></details>`).join('')}</div></div>`;
  }

  function compositeCompareDefaults(metric) {
    if (metric.meta.compositeType === 'drinkingWaterQuality') return { choice:'0', scale:'value' };
    if (metric.meta.compositeType === 'remediationProceedings') return { choice:'active', scale:'value' };
    if (metric.meta.compositeType === 'sexBreakdown') return { choice:metric.meta.defaultSex || 'totale', scale:'value' };
    if (metric.meta.compositeType === 'demographicBreakdown') return { choice:`${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}`, scale:'value' };
    if (metric.meta.compositeType === 'stock') return { choice:'share', scale:'value' };
    if (metric.meta.compositeType === 'omi') return { choice:'sale', scale:'value' };
    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) return { choice:'part-0', scale:'value' };
    return { choice:'', scale:'value' };
  }

  function compositeCompareSelection(metric, row, choice, scale = 'value') {
    if (metric.meta.compositeType === 'sexBreakdown') {
      const part = (row.parts || []).find(item => item.key === choice) || row.parts?.[0] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, part };
    }
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const part = (row.parts || []).find(item => item.key === choice) || row.parts?.[0] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, part };
    }
    if (metric.meta.compositeType === 'stock') {
      const count = choice === 'count';
      return { value: count ? row.count : row.value, unit: count ? 'number' : 'percent' };
    }
    if (metric.meta.compositeType === 'omi') {
      const rent = choice === 'rent';
      return { value: rent ? row.rentMean : row.saleMean, unit: rent ? 'rentm2' : 'eurm2' };
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = row.parts?.[index] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, part, index };
    }
    if (metric.meta.compositeType === 'mobility') {
      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));
      const part = row.parts?.[index] || {};
      return { value: scale === 'count' ? part.count : part.value, unit: scale === 'count' ? 'number' : 'per1000', part, index };
    }
    return { value: row.value, unit: metric.meta.unit };
  }

  function compositeCompareAggregate(metric, choice, scale = 'value') {
    if (metric.meta.compositeType === 'remediationProceedings') {
      const key=choice==='closed'?'closed':'active';
      const part=(metric.aggregate?.parts||[]).find(item=>item.key===key)||{};
      return {value:part.value,unit:'number',label:`Versilia · ${part.label||'procedimenti'}`,note:metric.aggregate?.note};
    }
    if (metric.meta.compositeType === 'sexBreakdown') {
      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };
    }
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.ageLabel || ''} · ${part.genderLabel || ''}`, note:metric.aggregate?.note };
    }
    if (metric.meta.compositeType === 'stock') {
      const count = choice === 'count';
      const value = count ? metric.aggregate?.count : metric.aggregate?.value;
      return {
        value,
        unit: count ? 'number' : 'percent',
        label: count ? 'Versilia · residenti stranieri' : 'Versilia · quota residenti stranieri',
        note: count ? `${number0.format(metric.aggregate?.count || 0)} residenti di cittadinanza straniera nei sette comuni.` : metric.aggregate?.note
      };
    }
    if (metric.meta.compositeType === 'omi') {
      const rent = choice === 'rent';
      return {
        value: rent ? metric.aggregate?.rentMean : metric.aggregate?.saleMean,
        unit: rent ? 'rentm2' : 'eurm2',
        label: rent ? 'Versilia · affitto medio comunale' : 'Versilia · vendita media comunale',
        note: 'Media semplice dei sette valori comunali di riferimento.'
      };
    }
    if (metric.meta.compositeType === 'agricultureProfile') {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      const values = metric.rows.map(row => row.parts?.[index]?.value).filter(value => value !== null && value !== undefined && Number.isFinite(Number(value))).map(Number);
      return { value:values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null, unit:part.unit || metric.meta.unit, label:`Media comuni Versilia · ${part.label || metric.meta.label}`, note:`Media semplice dei ${values.length} comuni con dato disponibile.` };
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };
    }
    if (metric.meta.compositeType === 'mobility') {
      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));
      const part = metric.aggregate?.parts?.[index] || {};
      return {
        value: scale === 'count' ? part.count : part.value,
        unit: scale === 'count' ? 'number' : 'per1000',
        label: `Versilia · ${part.label || metric.meta.primaryLabel || 'mobilità residenziale'}`,
        note: scale === 'count' ? 'Somma dei flussi registrati nei sette comuni.' : metric.aggregate?.note
      };
    }
    return metric.aggregate;
  }

  function demographicAgeOptionsMarkup(metric, selectedKey) {
    const options = metric.meta.ageOptions || [];
    const groups = [];
    options.forEach(option => {
      const group = option.group || 'Fasce';
      if (!groups.includes(group)) groups.push(group);
    });
    return groups.map(group => `<optgroup label="${html(group)}">${options.filter(option => (option.group || 'Fasce') === group).map(option => `<option value="${html(option.key)}" ${option.key === selectedKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</optgroup>`).join('');
  }

  function demographicRateTooltipMarkup({boxX,boxY,guideX,guideY,label,part}) {
    const boxWidth = 228, boxHeight = 58;
    const targetY = boxY < guideY ? boxY + boxHeight : boxY;
    const value = part?.value;
    const numerator = Number(part?.numerator) || 0;
    const denominator = Number(part?.denominator) || 0;
    return `<g class="chart-tooltip" hidden><line class="chart-guide" x1="${guideX}" y1="${guideY}" x2="${guideX}" y2="${targetY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+15}">${html(label)}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+34}">${html(formatValue(value,'percent'))}</text><text class="chart-tooltip-meta" x="${boxX+12}" y="${boxY+50}">${html(number0.format(numerator))} / ${html(number0.format(denominator))}</text></g>`;
  }

  function demographicRatePyramidMarkup(metric, row) {
    const cells = new Map((row.parts || []).map(part => [part.key, part]));
    const ageMap = new Map((metric.meta.ageOptions || []).map(age => [age.key, age]));
    const keys = metric.meta.pyramidAgeKeys || [];
    const bands = keys.map(key => ageMap.get(key)).filter(Boolean).reverse();
    if (!bands.length) return '';
    const maxValue = 100;
    const center = 430, gap = 48, maxWidth = 300, rowHeight = 42, top = 78, bottom = 58;
    const height = top + bands.length * rowHeight + bottom;
    const tickXs = [center-gap-maxWidth, center-gap-maxWidth/2, center, center+gap+maxWidth/2, center+gap+maxWidth];
    const tickValues = [100, 50, 0, 50, 100];
    const axis = tickXs.map((x,index)=>`<g class="age-pyramid-axis"><line x1="${x}" y1="${top-18}" x2="${x}" y2="${height-bottom+10}"/><text x="${x}" y="${height-22}" text-anchor="middle">${tickValues[index]}%</text></g>`).join('');
    const rows = bands.map((age,index) => {
      const y = top + index * rowHeight;
      const men = cells.get(`${age.key}|men`) || {};
      const women = cells.get(`${age.key}|women`) || {};
      const menValue = Math.max(0, Math.min(100, Number(men.value) || 0));
      const womenValue = Math.max(0, Math.min(100, Number(women.value) || 0));
      const menWidth = menValue / maxValue * maxWidth;
      const womenWidth = womenValue / maxValue * maxWidth;
      const tooltipY = y < 112 ? y + 22 : y - 64;
      const menBoxX = Math.max(8, center-gap-menWidth-238);
      const womenBoxX = Math.min(624, center+gap+womenWidth+10);
      const menLabel = `${age.label} · Uomini`;
      const womenLabel = `${age.label} · Donne`;
      const menAria = `${menLabel}: ${formatValue(men.value,'percent')}; ${number0.format(Number(men.numerator)||0)} su ${number0.format(Number(men.denominator)||0)}`;
      const womenAria = `${womenLabel}: ${formatValue(women.value,'percent')}; ${number0.format(Number(women.numerator)||0)} su ${number0.format(Number(women.denominator)||0)}`;
      return `<g class="age-pyramid-row"><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(menAria)}"><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="22" rx="4" class="age-pyramid-men"></rect>${demographicRateTooltipMarkup({boxX:menBoxX,boxY:tooltipY,guideX:center-gap-menWidth,guideY:y+11,label:menLabel,part:men})}</g><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(womenAria)}"><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="22" rx="4" class="age-pyramid-women"></rect>${demographicRateTooltipMarkup({boxX:womenBoxX,boxY:tooltipY,guideX:center+gap+womenWidth,guideY:y+11,label:womenLabel,part:women})}</g><text x="${center}" y="${y+16}" text-anchor="middle">${html(age.label)}</text></g>`;
    }).join('');
    return `<div class="demographic-rate-pyramid" data-lavoro-istruzione-pyramid="1"><div class="demographic-rate-pyramid-head"><div><span class="overline">${row.town === 'Versilia' ? 'Totale Versilia · Età e sesso' : 'Età e sesso'}</span><h4>${row.town === 'Versilia' ? 'Piramide dei tassi · Versilia' : 'Piramide dei tassi'}</h4></div><small>2024 · scala 0–100%</small></div><div class="trend-chart age-pyramid-trend"><svg class="age-pyramid-chart demographic-rate-pyramid-chart" viewBox="0 0 860 ${height}" role="img" aria-label="${html(metric.meta.label)} per età e sesso a ${html(row.town)}"><text x="215" y="32" text-anchor="middle" class="age-pyramid-title">Uomini</text><text x="645" y="32" text-anchor="middle" class="age-pyramid-title">Donne</text><text x="430" y="54" text-anchor="middle" class="age-pyramid-unit">Percentuale nella fascia e nel sesso</text>${axis}<line x1="${center-gap}" y1="${top-24}" x2="${center-gap}" y2="${height-bottom+10}" class="age-pyramid-center"/><line x1="${center+gap}" y1="${top-24}" x2="${center+gap}" y2="${height-bottom+10}" class="age-pyramid-center"/>${rows}<text x="430" y="${height-4}" text-anchor="middle" class="age-pyramid-unit">percentuale</text></svg></div><p class="aggregate-note demographic-rate-pyramid-note">${row.town === 'Versilia' ? 'Il totale Versilia è calcolato sommando numeratori e denominatori dei sette Comuni, non mediando le percentuali. ' : ''}La piramide usa solo fasce non sovrapposte. Le letture aggregate 25–64 e complessiva restano disponibili nei selettori e nel dettaglio.</p></div>`;
  }

  function demographicRateTableMarkup(metric, row) {
    const ages = metric.meta.ageOptions || [];
    const genders = metric.meta.genderOptions || [];
    const cells = new Map((row.parts || []).map(part => [part.key,part]));
    return `<details class="detail-disclosure demographic-rate-detail"><summary><span>Valori e basi di calcolo</span><small>6 fasce · Totale, Uomini, Donne</small></summary><div class="demographic-rate-table-wrap"><table class="demographic-rate-table"><thead><tr><th>Età</th>${genders.map(g=>`<th>${html(g.label)}</th>`).join('')}</tr></thead><tbody>${ages.map(age=>`<tr class="${age.group === 'Aggregati' ? 'aggregate-age-row' : ''}"><th><span>${html(age.label)}</span><small>${html(age.group || '')}</small></th>${genders.map(g=>{const part=cells.get(`${age.key}|${g.key}`)||{};return `<td><strong>${html(formatValue(part.value,'percent'))}</strong><small>${html(number0.format(Number(part.numerator)||0))} / ${html(number0.format(Number(part.denominator)||0))}</small></td>`;}).join('')}</tr>`).join('')}</tbody></table></div><p class="demographic-rate-table-note">Il rapporto sotto ogni percentuale mostra numeratore e denominatore utilizzati. 25–64 è ricostruita sommando 25–49 e 50–64 sui conteggi prima del calcolo del tasso.</p></details>`;
  }

  function compositeCompareControls(metric, choice, scale = 'value') {
    if (metric.meta.compositeType === 'sexBreakdown') {
      const options = metric.meta.sexOptions || (metric.rows?.[0]?.parts || []).map(part => ({key:part.key,label:part.label}));
      return `<div class="compare-view-controls demographic-view-controls"><label class="compare-choice-select"><span>Sesso</span><select data-composite-component>${options.map(option=>`<option value="${html(option.key)}" ${option.key === choice ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>`;
    }
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const [ageKey,genderKey] = String(choice || '').split('|');
      return `<div class="compare-view-controls demographic-view-controls"><label class="compare-choice-select"><span>Fascia d’età</span><select data-demographic-age>${demographicAgeOptionsMarkup(metric,ageKey)}</select></label><label class="compare-choice-select"><span>Genere</span><select data-demographic-gender>${(metric.meta.genderOptions || []).map(option=>`<option value="${html(option.key)}" ${option.key === genderKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>`;
    }
    if (metric.meta.compositeType === 'stock') {
      return `<div class="compare-view-controls"><div><span class="compare-view-label">Lettura</span><div class="scale-switch compact" role="group" aria-label="Lettura residenti stranieri"><button type="button" data-composite-choice="share" class="${choice === 'share' ? 'active' : ''}">Quota %</button><button type="button" data-composite-choice="count" class="${choice === 'count' ? 'active' : ''}">Valore assoluto</button></div></div></div>`;
    }
    if (metric.meta.compositeType === 'omi') {
      return `<div class="compare-view-controls"><div><span class="compare-view-label">Quotazione</span><div class="scale-switch compact" role="group" aria-label="Lettura quotazioni immobiliari"><button type="button" data-composite-choice="sale" class="${choice === 'sale' ? 'active' : ''}">Vendita</button><button type="button" data-composite-choice="rent" class="${choice === 'rent' ? 'active' : ''}">Affitto</button></div></div></div>`;
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const labels = metric.rows?.[0]?.parts || [];
      return `<div class="compare-view-controls"><label class="compare-choice-select"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${labels.map((part,index)=>`<option value="part-${index}" ${choice === `part-${index}` ? 'selected' : ''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`;
    }
    if (metric.meta.compositeType === 'mobility') {
      const labels = metric.rows?.[0]?.parts || [];
      return `<div class="compare-view-controls mobility-view-controls"><label class="compare-choice-select"><span>Voce</span><select data-composite-component>${labels.map((part,index)=>`<option value="part-${index}" ${choice === `part-${index}` ? 'selected' : ''}>${html(part.label)}</option>`).join('')}</select></label><div><span class="compare-view-label">Unità</span><div class="scale-switch compact" role="group" aria-label="Scala della mobilità residenziale"><button type="button" data-composite-scale="rate" class="${scale === 'rate' ? 'active' : ''}">Ogni 1.000</button><button type="button" data-composite-scale="count" class="${scale === 'count' ? 'active' : ''}">Valore assoluto</button></div></div></div>`;
    }
    return '';
  }

  function compositeCompareBarRows(data, metricKey, choice, scale = 'value') {
    const metric = data.metrics[metricKey];
    const rows = metric.rows.map(row => {
      const selected = compositeCompareSelection(metric,row,choice,scale);
      return { ...row, displayValue:selected.value, displayUnit:selected.unit };
    }).sort((a,b)=>{const av=a.displayValue===null||a.displayValue===undefined?NaN:Number(a.displayValue),bv=b.displayValue===null||b.displayValue===undefined?NaN:Number(b.displayValue);return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);});
    const max = Math.max(...rows.map(r => Math.abs(Number(r.displayValue) || 0)), 0.0001);
    return rows.map((row,index) => {
      const query = new URLSearchParams({ tema:metric.meta.theme, indicatore:metricKey });
      const rowSlug=row.slug || normalize(row.town).replaceAll(' ','-');
      const href=route(`comuni/${rowSlug}/?${query}`);
      const formatted=formatMetricRowValue(row,row.displayValue,row.displayUnit);
      return `<a href="${href}" class="bar-row" aria-label="${html(row.town)}: ${html(formatted)}"><span class="bar-rank">${row.displayValue === null || row.displayValue === undefined ? '—' : index+1}</span><span class="bar-town">${html(row.town)}</span><span class="bar-track"><span class="bar-fill" style="width:${row.displayValue === null || row.displayValue === undefined ? 0 : Math.max(1.5,Math.abs(Number(row.displayValue)||0)/max*100)}%"></span><span class="bar-hover-label">${html(row.town)} · ${html(formatted)}</span></span><strong>${html(formatted)}</strong></a>`;
    }).join('');
  }

  function compositeCompareMarkup(data, metricKey, view={}) {
    const metric = data.metrics[metricKey];
    const rows = metricRows(data, metricKey);
    if (metric.meta.compositeType === 'drinkingWaterQuality') return drinkingWaterQualityCompareMarkup(data,metricKey,view.choice);
    if (metric.meta.compositeType === 'remediationProceedings') return remediationCompareMarkup(data,metricKey,view.choice);
    if (metric.meta.compositeType === 'stock') {
      return `<div class="composite-stock-list">${rows.map(row=>{const query=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a class="composite-stock-row" href="${route(`comuni/${row.slug}/?${query}`)}"><strong>${html(row.town)}</strong><span><b>${html(formatValue(row.value,'percent'))}</b><small>quota residenti</small></span><span><b>${html(formatValue(row.count,'number'))}</b><small>residenti stranieri</small></span></a>`;}).join('')}</div>`;
    }
    if (metric.meta.compositeType === 'omi') {
      return `<div class="omi-compare-list">${rows.map(row => {
        const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
        return `<article class="omi-compare-card"><div class="omi-compare-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(number0.format((row.zones || []).length))} zone OMI</span></div><div class="omi-compare-values"><div><span>Vendita · media comunale</span><strong>${html(formatValue(row.saleMean,'eurm2'))}</strong></div><div><span>Affitto · media comunale</span><strong>${html(formatValue(row.rentMean,'rentm2'))}</strong></div></div><details class="omi-zone-disclosure"><summary>Espandi le zone OMI <b>+</b></summary>${omiZoneTableMarkup(row,true)}</details></article>`;
      }).join('')}</div>`;
    }
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const defaults = compositeCompareDefaults(metric);
      return `<div class="comparison-bars">${compositeCompareBarRows(data,metricKey,defaults.choice,defaults.scale)}</div>`;
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const defaults = compositeCompareDefaults(metric);
      return `<div class="comparison-bars">${compositeCompareBarRows(data,metricKey,defaults.choice,defaults.scale)}</div>`;
    }
    if (metric.meta.compositeType === 'mobility') {
      const headParts = metric.rows?.[0]?.parts || [];
      return `<div class="composite-mobility-table" role="table" aria-label="${html(metric.meta.label)}">
        <div class="composite-mobility-head" role="row"><span>Comune</span>${headParts.map(part=>`<span>${html(part.label)}</span>`).join('')}</div>
        ${rows.map(row => {
          const parts = row.parts || [];
          const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
          return `<a class="composite-mobility-row" role="row" href="${route(`comuni/${row.slug}/?${query}`)}">
            <strong>${html(row.town)}</strong>${parts.map((part, index) => `<span class="${index === 2 ? 'balance' : ''}">${html(formatValue(part.value, 'per1000'))}<small>${html(number0.format(part.count))} persone</small></span>`).join('')}
          </a>`;
        }).join('')}</div>`;
    }
    const versiliaPyramid = metric.meta.key === 'ageDistribution' && metric.aggregate?.ageSexPyramid
      ? agePyramidMarkup(metric,{...metric.aggregate,town:'Versilia'})
      : '';
    const incomeBandDetail = metric.meta.key === 'incomeDistribution' && rows.some(row => row.detailParts?.length)
      ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div>${rows.map(row => `<section class="income-band-town-detail"><h4>${html(row.town)}</h4><div class="composite-town-detail">${(row.detailParts || []).map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></section>`).join('')}</div></details>`
      : '';
    return `${compositePartLegend(metric)}<div class="composite-distribution-list">${rows.map(row => {
      const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
      const parts = row.parts || [];
      const summary = compositeSummary(metric, row);
      return `<div class="composite-distribution-row">
        <div class="composite-row-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(summary.label)} <b>${html(summary.formatted)}</b></span></div>
        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;
    }).join('')}</div>${incomeBandDetail}${versiliaPyramid}`;
  }

  function compositeTownMarkup(metric, row) {
    if (metric.meta.compositeType === 'drinkingWaterQuality') return drinkingWaterQualityTownMarkup(metric,row);
    if (metric.meta.compositeType === 'remediationProceedings') return remediationTownMarkup(metric,row);
    const parts = row.parts || [];
    if (metric.meta.compositeType === 'sexBreakdown') return '';
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const pyramid = demographicRatePyramidMarkup(metric,row);
      const detail = demographicRateTableMarkup(metric,row);
      const history = row.series?.values?.length ? `<details class="detail-disclosure demographic-history"><summary><span>Storico della lettura base</span><small>${html(metric.meta.defaultAge === '25-64' ? '25–64 anni · Totale' : 'lettura base')}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · lettura base`)}</div></details>` : '';
      return pyramid + detail + history;
    }
    if (metric.meta.compositeType === 'stock') {
      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>${foreignOriginsMarkup(metric,row,'town')}`;
    }
    if (metric.meta.compositeType === 'omi') {
      return `<div class="omi-town-summary"><article><span>Vendita · media comunale</span><strong>${html(formatValue(row.saleMean,'eurm2'))}</strong><small>Media semplice delle ${html(number0.format((row.zones || []).length))} zone visualizzate</small></article><article><span>Affitto · media comunale</span><strong>${html(formatValue(row.rentMean,'rentm2'))}</strong><small>Media semplice delle ${html(number0.format((row.zones || []).length))} zone visualizzate</small></article></div><details class="detail-disclosure omi-town-zone-disclosure"><summary><span>Dettaglio per zona OMI</span><small>${html(metric.meta.year)} · abitazioni civili / stato normale</small></summary><div class="omi-town-zone-body">${omiZoneTableMarkup(row)}</div></details>`;
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const incomeSources = metric.meta.key === 'incomeSourceProfile';
      const totalCount = parts.reduce((sum, part) => sum + (Number(part.count) || 0), 0);
      const showStaffCounts = metric.meta.key === 'municipalStaffAgeStructure';
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${row.notApplicable ? 'Comune non costiero' : (incomeSources ? (part.count === null || part.count === undefined ? 'n.d. · dichiaranti con questa fonte' : `${html(number0.format(part.count))} dichiaranti con questa fonte`) : (showStaffCounts && part.count !== undefined ? `${html(number0.format(part.count))} dipendenti su ${html(number0.format(totalCount))} · ${html(metric.meta.year)}` : html(metric.meta.year)))}</small></article>`).join('')}</div>`;
    }
    if (metric.meta.compositeType === 'mobility') {
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===2?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,'per1000'))}</strong><small>${html(number0.format(part.count))} persone · ${html(metric.meta.year)}</small></article>`).join('')}</div>`;
    }
    const countLabel = metric.meta.key === 'incomeDistribution' ? 'dichiaranti' : 'residenti';
    const detailParts = metric.meta.key === 'incomeDistribution' ? (row.detailParts || []) : [];
    const detailDisclosure = detailParts.length ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div class="composite-town-detail">${detailParts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></details>` : '';
    const agePyramidDisclosure = agePyramidMarkup(metric,row);
    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b>${part.count === null || part.count === undefined ? '' : `<small>${html(number0.format(part.count))} ${html(countLabel)}</small>`}</div>`).join('')}</div>${agePyramidDisclosure}</div>${detailDisclosure}`;
  }

  function compositeSelectionOptions(metric, row) {
    if (metric.meta.compositeType === 'sexBreakdown') return (row.parts || []).map(part=>({ key:part.key, label:part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatValue(part.value,part.unit || metric.meta.unit), part }));
    if (metric.meta.compositeType === 'demographicBreakdown') return (row.parts || []).map(part=>({ key:part.key, label:part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatValue(part.value,part.unit || metric.meta.unit), part }));
    if (metric.meta.compositeType === 'stock') return [
      { key:'share', label:'Quota di residenti stranieri', value:row.value, unit:'percent', formatted:formatValue(row.value,'percent') },
      { key:'count', label:'Residenti di cittadinanza straniera', value:row.count, unit:'number', formatted:formatValue(row.count,'number') }
    ];
    if (metric.meta.compositeType === 'omi') return [
      { key:'sale', label:'Vendita media comunale', value:row.saleMean, unit:'eurm2', formatted:formatValue(row.saleMean,'eurm2') },
      { key:'rent', label:'Affitto medio comunale', value:row.rentMean, unit:'rentm2', formatted:formatValue(row.rentMean,'rentm2') }
    ];
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) return (row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatMetricRowValue(row,part.value,part.unit || metric.meta.unit), index }));
    if (metric.meta.compositeType !== 'distribution') return [];
    const summary = compositeSummary(metric,row);
    return [{ key:'summary', label:summary.label, value:summary.value, unit:summary.unit, formatted:summary.formatted }, ...(row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:'percent', formatted:`${number1.format(part.value)}%`, index }))];
  }

  function compositeSelectionAggregate(metric, choice) {
    if (metric.meta.compositeType === 'sexBreakdown') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }
    if (metric.meta.compositeType === 'demographicBreakdown') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.ageLabel || ''} · ${part.genderLabel || ''}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }
    if (metric.meta.compositeType === 'stock') {
      const count = choice === 'count';
      const value = count ? metric.aggregate?.count : metric.aggregate?.value;
      const unit = count ? 'number' : 'percent';
      return { label: count ? 'Versilia · residenti stranieri' : 'Versilia · quota residenti stranieri', value, unit, formatted:formatValue(value,unit) };
    }
    if (metric.meta.compositeType === 'omi') {
      const rent = choice === 'rent';
      const value = rent ? metric.aggregate?.rentMean : metric.aggregate?.saleMean;
      const unit = rent ? 'rentm2' : 'eurm2';
      return { label: rent ? 'Versilia · affitto medio comunale' : 'Versilia · vendita media comunale', value, unit, formatted:formatValue(value,unit) };
    }
    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      const unit = part.unit || metric.meta.unit;
      return { label:`Versilia · ${part.label || metric.meta.label}`, value:part.value, unit, formatted:formatValue(part.value,unit) };
    }
    if (choice === 'summary') return compositeAggregateSummary(metric);
    const index = Number(String(choice).replace('part-',''));
    const part = metric.aggregate?.parts?.[index];
    return { label:`Versilia · ${part?.label || ''}`, value:part?.value, unit:'percent', formatted:part?.value === undefined ? 'n.d.' : `${number1.format(part.value)}%` };
  }

  function compositeSelectionRank(metric, row, choice) {
    const values = metric.rows.map(r => {
      if (metric.meta.compositeType === 'sexBreakdown') { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:Number(part?.value)}; }
      if (metric.meta.compositeType === 'demographicBreakdown') { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:Number(part?.value)}; }
      if (metric.meta.compositeType === 'stock') return { code:r.code, value:Number(choice === 'count' ? r.count : r.value) };
      if (metric.meta.compositeType === 'omi') return { code:r.code, value:Number(choice === 'rent' ? r.rentMean : r.saleMean) };
      if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) { const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); const raw=r.parts?.[index]?.value; return { code:r.code, value:raw===null||raw===undefined?NaN:Number(raw) }; }
      if (choice === 'summary') return { code:r.code, value:Number(r.summaryValue) };
      const index = Number(String(choice).replace('part-',''));
      return { code:r.code, value:Number(r.parts?.[index]?.value) };
    }).filter(x => Number.isFinite(x.value)).sort((a,b)=>b.value-a.value);
    return values.findIndex(x=>x.code===row.code)+1;
  }

  function compositeDeltaText(local, aggregate, unit) {
    if (!Number.isFinite(Number(local)) || !Number.isFinite(Number(aggregate))) return { headline:'n.d.', direction:'confronto non disponibile' };
    const diff=Number(local)-Number(aggregate);
    if (unit==='percent') {
      if (Math.abs(diff)<0.05) return { headline:'0,0%', direction:'in linea con la Versilia' };
      return { headline:`${diff>0?'+':'−'}${number1.format(Math.abs(diff))}%`, direction:diff>0?'sopra la Versilia':'sotto la Versilia' };
    }
    if (unit==='years') {
      if (Math.abs(diff)<0.05) return { headline:'0,0 anni', direction:'in linea con la Versilia' };
      return { headline:`${diff>0?'+':'−'}${number1.format(Math.abs(diff))} anni`, direction:diff>0?'sopra la media Versilia':'sotto la media Versilia' };
    }
    if (unit==='currency') {
      if (Math.abs(diff)<0.5) return { headline:'0 €', direction:'in linea con la Versilia' };
      return { headline:`${diff>0?'+':'−'}${currency0.format(Math.abs(diff))}`, direction:diff>0?'sopra la media Versilia':'sotto la media Versilia' };
    }
    return { headline:formatValue(diff,unit), direction:diff>0?'sopra la Versilia':diff<0?'sotto la Versilia':'in linea con la Versilia' };
  }

  function updateAgricultureProfileTownPosition(metric,row,choice,position) {
    if (!position || metric?.meta?.compositeType !== 'agricultureProfile') return;
    const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);
    const localPart=row?.parts?.[index] || {};
    const totalPart=metric.aggregate?.parts?.[index] || {};
    const localRaw=localPart.value;
    const totalRaw=totalPart.value;
    const local=localRaw === null || localRaw === undefined ? NaN : Number(localRaw);
    const total=totalRaw === null || totalRaw === undefined ? NaN : Number(totalRaw);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local / total * 100 : null;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(overline) overline.textContent='Quota sul totale Versilia';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>dato comunale non disponibile</small>`
      : `${html(number2.format(share))}%<small>del totale della coltura</small>`;
    if(noteEl) noteEl.textContent=`Quota del Comune sul totale Versilia della coltura, calcolato sui Comuni con dato disponibile (${totalPart.coverage || 'copertura dichiarata'}). I valori mancanti restano n.d.`;
    if(aggLabel) aggLabel.textContent=`Versilia · ${totalPart.label || metric.meta.label}`;
    if(aggValue) aggValue.textContent=formatValue(totalPart.value,totalPart.unit || metric.meta.unit);
  }

  function updateMaritimeTownPosition(metric,row,choice,position) {
    if (!position || !['maritimeConcessions','maritimeConcessionFeesDue'].includes(metric?.meta?.key) || row?.notApplicable) return;
    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const local=Number(selected?.value);
    const total=Number(agg?.value);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : null;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(overline) overline.textContent=metric.meta.comparisonOverline || 'Peso sulla Versilia costiera';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>quota non disponibile</small>`
      : `${html(number1.format(share))}%<small>del totale dei quattro Comuni costieri</small>`;
    if(noteEl) noteEl.textContent=metric.meta.comparisonNote || 'Quota del valore comunale sul totale dei quattro Comuni costieri.';
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }

  function updateExtractiveTownPosition(metric,row,choice,position) {
    if (!position || !['extractiveSites','extractivePlanning'].includes(metric?.meta?.key)) return;
    const options=compositeSelectionOptions(metric,row);
    const selected=options.find(option=>option.key===choice) || options[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const selectedPart=selected?.index === undefined ? null : row.parts?.[selected.index];
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');

    if (metric.meta.key === 'extractivePlanning' && selectedPart?.key?.endsWith('_pct')) {
      if(overline) overline.textContent='Quota territoriale Versilia';
      if(deltaEl) deltaEl.innerHTML=`${html(agg.formatted)}<small>sul territorio complessivo dei sette Comuni</small>`;
      if(noteEl) noteEl.textContent='Confronto diretto tra due quote territoriali: la percentuale comunale non viene divisa per la percentuale Versilia.';
      if(aggLabel) aggLabel.textContent=`${row.town} · quota comunale`;
      if(aggValue) aggValue.textContent=selected.formatted;
      return;
    }

    const localRaw=selected?.value;
    const totalRaw=agg?.value;
    const local=localRaw === null || localRaw === undefined ? NaN : Number(localRaw);
    const total=totalRaw === null || totalRaw === undefined ? NaN : Number(totalRaw);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : null;
    if(overline) overline.textContent=metric.meta.comparisonOverline || 'Peso sulla Versilia';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>${total === 0 ? 'totale Versilia pari a zero' : 'quota non disponibile'}</small>`
      : `${html(number2.format(share))}%<small>del totale della lettura selezionata</small>`;
    if(noteEl) noteEl.textContent=metric.meta.comparisonNote || 'Quota del valore comunale sul totale dei sette Comuni per la lettura selezionata.';
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }

  function updateFiscalRecoveryTownPosition(metric,row,choice,position) {
    if (!position || metric?.meta?.key !== 'fiscalRecoveryActivity') return;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    const apply=(heading,headline,direction,note,label,value)=>{
      if(overline) overline.textContent=heading;
      if(deltaEl) deltaEl.innerHTML=`${html(headline)}<small>${html(direction)}</small>`;
      if(noteEl) noteEl.textContent=note;
      if(aggLabel) aggLabel.textContent=label;
      if(aggValue) aggValue.textContent=value;
    };

    if(choice === 'part-1') {
      const local=Number(row.parts?.[1]?.value);
      const total=Number(metric.aggregate?.parts?.[1]?.value);
      const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : 0;
      apply(
        'Peso sul totale Versilia',
        `${number1.format(share)}%`,
        'del recupero tributario complessivo',
        'Quota degli incassi da verifica e controllo del Comune sul totale registrato nei sette Comuni della Versilia.',
        'Versilia · recupero totale',
        formatValue(total,'currency')
      );
      return;
    }

    if(choice === 'part-2') {
      const local=Number(row.parts?.[2]?.value) || 0;
      const total=Number(metric.aggregate?.parts?.[2]?.value) || 0;
      const beneficiaries=metric.rows
        .map(item=>({ town:item.town, value:Number(item.parts?.[2]?.value) || 0 }))
        .filter(item=>item.value > 0)
        .sort((a,b)=>b.value-a.value);
      const share=total > 0 ? local/total*100 : 0;
      const rank=beneficiaries.findIndex(item=>item.town===row.town)+1;
      const note=local > 0
        ? `${row.town} è ${rank}° per importo attribuito tra i ${beneficiaries.length} Comuni versiliesi beneficiari. Il dato non misura l’efficacia complessiva dell’attività fiscale comunale.`
        : `${row.town} non compare tra i beneficiari del prospetto DAIT 2025. L’assenza non implica assenza di controlli o di segnalazioni comunali.`;
      apply(
        'Contributo attribuito in Versilia',
        `${number1.format(share)}%`,
        local > 0 ? 'del contributo DAIT attribuito in Versilia' : 'nessun contributo attribuito',
        note,
        `Versilia · ${beneficiaries.length} Comuni beneficiari`,
        formatValue(total,'currency')
      );
      return;
    }

    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const delta=compositeDeltaText(selected.value,agg.value,selected.unit);
    apply(
      'Rispetto alla Versilia',
      delta.headline,
      delta.direction,
      'Il confronto con la Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.',
      agg.label,
      agg.formatted
    );
  }

  function tplCompareDetailMarkup(data) {
    const metric = data.metrics.scheduledTplTripsPer1000;
    if (!metric) return '';
    const rows = metric.rows
      .map(row => ({ row, tpl:data.details?.[row.code]?.mobility?.tpl }))
      .filter(item => item.tpl);
    if (rows.length !== 7) return '';
    return `<details class="detail-disclosure tpl-compare-detail"><summary><span>Dettaglio del servizio TPL programmato</span><small>Corse, modalità, accessi, route e orari · 7/7 Comuni</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th><th>Corse</th><th>Bus</th><th>Ferrovia</th><th>Punti GTFS</th><th>Route</th><th>Finestra di servizio</th></tr></thead><tbody>${rows.map(({row,tpl})=>`<tr><th>${html(row.town)}</th><td>${html(number0.format(tpl.trips))}</td><td>${html(number0.format(tpl.busTrips))}</td><td>${html(number0.format(tpl.railTrips))}</td><td>${html(number0.format(tpl.activeAccessPoints))}</td><td>${html(number0.format(tpl.routes))}</td><td class="tpl-service-cell"><span class="tpl-service-range">${html(tpl.firstDeparture)}–${html(tpl.lastDeparture)}</span><small class="tpl-service-span">${html(number2.format(tpl.serviceSpanHours))} h</small></td></tr>`).join('')}</tbody></table></div><p class="aggregate-note tpl-detail-note">Un punto GTFS è una coppia (feed, stop_id) attiva: direzioni, banchine o feed diversi possono descrivere separatamente luoghi fisicamente vicini. Le route sono un dettaglio descrittivo. Gli orari “+1 giorno” appartengono alla stessa giornata operativa GTFS.</p></details>`;
  }

  function coastDetailMarkup(metric, rows, title) {
    if (metric?.meta?.detailGroup !== 'coast') return '';
    const applicable = (rows || []).filter(row => !row.notApplicable && row.coastDetail);
    if (!applicable.length) {
      return `<aside class="benchmark-unavailable coast-not-applicable"><span class="overline">Applicabilità territoriale</span><h3>Indicatore non applicabile</h3><p>Questo Comune non ha costa marina; il valore resta n.a. e non entra nei calcoli Versilia.</p></aside>`;
    }
    const key = metric.meta.key;
    let head = '';
    let body = '';
    let note = '';
    if (key === 'bathingWaterQuality') {
      head = '<tr><th>Comune</th><th>Aree ecc.</th><th>Buone</th><th>Suff.</th><th>Scarse</th><th>Totale</th><th>km ecc.</th><th>km buoni</th><th>km suff.</th><th>km scarsi</th><th>km totali</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(number0.format(d.areas.excellent))}</td><td>${html(number0.format(d.areas.good))}</td><td>${html(number0.format(d.areas.sufficient))}</td><td>${html(number0.format(d.areas.poor))}</td><td>${html(number0.format(d.areas.total))}</td><td>${html(number2.format(d.kilometres.excellent))}</td><td>${html(number2.format(d.kilometres.good))}</td><td>${html(number2.format(d.kilometres.sufficient))}</td><td>${html(number2.format(d.kilometres.poor))}</td><td>${html(number2.format(d.kilometres.total))}</td></tr>`; }).join('');
      note = 'La classificazione 2025 usa i dati 2022–2025. Aree e chilometri sono universi distinti nella stessa card.';
    } else if (key === 'bathingNonCompliantSamples') {
      head = '<tr><th>Comune</th><th>Tutti · NC/totale</th><th>Routinari · NC/totale</th><th>Supplettivi · NC/totale</th><th>Aree con almeno un routinario NC</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(`${d.all.nonCompliant}/${d.all.total}`)}</td><td>${html(`${d.routine.nonCompliant}/${d.routine.total}`)}</td><td>${html(`${d.supplementary.nonCompliant}/${d.supplementary.total}`)}</td><td>${html(`${d.routine.affectedAreas}/${d.routine.areas}`)}</td></tr>`; }).join('');
      note = 'NC significa campione non conforme, non episodio. Deduplica: Codice area + Data + Rout./Suppl.';
    } else if (key === 'blueFlagBeaches') {
      head = '<tr><th>Comune</th><th>Località 2026</th><th>Numero</th></tr>';
      body = applicable.map(row => `<tr><th>${html(row.town)}</th><td>${html(row.coastDetail.localities2026.join('; '))}</td><td>${html(number0.format(row.value))}</td></tr>`).join('');
      note = 'Le denominazioni unite da una barra restano una sola località. Il riconoscimento non misura soltanto la qualità microbiologica.';
    } else if (key === 'shorelineDynamics') {
      head = '<tr><th>Comune</th><th>Analizzata km</th><th>Erosione km</th><th>Stabile km</th><th>Avanzamento km</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(number3.format(d.analysedKm))}</td><td>${html(number3.format(d.erosionKm))}</td><td>${html(number3.format(d.stableKm))}</td><td>${html(number3.format(d.advanceKm))}</td></tr>`; }).join('');
      note = 'Erosione e avanzamento indicano variazioni superiori a 5 m nel periodo 2006–2020; stabile indica variazioni entro ±5 m.';
    } else if (key === 'rigidDefenceProtectedCoast') {
      head = '<tr><th>Comune</th><th>Costa km</th><th>Protetta km</th><th>Quota</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(number3.format(d.coastKm))}</td><td>${html(number3.format(d.protectedKm))}</td><td>${html(formatValue(row.value,'percent'))}</td></tr>`; }).join('');
      note = 'Sono considerate le opere rigide della metodologia ISPRA 2020; i ripascimenti artificiali sono esclusi.';
    }
    else if (key === 'maritimeConcessions') {
      head = '<tr><th>Comune</th><th>Totali</th><th>Turistico-ricreative</th><th>Quota TR</th><th>Licenze</th><th>Atti formali</th><th>Consegne</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail, types=Object.fromEntries((d.titleTypeBreakdown||[]).map(x=>[x.label,x.count])); return `<tr><th>${html(row.town)}</th><td>${html(number0.format(d.totalConcessions))}</td><td>${html(number0.format(d.touristRecreationalConcessions))}</td><td>${html(number1.format(d.touristRecreationalShare))}%</td><td>${html(number0.format(types['Licenza']||0))}</td><td>${html(number0.format(types['Atto Formale']||0))}</td><td>${html(number0.format(types['Consegna']||0))}</td></tr>`; }).join('');
      note = 'Il dettaglio usa i titoli unici idconc. Una concessione classificata dal SID come stabilimento balneare non viene trasformata nel conteggio degli stabilimenti.';
    } else if (key === 'maritimeConcessionFeesDue') {
      head = '<tr><th>Comune</th><th>Dovuto totale</th><th>Dovuto TR</th><th>Media totale</th><th>Mediana totale</th><th>Canone minimo</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(formatValue(d.canoneDovutoEur,'currency2'))}</td><td>${html(formatValue(d.touristRecreationalCanoneDovutoEur,'currency2'))}</td><td>${html(formatValue(d.meanCanoneEur,'currency2'))}</td><td>${html(formatValue(d.medianCanoneEur,'currency2'))}</td><td>${html(number0.format(d.minimumCanoneCount))} · ${html(number1.format(d.minimumCanoneShare))}%</td></tr>`; }).join('');
      note = 'Sono canoni dovuti registrati dal SID, non incassi o gettito comunale. Media e mediana sono calcolate sul totale dei titoli del Comune.';
    }
    if (!head || !body) return '';
    return `<details class="detail-disclosure coast-detail" open><summary><span>${html(title)}</span><small>Valori elementari e denominatori</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead>${head}</thead><tbody>${body}</tbody></table></div><p class="aggregate-note">${html(note)}</p></details>`;
  }

  function extractiveDetailMarkup(metric, rows, title) {
    if (metric?.meta?.detailGroup !== 'extractive') return '';
    const key=metric.meta.key;
    const list=(rows||[]);
    if (key === 'extractiveSites') {
      if (list.length === 1) {
        const row=list[0], d=row.extractiveDetail || {}, records=d.records || [];
        const summary=`<div class="composite-town-detail"><div><span>Totale RTCave</span><b>${html(number0.format(d.recordCount||0))}</b><small>record distinti per codice_rt</small></div><div><span>Stati</span><b>${html((d.statusBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>valori originali RTCave</small></div><div><span>Tipologie</span><b>${html((d.typeBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>classificazione RTCave</small></div><div><span>Produzione</span><b>${html((d.productionBreakdown||[]).map(x=>`${x.label} ${x.count}`).join(' · ') || 'nessun sito')}</b><small>macro-classe produttiva</small></div></div>`;
        const table=records.length ? `<div class="indicator-table-scroll extractive-records-scroll"><table class="indicator-values-table"><thead><tr><th>Codice RT</th><th>Cava</th><th>Località</th><th>Stato</th><th>Tipologia</th><th>Produzione</th><th>Comprensorio</th><th>Giacimento</th><th>Coordinate</th></tr></thead><tbody>${records.map(r=>`<tr><td>${html(r.codice_rt||'n.d.')}</td><th>${html(r.nome_cava||'n.d.')}</th><td>${html(r.localita||'n.d.')}</td><td>${html(r.stato||'n.d.')}</td><td>${html(r.tipologia||'n.d.')}</td><td>${html(r.tipo_produzione||'n.d.')}</td><td>${html(r.nome_comprensorio||'n.d.')}</td><td>${html(r.nome_giacimento||'n.d.')}</td><td>${html(`${r.lat??'n.d.'}, ${r.lon??'n.d.'}`)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="aggregate-note">Nessun record RTCave nello snapshot.</p>';
        return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Anagrafica pubblica RTCave</small></summary>${summary}${table}<p class="aggregate-note">Chiusa, Inattiva e SED non sono sinonimi. La classe produttiva RTCave non viene reinterpretata come litologia.</p></details>`;
      }
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Stato, tipologia e classe produttiva</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th><th>Totale</th><th>Attivi</th><th>Inattivi</th><th>Sospesi</th><th>Scaduti</th><th>Chiusi</th><th>n.d.</th></tr></thead><tbody>${list.map(row=>{const p=Object.fromEntries((row.parts||[]).map(x=>[x.key,x.value]));return `<tr><th>${html(row.town)}</th><td>${html(number0.format(p.total||0))}</td><td>${html(number0.format(p.state_active||0))}</td><td>${html(number0.format(p.state_inactive||0))}</td><td>${html(number0.format(p.state_suspended||0))}</td><td>${html(number0.format(p.state_expired||0))}</td><td>${html(number0.format(p.state_closed||0))}</td><td>${html(number0.format(p.state_nd||0))}</td></tr>`}).join('')}</tbody></table></div><p class="aggregate-note">I dettagli comunali conservano tutti i campi pubblici dell’endpoint, compresi comprensorio, giacimento, coordinate e ID tecnici nello snapshot.</p></details>`;
    }
    if (key === 'extractiveProduction') {
      const applicable=list.filter(r=>r.productionDetail);
      if (!applicable.length) return `<aside class="benchmark-unavailable"><span class="overline">Disponibilità del dato</span><h3>Produzione comunale n.d.</h3><p>Il monitoraggio PRC non consente un raccordo comunale omogeneo per questo Comune; nessuno zero viene inferito.</p></aside>`;
      const years=applicable[0].productionDetail.years||[];
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>Volumi effettivamente estratti · m³</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th>${years.map(y=>`<th>${html(String(y))}</th>`).join('')}</tr></thead><tbody>${applicable.map(r=>`<tr><th>${html(r.town)}</th>${r.productionDetail.values.map(v=>`<td>${html(number0.format(v))}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="aggregate-note">Per Stazzema la serie conserva separatamente Bacino di Stazzema e Cardoso delle Apuane; l’OPS 2019–2038 resta un benchmark pianificatorio, non un volume autorizzato.</p></details>`;
    }
    if (key === 'extractivePlanning') {
      return `<details class="detail-disclosure extractive-detail" open><summary><span>${html(title)}</span><small>G, GP, ACC e patrimonio storico PRC</small></summary><div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Comune</th><th>G n.</th><th>G ha</th><th>G %</th><th>GP n.</th><th>GP ha</th><th>GP %</th><th>ACC n.</th><th>ACC ha</th><th>ACC %</th><th>MOS</th><th>pMOS</th><th>SED censiti</th></tr></thead><tbody>${list.map(row=>{const d=row.prcDetail||{};return `<tr><th>${html(row.town)}</th><td>${html(number0.format(d.g?.[0]||0))}</td><td>${html(number2.format(d.g?.[1]||0))}</td><td>${html(number3.format(d.g?.[2]||0))}%</td><td>${html(number0.format(d.gp?.[0]||0))}</td><td>${html(number2.format(d.gp?.[1]||0))}</td><td>${html(number3.format(d.gp?.[2]||0))}%</td><td>${html(number0.format(d.acc?.[0]||0))}</td><td>${html(number2.format(d.acc?.[1]||0))}</td><td>${html(number3.format(d.acc?.[2]||0))}%</td><td>${html(number0.format(d.mos||0))}</td><td>${html(number0.format(d.pmos||0))}</td><td>${html(number0.format(d.sed||0))}</td></tr>`}).join('')}</tbody></table></div><p class="aggregate-note">Giacimenti, Giacimenti Potenziali e ACC restano categorie distinte. I SED sono siti dismessi censiti dal PRC in una ricognizione non esaustiva.</p></details>`;
    }
    return '';
  }

  function extractiveCompareDetailMarkup(metric) {
    return extractiveDetailMarkup(metric, metric.rows, 'Dettaglio attività estrattive');
  }

  function extractiveTownDetailMarkup(metric,row) {
    return extractiveDetailMarkup(metric,[row],`Dettaglio · ${row.town}`);
  }

  function coastCompareDetailMarkup(metric) {
    return coastDetailMarkup(metric, metric.rows, 'Dettaglio dei quattro Comuni costieri');
  }

  function coastTownDetailMarkup(metric, row) {
    return coastDetailMarkup(metric, [row], `Dettaglio · ${row.town}`);
  }

  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {
    const metric = data.metrics[metricKey];
    const def = document.getElementById('compare-definition');
    const bars = document.getElementById('compare-bars');
    const benchmark = document.getElementById('compare-benchmark');
    const tools = document.getElementById('compare-tools');
    const demographicPyramid = document.getElementById('compare-demographic-pyramid');
    const hasNormalized = metric.rows.some(r => r.normalized);
    const compositeType = metric.meta.compositeType || '';
    const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','demographicBreakdown','sexBreakdown'].includes(compositeType);
    const specialComposite = ['drinkingWaterQuality','remediationProceedings'].includes(compositeType);
    const view = requestedView || compositeCompareDefaults(metric);
    const selectedAggregate = (selectableComposite || compositeType === 'remediationProceedings') ? compositeCompareAggregate(metric,view.choice,view.scale) : null;
    const aggregate = selectedAggregate || (normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate);
    const unit = selectedAggregate?.unit || (normalized && metric.meta.normalized ? metric.meta.normalized.unit : metric.meta.unit);
    const distributionSummary = compositeType === 'distribution' ? compositeAggregateSummary(metric) : null;
    const controls = selectableComposite ? '' : (hasNormalized ? `<div class="scale-switch" role="group" aria-label="Scala"><button type="button" data-scale="raw" class="${normalized ? '' : 'active'}">Valore assoluto</button><button type="button" data-scale="normalized" class="${normalized ? 'active' : ''}">Rapportato</button></div>` : '');
    const chartControls = selectableComposite ? compositeCompareControls(metric,view.choice,view.scale) : '';
    const definitionControls = '';
    const chartScaleControls = controls;
    const summaryLabel = distributionSummary ? distributionSummary.label : aggregate.label;
    const summaryValue = distributionSummary ? distributionSummary.formatted : formatValue(aggregate.value,unit);
    def.innerHTML = compositeType === 'drinkingWaterQuality'
      ? `<div class="indicator-definition water-quality-definition"><h2>${html(metric.meta.label)}</h2><p>${html(metric.meta.description)}</p><dl><div><dt>Periodo</dt><dd>${html(metric.meta.year)}</dd></div><div><dt>Fonte</dt><dd><a href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">${html(metric.meta.source)} ↗</a></dd></div><div><dt>Copertura</dt><dd>${html(number0.format(metric.aggregate?.value||0))} località GAIA · 7 Comuni</dd></div><div><dt>Parametri</dt><dd>${html(number0.format(metric.parameterDefinitions?.length||0))} per località</dd></div></dl><small class="aggregate-note">Nessuna media comunale delle concentrazioni e nessun indice sintetico.</small></div>`
      : `${definitionControls}<div class="indicator-definition"><h2>${html(normalized && metric.meta.normalized ? metric.meta.normalized.label : metric.meta.label)}</h2><p>${html(normalized && metric.meta.normalized ? metric.meta.normalized.description : metric.meta.description)}</p><dl><div><dt>Anno</dt><dd>${html(metric.meta.year)}</dd></div><div><dt>Fonte</dt><dd><a href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">${html(metric.meta.source)} ↗</a></dd></div><div><dt>${html(summaryLabel)}</dt><dd>${html(summaryValue)}</dd></div></dl><small class="aggregate-note">${html(aggregate.note || metric.aggregate?.note || '')}</small></div>`;

    if (selectableComposite) {
      const note = compositeType === 'omi' ? `<p class="composite-compare-note"><strong>Dettaglio OMI:</strong> il dettaglio delle singole sotto-aree è disponibile nelle schede dei comuni. Clicca una riga per aprire il territorio.</p>` : (compositeType === 'mobility' ? `<p class="composite-compare-note">Scegli la voce e l’unità direttamente dal grafico. “Ogni 1.000” rende più omogeneo il confronto tra comuni di dimensioni diverse.</p>` : '');
      const stockDetail = compositeType === 'stock' ? foreignOriginsCompareMarkup(metric) : '';
      bars.innerHTML = `<div class="topic-bars selectable-topic-bars"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${chartControls}</div><div class="comparison-bars" data-composite-choice="${html(view.choice)}" data-composite-scale="${html(view.scale)}">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${note}${stockDetail}</div>`;
    } else {
      bars.innerHTML = compositeType ? `<div class="topic-bars composite-topic-bars">${compositeCompareMarkup(data,metricKey,view)}</div>` : `<div class="topic-bars">${chartScaleControls ? `<div class="compare-chart-toolbar scale-toolbar">${chartScaleControls}</div>` : ''}<div class="comparison-bars">${barRows(data,metricKey,{normalized})}</div></div>`;
    }

    if (metric.meta.detailGroup === 'tpl') bars.insertAdjacentHTML('beforeend', tplCompareDetailMarkup(data));
    if (metric.meta.detailGroup === 'coast') bars.insertAdjacentHTML('beforeend', coastCompareDetailMarkup(metric));
    if (metric.meta.detailGroup === 'extractive') bars.insertAdjacentHTML('beforeend', extractiveCompareDetailMarkup(metric));

    installAgePyramidDelegation(bars);
    if (metric.meta.detailGroup !== 'tpl') {
      def.querySelectorAll('[data-scale]').forEach(button => button.addEventListener('click', () => renderCompareMetric(data,themeKey,metricKey,button.dataset.scale === 'normalized',view)));
    }
    if (selectableComposite) {
      // Delegate from #compare-bars: ux-history rebuilds the markup inside this node,
      // so listeners attached directly to buttons/selects would be lost after enhancement.
      bars.onclick = event => {
        const choiceButton = event.target.closest('button[data-composite-choice]');
        if (choiceButton && bars.contains(choiceButton)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:choiceButton.dataset.compositeChoice});
          return;
        }
        const scaleButton = event.target.closest('button[data-composite-scale]');
        if (scaleButton && bars.contains(scaleButton)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,scale:scaleButton.dataset.compositeScale});
        }
      };
      bars.onchange = event => {
        const ageSelect = event.target.closest('select[data-demographic-age]');
        const genderSelect = event.target.closest('select[data-demographic-gender]');
        if ((ageSelect || genderSelect) && bars.contains(event.target)) {
          const [oldAge,oldGender] = String(view.choice || '').split('|');
          const age = ageSelect ? ageSelect.value : oldAge;
          const gender = genderSelect ? genderSelect.value : oldGender;
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:`${age}|${gender}`});
          return;
        }
        const componentSelect = event.target.closest('select[data-composite-component]');
        if (componentSelect && bars.contains(componentSelect)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:componentSelect.value});
        }
      };
    } else if (specialComposite) {
      bars.onclick = null;
      bars.onchange = event => {
        const qualitySelect=event.target.closest('select[data-water-quality-parameter-compare]');
        if(qualitySelect&&bars.contains(qualitySelect)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:qualitySelect.value});
          return;
        }
        const remediationSelect=event.target.closest('select[data-remediation-compare-view]');
        if(remediationSelect&&bars.contains(remediationSelect)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:remediationSelect.value});
        }
      };
    } else if (hasNormalized) {
      // Lo switch assoluto/rapportato vive accanto al grafico: delega dal
      // contenitore stabile perché il render sostituisce il markup interno.
      bars.onclick = event => {
        const scaleButton = event.target.closest('button[data-scale]');
        if (scaleButton && bars.contains(scaleButton)) {
          renderCompareMetric(data,themeKey,metricKey,scaleButton.dataset.scale === 'normalized',view);
        }
      };
      bars.onchange = null;
    } else {
      bars.onclick = null;
      bars.onchange = null;
    }

    if (demographicPyramid) {
      demographicPyramid.innerHTML = compositeType === 'demographicBreakdown'
        ? demographicRatePyramidMarkup(metric,{town:'Versilia',parts:metric.aggregate?.parts || []})
        : '';

      if (compositeType === 'demographicBreakdown') {
        const points = [...demographicPyramid.querySelectorAll('.age-pyramid-point')];
        const hideAll = except => points.forEach(point => {
          if (point === except) return;
          point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
        });
        points.forEach(point => {
          const tooltip = point.querySelector('.chart-tooltip');
          if (!tooltip) return;
          const show = () => {
            hideAll(point);
            tooltip.removeAttribute('hidden');
          };
          const hide = () => tooltip.setAttribute('hidden','');
          point.addEventListener('pointerenter', show);
          point.addEventListener('pointerleave', hide);
          point.addEventListener('focus', show);
          point.addEventListener('blur', hide);
          point.addEventListener('click', event => {
            event.preventDefault();
            show();
          });
          point.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              show();
            } else if (event.key === 'Escape') {
              hide();
              point.blur();
            }
          });
        });
      }
    }

    const benchmarkMetric = compositeType === 'sexBreakdown' && metric.meta.benchmarksBySex?.[view.choice]
      ? { ...metric, meta:{ ...metric.meta, benchmark:metric.meta.benchmarksBySex[view.choice] } }
      : metric;
    benchmark.innerHTML = (metricKey.startsWith('slowMobility') || (metric.meta.compositeType && compositeType !== 'sexBreakdown')) ? '' : benchmarkMarkup(benchmarkMetric,aggregate,unit,null);
    tools.innerHTML = `${libraryHistoryTableMarkup(metric)}${methodDisclosure(metric)}<div class="data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a>${metricKey.startsWith('slowMobility') ? `<a href="${route('percorsi/')}">Esplora la cartografia</a>` : ''}<button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div>`;
    tools.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data,metricKey,normalized));
    tools.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  }


  function libraryHistoryTableMarkup(metric) {
    const keys = new Set(['libraryLoansPerResident','libraryActiveBorrowersPer100','libraryWeeklyOpeningHours']);
    if (!keys.has(metric?.meta?.key)) return '';
    const rows = metric.rows || [];
    const years = [...new Set(rows.flatMap(row => row.series?.years || []))].sort((a,b)=>a-b);
    if (!years.length) return '';
    const maps = new Map(rows.map(row => [row.code, new Map((row.series?.years || []).map((year,index)=>[year,row.series.values[index]]))]));
    const tableRows = [...years].reverse().map(year => {
      const available = rows.map(row => maps.get(row.code)?.get(year)).filter(value => value !== null && value !== undefined);
      const mean = available.length ? available.reduce((sum,value)=>sum+Number(value),0) / available.length : null;
      const cells = rows.map(row => {
        const value = maps.get(row.code)?.get(year);
        return `<td>${value === null || value === undefined ? 'n.d.' : html(formatValue(value, metric.meta.unit))}</td>`;
      }).join('');
      return `<tr${year === 2020 ? ' class="library-pandemic-year"' : ''}><th scope="row">${html(String(year))}${year === 2020 ? ' *' : ''}</th>${cells}<td><b>${mean === null ? 'n.d.' : html(formatValue(mean, metric.meta.unit))}</b><small>${available.length}/7</small></td></tr>`;
    }).join('');
    const range = `${years[0]}–${years.at(-1)}`;
    const pandemic = years.includes(2020) ? ' * 2020: anno pandemico anomalo.' : '';
    return `<details class="detail-disclosure library-history-detail" open><summary><span>Serie storica completa</span><small>${html(range)} · valori ufficiali disponibili</small></summary><div class="indicator-table-scroll"><table class="library-history-table"><thead><tr><th>Anno</th>${rows.map(row=>`<th>${html(row.town)}</th>`).join('')}<th>Media comuni con dato</th></tr></thead><tbody>${tableRows}</tbody></table></div><p class="aggregate-note">La media di ogni anno è aritmetica e usa esclusivamente i Comuni con un valore disponibile; gli n.d. non entrano nel divisore.${html(pandemic)}</p></details>`;
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
    const isOmi = metric.meta.compositeType === 'omi';
    const isDemographic = metric.meta.compositeType === 'demographicBreakdown';
    const isSexBreakdown = metric.meta.compositeType === 'sexBreakdown';
    const lines = isSexBreakdown ? [['Territorio','Codice Istat','Indicatore','Anno','Sesso','Valore','Unità','Fonte']] : isOmi ? [['Comune','Codice Istat','Indicatore','Anno','Zona OMI','Area','Vendita €/m²','Affitto €/m²/mese','Fonte']] : isDemographic ? [['Comune','Codice Istat','Indicatore','Anno','Fascia età','Genere','Valore %','Numeratore','Denominatore','Fonte']] : metric.meta.compositeType ? [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Componente', 'Valore', 'Unità', 'Conteggio', 'Fonte']] : [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Valore', 'Unità', 'Fonte']];
    if (isSexBreakdown) {
      const sources = [...metric.rows.map(row=>({territory:row.town,code:row.code,parts:row.parts||[]})), {territory:'Versilia',code:'202M',parts:metric.aggregate?.parts||[]}];
      sources.forEach(source => source.parts.forEach(part => (part.series?.years || []).forEach((year,index) => lines.push([source.territory,source.code,label,year,part.label,part.series.values[index],part.unit || metric.meta.unit,metric.sourceUrl]))));
    }
    else if (isOmi) rows.forEach(row => (row.zones || []).forEach(zone => lines.push([row.town,row.code,label,metric.meta.year,zone.code,zone.label,zone.sale,zone.rent,metric.sourceUrl])));
    else if (isDemographic) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town,row.code,label,metric.meta.year,part.ageLabel,part.genderLabel,part.value,part.numerator,part.denominator,metric.sourceUrl])));
    else if (metric.meta.compositeType) rows.forEach(row => ((metric.meta.key === 'incomeDistribution' && row.detailParts?.length) ? row.detailParts : (row.parts || [])).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, row.notApplicable ? 'n.a.' : part.value, part.unit || metric.meta.unit, part.count, metric.sourceUrl])));
    else rows.forEach(row => lines.push([row.town, row.code, label, metric.meta.year, row.notApplicable ? 'n.a.' : row.displayValue, row.displayUnit, metric.sourceUrl]));
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
    const params = new URLSearchParams
(location.search);
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
    renderTownMetric(data, town, themeKey, metricKey, selectMetric);
    scrollActiveControl(document.querySelector('.theme-nav'));
  }

  function slowMobilityMapHref(townName, metricKey) {
    const modes = {
      slowMobilityTrekking: 'trekking',
      slowMobilityCammini: 'cammino',
      slowMobilityBici: 'bicycle',
      slowMobilityMtb: 'mtb'
    };
    const params = new URLSearchParams({ comune: townName });
    if (modes[metricKey]) params.set('tipo', modes[metricKey]);
    return route(`percorsi/?${params.toString()}`);
  }

  function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect) {
    const theme = data.themes[themeKey];
    const metric = data.metrics[metricKey];
    const row = metric.rows.find(r => r.code === town.code);
    const ranked = metricRows(data, metricKey);
    const rank = ranked.findIndex(r => r.code === town.code) + 1;
    const container = document.getElementById('town-topic');
    container.dataset.theme = themeKey;
    container.classList.toggle('erp-arrears-view', metricKey === 'erpArrears');
    const historical = Boolean(row.series?.values?.length);
    const composite = Boolean(metric.meta.compositeType);
    const distribution = metric.meta.compositeType === 'distribution';
    const omi = metric.meta.compositeType === 'omi';
    const stock = metric.meta.compositeType === 'stock';
    const securityMeasures = ['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType);
    const demographicBreakdown = metric.meta.compositeType === 'demographicBreakdown';
    const sexBreakdown = metric.meta.compositeType === 'sexBreakdown';
    const drinkingQuality = metric.meta.compositeType === 'drinkingWaterQuality';
    const remediation = metric.meta.compositeType === 'remediationProceedings';
    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown;
    const options = selectable ? compositeSelectionOptions(metric,row) : [];
    const defaultDemographicChoice = demographicBreakdown ? `${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}` : null;
    const defaultSexChoice = sexBreakdown ? (metric.meta.defaultSex || 'totale') : null;
    const summary = distribution ? compositeSummary(metric,row) : (sexBreakdown ? (options.find(option=>option.key===defaultSexChoice) || options[0]) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures) ? options[0] : null)));
    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (sexBreakdown ? compositeSelectionAggregate(metric,defaultSexChoice) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)))));
    const summaryDelta = selectable ? (row.notApplicable ? { headline:'n.a.', direction:'Comune non costiero' } : compositeDeltaText(summary.value,aggregateSummary.value,summary.unit)) : null;
    const panelOverline = drinkingQuality ? 'Dati analitici GAIA' : remediation ? 'Dettaglio dei procedimenti' : composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : sexBreakdown ? 'Totale, Maschi e Femmine' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa') : (historical ? 'Andamento storico' : 'Confronto territoriale');
    const panelTitle = drinkingQuality ? 'Valori per località e parametro' : remediation ? 'Iter attivi e chiusi' : composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : sexBreakdown ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`) : (historical ? 'Evoluzione nel tempo' : 'Confronto tra i comuni');
    const selector = demographicBreakdown ? `<div class="composite-read-selector demographic-town-selectors"><label><span>Fascia d’età</span><select data-demographic-town-age>${demographicAgeOptionsMarkup(metric,metric.meta.defaultAge || '25-64')}</select></label><label><span>Genere</span><select data-demographic-town-gender>${(metric.meta.genderOptions || []).map(option=>`<option value="${html(option.key)}" ${option.key === (metric.meta.defaultGender || 'total') ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>` : (selectable ? `<label class="composite-read-selector"><span>${html(metric.meta.selectorLabel || 'Dato in evidenza')}</span><select data-composite-choice>${options.map((option,index)=>`<option value="${html(option.key)}" ${index===0?'selected':''}>${html(option.label)}</option>`).join('')}</select></label>` : '');
    const primaryLabel = drinkingQuality ? 'Consultazione analitica' : remediation ? 'Procedimenti SISBON' : selectable ? summary.label : (composite ? (metric.meta.primaryLabel || 'Valore di riferimento') : '');
    const primaryValue = drinkingQuality ? `${number0.format(metric.parameterDefinitions?.length||0)} parametri GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : selectable ? summary.formatted : formatMetricRowValue(row,row.value,metric.meta.unit);
    const positionMarkup = selectable
      ? `<aside class="versilia-position composite-versilia-position" data-composite-selection="summary"><span class="overline">Rispetto alla Versilia</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${html(summaryDelta.direction)}</small></strong><p>Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.</p><div><span data-composite-aggregate-label>${html(aggregateSummary.label)}</span><b data-composite-aggregate-value>${html(aggregateSummary.formatted)}</b></div></aside>`
      : (drinkingQuality
        ? ''
        : remediation
        ? `<aside class="versilia-position remediation-overview"><span class="overline">Fotografia SISBON</span><strong>${html(number0.format(remediationPartValue(row,'active')+remediationPartValue(row,'closed')))}<small>procedimenti</small></strong><p>Il conteggio non equivale automaticamente a siti attualmente contaminati.</p><div><span>Attivi / chiusi</span><b>${html(number0.format(remediationPartValue(row,'active')))} / ${html(number0.format(remediationPartValue(row,'closed')))}</b></div></aside>`
        : row.notApplicable
        ? `<aside class="versilia-position"><span class="overline">Applicabilità territoriale</span><strong>n.a.<small>Comune non costiero</small></strong><p>${html(row.applicabilityNote)}</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</b></div></aside>`
        : `<aside class="versilia-position"><span class="overline">Ordine del valore</span><strong>${rank}<sup>°</sup> <small>su 7</small></strong><p>${html(interpretation(metric.meta))}</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</b></div></aside>`);
    container.innerHTML = `<div class="town-topic-heading"><div><h2>${html(theme.question)}</h2></div><a href="${route(`confronta/${themeKey}/?indicatore=${metricKey}`)}">Confronta i 7 comuni <span>→</span></a></div>
      ${metricControls(data, themeKey, metricKey, true)}
      ${metricKey.startsWith('slowMobility') ? `<div class="slow-mobility-map-entry"><span>Vedi sulla mappa i percorsi di ${html(town.name)} corrispondenti alla selezione.</span><a href="${slowMobilityMapHref(town.name, metricKey)}">Esplora sulla mappa <b>→</b></a></div>` : ''}
      <div class="town-metric-layout${drinkingQuality?' single-column':''}"><article class="town-metric-primary">${composite ? `<span class="composite-primary-label" data-composite-primary-label>${html(primaryLabel)}</span>` : ''}<strong data-composite-primary-value>${html(primaryValue)}</strong><p>${html(metric.meta.description)}</p>${row.notApplicable ? `<p class="normalized-companion"><b>Applicabilità:</b> ${html(row.applicabilityNote)}</p>` : ''}
        ${selector}
        ${row.normalized ? `<p class="normalized-companion"><b>${html(row.normalized.label)}:</b> ${html(formatValue(row.normalized.value, row.normalized.unit))}</p>` : ''}
        <div><span>${html(metric.meta.year)}</span><a class="inline-source-link" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte originale ↗</a></div></article>
        ${positionMarkup}</div>
      <section class="history-panel ${composite ? 'composite-history-panel' : ''}"><div class="panel-title"><div><span class="overline">${html(panelOverline)}</span><h3>${html(panelTitle)}</h3></div><a class="source-pill" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${html(metric.meta.source)} ↗</a></div>
        ${composite ? `<div class="composite-fixed-detail">${compositeTownMarkup(metric, row)}</div>` : (historical ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : `<div class="comparison-bars">${barRows(data, metricKey, { selectedTown: normalize(town.name).replaceAll(' ', '-') })}</div>`)}</section>
      ${coastTownDetailMarkup(metric,row)}
      ${extractiveTownDetailMarkup(metric,row)}
      ${deepDiveMarkup(data, town, themeKey, metricKey)}
      ${erpArrearsDetailMarkup(metric,row)}
      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}
      ${methodDisclosure(metric)}
      <div class="data-actions town-data-actions"><a href="${indicatorHref(metric)}">Scheda indicatore</a>${metricKey.startsWith('slowMobility') ? `<a href="${slowMobilityMapHref(town.name, metricKey)}">Esplora sulla mappa</a>` : ''}<button type="button" data-share>Condividi</button><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div>`;

    if (selectable) {
      const initialPosition=container.querySelector('.composite-versilia-position');
      const initialChoice=options[0]?.key || 'summary';
      updateFiscalRecoveryTownPosition(metric,row,initialChoice,initialPosition);
      updateAgricultureProfileTownPosition(metric,row,initialChoice,initialPosition);
      updateMaritimeTownPosition(metric,row,initialChoice,initialPosition);
      updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);
    }

    const tablist = container.querySelector('[role="tablist"]');
    installTablist(tablist, onMetricSelect);
    container.querySelector('[data-share]')?.addEventListener('click', event => shareCurrentPage(event.currentTarget));
    container.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data, metricKey));
    container.querySelector('[data-print]')?.addEventListener('click', () => window.print());
    if (selectable) {
      const select=container.querySelector('[data-composite-choice]');
      const demoAge=container.querySelector('[data-demographic-town-age]');
      const demoGender=container.querySelector('[data-demographic-town-gender]');
      const applyChoice=(choice)=>{
        const selected=options.find(option=>option.key===choice) || options[0];
        const agg=compositeSelectionAggregate(metric,choice);
        const delta=row.notApplicable ? { headline:'n.a.', direction:'Comune non costiero' } : compositeDeltaText(selected.value,agg.value,selected.unit);
        const labelEl=container.querySelector('[data-composite-primary-label]');
        const valueEl=container.querySelector('[data-composite-primary-value]');
        const position=container.querySelector('.composite-versilia-position');
        if(labelEl) labelEl.textContent=selected.label;
        if(valueEl) valueEl.textContent=selected.formatted;
        if(position) {
          position.dataset.compositeSelection=choice;
          const deltaEl=position.querySelector('[data-composite-delta]');
          if(deltaEl) deltaEl.innerHTML=`${html(delta.headline)}<small>${html(delta.direction)}</small>`;
          const aggLabel=position.querySelector('[data-composite-aggregate-label]');
          const aggValue=position.querySelector('[data-composite-aggregate-value]');
          if(aggLabel) aggLabel.textContent=agg.label;
          if(aggValue) aggValue.textContent=agg.formatted;
        }
        updateFiscalRecoveryTownPosition(metric,row,choice,position);
        updateAgricultureProfileTownPosition(metric,row,choice,position);
        updateMaritimeTownPosition(metric,row,choice,position);
        updateExtractiveTownPosition(metric,row,choice,position);
        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));
      };
      select?.addEventListener('change',()=>applyChoice(select.value));
      const applyDemographic=()=>applyChoice(`${demoAge?.value || metric.meta.defaultAge || '25-64'}|${demoGender?.value || metric.meta.defaultGender || 'total'}`);
      demoAge?.addEventListener('change',applyDemographic);
      demoGender?.addEventListener('change',applyDemographic);
    }
    if (drinkingQuality) {
      const root=container.querySelector('.water-quality-town');
      const localitySelect=root?.querySelector('[data-water-quality-locality]');
      const parameterSelect=root?.querySelector('[data-water-quality-parameter-town]');
      const selectedHost=root?.querySelector('[data-water-quality-selected]');
      const applyWaterQuality=()=>{
        if(selectedHost) selectedHost.innerHTML=waterQualitySelectedMarkup(metric,row,localitySelect?.value||0,parameterSelect?.value||0);
      };
      localitySelect?.addEventListener('change',applyWaterQuality);
      parameterSelect?.addEventListener('change',applyWaterQuality);
    }
    if (remediation) {
      const root=container.querySelector('.remediation-town');
      const viewSelect=root?.querySelector('[data-remediation-town-view]');
      const benchmarkHost=root?.querySelector('[data-remediation-benchmark-host]');
      const applyRemediation=()=>{
        const view=viewSelect?.value==='closed'?'closed':'active';
        root?.querySelectorAll('[data-remediation-status]').forEach(item=>item.toggleAttribute('hidden',item.dataset.remediationStatus!==view));
        if(benchmarkHost) benchmarkHost.innerHTML=remediationBenchmarkMarkup(metric,row,view);
      };
      viewSelect?.addEventListener('change',applyRemediation);
    }
    installChartInteractions(container);
    installAgePyramidDelegation(container);
    scrollActiveControl(tablist);

    const context = document.getElementById('town-context');
    context.innerHTML = themeKey === 'sicurezza' ? crimeMarkup(data) : (themeKey === 'demografia' ? brainDrainMarkup(data) : '');
    if (themeKey === 'sicurezza') installCrimeInteractions(data);
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
    const metric = data.metrics[key];
    const row = metric.rows.find(r => r.code === town.code);
    const rank = metricRows(data, key).findIndex(item => item.code === town.code) + 1;
    const drinkingQuality=metric.meta.compositeType==='drinkingWaterQuality',remediation=metric.meta.compositeType==='remediationProceedings';
    const cardValue = drinkingQuality ? `${number0.format(row.localities?.length||0)} località GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : metric.meta.compositeType === 'distribution' ? compositeSummary(metric,row).formatted : formatMetricRowValue(row,row.value,metric.meta.unit);
    const cardMeta=drinkingQuality ? `${metric.meta.year} · dettaglio analitico` : remediation ? `${metric.meta.year} · conteggi SISBON` : `${metric.meta.year} · ${row.notApplicable ? 'n.a.' : `${rank}° valore`}`;
    return `<button type="button" data-indicator="${key}" class="${key === activeKey ? 'active' : ''}" aria-pressed="${key === activeKey}"><span>${html(metric.meta.shortLabel)}</span><strong>${html(cardValue)}</strong><small>${html(cardMeta)}</small></button>`;
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

  function deepDiveMarkup(data, town, themeKey, metricKey = '') {
    const detail = data.details[town.code];
    if (!detail) return '';
    if (themeKey === 'salute') {
      const health = data.healthB?.[town.code];
      if (!health) return '';
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Dettagli sanitari aggiuntivi</h3></div><p>Questa sezione contiene soltanto dati che non sono già presenti nel selettore degli indicatori.</p></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio sanitario</span><small>Altre patologie e mortalità per causa</small></summary><div class="deep-columns"><div><h4>Altre patologie selezionate</h4><ul class="deep-list deep-list--rates"><li><span>Ipertensione</span><span class="deep-list-value"><strong>${number2.format(health.hypertension)}</strong><small>ogni 1.000 residenti</small></span></li><li><span>BPCO</span><span class="deep-list-value"><strong>${number2.format(health.copd)}</strong><small>ogni 1.000 residenti</small></span></li></ul></div><div><h4>Mortalità per causa</h4><ul class="deep-list deep-list--rates"><li><span>Tumori</span><span class="deep-list-value"><strong>${number2.format(health.mortalityTumors)}</strong><small>ogni 100.000 residenti</small></span></li><li><span>Malattie circolatorie</span><span class="deep-list-value"><strong>${number2.format(health.mortalityCirculatory)}</strong><small>ogni 100.000 residenti</small></span></li><li><span>Malattie respiratorie</span><span class="deep-list-value"><strong>${number2.format(health.mortalityRespiratory)}</strong><small>ogni 100.000 residenti</small></span></li></ul></div></div></details></section>`;
    }
    if (themeKey === 'economia') {
      const e = detail.economy;
      const maxWorkers = Math.max(...e.topSectors.map(s => s.workers), 1);
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Struttura economica</h3></div><p>Fasce di reddito, capacità ricettiva e principali settori per presenza locale. I valori derivano dalle stesse fonti richiamate negli indicatori.</p></div>
        <div class="deep-facts-grid"><article class="deep-fact"><span>Dichiaranti</span><strong>${number0.format(town.taxpayers)}</strong><small>Anno ${html(e.incomeYear)}</small></article></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio economico</span><small>Settori produttivi e fasce di reddito</small></summary><div class="deep-columns"><div><h4>Principali settori per addetti</h4><div class="deep-bar-list">${e.topSectors.map(s => `<div class="deep-bar-row"><div class="deep-bar-heading"><span>${html(s.label)}</span><span class="deep-bar-value"><strong>${number2.format(s.workers)}</strong><small>addetti</small></span></div><div class="deep-bar-track"><span style="width:${s.workers / maxWorkers * 100}%"></span></div><small>${number0.format(s.localUnits)} unità locali</small></div>`).join('')}</div></div>
        <div><h4>Dichiaranti per fascia di reddito</h4><ul class="deep-list deep-list--income">${e.incomeBands.map(b => `<li><span>${html(b.label)}</span><span class="deep-list-value"><strong>${number0.format(b.people)}</strong><small>dichiaranti</small></span></li>`).join('')}</ul></div></div></details></section>`;
    }
    if (themeKey === 'mobilita') {
      const m = detail.mobility;
      const metric = data.metrics?.[metricKey];
      const flowSection = data.themes?.mobilita?.sections?.find(section => section.key === 'pendolarismo');
      const isTpl = metric?.meta?.detailGroup === 'tpl';
      const isFlow = Boolean(flowSection?.metrics?.includes(metricKey));
      if (isTpl && m.tpl) {
        return `<section class="topic-deep-dive tpl-town-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Trasporto pubblico programmato</h3></div><p>Dettaglio del servizio GTFS nella giornata di riferimento. Corse, accessi e ampiezza oraria descrivono l’offerta programmata, non puntualità, capacità o passeggeri.</p></div>
          <details class="detail-disclosure tpl-town-detail"><summary><span>Mostra il dettaglio TPL programmato</span><small>Bus, ferrovia, accessi, route e orari</small></summary><div class="deep-facts-grid tpl-town-service-grid" role="list" aria-label="Dettaglio del servizio TPL programmato"><article class="deep-fact" role="listitem"><span>Corse programmate</span><strong>${number0.format(m.tpl.trips)}</strong><small>totale bus e ferrovia</small></article><article class="deep-fact" role="listitem"><span>Bus</span><strong>${number0.format(m.tpl.busTrips)}</strong><small>corse programmate</small></article><article class="deep-fact" role="listitem"><span>Ferrovia</span><strong>${number0.format(m.tpl.railTrips)}</strong><small>corse programmate</small></article><article class="deep-fact" role="listitem"><span>Punti di accesso GTFS</span><strong>${number0.format(m.tpl.activeAccessPoints)}</strong><small>coppie feed e stop_id attive</small></article><article class="deep-fact" role="listitem"><span>Route GTFS attive</span><strong>${number0.format(m.tpl.routes)}</strong><small>dettaglio descrittivo</small></article><article class="deep-fact tpl-town-service-fact" role="listitem"><span>Finestra di servizio</span><strong class="tpl-town-service-range">${html(m.tpl.firstDeparture)}–${html(m.tpl.lastDeparture)}</strong><small class="tpl-town-service-span">${number2.format(m.tpl.serviceSpanHours)} h</small></article></div><p class="aggregate-note tpl-detail-note">Fotografia del servizio programmato del 26 agosto 2026. I punti GTFS non coincidono necessariamente con fermate fisiche uniche; gli orari “+1 giorno” appartengono alla stessa giornata operativa.</p></details></section>`;
      }
      if (!isFlow) return '';
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Flussi di pendolarismo</h3></div><p>Origini e destinazioni principali dei flussi rilevati dal censimento. Il saldo non misura la qualità della mobilità.</p></div>
        <details class="detail-disclosure"><summary><span>Mostra origini e destinazioni</span><small>Prime cinque relazioni di pendolarismo</small></summary><div class="deep-columns"><div><h4>Destinazioni principali</h4><ul class="deep-list deep-list--flows">${m.topDestinations.map(x => `<li><span>${html(x.name)}</span><span class="deep-list-value"><strong>${number0.format(x.people)}</strong><small>pendolari</small></span></li>`).join('')}</ul></div><div><h4>Origini principali</h4><ul class="deep-list deep-list--flows">${m.topOrigins.map(x => `<li><span>${html(x.name)}</span><span class="deep-list-value"><strong>${number0.format(x.people)}</strong><small>pendolari</small></span></li>`).join('')}</ul></div></div></details></section>`;
    }
    if (themeKey === 'ambiente') {
      const e = detail.environment;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Pressioni ambientali</h3></div><p>Andamento dei rifiuti, incremento netto di suolo consumato ed esposizione della popolazione ai rischi territoriali.</p></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio dei rischi</span><small>Edifici esposti</small></summary><div class="risk-grid"><article><span>Edifici esposti ad alluvioni</span><strong>${number0.format(e.flood.buildings)}</strong></article><article><span>Edifici esposti a frane</span><strong>${number0.format(e.landslide.buildings)}</strong></article></div></details></section>`;
    }
    if (themeKey === 'comunita') {
      const g = detail.government;
      return `<section class="topic-deep-dive"><div class="deep-heading"><div><span class="overline">Approfondimento comunale</span><h3>Cassa, opere e PNRR</h3></div><p>Pagamenti e
incassi di cassa, valore delle opere monitorate e stato dei progetti PNRR censiti.</p></div>
        <details class="detail-disclosure"><summary><span>Mostra il dettaglio amministrativo</span><small>Cassa e opere monitorate</small></summary><div class="government-grid"><article><span>Pagamenti</span><strong>${currency0.format(g.payments)}</strong><small>Anno ${html(g.year)}</small></article><article><span>Incassi</span><strong>${currency0.format(g.receipts)}</strong><small>Saldo ${currency0.format(g.cashBalance)}</small></article><article><span>Opere monitorate</span><strong>${number0.format(g.publicWorks)}</strong><small>Valore ${currency0.format(g.publicWorksValue)}</small></article></div></details></section>`;
    }
    return '';
  }


  function incomeInflationMarkup(data) {
    const c=data.incomeInflationContext;if(!c?.years?.length)return '';
    const w=720,h=300,l=52,r=18,t=22,b=42,all=[...c.incomeIndex,...c.priceIndex,...c.realIncomeIndex].map(Number).filter(Number.isFinite),min=Math.floor(Math.min(...all,98)-2),max=Math.ceil(Math.max(...all,102)+2);
    const x=i=>l+(w-l-r)*i/Math.max(1,c.years.length-1),y=v=>t+(h-t-b)*(max-Number(v))/Math.max(1,max-min),path=values=>values.map((v,i)=>`${i?'L':'M'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' '),ticks=[...new Set([min,100,110,120,max].filter(v=>v>=min&&v<=max))].sort((a,b)=>a-b);
    const grid=ticks.map(v=>`<g><line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".12"></line><text x="${l-10}" y="${y(v)+4}" text-anchor="end" class="chart-label chart-y-label">${html(number0.format(v))}</text></g>`).join(''),labels=c.years.map((year,i)=>(i%2===0||i===c.years.length-1)?`<text x="${x(i)}" y="${h-14}" text-anchor="middle" class="chart-label">${html(year)}</text>`:'').join('');
    return `<section class="crime-context page-width income-inflation-context" id="redditi-prezzi"><div class="crime-context-copy"><span class="overline">Contesto · redditi e costo della vita</span><h2>Redditi vs inflazione</h2><p>Confronto tra reddito imponibile medio dei sette comuni e NIC nazionale ISTAT, entrambi riportati a <strong>${html(c.base)}</strong>.</p><div class="crime-stats"><article><span>Imponibile medio</span><strong>+${html(number1.format(c.nominalGrowthPercent))}%</strong><small>2016–2024</small></article><article><span>Prezzi NIC Italia</span><strong>+${html(number1.format(c.priceGrowthPercent))}%</strong><small>2016–2024</small></article><article><span>A prezzi costanti</span><strong>+${html(number1.format(c.realGrowthPercent))}%</strong><small>imponibile medio</small></article></div><p class="brain-drain-note">${html(c.note)}</p><div><a class="source-pill" href="${html(c.incomeSourceUrl)}" target="_blank" rel="noreferrer">Fonte redditi · MEF ↗</a> <a class="source-pill" href="${html(c.priceSourceUrl)}" target="_blank" rel="noreferrer">Fonte prezzi · ISTAT ↗</a></div></div><div class="crime-context-data"><h3>Redditi e prezzi · ${html(c.base)}</h3><div class="income-inflation-legend"><span>━ ${html(c.incomeLabel)}</span><span>┅ ${html(c.priceLabel)}</span><span>┈ ${html(c.realLabel)}</span></div><div class="trend-chart"><svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Confronto redditi e prezzi dal 2016 al 2024">${grid}${labels}<path d="${path(c.incomeIndex)}" fill="none" stroke="currentColor" stroke-width="3.4"></path><path d="${path(c.priceIndex)}" fill="none" stroke="currentColor" stroke-width="2.8" stroke-dasharray="10 7" opacity=".72"></path><path d="${path(c.realIncomeIndex)}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-dasharray="2 6" opacity=".9"></path>${c.incomeIndex.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="3.5" fill="currentColor"><title>${html(c.years[i])}: ${html(number1.format(v))}</title></circle>`).join('')}</svg></div><p class="brain-drain-note">Il NIC nazionale misura l’andamento medio dei prezzi in Italia. Il reddito è invece calcolato sui sette Comuni della Versilia: il grafico è un confronto di contesto, non un’identità territoriale.</p></div></section>`;
  }

  function brainDrainMarkup(data) {
    const b = data.brainDrain;
    if (!b) return '';
    return `<section class="crime-context brain-drain-context page-width" id="mobilita-laureati"><div class="crime-context-copy"><span class="overline">Contesto sovracomunale · capitale umano</span><h2>Mobilità dei laureati italiani 25–39 anni</h2><p>L’indicatore ufficiale BesT non è disponibile in modo affidabile per i singoli Comuni. Per la Versilia viene quindi esposto il livello provinciale, senza attribuire il valore di Lucca ai sette territori.</p><a class="source-pill" href="${html(b.sourceUrl)}" target="_blank" rel="noreferrer">Fonte Istat · BesT ↗</a></div><div class="crime-context-data"><h3>Saldo migratorio dei laureati · ${html(b.year)}</h3><div class="crime-stats brain-drain-stats"><article><span>Provincia di Lucca</span><strong>${html(number1.format(b.provinceValue))}‰</strong><small>laureati italiani 25–39 anni</small></article><article><span>Toscana</span><strong>${b.regionValue>0?'+':''}${html(number1.format(b.regionValue))}‰</strong><small>riferimento regionale</small></article><article><span>Italia</span><strong>${b.italyValue>0?'+':''}${html(number1.format(b.italyValue))}‰</strong><small>riferimento nazionale</small></article></div><details class="brain-drain-detail"><summary>Confronta le province toscane <b>+</b></summary><div class="brain-drain-provinces">${b.rows.map(row=>`<div><span>${html(row.name)}</span><strong>${row.value>0?'+':''}${html(number1.format(row.value))}‰</strong></div>`).join('')}</div></details><p class="brain-drain-note">${html(b.note)}</p></div></section>`;
  }

  function crimeMarkup(data) {
    return `<section class="crime-context page-width" id="criminalita"><div class="crime-context-copy"><span class="overline">Contesto sovracomunale</span><h2>Criminalità e delitti denunciati</h2><p>Il dato non è disponibile in forma omogenea per comune. Viene quindi mostrato per Provincia di Lucca, Toscana e Italia, senza attribuirlo ai singoli territori.</p><a class="source-pill" href="https://www.istat.it/" target="_blank" rel="noreferrer">Fonte Istat ↗</a></div>
      <div class="crime-context-data"><div class="crime-tabs">${['total','theft','burglary','fraud'].map((k, i) => `<button type="button" class="${i === 0 ? 'active' : ''}" data-crime="${k}">${{total:'Totale',theft:'Furti',burglary:'In abitazione',fraud:'Truffe e frodi'}[k]}</button>`).join('')}</div><div id="crime-data"></div></div></section>`;
  }

  function installCrimeInteractions(data) {
    const root = document.querySelector('.crime-context [data-crime]')?.closest('.crime-context');
    const target = root?.querySelector('#crime-data');
    if (!root || !target || !data.crime) return;
    const update = key => {
      root.querySelectorAll('[data-crime]').forEach(b => b.classList.toggle('active', b.dataset.crime === key));
      const labels = { total:'Delitti denunciati', theft:'Furti denunciati', burglary:'Furti in abitazione', fraud:'Truffe e frodi informatiche' };
      target.innerHTML = `<h3>${labels[key]} · ${html(data.crime.year)}</h3><div class="crime-stats">${data.crime.areas.map(area => `<article><span>${html(area.name)}</span><strong>${number1.format(area.values[key])}</strong><small>ogni 100.000 abitanti</small></article>`).join('')}</div>`;
    };
    root.querySelectorAll('[data-crime]').forEach(b => b.addEventListener('click', () => update(b.dataset.crime)));
    update('total');
  }

  function resolveSourcePolicy(metricKey, metric, registry) {
    const defaults = registry?.defaults || {};
    const override = registry?.metricOverrides?.[metricKey] || {};
    const profileId = override.profile || registry?.sourceProfileByUrl?.[metric.sourceUrl] || '';
    const profile = registry?.sourceProfiles?.[profileId] || {};
    const policy = { ...defaults, ...profile, ...override };
    delete policy.profile;
    return { ...policy, profileId };
  }

  function canonicalSourceForMonitor(value) {
    try {
      const url = new URL(value);
      url.hash = '';
      ['v','cache','cachebust','timestamp','_'].forEach(key => url.searchParams.delete(key));
      url.searchParams.sort();
      return url.href;
    } catch (_error) {
      return String(value || '');
    }
  }

  function indicatorComparisonTable(data, metricKey) {
    const metric = data.metrics[metricKey];
    const rows = [...metric.rows].sort((a, b) => a.town.localeCompare(b.town, 'it'));
    if (metric.meta.compositeType) return `<div class="indicator-composite-table">${compositeCompareMarkup(data, metricKey)}</div>`;
    return `<div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th scope="col">Comune</th><th scope="col">Valore · ${html(metric.meta.year)}</th><th scope="col">Apri il territorio</th></tr></thead><tbody>${rows.map(row => `<tr><th scope="row">${html(row.town)}</th><td>${html(formatValue(row.value, metric.meta.unit))}</td><td><a href="${route(`comuni/${row.slug}/?tema=${metric.meta.theme}&indicatore=${metricKey}`)}">Scheda comunale <span aria-hidden="true">→</span></a></td></tr>`).join('')}</tbody></table></div>`;
  }

  function indicatorHistoryTable(metric) {
    const seriesFor = row => metric.meta.key === 'income' && row.longSeries?.years?.length ? row.longSeries : row.series;
    const historicalRows = metric.rows.filter(row => seriesFor(row)?.years?.length && seriesFor(row)?.values?.length);
    if (!historicalRows.length) {
      return `<div class="indicator-history-empty"><strong>Serie storica non ancora disponibile</strong><p>La fonte utilizzata non consente, al momento, di pubblicare una sequenza comunale omogenea. Il sito mantiene quindi soltanto l’ultima annualità verificata.</p></div>`;
    }
    const years = [...new Set(historicalRows.flatMap(row => seriesFor(row).years))].sort((a, b) => Number(a) - Number(b));
    return `${metric.meta.key === 'income' ? `<p class="brain-drain-note">${html(metric.meta.longHistoryNote)}</p>` : ''}<div class="indicator-table-scroll"><table class="indicator-history-table"><thead><tr><th scope="col">Comune</th>${years.map(year => `<th scope="col">${html(year)}</th>`).join('')}</tr></thead><tbody>${historicalRows.sort((a, b) => a.town.localeCompare(b.town, 'it')).map(row => {
      const series = seriesFor(row);
      const values = new Map(series.years.map((year, index) => [String(year), series.values[index]]));
      return `<tr><th scope="row">${html(row.town)}</th>${years.map(year => `<td>${values.has(String(year)) ? html(formatValue(values.get(String(year)), metric.meta.key === 'income' ? 'currency' : metric.meta.unit)) : '—'}</td>`).join('')}</tr>`;
    }).join('')}</tbody></table></div>`;
  }

  function renderIndicator(data, registry, monitorState) {
    const metric = data.metrics[pageMetric];
    if (!metric) return renderNotFound();
    const theme = data.themes[metric.meta.theme];
    if (!theme) return renderNotFound();
    const policy = resolveSourcePolicy(pageMetric, metric, registry);
    const metricMonitorState = monitorState?.metrics?.[pageMetric];
    const checkedAt = metricMonitorState?.checkedAt
      ? new Intl.DateTimeFormat('it-IT', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(metricMonitorState.checkedAt))
      : 'Controllo non ancora registrato';
    const historyCount = metric.rows.filter(row => row.series?.years?.length).length;
    const license = policy.licenseUrl
      ? `<a href="${html(policy.licenseUrl)}" target="_blank" rel="noreferrer">${html(policy.licenseName)} ↗</a>`
      : html(policy.licenseName || 'Condizioni indicate dalla fonte');

    app.innerHTML = `<main class="inner-page indicator-page" data-theme="${html(theme.key)}">
      <nav class="breadcrumbs page-width" aria-label="Percorso"><a href="${route('')}">Home</a><span>›</span><a href="${route(`confronta/${theme.key}/`)}">${html(theme.label)}</a><span>›</span><strong>${html(metric.meta.label)}</strong></nav>
      <section class="indicator-hero page-width"><div><span class="overline">Indicatore · ${html(theme.label)}</span><h1>${html(metric.meta.label)}</h1><p>${html(metric.meta.description)}</p></div>
        <dl><div><dt>Anno</dt><dd>${html(metric.meta.year)}</dd></div><div><dt>Copertura</dt><dd>${html(metric.method?.coverage || '7/7')}</dd></div><div><dt>Serie storica</dt><dd>${historyCount ? `${historyCount}/7 comuni` : 'Non disponibile'}</dd></div></dl>
        <div class="indicator-hero-actions"><a class="button-link" href="${route(`confronta/${theme.key}/?indicatore=${pageMetric}`)}">Confronta i 7 comuni <span>→</span></a><a class="source-pill" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte originale ↗</a></div></section>
      <section class="indicator-current page-width" aria-labelledby="indicator-current-title"><div class="section-heading"><div><span class="overline">Valori comunali</span><h2 id="indicator-current-title">Il dato nei sette comuni</h2></div><p>Ordine alfabetico: nessuna graduatoria e nessun giudizio di merito.</p></div>
        <div class="indicator-current-layout">${indicatorComparisonTable(data, pageMetric)}<aside><span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p></aside></div></section>
      <section class="indicator-benchmark page-width">${benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>
      <section class="indicator-history page-width" aria-labelledby="indicator-history-title"><div class="section-heading"><div><span class="overline">Andamento</span><h2 id="indicator-history-title">Serie storica comunale</h2></div><p>I valori compaiono soltanto quando la definizione resta omogenea nel tempo.</p></div>${indicatorHistoryTable(metric)}</section>
      <section class="indicator-method page-width" aria-labelledby="indicator-method-title"><div class="section-heading"><div><span class="overline">Trasparenza</span><h2 id="indicator-method-title">Fonte, aggiornamento e metodo</h2></div><p>Le informazioni necessarie per ricostruire e valutare il dato.</p></div>
        <div class="indicator-governance-grid"><dl><div><dt>Produttore</dt><dd>${html(policy.publisher || metric.meta.source)}</dd></div><div><dt>Fonte utilizzata</dt><dd><a href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">${html(metric.meta.source)} ↗</a></dd></div><div><dt>Frequenza</dt><dd>${html(policy.frequencyLabel || 'Secondo la fonte')}</dd></div><div><dt>Prossimo aggiornamento atteso</dt><dd>${html(policy.expectedRelease || 'Secondo il calendario della fonte')}</dd></div><div><dt>Ultimo controllo della fonte</dt><dd>${html(checkedAt)}</dd></div><div><dt>Licenza o condizioni di riuso</dt><dd>${license}</dd></div></dl>
          <div><h3>Acquisizione</h3><p>${html(policy.acquisitionMethod || 'Verifica manuale della fonte ufficiale.')}</p>${methodDisclosure(metric)}</div></div>
        <div class="data-actions indicator-data-actions"><button type="button" data-share>Condividi</button><button type="button" data-download>Scarica CSV</button><button type="button" data-print>Stampa / PDF</button></div></section>
      <section class="topic-town-links page-width"><div><span class="overline">Schede comunali</span><h2>Apri il territorio</h2></div><div>${[...metric.rows].sort((a, b) => a.town.localeCompare(b.town, 'it')).map(row => `<a href="${route(`comuni/${row.slug}/?tema=${theme.key}&indicatore=${pageMetric}`)}"><span>${html(row.town)}</span><b>→</b></a>`).join('')}</div></section>
    </main>`;

    document.querySelector('[data-share]')?.addEventListener('click', event => shareCurrentPage(event.currentTarget));
    document.querySelector('[data-download]')?.addEventListener('click', () => downloadMetricCSV(data, pageMetric));
    document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  }

  function renderProject(data) {
    const sources = [
      ['Istat','https://www.istat.it/'],['Istat — Frame SBS Territoriale',data.businessSource],['Eurostat','https://ec.europa.eu/eurostat/'],['Regione Toscana','https://www.regione.toscana.it/statistiche'],['Ministero dell’economia e delle finanze','https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'],['ARS Toscana — La salute dei comuni',data.arsSource],['ISPRO — Registro di mortalità regionale','https://www.ispro.toscana.it/registro-mortalita-regionale-rmr'],['ISPRA','https://www.isprambiente.gov.it/'],['Regione Toscana — RTCave','https://cave.regione.toscana.it/'],['Regione Toscana — Piano Regionale Cave','https://www.regione.toscana.it/piano-regionale-cave'],['MIT / SID — Il Portale del Mare','https://dati.mit.gov.it/catalog/dataset/concessioni-demaniali-marittime-a-agosto-2026'],['BDAP','https://openbdap.rgs.mef.gov.it/'],['SIOPE','https://www.siope.it/'],['Italia Domani — Open data PNRR','https://www.italiadomani.gov.it/it/catalogo-open-data.html'],['ANAC — Open data','https://dati.anticorruzione.it/opendata'],['Cruscotto Italia — AgID','https://cruscotto-italia.dati.gov.it/']
    ];
    const versions = [
      ['2026.09.01-v1.27.0','1 settembre 2026','177 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunte Concessioni demaniali marittime e Canoni demaniali dovuti dallo snapshot MIT/SID agosto 2026, con selector Totale / Turistico-ricreative e copertura 4 Comuni costieri + 3 n.a. Superficie, metri e quota di litorale restano rinviati per incompletezza geometrica.'],
      ['2026.08.31-v1.26.0','31 agosto 2026','175 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Lotto Bonifica e rischio idraulico: indicatori PAB 2026, reticolo in gestione DCRT 24/2025, opere idrauliche DGRT 1155/2021 e stato operativo degli interventi al 31 agosto 2026. Restano rinviati soltanto i km fisici unici manutenzionati e la relativa quota di reticolo, perché 49 feature operative non espongono geometria.'],
      ['2026.08.30-v1.25.0','30 agosto 2026','166 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunta Morosità ERP: serie 2020–2024 dai bilanci E.R.P. Lucca, percentuali ricalcolate dagli importi elementari e dettaglio contabile 2024 per ciascun Comune.'],
      ['2026.08.29-v1.24.0','29 agosto 2026','165 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto Acqua e bonifiche: perdite della rete idrica Istat, qualità dell’acqua potabile GAIA per 70 località e procedimenti SISBON attivi/chiusi, senza proxy per fognatura o depurazione.'],
      ['2026.08.28-v1.23.0','28 agosto 2026','162 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Costa e mare: qualità delle aree di balneazione, campioni non conformi, spiagge Bandiera Blu, dinamica del litorale e costa protetta da opere rigide, con 4 Comuni costieri e 3 n.a. senza stime.'],
      ['2026.08.28-v1.22.0','28 agosto 2026','157 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Estesa la Speranza di vita alla nascita con serie ufficiali ARS 2008–2022 per Totale, Maschi e Femmine, aggregato ufficiale Versilia e benchmark Toscana.'],
      ['2026.08.27-v1.21.0','27 agosto 2026','157 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti tre indicatori Cultura e biblioteche della Regione Toscana 2024: prestiti per residente, utenti attivi del prestito ogni 100 residenti e ore medie di apertura settimanale, con copertura corrente 5/7 e serie storiche ufficiali senza stime.'],
      ['2026.08.26-v1.20.0','26 agosto 2026','154 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto Agricoltura e territorio: aziende agricole, SAU territoriale e quota comunale, dimensione media aziendale, profilo colture e superficie irrigata dal 7° Censimento Istat 2020.'],
      ['2026.08.26-v1.19.0','26 agosto 2026','149 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti tre indicatori TPL programmato 7/7 da GTFS regionali: corse, punti di accesso attivi e ampiezza oraria del servizio.'],
      ['2026.08.25-v1.18.0','25 agosto 2026','146 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti Welfare e servizi sociali (spesa per abitante e composizione per area di utenza) e Prima infanzia (ricettività potenziale 3–36 mesi).'],
      ['2026.08.24-v1.17.0','24 agosto 2026','143 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Scuola MIM: sicurezza documentale, accessibilità, mensa e palestra, epoca di costruzione e raggiungibilità dei 109 edifici scolastici censiti nei sette Comuni.'],
      ['2026.08.24-v1.16.0','24 agosto 2026','138 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Canonicalizzato il catalogo effettivamente pubblicato; completati Demografia, Redditi, Fiscalità, Amministrazione e letture per età e genere; riallineati versioni, controlli e metadati.'],
      ['2026.08.20-v1.15.0','20 agosto 2026','132 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Completato il Lotto A Redditi con profilo delle fonti, dettaglio delle fasce, peso delle pensioni e rapporto tra contribuenti e popolazione maggiorenne.'],
      ['2026.08.20-v1.14.0','20 agosto 2026','129 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiornata la Demografia con dinamica naturale, indici di dipendenza, distribuzione 2026, piramide per età e sesso e dettaglio dei residenti stranieri.'],
      ['2026.08.16-v1.13.0','16 agosto 2026','127 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Estesi redditi e costo della vita con serie MEF 2011–2024, redditi vs inflazione, fiscalità locale standardizzata, carburanti e costo del servizio rifiuti.'],
      ['2026.08.14-v1.12.0','14 agosto 2026','121 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Rafforzato Sicurezza e territorio con sicurezza stradale, Missione 03 e proventi del Codice della strada.'],
      ['2026.08.14-v1.11.0','14 agosto 2026','119 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti residenti stranieri, mobilità residenziale con l’estero e complessiva, quotazioni immobiliari OMI e il contesto sulla mobilità dei laureati.'],
      ['2026.08.14-v1.10.0','14 agosto 2026','115 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Integrate distribuzione per fasce d’età, mobilità residenziale interna e distribuzione dei dichiaranti per fascia di reddito.'],
      ['2026.08.12-v1.9.0','12 agosto 2026','115 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Integrati Percorsi e mobilità lenta nel dataset principale e separato il tema Sicurezza e territorio.'],
      ['2026.08.09-v1.8.0','9 agosto 2026','106 indicatori. Aggiunte 106 schede canoniche degli indicatori, politica esplicita di aggiornamento delle fonti e sette serie comunali Istat omogenee 2021–2023.'],
      ['2026.08.07-v1.7.0','7 agosto 2026','106 indicatori. Aggiunti dettaglio ISTAT ASIA su unità locali, addetti e settori ATECO, dati AGCOM FTTH verificati e controlli automatici rafforzati sulle fonti.'],
      ['2026.08.05-v1.6.0','5 agosto 2026','98 indicatori. Aggiunto il tema Bilanci comunali con rendiconto 2024–2025, capacità di riscossione e pagamento, risultato di amministrazione e spesa per missione.'],
      ['2026.08.3','2 agosto 2026','51 indicatori. Ampliata la salute con speranza di vita, mortalità, cronicità, pronto soccorso, ricoveri e assistenza domiciliare, usando tassi comunali e aggregati ufficiali ARS Toscana.'],
      ['2026.08.2','2 agosto 2026','43 indicatori. Aggiunti valore aggiunto delle unità locali, produttività per addetto e quote dell’industria, con confronti omogenei Toscana–Italia e perimetro distinto dal PIL.'],
      ['2026.08.1','2 agosto 2026','39 indicatori e nuovi approfondimenti comunali su struttura economica, pendolarismo reale, pressioni ambientali, cassa pubblica, opere, PNRR e contratti.'],
      ['2026.08','agosto 2026','7 comuni, 9 temi e 27 indicatori con fonti dirette, confronti ponderati, valori normalizzati ed esportazione CSV.'],
      ['2026.07','luglio 2026','Prima raccolta strutturata e prototipo delle viste comparative e comunali.']
    ];
    app.innerHTML = `<main class="editorial-page"><section class="editorial-hero page-width"><span class="overline">Il progetto</span><h1>Un solo posto per capire la Versilia.</h1><p>I dati pubblici esistono, ma spesso sono dispersi tra portali, allegati e fogli di calcolo. Osservatorio Versilia li riunisce, li spiega e li rende confrontabili senza nasconderne limiti e provenienza.</p></section>
      <section class="project-story page-width"><div><span class="section-number">01</span><h2>Perché nasce</h2></div><div class="prose"><p>Per trovare un numero comunale non dovrebbe essere necessario conoscere decine di banche dati, interpretare formati diversi o ricostruire ogni volta il significato di una voce.</p><p>Il progetto è ideato e curato da <strong>Emanuele Anzilotti</strong> con un obiettivo semplice: offrire un punto di accesso chiaro ai dati che aiutano a leggere i sette comuni della Versilia storica e il territorio nel suo insieme.</p></div></section>
      <section class="independence-note page-width" aria-label="Natura del progetto"><div><span class="overline">Un progetto civico indipendente</span><h2>Le fonti sono istituzionali.<br>L’osservatorio non lo è.</h2></div><p>Osservatorio Versilia non rappresenta Comuni, Provincia, Regione, Istat o altri enti citati. Le amministrazioni e gli istituti produttori restano la fonte autorevole dei dati; eventuali errori di trascrizione, elaborazione o interpretazione sono responsabilità del progetto.</p></section>
      <section class="method-detail page-width" id="metodo"><div class="section-heading"><div><span class="section-number">02</span><h2>Il metodo</h2></div><p>Cinque regole per evitare confronti solo apparentemente precisi.</p></div><ol class="principles-grid">
        ${[['Scala certa','Un dato entra nelle schede comunali solo quando è davvero disponibile a quel livello territoriale.'],['Contesto visibile','Anno, unità, definizione e fonte accompagnano sempre il numero.'],['Confronti omogenei','Toscana e Italia compaiono soltanto quando perimetro e periodo sono compatibili.'],['Aggregazioni dichiarate','Totali e medie della Versilia indicano come sono stati calcolati, incluse le ponderazioni.'],['Nessun voto','Posizioni e distanze descrivono i valori: non diventano pagelle o giudizi politici automatici.']].map((x,i)=>`<li><span>0${i+1}</span><h3>${x[0]}</h3><p>${x[1]}</p></li>`).join('')}</ol></section>
      <section class="source-directory page-width"><div><span class="section-number">03</span><h2>Le fonti</h2></div><div><p>Ogni indicatore rimanda alla propria fonte. Tra i principali produttori e portali utilizzati:</p><ul>${sources.map(([name,url])=>`<li><a href="${html(url)}" target="_blank" rel="noreferrer">${html(name)} <span>↗</span></a></li>`).join('')}</ul></div></section>
      <section class="license-section page-width" id="licenza"><div><span class="section-number">04</span><h2>Licenza e riuso</h2></div><div class="prose"><p>Salvo diversa indicazione, testi, elaborazioni e visualizzazioni originali di Osservatorio Versilia sono disponibili con licenza <a href="https://creativecommons.org/licenses/by/4.0/deed.it" target="_blank" rel="noreferrer">CC BY 4.0</a>: possono essere condivisi e adattati citando la fonte.</p><p>Dati, stemmi, fotografie e materiali di terzi mantengono le condizioni d’uso e le licenze indicate dai rispettivi titolari. Per un uso ufficiale o amministrativo va sempre consultata la fonte originaria.</p></div></section>
      <section class="versions-section page-width" id="versioni"><div><span class="section-number">05</span><h2>Versioni dei dati</h2></div><div class="version-list">${versions.map(v=>`<article><div><strong>${v[0]}</strong><time>${v[1]}</time></div><p>${v[2]}</p></article>`).join('')}<p class="update-policy">Le correzioni puntuali possono essere pubblicate subito; gli aggiornamenti organici ricevono un nuovo numero di versione e una data visibile in tutto il sito.</p></div></section>
      <section class="contact-panel page-width"><div><span class="overline">Manca qualcosa?</span><h2>Un osservatorio migliora anche grazie alle segnalazioni.</h2></div><div><p>Puoi indicare un errore, una fonte più recente o proporre un nuovo indicatore comunale verificabile.</p><a class="button-link" href="${route('segnala/')}">Invia una segnalazione</a><a class="plain-contact" href="mailto:info@osservatorioversilia.it">info@osservatorioversilia.it</a></div></section>
    </main>`;
  }

  function renderFeedback(data) {
    app.innerHTML = `<main class="editorial-page"><section class="editorial-hero compact page-width"><span class="overline">Segnala</span><h1>Un dato da correggere o aggiungere?</h1><p>Indica l’informazione, il territorio e possibilmente una fonte verificabile. Il modulo prepara un’email nel programma di posta del dispositivo: non salva dati sul sito.</p></section>
      <section class="feedback-layout page-width"><aside><span class="overline">Prima di inviare</span><h2>Più dettagli dai, più semplice sarà verificare.</h2><ul><li>Indica il comune o se riguarda tutta la Versilia.</li><li>Scrivi il nome dell’indicatore o del tema.</li><li>Allega nel testo un link alla fonte istituzionale.</li><li>Spiega con precisione cosa non torna.</li></ul><p>Puoi anche scrivere direttamente a <a href="mailto:info@osservatorioversilia.it">info@osservatorioversilia.it</a>.</p></aside>
        <form class="feedback-form"><div class="form-row"><label>Tipo di segnalazione<select name="category" required><option value="" disabled selected>Seleziona</option><option>Errore o dato da correggere</option><option>Nuovo indicatore</option><option>Fonte o dato più recente</option><option>Suggerimento sul sito</option></select></label><label>Comune o territorio<select name="town" required>${['Tutta la Versilia',...data.towns.map(t=>t.name)].map(x=>`<option>${html(x)}</option>`).join('')}</select></label></div>
        <label>Indicatore o tema<input name="indicator" placeholder="Es. popolazione residente, viabilità, istruzione"></label><label>Link alla fonte<input name="source" type="url" inputmode="url" placeholder="https://…"></label><label>Cosa vuoi segnalare?<textarea name="message" rows="7" required placeholder="Descrivi il dato, l’errore o il suggerimento con le informazioni utili per verificarlo."></textarea></label>
        <div class="form-row"><label>Nome <span>(facoltativo)</span><input name="name" autocomplete="name"></label><label>Email <span>(facoltativa)</span><input name="email" type="email" autocomplete="email"></label></div><div class="form-submit"><button type="submit">Prepara l’email</button><p>Il modulo non salva né invia dati: apre il programma di posta del tuo dispositivo con un messaggio già compilato.</p></div><p class="form-status" role="status" hidden>Email preparata. Se non si è aperto nulla, scrivi a info@osservatorioversilia.it.</p></form></section></main>`;
    const form = document.querySelector('.feedback-form');
    form.addEventListener('submit', event => {
      event.preventDefault(); const fd = new FormData(form);
      const category = String(fd.get('category') || ''), town = String(fd.get('town') || '');
      const subject = `[Osservatorio Versilia] ${category} · ${town}`;
      const body = [`Tipo: ${category}`,`Comune/territorio: ${town}`,`Indicatore o tema: ${fd.get('indicator') || 'non specificato'}`,`Fonte proposta: ${fd.get('source') || 'non specificata'}`,'',String(fd.get('message') || ''),'',`Nome: ${fd.get('name') || 'non indicato'}`,`Email: ${fd.get('email') || 'non indicata'}`].join('\n');
      document.querySelector('.form-status').hidden = false;
      location.href = `mailto:info@osservatorioversilia.it?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
  }

  function isClimateMetric(data, metricKey) {
    return data.metrics?.[metricKey]?.dataStorage?.type === 'external-climate';
  }

  function climateDetailHref(data, metricKey, town = '') {
    const detail = data.metrics?.[metricKey]?.meta?.climateDetail || { indicator: 'temperature', hash: '' };
    const params = new URLSearchParams();
    if (town) params.set('comune', town);
    params.set('indicatore', detail.indicator);
    return `${route(`confronta/meteo-clima/?${params.toString()}`)}${detail.hash}`;
  }

  const baseFormatValue = formatValue;
  formatValue = (value, unit) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'n.d.';
    const v = Number(value);
    if (unit === 'climateCelsius') return `${number2.format(v)} °C`;
    if (unit === 'climateMm') return `${number0.format(v)} mm`;
    return baseFormatValue(value, unit);
  };

  const baseBarRows = barRows;
  barRows = (data, metricKey, options = {}) => {
    if (!isClimateMetric(data, metricKey)) return baseBarRows(data, metricKey, options);
    const normalized = Boolean(options.normalized);
    const selectedTown = options.selectedTown || '';
    const rows = metricRows(data, metricKey, normalized).slice().sort((a, b) => a.town.localeCompare(b.town, 'it'));
    const maxAbs = Math.max(...rows.map(row => Math.abs(Number(row.displayValue) || 0)), 0.0001);
    return rows.map(row => {
      const query = new URLSearchParams({ tema: data.metrics[metricKey].meta.theme, indicatore: metricKey });
      const href = route(`comuni/${row.slug}/?${query}`);
      const value = Number(row.displayValue) || 0;
      const extent = Math.min(50, Math.abs(value) / maxAbs * 50);
      const left = value < 0 ? 50 - extent : 50;
      const fill = value < 0 ? '#7894a0' : '#4f8162';
      return `<a href="${href}" class="bar-row ${row.slug === selectedTown ? 'selected' : ''}" aria-label="${html(row.town)}: ${html(formatValue(row.displayValue, row.displayUnit))}">
        <span aria-hidden="true"></span><span class="bar-town">${html(row.town)}</span>
        <span class="bar-track" style="position:relative"><span aria-hidden="true" style="position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:#6f8088;opacity:.75"></span><span class="bar-fill" style="position:absolute;left:${left.toFixed(2)}%;width:${extent.toFixed(2)}%;background:${fill};min-width:${extent ? '2px' : '0'}"></span>
          <span class="bar-hover-label">${html(row.town)} · ${html(formatValue(row.displayValue, row.displayUnit))}</span></span>
        <strong>${html(formatValue(row.displayValue, row.displayUnit))}</strong>
      </a>`;
    }).join('');
  };

  function linearClimateTrend(years, values, fromYear, toYear) {
    const pairs = years.map((year, index) => ({ year: Number(year), value: Number(values[index]) }))
      .filter(item => item.year >= fromYear && item.year <= toYear && Number.isFinite(item.value));
    if (pairs.length < 2) return null;
    const meanX = pairs.reduce((sum, item) => sum + item.year, 0) / pairs.length;
    const meanY = pairs.reduce((sum, item) => sum + item.value, 0) / pairs.length;
    const denominator = pairs.reduce((sum, item) => sum + (item.year - meanX) ** 2, 0);
    if (!denominator) return null;
    const slope = pairs.reduce((sum, item) => sum + (item.year - meanX) * (item.value - meanY), 0) / denominator;
    const intercept = meanY - slope * meanX;
    const start = intercept + slope * fromYear;
    const end = intercept + slope * toYear;
    return { slope, start, end, delta: end - start, perDecade: slope * 10, count: pairs.length };
  }

  function climateRowIdentity(data, townName) {
    const town = data.towns.find(item => item.name === townName);
    if (!town) return null;
    return { town: town.name, code: town.code, slug: normalize(town.name).replaceAll(' ', '-') };
  }

  function meanClimateValue(rows, selector = row => row.value) {
    const values = rows.map(selector).map(Number).filter(Number.isFinite);
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  }

  function buildLongClimateMetric(data, climate, metric) {
    const config = metric.dataStorage;
    const rows = Object.entries(climate.municipalities).map(([townName, series]) => {
      const identity = climateRowIdentity(data, townName);
      if (!identity) return null;
      const values = series[config.seriesKey];
      const trend = linearClimateTrend(series.years, values, config.trendFrom, config.trendTo);
      if (!trend) return null;
      const row = {
        ...identity,
        value: Number(trend.delta.toFixed(config.decimals)),
        formatted: '',
        series: { years: [...series.years], values: [...values] },
        normalized: null,
        benchmarkValue: null
      };
      if (config.normalizedPercent) {
        const percent = trend.start ? trend.delta / trend.start * 100 : null;
        row.normalized = Number.isFinite(percent) ? { value: Number(percent.toFixed(2)), unit: 'percent', label: 'Variazione percentuale del trend' } : null;
      }
      return row;
    }).filter(Boolean);

    const hydrated = {
      ...metric,
      rows,
      aggregate: {
        ...metric.aggregate,
        value: meanClimateValue(rows),
      },
      normalizedAggregate: null
    };

    if (config.normalizedPercent) {
      hydrated.normalizedAggregate = {
        ...metric.normalizedAggregate,
        value: meanClimateValue(rows, row => row.normalized?.value),
      };
    }
    return hydrated;
  }

  function buildMinMaxClimateMetric(data, minmax, metric) {
    const config = metric.dataStorage;
    const rows = Object.entries(minmax.municipalities).map(([townName, series]) => {
      const identity = climateRowIdentity(data, townName);
      if (!identity) return null;
      const values = series[config.seriesKey];
      const trend = linearClimateTrend(series.years, values, config.trendFrom, config.trendTo);
      if (!trend) return null;
      return {
        ...identity,
        value: Number(trend.delta.toFixed(config.decimals)),
        formatted: '',
        series: { years: [...series.years], values: [...values] },
        normalized: null,
        benchmarkValue: null
      };
    }).filter(Boolean);

    return {
      ...metric,
      rows,
      aggregate: {
        ...metric.aggregate,
        value: meanClimateValue(rows),
      },
      normalizedAggregate: null,
    };
  }

  function enrichClimateData(data, datasets) {
    Object.entries(data.metrics).forEach(([metricKey, metric]) => {
      if (!isClimateMetric(data, metricKey)) return;
      const storage = metric.dataStorage;
      const dataset = datasets[storage.path];
      if (!dataset?.municipalities) return;
      if (storage.builder === 'annual-trend') {
        data.metrics[metricKey] = buildLongClimateMetric(data, dataset, metric);
      } else if (storage.builder === 'minmax-trend') {
        data.metrics[metricKey] = buildMinMaxClimateMetric(data, dataset, metric);
      }
    });
  }

  function syncEnvironmentClimateUi(data) {
    const metricKey = new URLSearchParams(location.search).get('indicatore');
    const climate = isClimateMetric(data, metricKey);

    if (pageType === 'compare' && pageTheme === 'ambiente') {
      const benchmark = document.getElementById('compare-benchmark');
      if (benchmark) benchmark.hidden = climate;
    }

    if (pageType === 'town') {
      const profile = document.querySelector('main.town-profile');
      if (profile?.dataset.theme === 'ambiente') {
        const deep = profile.querySelector('.topic-deep-dive');
        const isFlood = metricKey === 'floodExposure';
        const isLandslide = metricKey === 'landslideExposure';
        if (deep) {
          deep.hidden = !(isFlood || isLandslide);
          if (isFlood || isLandslide) {
            const heading = deep.querySelector('.deep-heading h3');
            const intro = deep.querySelector('.deep-heading p');
            if (heading && heading.textContent !== (isFlood ? 'Dettaglio del rischio alluvionale' : 'Dettaglio del rischio frane')) {
              heading.textContent = isFlood ? 'Dettaglio del rischio alluvionale' : 'Dettaglio del rischio frane';
            }
            const introText = isFlood
              ? 'Edifici comunali esposti al rischio alluvionale secondo il dettaglio territoriale disponibile.'
              : 'Edifici comunali esposti al rischio frane secondo il dettaglio territoriale disponibile.';
            if (intro && intro.textContent !== introText) intro.textContent = introText;
            const details = deep.querySelector('details');
            if (details) details.open = true;
            [...deep.querySelectorAll('.risk-grid article')].forEach((article, index) => {
              article.hidden = isFlood ? index !== 0 : index !== 1;
            });
          }
        }
        const townBenchmark = profile.querySelector('.town-benchmark');
        if (townBenchmark) townBenchmark.hidden = climate;
      }
    }

    if (climate) {
      const town = pageType === 'town' ? document.querySelector('.town-hero h1')?.textContent?.trim() : '';
      const href = climateDetailHref(data, metricKey, town);
      document.querySelectorAll('.data-actions a').forEach(link => {
        if (link.textContent.includes('Scheda indicatore') || link.textContent.includes('Approfondimento storico')) {
          if (link.href !== href) link.href = href;
          if (link.textContent !== 'Approfondimento storico') link.textContent = 'Approfondimento storico';
        }
      });
    }
  }

  function installEnvironmentClimateCoherence(data) {
    syncEnvironmentClimateUi(data);
    if (!app) return;
    const scheduleSync = () => queueMicrotask(() => syncEnvironmentClimateUi(data));
    app.addEventListener('click', event => {
      if (event.target.closest('[data-metric], [data-profile-theme], [data-scale]')) scheduleSync();
    });
    app.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'Enter', ' '].includes(event.key)) return;
      if (event.target.closest('[data-metric], [data-profile-theme], [data-scale]')) scheduleSync();
    });
  }

  function installSearch(data) {
    const trigger = document.querySelector('.global-search-trigger');
    const categories = ['Indicatori comunali','Contesti sovracomunali','Temi','Comuni'];
    const items = [
      ...Object.entries(data.metrics).map(([key,m]) => ({ id:`metric-${key}`, label:m.meta.label, description:`${data.themes[m.meta.theme].label} · ${m.meta.year} · ${m.meta.description}`, category:'Indicatori comunali', href:isClimateMetric(data, key) ? climateDetailHref(data, key) : indicatorHref(m), badge:data.themes[m.meta.theme].label, keywords:normalize([m.meta.label,m.meta.shortLabel,m.meta.description,m.meta.source,data.themes[m.meta.theme].label,...(m.meta.searchTerms||[]),...(searchSynonyms[key]||[])].join(' ')) })),
      { id:'context-crime', label:'Criminalità e delitti denunciati', description:'Provincia di Lucca, Toscana e Italia · 2024. Il dato non è disponibile in forma omogenea per comune.', category:'Contesti sovracomunali', href:route('confronta/sicurezza/#criminalita'), badge:'Dato provinciale', keywords:normalize('criminalità reati delitti furti truffe sicurezza provincia lucca') },
      { id:'context-brain-drain', label:'Mobilità dei laureati italiani 25–39 anni', description:'Provincia di Lucca e confronto toscano · 2023. Contesto sovracomunale BesT.', category:'Contesti sovracomunali', href:route('confronta/demografia/#mobilita-laureati'), badge:'Dato provinciale', keywords:normalize('brain drain fuga cervelli laureati giovani emigrazione provincia lucca capitale umano') },
      ...Object.values(data.themes).map(t => ({ id:`theme-${t.key}`, label:t.label, description:`${t.question} ${t.description}`, category:'Temi', href:route(`confronta/${t.key}/`), badge:`${t.metrics.length} indicatori`, keywords:normalize(`${t.label} ${t.question} ${t.description}`) })),
      ...data.towns.map(t => ({ id:`town-${t.code}`, label:t.name, description:`Profilo comunale · codice Istat ${t.code}`, category:'Comuni', href:route(`comuni/${normalize(t.name).replaceAll(' ','-')}/`), badge:'Comune', keywords:normalize(`${t.name} comune territorio codice Istat ${t.code}`) }))
    ];
    const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','metric-roadInjuries','context-crime','context-brain-drain']);
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

  async function readOptionalJson(path) {
    try {
      const item = await fetch(asset(path));
      return item.ok ? item.json() : null;
    } catch (_error) {
      return null;
    }
  }

  async function start() {
    try {
      const response = await fetch(asset('data/site-data.json'));
      if (!response.ok) throw new Error(`Errore ${response.status}`);
      const data = await response.json();

      if (['home', 'compare', 'town'].includes(pageType)) {
        const paths = [...new Set(Object.values(data.metrics)
          .filter(metric => metric.dataStorage?.type === 'external-climate')
          .map(metric => metric.dataStorage.path))];
        const loaded = await Promise.all(paths.map(async path => [path, await readOptionalJson(path)]));
        enrichClimateData(data, Object.fromEntries(loaded.filter(([, dataset]) => dataset)));
      }

      let sourceRegistry = null;
      let monitorState = null;
      if (pageType === 'indicator') {
        [sourceRegistry, monitorState] = await Promise.all([
          readOptionalJson('data/source-registry.json'),
          readOptionalJson('data/source-monitor-state.json')
        ]);
      }
      mountShell(data);
      if (pageType === 'home') renderHome(data);
      else if (pageType === 'compare') renderCompare(data);
      else if (pageType === 'town') renderTown(data);
      else if (pageType === 'indicator') renderIndicator(data, sourceRegistry, monitorState);
      else if (pageType === 'project') renderProject(data);
      else if (pageType === 'feedback') renderFeedback(data);
      else if (['status', 'pnrr', 'special'].includes(pageType)) {
        /* Contenuto prerenderizzato: monta shell e ricerca senza sostituire #app. */
      } else renderNotFound();
      if (['compare', 'town'].includes(pageType)) installEnvironmentClimateCoherence(data);
    } catch (error) {
      console.error(error);
      app.innerHTML = `<div class="app-error"><strong>Impossibile caricare i dati.</strong><p>Controlla che il sito sia aperto tramite un server web e non direttamente come file locale.</p></div>`;
    }
  }

  start();
})();
