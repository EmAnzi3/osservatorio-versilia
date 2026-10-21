// Presentation over the original anchored A6 transport. No numerical engine.
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const fold=(title,content)=>{const n=node('details');n.append(node('summary',title),content);return n;};
const operations={observe:'Un dato comunale',lookup:'Analisi per località',compare:'Confronto fra i sette Comuni',series:'Serie di un Comune',rank:'Ordine numerico dei sette Comuni',benchmark_gap:'Scostamento dal riferimento',absolute_change:'Variazione assoluta',relative_change:'Variazione percentuale',weighted_ratio:'Rapporto da componenti',percentage_points:'Variazione in punti percentuali',trend:'Andamento',correlation:'Associazione',anomaly:'Anomalia'};
const profiles={observe:'current',lookup:'current',compare:'comparison',series:'history',rank:'ranking'};
const units={number:'unità',percent:'%',currency:'€',years:'anni',category_code:'categoria',millionCurrency:'milioni di €',studentsPerClass:'alunni per classe'};
const number=x=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:15}).format(x);
const value=o=>o.notApplicable?'Non applicabile':o.dataUnavailable||o.value===null||o.value===undefined?'n.d.':o.unit==='category_code'?o.categoryLabel||'Categoria senza etichetta':typeof o.value==='number'?number(o.value):String(o.value);
const sourceURL=x=>{try{const u=new URL(x);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}};
const option=(value,label,disabled=false)=>{const o=node('option',label);o.value=value;o.disabled=disabled;return o;};
const canonical=x=>JSON.stringify(x); // used only to preserve the exact UI selection snapshot

