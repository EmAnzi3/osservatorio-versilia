(() => {
  'use strict';
  const entry = document.getElementById('climate-environment-entry');
  const app = document.getElementById('app');
  if (!entry || !app) return;

  const place = () => {
    const hero = app.querySelector('.topic-hero');
    if (!hero) return false;
    hero.insertAdjacentElement('afterend', entry);
    entry.hidden = false;
    return true;
  };

  if (place()) return;
  const observer = new MutationObserver(() => {
    if (place()) observer.disconnect();
  });
  observer.observe(app, { childList: true, subtree: true });
  window.setTimeout(() => observer.disconnect(), 10000);
})();
