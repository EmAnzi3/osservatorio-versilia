t kids=childNodes(sec,d);
  let result;
  if(kids.length){
    const childAggs=kids.map(ch=>aggregateNode(ch.sec,ch.d));
    result={
      vers: years.map((_,yi)=>sumNullable(childAggs.map(a=>a.vers[yi]))),
      region: years.map((_,yi)=>sumNullable(childAggs.map(a=>a.region[yi]))),
      towns: towns.map((t,ti)=>years.map((_,yi)=>sumNullable(childAggs.map(a=>a.towns[ti][yi])))),
      art: towns.map((t,ti)=>sumNullable(childAggs.map(a=>a.art[ti])))
    };
  } else {
    const row=exact.get(k);
    if(!row){result=emptyAggregate();}
    else {
      const townsSeries=towns.map(t=>row[3+t.i][0].slice());
      result={
        vers: years.map((_,yi)=>sumNullable(townsSeries.map(series=>series[yi]))),
        region: row[1].slice(),
        towns: townsSeries,
        art: towns.map(t=>row[3+t.i][1])
      };
    }
  }
  aggregateCache.set(k,result);
  return result;
}
function compositionChildren(){
  const kids=state.sec?childNodes(state.sec,state.d):sections.map(([s])=>ensure(s,''));
  return kids.map(n=>{const agg=aggregateNode(n.sec,n.d);return {node:n,value:agg.vers[latest]};});
}
function compositionTotalForCurrent(){
  if(!state.sec){const items=compositionChildren();return sumNullable(items.map(x=>x.value));}
  return aggregateNode(state.sec,state.d).vers[latest];
}
function derivedMet(n,townIdx,yi=latest){
  const agg=aggregateNode(n.sec,n.d),a=agg.towns[townIdx][yi],art=yi===latest?agg.art[townIdx]:null,ra=agg.region[yi],tt=DATA.tt[townIdx][yi],rt=DATA.rt[yi];
  const lq=(a===null||ra===null||!ra||!tt||!rt)?null:(a/tt)/(ra/rt);
  const weight=(a===null||ra===null||!ra)?null:a/ra*100;
  const share=(a===null||art===null)?null:(a===0?(art===0?0:null):art/a*100);
  return{a,art,ra,lq,weight,share};
}

