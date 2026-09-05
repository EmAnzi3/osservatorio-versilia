(() => {
  'use strict';

  const loader = document.currentScript;
  const app = document.getElementById('app');
  const partsRoot = new URL('./app-parts/', loader.src);
  globalThis.__OV_SCRIPT_URL__ = loader.src;

  const VERSION='20260903-v129-salute-finanziaria-selector';
  const ATLAS_VERSION='20260904-v130-economia-atlas-draft';
  const PINNED_COMMIT = 'c68e0ffc4b0f29a98eb4eb128625607374176479';
  const CDN_ROOT = `https://cdn.jsdelivr.net/gh/EmAnzi3/osservatorio-versilia@${PINNED_COMMIT}/`;
  const RAW_ROOT = `https://raw.githubusercontent.com/EmAnzi3/osservatorio-versilia/${PINNED_COMMIT}/`;
  const ORIGINAL_HERO = new URL(`../images/versilia-viareggio-apuane.jpg?v=${VERSION}`, loader.src).href;
  const crestFiles = {
    massarosa: 'massarosa.png',
    viareggio: 'viareggio.svg',
    camaiore: 'camaiore.svg',
    pietrasanta: 'pietrasanta.svg',
    seravezza: 'seravezza.png',
    'forte dei marmi': 'forte-dei-marmi.svg',
    stazzema: 'stazzema.webp'
  };

  const normalize = value => String(value || '')
    .toLocaleLowerCase('it')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .trim();

  function identifyCrest(image) {
    const alt = normalize(image.getAttribute('alt'));
    for (const [town, file] of Object.entries(crestFiles)) {
      if (alt.includes(town)) return file;
    }
    const src = image.getAttribute('src') || '';
    const filename = src.split(/[/?#]/).filter(Boolean).at(-1);
    return Object.values(crestFiles).includes(filename) ? filename : null;
  }

  function repairImage(image) {
    if (!(image instanceof HTMLImageElement)) return;
    const crest = identifyCrest(image);
    if (crest && image.dataset.ovCrestFixed !== crest) {
      image.dataset.ovCrestFixed = crest;
      image.addEventListener('error', () => {
        if (image.dataset.ovRawFallback === '1') return;
        image.dataset.ovRawFallback = '1';
        image.src = `${RAW_ROOT}crests/${crest}`;
      });
      image.src = `${CDN_ROOT}crests/${crest}`;
      return;
    }

    const alt = normalize(image.getAttribute('alt'));
    if (alt.includes('litorale di viareggio') && image.dataset.ovHeroFixed !== '1') {
      image.dataset.ovHeroFixed = '1';
      image.src = ORIGINAL_HERO;
    }
  }

  const imageObserver = new MutationObserver(records => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (!(node instanceof Element)) continue;
        if (node.matches('img')) repairImage(node);
        node.querySelectorAll?.('img').forEach(repairImage);
      }
    }
  });
  imageObserver.observe(document.documentElement, { childList: true, subtree: true });
  document.querySelectorAll('img').forEach(repairImage);

  const loadStylesheet = href => new Promise(resolve => {
    const existing = [...document.querySelectorAll('link[rel="stylesheet"]')]
      .find(link => link.href === href);
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

  const loadScript = src => new Promise((resolve, reject) => {
    const existing = [...document.scripts].find(script => script.src === src);
    if (existing) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.defer = true;
    script.addEventListener('load', resolve, { once: true });
    script.addEventListener('error', () => reject(new Error(`Impossibile caricare ${src}`)), { once: true });
    document.head.append(script);
  });

  const load = async () => {
    await Promise.all([
      loadStylesheet(new URL(`./fonts.css?v=${VERSION}`, loader.src).href),
      loadStylesheet(new URL(`./fidelity.css?v=${VERSION}`, loader.src).href),
      loadStylesheet(new URL(`./agricoltura-ii-draft.css?v=${VERSION}`, loader.src).href),
      loadStylesheet(new URL(`./economy-atlas.css?v=${ATLAS_VERSION}`, loader.src).href)
    ]);

    if (document.fonts?.load) {
      await Promise.allSettled([
        document.fonts.load('400 1em Geist'),
        document.fonts.load('700 1em Geist'),
        document.fonts.load('500 1em "Geist Mono"')
      ]);
    }

    await loadScript(new URL(`./agricoltura-ii-draft.js?v=${VERSION}`, loader.src).href);

    const parts = await Promise.all(
      Array.from({ length: 7 }, (_, index) => String(index).padStart(2, '0'))
        .map(async index => {
          const response = await fetch(new URL(`${index}.txt?v=${VERSION}`, partsRoot), { cache: 'no-store' });
          if (!response.ok) throw new Error(`Impossibile caricare il modulo ${index}: ${response.status}`);
          return response.text();
        })
    );

    const moduleUrl = URL.createObjectURL(new Blob([parts.join('')], { type: 'text/javascript' }));
    try {
      await import(moduleUrl);
      await loadScript(new URL(`./economy-atlas.js?v=${ATLAS_VERSION}`, loader.src).href);
      document.querySelectorAll('img').forEach(repairImage);
      await loadScript(new URL(`./fidelity.js?v=${VERSION}`, loader.src).href);
    } finally {
      URL.revokeObjectURL(moduleUrl);
    }
  };

  load().catch(error => {
    console.error(error);
    if (app) app.innerHTML = '<div class="app-error"><strong>Impossibile caricare l’applicazione.</strong><p>Ricarica la pagina. Se il problema persiste, segnala l’indirizzo della pagina.</p></div>';
  });
})();
