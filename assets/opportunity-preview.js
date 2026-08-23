(() => {
  const root = document.querySelector('[data-opportunity-preview]');
  if (!root) return;

  const townSelect = root.querySelector('[data-op-town]');
  const sourceSelect = root.querySelector('[data-op-source]');
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
    const access = accessSelect?.value || '';
    const query = normalize(searchInput?.value || '');
    let visible = 0;

    cards.forEach((card) => {
      const towns = (card.dataset.towns || '').split('|').filter(Boolean);
      const townMatch = !town || towns.includes(town);
      const sourceMatch = !source || card.dataset.source === source;
      const accessMatch = !access || card.dataset.access === access;
      const searchMatch = !query || normalize(card.dataset.search).includes(query);
      const show = townMatch && sourceMatch && accessMatch && searchMatch;
      card.hidden = !show;
      if (show) visible += 1;
    });

    if (visibleLabel) {
      visibleLabel.textContent = `${visible} ${visible === 1 ? 'opportunità visibile' : 'opportunità visibili'}`;
    }
    if (emptyState) emptyState.hidden = visible !== 0;
    updateSelectedTown(town);
  };

  townSelect?.addEventListener('change', apply);
  sourceSelect?.addEventListener('change', apply);
  accessSelect?.addEventListener('change', apply);
  searchInput?.addEventListener('input', apply);
  resetButton?.addEventListener('click', () => {
    if (townSelect) townSelect.value = '';
    if (sourceSelect) sourceSelect.value = '';
    if (accessSelect) accessSelect.value = '';
    if (searchInput) searchInput.value = '';
    apply();
    townSelect?.focus();
  });

  apply();
})();