function renderCurrentDerived(n){
  let ms=towns.map(t=>({t,m:derivedMet(n,t.i)})),vals=ms.map(x=>metricValue(x.m)).filter(v=>v!==null),max=Math.max(1,...vals),auto=ms.filter(x=>x.m.a!==null).sort((a,b)=>(b.m.a??-1)-(a.m.a??-1))[0]?.t.slug||towns[0].slug;
  if(!state.detailTown||!towns.some(t=>t.slug===state.detailTown))state.detailTown=auto;
  let detail=ms.find(x=>x.t.slug===state.detailTown)||ms[0],dm=detail.m,total=compositionTotalForCurrent();
  return `<div class="selected-title"><code>${n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>${fmt(total)} UL attive in Versilia · anno 2025</p>${hierarchyContext(n)}</div>
  <div class="metric-row"><span>Metrica del confronto</span><div class="mini-switch"><button data-metric="active" class="${state.metric==='active'?'active':''}">UL attive</button><button data-metric="lq" class="${state.metric==='lq'?'active':''}">Specializzazione</button><button data-metric="weight" class="${state.metric==='weight'?'active':''}">Peso Toscana</button></div></div>
  <div class="lollipops">${ms.map(x=>{let v=metricValue(x.m),cl=v===null?'nd':v===0?'zero':'',pct=v===null||v===0?0:(v/max*100);return `<div class="lrow clickable ${cl} ${x.t.slug===state.detailTown?'selected':''}" data-town="${x.t.slug}" title="${escapeHtml(x.t.name)} · ${metricUnit()}: ${metricFmt(v)}"><div class="lname">${escapeHtml(x.t.name)}</div><div class="track"><span class="stem" style="--pct:${pct}%"></span><span class="dot" style="--pct:${pct}%"></span></div><div class="lvalue">${metricFmt(v)}<small>${metricUnit()}</small></div></div>`}).join('')}</div>
  <div class="legend-note"><span><i class="legend-dot"></i> valore positivo</span><span><i class="legend-zero"></i> zero osservato</span><span><i class="legend-nd"></i> n.d.</span></div>
  <div class="detail-heading"><h4>Dettaglio analitico</h4><select id="detailTown" class="town-select">${towns.map(t=>`<option value="${t.slug}" ${t.slug===state.detailTown?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select></div>
  <div class="kpis"><div class="kpi"><span>UL attive</span><strong>${fmt(dm.a)}</strong><small>2025</small></div><div class="kpi"><span>UL artigiane</span><strong>${fmt(dm.art)}</strong><small>${dm.share===null?'quota n.d.':fmt(dm.share,1)+'% del nodo'}</small></div><div class="kpi"><span>Specializzazione</span><strong>${dm.lq===null?'n.d.':fmt(dm.lq,2)+'×'}</strong><small>1× = Toscana</small></div><div class="kpi"><span>Peso regionale</span><strong>${dm.weight===null?'n.d.':fmt(dm.weight,2)+'%'}</strong><small>delle UL toscane</small></div><div class="kpi"><span>Riferimento Toscana</span><strong>${fmt(dm.ra)}</strong><small>UL attive · 2025</small></div><div class="kpi"><span>Quota artigiana</span><strong>${dm.share===null?'n.d.':fmt(dm.share,1)+'%'}</strong><small>nel Comune</small></div></div>`;
}
function renderHistoryDerived(n){
  const agg=aggregateNode(n.sec,n.d),W=760,H=350,L=48,R=20,T=26,B=44;let visible=towns.filter(t=>state.visible.has(t.slug));if(!visible.length){state.visible.add(towns[0].slug);visible=[towns[0]]}
  let all=[];visible.forEach(t=>years.forEach((yr,yi)=>{let v=agg.towns[t.i][yi];if(v!==null)all.push(v)}));let ymax=Math.max(1,...all);ymax=Math.ceil(ymax/10)*10;let x=i=>L+i/(years.length-1)*(W-L-R),y=v=>T+(1-v/ymax)*(H-T-B);
  let svg='';for(let j=0;j<=4;j++){let vv=ymax*(4-j)/4,yy=T+j*(H-T-B)/4;svg+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text class="axistext" x="${L-8}" y="${yy+3}" text-anchor="end">${fmt(vv,0)}</text>`}
  years.forEach((yr,i)=>{svg+=`<text class="axistext" x="${x(i)}" y="${H-14}" text-anchor="middle">${String(yr).slice(2)}</text>`});let bi=years.indexOf(2022);if(bi>=0){let bx=x(bi);svg+=`<rect x="${bx-6}" y="${T}" width="12" height="${H-T-B}" fill="#f3e3da" opacity=".55"/><line class="breakline" x1="${bx}" x2="${bx}" y1="${T}" y2="${H-B}"/><text class="breaktext" x="${bx+5}" y="${T+10}">ATECO 2022</text>`}
  visible.forEach(t=>{let pts=years.map((yr,yi)=>{let v=agg.towns[t.i][yi];return v===null?null:{x:x(yi),y:y(v),v,yr}}),color=PALETTE[t.i%PALETTE.length];for(const d of pathFromPoints(pts))svg+=`<path class="trendline" d="${d}" stroke="${color}"/>`;pts.filter(Boolean).forEach(p=>svg+=`<circle class="trenddot" cx="${p.x}" cy="${p.y}" r="3.2" stroke="${color}"><title>${escapeHtml(t.name)} · ${p.yr}: ${fmt(p.v)} UL</title></circle>`) });
  return `<div class="selected-title"><code>${n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>Serie annuale delle UL attive · 2014–2025</p>${hierarchyContext(n)}</div><div class="history-controls"><div class="town-chips">${towns.map(t=>`<button class="town-chip ${state.visible.has(t.slug)?'':'off'}" data-vtown="${t.slug}" style="border-color:${PALETTE[t.i%PALETTE.length]}">${escapeHtml(t.name)}</button>`).join('')}</div><div class="history-tools"><button id="allTowns">Tutti</button><button id="oneTown">Solo dettaglio</button></div></div><div class="history-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Serie storiche aggregate 2014-2025">${svg}</svg></div><div class="history-foot"><strong>2022.</strong> La linea evidenzi