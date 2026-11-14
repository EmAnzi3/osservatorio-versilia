vengono idratate dalla tassonomia ufficiale; in assenza di rete
// NON si eredita mai la descrizione della sezione, per evitare etichette false/generiche.
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
  if(!sec)return sections.map(([s])=>ensure(s,'')).filter(n=>[...nodes.values()].some(x=>x.sec===n.sec&&x.d));
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
const initialTown=root.host?.getAttribute('town')||'';const initialTownMeta=towns.find(t=>t.slug===initialTown)||null;const state={sec:'',d:'',tab:'current',metric:'active',detailTown:initialTown,visible:new Set(initialTown?[initialTown]:towns.map(t=>t.slug)),leftMode:'composition'};
const $=s=>root.querySelector(s);
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
function selectNode(sec,d='',autoAdvance=true){state.sec=sec;state.d=autoAdvance&&sec?descendSingleton(sec,d):d;state.detailTown=initialTown||'';renderAll()}
function clearAll(){state.sec='';state.d='';state.tab='current';state.metric='active';state.detailTown=initialTown||'';$('#search').value='';$('#results').hidden=true;renderAll()}
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
function escapeHtml(s){return String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;