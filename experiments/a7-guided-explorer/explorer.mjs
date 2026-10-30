// Presentation over the original anchored A6 transport. No numerical engine.
import limitsIt from './limits-it.mjs';
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const fold=(title,content)=>{const n=node('details');n.append(node('summary',title),content);return n;};
const operations={observe:'Il valore in un Comune',lookup:'Il dettaglio per località',compare:'Confronta i sette Comuni',series:'Com’è cambiato nel tempo in un Comune',rank:'Dal valore più alto al più basso',benchmark_gap:'Rispetto a Toscana o Italia',absolute_change:'Quanto è cambiato (differenza)',relative_change:'Quanto è cambiato (in percentuale)',weighted_ratio:'Il valore della Versilia nel suo insieme',percentage_points:'Quanto è cambiato (in punti percentuali)',trend:'Tendenza nel tempo',correlation:'Associazione',anomaly:'Valori fuori scala fra i sette Comuni'};
const profiles={observe:'current',lookup:'current',compare:'comparison',series:'history',rank:'ranking',benchmark_gap:'benchmark',weighted_ratio:'aggregation',absolute_change:'changes',relative_change:'changes',percentage_points:'changes',trend:'trends',anomaly:'outliers'};
const allTowns=['compare','rank','weighted_ratio','anomaly'];
const changes=['absolute_change','relative_change','percentage_points'];
// Display translations only: these labels never authorize a calculation or
// replace the original reasons preserved in the evidence.
const trendReasons={census_historical_dimension_not_available:'Per questo dettaglio la serie storica non è disponibile. Non significa che il dato manchi nella fonte.',insufficient_observations:'Ci sono troppo pochi anni disponibili per calcolare una tendenza.',distinct_finance_massarosa_osl_temporal_perimeter_not_attested:'Per Massarosa la continuità fra bilancio ordinario e gestione del dissesto non è garantita.'};
const outlierReasons={anomaly_zero_interquartile_range:'Almeno metà dei Comuni ha valori molto vicini o uguali: lo scarto interquartile è zero e la regola non può distinguere valori fuori scala.',anomaly_requires_four_usable_observations:'Servono almeno quattro valori disponibili per applicare la regola.'};
const outlierClasses={above_fence:'Sopra la soglia superiore',below_fence:'Sotto la soglia inferiore',within_fences:'Entro le soglie'};
const units={count:'unità',meters:'m',hectares:'ha',cubicMetres:'m³',currency2:'€',eurliter:'€/l',eurm2:'€/m²',eurm2month:'€/m²/mese',per10k:'per 10.000',km2:'km²',celsius:'°C',index:'indice',percent_change:'%',sqm_per_resident:'m²/residente',km_per_km2:'km/km²',currency_per_resident:'€/residente',number:'unità',percentage_points:'punti percentuali',percentagePoints:'punti percentuali',hectaresPerFarm:'ha/azienda',per1000:'per 1.000',per100:'per 100',per100k:'per 100.000',minutes:'minuti',hours:'ore',people:'persone',squareKm:'km²',peoplePerSquareKm:'residenti/km²',eurPerResident:'€/residente',invalsi_score:'punti INVALSI',nights:'notti',decimal:'',percent:'%',currency:'€',years:'anni',category_code:'categoria',millionCurrency:'milioni di €',studentsPerClass:'alunni per classe'};
// Public display: at most two decimals. Exact values stay in the downloadable evidence.
const number=x=>x!==0&&Math.abs(x)<.005?(x<0?'> −0,01':'< 0,01'):new Intl.NumberFormat('it-IT',{maximumFractionDigits:2}).format(x);
const concise=number;
const value=o=>o.notApplicable?'Non applicabile':o.dataUnavailable||o.value===null||o.value===undefined?'n.d.':o.unit==='category_code'?o.categoryLabel||'Categoria senza etichetta':typeof o.value==='number'?number(o.value):String(o.value);
const sourceURL=x=>{try{const u=new URL(x);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}};
const option=(value,label,disabled=false)=>{const o=node('option',label);o.value=value;o.disabled=disabled;return o;};
const canonical=x=>JSON.stringify(x);
// Reuse (A7.5.5): exact values for the CSV, a shareable link for the selection
// and a printable reading. Nothing here computes a new number.
const csvCell=x=>{const t=x===null||x===undefined?'':String(x);return /[;"\n\r]/u.test(t)?'"'+t.replace(/"/gu,'""')+'"':t;};
const exact=x=>typeof x==='number'&&Number.isFinite(x)?String(x).replace('.',','):x===null||x===undefined?'':String(x);
const fileSlug=t=>String(t).normalize('NFD').replace(/[\u0300-\u036f]/gu,'').toLowerCase().replace(/[^a-z0-9]+/gu,'-').replace(/^-|-$/gu,'').slice(0,60)||'dati';
const SHARE='esplora';
let periodNames={};const periodLabel=p=>p===null||p===undefined?'Non dichiarato':periodNames[String(p)]||String(p); // used only to preserve the exact UI selection snapshot

export async function startExplorer(openRuntime,presentation){
 periodNames=presentation.periods||{};
 const $=id=>document.getElementById('explorer-'+id);
 const fields=$('form').querySelector('fieldset');
 const unitLabel=o=>units[o.unit]??((presentation.metrics[$('metric').value]?.unit===o.unit?presentation.metrics[$('metric').value]?.unitLabel:null)||o.unit);
 let runtime,root,detail,generation=0,pending=null,current=null,pageIndex=0;
 const status=text=>{$('status').textContent=text;};
 const revoke=()=>{generation++;pending=null;current=null;$('result').hidden=true;$('result').replaceChildren();$('consent').hidden=true;};
 const fail=()=>{revoke();runtime=null;fields.disabled=true;$('retry').hidden=false;status('Non riusciamo a caricare i dati in questo momento. Riprova fra poco.');};
 const safe=fn=>async(...args)=>{try{await fn(...args);}catch{fail();}};
 const active=async(promise,ticket)=>{try{return await promise;}catch(error){if(ticket===generation)throw error;return null;}};
 const townName=code=>({tuscany:'Toscana',italy:'Italia'})[code]||root.towns.find(t=>t.code===code)?.name||code;
 const benchmarkScopes=()=>detail?.declaration.benchmarkScopesByDimension[view()?.dimension]?.filter(s=>['tuscany','italy'].includes(s))||[];
 const viewLabel=dimension=>{
   const named=presentation.metrics[$('metric').value]?.views?.[dimension];
   if(named)return named;
   return ({total:'Dato complessivo',territoryTotal:'Totale del territorio','stat:min':'Valore minimo','stat:mean':'Valore medio','stat:max':'Valore massimo','sex:men':'Sesso: maschi','sex:women':'Sesso: femmine'})[dimension]||dimension.replace(/^ateco:/u,'ATECO ').replace(/\|active$/u,' · unità locali attive').replace(/\|artisan$/u,' · unità locali artigiane').replace(/^part:/u,'Voce: ');
 };
 function view(){return detail?.views.find(v=>v.dimension===$('view').value);}
 function setOperation(){
   revoke();const v=view();$('operation').replaceChildren();
   // Only readings materialized in this release are offered; others are not listed.
   const order=['observe','lookup','compare','rank','benchmark_gap','series','trend','absolute_change','relative_change','percentage_points','anomaly','weighted_ratio'];
   for(const operation of [...(v?.declaredOperations||[])].sort((a,b)=>(order.indexOf(a)+1||99)-(order.indexOf(b)+1||99))){const available=Boolean(v.shards[profiles[operation]])&&(operation!=='benchmark_gap'||benchmarkScopes().length>0)&&(operation!=='anomaly'||Boolean(root.outlierSelection));if(available)$('operation').append(option(operation,operations[operation]||operation));}
   const available=Array.from($('operation').options).find(o=>!o.disabled);
   if(available)$('operation').value=available.value;
   else{$('operation').value='';status('Per questa vista non ci sono ancora letture consultabili qui. Non significa che il dato sia assente.');}
   setBenchmark();setTown();
 }
 function setBenchmark(){
   const enabled=$('operation').value==='benchmark_gap';
   $('benchmark-field').hidden=!enabled;$('benchmark').disabled=!enabled;
   $('benchmark').required=enabled;
   $('benchmark').replaceChildren(option('','Scegli il riferimento'),...(enabled?benchmarkScopes().map(s=>option(s,townName(s))):[]));
 }
 function setTown(){
   const aggregate=$('operation').value==='weighted_ratio';
   const ranking=$('operation').value==='rank';
   const outliers=$('operation').value==='anomaly';
   const all=allTowns.includes($('operation').value);$('town').disabled=all;
   $('town-field').hidden=all;
   $('town').setAttribute('aria-describedby','explorer-reference');
   $('reference').textContent=aggregate?'Il valore dell’intera Versilia, calcolato sommando le componenti dei sette Comuni (non è la media dei valori comunali). Se manca un Comune il valore non viene calcolato.':$('operation').value==='benchmark_gap'?'Scegli se confrontare il Comune con la Toscana o con l’Italia. Anno e fonte compaiono nel risultato.':all?'I sette Comuni a confronto, ciascuno con il proprio anno di riferimento.':'Si mostra l’anno più recente disponibile, indicato nel risultato.';
   if(changes.includes($('operation').value)){
     const periods=view()?.changePeriodsByTown?.[$('town').value];
     $('reference').textContent=periods?'Variazione fra il primo e l’ultimo anno disponibile: '+periodLabel(periods[0])+' → '+periodLabel(periods[1])+'. Non è una variazione annua.':'Per questo dettaglio non ci sono due anni confrontabili.';
   }
   if(ranking)$('reference').textContent='I sette Comuni in ordine, dal valore più alto al più basso, nell’anno più recente disponibile. A parità di valore la posizione è la stessa. L’ordine non è un giudizio sull’amministrazione.';
   if(outliers)$('reference').textContent='Mostra se qualche Comune ha un valore molto lontano dagli altri sei, nell’anno più recente disponibile. Le soglie si ricavano dai sette valori (regola di Tukey). Non indica un errore né un giudizio.';
   if($('operation').value==='trend')$('reference').textContent='La tendenza sull’intera serie nativa disponibile per il Comune, senza scegliere anni di comodo. Nessuna previsione.';
   $('run').disabled=!view()?.shards[profiles[$('operation').value]]||($('operation').value==='benchmark_gap'&&!benchmarkScopes().includes($('benchmark').value));
 }
 function filterViews(){
   const old=$('view').value;const filter=$('filter').value.trim().toLocaleLowerCase('it');
   $('view').replaceChildren(...detail.views.filter(v=>(viewLabel(v.dimension)+' '+v.dimension).toLocaleLowerCase('it').includes(filter)).map(v=>option(v.dimension,viewLabel(v.dimension))));
   if(Array.from($('view').options).some(o=>o.value===old))$('view').value=old;
   setOperation();
   if(!$('view').options.length)status('Nessuna vista corrisponde al filtro. Modifica o cancella la ricerca.');
 }
 async function metricChanged(){
   revoke();const ticket=generation;const selected=$('metric').value;
   detail=null;$('view').replaceChildren();$('operation').replaceChildren();setBenchmark();setTown();$('run').disabled=true;$('filter').value='';
   $('description').textContent=presentation.metrics[selected]?.description||'';
   status('Caricamento delle viste di questo indicatore…');
   const loaded=await active(runtime.discover(selected),ticket);
   if(ticket!==generation)return;
   detail=loaded;
   // Show detail controls only when they help: one view needs no choice, few views need no search.
   $('view-field').hidden=detail.views.length<2;$('filter-field').hidden=detail.views.length<=8;
   filterViews();
   if(!$('run').disabled)status('Scegli vista e operazione, poi mostra i dati.');
 }
 async function themeChanged(){
   revoke();const members=root.metrics.filter(m=>m.theme===$('theme').value);
   $('metric').replaceChildren(option('','Scegli un indicatore'),...members.map(m=>option(m.metric,m.label)));
   detail=null;$('view').replaceChildren();$('operation').replaceChildren();setBenchmark();setTown();$('run').disabled=true;$('description').textContent='';$('view-field').hidden=false;$('filter-field').hidden=true;
   status('Scegli un indicatore del tema selezionato.');
 }
 function request(){
   const operation=$('operation').value;
   const periods=changes.includes(operation)?view()?.changePeriodsByTown?.[$('town').value]:null;
   const screen=operation==='anomaly'?root.outlierSelection:null;
   return {operation,...(operation==='benchmark_gap'?{benchmark:$('benchmark').value}:{}),...(screen?{rule:screen.rule,reference:screen.reference,purpose:screen.purpose}:{}),selectors:[{metric:$('metric').value,dimension:$('view').value,...(periods?{periods:[...periods]}:{}),towns:allTowns.includes(operation)?root.towns.map(t=>t.code).sort():[$('town').value]}]};
 }
 function show(result){
   current=result;pageIndex=0;render();
   try{history.replaceState(null,'',location.pathname+location.search+'#'+shareState());}catch{}
   status(result.steps[0].response.status==='computed'?'Dati caricati dalla versione verificata.':'Per questa scelta il calcolo non è disponibile: il motivo è spiegato sotto.');
 }
 async function execute(plan,approvedPartial=false){
   revoke();const ticket=generation;const frozen=canonical(plan);status('Verifica e caricamento dei dati selezionati…');
   const result=await active(runtime.run(JSON.parse(frozen),{approvedPartial}),ticket);
   if(ticket!==generation)return;
   if(result.resolution==='needs_confirmation'){pending=JSON.parse(frozen);$('consent').hidden=false;status('Serve la tua scelta sulla copertura incompleta. Nessun valore è ancora mostrato.');return;}
   if(result.resolution!=='resolved'){status('Questa lettura non è ancora disponibile qui. Non significa che il dato manchi.');return;}
   show(result);
 }
 function renderBenchmark(response,out){
   const r=response.result;
   const municipal=response.observations.find(o=>o.geography===r?.geography);
   const reference=response.observations.find(o=>o.geography===r?.benchmarkScope);
   // Display only the native result. No subtraction or percent conversion here.
   if(!r||!municipal||!reference||!['tuscany','italy'].includes(r.benchmarkScope)||
      ![r.municipalValue,r.benchmarkValue,r.value].every(x=>typeof x==='number'&&Number.isFinite(x)))throw Error('incompatible_benchmark_result');
   const summary=node('section');summary.className='explorer-benchmark';summary.setAttribute('aria-label','Confronto con '+townName(r.benchmarkScope));
   summary.append(node('h4',townName(r.geography)+' e '+townName(r.benchmarkScope)));
   const cards=node('dl');cards.className='explorer-benchmark-values';
   for(const [key,label,amount,unit] of [['municipal',townName(r.geography),r.municipalValue,unitLabel(municipal)],['reference',townName(r.benchmarkScope),r.benchmarkValue,unitLabel(reference)],['gap','Scostamento',r.value,unitLabel(r)]]){
     const card=node('div');const shown=node('dd',(key==='gap'&&amount>0?'+':'')+concise(amount)+' '+unit);
     shown.dataset.benchmarkValue=key;card.append(node('dt',label),shown);cards.append(card);
   }
   summary.append(cards,node('p','Valori arrotondati; il dettaglio è nella tabella.'),node('p','Periodo del risultato: '+periodLabel(r.period)+'. Scostamento = valore comunale meno riferimento. Un valore positivo o negativo non è un giudizio sulla qualità amministrativa.'));
   for(const [key,label] of [['numeratorPeriod','Periodo del numeratore'],['denominatorPeriod','Periodo del denominatore']])if(r[key]!==undefined)summary.append(node('p',label+': '+String(r[key])));
   if(r.unit==='percentage_points')summary.append(node('p','La differenza fra le due percentuali è espressa in punti percentuali, non come variazione percentuale.'));
   out.append(summary);
 }
 function renderAggregation(response,out){
   const r=response.result;const codes=root.towns.map(t=>t.code).sort();
   // A full-area label requires the native result to include the exact scope.
   // Never calculate sums, weights or a ratio in the browser.
   if(!r||!Array.isArray(r.geographies)||canonical([...r.geographies].sort())!==canonical(codes)||
      response.coverage?.requested!==codes.length||response.coverage?.usable!==codes.length||
      ![r.value,r.numerator,r.denominator,r.scale].every(x=>typeof x==='number'&&Number.isFinite(x))||
      r.denominator<=0||r.scale<=0)throw Error('incompatible_full_area_result');
   const summary=node('section');summary.className='explorer-aggregation';summary.setAttribute('aria-label','Rapporto aggregato della Versilia');
   summary.append(node('h4','Versilia · sette Comuni'));
   const values=node('dl');values.className='explorer-benchmark-values';
   const card=node('div');const amount=node('dd',concise(r.value)+' '+unitLabel(r));amount.dataset.aggregationValue='true';
   card.append(node('dt','Rapporto aggregato'),amount);values.append(card);summary.append(values);
   summary.append(node('p','Rapporto delle somme dei numeratori e dei denominatori, con la scala prevista dalla misura. Non è la media dei tassi comunali né una somma generica.'),node('p','Periodo del risultato: '+periodLabel(r.period)+'.'));
   for(const [key,label] of [['numeratorPeriod','Periodo del numeratore'],['denominatorPeriod','Periodo del denominatore']])if(r[key]!==undefined)summary.append(node('p',label+': '+String(r[key])));
   summary.append(node('p','Perimetro: '+codes.map(townName).join(', ')+'.'));
   out.append(summary);
 }
 function renderChange(response,out,selector,operation){
   const r=response.result;const observations=response.observations||[];
   const [start,end]=observations;
   if(!r||observations.length!==2||response.coverage?.requested!==2||response.coverage?.usable!==2||
      ![r.value,start?.value,end?.value].every(x=>typeof x==='number'&&Number.isFinite(x))||
      observations.some(o=>o.dataUnavailable||o.notApplicable||o.geography!==selector.towns[0])||
      r.startPeriod!==start.period||r.endPeriod!==end.period||r.startPeriod===r.endPeriod||
      (selector.periods&&canonical(selector.periods)!==canonical([r.startPeriod,r.endPeriod])))throw Error('incompatible_change_result');
   const summary=node('section');summary.className='explorer-change';summary.setAttribute('aria-label','Variazione temporale');
   summary.append(node('h4',townName(selector.towns[0])+' · '+periodLabel(r.startPeriod)+' → '+periodLabel(r.endPeriod)));
   const cards=node('dl');cards.className='explorer-benchmark-values';
   for(const [key,label,amount,unit] of [['start','Valore iniziale · '+periodLabel(r.startPeriod),start.value,unitLabel(start)],['end','Valore finale · '+periodLabel(r.endPeriod),end.value,unitLabel(end)],['change',operations[operation],r.value,unitLabel(r)]]){
     const card=node('div');const shown=node('dd',(key==='change'&&amount>0?'+':'')+concise(amount)+' '+unit);shown.dataset.changeValue=key;card.append(node('dt',label),shown);cards.append(card);
   }
   summary.append(cards,node('p','La variazione riguarda questi due anni, non un tasso annuo né l’effetto di un intervento. Il segno non indica automaticamente miglioramento o peggioramento.'));
   summary.append(node('p',operation==='relative_change'?'Variazione percentuale rispetto al valore iniziale. È distinta dalla differenza in punti percentuali.':r.unit==='percentage_points'||r.unit==='percentagePoints'?'Differenza espressa in punti percentuali, distinta dalla variazione percentuale relativa.':'Differenza fra valore finale e iniziale, nell’unità della misura.'));
   out.append(summary);
 }
 function renderTrend(response,out,selector){
   const r=response.result,observations=response.observations||[];
   // Present the native OLS result verbatim: never fit a line, recalculate a
   // slope, close gaps or extrapolate from the observations in the browser.
   if(!r||r.method!=='OLS slope'||r.forecast!==false||!Number.isFinite(r.slope)||
      !Number.isInteger(r.n)||r.n<2||r.n!==observations.length||
      response.coverage?.requested!==r.n||response.coverage?.usable!==r.n||
      !Array.isArray(r.timeAxis)||r.timeAxis.length!==r.n||!r.timeAxis.every(Number.isFinite)||
      typeof r.unit!=='string'||!r.unit.endsWith('/year')||
      observations.some(o=>o.geography!==selector.towns[0]||!Number.isFinite(o.value)||o.dataUnavailable||o.notApplicable))throw Error('incompatible_trend_result');
   const baseUnit=r.unit.slice(0,-5);
   const slopeUnit=(baseUnit==='percentage_points'?'punti percentuali':unitLabel({unit:baseUnit})||'unità della misura')+' per anno';
   const summary=node('section');summary.className='explorer-trend';summary.setAttribute('aria-label','Tendenza della serie nativa');
   summary.append(node('h4',townName(selector.towns[0])+' · tendenza della serie'));
   const cards=node('dl');cards.className='explorer-benchmark-values';
   for(const [key,label,text] of [['slope','Pendenza stimata',(r.slope>0?'+':'')+concise(r.slope)+' '+slopeUnit],['periods','Periodi osservati',periodLabel(observations[0].period)+' → '+periodLabel(observations.at(-1).period)],['n','Osservazioni utilizzate',String(r.n)]]){
     const card=node('div'),shown=node('dd',text);shown.dataset.trendValue=key;card.append(node('dt',label),shown);cards.append(card);
   }
   summary.append(cards,node('p','Variazione media per anno sull’intera serie disponibile: non è una previsione.'),node('p','Il segno non indica automaticamente miglioramento o peggioramento, né l’effetto di un intervento.'));
   const method=node('div');
   method.append(node('p','La tendenza è la retta che meglio approssima i valori nel tempo (minimi quadrati). Indica la direzione media, non una previsione.'),node('p','I valori sono arrotondati per la lettura; anni e valori sono nella tabella.'));
   if(baseUnit==='percentage_points')method.append(node('p','Per una misura percentuale, la pendenza è in punti percentuali per anno, non in percentuale relativa.'));
   const axis=node('p','Anni considerati: '+r.timeAxis.map(String).join(', '));axis.dataset.trendAxis='true';
   method.append(axis);
   summary.append(fold('Come si legge',method));out.append(summary);
 }
 function renderOutliers(response,out,selector){
   const r=response.result,observations=response.observations||[];
   const codes=root.towns.map(t=>t.code).sort();
   // Present the native Tukey screen verbatim: never compute quartiles, fences
   // or classifications in the browser, never drop a town or change the rule.
   // Positions on the strip are display geometry only, never a new statistic.
   if(!r||r.rule!=='tukey_1_5_iqr'||canonical([...selector.towns].sort())!==canonical(codes)||
      !Number.isInteger(r.n)||r.n!==response.coverage?.usable||!Array.isArray(r.observations)||r.observations.length!==r.n||
      ![r.q1,r.q3,r.median,r.iqr,r.lowerFence,r.upperFence].every(Number.isFinite)||!(r.lowerFence<=r.upperFence)||
      r.observations.some(o=>!codes.includes(o.geography)||!Number.isFinite(o.value)||!outlierClasses[o.classification])||
      new Set(r.observations.map(o=>o.geography)).size!==r.n)throw Error('incompatible_outlier_result');
   const raw=unitLabel({unit:r.unit}),unit=raw&&raw!=='indice'?' '+raw:'';
   const fmt=x=>concise(x)+unit;
   const above=r.observations.filter(o=>o.classification==='above_fence'),below=r.observations.filter(o=>o.classification==='below_fence');
   const names=list=>list.map(o=>townName(o.geography)).join(' e ');
   const summary=node('section');summary.className='explorer-outliers';summary.setAttribute('aria-label','Valori fuori scala fra i sette Comuni');
   const period=observations[0]?.period;
   summary.append(node('p','Valori fuori scala fra i sette Comuni'+(period!==undefined?' · '+periodLabel(period):'')));
   summary.lastChild.className='explorer-outliers-kicker';
   const verdict=node('h4',above.length||below.length?[above.length?names(above)+(above.length>1?' sono':' è')+' molto sopra gli altri Comuni':'',below.length?names(below)+(below.length>1?' sono':' è')+' molto sotto gli altri Comuni':''].filter(Boolean).join('; ')+'.':'Nessun Comune è fuori scala: tutti i valori sono nella fascia attesa.');
   verdict.dataset.outlierVerdict=above.length||below.length?'flagged':'none';summary.append(verdict);
   // Strip: shaded expected band between the native fences, median tick, one dot per town.
   const values=r.observations.map(o=>o.value);
   let lo=Math.min(r.lowerFence,...values),hi=Math.max(r.upperFence,...values);
   const pad=(hi-lo)*.06||Math.abs(hi)*.1||1;lo-=pad;hi+=pad;
   const at=x=>((x-lo)/(hi-lo)*100).toFixed(3)+'%';
   const strip=node('div');strip.className='explorer-strip';strip.setAttribute('role','img');
   strip.setAttribute('aria-label','Posizione dei sette Comuni rispetto alla fascia attesa, da '+fmt(r.lowerFence)+' a '+fmt(r.upperFence)+'. '+verdict.textContent+' I valori sono nella tabella.');
   const track=node('div');track.className='explorer-strip-track';
   const band=node('span');band.className='explorer-strip-band';band.style.left=at(r.lowerFence);band.style.width=((r.upperFence-r.lowerFence)/(hi-lo)*100).toFixed(3)+'%';
   const median=node('span');median.className='explorer-strip-median';median.style.left=at(r.median);
   track.append(band,median);
   for(const o of [...r.observations].sort((a,b)=>(a.classification!=='within_fences')-(b.classification!=='within_fences'))){
     const flagged=o.classification!=='within_fences';
     const dot=node('span');dot.className='explorer-strip-dot'+(flagged?' is-out':'');dot.style.left=at(o.value);
     dot.dataset.outlierGeography=o.geography;dot.dataset.outlierClass=o.classification;
     dot.title=townName(o.geography)+': '+fmt(o.value)+' · '+outlierClasses[o.classification];
     track.append(dot);
     if(flagged){const tag=node('span',townName(o.geography)+' · '+fmt(o.value));tag.className='explorer-strip-tag';const left=(o.value-lo)/(hi-lo);if(left>.6)tag.style.right='0';else if(left<.4)tag.style.left='0';else{tag.style.left=at(o.value);tag.style.transform='translateX(-50%)';}track.append(tag);}
   }
   strip.append(track);summary.append(strip);
   const legend=node('dl');legend.className='explorer-strip-legend';
   for(const [key,label,amount,cls] of [['lower','Soglia inferiore',r.lowerFence,'band'],['median','Valore mediano',r.median,'median'],['upper','Soglia superiore',r.upperFence,'band']]){
     const item=node('div');item.className='is-'+cls;const shown=node('dd',fmt(amount));shown.dataset.outlierValue=key;item.append(node('dt',label),shown);legend.append(item);
   }
   summary.append(legend);
   const key=node('p');key.className='explorer-strip-key';
   const swatch=(cls,text)=>{const s=node('span',text);s.className='explorer-strip-key-'+cls;return s;};
   key.append(swatch('band','Fascia attesa'),swatch('in','Comune nella fascia'),swatch('out','Comune fuori scala'));
   summary.append(key);
   const how=node('div');
   how.append(node('p','Un valore è fuori scala quando esce dalla fascia attesa. La fascia si ricava dai sette valori: dal primo al terzo quartile, allargati di 1,5 volte la loro distanza (regola di Tukey).'),node('p','Con sette Comuni è una lettura descrittiva: non indica un errore nel dato, una qualità dell’amministrazione o una priorità. Un altro gruppo di Comuni darebbe soglie diverse.'));
   const ul=node('ul');
   for(const [field,label] of [['q1','Primo quartile'],['q3','Terzo quartile'],['iqr','Scarto interquartile'],['median','Mediana'],['lowerFence','Soglia inferiore'],['upperFence','Soglia superiore']]){const item=node('li',label+': '+number(r[field])+unit);item.dataset.outlierOriginal=field;ul.append(item);}
   how.append(ul,node('p','Valori di ogni Comune nella tabella.'));
   summary.append(fold('Come si legge',how));out.append(summary);
 }
 function rankingRows(response,selector,out){
   const r=response.result,observations=response.observations||[];
   const codes=root.towns.map(t=>t.code).sort();
   const usable=observations.filter(o=>typeof o.value==='number'&&Number.isFinite(o.value)&&!o.dataUnavailable&&!o.notApplicable);
   // Preserve native order and competition ranks verbatim. No sorting, rank
   // calculation, polarity interpretation or missing-value replacement in JS.
   if(r?.direction!=='descending'||r.ties!=='competition'||!Array.isArray(r.ranking)||
      canonical([...selector.towns].sort())!==canonical(codes)||response.coverage?.requested!==codes.length||
      r.ranking.length!==usable.length||r.ranking.length!==response.coverage?.usable||
      new Set(r.ranking.map(row=>row.geography)).size!==r.ranking.length)throw Error('incompatible_ranking_result');
   const ordered=r.ranking.map(row=>{
     const observation=usable.find(o=>o.geography===row.geography);
     if(!observation||!codes.includes(row.geography)||observation.unit==='category_code'||
        row.value!==observation.value||!Number.isInteger(row.rank)||row.rank<1||row.rank>r.ranking.length)throw Error('incompatible_ranking_row');
     return {...observation,nativeRank:row.rank};
   });
   const summary=node('section');summary.className='explorer-ranking';summary.setAttribute('aria-label','Ordine numerico descrittivo');
   summary.append(node('h4','Dal valore maggiore al minore'),node('p','A valori uguali corrisponde la stessa posizione (per esempio 1, 1, 3). L’ordine non è un giudizio sull’amministrazione.'),fold('Come leggere le posizioni',node('p','A valori uguali corrisponde la stessa posizione; la posizione seguente può saltare un numero. Questo ordine non indica una criticità o l’effetto di un intervento. Periodo, fonte e definizione sono riportati per ogni Comune.')));
   out.append(summary);
   return [...ordered,...observations.filter(o=>!r.ranking.some(row=>row.geography===o.geography))];
 }
 function shareState(){
   const p=new URLSearchParams();const operation=$('operation').value;
   p.set('indicatore',$('metric').value);p.set('dettaglio',$('view').value);p.set('domanda',operation);
   if(!allTowns.includes(operation))p.set('comune',$('town').value);
   if(operation==='benchmark_gap')p.set('riferimento',$('benchmark').value);
   return SHARE+'&'+p.toString();
 }
 function csvRows(response,observations,selector,operation){
   const metric=root.metrics.find(m=>m.metric===selector.metric).label,detailLabel=viewLabel(selector.dimension),reading=operations[operation]||operation;
   const rows=[['Indicatore','Dettaglio','Lettura','Territorio','Periodo','Valore','Unità','Nota','Fonte']];
   for(const o of observations){
     const note=o.nativeRank!==undefined?'Posizione '+o.nativeRank:(response.result?.observations||[]).find(x=>x.geography===o.geography)?.classification?outlierClasses[(response.result.observations.find(x=>x.geography===o.geography)).classification]:o.dataUnavailable?'Dato non disponibile':o.notApplicable?'Non applicabile':'';
     rows.push([metric,detailLabel,reading,townName(o.geography)+(o.localityName?' · '+o.localityName:''),periodLabel(o.period),o.unit==='category_code'?(o.categoryLabel||''):exact(o.value),o.unit==='category_code'?'':unitLabel(o),note,o.source||'']);
   }
   const r=response.status==='computed'?response.result:null;
   const add=(territory,period,amount,unit,note)=>rows.push([metric,detailLabel,reading,territory,period,exact(amount),unit,note,'']);
   if(r&&operation==='benchmark_gap')add(townName(r.geography)+' meno '+townName(r.benchmarkScope),periodLabel(r.period),r.value,unitLabel(r),'Scostamento');
   if(r&&operation==='weighted_ratio')add('Versilia · sette Comuni',periodLabel(r.period),r.value,unitLabel(r),'Rapporto aggregato');
   if(r&&changes.includes(operation))add(townName(selector.towns[0]),periodLabel(r.startPeriod)+' → '+periodLabel(r.endPeriod),r.value,unitLabel(r),reading);
   if(r&&operation==='trend')add(townName(selector.towns[0]),'Intera serie',r.slope,unitLabel({unit:r.unit.replace(/\/year$/u,'')})+' per anno','Pendenza stimata');
   if(r&&operation==='anomaly')for(const [key,label] of [['lowerFence','Soglia inferiore'],['median','Valore mediano'],['upperFence','Soglia superiore']])add('Sette Comuni','',r[key],unitLabel({unit:r.unit}),label);
   return rows;
 }
 function download(name,text,type){
   const url=URL.createObjectURL(new Blob([text],{type}));const a=node('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function tools(response,observations,selector,operation){
   const bar=node('div');bar.className='explorer-tools';bar.setAttribute('role','group');bar.setAttribute('aria-label','Usa questo risultato');
   const done=node('span');done.className='explorer-tools-status';done.setAttribute('role','status');
   const link=node('button','Copia il link');link.type='button';link.dataset.explorerTool='link';
   link.onclick=async()=>{const url=location.href;try{await navigator.clipboard.writeText(url);done.textContent='Link copiato: chi lo apre vede questa stessa lettura.';}catch{done.textContent=url;}};
   const csv=node('button','Scarica i dati (CSV)');csv.type='button';csv.dataset.explorerTool='csv';
   csv.onclick=()=>{const text=csvRows(response,observations,selector,operation).map(r=>r.map(csvCell).join(';')).join('\r\n')+'\r\n';download('osservatorio-versilia-'+fileSlug(root.metrics.find(m=>m.metric===selector.metric).label)+'.csv','\ufeff'+text,'text/csv;charset=utf-8');done.textContent='CSV scaricato con i valori esatti, separati da punto e virgola.';};
   const print=node('button','Stampa o salva in PDF');print.type='button';print.dataset.explorerTool='print';
   // Print a copy of the result alone: the rest of the page is not laid out, so no blank pages.
   print.onclick=()=>{const sheet=node('section');sheet.className='a7-explorer explorer-print-sheet';const copy=$('result').cloneNode(true);
     copy.removeAttribute('id');copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));copy.querySelectorAll('details').forEach(d=>d.open=true);
     sheet.append(copy);document.body.append(sheet);document.documentElement.classList.add('explorer-printing');
     const restore=()=>{document.documentElement.classList.remove('explorer-printing');sheet.remove();window.removeEventListener('afterprint',restore);};window.addEventListener('afterprint',restore);window.print();};
   bar.append(link,csv,print,done);return bar;
 }
 async function restore(){
   if(!location.hash.startsWith('#'+SHARE+'&'))return;
   const p=new URLSearchParams(location.hash.slice(SHARE.length+2));const entry=root.metrics.find(m=>m.metric===p.get('indicatore'));
   if(!entry){status('Il link aperto non corrisponde più a un indicatore disponibile. Scegli un tema per ricominciare.');return;}
   $('theme').value=entry.theme;await themeChanged();$('metric').value=entry.metric;await metricChanged();
   if(!detail)return;
   const wanted=p.get('dettaglio');if(wanted&&detail.views.some(v=>v.dimension===wanted)){$('view').value=wanted;setOperation();}
   const operation=p.get('domanda');if(Array.from($('operation').options).some(o=>o.value===operation)){$('operation').value=operation;setBenchmark();}
   const town=p.get('comune');if(town&&Array.from($('town').options).some(o=>o.value===town))$('town').value=town;
   const scope=p.get('riferimento');if(scope&&Array.from($('benchmark').options).some(o=>o.value===scope))$('benchmark').value=scope;
   setTown();
   document.getElementById('a7-explorer')?.scrollIntoView({block:'start'});
   if(!$('run').disabled)await execute({schemaVersion:1,steps:[{id:'selection',request:request()}]});
   else status('Il link aperto non corrisponde più a una lettura disponibile: controlla le scelte e premi «Mostra i dati».');
 }
 function render(){
   const response=current.steps[0].response;const selector=current.plan.steps[0].request.selectors[0];const operation=current.plan.steps[0].request.operation;
   const out=$('result');out.replaceChildren();out.hidden=false;
   const heading=node('h3',root.metrics.find(m=>m.metric===selector.metric).label);heading.id='explorer-result-title';out.append(heading);
   out.append(node('p',viewLabel(selector.dimension)+' · '+(operations[operation]||operation)));
   const printed=node('p','Osservatorio Versilia · Chiedi alla Versilia · '+location.href);printed.className='explorer-print-only';out.append(printed);
   const toolbar=node('div');out.append(toolbar);
   if(response.status!=='computed')out.append(node('p','Per questa scelta il calcolo non è disponibile. I valori sotto sono solo informativi.'));
   if(changes.includes(operation)&&response.status==='computed')renderChange(response,out,selector,operation);
   if(changes.includes(operation)&&response.status!=='computed')out.append(node('p','Nessuna variazione calcolabile per questi anni.'));
   if(operation==='trend'&&response.status==='computed')renderTrend(response,out,selector);
   if(operation==='trend'&&response.status!=='computed'){
     out.append(node('p','Nessuna tendenza stimata per questa scelta.'));
     for(const reason of response.reasons||[])if(trendReasons[reason])out.append(node('p',trendReasons[reason]));
   }
   if(operation==='anomaly'&&response.status==='computed')renderOutliers(response,out,selector);
   if(operation==='anomaly'&&response.status!=='computed'){
     out.append(node('p','Nessun valore fuori scala calcolabile per questa scelta.'));
     for(const reason of response.reasons||[])if(outlierReasons[reason])out.append(node('p',outlierReasons[reason]));
   }
   if(operation==='benchmark_gap'&&response.status==='computed')renderBenchmark(response,out);
   if(operation==='weighted_ratio'&&response.status==='computed')renderAggregation(response,out);
   if(operation==='weighted_ratio'&&response.status!=='computed')out.append(node('p','Il valore dell’intera Versilia non è disponibile per questa scelta. Le eventuali osservazioni comunali non lo sostituiscono.'));
   if(response.coverage&&response.coverage.usable<response.coverage.requested)out.append(node('p',`Dati disponibili per ${response.coverage.usable} su ${response.coverage.requested}. I dati mancanti restano tali: non vengono trattati come zero.`));
   const ranked=operation==='rank'&&response.status==='computed';
   const observations=ranked?rankingRows(response,selector,out):response.observations||[];
   if(operation==='rank'&&!ranked)out.append(node('p','Nessuna posizione numerica viene assegnata: i dati non permettono un ordine valido.'));
   if(response.warnings?.length||response.reasons?.length){
     // Italian readings for the public; original codes remain in the complete evidence.
     const limits=node('div');let untranslated=0;
     for(const [key,title] of [['reasons','Perché il calcolo non è disponibile'],['warnings','Cose da sapere prima di usare questo dato']])if(response[key]?.length){
       const texts=[...new Set(response[key].map(code=>limitsIt[key][code]??limitsIt.warnings[code]??(untranslated++,null)).filter(Boolean))];
       if(!texts.length)continue;limits.append(node('h4',title));const ul=node('ul');for(const text of texts){const li=node('li',text);li.dataset.limitReading=key;ul.append(li);}limits.append(ul);
     }
     if(untranslated)limits.append(node('p','Altre avvertenze tecniche sono riportate nell’evidenza completa.'));
     const summary=fold('Come leggere questo dato',limits);summary.classList.add('explorer-limits');out.append(summary);
   }
   // Never turn a category code into a number or use retained refusal values as a chart.
   const visible=observations.slice(pageIndex*20,(pageIndex+1)*20);
   const base=observations[0];
   const chart=response.status==='computed'&&!['lookup','anomaly'].includes(operation)&&base&&observations.length>1&&observations.every(o=>typeof o.value==='number'&&Number.isFinite(o.value)&&o.value>=0&&!o.dataUnavailable&&!o.notApplicable&&o.unit!=='category_code'&&['unit','dimension','population','definition','method'].every(k=>o[k]===base[k]))&&(observations.every(o=>o.period===base.period)||observations.every(o=>o.geography===base.geography));
   if(chart){
     const graph=node('div');graph.setAttribute('role','img');graph.setAttribute('aria-label','Confronto visivo delle osservazioni riportate nella tabella. Scala da zero; valori mancanti non rappresentati.');
     const maximum=Math.max(...observations.map(o=>o.value))||1;
     graph.append(node('p',`Scala da 0 a ${number(maximum)} ${unitLabel(base)}.`));
     for(const o of visible){const row=node('div');row.className='explorer-bar-row';if(ranked)row.dataset.rankingGeography=o.geography;const track=node('span');track.className='explorer-bar-track';const bar=node('span');bar.className='explorer-bar';bar.style.display='block';bar.style.width=(o.value/maximum*100)+'%';track.append(bar);row.append(node('span',(['series','trend'].includes(operation)||changes.includes(operation))?periodLabel(o.period):(ranked?String(o.nativeRank)+'. ':'')+townName(o.geography)),track,node('span',value(o)));graph.append(row);}out.append(graph);
   }
   const wrap=node('div');wrap.className='explorer-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Osservazioni originali · tabella scorribile');wrap.setAttribute('aria-describedby','explorer-table-hint');const table=node('table');table.append(node('caption','Osservazioni originali · periodo e fonte per ogni riga'));
   const head=node('thead');const hr=node('tr');for(const h of [...(ranked?['Posizione numerica']:[]),'Territorio','Periodo','Valore','Fonte']){const th=node('th',h);th.scope='col';hr.append(th);}head.append(hr);table.append(head);
   const body=node('tbody');for(const o of visible){const tr=node('tr');if(ranked){tr.dataset.rankingGeography=o.geography;const position=node('td',o.nativeRank===undefined?'—':String(o.nativeRank));position.dataset.nativeRank=o.nativeRank===undefined?'':String(o.nativeRank);tr.append(position);}tr.append(node('td',townName(o.geography)+(o.localityName?' · '+o.localityName:'')),node('td',periodLabel(o.period)));const cell=node('td',value(o));cell.dataset.observationValue='true';if(o.unit!=='category_code'&&o.value!==null&&o.value!==undefined&&!o.dataUnavailable&&!o.notApplicable)cell.append(node('span',' '+(unitLabel(o))));tr.append(cell);
     const source=node('td');const link=sourceURL(o.source);if(link){const a=node('a','Fonte');a.href=link;a.target='_blank';a.rel='noopener noreferrer';source.append(a);}else source.append(node('span',String(o.source||'Fonte non dichiarata')));
    tr.append(source);body.append(tr);}
   table.append(body);wrap.append(table);const hint=node('p','Scorri la tabella in orizzontale per leggere tutte le colonne.');hint.id='explorer-table-hint';hint.className='explorer-scroll-hint';out.append(hint,wrap);
   if(!observations.length)out.append(node('p','Nessun valore disponibile per questa scelta.'));
   if(observations.length>20){const nav=node('nav');nav.setAttribute('aria-label','Pagine delle osservazioni');const prev=node('button','Precedenti');prev.type='button';prev.disabled=pageIndex===0;prev.onclick=()=>{pageIndex--;render();};const next=node('button','Successive');next.type='button';next.disabled=(pageIndex+1)*20>=observations.length;next.onclick=()=>{pageIndex++;render();};nav.append(prev,node('span',`Pagina ${pageIndex+1} di ${Math.ceil(observations.length/20)} `),next);out.append(nav);}
   if(response.excluded?.length)out.append(node('p','Alcuni valori non sono disponibili e non sono stati stimati.'));
   // Machine-readable evidence kept in the page for verification and export, not shown.
   toolbar.replaceWith(tools(response,observations,selector,operation));
   const provenance=node('pre',JSON.stringify(current,null,2));provenance.dataset.explorerEvidence='true';provenance.hidden=true;out.append(provenance);
 }
 $('theme').addEventListener('change',safe(themeChanged));
 $('metric').addEventListener('change',safe(async()=>{if(!$('metric').value){revoke();detail=null;$('view').replaceChildren();$('operation').replaceChildren();setBenchmark();setTown();$('run').disabled=true;return;}await metricChanged();}));
 $('filter').addEventListener('input',()=>{if(detail)filterViews();});
 $('view').addEventListener('change',setOperation);
 $('operation').addEventListener('change',()=>{revoke();setBenchmark();setTown();});
 $('benchmark').addEventListener('change',()=>{revoke();setTown();status('Riferimento modificato: premi «Mostra i dati».');});
 $('town').addEventListener('change',()=>{revoke();setTown();});
 $('form').addEventListener('submit',event=>{event.preventDefault();if(!$('run').disabled)safe(()=>execute({schemaVersion:1,steps:[{id:'selection',request:request()}]}))();});
 $('accept').addEventListener('click',()=>{if(pending){const plan=pending;safe(()=>execute(plan,true))();}});
 $('cancel').addEventListener('click',()=>{revoke();status('Consultazione annullata. Puoi cambiare scelta.');});
 async function initialize(){
   revoke();fields.disabled=true;$('retry').hidden=true;status('Verifica della versione dei dati…');
   runtime=await openRuntime();root=await runtime.discover();
   if(root.catalogSha256!==presentation.catalogSha256)throw Error('presentation_catalog_mismatch');
   $('theme').replaceChildren(option('','Scegli un tema'),...[...new Set(root.metrics.map(m=>m.theme))].map(key=>option(key,presentation.themes[key]||key)));
   $('metric').replaceChildren();$('view').replaceChildren();$('operation').replaceChildren();$('town').replaceChildren(...[...root.towns].sort((a,b)=>a.name.localeCompare(b.name,'it')).map(t=>option(t.code,t.name)));
   detail=null;setBenchmark();setTown();$('run').disabled=true;fields.disabled=false;
   status(root.scope==='all_metrics'?'Scegli un tema per esplorare il catalogo. Le capacità consultabili dipendono dalla vista.':'Anteprima su un sottoinsieme esplicito del catalogo. Non rappresenta tutte le capacità disponibili.');
   await restore();
 }
 $('retry').onclick=safe(initialize);
 await safe(initialize)();
}
