(() => {
  'use strict';

  const params = new URLSearchParams(location.search);
  const municipality = params.get('comune') || '';
  const mode = params.get('tipo') || '';
  const allowedModes = new Set(['trekking', 'cammino', 'bicycle', 'mtb']);
  const requestedMode = allowedModes.has(mode) ? mode : '';

  if (!municipality && !requestedMode) return;

  let attempts = 0;
  const apply = () => {
    attempts += 1;
    let municipalityReady = !municipality;
    let modeReady = !requestedMode;

    const select = document.getElementById('municipality');
    if (municipality && select && [...select.options].some(option => option.value === municipality)) {
      municipalityReady = true;
      if (select.value !== municipality) {
        select.value = municipality;
        select.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    if (requestedMode) {
      const chip = document.querySelector(`.chip[data-mode="${requestedMode}"]`);
      if (chip) {
        modeReady = true;
        if (!chip.classList.contains('active')) chip.click();
      }
    }

    if ((municipalityReady && modeReady) || attempts >= 80) {
      clearInterval(timer);
    }
  };

  const timer = setInterval(apply, 100);
  apply();
})();
