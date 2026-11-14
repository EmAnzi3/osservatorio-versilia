// Dossier: scelta del Comune. Mostra le frasi dedicate, evidenzia il Comune nei
// grafici e nelle tabelle e tiene la scelta nell'indirizzo (?comune=...).
(function () {
  var root = document.querySelector('.dr');
  var picker = root && root.querySelector('.dr-picker');
  var select = picker && picker.querySelector('select');
  if (!select) return;
  picker.hidden = false;
  var share = picker.querySelector('.dr-share');
  var status = picker.querySelector('.dr-share-ok');

  function apply(slug, push) {
    var option = Array.prototype.find.call(select.options, function (o) { return o.value === slug; }) || select.options[0];
    select.value = option.value;
    var code = option.getAttribute('data-code') || '';
    root.classList.toggle('has-town', !!code);
    root.querySelectorAll('[data-town]').forEach(function (node) {
      var mine = node.getAttribute('data-town') === code;
      if (node.classList.contains('dr-town-text') || node.classList.contains('dr-town-card')) node.hidden = !mine;
      else node.classList.toggle('is-town', mine);
    });
    if (share) share.hidden = false;
    if (status) status.textContent = '';
    if (push) {
      var url = new URL(window.location.href);
      if (option.value) url.searchParams.set('comune', option.value); else url.searchParams.delete('comune');
      window.history.replaceState(null, '', url.toString());
    }
  }

  select.addEventListener('change', function () { apply(select.value, true); });
  if (share) share.addEventListener('click', function () {
    var done = function () { status.textContent = 'Link copiato'; };
    if (navigator.clipboard) navigator.clipboard.writeText(window.location.href).then(done, function () { status.textContent = window.location.href; });
    else status.textContent = window.location.href;
  });
  apply(new URLSearchParams(window.location.search).get('comune') || '', false);
})();
