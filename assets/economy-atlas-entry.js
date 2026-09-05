(()=>{
  'use strict';
  if(document.body.dataset.page!=='compare'||document.body.dataset.theme!=='economia')return;
  const mount=()=>{
    if(document.getElementById('economy-atlas-entry'))return true;
    const hero=document.querySelector('main[data-theme="economia"] .topic-hero');
    if(!hero)return false;
    const section=document.createElement('section');
    section.id='economy-atlas-entry';
    section.className='economy-atlas-entry page-width';
    section.innerHTML=`<div class="economy-atlas-entry-card"><div><span class="overline">Economia · Registro Imprese</span><h2>Atlante delle attività economiche</h2><p>Esplora 1.228 codici ATECO, confronta le unità locali nei sette Comuni e leggi specializzazione, peso toscano e storico 2014–2025.</p><div class="economy-atlas-entry-facts"><span>1.228 codici</span><span>7 Comuni + Toscana</span><span>ATECO 2007 · agg. 2022</span></div></div><a class="economy-atlas-entry-link" href="atlante-attivita-economiche/">Esplora l’Atlante →</a></div>`;
    hero.insertAdjacentElement('afterend',section);
    return true;
  };
  if(mount())return;
  const observer=new MutationObserver(()=>{if(mount())observer.disconnect()});
  observer.observe(document.getElementById('app')||document.documentElement,{childList:true,subtree:true});
})();
