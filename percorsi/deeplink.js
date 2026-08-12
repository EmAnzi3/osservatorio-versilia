(() => {
  'use strict';
  const municipality = new URLSearchParams(location.search).get('comune');
  if (!municipality) return;
  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    const select = document.getElementById('municipality');
    if (select && [...select.options].some(option => option.value === municipality)) {
      select.value = municipality;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      clearInterval(timer);
    } else if (attempts >= 80) {
      clearInterval(timer);
    }
  }, 100);
})();
