(() => {
  'use strict';

  const scriptUrl = document.currentScript?.src || new URL('assets/visual-grammar.js', document.baseURI).href;
  const dataUrl = new URL('../data/site-data.json', scriptUrl).href;
  const projectSystemUrl = new URL('../progetto/#sistema-territoriale', scriptUrl).href;
  const number1 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number0 = new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 });
  let data = null;
  let scheduled = false;

  const scopeProfiles = {
    administrative: {
      label: 'Amministrativo',
      description: 'Il confine comunale è parte del fenomeno osservato: il dato misura attività, risorse o servizi attribuiti direttamente all’amministrazione o al perimetro comunale.'
    },
    territorial: {
      label: 'Territoriale',
      description: 'Il dato descrive residenti, stock o fenomeni localizzati nel Comune. Il confine è utile per leggere il territorio, ma non implica che il Comune sia un sistema autonomo.'
    },
    functional: {
      label: 'Funzionale',
      description: 'Il fenomeno supera strutturalmente i confini comunali. Il valore indica dove persone, imprese o servizi sono localizzati o censiti, non delimita un sistema economico-sociale autonomo.'
    }
  };

  const themeScopeDefaults = {
    demografia: 'territorial',
    economia: 'functional',
    lavoro: 'functional',
    istruzione: 'territorial',
    salute: 'functional',
    mobilita: 'functional',
    abitare: 'territorial',
    ambiente: 'territorial',
    bilanci: 'administrative',
    comunita: 'administrative'
  };

  const administrativeMetrics = new Set([
    'currentRevenueAccruedPerResident',
    'currentExpenditureCommittedPerResident',
    'capitalExpenditureCommittedPerResident',
    'ownRevenueShare',
    'currentCollectionCapacity',
    'currentPaymentCapacity',
    'availableAdministrationResultPerResident',
    'rigidExpenditureShare',
    'currentPayments',
    'capitalPayments',
    'siopePayments',
    'educationMissionExpenditurePerResident',
    'socialMissionExpenditurePerResident',
    'environmentMissionExpenditurePerResident',
    'mobilityMissionExpenditurePerResident',
    'cultureSportMissionExpenditurePerResident',
    'tourismDevelopmentMissionExpenditurePerResident',
    'publicWorks',
    'pnrrFunding',
    'pnrrConcluded',
    'recycling',
    'wastePerResident',
    'residualWaste'
  ]);

  const territorialMetrics = new Set([
    'income',
    'incomeUnder15k',
    'diplomaPlus',
    'tertiary',
    'lifeExpectancy',
    'mortalityAll',
    'chronicTotal',
    'diabetes',
    'dementia',
    'disability064Per1000',
    'motorization',
    'pollutingCars',
    'evPoints',
    'ftthCoverageDesi',
    'ftthReachedHouseholds',
    'ftthUnreachedHouseholds',
    'ftthCoverage20m',
    'roadInjuries',
    'thirdSector'
  ]);

  const functionalMetrics = new Set([
    'schoolSites',
    'schoolStudents',
    'studentsPerClass',
    'primaryFullTimeShare',
    'emergencyAccess',
    'emsResponseTimeP75',
    'hospitalizedAll',
    'elderlyHomeCare',
    'pharmaciesPer1000',
    'hospitals'
  ]);

  function unitKind(unit) {
    const token = String(unit || '').trim().toLowerCase();
    if (token === 'percent' || token === '%') return 'percent';
    if (token === 'percentagepoints' || token === 'percentage-points' || token === 'p.p.') return 'percentage-points';
    if (token === 'currency' || token === 'eur' || token === '€' || token === '€/ab.') return 'currency';
    return token;
  }

  function metricKeyFor(root) {
    const home = root.closest?.('#home-explorer');
    const dashboard = root.closest?.('.topic-dashboard');
    const townTopic = root.closest?.('#town-topic');
    const local = home || dashboard || townTopic;
    const active = local?.querySelector('[data-metric].active, [data-metric][aria-selected="true"]');
    if (active?.dataset.metric) return active.dataset.metric;
    return new URLSearchParams(location.search).get('indicatore');
  }

  function normalizedFor(root) {
    const dashboard = root.closest?.('.topic-dashboard');
    return Boolean(dashboard?.querySelector('[data-scale="normalized"].active'));
  }

  function townRow(metric, townName) {
    return metric?.rows?.find(row => row.town === townName) || null;
  }

  function valueFor(row, metric, normalized) {
    if (!row) return null;
    return normalized && row.normalized ? row.normalized.value : row.value;
  }

  function unitFor(row, metric, normalized) {
    if (normalized && row?.normalized) return row.normalized.unit;
    if (normalized && metric?.meta?.normalized) return metric.meta.normalized.unit;
    return metric?.meta?.unit || '';
  }

  function aggregateFor(metric, normalized) {
    return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;
  }

  function finite(value) {
    if (value === null || value === undefined || value === '') return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function metricScope(metricKey, metric) {
    if (administrativeMetrics.has(metricKey)) return 'administrative';
    if (territorialMetrics.has(metricKey)) return 'territorial';
    if (functionalMetrics.has(metricKey)) return 'functional';
    return themeScopeDefaults[metric?.meta?.theme] || 'territorial';
  }

  function readingScaleMarkup(metricKey, metric) {
    const scope = metricScope(metricKey, metric);
    const profile = scopeProfiles[scope];
    return `<aside class="reading-scale" data-reading-scale="${scope}" data-reading-metric="${metricKey}">
      <div><span class="overline">Scala di lettura</span><strong>${profile.label}</strong></div>
      <p>${profile.description}</p>
    </aside>`;
  }

  function formatAxis(value, unit) {
    if (finite(value) === null) return 'n.d.';
    const n = Number(value);
    const formatted = Math.abs(n) >= 100 ? number0.format(n) : number1.format(n);
    const kind = unitKind(unit);
    if (kind === 'percent') return `${formatted}%`;
    if (kind === 'percentage-points') return `${formatted} p.p.`;
    if (kind === 'currency') return `${formatted} €`;
    if (kind === 'millioncurrency') return `${formatted} mln €`;
    if (kind === 'years') return `${formatted} anni`;
    if (kind === 'nights') return `${formatted} notti`;
    return unit ? `${formatted} ${unit}` : formatted;
  }

  function scaleFor(values, aggregateValue, unit) {
    const numeric = values.map(finite).filter(value => value !== null);
    const reference = finite(aggregateValue);
    if (reference !== null) numeric.push(reference);
    if (!numeric.length) return { min: 0, max: 1, kind: 'absolute' };

    const allPercent = unitKind(unit) === 'percent' && numeric.every(value => value >= 0 && value <= 100);
    if (allPercent) return { min: 0, max: 100, kind: 'percent' };

    let min = Math.min(...numeric);
    let max = Math.max(...numeric);
    if (min >= 0) {
      min = 0;
      max = max === 0 ? 1 : max * 1.05;
      return { min, max, kind: 'absolute' };
    }
    if (max <= 0) {
      max = 0;
      min = min === 0 ? -1 : min * 1.05;
      return { min, max, kind: 'signed' };
    }
    const padding = (max - min) * 0.06 || 1;
    return { min: min - padding, max: max + padding, kind: 'signed' };
  }

  function position(value, scale) {
    const n = finite(value);
    if (n === null) return null;
    const span = scale.max - scale.min || 1;
    return Math.max(0, Math.min(100, ((n - scale.min) / span) * 100));
  }

  function deltaFor(metric, row, metricKey = '') {
    const local = finite(row?.value);
    const aggregate = finite(metric?.aggregate?.value);
    if (local === null || aggregate === null) {
      return { headline: 'n.d.', direction: 'confronto non disponibile', compact: 'confronto non disponibile' };
    }

    const key = metricKey || metric?.meta?.key || '';
    if (key === 'population') {
      if (aggregate <= 0) {
        return { headline: 'n.d.', direction: 'quota non disponibile', compact: 'quota non disponibile', overline: 'Quota sulla Versilia' };
      }
      const share = local / aggregate * 100;
      const formattedShare = number1.format(share);
      return {
        headline: `${formattedShare}%`,
        direction: 'della popolazione versiliese',
        compact: `${formattedShare}% della popolazione versiliese`,
        overline: 'Quota sulla Versilia',
        note: 'Quota dei residenti del comune sul totale della popolazione dei sette comuni.',
      };
    }

    const kind = unitKind(metric?.meta?.unit);
    if (kind === 'percent' || kind === 'percentage-points') {
      const diff = local - aggregate;
      if (Math.abs(diff) < 0.05) return { headline: '0,0 punti', direction: 'in linea', compact: 'in linea con Versilia' };
      const sign = diff > 0 ? '+' : '−';
      const abs = number1.format(Math.abs(diff));
      return {
        headline: `${sign}${abs} punti`,
        direction: diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
        compact: `${sign}${abs} p.p. vs Versilia`,
      };
    }

    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
        compact: 'confronto con Versilia',
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return { headline: '0,0%', direction: 'in linea', compact: 'in linea con Versilia' };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: relative > 0 ? 'sopra la Versilia' : 'sotto la Versilia',
      compact: `${sign}${abs}% vs Versilia`,
    };
  }

  function enhanceComparison(container) {
    if (!data || !container?.isConnected) return;
    const metricKey = metricKeyFor(container);
    const metric = data.metrics?.[metricKey];
    if (!metric) return;

    const normalized = normalizedFor(container);
    const aggregate = aggregateFor(metric, normalized);
    const rows = [...container.querySelectorAll(':scope > .bar-row')];
    if (!rows.length) return;

    const mapped = rows.map(rowEl => {
      const townName = rowEl.querySelector('.bar-town')?.textContent?.trim();
      const row = townRow(metric, townName);
      return { rowEl, row, value: valueFor(row, metric, normalized) };
    });
    const firstRow = mapped.find(item => item.row)?.row;
    const unit = unitFor(firstRow, metric, normalized);
    const scale = scaleFor(mapped.map(item => item.value), aggregate?.value, unit);
    const referencePosition = position(aggregate?.value, scale);
    const zeroPosition = position(0, scale) ?? 0;
    const signature = [metricKey, normalized ? 'n' : 'r', aggregate?.value, unit, ...mapped.map(item => item.value)].join('|');
    if (container.dataset.visualGrammarSignature === signature && container.querySelector(':scope > .comparison-legend')) return;
    container.dataset.visualGrammarSignature = signature;
    container.dataset.viz = scale.kind === 'percent' ? 'percent-dotplot' : scale.kind === 'signed' ? 'signed-dotplot' : 'lollipop';

    container.querySelector(':scope > .comparison-legend')?.remove();
    container.querySelector(':scope > .comparison-axis')?.remove();
    container.querySelector(':scope > .comparison-note')?.remove();

    const legend = document.createElement('div');
    legend.className = 'comparison-legend';
    legend.innerHTML = `<span><i class="comparison-legend-dot" aria-hidden="true"></i>Comune</span><span><i class="comparison-legend-reference" aria-hidden="true"></i>${aggregate?.label || 'Versilia'}</span>`;
    container.prepend(legend);

    mapped.forEach(({ rowEl, row, value }) => {
      rowEl.querySelector('.bar-rank')?.remove();
      rowEl.classList.add('comparison-row');
      const track = rowEl.querySelector('.bar-track');
      if (!track) return;
      const x = position(value, scale);
      if (x === null) {
        const missing = '<span class="comparison-missing">Dato non disponibile</span>';
        if (track.innerHTML !== missing) track.innerHTML = missing;
        rowEl.classList.add('missing');
        return;
      }
      rowEl.classList.remove('missing');
      const stemLeft = Math.min(zeroPosition, x);
      const stemWidth = Math.abs(x - zeroPosition);
      const markup = `
        <span class="comparison-axis-line" aria-hidden="true"></span>
        ${scale.kind === 'signed' ? `<span class="comparison-zero" style="left:${zeroPosition}%" aria-hidden="true"></span>` : ''}
        ${referencePosition !== null ? `<span class="comparison-reference" style="left:${referencePosition}%" aria-hidden="true"></span>` : ''}
        <span class="comparison-stem" style="left:${stemLeft}%;width:${stemWidth}%" aria-hidden="true"></span>
        <span class="comparison-dot" style="left:${x}%" aria-hidden="true"></span>`;
      if (track.innerHTML !== markup) track.innerHTML = markup;
      if (row) rowEl.setAttribute('aria-label', `${row.town}: ${formatAxis(value, unit)}; ${aggregate?.label || 'Versilia'}: ${formatAxis(aggregate?.value, unit)}`);
    });

    const axis = document.createElement('div');
    axis.className = 'comparison-axis';
    axis.innerHTML = `<span>${formatAxis(scale.min, unit)}</span><span>${scale.kind === 'percent' ? 'scala 0–100%' : scale.kind === 'signed' ? 'lo zero è evidenziato' : 'scala con origine a zero'}</span><span>${formatAxis(scale.max, unit)}</span>`;
    container.append(axis);

    const note = document.createElement('p');
    note.className = 'comparison-note';
    note.textContent = 'I comuni sono ordinati per valore per facilitare il confronto. L’ordine non esprime merito o qualità.';
    container.append(note);
  }

  function enhanceReadingScales() {
    if (!data) return;

    const definition = document.querySelector('#compare-definition .indicator-definition');
    if (definition) {
      const metricKey = metricKeyFor(definition);
      const metric = data.metrics?.[metricKey];
      if (metric) {
        const existing = definition.querySelector(':scope > .reading-scale');
        if (!existing || existing.dataset.readingMetric !== metricKey) {
          existing?.remove();
          const actions = definition.querySelector(':scope > .data-actions');
          const wrapper = document.createElement('div');
          wrapper.innerHTML = readingScaleMarkup(metricKey, metric);
          const block = wrapper.firstElementChild;
          if (actions) definition.insertBefore(block, actions);
          else definition.append(block);
        }
      }
    }

    const townLayout = document.querySelector('#town-topic .town-metric-layout');
    if (townLayout) {
      const metricKey = metricKeyFor(townLayout);
      const metric = data.metrics?.[metricKey];
      if (metric) {
        const existing = townLayout.parentElement?.querySelector(':scope > .reading-scale');
        if (!existing || existing.dataset.readingMetric !== metricKey) {
          existing?.remove();
          const wrapper = document.createElement('div');
          wrapper.innerHTML = readingScaleMarkup(metricKey, metric);
          townLayout.insertAdjacentElement('afterend', wrapper.firstElementChild);
        }
      }
    }
  }

  function enhanceTownPosition() {
    if (!data) return;
    const panel = document.querySelector('.versilia-position');
    const townName = document.querySelector('.town-identity h1')?.textContent?.trim();
    if (!panel || !townName) return;
    const metricKey = metricKeyFor(panel);
    const metric = data.metrics?.[metricKey];
    const row = townRow(metric, townName);
    if (!metric || !row) return;

    const delta = deltaFor(metric, row, metricKey);
    const overlineText = delta.overline || 'Rispetto alla Versilia';
    const noteText = delta.note || 'Il confronto con la Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.';
    const signature = `${metricKey}|${delta.headline}|${delta.direction}|${overlineText}|${noteText}`;
    if (panel.dataset.visualGrammarSignature === signature) return;
    panel.dataset.visualGrammarSignature = signature;
    const overline = panel.querySelector('.overline');
    const strong = panel.querySelector(':scope > strong');
    const note = panel.querySelector(':scope > p');
    if (overline && overline.textContent !== overlineText) overline.textContent = overlineText;
    const strongMarkup = `${delta.headline}<small>${delta.direction}</small>`;
    if (strong && strong.innerHTML !== strongMarkup) strong.innerHTML = strongMarkup;
    if (note && note.textContent !== noteText) note.textContent = noteText;
  }

  function enhanceIndicatorCards() {
    if (!data) return;
    const townName = document.querySelector('.town-identity h1')?.textContent?.trim();
    if (!townName) return;
    document.querySelectorAll('.indicator-card-grid button[data-indicator]').forEach(button => {
      const metricKey = button.dataset.indicator;
      const metric = data.metrics?.[metricKey];
      const row = townRow(metric, townName);
      const small = button.querySelector('small');
      if (!metric || !row || !small) return;
      const delta = deltaFor(metric, row, metricKey);
      const text = `${metric.meta.year} · ${delta.compact}`;
      if (small.textContent !== text) small.textContent = text;
    });
  }

  function enhanceHomeMethod() {
    const method = document.querySelector('.method-section');
    if (!method) return;
    const articles = [...method.querySelectorAll('.method-list article')];
    const scaleArticle = articles.find(article => article.querySelector('h3')?.textContent.trim() === 'La scala conta');
    if (scaleArticle) {
      const heading = scaleArticle.querySelector('h3');
      const paragraph = scaleArticle.querySelector('p');
      if (heading) heading.textContent = 'Il Comune non è sempre il sistema';
      if (paragraph) paragraph.textContent = 'Ogni indicatore dichiara se il confine comunale è amministrativo, territoriale o soltanto una localizzazione dentro un fenomeno sovracomunale.';
    }
    if (!method.querySelector('.system-reading-link')) {
      const link = document.createElement('a');
      link.className = 'system-reading-link';
      link.href = projectSystemUrl;
      link.innerHTML = '<span>Comune e sistema territoriale</span><strong>Come cambia la lettura di lavoro, economia e mobilità →</strong>';
      method.append(link);
    }
  }

  function enhanceProjectMethod() {
    const method = document.querySelector('.method-detail');
    if (!method || method.dataset.territorialReadingEnhanced === 'true') return;
    method.dataset.territorialReadingEnhanced = 'true';
    const headingCopy = method.querySelector('.section-heading > p');
    if (headingCopy) headingCopy.textContent = 'Sei regole per evitare confronti solo apparentemente precisi.';

    const principles = method.querySelector('.principles-grid');
    if (principles) {
      const items = [...principles.querySelectorAll(':scope > li')];
      const first = items[0];
      if (first) {
        const heading = first.querySelector('h3');
        const paragraph = first.querySelector('p');
        if (heading) heading.textContent = 'Scala esplicita';
        if (paragraph) paragraph.textContent = 'Ogni indicatore dichiara se va letto come dato amministrativo, territoriale o funzionale: il Comune non viene trattato automaticamente come un sistema chiuso.';
      }
      if (!principles.querySelector('.base-size-principle')) {
        const last = items.at(-1);
        if (last?.querySelector('span')) last.querySelector('span').textContent = '06';
        const item = document.createElement('li');
        item.className = 'base-size-principle';
        item.innerHTML = '<span>05</span><h3>Basi numeriche diverse</h3><p>Tassi e variazioni percentuali possono essere più instabili nei comuni piccoli: quando pochi casi spostano molto una percentuale, il dato va letto insieme ai valori assoluti e alla serie storica disponibili.</p>';
        if (last) principles.insertBefore(item, last);
        else principles.append(item);
      }
    }

    if (!document.getElementById('sistema-territoriale')) {
      const section = document.createElement('section');
      section.id = 'sistema-territoriale';
      section.className = 'system-reading page-width';
      section.innerHTML = `<div class="system-reading-intro"><span class="section-number">03</span><div><span class="overline">Comune e sistema territoriale</span><h2>Sette amministrazioni, un territorio interdipendente.</h2><p>I confini comunali sono essenziali per bilanci, servizi e responsabilità amministrative. Lo sono molto meno per mercato del lavoro, sistema produttivo, mobilità, sanità e turismo, che funzionano su reti sovracomunali.</p></div></div>
        <div class="system-reading-grid">
          <article data-scope="administrative"><strong>Amministrativo</strong><p>Il confine comunale è parte del fenomeno. È il caso, per esempio, di bilanci, opere e risorse attribuite all’ente.</p></article>
          <article data-scope="territorial"><strong>Territoriale</strong><p>Il Comune è una buona unità descrittiva per residenti, abitazioni o fenomeni localizzati, ma non è necessariamente un sistema autonomo.</p></article>
          <article data-scope="functional"><strong>Funzionale</strong><p>Flussi di lavoro, imprese, servizi e mobilità superano i confini. Il valore comunale indica localizzazione o residenza, non il perimetro reale del sistema.</p></article>
        </div>
        <div class="system-reading-caution"><div><span class="overline">Comuni di dimensioni diverse</span><h3>Una percentuale non pesa sempre allo stesso modo.</h3></div><p>Viareggio e Stazzema hanno basi numeriche molto diverse. Normalizzare per abitante rende i valori confrontabili, ma non elimina la maggiore volatilità dei tassi nei territori piccoli: pochi casi possono produrre variazioni percentuali ampie.</p></div>
        <div class="system-reading-links"><a href="${new URL('../confronta/lavoro/', scriptUrl).href}">Lavoro <span>→</span></a><a href="${new URL('../confronta/economia/', scriptUrl).href}">Economia <span>→</span></a><a href="${new URL('../confronta/mobilita/', scriptUrl).href}">Mobilità <span>→</span></a></div>`;
      method.insertAdjacentElement('afterend', section);
    }
  }

  function reviseCopy() {
    document.querySelectorAll('.method-list h3').forEach(heading => {
      if (heading.textContent.trim() === 'Posizione, non giudizio') {
        heading.textContent = 'Differenze, non podi';
        const paragraph = heading.nextElementSibling;
        if (paragraph) paragraph.textContent = 'I comuni possono essere ordinati per valore per facilitare la lettura, ma il sito evidenzia distanze e contesto, non posizioni ordinali.';
      }
    });

    document.querySelectorAll('.principles-grid h3').forEach(heading => {
      if (heading.textContent.trim() === 'Nessun voto') {
        const paragraph = heading.nextElementSibling;
        const text = 'Distanze e confronti descrivono i valori: non diventano pagelle, podi o giudizi politici automatici.';
        if (paragraph && paragraph.textContent !== text) paragraph.textContent = text;
      }
    });

    const intro = document.querySelector('.hero-intro p');
    if (intro?.textContent.includes('posizione rispetto alla Versilia')) intro.textContent = intro.textContent.replace('posizione rispetto alla Versilia', 'confronto con la Versilia');
    const townsIntro = document.querySelector('.towns-section .section-heading > p');
    if (townsIntro?.textContent.includes('posizione nel contesto')) townsIntro.textContent = townsIntro.textContent.replace('posizione nel contesto', 'confronto nel contesto');

    enhanceHomeMethod();
    enhanceProjectMethod();
  }

  function enhance() {
    scheduled = false;
    if (!data) return;
    document.querySelectorAll('.comparison-bars').forEach(enhanceComparison);
    enhanceReadingScales();
    enhanceTownPosition();
    enhanceIndicatorCards();
    reviseCopy();
  }

  function scheduleEnhance() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(enhance);
  }

  const observer = new MutationObserver(scheduleEnhance);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'aria-selected'] });

  fetch(dataUrl, { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw new Error(`Dati non disponibili (${response.status})`);
      return response.json();
    })
    .then(payload => {
      data = payload;
      enhance();
    })
    .catch(error => console.warn('Grammatica visuale non applicata:', error));
})();