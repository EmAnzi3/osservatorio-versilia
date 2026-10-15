// Keep the focused reader heading visible below the public sticky header.
document.getElementById('a7-guided').addEventListener('focusin', event => {
  const target = event.target;
  if (!['risposta', 'titolo-chiarimento'].includes(target.id)) return;
  requestAnimationFrame(() => {
    if (document.activeElement === target && !target.closest('[hidden]')) {
      target.scrollIntoView({block:'start', behavior:'instant'});
    }
  });
});

// All imports stay in this immutable release directory. An unavailable module
// must not fall back to code from a different deployment or expose old results.
try {
  await import('./preview.mjs');
} catch (error) {
  document.getElementById('stato').textContent = 'Evidenze non disponibili o non verificabili. Nessun risultato mostrato. Ricarica la pagina.';
  for (const id of ['dossier','domanda','mostra','domanda-testo','verifica-testo']) document.getElementById(id).disabled = true;
  document.getElementById('risposta').hidden = true;
  document.getElementById('risposta').replaceChildren();
}