export async function startExplorer(openRuntime,presentation){
 const $=id=>document.getElementById('explorer-'+id);
 const fields=$('form').querySelector('fieldset');
 const unitLabel=o=>units[o.unit]||(presentation.metrics[$('metric').value]?.unit===o.unit?presentation.metrics[$('metric').value]?.unitLabel:null)||o.unit;
 let runtime,root,detail,generation=0,pending=null,current=null,pageIndex=0;
 const status=text=>{$('status').textContent=text;};
 const revoke=()=>{generation++;pending=null;current=null;$('result').hidden=true;$('result').replaceChildren();$('consent').hidden=true;};
 const fail=()=>{revoke();runtime=null;fields.disabled=true;$('retry').hidden=false;status('Non possiamo verificare i dati di questa selezione. Nessun risultato viene mostrato. Riprova per caricare la stessa versione.');};
 const safe=fn=>async(...args)=>{try{await fn(...args);}catch{fail();}};
 const active=async(promise,ticket)=>{try{return await promise;}catch(error){if(ticket===generation)throw error;return null;}};
 const townName=code=>root.towns.find(t=>t.code===code)?.name||code;
 const viewLabel=dimension=>{
   const named=presentation.metrics[$('metric').value]?.views?.[dimension];
   if(named)return named;
   return ({total:'Vista principale',territoryTotal:'Totale territoriale nativo','sex:men':'Sesso: maschi','sex:women':'Sesso: femmine'})[dimension]||dimension.replace(/^ateco:/u,'ATECO ').replace(/\|active$/u,' · unità locali attive').replace(/\|artisan$/u,' · unità locali artigiane').replace(/^part:/u,'Voce: ');
 };
 function view(){return detail?.views.find(v=>v.dimension===$('view').value);}
 function setOperation(){
   revoke();const v=view();$('operation').replaceChildren();
   for(const operation of v?.declaredOperations||[]){const available=Boolean(v.shards[profiles[operation]]);$('operation').append(option(operation,(operations[operation]||operation)+(available?'':' · non ancora consultabile qui'),!available));}
   const available=Array.from($('operation').options).find(o=>!o.disabled);
   if(available)$('operation').value=available.value;
   else{$('operation').value='';status('Questa vista è dichiarata dal motore ma non è materializzata in questa versione. Non significa che il dato sia assente.');}
   setTown();
 }
 function setTown(){
   const all=['compare','rank'].includes($('operation').value);$('town').disabled=all;
   $('town').setAttribute('aria-describedby','explorer-reference');
   $('reference').textContent=all?'Il confronto comprende sette osservazioni comunali, non un aggregato della Versilia. Il periodo effettivo è riportato per ogni dato.':'Riferimento predefinito della vista: il periodo effettivo compare nel risultato. Nessun anno arbitrario viene sostituito con un altro.';
   $('run').disabled=!view()?.shards[profiles[$('operation').value]];
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
   detail=null;$('view').replaceChildren();$('operation').replaceChildren();$('run').disabled=true;$('filter').value='';
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
   detail=null;$('view').replaceChildren();$('operation').replaceChildren();$('run').disabled=true;$('description').textContent='';
   status('Scegli un indicatore del tema selezionato.');
 }
 function request(){
   const operation=$('operation').value;
   return {operation,selectors:[{metric:$('metric').value,dimension:$('view').value,towns:['compare','rank'].includes(operation)?root.towns.map(t=>t.code).sort():[$('town').value]}]};
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
 function render(){
   const response=current.steps[0].response;const selector=current.plan.steps[0].request.selectors[0];const operation=current.plan.steps[0].request.operation;
   const out=$('result');out.replaceChildren();out.hidden=false;
   const heading=node('h3',root.metrics.find(m=>m.metric===selector.metric).label);heading.id='explorer-result-title';out.append(heading);
   out.append(node('p',viewLabel(selector.dimension)+' · '+(operations[operation]||operation)));
   if(response.status!=='computed')out.append(node('p','Calcolo non disponibile per questa selezione. Le eventuali osservazioni seguenti sono conservate nel rifiuto originale: non costituiscono un risultato calcolato.'));
   if(response.coverage)out.append(node('p',`Copertura: ${response.coverage.usable} osservazioni utilizzabili su ${response.coverage.requested} richieste. I dati mancanti restano distinti da zero.`));
   if(operation==='rank'&&response.status==='computed'&&Array.isArray(response.result?.ranking)){
     const ranks=node('ol');ranks.setAttribute('aria-label','Ordine numerico restituito dal motore');
     for(const row of response.result.ranking){const item=node('li',townName(row.geography)+' · '+number(row.value));item.value=row.rank;ranks.append(item);}out.append(ranks,node('p','Posizioni native, con pari merito conservati. L’ordine numerico non è una graduatoria di qualità amministrativa.'));
   }
   if(response.warnings?.length||response.reasons?.length){
     out.append(node('p','Sono presenti limiti metodologici. Prima di interpretare o citare questi dati consulta definizioni, avvertenze e motivi originali. Nessuna posizione numerica misura la qualità di un’amministrazione.'));
     const limits=node('div');for(const [key,title] of [['reasons','Motivi del rifiuto'],['warnings','Avvertenze originali']])if(response[key]?.length){limits.append(node('h4',title));const ul=node('ul');for(const item of response[key])ul.append(node('li',item));limits.append(ul);}out.append(fold('Limiti del dato · testi originali del motore',limits));
   }
   // Never turn a category code into a number or use retained refusal values as a chart.
   const observations=response.observations||[];const visible=observations.slice(pageIndex*20,(pageIndex+1)*20);
   const base=observations[0];
   const chart=response.status==='computed'&&operation!=='lookup'&&base&&observations.length>1&&observations.every(o=>typeof o.value==='number'&&Number.isFinite(o.value)&&o.value>=0&&!o.dataUnavailable&&!o.notApplicable&&o.unit!=='category_code'&&['unit','dimension','population','definition','method'].every(k=>o[k]===base[k]))&&(observations.every(o=>o.period===base.period)||observations.every(o=>o.geography===base.geography));
   if(chart){
     const graph=node('div');graph.setAttribute('role','img');graph.setAttribute('aria-label','Confronto visivo delle osservazioni riportate nella tabella. Scala da zero; valori mancanti non rappresentati.');
     const maximum=Math.max(...observations.map(o=>o.value))||1;
     graph.append(node('p',`Scala da 0 a ${number(maximum)} ${unitLabel(base)}. Nessuna interpolazione fra periodi.`));
     for(const o of visible){const row=node('div');row.className='explorer-bar-row';const track=node('span');track.className='explorer-bar-track';const bar=node('span');bar.className='explorer-bar';bar.style.display='block';bar.style.width=(o.value/maximum*100)+'%';track.append(bar);row.append(node('span',operation==='series'?String(o.period):townName(o.geography)),track,node('span',value(o)));graph.append(row);}out.append(graph);
   }
   const wrap=node('div');wrap.className='explorer-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Osservazioni originali · tabella scorribile');wrap.setAttribute('aria-describedby','explorer-table-hint');const table=node('table');table.append(node('caption','Osservazioni originali · periodo e fonte per ogni riga'));
   const head=node('thead');const hr=node('tr');for(const h of ['Territorio','Periodo','Valore','Fonte e definizione'])hr.append(node('th',h));head.append(hr);table.append(head);
   const body=node('tbody');for(const o of visible){const tr=node('tr');tr.append(node('td',townName(o.geography)+(o.localityName?' · '+o.localityName:'')),node('td',String(o.period??'Non dichiarato')));const cell=node('td',value(o));if(o.unit!=='category_code'&&o.value!==null&&o.value!==undefined&&!o.dataUnavailable&&!o.notApplicable)cell.append(node('span',' '+(unitLabel(o))));tr.append(cell);
     const source=node('td');const link=sourceURL(o.source);if(link){const a=node('a','Fonte');a.href=link;a.target='_blank';a.rel='noopener noreferrer';source.append(a);}else source.append(node('span',String(o.source||'Fonte non dichiarata')));
     const explanation=node('div');for(const [key,label] of [['definition','Definizione'],['population','Popolazione descritta'],['periodBasis','Riferimento temporale'],['method','Metodo'],['parameter','Parametro'],['referenceText','Riferimento pubblicato, senza valutazione di conformità']])if(o[key])explanation.append(node('p',label+': '+o[key]));source.append(fold('Definizione originale',explanation));tr.append(source);body.append(tr);}
   table.append(body);wrap.append(table);const hint=node('p','Scorri la tabella in orizzontale per leggere tutte le colonne.');hint.id='explorer-table-hint';hint.className='explorer-scroll-hint';out.append(hint,wrap);
   if(!observations.length)out.append(node('p','Nessuna osservazione utilizzabile restituita. Non è stato inserito alcuno zero sostitutivo.'));
   if(observations.length>20){const nav=node('nav');nav.setAttribute('aria-label','Pagine delle osservazioni');const prev=node('button','Precedenti');prev.type='button';prev.disabled=pageIndex===0;prev.onclick=()=>{pageIndex--;render();};const next=node('button','Successive');next.type='button';next.disabled=(pageIndex+1)*20>=observations.length;next.onclick=()=>{pageIndex++;render();};nav.append(prev,node('span',`Pagina ${pageIndex+1} di ${Math.ceil(observations.length/20)} `),next);out.append(nav);}
   if(response.excluded?.length)out.append(fold('Osservazioni escluse · nessuna imputazione',node('pre',JSON.stringify(response.excluded,null,2))));
   const provenance=node('pre',JSON.stringify(current,null,2));provenance.dataset.explorerEvidence='true';out.append(fold('Evidenza completa per la verifica',provenance));
 }
 $('theme').addEventListener('change',safe(themeChanged));
 $('metric').addEventListener('change',safe(async()=>{if(!$('metric').value){revoke();detail=null;$('view').replaceChildren();$('operation').replaceChildren();$('run').disabled=true;return;}await metricChanged();}));
 $('filter').addEventListener('input',()=>{if(detail)filterViews();});
 $('view').addEventListener('change',setOperation);
 $('operation').addEventListener('change',()=>{revoke();setTown();});
 $('town').addEventListener('change',revoke);
 $('form').addEventListener('submit',event=>{event.preventDefault();if(!$('run').disabled)safe(()=>execute({schemaVersion:1,steps:[{id:'selection',request:request()}]}))();});
 $('accept').addEventListener('click',()=>{if(pending){const plan=pending;safe(()=>execute(plan,true))();}});
 $('cancel').addEventListener('click',()=>{revoke();status('Consultazione annullata. Puoi cambiare selezione.');});
 async function initialize(){
   revoke();fields.disabled=true;$('retry').hidden=true;status('Verifica della versione dei dati…');
   runtime=await openRuntime();root=await runtime.discover();
   if(root.catalogSha256!==presentation.catalogSha256)throw Error('presentation_catalog_mismatch');
   $('theme').replaceChildren(option('','Scegli un tema'),...[...new Set(root.metrics.map(m=>m.theme))].map(key=>option(key,presentation.themes[key]||key)));
   $('metric').replaceChildren();$('view').replaceChildren();$('operation').replaceChildren();$('town').replaceChildren(...[...root.towns].sort((a,b)=>a.name.localeCompare(b.name,'it')).map(t=>option(t.code,t.name)));
   detail=null;$('run').disabled=true;fields.disabled=false;
   status(root.scope==='all_metrics'?'Scegli un tema per esplorare il catalogo. Le capacità consultabili dipendono dalla vista.':'Anteprima su un sottoinsieme esplicito del catalogo. Non rappresenta tutte le capacità disponibili.');
 }
 $('retry').onclick=safe(initialize);
 await safe(initialize)();
}
