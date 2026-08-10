(() => {
  'use strict';
  const template = document.getElementById('climate-environment-template');
  const app = document.getElementById('app');
  if (!template || !app) return;

  const mount = () => {
    const hero = app.querySelector('.topic-hero');
    if (!hero || app.querySelector('#climate-environment-entry')) return false;
    hero.insertAdjacentElement('afterend', template.content.firstElementChild.cloneNode(true));
    return true;
  };

  mount();
  const observer = new MutationObserver(() => mount());
  observer.observe(app, { childList: true, subtree: true });
  window.setTimeout(() => observer.disconnect(), 15000);
})();
