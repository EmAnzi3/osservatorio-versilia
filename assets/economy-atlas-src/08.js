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
