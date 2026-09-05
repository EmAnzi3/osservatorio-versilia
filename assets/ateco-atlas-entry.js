(() => {
  'use strict';
  const body=document.body;
  if(body?.dataset.page!=='compare' || body.dataset.theme!=='economia') return;
  const href='atlante-attivita-economiche/';
  const inject=()=>{
    if(document.querySelector('.atlas-entry-card')) return true;
    const dashboard=document.querySelector('.topic-dashboard');
    if(!dashboard) return false;
    const section=document.createElement('section');
    section.className='atlas-entry-card page-width';
    section.setAttribute('aria-labelledby','atlas-entry-title');
    section.innerHTML=`<div><span class="atlas-entry-kicker">Esploratore autonomo</span><h2 id="atlas-entry-title">Atlante delle attività economiche</h2><p>Esplora la struttura delle attività economiche della Versilia lungo tutta la gerarchia ATECO, confronta i sette Comuni e consulta specializzazione e storico.</p><div class="atlas-entry-meta"><span>1.228 codici ATECO</span><span>2014–2025</span><span>7 Comuni + Toscana</span></div></div><a class="button-link" href="${href}">Esplora l’Atlante <span aria-hidden="true">→</span></a>`;
    dashboard.parentNode.insertBefore(section,dashboard);
    return true;
  };
  if(inject()) return;
  const observer=new MutationObserver(()=>{if(inject())observer.disconnect();});
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
})();
