','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}
function renderCrumbs(){
  let parts=[`<button class="crumb ${!state.sec?'current':''}" data-root="1">Tutte le attività</button>`];
  if(state.sec){for(const n of ancestors(state.sec,state.d)){parts.push('<span class="sep">›</span>');parts.push(`<button class="crumb ${n.d===state.d?'current':''}" data-sec="${n.sec}" data-d="${n.d}" title="${escapeHtml(n.label)}">${n.d?displayCode(n.d):n.sec}</button>`);}}
  $('#crumbs').innerHTML=parts.join('');$('#crumbs').querySelectorAll('button').forEach(b=>b.onclick=()=>b.dataset.root?clearAll():selectNode(b.dataset.sec,b.dataset.d,false));
  let n=currentNode(),st=$('#status');if(n&&n.hasData){st.className='node-status direct';st.textContent='Valore disponibile'}else{st.className='node-status nav';st.textContent=state.sec?'Continua a esplorare':'Navigazione ATECO'}
}
function arcPath(cx,cy,r,a0,a1){let x0=cx+r*Math.cos(a0),y0=cy+r*Math.sin(a0),x1=cx+r*Math.cos(a1),y1=cy+r*Math.sin(a1),large=(a1-a0)>Math.PI?1:0;return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`}
function renderDonut(){
  const mode=state.leftMode||'composition';
  root.querySelector('#modeComposition')?.classList.toggle('active',mode==='composition');
  root.querySelector('#modeNavigation')?.classList.toggle('active',mode==='navigation');
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
function getRow(){let n=currentNode();return n&&n.hasData?exact.get(n.key):null}
function met(row,townIdx,yi=latest){let a=row[3+townIdx][0][yi],art=yi===latest?row[3+townIdx][1]:null,ra=row[1][yi],tt=DATA.tt[townIdx][yi],rt=DATA.rt[yi];let lq=(a===null||ra===null||!ra||!tt||!rt)?null:(a/tt)/(ra/rt);let weight=(a===null||ra===null||!ra)?null:a/ra*100;let share=(a===null||art===null)?null:(a===0?(art===0?0:null):art/a*100);return{a,art,ra,lq,weight,share}}
function metricValue(m){return state.metric==='active'?m.a:state.metric==='lq'?m.lq:m.weight}
function metricFmt(v){if(v===null)return'n.d.';if(state.metric==='active')return fmt(v,0);if(state.metric==='lq')return fmt(v,2)+'×';return fmt(v,2)+'%'}
function metricUnit(){return state.metric==='active'?'UL':state.metric==='lq'?'LQ':'peso Toscana'}

const aggregateCache=new Map();
function sumNullable(values){
  let sum=0,has=false;
  values.forEach(v=>{if(v!==null&&v!==undefined){sum+=v;has=true;}});
  return has?sum:null;
}
function emptyAggregate(){return{vers:years.map(()=>null),region:years.map(()=>null),towns:towns.map(()=>years.map(()=>null)),art:towns.map(()=>null)};}
function aggregateNode(sec,d=''){
  const k=key(sec,d); if(aggregateCache.has(k)) return aggregateCache.get(k);
  cons