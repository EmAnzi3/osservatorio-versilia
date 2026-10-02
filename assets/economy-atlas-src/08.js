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

/* ov-atlas-export-actions: standalone Atlas only */
function csvCell(value){
  const text=String(value??'');
  return /[;"\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;
}
function csvLevel(n){return n.d?(LEVELS[n.d.length]||'Codice'):'Sezione'}
function csvCode(n){return n.d?String(n.sec)+' '+displayCode(n.d):n.sec}
function atlasCsvRows(){
  const t=activeTerritoryMeta();
  const territory=t?.name||'Versilia';
  const ordered=[...nodes.values()].filter(n=>n&&n.sec).sort((a,b)=>{
    const ac=String(a.sec)+' '+String(a.d||''),bc=String(b.sec)+' '+String(b.d||'');
    return ac.localeCompare(bc,'it',{numeric:true});
  });
  const rows=[['Territorio','Codice ATECO','Livello','Descrizione','Anno','UL attive','UL artigiane (2025)','Fonte']];
  ordered.forEach(n=>{
    const agg=aggregateNode(n.sec,n.d);
    years.forEach((yr,yi)=>{
      const active=t?agg.towns[t.i][yi]:agg.vers[yi];
      const artisan=yi===latest?(t?agg.art[t.i]:sumNullable(agg.art)):null;
      if(active===null&&artisan===null)return;
      rows.push([territory,csvCode(n),csvLevel(n),n.label||'',yr,active??'',artisan??'','Regione Toscana / Registro Imprese InfoCamere']);
    });
  });
  return rows;
}
function downloadAtlasCsv(){
  const rows=atlasCsvRows();
  const csv='\ufeff'+rows.map(row=>row.map(csvCell).join(';')).join('\r\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download='atlante-attivita-economiche-'+(state.territory||'versilia')+'-2014-2025.csv';
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),0);
}
function ensureAtlasExportActions(){
  if(root.host?.hasAttribute('embedded'))return;
  if(root.querySelector('.atlas-export-actions'))return;
  const standaloneStyle=document.createElement('style');
  standaloneStyle.id='atlas-standalone-ui-style';
  standaloneStyle.textContent='.hero{position:relative;width:100vw;min-height:365px;margin-left:calc(50% - 50vw);display:grid;grid-template-columns:80px minmax(0,1fr);align-content:center;gap:28px;padding:46px max(24px,calc((100vw - 1240px)/2));border:0;color:#fff;background:linear-gradient(90deg,rgba(6,31,49,.95) 0%,rgba(6,31,49,.84) 38%,rgba(6,31,49,.48) 69%,rgba(6,31,49,.18) 100%),url("https://upload.wikimedia.org/wikipedia/commons/4/40/11_Piacenza%2C_Italy_-_%E3%82%B7%E3%83%A7%E3%83%83%E3%83%94%E3%83%B3%E3%82%B0_%E3%82%A4%E3%82%BF%E3%83%AA%E3%82%A2.jpg") center 54%/cover no-repeat;overflow:hidden}.hero:before{content:"";position:absolute;left:max(24px,calc((100vw - 1240px)/2));top:0;width:72px;height:4px;background:#ffdb4d}.hero:after{content:"Attività commerciali · Wikimedia Commons";position:absolute;right:max(14px,calc((100vw - 1240px)/2));bottom:12px;padding:5px 8px;border-radius:6px;background:rgba(5,31,48,.62);color:rgba(255,255,255,.78);font-size:8px;font-weight:600}.hero>*{position:relative;z-index:2}.hero-symbol{width:68px;height:68px;border:1px solid rgba(255,255,255,.38);border-radius:20px 20px 20px 7px;background:rgba(255,255,255,.14);color:#ffdb4d;display:grid;place-items:center;font:800 18px var(--mono);backdrop-filter:blur(8px)}.hero .overline{color:#ffdb4d}.hero h1{color:#fff;text-shadow:0 3px 22px rgba(0,0,0,.24)}.hero p{max-width:780px;color:rgba(255,255,255,.91);font-size:15px;line-height:1.58;margin:0}.hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.meta-pill{background:rgba(5,31,48,.50);border:1px solid rgba(255,255,255,.24);border-radius:999px;padding:8px 11px;color:#fff;font-size:10px;font-weight:750;backdrop-filter:blur(8px)}.meta-pill strong{color:#ffdb4d}@media(max-width:680px){.hero{min-height:390px;grid-template-columns:44px minmax(0,1fr);align-content:end;gap:14px;padding:36px 20px 34px}.hero:before{left:20px;width:54px}.hero:after{right:9px;bottom:8px;font-size:7px}.hero-symbol{width:44px;height:44px;border-radius:13px 13px 13px 4px;font-size:13px}.hero h1{font-size:47px}.hero p{font-size:13px}}';
  root.appendChild(standaloneStyle);
  const explorer=root.querySelector('.explorer');
  if(!explorer)return;
  const style=document.createElement('style');
  style.id='atlas-data-actions-style';
  style.textContent=`.data-actions{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 18px}.data-actions button{min-height:30px;display:inline-flex;align-items:center;justify-content:center;border:1px solid #c9d3d1;border-radius:7px;background:#fbf7f0;color:#102f45;padding:5px 8px;font-size:7px;font-weight:760;line-height:1;white-space:nowrap;cursor:pointer}.data-actions button:hover,.data-actions button:focus-visible{border-color:#145b78;background:#e4eff2;outline:none}.data-actions [data-download]::before,.data-actions [data-print]::before{content:"";width:17px;height:17px;flex:0 0 17px;margin-right:5px;background:center/contain no-repeat}.data-actions [data-download]::before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23217346' d='M4 2h11l5 5v15H4z'/%3E%3Cpath fill='none' stroke='%23fff' stroke-width='1.4' d='M15 2v5h5'/%3E%3Cpath fill='%23fff' d='M7.1 10h2.1l1.3 2.2 1.3-2.2h2l-2.2 3.5 2.4 3.8h-2.1l-1.5-2.4-1.5 2.4H6.8l2.4-3.8z'/%3E%3C/svg%3E")}.data-actions [data-print]::before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23b84b34' d='M4 2h11l5 5v15H4z'/%3E%3Cpath fill='none' stroke='%23fff' stroke-width='1.4' d='M15 2v5h5'/%3E%3Ctext x='6.2' y='16.2' fill='%23fff' font-size='6.1' font-family='Arial,sans-serif' font-weight='700'%3EPDF%3C/text%3E%3C/svg%3E")}@media print{.data-actions{display:none!important}}`;
  root.appendChild(style);
  const bar=document.createElement('div');
  bar.className='data-actions atlas-export-actions';
  bar.innerHTML='<button type="button" id="atlasDownloadCsv" data-download>Scarica CSV</button><button type="button" id="atlasPrint" data-print>Stampa / PDF</button>';
  explorer.insertAdjacentElement('beforebegin',bar);
  bar.querySelector('#atlasDownloadCsv').onclick=downloadAtlasCsv;
  bar.querySelector('#atlasPrint').onclick=()=>window.print();
}

renderAll();
ensureAtlasExportActions();

    }
  }
  if(!customElements.get('ov-economy-atlas')) customElements.define('ov-economy-atlas', OVEconomyAtlas);
})();
