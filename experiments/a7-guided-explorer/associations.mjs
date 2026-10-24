// Guided presentation of exact native requests, not a calculator or pair search.
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const copy=x=>JSON.parse(JSON.stringify(x));
const key=x=>JSON.stringify(x);
const number=x=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:21}).format(x);
const coefficient=x=>(Object.is(x,-0)?'-0':String(x)).replace('.',',');
const tick=x=>'≈ '+new Intl.NumberFormat('it-IT',{maximumSignificantDigits:3,notation:x!==0&&Math.abs(x)<.0001?'scientific':'compact'}).format(x);
const fold=(title,content)=>{const n=el('details');n.append(el('summary',title),content);return n;};
const option=(value,text)=>{const n=el('option',text);n.value=value;return n;};
const axes={municipalities:'Fra Comuni',periods:'Fra periodi'};
const methods={spearman:'Spearman · associazione dei ranghi',pearson:'Pearson · associazione lineare'};
const reasons={explicit_analysis_axis_required:'Manca l’asse esplicito dell’analisi: il motore non lo sceglie al posto dell’autore del piano.',explicit_correlation_method_required:'Manca il metodo esplicito: il motore non aggiunge un metodo alla richiesta.',explicit_pair_selection_purpose_required:'Manca il motivo esplicito della scelta delle due variabili.',cross_section_requires_one_period:'Il confronto fra Comuni richiede un solo periodo per ciascuna variabile.',partial_coverage_requires_opt_in:'La copertura incompleta richiede una scelta esplicita.',insufficient_observations:'Le osservazioni utilizzabili non sono sufficienti per questa analisi.',numerically_constant_variable:'Una variabile è costante nelle coppie utilizzabili.',business_cumulative_temporal_correlation_not_supported:'Le variazioni economiche hanno intervalli con una baseline condivisa: il motore non ammette una correlazione temporale per questa selezione.'};

