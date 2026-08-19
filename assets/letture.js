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
  const nf = (value, digits = 0) => new Intl.NumberFormat('it-IT', { minimumFractionDigits: digits, maximumFractionDigits: digits, useGrouping: true }).format(Number(value));
  const signed = (value, digits = 1, suffix = '') => `${Number(value) > 0 ? '+' : ''}${nf(value, digits)}${suffix}`;
  const date = value => value ? new Date(value).toLocaleDateString('it-IT') : 'non disponibile';
  const metricHref = (key, metric) => new URL(`confronta/${metric?.meta?.theme || ''}/?indicatore=${encodeURIComponent(key)}`, ROOT).href;
  const townName = row => row?.town || row?.municipality || row?.name || row?.comune || '';
  const rows = metric => Array.isArray(metric?.rows)
    ? metric.rows.filter(row => townName(row)).sort((a,b)=>townName(a).localeCompare(townName(b),'it'))
    : [];

  const THEME_PATHS = {
    demografia: '<path d="M18 21a8 8 0 0 0-16 0"></path><circle cx="10" cy="8" r="5"></circle><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"></path>',
    economia: '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1 0-6.76Z"></path><path d="M7 12h5"></path><path d="M15 9.4a4 4 0 1 0 0 5.2"></path>',
    lavoro: '<path d="M12 12h.01"></path><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"></path><path d="M22 13a18.15 18.15 0 0 1-20 0"></path><rect width="20" height="14" x="2" y="6" rx="2"></rect>',
    mobilita: '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"></path><path d="M7 14h.01"></path><path d="M17 14h.01"></path><rect width="18" height="8" x="3" y="10" rx="2"></rect><path d="M5 18v2"></path><path d="M19 18v2"></path>',
    sicurezza: '<path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3z"></path><path d="m9 12 2 2 4-4"></path>',
    ambiente: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>',
    bilanci: '<path d="M3 22h18"></path><path d="M6 18v-7"></path><path d="M10 18v-7"></path><path d="M14 18v-7"></path><path d="M18 18v-7"></path><path d="M12 2 2 7h20Z"></path>',
    comunita: '<path d="M10 12h4"></path><path d="M10 8h4"></path><path d="M14 21v-3a2 2 0 0 0-4 0v3"></path><path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"></path><path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"></path>'
  };
  const STORY_PATHS = {
    residents: THEME_PATHS.demografia,
    split: '<path d="M4 6h7"></path><path d="m8 3 3 3-3 3"></path><path d="M20 18h-7"></path><path d="m16 15-3 3 3 3"></path><path d="M4 18h4a4 4 0 0 0 4-4V10a4 4 0 0 1 4-4h4"></path>',
    aging: '<circle cx="9" cy="7" r="4"></circle><path d="M3 21a6 6 0 0 1 12 0"></path><circle cx="18" cy="16" r="4"></circle><path d="M18 14v2l1.2 1.2"></path>',
    mobility: '<path d="M4 8h14"></path><path d="m14 4 4 4-4 4"></path><path d="M20 16H6"></path><path d="m10 12-4 4 4 4"></path>',
    check: '<path d="M20 6 9 17l-5-5"></path>',
    limit: '<circle cx="12" cy="12" r="9"></circle><path d="M12 8v5"></path><path d="M12 16h.01"></path>'
  };

  function icon(path, size = 24) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path || ''}</svg>`;
  }
  const themeIcon = (theme, size = 24) => icon(THEME_PATHS[theme] || THEME_PATHS.demografia, size);
  const storyIcon = (name, size = 24) => icon(STORY_PATHS[name] || STORY_PATHS.check, size);

  function statusFor(key, state, metric) {
    const operational = state?.metrics?.[key] || {};
    return {
      period: operational.publishedPeriod || metric?.meta?.year || '',
      checked: operational.checkedAt || state?.checkedAt || '',
      status: operational.status || ''
    };
  }

  function unitValue(value, meta, digits = 1, signedValue = false) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) return '—';
    const unit = meta?.unit || '';
    const n = Number(value);
    if (unit === 'percent') return signedValue ? signed(n, digits, '%') : `${nf(n,digits)}%`;
    if (unit === 'per1000') return `${signedValue ? signed(n,digits) : nf(n,digits)} ogni 1.000`;
    if (unit === 'number') return nf(n, 0);
    if (unit === 'years') return `${nf(n,digits)} anni`;
    return signedValue ? signed(n,digits) : nf(n,digits);
  }

  function populationStory(data) {
    const population = data.metrics.population;
    const change = data.metrics.populationChange;
    const aging = data.metrics.oldAgeIndex;
    const mobility = data.metrics.totalResidentialMobility;
    if (![population, change, aging, mobility].every(Boolean)) throw new Error('Indicatori demografici del pilota incompleti');

    const popRows = rows(population);
    const changeRows = rows(change);
    const agingRows = rows(aging);
    const mobilityRows = rows(mobility);
    const commonYears = popRows[0].series.years.map(Number);
    const totals = commonYears.map((year, index) => popRows.reduce((sum,row)=>sum+Number(row.series.values[index]),0));
    const startYear = commonYears[0], endYear = commonYears.at(-1);
    const startTotal = totals[0], endTotal = totals.at(-1);
    const totalDelta = endTotal - startTotal;
    const totalPct = totalDelta / startTotal * 100;
    const gainRows = changeRows.filter(row=>Number(row.value)>0);
    const lossRows = changeRows.filter(row=>Number(row.value)<0);
    const gains = gainRows.reduce((sum,row)=> {
      const source=popRows.find(candidate=>townName(candidate)===townName(row));
      return sum + (source.series.values.at(-1)-source.series.values[0]);
    },0);
    const losses = lossRows.reduce((sum,row)=> {
      const source=popRows.find(candidate=>townName(candidate)===townName(row));
      return sum + (source.series.values.at(-1)-source.series.values[0]);
    },0);

    const ageChanges = agingRows.map(row=>({
      town: townName(row),
      from: Number(row.series.values[0]),
      to: Number(row.series.values.at(-1)),
      delta: Number(row.series.values.at(-1))-Number(row.series.values[0]),
      years: row.series.years
    }));
    const allAging = ageChanges.every(item=>item.delta>0);
    const benchmark = aging.meta?.benchmark || {};
    const benchmarkYear = Number(benchmark.year || 2024);
    const aboveTuscany = agingRows.filter(row=> {
      const idx=(row.series?.years||[]).map(Number).indexOf(benchmarkYear);
      return idx>=0 && Number(row.series.values[idx])>Number(benchmark.tuscany);
    }).length;

    const mobilityByTown = Object.fromEntries(mobilityRows.map(row=>[townName(row),Number(row.value)]));
    const positiveMobility = mobilityRows.filter(row=>Number(row.value)>0).length;
    const decliningPositive = changeRows.filter(row=>Number(row.value)<0 && Number(mobilityByTown[townName(row)])>0).map(row=>townName(row));

    return {
      population, change, aging, mobility,
      popRows, changeRows, agingRows, mobilityRows,
      years: commonYears, totals, startYear, endYear, startTotal, endTotal, totalDelta, totalPct,
      gainRows, lossRows, gains, losses,
      ageChanges, allAging, benchmark, benchmarkYear, aboveTuscany,
      mobilityByTown, positiveMobility, decliningPositive
    };
  }

  function lineChart(story) {
    const values=story.totals, years=story.years;
    const width=900,height=300,left=54,right=26,top=30,bottom=42;
    const min=Math.min(...values),max=Math.max(...values),pad=Math.max((max-min)*.35,150);
    const yMin=min-pad,yMax=max+pad;
    const x=index=>left+index/(values.length-1)*(width-left-right);
    const y=value=>top+(yMax-value)/(yMax-yMin)*(height-top-bottom);
    const path=values.map((v,i)=>`${i?'L':'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const points=values.map((v,i)=>`<g class="story-chart-point"><circle cx="${x(i)}" cy="${y(v)}" r="4"><title>${years[i]}: ${nf(v,0)} residenti</title></circle>${(i===0||i===values.length-1)?`<text x="${x(i)}" y="${y(v)-13}" text-anchor="${i===0?'start':'end'}">${nf(v,0)}</text>`:''}</g>`).join('');
    const labels=years.map((yr,i)=> (i===0||i===values.length-1||yr===2022) ? `<text x="${x(i)}" y="${height-12}" text-anchor="middle">${yr}</text>` : '').join('');
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Residenti complessivi nei sette Comuni dal ${story.startYear} al ${story.endYear}"><line class="story-chart-grid" x1="${left}" x2="${width-right}" y1="${y(story.startTotal)}" y2="${y(story.startTotal)}"></line><path class="story-chart-line" d="${path}"></path>${points}${labels}</svg>`;
  }

  function populationRowsMarkup(story) {
    const max=Math.max(...story.changeRows.map(row=>Math.abs(Number(row.value))),1);
    return story.changeRows.map(row=>{
      const value=Number(row.value), width=Math.max(Math.abs(value)/max*48,1.5);
      return `<div class="story-change-row"><strong>${esc(townName(row))}</strong><div class="story-change-track" aria-hidden="true"><span class="story-zero"></span><i class="${value>=0?'gain':'loss'}" style="--bar:${width}%"></i></div><b>${esc(unitValue(value,story.change.meta,1,true))}</b></div>`;
    }).join('');
  }

  function agingRowsMarkup(story) {
    const all=story.ageChanges.flatMap(item=>[item.from,item.to]);
    const min=Math.min(...all)-15,max=Math.max(...all)+15,span=max-min;
    return story.ageChanges.map(item=>{
      const from=(item.from-min)/span*100,to=(item.to-min)/span*100;
      return `<div class="story-age-row"><strong>${esc(item.town)}</strong><div class="story-age-track" aria-label="${esc(item.town)}: da ${nf(item.from,1)} a ${nf(item.to,1)}"><i style="--from:${from}%;--to:${to}%"></i><span class="age-from" style="--pos:${from}%"></span><span class="age-to" style="--pos:${to}%"></span></div><div><small>${story.startYear}</small><b>${nf(item.from,1)}</b><span>→</span><small>${story.endYear}</small><b>${nf(item.to,1)}</b></div></div>`;
    }).join('');
  }

  function mobilityRowsMarkup(story) {
    return story.changeRows.map(row=>{
      const town=townName(row), populationChange=Number(row.value), mobility=story.mobilityByTown[town];
      const mismatch=populationChange<0 && mobility>0;
      return `<div class="story-mobility-row ${mismatch?'mismatch':''}"><strong>${esc(town)}</strong><span><small>Residenti ${story.startYear}–${story.endYear}</small><b>${esc(unitValue(populationChange,story.change.meta,1,true))}</b></span><span><small>Trasferimenti ${esc(story.mobility.meta.year)}</small><b>${esc(unitValue(mobility,story.mobility.meta,1,true))}</b></span>${mismatch?'<em>andamenti diversi</em>':''}</div>`;
    }).join('');
  }

  function sourceLink(key, metric, state) {
    const st=statusFor(key,state,metric);
    return `<a class="story-source-link" href="${metricHref(key,metric)}"><span>${esc(metric.meta.label)}</span><small>${esc(st.period)} · ultimo controllo ${esc(date(st.checked))}</small><b>Apri il dato →</b></a>`;
  }

  function demographyDetail(item, payload) {
    const {data,state}=payload;
    const story=populationStory(data);
    const totalDirection=story.totalPct<0?'diminuiscono':'aumentano';
    const totalAbs=Math.abs(story.totalDelta);
    const allAgingText=story.allAging ? 'in tutti e sette i Comuni' : 'nella maggior parte dei Comuni';
    document.querySelector('.reading-main')?.setAttribute('data-theme','demografia');

    return `<section class="story-hero page-width" data-theme="demografia">
      <div class="breadcrumbs"><a href="${new URL('letture/',ROOT).href}">Capire la Versilia</a><span>›</span><strong>${esc(item.title)}</strong></div>
      <div class="story-hero-grid"><div><span class="overline">${themeIcon('demografia',18)} Demografia · lettura pilota</span><h1>${esc(item.title)}</h1><p class="story-deck">Tra ${story.startYear} e ${story.endYear} i residenti dei sette Comuni ${totalDirection} di <strong>${nf(totalAbs,0)} persone (${unitValue(story.totalPct,story.change.meta,1,true)})</strong>. Ma il dato complessivo nasconde traiettorie comunali opposte, mentre l’indice di vecchiaia cresce ${allAgingText}.</p></div><div class="story-hero-icon">${themeIcon('demografia',54)}</div></div>
      <div class="story-question"><span>La domanda</span><strong>${esc(item.question)}</strong></div>
    </section>

    <section class="story-thesis page-width" data-theme="demografia">
      <div class="story-thesis-label">${storyIcon('check',22)} <span>La storia in una frase</span></div>
      <p>La Versilia <strong>non si sta svuotando in modo uniforme</strong>: nel complesso cambia poco nel numero dei residenti, ma le perdite si concentrano in alcuni Comuni e <strong>l’invecchiamento è una tendenza comune a tutto il territorio</strong>.</p>
    </section>

    <section class="story-facts page-width" data-theme="demografia" aria-label="Tre evidenze chiave">
      <article><span class="story-fact-icon">${storyIcon('residents',24)}</span><div><strong>${unitValue(story.totalPct,story.change.meta,1,true)}</strong><p>residenti complessivi ${story.startYear}–${story.endYear}</p></div></article>
      <article><span class="story-fact-icon">${storyIcon('split',24)}</span><div><strong>${story.gainRows.length} / 7</strong><p>Comuni con più residenti rispetto al ${story.startYear}</p></div></article>
      <article><span class="story-fact-icon">${storyIcon('aging',24)}</span><div><strong>${story.ageChanges.filter(item=>item.delta>0).length} / 7</strong><p>Comuni con indice di vecchiaia in aumento</p></div></article>
    </section>

    <section class="story-chapter page-width" data-theme="demografia" data-story-chapter="population">
      <header class="story-chapter-head"><span class="story-number">01</span><span class="story-chapter-icon">${storyIcon('split',28)}</span><div><span class="overline">Residenti · ${story.startYear}–${story.endYear}</span><h2>Una quasi stabilità che nasconde sette traiettorie</h2></div></header>
      <div class="story-copy"><p>Il totale dei sette Comuni passa da <strong>${nf(story.startTotal,0)}</strong> a <strong>${nf(story.endTotal,0)} residenti</strong>. La variazione complessiva è contenuta (${unitValue(story.totalPct,story.change.meta,1,true)}), ma non perché tutti i territori siano fermi.</p><p>I quattro Comuni in calo perdono complessivamente <strong>${nf(Math.abs(story.losses),0)} residenti</strong>; i tre in crescita ne aggiungono <strong>${nf(story.gains,0)}</strong>. È questa compensazione a rendere quasi piatto il totale della Versilia.</p></div>
      <div class="story-visual story-line-card"><div class="story-visual-head"><div>${storyIcon('residents',22)}<span>Residenti complessivi dei sette Comuni</span></div><small>Somma dei valori comunali Istat · unità: residenti</small></div><div class="story-line-chart">${lineChart(story)}</div></div>
      <div class="story-visual"><div class="story-visual-head"><div>${storyIcon('split',22)}<span>Come cambia ciascun Comune</span></div><small>Ordine alfabetico · unità: %</small></div><div class="story-change-list">${populationRowsMarkup(story)}</div></div>
      <p class="story-reading-note"><strong>Cosa aggiunge questo passaggio.</strong> Dire soltanto “la Versilia perde lo 0,9%” nasconde la parte più importante: il dato territoriale è il risultato di andamenti locali molto diversi.</p>
    </section>

    <section class="story-chapter page-width" data-theme="demografia" data-story-chapter="aging">
      <header class="story-chapter-head"><span class="story-number">02</span><span class="story-chapter-icon">${storyIcon('aging',28)}</span><div><span class="overline">Struttura per età · ${story.startYear}–${story.endYear}</span><h2>L’invecchiamento, invece, è una storia comune</h2></div></header>
      <div class="story-copy"><p>L’indice di vecchiaia misura quante persone di 65 anni e oltre ci sono ogni 100 residenti tra 0 e 14 anni. Dal ${story.startYear} al ${story.endYear} <strong>aumenta in tutti e sette i Comuni</strong>.</p><p>${story.benchmark?.tuscany ? `Nel ${story.benchmarkYear}, usando lo stesso anno del benchmark Istat, <strong>${story.aboveTuscany} Comuni su 7</strong> erano sopra il valore toscano di <strong>${nf(story.benchmark.tuscany,1)}</strong>.` : ''} Il fenomeno quindi non coincide con i soli Comuni che perdono popolazione.</p></div>
      <div class="story-visual"><div class="story-visual-head"><div>${storyIcon('aging',22)}<span>Indice di vecchiaia: inizio e fine periodo</span></div><small>Unità: persone 65+ ogni 100 residenti 0–14</small></div><div class="story-age-list">${agingRowsMarkup(story)}</div></div>
      <p class="story-reading-note"><strong>Cosa aggiunge questo passaggio.</strong> Il numero totale degli abitanti può restare quasi stabile mentre cambia profondamente la composizione della popolazione. È qui che la lettura smette di essere una semplice storia di “spopolamento”.</p>
    </section>

    <section class="story-chapter page-width" data-theme="demografia" data-story-chapter="mobility">
      <header class="story-chapter-head"><span class="story-number">03</span><span class="story-chapter-icon">${storyIcon('mobility',28)}</span><div><span class="overline">Trasferimenti di residenza · ${esc(story.mobility.meta.year)}</span><h2>Perdere residenti non significa automaticamente “da qui se ne vanno tutti”</h2></div></header>
      <div class="story-copy"><p>Nel ${esc(story.mobility.meta.year)} il saldo complessivo dei trasferimenti di residenza è positivo in <strong>${story.positiveMobility} Comuni su 7</strong>. È positivo anche in <strong>${story.decliningPositive.length} dei ${story.lossRows.length} Comuni</strong> che, guardando al periodo ${story.startYear}–${story.endYear}, hanno meno residenti.</p><p>I due indicatori descrivono periodi e fenomeni diversi, ma proprio questa differenza è informativa: <strong>i trasferimenti di residenza non bastano, da soli, a spiegare la traiettoria demografica complessiva</strong>.</p></div>
      <div class="story-visual"><div class="story-visual-head"><div>${storyIcon('mobility',22)}<span>Due segnali da non confondere</span></div><small>Popolazione: % ${story.startYear}–${story.endYear} · trasferimenti: saldo per 1.000 nel ${esc(story.mobility.meta.year)}</small></div><div class="story-mobility-list">${mobilityRowsMarkup(story)}</div></div>
      <p class="story-reading-note"><strong>Cosa aggiunge questo passaggio.</strong> In ${story.decliningPositive.join(', ')} il saldo dei trasferimenti ${esc(story.mobility.meta.year)} è positivo nonostante la popolazione sia inferiore al ${story.startYear}. Senza nascite, decessi e altre componenti del bilancio demografico non possiamo attribuire una causa.</p>
    </section>

    <section class="story-conclusion" data-theme="demografia"><div class="page-width">
      <div class="story-conclusion-head">${themeIcon('demografia',34)}<div><span class="overline">Cosa resta della storia</span><h2>Il tema non è soltanto quanti siamo, ma come cambia la popolazione</h2></div></div>
      <div class="story-conclusion-grid"><article><span>${storyIcon('check',22)}</span><h3>Cosa possiamo dire</h3><p>La stabilità aggregata nasconde forti differenze comunali; l’invecchiamento cresce ovunque; il saldo dei trasferimenti non coincide automaticamente con la variazione complessiva dei residenti.</p></article><article><span>${storyIcon('limit',22)}</span><h3>Cosa non possiamo dire</h3><p>Questi indicatori non spiegano da soli perché la popolazione cambi. Per attribuire cause servono almeno saldo naturale, nascite, decessi e ulteriori informazioni su casa, lavoro e scelte migratorie.</p></article></div>
    </div></section>

    <section class="story-sources page-width" data-theme="demografia"><div class="story-section-title"><span class="overline">Controlla la lettura</span><h2>I dati dietro il racconto</h2><p>La storia non conserva copie dei valori: ogni numero sopra è calcolato dai dati canonici dell’Osservatorio al caricamento della pagina.</p></div><div class="story-source-grid">${['population','populationChange','oldAgeIndex','totalResidentialMobility'].map(key=>sourceLink(key,data.metrics[key],state)).join('')}</div><p class="reading-status-note">Stato generale delle fonti registrato il ${esc(date(state?.checkedAt))}. <a href="${new URL('stato-dati/',ROOT).href}">Apri Stato dei dati →</a></p></section>`;
  }

  function plannedDetail(item, data) {
    const theme=item.themes?.[0] || 'demografia';
    document.querySelector('.reading-main')?.setAttribute('data-theme',theme);
    return `<section class="story-hero page-width" data-theme="${esc(theme)}"><div class="breadcrumbs"><a href="${new URL('letture/',ROOT).href}">Capire la Versilia</a><span>›</span><strong>${esc(item.title)}</strong></div><div class="story-hero-grid"><div><span class="overline">${themeIcon(theme,18)} ${esc(data.themes?.[theme]?.label || theme)} · in sviluppo</span><h1>${esc(item.title)}</h1><p class="story-deck">Questa possibile lettura resta nel piano editoriale, ma <strong>non viene ancora presentata come storia</strong>: prima bisogna verificare quali conclusioni sono davvero sostenute dai dati.</p></div><div class="story-hero-icon">${themeIcon(theme,54)}</div></div><div class="story-question"><span>Domanda da verificare</span><strong>${esc(item.question)}</strong></div></section><section class="planned-reading page-width" data-theme="${esc(theme)}"><span class="story-chapter-icon">${storyIcon('limit',28)}</span><div><h2>Non basta mettere insieme gli indicatori</h2><p>Questa pagina verrà sviluppata solo quando i dati consentiranno di formulare una tesi, mostrarne le prove, evidenziare le eccezioni e dichiarare ciò che non possiamo concludere.</p><a href="${new URL('letture/una-versilia-che-cambia/',ROOT).href}">Guarda il pilota editoriale →</a></div></section>`;
  }

  function index(config, data) {
    const pilot=config.items.find(item=>item.status==='pilot') || config.items[0];
    const planned=config.items.filter(item=>item.slug!==pilot.slug);
    const story=populationStory(data);
    const pilotTheme=pilot.themes?.[0] || 'demografia';
    const plannedCards=planned.map(item=>{
      const theme=item.themes?.[0] || 'demografia';
      return `<article class="reading-plan-card" data-theme="${esc(theme)}"><span class="reading-plan-icon">${themeIcon(theme,25)}</span><div><small>Da costruire sui dati</small><h3>${esc(item.title)}</h3><p>${esc(item.question)}</p></div></article>`;
    }).join('');
    return `<section class="reading-index-hero page-width"><span class="overline">Osservatorio Versilia · livello editoriale · bozza</span><h1>Capire la Versilia</h1><p>Storie e chiavi di lettura costruite mettendo in relazione indicatori diversi. Non un’altra lista di dati: ogni pagina deve arrivare a una conclusione verificabile, mostrarne le prove e dichiararne i limiti.</p></section>
      <section class="reading-pilot page-width" data-theme="${esc(pilotTheme)}"><div class="reading-pilot-copy"><span class="reading-pilot-icon">${themeIcon(pilotTheme,34)}</span><div><span class="overline">Pilota editoriale · Demografia</span><h2>${esc(pilot.title)}</h2><p>${unitValue(story.totalPct,story.change.meta,1,true)} residenti complessivi dal ${story.startYear}; indice di vecchiaia in aumento in ${story.ageChanges.filter(item=>item.delta>0).length} Comuni su 7. <strong>Il punto è capire perché questi due segnali raccontano una storia diversa dal semplice “spopolamento”.</strong></p><a href="${new URL(`letture/${pilot.slug}/`,ROOT).href}">Leggi la storia →</a></div></div><div class="reading-pilot-facts"><div><strong>${unitValue(story.totalPct,story.change.meta,1,true)}</strong><span>residenti ${story.startYear}–${story.endYear}</span></div><div><strong>${story.gainRows.length}/7</strong><span>Comuni in crescita</span></div><div><strong>${story.ageChanges.filter(item=>item.delta>0).length}/7</strong><span>indice di vecchiaia ↑</span></div></div></section>
      <section class="reading-roadmap page-width"><div class="story-section-title"><span class="overline">Prossime domande</span><h2>Non le chiamiamo ancora Letture</h2><p>Restano ipotesi editoriali. Verranno aperte soltanto se l’analisi dei dati produce una storia che aggiunge qualcosa rispetto a una normale pagina di confronto.</p></div><div class="reading-plan-grid">${plannedCards}</div></section>`;
  }

  Promise.all(Object.values(URLS).map(url=>fetch(url).then(response=>{if(!response.ok) throw new Error(`${url.pathname}: ${response.status}`); return response.json();})))
    .then(([config,data,registry,state])=>{
      if (!registry?.schemaVersion) throw new Error('Source registry non valido');
      const app=document.getElementById('reading-app');
      const reading=document.body.dataset.reading || '';
      if (!reading) { app.innerHTML=index(config,data); return; }
      const item=config.items.find(candidate=>candidate.slug===reading);
      if (!item) throw new Error(`Lettura non configurata: ${reading}`);
      app.innerHTML=item.status==='pilot' && item.renderer==='demography-story-v2'
        ? demographyDetail(item,{data,state,registry})
        : plannedDetail(item,data);
    })
    .catch(error=>{
      console.error(error);
      document.getElementById('reading-app').innerHTML='<div class="app-error"><strong>Lettura non disponibile.</strong><p>I dati canonici necessari non sono stati caricati.</p></div>';
    });
})();
