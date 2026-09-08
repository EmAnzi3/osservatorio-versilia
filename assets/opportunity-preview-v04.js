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
  const relevanceSelect = root.querySelector('[data-op-relevance]');
  const accessSelect = root.querySelector('[data-op-access]');
  const newSelect = root.querySelector('[data-op-new]');
  const sortSelect = root.querySelector('[data-op-sort]');
  const searchInput = root.querySelector('[data-op-search]');
  const resetButton = root.querySelector('[data-op-reset]');
  const visibleLabel = root.querySelector('[data-op-visible]');
  const cards = Array.from(root.querySelectorAll('[data-opportunity-card]'));
  const lists = Array.from(root.querySelectorAll('[data-op-list]'));
  const originalOrder = new Map(cards.map((card, index) => [card, index]));

  cards.forEach((card) => {
    const statuses = new Set(Array.from(card.querySelectorAll('[data-town-status]')).map((chip) => chip.dataset.townStatus));
    if (statuses.has('eligible') && statuses.has('conditional')) {
      card.dataset.access = 'specific_requirement';
      const badge = card.querySelector('.op-access');
      if (badge && card.dataset.relevance !== 'partner') {
        badge.classList.remove('op-access-direct');
        badge.classList.add('op-access-specific');
        badge.textContent = 'Accesso differenziato';
      }
      if (!card.querySelector('.op-condition')) {
        const townBlock = card.querySelector('.op-town-block');
        if (townBlock) {
          const note = document.createElement('div');
          note.className = 'op-condition';
          note.innerHTML = '<strong>Requisiti diversi per Comune</strong><span>L’ammissibilità o il ruolo cambiano sul territorio: consulta i dettagli dei singoli Comuni.</span>';
          townBlock.before(note);
        }
      }
    }
  });

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

  const orderCards = (mode) => {
    lists.forEach((list) => {
      const listCards = cards.filter((card) => card.parentElement === list);
      const ordered = [...listCards].sort((a, b) => {
        if (mode === 'recent') {
          const aSeen = String(a.dataset.firstSeen || '');
          const bSeen = String(b.dataset.firstSeen || '');
          const bySeen = bSeen.localeCompare(aSeen);
          if (bySeen) return bySeen;
        }
        return (originalOrder.get(a) || 0) - (originalOrder.get(b) || 0);
      });
      ordered.forEach((card) => list.appendChild(card));
    });
  };

  const apply = () => {
    const town = townSelect?.value || '';
    const source = sourceSelect?.value || '';
    const lifecycle = lifecycleSelect?.value || '';
    const relevance = relevanceSelect?.value || '';
    const access = accessSelect?.value || '';
    const novelty = newSelect?.value || '';
    const sortMode = sortSelect?.value || 'deadline';
    const query = normalize(searchInput?.value || '');
    let visible = 0;
    let municipalVisible = 0;
    let partnerVisible = 0;

    orderCards(sortMode);
    cards.forEach((card) => {
      const towns = (card.dataset.towns || '').split('|').filter(Boolean);
      const cardRelevance = card.dataset.relevance || 'direct_conditional';
      const isPartner = cardRelevance === 'partner';
      const relevanceMatch = !relevance || (relevance === 'partner' ? isPartner : !isPartner);
      const townMatch = !town || towns.includes(town);
      const sourceMatch = !source || card.dataset.source === source;
      const lifecycleMatch = !lifecycle || card.dataset.lifecycle === lifecycle;
      const accessMatch = !access || card.dataset.access === access;
      const noveltyMatch = novelty !== 'new' || card.dataset.new === 'true';
      const searchMatch = !query || normalize(card.dataset.search).includes(query);
      const show = relevanceMatch && townMatch && sourceMatch && lifecycleMatch && accessMatch && noveltyMatch && searchMatch;
      card.hidden = !show;
      if (show) {
        visible += 1;
        if (isPartner) partnerVisible += 1;
        else municipalVisible += 1;
      }
    });

    if (visibleLabel) {
      const base = `${visible} ${visible === 1 ? 'scheda visibile' : 'schede visibili'}`;
      visibleLabel.textContent = `${base} · ${municipalVisible} comunali · ${partnerVisible} partnership`;
    }
    root.querySelectorAll('[data-op-empty-for]').forEach((empty) => {
      const kind = empty.dataset.opEmptyFor;
      const count = kind === 'partner' ? partnerVisible : municipalVisible;
      empty.hidden = count !== 0;
    });
    updateSelectedTown(town);
  };

  [townSelect, sourceSelect, lifecycleSelect, relevanceSelect, accessSelect, newSelect, sortSelect].forEach((control) => control?.addEventListener('change', apply));
  searchInput?.addEventListener('input', apply);
  resetButton?.addEventListener('click', () => {
    if (townSelect) townSelect.value = '';
    if (sourceSelect) sourceSelect.value = '';
    if (lifecycleSelect) lifecycleSelect.value = '';
    if (relevanceSelect) relevanceSelect.value = '';
    if (accessSelect) accessSelect.value = '';
    if (newSelect) newSelect.value = '';
    if (sortSelect) sortSelect.value = 'deadline';
    if (searchInput) searchInput.value = '';
    apply();
    townSelect?.focus();
  });

  apply();
})();
