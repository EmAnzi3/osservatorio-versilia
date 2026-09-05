const DATA=window.__ATECO_PAYLOAD.DATA;
const LABELS=window.__ATECO_PAYLOAD.LABELS||{};
const EMBEDDED_ATECO=window.__ATECO_PAYLOAD.ATECO||{};
Object.assign(LABELS,{
  'L 68':'Attività immobiliari',
  'L 681':'Compravendita di beni immobili effettuata su beni propri',
  'L 6810':'Compravendita di beni immobili effettuata su beni propri',
  'L 68100':'Compravendita di beni immobili effettuata su beni propri',
  'L 682':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 6820':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 68200':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 682001':'Locazione immobiliare di beni propri o in leasing (affitto)',
  'L 682002':'Affitto di aziende',
  'L 683':'Attività immobiliari per conto terzi',
  'L 6831':'Attività di mediazione immobiliare',
  'L 68310':'Attività di mediazione immobiliare',
  'L 683100':'Attività di mediazione immobiliare',
  'L 6832':'Gestione di immobili per conto terzi',
  'L 68320':'Amministrazione di condomini e gestione di beni immobili per conto terzi',
  'L 683200':'Amministrazione di condomini e gestione di beni immobili per conto terzi'
});
const LEVELS={0:'Sezione',2:'Divisione',3:'Gruppo',4:'Classe',5:'Categoria',6:'Sottocategoria'};
const PALETTE=['#ad6247','#145b78','#5f8b78','#c89b3c','#6f6690','#3e7180','#b65358','#6b7b4d','#9a6b18','#587489','#8c5e76','#477b69'];
const towns=DATA.t.map((x,i)=>({slug:x[0],name:x[1],i}));
const years=DATA.y; const latest=years.length-1;
const exact=new Map();
DATA.c.forEach(r=>exact.set(r[0],r));
const sections=Object.entries(DATA.s);
const nodes=new Map();
function displayCode(d){if(!d)return'';if(d.length===2)return d;if(d.length===3)return d.slice(0,2)+'.'+d.slice(2);if(d.length===4)return d.slice(0,2)+'.'+d.slice(2);if(d.length===5)return d.slice(0,2)+'.'+d.slice(2,4)+'.'+d.slice(4);return d.slice(0,2)+'.'+d.slice(2,4)+'.'+d.slice(4)}
function key(sec,d=''){return d?sec+' '+d:sec}
function nodeLabel(sec,d=''){return LABELS[key(sec,d)]||(d?'':(LABELS[sec]||''))}
function ensure(sec,d=''){let k=key(sec,d);if(!nodes.has(k))nodes.set(k,{key:k,sec,d,label:nodeLabel(sec,d),hasData:d?exact.has(k):false});return nodes.get(k)}
sections.forEach(([s])=>ensure(s,''));
DATA.c.forEach(r=>{let m=r[0].match(/^([A-Z])\s+(\d+)$/);if(!m)return;let [_,s,d]=m;ensure(s,'');for(let L of [2,3,4,5,6])if(d.length>=L)ensure(s,d.slice(0,L));});
function childNodes(sec,d=''){
  if(!sec)return sections.map(([s])=>ensure(s,'')).filter(n=>[...nodes.values()].some(x=>x.sec===s&&x.d));
  const next={0:2,2:3,3:4,4:5,5:6}[d.length]; if(!next)return[];
  const seen=new Map(); for(const n of nodes.values()){if(n.sec!==sec||n.d.length!==next)continue;if(d&& !n.d.startsWith(d))continue;seen.set(n.d,n)}
  return [...seen.values()].sort((a,b)=>a.d.localeCompare(b.d,'it',{numeric:true}));
}
function ancestors(sec,d){let arr=[];if(!sec)return arr;arr.push(ensure(sec,''));for(let L of [2,3,4,5,6])if(d.length>=L)arr.push(ensure(sec,d.slice(0,L)));return arr}
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[’']/g,' ').replace(/\s+/g,' ').trim()}
const aliases={nautica:['C 3012','C 3315'],marmo:['B 0811','C 23701','C 23702'],balneari:['R 93292'],'stabilimenti balneari':['R 93292'],'gallerie d arte':['G 477831'],'galleria d arte':['G 477831']};
const taxonomyState={status:'loaded',source:'ISTAT ATECO 2007–2022',missing:[],resolved:0,total:0,error:''};
function applyEmbeddedTaxonomy(){
  let resolved=0;
  for(const n of nodes.values()){
    const code=n.d?displayCode(n.d):n.sec;
    const label=EMBEDDED_ATECO[code]||'';
    if(label){n.label=label;LABELS[n.key]=label;resolved++;}
  }
  taxonomyState.total=nodes.size;taxonomyState.resolved=resolved;
  taxonomyState.missing=[...nodes.values()].filter(n=>!String(n.label||'').trim());
  taxonomyState.status=taxonomyState.missing.length?'incomplete':'loaded';
}
function setTaxonomyAudit(){return;}

function taxonomyReady(){return taxonomyState.status==='loaded'&&!taxonomyState.missing.length}
function rawToPretty(raw){let m=raw.match(/^([A-Z])\s+(\d+)$/);return m?m[1]+' · '+displayCode(m[2]):raw}
function fmt(v,d=0){if(v===null||v===undefined||Number.isNaN(v))return'n.d.';return new Intl.NumberFormat('it-IT',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v)}
const state={sec:'',d:'',tab:'current',metric:'active',detailTown:'',visible:new Set(towns.map(t=>t.slug)),leftMode:'composition'};
const $=s=>document.querySelector(s);
function currentNode(){if(!state.sec)return null;return ensure(state.sec,state.d)}
function descendSingleton(sec,d=''){
  let cur=d,guard=0;
  while(sec&&guard++<8){
    const kids=childNodes(sec,cur);
    if(kids.length!==1)break;
    cur=kids[0].d;
  }
  return cur;
}
function taxonomyReady(){return taxonomyState.status==='loaded'&&!taxonomyState.missing.length}
function selectNode(sec,d='',autoAdvance=true){state.sec=sec;state.d=autoAdvance&&sec?descendSingleton(sec,d):d;state.detailTown='';renderAll()}
function clearAll(){state.sec='';state.d='';state.tab='current';state.metric='active';state.detailTown='';$('#search').value='';$('#results').hidden=true;renderAll()}
function renderSelectors(){
  const taxonomyLocked=false;
  const defs=[['Sezione',0],['Divisione',2],['Gruppo',3],['Classe',4],['Categoria',5],['Sottocategoria',6]];let out='';
  defs.forEach(([name,L],idx)=>{
    let opts=[],disabled=false,selected='';
    if(L===0){opts=sections.map(([s])=>ensure(s,''));selected=state.sec}
    else{
      let parentLen={2:0,3:2,4:3,5:4,6:5}[L];let parentD=parentLen?state.d.slice(0,parentLen):'';
      if(!state.sec || (parentLen&&state.d.length<parentLen)){disabled=true}else opts=childNodes(state.sec,parentD);
      if(state.d.length>=L)selected=state.d.slice(0,L);
    }
    disabled=disabled||taxonomyLocked;
    let ph=`${name}`;out+=`<div class="selector"><label>${name}</label><select data-level="${L}" ${disabled?'disabled':''}><option value="">${L===0?'Tutte le sezioni':'—'}</option>${opts.map(n=>`<option value="${L===0?n.sec:n.d}" ${selected===(L===0?n.sec:n.d)?'selected':''} ${L===0&&!childNodes(n.sec,'').length?'disabled':''}>${L===0?n.sec:displayCode(n.d)}${n.label?' · '+escapeHtml(n.label):''}</option>`).join('')}</select></div>`;
  });
  $('#selectors').innerHTML=out;
  $('#selectors').querySelectorAll('select').forEach(sel=>sel.onchange=()=>{
    const L=+sel.dataset.level,v=sel.value;
    if(L===0){state.sec=v;state.d=v?descendSingleton(v,''):''}
    else if(v){state.d=descendSingleton(state.sec,v)}
    else{const parentLen={2:0,3:2,4:3,5:4,6:5}[L];state.d=parentLen?state.d.slice(0,parentLen):''}
    state.detailTown='';renderAll();
  });
}
function escapeHtml(s){return String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}
function renderCrumbs(){
  let parts=[`<button class="crumb ${!state.sec?'current':''}" data-root="1">Tutte le attività</button>`];
  if(state.sec){for(const n of ancestors(state.sec,state.d)){parts.push('<span class="sep">›</span>');parts.push(`<button class="crumb ${n.d===state.d?'current':''}" data-sec="${n.sec}" data-d="${n.d}" title="${escapeHtml(n.label)}">${n.d?displayCode(n.d):n.sec}</button>`);}}
  $('#crumbs').innerHTML=parts.join('');$('#crumbs').querySelectorAll('button').forEach(b=>b.onclick=()=>b.dataset.root?clearAll():selectNode(b.dataset.sec,b.dataset.d,false));
  let n=currentNode(),st=$('#status');if(n&&n.hasData){st.className='node-status direct';st.textContent='Valore disponibile'}else{st.className='node-status nav';st.textContent=state.sec?'Continua a esplorare':'Navigazione ATECO'}
}
function arcPath(cx,cy,r,a0,a1){let x0=cx+r*Math.cos(a0),y0=cy+r*Math.sin(a0),x1=cx+r*Math.cos(a1),y1=cy+r*Math.sin(a1),large=(a1-a0)>Math.PI?1:0;return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`}
function renderDonut(){
  const mode=state.leftMode||'composition';
  document.querySelector('#modeComposition')?.classList.toggle('active',mode==='composition');
  document.querySelector('#modeNavigation')?.classList.toggle('active',mode==='navigation');
  let kids=childNodes(state.sec,state.d),svg=$('#donut'),center=$('#donutCenter');svg.innerHTML='';
  if(mode==='navigation'){
    if(!kids.length){svg.innerHTML='<circle cx="160" cy="160" r="118" fill="none" stroke="#e4e9e7" stroke-width="36"/><circle cx="160" cy="160" r="112" fill="none" stroke="#ad6247" stroke-width="2" stroke-dasharray="3 6"/>';center.innerHTML=`<strong>${state.d?displayCode(state.d):state.sec||'—'}</strong><span>massima granularità<br>disponibile</span>`;$('#children').innerHTML='<div class="empty">Non ci sono livelli successivi nel set di codici disponibile.</div>';return;}
    const gap=Math.min(.025,0.42/kids.length),step=Math.PI*2/kids.length,r=116;
    kids.forEach((n,i)=>{let a0=-Math.PI/2+i*step+gap,a1=-Math.PI/2+(i+1)*step-gap;let p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',arcPath(160,160,r,a0,a1));p.setAttribute('fill','none');p.setAttribute('stroke',PALETTE[i%PALETTE.length]);p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.innerHTML=`<title>${n.d?displayCode(n.d):n.sec} · ${n.label||''}</title>`;p.onclick=()=>selectNode(n.sec,n.d);p.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectNode(n.sec,n.d)}};svg.appendChild(p)});
    let here=currentNode();center.innerHTML=state.sec?`<strong>${state.d?displayCode(state.d):state.sec}</strong><span>${escapeHtml(here?.label||'')}<br><b>${kids.length}</b> voci successive</span>`:`<strong>${kids.length}</strong><span>sezioni navigabili<br>su ${DATA.c.length.toLocaleString('it-IT')} codici</span>`;
    $('#children').innerHTML=kids.map(n=>`<button class="child" data-sec="${n.sec}" data-d="${n.d}"><code>${n.d?displayCode(n.d):n.sec}</code><span>${escapeHtml(n.label||'')}</span></button>`).join('');
    $('#children').querySelectorAll('.child').forEach(b=>b.onclick=()=>selectNode(b.dataset.sec,b.dataset.d));
    return;
  }
  const items=compositionChildren();
  const usable=items.filter(x=>x.value!==null);
  const total=sumNullable(usable.map(x=>x.value));
  if(!usable.length || total===null || total<=0){
    svg.innerHTML='<circle cx="160" cy="160" r="118" fill="none" stroke="#e4e9e7" stroke-width="36"/><circle cx="160" cy="160" r="112" fill="none" stroke="#ad6247" stroke-width="2" stroke-dasharray="3 6"/>';
    center.innerHTML=`<strong>${state.d?displayCode(state.d):state.sec||'Versilia'}</strong><span>nessuna UL attiva<br>aggregabile</span>`;
    $('#children').innerHTML='<div class="empty">Non ci sono valori aggregabili per la composizione percentuale a questo livello.</div>';
    return;
  }
  let cursor=-Math.PI/2;
  usable.forEach((item,i)=>{
    const pct=item.value/total,span=pct*Math.PI*2,gap=Math.min(.02,0.35/usable.length),a0=cursor+gap,a1=cursor+span-gap;cursor+=span;
    if(a1<=a0)return;
    let p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',arcPath(160,160,116,a0,a1));p.setAttribute('fill','none');p.setAttribute('stroke',PALETTE[i%PALETTE.length]);p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');
    p.innerHTML=`<title>${item.node.d?displayCode(item.node.d):item.node.sec} · ${item.node.label||''} — ${fmt(item.value)} UL · ${fmt(pct*100,1)}%</title>`;
    p.onclick=()=>selectNode(item.node.sec,item.node.d);p.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectNode(item.node.sec,item.node.d)}};svg.appendChild(p);
  });
  const totalCurrent=compositionTotalForCurrent();
  const here=currentNode();
  center.innerHTML=state.sec
    ?`<strong>${displayCode(state.d)}</strong><span>${escapeHtml(here?.label||'')}<br><b>${fmt(totalCurrent)}</b> UL attive</span>`
    :`<strong>Versilia</strong><span>composizione per sezione<br><b>${fmt(total)}</b> UL attive</span>`;
  $('#children').innerHTML=items.map((item,idx)=>{
    const v=item.value,p=v===null||total===null||total===0?null:(v/total*100); const stateClass=v===null?'nd':v===0?'zero':'';
    return `<button class="child ${stateClass}" data-sec="${item.node.sec}" data-d="${item.node.d}"><code>${item.node.d?displayCode(item.node.d):item.node.sec}</code><span>${escapeHtml(item.node.label||'')}</span><small>${v===null?'n.d.':fmt(v)+' UL · '+fmt(p,1)+'%'}</small></button>`;
  }).join('');
  $('#children').querySelectorAll('.child').forEach(b=>b.onclick=()=>selectNode(b.dataset.sec,b.dataset.d));
}
