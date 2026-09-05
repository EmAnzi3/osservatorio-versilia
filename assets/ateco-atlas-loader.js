(() => {
  'use strict';
  const app=document.getElementById('app');
  const ownScript=document.currentScript;

  async function decodePayload(){
    const encoded=window.__ATECO_ATLAS_PAYLOAD_GZIP||'';
    if(!encoded) throw new Error('Dataset Atlante non disponibile');
    const binary=atob(encoded);
    const bytes=new Uint8Array(binary.length);
    for(let i=0;i<binary.length;i++) bytes[i]=binary.charCodeAt(i);
    if(typeof DecompressionStream!=='function') throw new Error('Browser non compatibile con il dataset compresso');
    const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }
  function loadScript(name){
    return new Promise((resolve,reject)=>{
      const script=document.createElement('script');
      script.src=new URL(name,ownScript.src).href;
      script.onload=resolve;
      script.onerror=()=>reject(new Error(`Impossibile caricare ${name}`));
      document.head.append(script);
    });
  }
  (async()=>{
    if(!app) throw new Error('Struttura Atlante non disponibile');
    window.__ATECO_PAYLOAD=await decodePayload();
    await loadScript('./ateco-atlas-core-1.js?v=1');
    await loadScript('./ateco-atlas-core-2.js?v=1');
    document.body.classList.add('atlas-ready');
  })().catch(error=>{
    console.error(error);
    if(app) app.innerHTML='<section class="page-width"><div class="app-error"><strong>Impossibile caricare l’Atlante.</strong><p>Ricarica la pagina. Se il problema persiste, segnala l’indirizzo della pagina.</p></div></section>';
  });
})();
