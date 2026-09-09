(() => {
  'use strict';
  const root = document.getElementById('turnout-app');
  const methodRoot = document.getElementById('turnout-method-root');
  if (!root) return;

  const pct = v => v == null ? 'n.d.' : `${new Intl.NumberFormat('it-IT',{minimumFractionDigits:1,maximumFractionDigits:1}).format(v)}%`;
  const num = v => v == null ? 'n.d.' : new Intl.NumberFormat('it-IT').format(v);
  const esc = v => String(v ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  const familyOrder = ['politiche_camera','europee','regionali_toscana','referendum'];
  let data;
  const state = { family:'referendum', event:null, town:'Camaiore', municipalTown:'Camaiore' };

  const latestEvent = family => data.families[family].events.at(-1);
  const currentEvent = () => data.families[state.family].events.find(e => e.id === state.event) || latestEvent(state.family);
  const eventTitle = e => e.question ? `${e.dateLabel} · Quesito ${e.questionId}` : e.dateLabel;
  const eventQuestion = e => e.question || data.families[state.family].note;

  function familyControls(){
    const events = [...data.families[state.family].events].reverse();
    return `<div class="metric-switch turnout-family-tabs" role="tablist" aria-label="Famiglia elettorale">${familyOrder.map(key => `<button type="button" role="tab" aria-selected="${state.family===key?'true':'false'}" data-family="${key}" class="${state.family===key?'active':''}">${esc(data.families[key].short)}</button>`).join('')}</div>
      <label class="turnout-event-field"><span>Consultazione</span><select id="turnout-event-select" aria-label="Seleziona la consultazione">${events.map(e => `<option value="${esc(e.id)}" ${currentEvent().id===e.id?'selected':''}>${esc(eventTitle(e))}${e.question ? ` · ${esc(e.question.slice(0,80))}` : ''}</option>`).join('')}</select></label>`;
  }

  function comparisonMarkup(e){
    const rows = [...e.municipalities].sort((a,b)=>b.turnout-a.turnout);
    const reference = Math.max(0,Math.min(100,e.versilia.turnout));
    return `<div class="comparison-bars turnout-comparison" data-viz="lollipop">
      <div class="comparison-legend"><span><i class="comparison-legend-dot" aria-hidden="true"></i>Comune</span><span><i class="comparison-legend-reference" aria-hidden="true"></i>Versilia · ${pct(e.versilia.turnout)}</span></div>
      ${rows.map(r => {
        const value = Math.max(0,Math.min(100,r.turnout));
        return `<div class="bar-row comparison-row" aria-label="${esc(r.name)}: ${pct(r.turnout)}; Versilia: ${pct(e.versilia.turnout)}"><span class="bar-town">${esc(r.name)}</span><span class="bar-track"><span class="comparison-axis-line" aria-hidden="true"></span><span class="comparison-reference" style="left:${reference}%" aria-hidden="true"></span><span class="comparison-stem" style="left:0%;width:${value}%" aria-hidden="true"></span><span class="comparison-dot" style="left:${value}%" aria-hidden="true"></span><span class="bar-hover-label">${esc(r.name)} · ${pct(r.turnout)}</span></span><strong>${pct(r.turnout)}</strong></div>`;
      }).join('')}
      <div class="comparison-axis"><span>0%</span><span>scala con origine a zero</span><span>100%</span></div>
      <p class="comparison-note">I Comuni sono ordinati per affluenza per facilitare il confronto. L’ordine non esprime merito o qualità.</p>
    </div>`;
  }

  function sexMarkup(e){
    if (!e.versilia.mfComplete) return `<details class="detail-disclosure turnout-sex-detail"><summary><span>Affluenza per sesso</span><small>Dettaglio non disponibile per tutti i Comuni</small></summary><div class="method-disclosure-body"><p>Il dettaglio uomini/donne è mostrato solo quando la fonte lo rende disponibile per tutti i Comuni.</p></div></details>`;
    const gap = e.versilia.maleTurnout - e.versilia.femaleTurnout;
    return `<details class="detail-disclosure turnout-sex-detail"><summary><span>Affluenza per sesso · Versilia</span><small>Dettaglio disponibile per tutti i Comuni</small></summary><div class="method-disclosure-body"><dl class="turnout-sex-values"><div><dt>Uomini</dt><dd>${pct(e.versilia.maleTurnout)}</dd></div><div><dt>Donne</dt><dd>${pct(e.versilia.femaleTurnout)}</dd></div><div><dt>Differenza</dt><dd>${gap>=0?'+':''}${pct(gap)}</dd></div></dl><p>Il confronto uomini/donne è mostrato soltanto dove i dati ufficiali sono completi.</p></div></details>`;
  }

  function currentSection(){
    const e = currentEvent();
    return `<section class="indicator-current page-width" aria-labelledby="turnout-current-title"><div class="section-heading"><div><span class="overline">Confronto territoriale</span><h2 id="turnout-current-title">Affluenza alla consultazione selezionata</h2></div><p>Ogni confronto usa la stessa consultazione, data, turno e universo elettorale per tutti i sette Comuni.</p></div>
      <div class="topic-dashboard turnout-dashboard"><aside class="topic-controls">${familyControls()}<div class="indicator-definition"><h2>${esc(data.families[state.family].label)}</h2><p>${esc(data.families[state.family].note)}</p><dl><div><dt>Data / quesito</dt><dd>${esc(eventTitle(e))}</dd></div><div><dt>Affluenza Versilia</dt><dd>${pct(e.versilia.turnout)}</dd></div></dl><small class="aggregate-note">Il dato Versilia considera insieme elettori e votanti dei sette Comuni, evitando una semplice media delle percentuali.</small></div></aside>
      <div class="topic-bars"><div class="turnout-event-question"><strong>${esc(eventTitle(e))}</strong>${esc(eventQuestion(e))}</div>${comparisonMarkup(e)}${sexMarkup(e)}</div></div></section>`;
  }

  function canonicalPoint({x,y,label,valueText,width,left,right,detail=''}){
    const boxWidth = 230;
    const boxHeight = detail ? 66 : 50;
    const boxX = Math.max(left - 8, Math.min(width - right - boxWidth, x - boxWidth / 2));
    const boxY = y < boxHeight + 28 ? y + 18 : y - boxHeight - 16;
    return `<g class="chart-point" tabindex="0" role="button" aria-label="${esc(label)}: ${esc(valueText)}">
      <circle class="chart-hit" cx="${x}" cy="${y}" r="13"></circle>
      <circle class="chart-dot ux-series-point" cx="${x}" cy="${y}" r="4"></circle>
      <g class="chart-tooltip" hidden>
        <line class="chart-guide" x1="${x}" y1="${y}" x2="${x}" y2="${boxY < y ? boxY + boxHeight : boxY}"></line>
        <rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect>
        <text class="chart-tooltip-year" x="${boxX + 12}" y="${boxY + 14}">${esc(label)}</text>
        <text class="chart-tooltip-value" x="${boxX + 12}" y="${boxY + 34}">${esc(valueText)}</text>
        ${detail?`<text class="chart-tooltip-detail" x="${boxX + 12}" y="${boxY + 53}">${esc(detail)}</text>`:''}
      </g>
    </g>`;
  }

  function wireCanonicalTooltips(scope=root){
    scope.querySelectorAll('.turnout-history-chart').forEach(chart => {
      if (chart.dataset.ovTooltipWired === '1') return;
      chart.dataset.ovTooltipWired = '1';
      const points = [...chart.querySelectorAll('.chart-point')];
      const hideAll = () => points.forEach(point => {
        point.classList.remove('active');
        point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
      });
      const show = point => {
        hideAll();
        point.classList.add('active');
        point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
      };
      points.forEach((point,index) => {
        point.addEventListener('mouseenter',()=>show(point));
        point.addEventListener('mouseleave',hideAll);
        point.addEventListener('focus',()=>show(point));
        point.addEventListener('blur',hideAll);
        point.addEventListener('click',()=>show(point));
        point.addEventListener('keydown',event=>{
          if (event.key==='Escape'){hideAll();point.blur();return;}
          if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
          event.preventDefault();
          let next=index;
          if(event.key==='ArrowLeft') next=(index-1+points.length)%points.length;
          if(event.key==='ArrowRight') next=(index+1)%points.length;
          if(event.key==='Home') next=0;
          if(event.key==='End') next=points.length-1;
          points[next]?.focus();
        });
      });
      chart.addEventListener('mouseleave',hideAll);
    });
  }

  function standardChart({points, lineClass='', ariaLabel, pointLabel, pointDetail=null, showReference=false}){
    if (!points.length) return '<div class="indicator-history-empty"><strong>Serie storica non disponibile</strong></div>';
    const W=920,H=300,L=66,R=24,T=24,B=48;
    const x=i=>L+(points.length===1?.5:i/(points.length-1))*(W-L-R);
    const y=v=>T+(100-v)/100*(H-T-B);
    const line=points.map((p,i)=>`${i?'L':'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ');
    const refLine=showReference ? points.map((p,i)=>`${i?'L':'M'}${x(i).toFixed(1)},${y(p.reference).toFixed(1)}`).join(' ') : '';
    const grid=[0,25,50,75,100].map(v=>`<line class="chart-grid" x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"></line>`).join('');
    const step=Math.max(1,Math.ceil(points.length/10));
    const labels=points.map((p,i)=>({p,i})).filter(({i})=>i%step===0||i===points.length-1).map(({p,i})=>`<text class="chart-label" x="${x(i)}" y="${H-14}" text-anchor="middle">${esc(p.axisLabel)}</text>`).join('');
    const dots=points.map((p,i)=>canonicalPoint({x:x(i),y:y(p.value),label:pointLabel(p),valueText:pct(p.value),width:W,left:L,right:R,detail:pointDetail?pointDetail(p):''})).join('');
    const refs=showReference ? points.map((p,i)=>`<circle class="turnout-versilia-dot" cx="${x(i)}" cy="${y(p.reference)}" r="3" aria-hidden="true"></circle>`).join('') : '';
    return `<div class="chart-shell"><div class="trend-chart ux-history-chart turnout-history-chart" style="--series-color:var(--theme-color)"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(ariaLabel)}">${grid}<path class="chart-line ${lineClass}" d="${line}"></path>${showReference?`<path class="chart-line turnout-versilia-line" d="${refLine}"></path>`:''}${dots}${refs}${labels}</svg></div></div>`;
  }

  function trendChart(){
    const points = data.families[state.family].events.map(e => ({
      e,
      value: e.municipalities.find(r => r.name === state.town)?.turnout,
      reference: e.versilia.turnout,
      axisLabel: String(e.year)
    })).filter(p => p.value != null && p.reference != null);
    return `<div class="turnout-chart-legend"><span><i></i>${esc(state.town)}</span><span><i class="ref"></i>Versilia</span></div>${standardChart({
      points,
      ariaLabel:`Storico ${data.families[state.family].label} per ${state.town}`,
      pointLabel:p=>`${eventTitle(p.e)} · ${state.town}`,
      pointDetail:p=>`Versilia ${pct(p.reference)}`,
      showReference:true
    })}<small class="aggregate-note turnout-history-note">Nei referendum ogni quesito resta una voce distinta.</small>`;
  }

  function historySection(){
    return `<section class="indicator-history page-width" aria-labelledby="turnout-history-title"><div class="section-heading"><div><span class="overline">Andamento</span><h2 id="turnout-history-title">Serie storica comunale e Versilia</h2></div><p>Il confronto nel tempo resta all’interno della stessa famiglia elettorale.</p></div><div class="turnout-history-toolbar"><div class="metric-switch turnout-town-tabs" role="tablist" aria-label="Comune della serie storica">${data.towns.map(t=>`<button type="button" role="tab" aria-selected="${state.town===t.name?'true':'false'}" data-trend-town="${esc(t.name)}" class="${state.town===t.name?'active':''}">${esc(t.name)}</button>`).join('')}</div></div><section class="history-panel"><div class="panel-title"><div><span class="overline">${esc(data.families[state.family].short)}</span><h3>${esc(state.town)} · evoluzione dell’affluenza</h3></div><a class="source-pill" href="https://elezionistorico.interno.gov.it/eligendo/opendata.php" target="_blank" rel="noreferrer">Fonte DAIT / Eligendo ↗</a></div>${trendChart()}</section></section>`;
  }

  function municipalTrend(selected){
    const points=selected.history.map(e=>({
      e,
      value:e.turnout,
      axisLabel:String(e.year)
    }));
    return standardChart({
      points,
      ariaLabel:`Elezioni comunali: serie storica dell'affluenza per ${selected.town}`,
      pointLabel:p=>`${p.e.dateLabel} · ${selected.town}`,
      pointDetail:p=>`${num(p.e.voters)} votanti / ${num(p.e.electors)} elettori`
    });
  }

  function municipalSection(){
    const selected = data.communal.find(x=>x.town===state.municipalTown) || data.communal[0];
    const latest = selected.latest;
    const startYear = selected.history[0]?.year;
    return `<section class="indicator-history page-width turnout-municipal-section" aria-labelledby="turnout-municipal-title">
      <div class="section-heading"><div><span class="overline">Elezioni comunali</span><h2 id="turnout-municipal-title">Serie storiche comunali</h2></div><p>Primo turno o turno unico. Ogni Comune vota in anni diversi, quindi le serie restano separate.</p></div>
      <div class="turnout-history-toolbar"><div class="metric-switch turnout-town-tabs" role="tablist" aria-label="Comune della serie storica delle elezioni comunali">${data.communal.map(x=>`<button type="button" role="tab" aria-selected="${selected.town===x.town?'true':'false'}" data-municipal-town="${esc(x.town)}" class="${selected.town===x.town?'active':''}">${esc(x.town)}</button>`).join('')}</div></div>
      <section class="history-panel turnout-municipal-history"><div class="panel-title"><div><span class="overline">Comunali · primo turno / turno unico</span><h3>${esc(selected.town)} · ${esc(String(startYear))}–${esc(String(latest.year))}</h3></div><a class="source-pill" href="https://elezionistorico.interno.gov.it/eligendo/opendata.php" target="_blank" rel="noreferrer">Fonti ufficiali ↗</a></div>
        <dl class="turnout-municipal-latest"><div><dt>Ultima consultazione</dt><dd>${esc(latest.dateLabel)}</dd></div><div><dt>Affluenza</dt><dd>${pct(latest.turnout)}</dd></div><div><dt>Votanti</dt><dd>${num(latest.voters)}</dd></div><div><dt>Elettori</dt><dd>${num(latest.electors)}</dd></div></dl>
        ${municipalTrend(selected)}
        <div class="indicator-table-scroll turnout-municipal-history-table"><table class="indicator-history-table"><thead><tr><th>Data</th><th>Affluenza</th><th>Votanti</th><th>Elettori</th><th>Uomini</th><th>Donne</th></tr></thead><tbody>${selected.history.map(e=>`<tr><th scope="row">${esc(e.dateLabel)}</th><td>${pct(e.turnout)}</td><td>${num(e.voters)}</td><td>${num(e.electors)}</td><td>${pct(e.maleTurnout)}</td><td>${pct(e.femaleTurnout)}</td></tr>`).join('')}</tbody></table></div>
        <p class="aggregate-note turnout-municipal-note">Sono mostrate le consultazioni disponibili nelle fonti ufficiali.</p>
      </section>
      <details class="detail-disclosure turnout-latest-all"><summary><span>Ultime Comunali nei sette Comuni</span><small>Anni diversi · nessun aggregato Versilia</small></summary><div class="method-disclosure-body"><div class="indicator-table-scroll"><table class="indicator-values-table turnout-municipal-table"><thead><tr><th>Comune</th><th>Data</th><th>Affluenza</th><th>Votanti / elettori</th></tr></thead><tbody>${data.communal.map(x=>`<tr><th scope="row">${esc(x.town)}</th><td>${esc(x.latest.dateLabel)}</td><td>${pct(x.latest.turnout)}</td><td>${num(x.latest.voters)} / ${num(x.latest.electors)}</td></tr>`).join('')}</tbody></table></div></div></details>
    </section>`;
  }

  function provinceSection(){
    const groups={};
    data.provinceReferendumContext.forEach(row => (groups[row.date] ??=[]).push(row));
    return `<section class="indicator-history page-width" aria-labelledby="turnout-province-title"><div class="section-heading"><div><span class="overline">Contesto storico</span><h2 id="turnout-province-title">Referendum senza dettaglio comunale</h2></div><p>Per queste tornate è disponibile soltanto il dato provinciale.</p></div><div class="indicator-history-empty"><strong>Provincia di Lucca, non Versilia</strong><p>Per alcune consultazioni tra 1987 e 2006 è disponibile solo il dato della Provincia di Lucca.</p></div><div class="turnout-province-list">${Object.entries(groups).sort().map(([date,rows])=>`<details class="detail-disclosure"><summary><span>${esc(rows[0].dateLabel)}</span><small>${rows.length} ${rows.length===1?'quesito':'quesiti'} · Provincia di Lucca</small></summary><div class="method-disclosure-body"><table class="turnout-province-table"><thead><tr><th>Quesito</th><th>Affluenza</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.question)}</td><td>${pct(r.turnout)}</td></tr>`).join('')}</tbody></table></div></details>`).join('')}</div></section>`;
  }

  function methodSection(){
    if (!methodRoot) return;
    methodRoot.innerHTML = `<section class="indicator-method page-width" aria-labelledby="turnout-method-title"><div class="section-heading"><div><span class="overline">Come leggere i dati</span><h2 id="turnout-method-title">Confronti e limiti</h2></div><p>Politiche, Europee, Regionali e Referendum sono confrontati solo all’interno della stessa consultazione. Le Comunali restano separate per Comune.</p></div><details class="method-disclosure"><summary><span>Informazioni utili</span><small>Disponibilità e confronti</small></summary><div class="method-disclosure-body"><p>Il dettaglio uomini/donne compare soltanto quando è disponibile nelle fonti ufficiali. Per alcune consultazioni referendarie storiche è disponibile soltanto il dato provinciale, mostrato in una sezione separata.</p></div></details><div class="turnout-method-source-links"><a class="source-pill" href="../../../stato-dati/">Stato dei dati</a><a class="source-pill" href="https://elezionistorico.interno.gov.it/eligendo/opendata.php" target="_blank" rel="noreferrer">Ministero dell’Interno ↗</a></div></section>`;
  }

  function render(){
    root.innerHTML = currentSection()+historySection()+municipalSection()+provinceSection();
    bind();
    wireCanonicalTooltips();
    methodSection();
  }

  function bind(){
    root.querySelectorAll('[data-family]').forEach(button => button.addEventListener('click',()=>{state.family=button.dataset.family;state.event=latestEvent(state.family).id;render();}));
    root.querySelector('#turnout-event-select')?.addEventListener('change',event=>{state.event=event.target.value;render();});
    root.querySelectorAll('[data-trend-town]').forEach(button=>button.addEventListener('click',()=>{state.town=button.dataset.trendTown;render();}));
    root.querySelectorAll('[data-municipal-town]').forEach(button=>button.addEventListener('click',()=>{state.municipalTown=button.dataset.municipalTown;render();}));
  }

  async function loadArchive(){
    const response=await fetch('../../../data/affluenza/archive-00.b64');
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    const encoded=(await response.text()).replace(/\s+/g,'');
    const compressed=Uint8Array.from(atob(encoded),char=>char.charCodeAt(0));
    if(typeof DecompressionStream!=='function') throw new Error('DecompressionStream non disponibile');
    const stream=new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }

  loadArchive().then(payload=>{data=payload;state.event=latestEvent(state.family).id;render();}).catch(error=>{console.error(error);root.innerHTML='<div class="page-width"><div class="app-error"><strong>Impossibile caricare l’archivio affluenza.</strong></div></div>';});
})();
