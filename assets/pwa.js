(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', script?.src || location.href);
  const SERVICE_WORKER = new URL('service-worker.js', ROOT).href;

  // Il sito mantiene soltanto il supporto tecnico PWA/offline.
  // L'installazione, se disponibile, resta interamente gestita dal browser.
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(SERVICE_WORKER, { scope: ROOT.pathname }).catch(error => {
        console.warn('Registrazione PWA non riuscita', error);
      });
    }, { once: true });
  }
})();
