/* Versilia, la mascotte dell'Osservatorio: invita a fare una domanda a Chiedi.
   Discreta: compare in basso a destra, il fumetto si apre da solo una sola volta
   per visita (solo su schermi larghi), si chiude e si può nascondere del tutto. */
(() => {
  'use strict';

  if (document.querySelector('meta[name="robots"][content*="noindex" i]')) return;
  const script = document.currentScript;
  if (!script || !script.src) return;
  const root = new URL('../', script.src);
  const ask = new URL('chiedi/', root);
  if (location.pathname === ask.pathname || location.pathname === `${ask.pathname}index.html`) return;

  const HIDDEN = 'ov-mascotte-nascosta';
  const GREETED = 'ov-mascotte-salutato';
  const read = (store, key) => { try { return window[store].getItem(key); } catch { return null; } };
  const write = (store, key, value) => { try { window[store].setItem(key, value); } catch { /* storage non disponibile */ } };
  if (read('localStorage', HIDDEN) === '1') return;

  const EXAMPLES = ['Quanti abitanti ha Viareggio?', 'Quale Comune ha il reddito più alto?'];
  const image = name => new URL(`assets/mascotte/${name}`, root).href;
  const el = (tag, attrs = {}, text) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  };

  function mount() {
    if (document.getElementById('versilia-mascot')) return;
    const box = el('aside', { id: 'versilia-mascot', class: 'vm', 'aria-label': 'Versilia, la guida dell’Osservatorio' });

    const bubble = el('div', { id: 'vm-bubble', class: 'vm-bubble', role: 'dialog', 'aria-labelledby': 'vm-title' });
    bubble.hidden = true;
    const close = el('button', { type: 'button', class: 'vm-close', 'aria-label': 'Chiudi il fumetto' }, '×');
    const title = el('p', { id: 'vm-title', class: 'vm-title' }, 'Ciao, sono Versilia!');
    const text = el('p', { class: 'vm-text' }, 'Cosa vuoi sapere sul nostro territorio?');
    const form = el('form', { class: 'vm-form', action: ask.href, method: 'get', role: 'search' });
    const label = el('label', { class: 'vm-sr', for: 'vm-input' }, 'La tua domanda');
    const input = el('input', { id: 'vm-input', name: 'q', type: 'search', maxlength: '200', autocomplete: 'off', placeholder: 'Es.: reddito a Camaiore' });
    const send = el('button', { type: 'submit', class: 'vm-send' }, 'Chiedi');
    form.append(label, input, send);
    form.addEventListener('submit', event => { if (!input.value.trim()) { event.preventDefault(); input.focus(); } });
    const examples = el('div', { class: 'vm-examples', 'aria-label': 'Domande di esempio' });
    for (const question of EXAMPLES) {
      const link = el('a', { class: 'vm-example', href: `${ask.href}?q=${encodeURIComponent(question)}` }, question);
      examples.append(link);
    }
    const hide = el('button', { type: 'button', class: 'vm-hide' }, 'Non mostrare più');
    bubble.append(close, title, text, form, examples, hide);

    const avatar = el('button', { type: 'button', class: 'vm-avatar', 'aria-expanded': 'false', 'aria-controls': 'vm-bubble', 'aria-label': 'Fai una domanda a Versilia' });
    const img = el('img', { src: image('versilia-160.webp'), srcset: `${image('versilia-160.webp')} 1x, ${image('versilia-320.webp')} 2x`, alt: '', width: '80', height: '88', decoding: 'async' });
    avatar.append(img);
    box.append(bubble, avatar);
    document.body.append(box);

    const open = (focus = true) => {
      bubble.hidden = false;
      avatar.setAttribute('aria-expanded', 'true');
      box.classList.add('vm-open');
      write('sessionStorage', GREETED, '1');
      if (focus) input.focus({ preventScroll: true });
    };
    const shut = (focus = true) => {
      bubble.hidden = true;
      avatar.setAttribute('aria-expanded', 'false');
      box.classList.remove('vm-open');
      write('sessionStorage', GREETED, '1');
      if (focus) avatar.focus({ preventScroll: true });
    };
    avatar.addEventListener('click', () => (bubble.hidden ? open() : shut()));
    close.addEventListener('click', () => shut());
    bubble.addEventListener('keydown', event => { if (event.key === 'Escape') { event.stopPropagation(); shut(); } });
    hide.addEventListener('click', () => { write('localStorage', HIDDEN, '1'); box.remove(); });

    // Saluto automatico: una volta per visita, solo su schermi larghi, senza rubare il fuoco.
    const wide = window.matchMedia('(min-width: 720px)').matches;
    if (wide && read('sessionStorage', GREETED) !== '1') {
      window.setTimeout(() => { if (bubble.hidden && document.body.contains(box)) open(false); }, 2500);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });
  else mount();
})();