export async function startAssociations(openRuntime,presentation){
 const previous=document.getElementById('association-explorer');if(previous)previous.remove();
 document.getElementById('association-modes')?.remove();
 const panel=el('section');panel.id='association-explorer';panel.className='association-explorer';
 panel.setAttribute('aria-labelledby','association-title');
 const heading=el('h3','Metti in relazione due variabili');heading.id='association-title';
 panel.append(heading,el('p','Anteprima su un piano esplicito: i selettori mostrano soltanto le richieste preparate in questa versione. Non rappresentano tutti gli incroci del catalogo. Nessuna coppia viene scelta in base al coefficiente.'));
 const form=el('form'),fields=el('fieldset'),grid=el('div');fields.disabled=true;grid.className='explorer-fields';
 fields.append(el('legend','La relazione che vuoi esplorare'),grid);form.append(fields);
 const controls={};
 for(const [name,label] of [['left','Prima variabile'],['right','Seconda variabile'],['axis','Asse del confronto'],['method','Metodo'],['scope','Motivo e copertura della richiesta']]){
   const wrap=el('label',label),select=el('select');select.id='association-'+name;select.required=!['axis','method'].includes(name);
   if(name==='scope')wrap.className='explorer-wide';wrap.append(select);grid.append(wrap);controls[name]=select;
 }
 const reference=el('div');reference.id='association-reference';fields.append(reference);
 const run=el('button','Mostra la relazione');run.id='association-run';run.type='submit';fields.append(run);
 const status=el('p');status.id='association-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 const retry=el('button','Riprova la stessa versione');retry.id='association-retry';retry.type='button';retry.hidden=true;
 const consent=el('section');consent.id='association-consent';consent.hidden=true;
 consent.append(el('h4','La copertura è incompleta'),el('p','Puoi consultare le osservazioni conservate insieme ai limiti originali. La conferma non completa le coppie mancanti e non trasforma un rifiuto in un risultato.'));
 const accept=el('button','Leggi con questi limiti'),cancel=el('button','Annulla');accept.id='association-accept';cancel.id='association-cancel';accept.type=cancel.type='button';consent.append(accept,cancel);
 const out=el('section');out.id='association-result';out.hidden=true;out.setAttribute('aria-label','Risultato della relazione');
 panel.append(form,status,retry,consent,out);
 const container=document.getElementById('a7-explorer');
 let measure=document.getElementById('association-measure');
 if(!measure){
   measure=el('section');measure.id='association-measure';measure.setAttribute('aria-label','Esplora una misura');
   const originalForm=document.getElementById('explorer-form');originalForm.before(measure);
   for(const id of ['form','status','retry','consent','result'])measure.append(document.getElementById('explorer-'+id));
 }
 const modes=el('div');modes.id='association-modes';modes.setAttribute('role','group');modes.setAttribute('aria-label','Tipo di esplorazione');
 const one=el('button','Una misura'),two=el('button','Due variabili');one.type=two.type='button';one.id='association-mode-measure';two.id='association-mode-pair';
 one.setAttribute('aria-controls',measure.id);two.setAttribute('aria-controls',panel.id);modes.append(one,two);measure.before(modes);container.append(panel);
 let runtime,root,steps=[],generation=0,pending=null;
 const revoke=()=>{generation++;pending=null;consent.hidden=true;out.hidden=true;out.replaceChildren();};
 const mode=pair=>{revoke();measure.hidden=pair;panel.hidden=!pair;one.setAttribute('aria-pressed',String(!pair));two.setAttribute('aria-pressed',String(pair));status.textContent='Scegli la relazione e mostra i dati per consultarla.';};
 one.onclick=()=>mode(false);two.onclick=()=>mode(true);mode(true);
 const fail=()=>{revoke();fields.disabled=true;retry.hidden=false;status.textContent='Non possiamo verificare questa selezione. Nessun risultato viene mostrato. Riprova la stessa versione.';};
 const safe=fn=>async(...args)=>{try{await fn(...args);}catch{fail();}};
 const town=code=>root.towns.find(t=>t.code===code)?.name||String(code);
 const metric=id=>root.metrics.find(m=>m.metric===id)?.label||id;
 const unit=o=>({percent:'%',currency:'€',number:'unità',years:'anni',celsius:'°C',percentage_points:'punti percentuali'})[o.unit]||
   (presentation.metrics[o.metric]?.unit===o.unit?presentation.metrics[o.metric]?.unitLabel:null)||o.unit;
 const selectorLabel=s=>metric(s.metric)+' · '+(presentation.metrics[s.metric]?.views?.[s.dimension]||({total:'Vista principale'})[s.dimension]||s.dimension||'Vista principale')+' · '+(s.periods?.length>4?String(s.periods.length)+' periodi espliciti':s.periods?.join(', ')||'riferimento nativo')+(s.towns?' · '+s.towns.map(town).join(', '):' · ambito nativo');
 function candidates(until){
   return steps.filter(s=>{
     const r=s.request;
     return (until==='left'||key(r.selectors[0])===controls.left.value)&&
       (['left','right'].includes(until)||key(r.selectors[1])===controls.right.value)&&
       (['left','right','axis'].includes(until)||String(r.axis??'')===controls.axis.value)&&
       (['left','right','axis','method'].includes(until)||String(r.method??'')===controls.method.value);
   });
 }
 function fill(name,rows,value,label){
   const unique=new Map(rows.map(s=>[value(s),label(s)]));controls[name].replaceChildren(...Array.from(unique,([v,l])=>option(v,l)));
 }
 function selected(){return steps.find(s=>s.id===controls.scope.value);}
 function update(from){
   revoke();const order=['left','right','axis','method','scope'];
   for(const name of order.slice(order.indexOf(from)+1)){
     const rows=candidates(name);
     if(name==='right')fill(name,rows,s=>key(s.request.selectors[1]),s=>selectorLabel(s.request.selectors[1]));
     if(name==='axis')fill(name,rows,s=>String(s.request.axis??''),s=>axes[s.request.axis]||(s.request.axis?'Asse non riconosciuto':'Asse non dichiarato'));
     if(name==='method')fill(name,rows,s=>String(s.request.method??''),s=>methods[s.request.method]||(s.request.method?'Metodo non riconosciuto':'Metodo non dichiarato'));
     if(name==='scope')fill(name,rows,s=>s.id,s=>(s.request.purpose?.slice(0,100)||'Motivo non dichiarato')+(s.request.allowPartial===true?' · copertura incompleta richiesta esplicitamente':' · nessun consenso implicito'));
   }
   const step=selected();run.disabled=!step;reference.replaceChildren();
   if(step){
     for(const [i,label] of [[0,'Prima variabile'],[1,'Seconda variabile']])reference.append(el('p',label+': '+selectorLabel(step.request.selectors[i])));
     for(const [i,label] of [[0,'Periodi della prima variabile'],[1,'Periodi della seconda variabile']])if(step.request.selectors[i].periods?.length>4)reference.append(fold(label,el('p',step.request.selectors[i].periods.join(', '))));
     reference.append(fold('Motivo dichiarato della selezione',el('p',step.request.purpose||'Non dichiarato: nessun motivo viene aggiunto al posto dell’autore del piano.')));
   }
   status.textContent='Scegli la relazione e il metodo, poi mostra i dati. Le dichiarazioni del catalogo non autorizzano ogni coppia.';
 }
 function sources(observation,cell){
   const url=observation.source;let safeURL=null;try{const u=new URL(url);if(['http:','https:'].includes(u.protocol))safeURL=u.href;}catch{}
   if(safeURL){const a=el('a','Fonte');a.href=safeURL;a.target='_blank';a.rel='noopener noreferrer';cell.append(a);}else cell.append(el('span',url||'Fonte non dichiarata'));
   const detail=el('div');for(const [name,label] of [['definition','Definizione'],['population','Popolazione descritta'],['periodBasis','Riferimento temporale'],['method','Metodo']])if(observation[name])detail.append(el('p',label+': '+observation[name]));cell.append(fold('Definizione originale',detail));
 }
 function graph(result){
   const pairs=result.pairs;
   if(!pairs.length||result.n!==pairs.length||pairs.some(p=>![p.x.value,p.y.value].every(Number.isFinite)))throw Error('incompatible_native_pairs');
   // Coordinate projection only. Coefficient, pairs, n and exclusions come from A6.
   const xs=pairs.map(p=>p.x.value),ys=pairs.map(p=>p.y.value),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
   if(xmin===xmax||ymin===ymax)throw Error('constant_native_chart');
   const width=Math.max(300,Math.min(640,panel.clientWidth));
   const figure=el('figure'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',`0 0 ${width} 360`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Coppie originali A6: prima variabile sull’asse orizzontale, seconda sull’asse verticale. Tutti i valori e le fonti sono nella tabella.');
   const shape=(name,attrs)=>{const n=document.createElementNS(svg.namespaceURI,name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));svg.append(n);return n;};
   const bounds={left:110,right:width-45,top:45,bottom:290};
   shape('path',{d:`M${bounds.left} ${bounds.top} V${bounds.bottom} H${bounds.right}`,fill:'none',stroke:'#617b8b'});
   for(const [endpoint,x,y,text] of [['x-min',bounds.left,330,tick(xmin)],['x-max',bounds.right,330,tick(xmax)],['y-min',bounds.left-10,bounds.bottom,tick(ymin)],['y-max',bounds.left-10,bounds.top,tick(ymax)]]){
     const n=shape('text',{x,y,'data-axis-endpoint':endpoint,'text-anchor':endpoint==='x-min'?'start':'end','font-size':13});n.textContent=text;
   }
   pairs.forEach((p,i)=>{
     const x=bounds.left+(p.x.value-xmin)/(xmax-xmin)*(bounds.right-bounds.left),y=bounds.bottom-(p.y.value-ymin)/(ymax-ymin)*(bounds.bottom-bounds.top);
     const c=shape('circle',{cx:x,cy:y,r:8,fill:'#216b91','data-pair-key':p.key});
     const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=(result.axis==='municipalities'?town(p.key):p.key)+': '+number(p.x.value)+' / '+number(p.y.value);c.append(title);
     if(pairs.length<=20){const t=shape('text',{x:x+11,y:y-10,'font-size':14});t.textContent=String(i+1);}
   });
   const plot=el('div');plot.className='association-plot';plot.tabIndex=0;plot.setAttribute('role','region');plot.setAttribute('aria-label','Grafico delle coppie originali, scorribile in orizzontale sugli schermi stretti');plot.append(svg);
   figure.append(plot,el('figcaption','Su schermi stretti puoi scorrere il grafico in orizzontale. Asse orizzontale: '+metric(pairs[0].x.metric)+' ('+unit(pairs[0].x)+'), da '+number(xmin)+' a '+number(xmax)+'. Asse verticale: '+metric(pairs[0].y.metric)+' ('+unit(pairs[0].y)+'), da '+number(ymin)+' a '+number(ymax)+'. Le etichette della scala sono arrotondate; gli estremi qui riportati e le coppie nella tabella conservano i valori originali. Le scale non partono necessariamente da zero. Gli eventuali numeri identificano i punti, non posizioni in classifica. I punti sovrapposti restano distinti nella tabella.'));return figure;
 }
 function show(answer){
   const response=answer.steps[0].response;out.hidden=false;out.append(el('h4',response.status==='computed'?'La relazione osservata':'Il motore non ammette questo calcolo'));
   out.append(el('p','Associazione diversa da causalità: nessuna valutazione di efficacia amministrativa o raccomandazione automatica.'));
   if(response.warnings?.includes('stock_and_flow_reference_periods_differ'))out.append(el('p','Le variabili hanno riferimenti temporali diversi: una misura uno stock, l’altra un flusso. Leggi periodi e definizioni prima di interpretare la relazione.'));
   if(response.status==='computed'){
     const r=response.result;if(!r||!Number.isFinite(r.coefficient)||!['pearson','spearman'].includes(r.method)||!axes[r.axis])throw Error('incompatible_native_association');
     const cards=el('dl');cards.className='explorer-benchmark-values';
     for(const [label,value,name] of [['Coefficiente originale',coefficient(r.coefficient),'coefficient'],['Coppie utilizzate',String(r.n),'n'],['Metodo',methods[r.method],'method']]){
       const card=el('div'),valueNode=el('dd',value);valueNode.dataset.associationValue=name;card.append(el('dt',label),valueNode);cards.append(card);
     }
     out.append(cards,el('p','Nessun test di significatività o intervallo di confidenza fornito dal motore. '+(r.axis==='municipalities'?'I sette Comuni non sono automaticamente un campione indipendente.':'')),graph(r));
     const table=el('table');table.append(el('caption','Coppie originali · periodi, unità e fonti distinti per variabile'));
     const head=el('thead'),tr=el('tr');for(const label of ['Punto','Territorio o periodo','Prima variabile','Seconda variabile']){const th=el('th',label);th.scope='col';tr.append(th);}head.append(tr);table.append(head);
     const body=el('tbody');let pageIndex=0;
     const rows=()=>{body.replaceChildren();r.pairs.slice(pageIndex*20,(pageIndex+1)*20).forEach((p,i)=>{const row=el('tr');row.dataset.pairKey=p.key;row.append(el('td',String(pageIndex*20+i+1)),el('td',r.axis==='municipalities'?town(p.key):p.key));for(const o of [p.x,p.y]){const cell=el('td');cell.append(el('p',number(o.value)+' '+unit(o)),el('p','Periodo: '+String(o.period)));sources(o,cell);row.append(cell);}body.append(row);});};rows();table.append(body);
     const wrap=el('div');wrap.className='explorer-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Coppie originali, tabella scorribile');wrap.append(table);out.append(el('p','Puoi scorrere la tabella in orizzontale per leggere periodi e fonti.'),wrap);
     if(r.pairs.length>20){const nav=el('nav');nav.setAttribute('aria-label','Pagine delle coppie originali');const previous=el('button','Precedenti'),next=el('button','Successive'),label=el('span');previous.type=next.type='button';previous.id='association-previous';next.id='association-next';const update=()=>{previous.disabled=pageIndex===0;next.disabled=(pageIndex+1)*20>=r.pairs.length;label.textContent=`Pagina ${pageIndex+1} di ${Math.ceil(r.pairs.length/20)} `;};previous.onclick=()=>{pageIndex--;rows();update();};next.onclick=()=>{pageIndex++;rows();update();};update();nav.append(previous,label,next);out.append(nav);}
   }else{
     out.append(el('p','Le eventuali osservazioni conservate nel rifiuto non costituiscono un coefficiente valido. Nessun grafico o numero sostitutivo viene calcolato.'));
     for(const reason of response.reasons||[])if(reasons[reason])out.append(el('p',reasons[reason]));
   }
   if(response.pairCoverage)out.append(el('p','Copertura delle coppie: '+response.pairCoverage.paired+' su '+response.pairCoverage.requested+'. Le coppie mancanti non diventano zero.'));
   const details=el('div');for(const field of ['warnings','reasons'])if(response[field]?.length)details.append(el('pre',JSON.stringify(response[field],null,2)));
   if(response.result?.leaveOneOut)details.append(el('p','Sensibilità all’esclusione di una coppia alla volta · risultati originali, senza nuovi calcoli'),el('pre',JSON.stringify(response.result.leaveOneOut,null,2)));
   if(response.excluded?.length)details.append(el('p','Esclusioni originali'),el('pre',JSON.stringify(response.excluded,null,2)));
   out.append(fold('Metodo, sensibilità e limiti originali',details));const evidence=el('pre',JSON.stringify(answer,null,2));evidence.dataset.associationEvidence='true';out.append(fold('Evidenza completa per la verifica',evidence));
   status.textContent=response.status==='computed'?'Relazione caricata dal motore A6 nella versione verificata.':'Rifiuto originale del motore: questa selezione non produce un risultato calcolato.';
 }
 async function execute(plan,approvedPartial=false){
   revoke();const ticket=generation;status.textContent='Verifica e caricamento della relazione selezionata…';
   let answer;try{answer=await runtime.run(copy(plan),{approvedPartial});}catch(error){if(ticket===generation)throw error;return;}
   if(ticket!==generation)return;
   if(answer.resolution==='needs_confirmation'){pending=copy(plan);consent.hidden=false;status.textContent='Serve una conferma sulla copertura incompleta. Nessun valore è ancora mostrato.';return;}
   if(answer.resolution!=='resolved'){status.textContent='Questa richiesta non è preparata nel trasporto corrente. Non significa dato assente o divieto metodologico.';return;}
   show(answer);
 }
 for(const name of ['left','right','axis','method','scope'])controls[name].onchange=()=>update(name);
 form.onsubmit=event=>{event.preventDefault();const step=selected();if(step)safe(()=>execute({schemaVersion:1,steps:[copy(step)]}))();};
 accept.onclick=()=>{if(pending){const plan=pending;safe(()=>execute(plan,true))();}};
 cancel.onclick=()=>{revoke();status.textContent='Consultazione annullata. Puoi cambiare selezione.';};
 async function initialize(){
   revoke();fields.disabled=true;retry.hidden=true;status.textContent='Verifica del perimetro delle relazioni…';runtime=await openRuntime();root=await runtime.discover();
   if(root.catalogSha256!==presentation.catalogSha256)throw Error('presentation_catalog_mismatch');
   if(!root.associationPlan){mode(false);panel.remove();modes.remove();return;}
   steps=root.associationPlan.plan.steps;
   if(steps.some(s=>!Array.isArray(s.request.selectors)||s.request.selectors.length!==2))throw Error('association_controls_require_two_selectors');
   fill('left',steps,s=>key(s.request.selectors[0]),s=>selectorLabel(s.request.selectors[0]));update('left');fields.disabled=false;
 }
 retry.onclick=safe(initialize);await safe(initialize)();
}
