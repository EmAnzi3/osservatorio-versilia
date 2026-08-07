(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', script?.src || location.href);
  const SERVICE_WORKER = new URL('service-worker.js', ROOT).href;
  const INSTALL_ICON = `
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 3v12"></path><path d="m7 10 5 5 5-5"></path><path d="M5 20h14"></path>
    </svg>`;

  let deferredPrompt = null;
  let mountScheduled = false;

  const isStandalone = () =>
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  const isIos = () =>
    /iphone|ipad|ipod/i.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  function hideInstallUi() {
    document.querySelectorAll('[data-pwa-install-ui]').forEach(node => node.remove());
    document.querySelector('#pwa-install-dialog')?.close?.();
  }

  function dialogMarkup() {
    const ios = isIos();
    return `
      <dialog class="pwa-install-dialog" id="pwa-install-dialog" aria-labelledby="pwa-dialog-title">
        <button class="pwa-dialog-close" type="button" aria-label="Chiudi">×</button>
        <span class="pwa-dialog-kicker">Osservatorio Versilia · app</span>
        <h2 id="pwa-dialog-title">${ios ? 'Installa su iPhone o iPad' : 'Installa Osservatorio Versilia'}</h2>
        ${ios ? `
          <ol class="pwa-ios-steps">
            <li><strong>1</strong><span>Tocca <b>Condividi</b> nella barra di Safari.</span></li>
            <li><strong>2</strong><span>Scegli <b>Aggiungi alla schermata Home</b>.</span></li>
            <li><strong>3</strong><span>Tocca <b>Aggiungi</b>: l'icona OV comparirà tra le app.</span></li>
          </ol>
          <p class="pwa-dialog-note">Su iPhone e iPad l'installazione passa dal menu Condividi di Safari.</p>
        ` : `
          <p>Se il browser non mostra il pulsante automatico, apri il suo menu e scegli <b>Installa app</b> oppure <b>Aggiungi alla schermata Home</b>.</p>
          <p class="pwa-dialog-note">L'app usa lo stesso sito: dati e aggiornamenti restano sempre allineati.</p>
        `}
      </dialog>`;
  }

  function ensureDialog() {
    let dialog = document.querySelector('#pwa-install-dialog');
    if (dialog) return dialog;
    document.body.insertAdjacentHTML('beforeend', dialogMarkup());
    dialog = document.querySelector('#pwa-install-dialog');
    dialog.querySelector('.pwa-dialog-close')?.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    return dialog;
  }

  function openInstructions() {
    const dialog = ensureDialog();
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }

  async function requestInstall() {
    if (isStandalone()) {
      hideInstallUi();
      return;
    }

    if (!deferredPrompt) {
      openInstructions();
      return;
    }

    deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice.catch(() => null);
    deferredPrompt = null;
    document.documentElement.classList.remove('pwa-install-ready');
    if (choice?.outcome === 'accepted') hideInstallUi();
  }

  function bindInstallButton(button) {
    if (button.dataset.pwaBound === '1') return;
    button.dataset.pwaBound = '1';
    button.addEventListener('click', requestInstall);
  }

  function mountHeaderButton() {
    if (isStandalone() || document.querySelector('[data-pwa-header-install]')) return;
    const actions = document.querySelector('.site-header-actions');
    if (!actions) return;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'pwa-install-button';
    button.dataset.pwaInstallUi = '1';
    button.dataset.pwaHeaderInstall = '1';
    button.title = 'Installa Osservatorio Versilia';
    button.setAttribute('aria-label', 'Installa Osservatorio Versilia come app');
    button.innerHTML = `${INSTALL_ICON}<span>Installa app</span>`;
    bindInstallButton(button);

    const search = actions.querySelector('.global-search-trigger');
    actions.insertBefore(button, search || null);
  }

  function mountHomeCallout() {
    if (isStandalone() || document.body.dataset.page !== 'home' || document.querySelector('.pwa-install-callout')) return;
    const hero = document.querySelector('.home-hero');
    if (!hero) return;

    const section = document.createElement('section');
    section.className = 'pwa-install-callout page-width';
    section.dataset.pwaInstallUi = '1';
    section.setAttribute('aria-label', 'Installa Osservatorio Versilia come app');
    section.innerHTML = `
      <div class="pwa-callout-icon" aria-hidden="true">
        <img src="${new URL('pwa/icon-192.png', ROOT).href}" alt="">
      </div>
      <div class="pwa-callout-copy">
        <span class="pwa-callout-kicker">Disponibile anche come app</span>
        <strong>Porta l'Osservatorio sul telefono.</strong>
        <p>Installalo dalla schermata Home: si apre come un'app e le pagine già visitate restano disponibili anche senza rete.</p>
      </div>
      <button type="button" class="pwa-callout-action">${INSTALL_ICON}<span>Installa app</span></button>`;
    bindInstallButton(section.querySelector('button'));
    hero.insertAdjacentElement('afterend', section);
  }

  function mountUi() {
    if (isStandalone()) {
      hideInstallUi();
      return;
    }
    mountHeaderButton();
    mountHomeCallout();
  }

  function scheduleMount() {
    if (mountScheduled) return;
    mountScheduled = true;
    requestAnimationFrame(() => {
      mountScheduled = false;
      mountUi();
    });
  }

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredPrompt = event;
    document.documentElement.classList.add('pwa-install-ready');
    scheduleMount();
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    document.documentElement.classList.remove('pwa-install-ready');
    hideInstallUi();
  });

  window.matchMedia?.('(display-mode: standalone)').addEventListener?.('change', scheduleMount);

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(SERVICE_WORKER, { scope: ROOT.pathname }).catch(error => {
        console.warn('Registrazione PWA non riuscita', error);
      });
    });
  }

  new MutationObserver(scheduleMount).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scheduleMount, { once: true });
  else scheduleMount();
})();
