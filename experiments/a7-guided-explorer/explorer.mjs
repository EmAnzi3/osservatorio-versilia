// Presentation over the original anchored A6 transport. No numerical engine.
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const fold=(title,content)=>{const n=node('details');n.append(node('summary',title),content);return n;};
const operations={observe:'Un dato comunale',lookup:'Analisi per località',compare:'Confronto fra i sette Comuni',series:'Serie di un Comune',rank:'Ordine numerico dei sette Comuni',benchmark_gap:'Confronto con Toscana o Italia',absolute_change:'Variazione assoluta',relative_change:'Variazione percentuale',weighted_ratio:'Rapporto aggregato della Versilia',percentage_points:'Variazione in punti percentuali',trend:'Tendenza della serie',correlation:'Associazione',anomaly:'Anomalia'};
const profiles={observe:'current',lookup:'current',compare:'comparison',series:'history',rank:'ranking',benchmark_gap:'benchmark',weighted_ratio:'aggregation',absolute_change:'changes',relative_change:'changes',percentage_points:'changes',trend:'trends'};
const changes=['absolute_change','relative_change','percentage_points'];
// Display translations only: these labels never authorize a calculation or
// replace the original reasons preserved in the evidence.
const trendReasons={census_historical_dimension_not_available:'Per questa vista il motore non espone la serie storica necessaria. Questo non significa che il dato sia assente dalla fonte.',insufficient_observations:'La serie restituisce un numero di osservazioni insufficiente per stimare la tendenza.',distinct_finance_massarosa_osl_temporal_perimeter_not_attested:'La continuità del perimetro fra gestione ordinaria e OSL non è attestata per questa selezione.'};
const units={count:'unità',meters:'m',hectares:'ha',cubicMetres:'m³',currency2:'€',eurliter:'€/l',eurm2:'€/m²',eurm2month:'€/m²/mese',per10k:'per 10.000',km2:'km²',celsius:'°C',index:'indice',percent_change:'%',sqm_per_resident:'m²/residente',km_per_km2:'km/km²',currency_per_resident:'€/residente',number:'unità',percentage_points:'punti percentuali',percentagePoints:'punti percentuali',hectaresPerFarm:'ha/azienda',per1000:'per 1.000',per100:'per 100',per100k:'per 100.000',minutes:'minuti',hours:'ore',people:'persone',squareKm:'km²',peoplePerSquareKm:'residenti/km²',eurPerResident:'€/residente',invalsi_score:'punti INVALSI',nights:'notti',decimal:'',percent:'%',currency:'€',years:'anni',category_code:'categoria',millionCurrency:'milioni di €',studentsPerClass:'alunni per classe'};
const number=x=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:15}).format(x);
const concise=x=>new Intl.NumberFormat('it-IT',x!==0&&Math.abs(x)<.01?{maximumSignificantDigits:3}:{maximumFractionDigits:2}).format(x);
const value=o=>o.notApplicable?'Non applicabile':o.dataUnavailable||o.value===null||o.value===undefined?'n.d.':o.unit==='category_code'?o.categoryLabel||'Categoria senza etichetta':typeof o.value==='number'?number(o.value):String(o.value);
const sourceURL=x=>{try{const u=new URL(x);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}};
const option=(value,label,disabled=false)=>{const o=node('option',label);o.value=value;o.disabled=disabled;return o;};
const canonical=x=>JSON.stringify(x); // used only to preserve the exact UI selection snapshot

