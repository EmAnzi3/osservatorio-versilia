(() => {
  'use strict';

  const loader = document.currentScript;
  const app = document.getElementById('app');
  const partsRoot = new URL('./app-parts/', loader.src);
  const legacyMediaRoot = 'https://versilia-in-numeri.decent-raven-1888.chatgpt.site/';
  globalThis.__OV_SCRIPT_URL__ = loader.src;

  const rewriteImage = image => {
    const raw = image.getAttribute('src') || '';
    let url;
    try { url = new URL(raw, location.href); } catch { return; }
    const marker = '/osservatorio-versilia/';
    const relative = url.pathname.includes(marker) ? url.pathname.split(marker)[1] : url.pathname.replace(/^\//, '');
    if (/^(crests\/|images\/versilia-viareggio-apuane\.jpg$)/i.test(relative) && url.hostname !== 'versilia-in-numeri.decent-raven-1888.chatgpt.site') {
      image.src = new URL(relative, legacyMediaRoot).href;
    }
  };

  const mediaObserver = new MutationObserver(records => {
    records.forEach(record => record.addedNodes.forEach(node => {
      if (!(node instanceof Element)) return;
      if (node.matches('img')) rewriteImage(node);
      node.querySelectorAll?.('img').forEach(rewriteImage);
    }));
  });
  mediaObserver.observe(document.documentElement, { childList: true, subtree: true });
  document.querySelectorAll('img').forEach(rewriteImage);

  const load = async () => {
    const parts = await Promise.all(
      Array.from({ length: 7 }, (_, index) => String(index).padStart(2, '0'))
        .map(async index => {
          const response = await fetch(new URL(`${index}.txt`, partsRoot), { cache: 'no-store' });
          if (!response.ok) throw new Error(`Impossibile caricare il modulo ${index}: ${response.status}`);
          return response.text();
        })
    );
    const moduleUrl = URL.createObjectURL(new Blob([parts.join('')], { type: 'text/javascript' }));
    try {
      await import(moduleUrl);
    } finally {
      URL.revokeObjectURL(moduleUrl);
    }
  };

  load().catch(error => {
    console.error(error);
    if (app) app.innerHTML = '<div class="app-error"><strong>Impossibile caricare l’applicazione.</strong><p>Ricarica la pagina. Se il problema persiste, segnala l’indirizzo della pagina.</p></div>';
  });
})();
