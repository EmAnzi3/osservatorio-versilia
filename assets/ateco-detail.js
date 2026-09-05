(() => {
  'use strict';

  /*
   * Compatibilità con la build statica: le preview e la produzione caricano
   * ancora assets/ateco-detail.js come enhancer dell'Economia. Da v1.30 questo
   * file non rende più un secondo explorer ATECO: carica esclusivamente il
   * nuovo Atlante Registro Imprese, evitando due letture parallele delle UL.
   */
  const SCRIPT_URL = document.currentScript?.src || location.href;
  const VERSION = '20260904-v130-economia-atlas-draft';
  const page = document.body.dataset.page || '';
  const theme = document.body.dataset.theme || '';
  const relevant = page === 'town' || (page === 'compare' && theme === 'economia');
  if (!relevant) return;

  const cssUrl = new URL(`./economy-atlas.css?v=${VERSION}`, SCRIPT_URL).href;
  if (![...document.querySelectorAll('link[rel="stylesheet"]')].some(link => link.href === cssUrl || /\/economy-atlas\.css(?:\?|$)/.test(link.href))) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssUrl;
    document.head.appendChild(link);
  }

  if ([...document.scripts].some(script => /\/economy-atlas\.js(?:\?|$)/.test(script.src))) return;

  const script = document.createElement('script');
  script.src = new URL(`./economy-atlas.js?v=${VERSION}`, SCRIPT_URL).href;
  script.async = false;
  script.dataset.ovEconomyAtlas = '1';
  script.addEventListener('error', () => {
    console.error('[economy-atlas] Impossibile caricare il nuovo Atlante delle attività economiche.');
  }, { once: true });
  document.head.appendChild(script);
})();
