(() => {
  const root = document.querySelector('[data-opportunity-preview]');
  if (!root) return;

  const townSelect = root.querySelector('[data-op-town]');
  const statusSelect = root.querySelector('[data-op-status]');
  const searchInput = root.querySelector('[data-op-search]');
  const resetButton = root.querySelector('[data-op-reset]');
  const visibleLabel = root.querySelector('[data-op-visible]');
  const contextLabel = root.querySelector('[data-op-context]');
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
    const status = statusSelect?.value || '';
    const query = normalize(searchInput?.value || '');
    let visible = 0;

    cards.forEach((card) => {
      const towns = (card.dataset.towns || '').split('|').filter(Boolean);
      const statusMatch = !status || card.dataset.status === status;
      const townMatch = !town || towns.includes(town);
      const searchMatch = !query || normalize(card.dataset.search).includes(query);
      const show = statusMatch && townMatch && searchMatch;
      card.hidden = !show;
      if (show) visible += 1;
    });

    if (visibleLabel) {
      visibleLabel.textContent = `${visible} ${visible === 1 ? 'opportunità visibile' : 'opportunità visibili'}`;
    }
    if (contextLabel) {
      const selectedTown = townSelect?.selectedOptions?.[0]?.textContent || '';
      const selectedStatus = statusSelect?.selectedOptions?.[0]?.textContent || '';
      const parts = [];
      if (town) parts.push(selectedTown);
      if (status) parts.push(selectedStatus);
      if (query) parts.push(`ricerca “${searchInput.value.trim()}”`);
      contextLabel.textContent = parts.length ? parts.join(' · ') : 'Tutta la Versilia · tutti gli stati';
    }
    if (emptyState) emptyState.hidden = visible !== 0;
    updateSelectedTown(town);
  };

  townSelect?.addEventListener('change', apply);
  statusSelect?.addEventListener('change', apply);
  searchInput?.addEventListener('input', apply);
  resetButton?.addEventListener('click', () => {
    if (townSelect) townSelect.value = '';
    if (statusSelect) statusSelect.value = '';
    if (searchInput) searchInput.value = '';
    apply();
    townSelect?.focus();
  });

  apply();
})();
