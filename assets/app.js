(() => {
  'use strict';

  const loader = document.currentScript;
  const app = document.getElementById('app');
  const partsRoot = new URL('./app-parts/', loader.src);
  globalThis.__OV_SCRIPT_URL__ = loader.src;

  const loadStylesheet = href => new Promise(resolve => {
    const existing = document.querySelector(`link[href="${href}"]`);
    if (existing) {
      if (existing.sheet) resolve();
      else existing.addEventListener('load', resolve, { once: true });
      return;
    }
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.addEventListener('load', resolve, { once: true });
    link.addEventListener('error', resolve, { once: true });
    document.head.append(link);
  });

  const load = async () => {
    await loadStylesheet(new URL('./fonts.css', loader.src).href);
    if (document.fonts?.load) {
      await Promise.allSettled([
        document.fonts.load('400 1em Geist'),
        document.fonts.load('700 1em Geist'),
        document.fonts.load('500 1em "Geist Mono"')
      ]);
    }

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
