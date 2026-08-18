(() => {
  'use strict';

  function installFilters() {
    const table = document.querySelector('.data-status-table');
    if (!table) return;
    const theme = document.querySelector('[data-status-theme]');
    const status = document.querySelector('[data-status-filter]');
    const visible = document.querySelector('[data-status-visible]');
    const rows = [...table.querySelectorAll('tbody tr')];
    const update = () => {
      let count = 0;
      rows.forEach(row => {
        const show = (!theme?.value || row.dataset.theme === theme.value)
          && (!status?.value || row.dataset.status === status.value);
        row.hidden = !show;
        if (show) count += 1;
      });
      if (visible) visible.textContent = `${count} indicatori visibili`;
    };
    theme?.addEventListener('change', update);
    status?.addEventListener('change', update);
    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', installFilters, { once: true });
  } else {
    installFilters();
  }
})();
