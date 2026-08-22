(() => {
  const root = document.querySelector('[data-opportunity-preview]');
  if (!root) return;

  root.querySelectorAll('.op-source-favicon').forEach((img) => {
    const hideBroken = () => img.remove();
    if (img.complete && img.naturalWidth === 0) hideBroken();
    else img.addEventListener('error', hideBroken, { once: true });
  });

  const townSelect = root.querySelector('[data-op-town]');
  const sourceSelect = root.querySelector('[data-op-source]');
  const lifecycleSelect = root.querySelector('[data-op-lifecycle]');
  const accessSelect = root.querySelector('[data-op-access]');
  const searchInput = root.querySelector('[data-op-search]');
  const resetButton = root.querySelector('[data-op-reset]');
  const visibleLabel = root.querySelector('[data-op-visible]');
  const emptyState = root.querySelector('[data-op-empty]');
  const cards = Array.from(root.querySelectorAll('[data-opportunity-card]'));

  const normalize = (value) => String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

  const updateSelectedTown = (town) => {
    root.querySelectorAll('[data-town-chip]').forEach((chip) => {
      chip.classList.toggle('is-selected', Boolean(town) && chip.dataset.townChip === town);
    });
  };

  const apply = () => {
    const town = townSelect?.value || '';
    const source = sourceSelect?.value || '';
    const lifecycle = lifecycleSelect?.value || '';
    const access = accessSelect?.value || '';
    const query = normalize(searchInput?.value || '');
    let visible = 0;

    cards.forEach((card) => {
      const towns = (card.dataset.towns || '').split('|').filter(Boolean);
      const townMatch = !town || towns.includes(town);
      const sourceMatch = !source || card.dataset.source === source;
      const lifecycleMatch = !lifecycle || card.dataset.lifecycle === lifecycle;
      const accessMatch = !access || card.dataset.access === access;
      const searchMatch = !query || normalize(card.dataset.search).includes(query);
      const show = townMatch && sourceMatch && lifecycleMatch && accessMatch && searchMatch;
      card.hidden = !show;
      if (show) visible += 1;
    });

    if (visibleLabel) {
      visibleLabel.textContent = `${visible} ${visible === 1 ? 'opportunità visibile' : 'opportunità visibili'}`;
    }
    if (emptyState) emptyState.hidden = visible !== 0;
    updateSelectedTown(town);
  };

  [townSelect, sourceSelect, lifecycleSelect, accessSelect].forEach((control) => control?.addEventListener('change', apply));
  searchInput?.addEventListener('input', apply);
  resetButton?.addEventListener('click', () => {
    if (townSelect) townSelect.value = '';
    if (sourceSelect) sourceSelect.value = '';
    if (lifecycleSelect) lifecycleSelect.value = '';
    if (accessSelect) accessSelect.value = '';
    if (searchInput) searchInput.value = '';
    apply();
    townSelect?.focus();
  });

  apply();
})();
