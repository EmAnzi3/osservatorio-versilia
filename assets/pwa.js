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
  let headerObserver = null;
  let appObserver = null;

  const isStandalone = () =>
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  const isIos = () =>
    /iphone|ipad|ipod/i.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  const isAndroid = () => /Android/i.test(navigator.userAgent || '');
  const isSamsungInternet = () => /SamsungBrowser/i.test(navigator.userAgent || '');
  const isChromeAndroid = () => {
    const ua = navigator.userAgent || '';
    return /Android/i.test(ua) && /Chrome\//i.test(ua) && !/(SamsungBrowser|EdgA|OPR|Opera)/i.test(ua);
  };

  function hideInstallUi() {
    document.querySelectorAll('[data-pwa-install-ui]').forEach(node => node.remove());
    document.querySelector('#pwa-install-dialog')?.close?.();
  }

  function dialogMarkup() {
    const ios = isIos();
    const samsung = isSamsungInternet();
    const chromeAndroid = isChromeAndroid();
    let title = 'Installa Osservatorio Versilia';
    let body = `
      <p>Usa il comando <b>Installa app</b> del browser, quando disponibile.</p>
      <p class="pwa-dialog-note">Il browser decide la modalità di installazione disponibile sul dispositivo.</p>`;

    if (ios) {
      title = 'Installa su iPhone o iPad';
      body = `
        <ol class="pwa-ios-steps">
          <li><strong>1</strong><span>Apri il sito in <b>Safari</b>.</span></li>
          <li><strong>2</strong><span>Tocca <b>Condividi → Aggiungi alla schermata Home</b>.</span></li>
          <li><strong>3</strong><span>Conferma con <b>Aggiungi</b>.</span></li>
        </ol>
        <p class="pwa-dialog-note">Su iPhone e iPad l'installazione delle web app passa da Safari.</p>`;
    } else if (samsung) {
      title = 'Installa con Samsung Internet';
      body = `
        <ol class="pwa-ios-steps pwa-samsung-steps">
          <li><strong>1</strong><span>Usa il <b>badge di installazione PWA</b> di Samsung Internet oppure il comando <b>Installa app</b>, quando compare.</span></li>
          <li><strong>2</strong><span>Se compare <b>Installa nella schermata App</b>, conferma: è la modalità che integra la PWA tra le applicazioni.</span></li>
          <li><strong>3</strong><span>Se invece compare soltanto <b>Aggiungere alla schermata Home?</b> con un riquadro 1×1, il browser sta offrendo un semplice collegamento.</span></li>
        </ol>
        <p class="pwa-dialog-note">Il sito non può trasformare un collegamento 1×1 in un'app: quella scelta è gestita dal browser e da Android.</p>`;
    } else if (chromeAndroid) {
      title = 'Installa con Chrome';
      body = `
        <ol class="pwa-ios-steps pwa-chrome-steps">
          <li><strong>1</strong><span>Apri il menu <b>⋮</b> di Chrome e scegli <b>Installa e crea scorciatoia</b>.</span></li>
          <li><strong>2</strong><span>Nel pannello successivo scegli la prima voce <b>Installa</b>. Non scegliere <b>Crea scorciatoia</b>: quella apre il sito dentro Chrome.</span></li>
          <li><strong>3</strong><span>Dopo <b>Installa</b>, se appare <b>Aggiungere alla schermata Home?</b> mentre vedi <b>Installazione di Osservatorio in corso…</b>, l'app è già in installazione. Tocca <b>Annulla</b> se non vuoi anche l'icona sulla Home: l'installazione continua e l'app resta disponibile tra le applicazioni.</span></li>
        </ol>
        <p class="pwa-dialog-note">Su Galaxy la richiesta di aggiungere l'icona alla Home può comparire anche durante una vera installazione. È separata dalla scelta “Installa”.</p>`;
    } else if (isAndroid()) {
      title = 'Installa su Android';
      body = `
        <p>Apri il menu del browser e scegli <b>Installa app</b>, se disponibile.</p>
        <p class="pwa-dialog-note">Se il browser propone una scelta tra installazione e scorciatoia, usa l'installazione. L'eventuale richiesta successiva di aggiungere l'icona alla Home può essere opzionale.</p>`;
    }

    return `
      <dialog class="pwa-install-dialog" id="pwa-install-dialog" aria-labelledby="pwa-dialog-title">
        <button class="pwa-dialog-close" type="button" aria-label="Chiudi">×</button>
        <span class="pwa-dialog-kicker">Osservatorio Versilia · app</span>
        <h2 id="pwa-dialog-title">${title}</h2>
        ${body}
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

  function installLabel() {
    if (isAndroid() || isIos()) return 'Come installare';
    return deferredPrompt ? 'Installa app' : 'Come installare';
  }

  function syncInstallControls() {
    const label = installLabel();
    const ready = Boolean(deferredPrompt) && !isAndroid() && !isIos();
    document.querySelectorAll('[data-pwa-install-action]').forEach(button => {
      const span = button.querySelector('span');
      if (span && span.textContent !== label) span.textContent = label;
      const state = ready ? 'ready' : 'instructions';
      if (button.dataset.pwaState !== state) button.dataset.pwaState = state;
      const title = `${label} · Osservatorio Versilia`;
      if (button.title !== title) button.title = title;
      const aria = `${label} Osservatorio Versilia come app`;
      if (button.getAttribute('aria-label') !== aria) button.setAttribute('aria-label', aria);
    });
  }

  async function requestInstall() {
    if (isStandalone()) {
      hideInstallUi();
      return;
    }

    if (isAndroid() || isIos()) {
      openInstructions();
      return;
    }

    if (deferredPrompt) {
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice.catch(() => null);
      deferredPrompt = null;
      document.documentElement.classList.remove('pwa-install-ready');
      syncInstallControls();
      if (choice?.outcome === 'accepted') hideInstallUi();
      return;
    }

    openInstructions();
  }

  function bindInstallButton(button) {
    if (button.dataset.pwaBound === '1') return;
    button.dataset.pwaBound = '1';
    button.dataset.pwaInstallAction = '1';
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
    button.innerHTML = `${INSTALL_ICON}<span>${installLabel()}</span>`;
    bindInstallButton(button);

    const search = actions.querySelector('.global-search-trigger');
    actions.insertBefore(button, search || null);
  }

  function stopLifecycleObservers() {
    headerObserver?.disconnect();
    appObserver?.disconnect();
    headerObserver = null;
    appObserver = null;
  }

  function mountUi() {
    if (isStandalone()) {
      stopLifecycleObservers();
      hideInstallUi();
      return;
    }
    mountHeaderButton();
    syncInstallControls();
  }

  function scheduleMount() {
    if (mountScheduled) return;
    mountScheduled = true;
    requestAnimationFrame(() => {
      mountScheduled = false;
      mountUi();
    });
  }

  function startLifecycleObservers() {
    if (isStandalone()) {
      mountUi();
      return;
    }

    const headerMount = document.getElementById('site-header-mount');
    if (headerMount && !headerObserver) {
      headerObserver = new MutationObserver(scheduleMount);
      headerObserver.observe(headerMount, { childList: true });
    }

    const appMount = document.getElementById('app');
    if (appMount && !appObserver) {
      appObserver = new MutationObserver(scheduleMount);
      appObserver.observe(appMount, { childList: true });
    }

    scheduleMount();
  }

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredPrompt = event;
    document.documentElement.classList.add('pwa-install-ready');
    syncInstallControls();
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    document.documentElement.classList.remove('pwa-install-ready');
    stopLifecycleObservers();
    hideInstallUi();
  });

  window.matchMedia?.('(display-mode: standalone)').addEventListener?.('change', () => {
    if (isStandalone()) mountUi();
    else startLifecycleObservers();
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(SERVICE_WORKER, { scope: ROOT.pathname }).catch(error => {
        console.warn('Registrazione PWA non riuscita', error);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startLifecycleObservers, { once: true });
  } else {
    startLifecycleObservers();
  }
  window.addEventListener('load', startLifecycleObservers, { once: true });
})();