export async function startExplorer(openRuntime,presentation){
 const $=id=>document.getElementById('explorer-'+id);
 const fields=$('form').querySelector('fieldset');
 const unitLabel=o=>units[o.unit]??((presentation.metrics[$('metric').value]?.unit===o.unit?presentation.metrics[$('metric').value]?.unitLabel:null)||o.unit);
 let runtime,root,detail,generation=0,pending=null,current=null,pageIndex=0;
 const status=text=>{$('status').textContent=text;};
 const revoke=()=>{generation++;pending=null;current=null;$('result').hidden=true;$('result').replaceChildren();$('consent').hidden=true;};
 const fail=()=>{revoke();runtime=null;fields.disabled=true;$('retry').hidden=false;status('Non possiamo verificare i dati di questa selezione. Nessun risultato viene mostrato. Riprova per caricare la stessa versione.');};
 const safe=fn=>async(...args)=>{try{await fn(...args);}catch{fail();}};
 const active=async(promise,ticket)=>{try{return await promise;}catch(error){if(ticket===generation)throw error;return null;}};
 const townName=code=>({tuscany:'Toscana',italy:'Italia'})[code]||root.towns.find(t=>t.code===code)?.name||code;
 const benchmarkScopes=()=>detail?.declaration.benchmarkScopesByDimension[view()?.dimension]?.filter(s=>['tuscany','italy'].includes(s))||[];
 const viewLabel=dimension=>{
   const named=presentation.metrics[$('metric').value]?.views?.[dimension];
   if(named)return named;
   return ({total:'Vista principale',territoryTotal:'Totale territoriale nativo','stat:min':'Valore minimo','stat:mean':'Valore medio','stat:max':'Valore massimo','sex:men':'Sesso: maschi','sex:women':'Sesso: femmine'})[dimension]||dimension.replace(/^ateco:/u,'ATECO ').replace(/\|active$/u,' · unità locali attive').replace(/\|artisan$/u,' · unità locali artigiane').replace(/^part:/u,'Voce: ');
 };
 function view(){return detail?.views.find(v=>v.dimension===$('view').value);}
 function setOperation(){
   revoke();const v=view();$('operation').replaceChildren();
   for(const operation of v?.declaredOperations||[]){const available=Boolean(v.shards[profiles[operation]])&&(operation!=='benchmark_gap'||benchmarkScopes().length>0);$('operation').append(option(operation,(operations[operation]||operation)+(available?'':' · non ancora consultabile qui'),!available));}
   const available=Array.from($('operation').options).find(o=>!o.disabled);
   if(available)$('operation').value=available.value;
   else{$('operation').value='';status('Questa vista è dichiarata dal motore ma non è materializzata in questa versione. Non significa che il dato sia assente.');}
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
   const all=['compare','rank','weighted_ratio'].includes($('operation').value);$('town').disabled=all;
   $('town-field').hidden=aggregate||ranking;
   $('town').setAttribute('aria-describedby','explorer-reference');
   $('reference').textContent=aggregate?'Ambito: tutti i sette Comuni della Versilia. Il rapporto usa componenti e periodi verificati dal motore, non la media dei tassi comunali. Una copertura incompleta non produce un valore dell’intera Versilia.':$('operation').value==='benchmark_gap'?'Scegli esplicitamente Toscana o Italia fra i riferimenti ammessi per questa vista. Il periodo nativo e le fonti sono riportati nel risultato.':all?'Il confronto comprende sette osservazioni comunali, non un aggregato della Versilia. Il periodo effettivo è riportato per ogni dato.':'Riferimento predefinito della vista: il periodo effettivo compare nel risultato. Nessun anno arbitrario viene sostituito con un altro.';
   if(changes.includes($('operation').value)){
     const periods=view()?.changePeriodsByTown?.[$('town').value];
     $('reference').textContent=periods?'Variazione fra il primo e l’ultimo periodo della serie nativa: '+String(periods[0])+' → '+String(periods[1])+'. Non è una variazione annua. Il motore verifica comparabilità e copertura; nessun estremo mancante viene sostituito.':'Questa vista non espone due estremi della serie nativa. Il motore conserva il motivo del rifiuto; nessun periodo viene inventato.';
   }
   if(ranking)$('reference').textContent='Ambito: tutti i sette Comuni, dal valore maggiore al minore al riferimento nativo della vista. Pari merito conservati. La posizione numerica non indica criticità, merito amministrativo o effetto di un intervento. Nessun dato mancante viene trasformato in zero.';
   if($('operation').value==='trend')$('reference').textContent='Tendenza dell’intera serie nativa di un Comune. Il motore verifica periodi, copertura e comparabilità; non scegliamo finestre o scartiamo dati mancanti. Nessuna previsione: periodi effettivi, pendenza e numero di osservazioni compaiono nel risultato, quando ammesso.';
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
   detail=loaded;filterViews();
   if(!$('run').disabled)status('Scegli vista e operazione, poi mostra i dati.');
 }
 async function themeChanged(){
   revoke();const members=root.metrics.filter(m=>m.theme===$('theme').value);
   $('metric').replaceChildren(option('','Scegli un indicatore'),...members.map(m=>option(m.metric,m.label)));
   detail=null;$('view').replaceChildren();$('operation').replaceChildren();setBenchmark();setTown();$('run').disabled=true;$('description').textContent='';
   status('Scegli un indicatore del tema selezionato.');
 }
 function request(){
   const operation=$('operation').value;
   const periods=changes.includes(operation)?view()?.changePeriodsByTown?.[$('town').value]:null;
   return {operation,...(operation==='benchmark_gap'?{benchmark:$('benchmark').value}:{}),selectors:[{metric:$('metric').value,dimension:$('view').value,...(periods?{periods:[...periods]}:{}),towns:['compare','rank','weighted_ratio'].includes(operation)?root.towns.map(t=>t.code).sort():[$('town').value]}]};
 }
 function show(result){
   current=result;pageIndex=0;render();
   status(result.steps[0].response.status==='computed'?'Dati caricati dalla versione verificata.':'Il motore non ammette il calcolo richiesto. Il motivo e le eventuali osservazioni conservate sono riportati sotto.');
 }
 async function execute(plan,approvedPartial=false){
   revoke();const ticket=generation;const frozen=canonical(plan);status('Verifica e caricamento dei dati selezionati…');
   const result=await active(runtime.run(JSON.parse(frozen),{approvedPartial}),ticket);
   if(ticket!==generation)return;
   if(result.resolution==='needs_confirmation'){pending=JSON.parse(frozen);$('consent').hidden=false;status('Serve la tua scelta sulla copertura incompleta. Nessun valore è ancora mostrato.');return;}
   if(result.resolution!=='resolved'){status('Questa richiesta non è materializzata nel trasporto corrente. Non è una dichiarazione di assenza del dato.');return;}
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
   summary.append(cards,node('p','Sintesi arrotondata per la lettura; valori originali nella tabella sottostante.'),node('p','Periodo del risultato: '+String(r.period??'Non dichiarato')+'. Scostamento = valore comunale meno riferimento. Un valore positivo o negativo non è un giudizio sulla qualità amministrativa.'));
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
   summary.append(node('p','Rapporto delle somme dei numeratori e dei denominatori, con la scala prevista dalla misura. Non è la media dei tassi comunali né una somma generica.'),node('p','Sintesi arrotondata per la lettura; valore originale nelle componenti del calcolo.'),node('p','Periodo del risultato: '+String(r.period??'Non dichiarato')+'.'));
   for(const [key,label] of [['numeratorPeriod','Periodo del numeratore'],['denominatorPeriod','Periodo del denominatore']])if(r[key]!==undefined)summary.append(node('p',label+': '+String(r[key])));
   summary.append(node('p','Perimetro: '+codes.map(townName).join(', ')+'. Le osservazioni comunali seguenti restano distinte dal rapporto aggregato.'));
   const components=node('div');const list=node('ul');
   for(const [key,label] of [['value','Valore aggregato originale'],['numerator','Numeratore aggregato'],['denominator','Denominatore aggregato'],['scale','Scala']]){
     const item=node('li',label+': '+number(r[key])+(key==='value'?' '+unitLabel(r):''));item.dataset.aggregationComponent=key;list.append(item);
   }
   components.append(list,node('p','Definizioni, unità e periodi delle componenti seguono il metodo originale riportato nelle osservazioni.'));
   summary.append(fold('Componenti del calcolo',components));out.append(summary);
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
   summary.append(node('h4',townName(selector.towns[0])+' · '+String(r.startPeriod)+' → '+String(r.endPeriod)));
   const cards=node('dl');cards.className='explorer-benchmark-values';
   for(const [key,label,amount,unit] of [['start','Valore iniziale · '+String(r.startPeriod),start.value,unitLabel(start)],['end','Valore finale · '+String(r.endPeriod),end.value,unitLabel(end)],['change',operations[operation],r.value,unitLabel(r)]]){
     const card=node('div');const shown=node('dd',(key==='change'&&amount>0?'+':'')+concise(amount)+' '+unit);shown.dataset.changeValue=key;card.append(node('dt',label),shown);cards.append(card);
   }
   summary.append(cards,node('p','Sintesi arrotondata per la lettura; valori e periodi originali nella tabella. La variazione riguarda questi due periodi, non un tasso annuo né l’effetto di un intervento. Il segno non indica automaticamente miglioramento o peggioramento.'));
   summary.append(node('p',operation==='relative_change'?'Variazione percentuale rispetto al valore iniziale. È distinta dalla differenza in punti percentuali.':r.unit==='percentage_points'||r.unit==='percentagePoints'?'Differenza espressa in punti percentuali, distinta dalla variazione percentuale relativa.':'Differenza fra valore finale e iniziale, nell’unità della misura.'));
   if(response.formula)summary.append(fold('Formula originale del motore',node('p',response.formula)));
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
   for(const [key,label,text] of [['slope','Pendenza stimata',(r.slope>0?'+':'')+concise(r.slope)+' '+slopeUnit],['periods','Periodi osservati',String(observations[0].period)+' → '+String(observations.at(-1).period)],['n','Osservazioni utilizzate',String(r.n)]]){
     const card=node('div'),shown=node('dd',text);shown.dataset.trendValue=key;card.append(node('dt',label),shown);cards.append(card);
   }
   summary.append(cards,node('p','Stima OLS sull’intera serie nativa, usando gli anni effettivi. La pendenza non descrive una variazione identica in ogni anno e non è una previsione.'),node('p','Il segno non indica automaticamente miglioramento o peggioramento, né l’effetto di un intervento.'));
   const method=node('div');
   method.append(node('p','La retta dei minimi quadrati (OLS) sintetizza la tendenza della serie. Non è un test di significatività. Nessun confronto o ordinamento fra pendenze comunali.'),node('p','La sintesi è arrotondata per la lettura. La precisione originale e l’asse temporale completo sono conservati qui; osservazioni, fonti e definizioni sono nella tabella.'));
   if(baseUnit==='percentage_points')method.append(node('p','Per una misura percentuale, la pendenza è in punti percentuali per anno, non in percentuale relativa.'));
   const original=node('p','Pendenza originale: '+new Intl.NumberFormat('it-IT',{maximumSignificantDigits:21}).format(r.slope)+' '+slopeUnit);original.dataset.trendOriginal='true';
   const axis=node('p','Asse temporale effettivo: '+r.timeAxis.map(String).join(', '));axis.dataset.trendAxis='true';
   method.append(original,axis,node('p','Metodo originale: '+r.method+'. Gli intervalli fra gli anni restano quelli originali; nessuna osservazione è aggiunta per colmare lacune.'));
   if(response.formula)method.append(node('p','Formula originale: '+response.formula));
   summary.append(fold('Metodo e periodi utilizzati',method));out.append(summary);
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
   summary.append(node('h4','Dal valore maggiore al minore'),node('p','Posizioni descrittive, senza valutazioni amministrative. Pari merito conservati sulla precisione originale: per esempio 1, 1, 3.'),fold('Come leggere le posizioni',node('p','A valori uguali corrisponde la stessa posizione; la posizione seguente può saltare un numero. Questo ordine non indica una criticità o l’effetto di un intervento. Periodo, fonte e definizione sono riportati per ogni Comune.')));
   out.append(summary);
   return [...ordered,...observations.filter(o=>!r.ranking.some(row=>row.geography===o.geography))];
 }
 function render(){
   const response=current.steps[0].response;const selector=current.plan.steps[0].request.selectors[0];const operation=current.plan.steps[0].request.operation;
   const out=$('result');out.replaceChildren();out.hidden=false;
   const heading=node('h3',root.metrics.find(m=>m.metric===selector.metric).label);heading.id='explorer-result-title';out.append(heading);
   out.append(node('p',viewLabel(selector.dimension)+' · '+(operations[operation]||operation)));
   if(response.status!=='computed')out.append(node('p','Calcolo non disponibile per questa selezione. Le eventuali osservazioni seguenti sono conservate nel rifiuto originale: non costituiscono un risultato calcolato.'));
   if(changes.includes(operation)&&response.status==='computed')renderChange(response,out,selector,operation);
   if(changes.includes(operation)&&response.status!=='computed')out.append(node('p','Nessuna variazione è calcolata per questi riferimenti. Le osservazioni conservate non autorizzano una differenza sostitutiva.'));
   if(operation==='trend'&&response.status==='computed')renderTrend(response,out,selector);
   if(operation==='trend'&&response.status!=='computed'){
     out.append(node('p','Nessuna tendenza stimata per questa selezione. Le osservazioni conservate nel rifiuto non autorizzano una pendenza sostitutiva o una previsione.'));
     for(const reason of response.reasons||[])if(trendReasons[reason])out.append(node('p',trendReasons[reason]));
   }
   if(operation==='benchmark_gap'&&response.status==='computed')renderBenchmark(response,out);
   if(operation==='weighted_ratio'&&response.status==='computed')renderAggregation(response,out);
   if(operation==='weighted_ratio'&&response.status!=='computed')out.append(node('p','Nessun rapporto aggregato dell’intera Versilia è disponibile per questa selezione. Le eventuali osservazioni comunali non lo sostituiscono.'));
   if(response.coverage)out.append(node('p',`Copertura: ${response.coverage.usable} osservazioni utilizzabili su ${response.coverage.requested} richieste. I dati mancanti restano distinti da zero.`));
   const ranked=operation==='rank'&&response.status==='computed';
   const observations=ranked?rankingRows(response,selector,out):response.observations||[];
   if(operation==='rank'&&!ranked)out.append(node('p','Nessuna posizione numerica viene assegnata. Le osservazioni conservate nel rifiuto non costituiscono un ordinamento valido.'));
   if(response.warnings?.length||response.reasons?.length){
     out.append(node('p',operation==='rank'?'Consulta i limiti metodologici prima di interpretare o citare questi dati.':'Sono presenti limiti metodologici. Prima di interpretare o citare questi dati consulta definizioni, avvertenze e motivi originali. Nessuna posizione numerica misura la qualità di un’amministrazione.'));
     const limits=node('div');for(const [key,title] of [['reasons','Motivi del rifiuto'],['warnings','Avvertenze originali']])if(response[key]?.length){limits.append(node('h4',title));const ul=node('ul');for(const item of response[key])ul.append(node('li',item));limits.append(ul);}out.append(fold('Limiti del dato · testi originali del motore',limits));
   }
   // Never turn a category code into a number or use retained refusal values as a chart.
   const visible=observations.slice(pageIndex*20,(pageIndex+1)*20);
   const base=observations[0];
   const chart=response.status==='computed'&&operation!=='lookup'&&base&&observations.length>1&&observations.every(o=>typeof o.value==='number'&&Number.isFinite(o.value)&&o.value>=0&&!o.dataUnavailable&&!o.notApplicable&&o.unit!=='category_code'&&['unit','dimension','population','definition','method'].every(k=>o[k]===base[k]))&&(observations.every(o=>o.period===base.period)||observations.every(o=>o.geography===base.geography));
   if(chart){
     const graph=node('div');graph.setAttribute('role','img');graph.setAttribute('aria-label','Confronto visivo delle osservazioni riportate nella tabella. Scala da zero; valori mancanti non rappresentati.');
     const maximum=Math.max(...observations.map(o=>o.value))||1;
     graph.append(node('p',`Scala da 0 a ${number(maximum)} ${unitLabel(base)}. Nessuna interpolazione fra periodi.`));
     for(const o of visible){const row=node('div');row.className='explorer-bar-row';if(ranked)row.dataset.rankingGeography=o.geography;const track=node('span');track.className='explorer-bar-track';const bar=node('span');bar.className='explorer-bar';bar.style.display='block';bar.style.width=(o.value/maximum*100)+'%';track.append(bar);row.append(node('span',(['series','trend'].includes(operation)||changes.includes(operation))?String(o.period):(ranked?String(o.nativeRank)+'. ':'')+townName(o.geography)),track,node('span',value(o)));graph.append(row);}out.append(graph);
   }
   const wrap=node('div');wrap.className='explorer-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Osservazioni originali · tabella scorribile');wrap.setAttribute('aria-describedby','explorer-table-hint');const table=node('table');table.append(node('caption','Osservazioni originali · periodo e fonte per ogni riga'));
   const head=node('thead');const hr=node('tr');for(const h of [...(ranked?['Posizione numerica']:[]),'Territorio','Periodo','Valore','Fonte e definizione']){const th=node('th',h);th.scope='col';hr.append(th);}head.append(hr);table.append(head);
   const body=node('tbody');for(const o of visible){const tr=node('tr');if(ranked){tr.dataset.rankingGeography=o.geography;const position=node('td',o.nativeRank===undefined?'—':String(o.nativeRank));position.dataset.nativeRank=o.nativeRank===undefined?'':String(o.nativeRank);tr.append(position);}tr.append(node('td',townName(o.geography)+(o.localityName?' · '+o.localityName:'')),node('td',String(o.period??'Non dichiarato')));const cell=node('td',value(o));cell.dataset.observationValue='true';if(o.unit!=='category_code'&&o.value!==null&&o.value!==undefined&&!o.dataUnavailable&&!o.notApplicable)cell.append(node('span',' '+(unitLabel(o))));tr.append(cell);
     const source=node('td');const link=sourceURL(o.source);if(link){const a=node('a','Fonte');a.href=link;a.target='_blank';a.rel='noopener noreferrer';source.append(a);}else source.append(node('span',String(o.source||'Fonte non dichiarata')));
     const explanation=node('div');for(const [key,label] of [['definition','Definizione'],['population','Popolazione descritta'],['numeratorPeriod','Periodo del numeratore'],['denominatorPeriod','Periodo del denominatore'],['periodBasis','Riferimento temporale'],['method','Metodo'],['parameter','Parametro'],['referenceText','Riferimento pubblicato, senza valutazione di conformità']])if(o[key])explanation.append(node('p',label+': '+o[key]));if(operation==='weighted_ratio')for(const [key,label] of [['numerator','Numeratore'],['denominator','Denominatore'],['scale','Scala']])if(typeof o[key]==='number'&&Number.isFinite(o[key]))explanation.append(node('p',label+': '+number(o[key])));source.append(fold('Definizione originale',explanation));tr.append(source);body.append(tr);}
   table.append(body);wrap.append(table);const hint=node('p','Scorri la tabella in orizzontale per leggere tutte le colonne.');hint.id='explorer-table-hint';hint.className='explorer-scroll-hint';out.append(hint,wrap);
   if(!observations.length)out.append(node('p','Nessuna osservazione utilizzabile restituita. Non è stato inserito alcuno zero sostitutivo.'));
   if(observations.length>20){const nav=node('nav');nav.setAttribute('aria-label','Pagine delle osservazioni');const prev=node('button','Precedenti');prev.type='button';prev.disabled=pageIndex===0;prev.onclick=()=>{pageIndex--;render();};const next=node('button','Successive');next.type='button';next.disabled=(pageIndex+1)*20>=observations.length;next.onclick=()=>{pageIndex++;render();};nav.append(prev,node('span',`Pagina ${pageIndex+1} di ${Math.ceil(observations.length/20)} `),next);out.append(nav);}
   if(response.excluded?.length)out.append(fold('Osservazioni escluse · nessuna imputazione',node('pre',JSON.stringify(response.excluded,null,2))));
   const provenance=node('pre',JSON.stringify(current,null,2));provenance.dataset.explorerEvidence='true';out.append(fold('Evidenza completa per la verifica',provenance));
 }
 $('theme').addEventListener('change',safe(themeChanged));
 $('metric').addEventListener('change',safe(async()=>{if(!$('metric').value){revoke();detail=null;$('view').replaceChildren();$('operation').replaceChildren();setBenchmark();setTown();$('run').disabled=true;return;}await metricChanged();}));
 $('filter').addEventListener('input',()=>{if(detail)filterViews();});
 $('view').addEventListener('change',setOperation);
 $('operation').addEventListener('change',()=>{revoke();setBenchmark();setTown();});
 $('benchmark').addEventListener('change',()=>{revoke();setTown();status('Riferimento modificato. Mostra i dati per verificare la nuova selezione.');});
 $('town').addEventListener('change',()=>{revoke();setTown();});
 $('form').addEventListener('submit',event=>{event.preventDefault();if(!$('run').disabled)safe(()=>execute({schemaVersion:1,steps:[{id:'selection',request:request()}]}))();});
 $('accept').addEventListener('click',()=>{if(pending){const plan=pending;safe(()=>execute(plan,true))();}});
 $('cancel').addEventListener('click',()=>{revoke();status('Consultazione annullata. Puoi cambiare selezione.');});
 async function initialize(){
   revoke();fields.disabled=true;$('retry').hidden=true;status('Verifica della versione dei dati…');
   runtime=await openRuntime();root=await runtime.discover();
   if(root.catalogSha256!==presentation.catalogSha256)throw Error('presentation_catalog_mismatch');
   $('theme').replaceChildren(option('','Scegli un tema'),...[...new Set(root.metrics.map(m=>m.theme))].map(key=>option(key,presentation.themes[key]||key)));
   $('metric').replaceChildren();$('view').replaceChildren();$('operation').replaceChildren();$('town').replaceChildren(...[...root.towns].sort((a,b)=>a.name.localeCompare(b.name,'it')).map(t=>option(t.code,t.name)));
   detail=null;setBenchmark();setTown();$('run').disabled=true;fields.disabled=false;
   status(root.scope==='all_metrics'?'Scegli un tema per esplorare il catalogo. Le capacità consultabili dipendono dalla vista.':'Anteprima su un sottoinsieme esplicito del catalogo. Non rappresenta tutte le capacità disponibili.');
 }
 $('retry').onclick=safe(initialize);
 await safe(initialize)();
}
