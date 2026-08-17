(() => {
  'use strict';

  if (document.querySelector('meta[name="robots"][content*="noindex" i]')) return;

  const profiles = [
    { network: 'Facebook', handle: '@osservatorioversilia', mark: 'f', url: 'https://www.facebook.com/osservatorioversilia' },
    { network: 'Instagram', handle: '@osservatorioversilia', mark: '◎', url: 'https://www.instagram.com/osservatorioversilia/' },
    { network: 'LinkedIn', handle: 'Osservatorio Versilia', mark: 'in', url: 'https://www.linkedin.com/company/osservatorioversilia' },
    { network: 'X', handle: '@OssVersilia', mark: 'X', url: 'https://x.com/OssVersilia' },
  ];

  const profileLinks = () => `<div class="social-links">${profiles.map(profile => `
    <a class="social-profile-link" href="${profile.url}" target="_blank" rel="me noreferrer" aria-label="Segui Osservatorio Versilia su ${profile.network}">
      <span class="social-profile-mark" aria-hidden="true">${profile.mark}</span>
      <span class="social-profile-copy"><strong>${profile.network}</strong><small>${profile.handle}</small></span>
      <b aria-hidden="true">↗</b>
    </a>`).join('')}</div>`;

  const callout = placement => `
    <section class="social-callout page-width" data-social-placement="${placement}" aria-labelledby="social-${placement}-title">
      <div><span class="overline">Segui l’Osservatorio</span><h2 id="social-${placement}-title">Dati e storie della Versilia, anche sui social.</h2></div>
      <div><p>Grafici, confronti e approfondimenti dell’Osservatorio arrivano anche sui nostri canali social. Seguici per ritrovare i dati nel momento in cui diventano notizia o aiutano a leggere il territorio.</p>${profileLinks()}</div>
    </section>`;

  function ensureFooter() {
    const footer = document.querySelector('#site-footer-mount .site-footer');
    if (!footer || footer.querySelector('[data-social-placement="footer"]')) return Boolean(footer);
    const note = footer.querySelector('.footer-note');
    if (!note) return false;
    note.insertAdjacentHTML('beforebegin', `
      <div class="footer-social" data-social-placement="footer" aria-label="Segui Osservatorio Versilia">
        <strong>Segui Osservatorio Versilia</strong>${profileLinks()}
      </div>`);
    return true;
  }

  function ensurePageCallout() {
    const page = document.body.dataset.page || '';
    if (page === 'home') {
      if (document.querySelector('[data-social-placement="home"]')) return true;
      const anchor = document.querySelector('.source-portals');
      if (!anchor) return false;
      anchor.insertAdjacentHTML('beforebegin', callout('home'));
      return true;
    }
    if (page === 'project') {
      if (document.querySelector('[data-social-placement="project"]')) return true;
      const anchor = document.querySelector('.contact-panel');
      if (!anchor) return false;
      anchor.insertAdjacentHTML('beforebegin', callout('project'));
      return true;
    }
    return true;
  }

  function enhance() {
    ensureFooter();
    ensurePageCallout();
  }

  // Il prerender può già contenere i blocchi social, ma l'app principale
  // rimonta shell e contenuto dopo il fetch dei dati. L'observer resta quindi
  // attivo e reinserisce in modo idempotente i blocchi se un rerender li rimuove.
  enhance();
  const observer = new MutationObserver(enhance);
  observer.observe(document.body, { childList: true, subtree: true });
})();
