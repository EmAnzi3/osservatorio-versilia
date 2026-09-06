hierarchyContext(n)}</div><div class="empty"><strong>Per questo livello non è disponibile un valore autonomo.</strong><br>Usa <strong>Composizione %</strong> per leggere la distribuzione delle attività oppure scegli una voce più specifica.</div>`;return}
  box.innerHTML=state.tab==='current'?renderCurrent(row,n):renderHistory(row,n);wireAnalysis();
}
function wireAnalysis(){
  root.querySelectorAll('[data-metric]').forEach(b=>b.onclick=()=>{state.metric=b.dataset.metric;renderAnalysis()});root.querySelectorAll('.lrow[data-town]').forEach(r=>r.onclick=()=>{state.detailTown=r.dataset.town;renderAnalysis()});let ds=$('#detailTown');if(ds)ds.onchange=()=>{state.detailTown=ds.value;renderAnalysis()};root.querySelectorAll('[data-vtown]').forEach(b=>b.onclick=()=>{let s=b.dataset.vtown;state.visible.has(s)?state.visible.delete(s):state.visible.add(s);renderAnalysis()});let a=$('#allTowns');if(a)a.onclick=()=>{state.visible=new Set(towns.map(t=>t.slug));renderAnalysis()};let o=$('#oneTown');if(o)o.onclick=()=>{let s=state.detailTown||towns[0].slug;state.visible=new Set([s]);renderAnalysis()};
}
function renderAll(){renderSelectors();renderCrumbs();renderDonut();renderAnalysis()}
function searchItems(q){let nq=norm(q),digits=nq.replace(/[^0-9]/g,'');let score=new Map();for(const [alias,raws] of Object.entries(aliases))if(norm(alias).includes(nq)||nq.includes(norm(alias)))raws.forEach((r,i)=>score.set(r,100-i));for(const [raw,row] of exact){let n=nodes.get(raw),code=rawToPretty(raw),label=n?.label||'';let s=0;if(digits&&raw.replace(/\D/g,'').startsWith(digits))s=90;if(nq&&norm(label).includes(nq))s=Math.max(s,80);if(norm(code).includes(nq))s=Math.max(s,85);if(s)score.set(raw,Math.max(score.get(raw)||0,s));}return [...score.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,12).map(([r])=>nodes.get(r))}
$('#search').oninput=e=>{let q=e.target.value.trim(),res=$('#results');if(!q){res.hidden=true;return}let items=searchItems(q);res.innerHTML=items.length?items.map(n=>`<button class="result" data-raw="${n.key}"><span class="result-code">${n.sec} · ${displayCode(n.d)}</span><span class="result-name">${escapeHtml(n.label)}</span><span class="result-level">${LEVELS[n.d.length]}</span></button>`).join(''):'<div class="empty">Nessun risultato.</div>';res.hidden=false;res.querySelectorAll('[data-raw]').forEach(b=>b.onclick=()=>{let n=nodes.get(b.dataset.raw);$('#search').value=`${n.sec} ${displayCode(n.d)} · ${n.label}`;res.hidden=true;selectNode(n.sec,n.d,false)})};
$('#clear').onclick=clearAll;root.querySelector('.quick').onclick=e=>{let b=e.target.closest('button');if(!b)return;if(b.dataset.code){let n=nodes.get(b.dataset.code);if(n){$('#search').value=`${n.sec} ${displayCode(n.d)} · ${n.label}`;selectNode(n.sec,n.d,false)}}else if(b.dataset.q){$('#search').value=b.dataset.q;$('#search').dispatchEvent(new Event('input'));$('#search').focus()}};
$('#tabCurrent').onclick=()=>{state.tab='current';renderAnalysis()};$('#tabHistory').onclick=()=>{state.tab='history';renderAnalysis()};$('#modeComposition').onclick=()=>{state.leftMode='composition';state.detailTown=initialTown||'';renderDonut();renderAnalysis()};$('#modeNavigation').onclick=()=>{state.leftMode='navigation';state.detailTown=initialTown||'';renderDonut();renderAnalysis()};
root.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))$('#results').hidden=true});
applyEmbeddedTaxonomy();

// Territorial context: Versilia or one municipality, selectable from every standalone Atlas view.
fmt = function(v,d=0){if(v===null||v===undefined||Number.isNaN(v))return'n.d.';return new Intl.NumberFormat('it-IT',{useGrouping:'always',minimumFractionDigits:d,maximumFractionDigits:d}).format(v)};
const requestedTerritory = initialTown || new URLSearchParams(location.search).get('comune') || '';
const requestedTerritoryMeta = towns.find(t => t.slug === requestedTerritory) || null;
state.territory = requestedTerritoryMeta?.slug || '';
state.detailTown = state.territory || '';
state.visible = new Set(state.territory ? [state.territory] : towns.map(t => t.slug));

const originalCompositionChildren = compositionChildren;
const originalCompositionTotalForCurrent = compositionTotalForCurrent;
const originalRenderDonut = renderDonut;
const originalRenderCurrentDerived = renderCurrentDerived;
const originalRenderAnalysis = renderAnalysis;
const originalRenderAll = renderAll;
const originalSelectNode = selectNode;
const originalClearAll = clearAll;

function activeTerritoryMeta(){ return towns.find(t => t.slug === state.territory) || null; }
function territoryLabel(){ return activeTerritoryMeta()?.name || 'Versilia'; }
function aggregateValueForTerritory(agg, yi=latest){ const t=activeTerritoryMeta(); return t ? agg.towns[t.i][yi] : agg.vers[yi]; }
compositionChildren = function(){
  const kids=state.sec?childNodes(state.sec,state.d):sections.map(([s])=>ensure(s,''));
  return kids.map(n=>{const agg=aggregateNode(n.sec,n.d);return {node:n,value:aggregateValueForTerritory(agg,latest)};});
};
compositionTotalForCurrent = function(){
  if(!state.sec) return sumNullable(compositionChildren().map(x=>x.value));
  return aggregateValueForTerritory(aggregateNode(state.sec,state.d),latest);
};
selectNode = function(sec,d='',autoAdvance=true){state.sec=sec;state.d=autoAdvance&&sec?descendSingleton(sec,d):d;state.detailTown=state.territory||'';renderAll()};
clearAll = function(){state.sec='';state.d='';state.tab='current';state.metric='active';state.detailTown=state.territory||'';$('#search').value='';$('#results').hidden=true;renderAll()};
renderCurrentDerived = function(n){
  const markup=originalRenderCurrentDerived(n);
  return markup.replace(' UL attive in Versilia · anno 2025',` UL attive in ${escapeHtml(territoryLabel())} · anno 2025`);
};
renderDonut = function(){
  originalRenderDonut();
  if(state.leftMode==='composition'&&!state.sec){ const strong=$('#donutCenter strong'); if(strong) strong.textContent=territoryLabel(); }
};
renderAnalysis = function(){
  if(state.territory&&!state.detailTown) state.detailTown=state.territory;
  originalRenderAnalysis();
  const town=activeTerritoryMeta(),heading=$('#analysisHeading');
  if(heading&&town) heading.textContent=`${town.name} nel confronto territoriale`;
};
function quickValue(raw){
  const row=exact.get(raw); if(!row) return null;
  const t=activeTerritoryMeta();
  return t ? row[3+t.i][0][latest] : sumNullable(towns.map(item=>row[3+item.i][0][latest]));
}
function syncTerritoryContext(){
  const searchTop=$('.search-top');
  if(searchTop&&!$('#territory')){
    searchTop.insertAdjacentHTML('afterbegin',`<label class="field territory-field"><span>Territorio</span><select id="territory" aria-label="Territorio dell'Atlante"><option value="">Versilia</option>${towns.map(t=>`<option value="${t.slug}">${escapeHtml(t.name)}</option>`).join('')}</select></label>`);
    const style=document.createElement('style');style.id='territory-style';style.textContent='.search-top{grid-template-columns:minmax(190px,.34fr) minmax(0,1fr) auto}.territory-field select{width:100%;height:50px;border:1px solid #c7d2d0;border-radius:13px;padding:0 38px 0 13px;background:#fff;outline:none;font-weight:750}.territory-field select:focus{border-color:var(--theme);box-shadow:0 0 0 3px rgba(173,98,71,.11)}.hero-symbol svg{width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}@media(max-width:680px){.search-top{grid-template-columns:1fr}}';root.prepend(style);
    const territory=$('#territory');territory.onchange=()=>{
      state.territory=territory.value;state.detailTown=state.territory||'';state.visible=new Set(state.territory?[state.territory]:towns.map(t=>t.slug));
      if(!root.host?.hasAttribute('embedded')){const url=new URL(location.href);if(state.territory)url.searchParams.set('comune',state.territory);else url.searchParams.delete('comune');history.replaceState(history.state,'',url.pathname+url.search+url.hash)}
      renderAll();
    };
  }
  const territory=$('#territory');if(territory)territory.value=state.territory||'';
  const meta=activeTerritoryMeta();
  const symbol=root.querySelector('.hero-symbol');if(symbol)symbol.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v9h16v-9"/><path d="M3 10h18l-2-5H5l-2 5Z"/><path d="M7 10v1a2 2 0 0 0 4 0v-1m0 0v1a2 2 0 0 0 4 0v-1m0 0v1a2 2 0 0 0 4 0v-1"/><path d="M9 19v-5h6v5"/></svg>';
  const title=root.querySelector('.hero h1');if(title)title.textContent=meta?`Atlante delle attività economiche · ${meta.name}`:'Atlante delle attività economiche';
  const intro=root.querySelector('.hero p');if(intro)intro.textContent=meta?`Esplora le attività economiche di ${meta.name} dalla Sezione alla massima granularità disponibile, mantenendo il confronto con gli altri Comuni della Versilia e con la Toscana.`:'Esplora la presenza delle attività economiche nei sette Comuni della Versilia, dalla Sezione alla massima granularità disponibile. Seleziona un Comune per leggerne la struttura in modo dedicato.';
  const over=root.querySelector('.hero .overline');if(over)over.textContent=meta?`Economia · ${meta.name} · Registro Imprese`:'Economia · Registro Imprese';
  const quickTitle=$('.quick-title');if(quickTitle)quickTitle.textContent=`Accessi rapidi · attività frequenti in ${territoryLabel()} · 2025`;
  root.querySelectorAll('.quick button[data-code]').forEach(button=>{const b=button.querySelector('b'),v=quickValue(button.dataset.code);if(b)b.textContent=v===null?'n.d.':`${fmt(v)} UL`;});
}
renderAll = function(){
  if(state.territory&&!state.detailTown) state.detailTown=state.territory;
  syncTerritoryContext();originalRenderAll();syncTerritoryContext();
};

if(initialTown){
  const townMeta=towns.find(t=>t.slug===initialTown);
  const quickTitle=$('.quick-title');
  if(quickTitle) quickTitle.textContent='Accessi rapidi · attività frequenti in Versilia · 2025';
  const heading=$('#analysisHeading');
  if(heading&&townMeta) heading.textContent=`${townMeta.name} nel confronto territoriale`;
}
renderAll();

    }
  }
  if(!customElements.get('ov-economy-atlas')) customElements.define('ov-economy-atlas', OVEconomyAtlas);
})();
