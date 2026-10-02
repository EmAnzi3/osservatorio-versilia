(() => {
  'use strict';

  /*
   * A5 Demografia — REVIEW ADAPTER
   * EDITABILE: questo è l'unico file JS specifico del recovery.
   * Non modifica dataset, visual-grammar, ux-history o altre pagine.
   */

  const CONFIG = {
    mobilityContextMetrics: new Set([
      'internalResidentialMobility',
      'foreignResidentialMobility',
      'totalResidentialMobility'
    ]),
    townPhotos: {
      'Camaiore': 'Camaiore Countryside.jpg',
      'Forte dei Marmi': 'Forte dei Marmi - Municipio.jpg',
      'Massarosa': 'Massarosa.jpg',
      'Pietrasanta': 'Veduta di piazza duomo, Pietrasanta.jpg',
      'Seravezza': 'Seravezza-panorama.jpg',
      'Stazzema': 'Stazzema.JPG',
      'Viareggio': 'Viareggio, passeggiata a mare 2.JPG'
    }
  };

  const isTargetPage = () => (
    document.body.dataset.page === 'compare' &&
    document.body.dataset.theme === 'demografia'
  );

  const activeMetricKey = () => (
    document.querySelector('.topic-controls [data-metric].active')?.dataset.metric ||
    new URL(location.href).searchParams.get('indicatore') ||
    'population'
  );

  const commonsPhotoUrl = town => {
    const file = CONFIG.townPhotos[town];
    if (!file) return '';
    return `https://commons.wikimedia.org/wiki/Special:Redirect/file/${encodeURIComponent(file).replaceAll('%20','_')}?width=640`;
  };

  const csvIcon = `
    <span class="a5-export-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" role="img">
        <path d="M5 2.5h9l5 5V21.5H5z" fill="#2f7d57"/>
        <path d="M14 2.5v5h5" fill="none" stroke="#fff" stroke-width="1.4"/>
        <path d="M8 11.2l2.2 3.8m0-3.8L8 15m4.2-3.8h3.8M12.2 13h3.2M12.2 15h3.8" fill="none" stroke="#fff" stroke-width="1.25" stroke-linecap="round"/>
      </svg>
    </span>`;

  const pdfIcon = `
    <span class="a5-export-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" role="img">
        <path d="M5 2.5h9l5 5V21.5H5z" fill="#b84b34"/>
        <path d="M14 2.5v5h5" fill="none" stroke="#fff" stroke-width="1.4"/>
        <text x="7.2" y="15.1" fill="#fff" font-size="5.6" font-family="Arial, sans-serif" font-weight="700">PDF</text>
      </svg>
    </span>`;

  function moveDefinitionToSidebar() {
    const definition = document.getElementById('compare-definition');
    const controls = document.querySelector('main.a5-editorial-pilot .topic-controls');
    if (!definition || !controls || definition.parentElement === controls) return;
    controls.append(definition);
  }

  function decorateAndMoveActions() {
    const heading = document.querySelector('main.a5-editorial-pilot .compare-panel-heading');
    const tools = document.getElementById('compare-tools');
    if (!heading || !tools) return;

    const actions = tools.querySelector(':scope > .data-actions');
    if (actions) heading.append(actions);

    const current = heading.querySelector(':scope > .data-actions');
    if (!current) return;

    const download = current.querySelector('[data-download]');
    const print = current.querySelector('[data-print]');

    if (download && !download.querySelector('.a5-export-icon')) {
      download.insertAdjacentHTML('afterbegin', csvIcon);
    }
    if (print && !print.querySelector('.a5-export-icon')) {
      print.insertAdjacentHTML('afterbegin', pdfIcon);
    }
  }

  function updateContextualInsight() {
    const brainDrain = document.querySelector('main.a5-editorial-pilot .brain-drain');
    if (!brainDrain) return;
    brainDrain.hidden = !CONFIG.mobilityContextMetrics.has(activeMetricKey());
  }

  function updateToolLayout() {
    const tools = document.getElementById('compare-tools');
    if (!tools) return;
    tools.classList.toggle('a5-has-reading-scale', Boolean(tools.querySelector(':scope > .reading-scale')));
  }

  function currentValueMap() {
    const map = new Map();
    document.querySelectorAll('#compare-bars .bar-row').forEach(row => {
      const town = row.querySelector('.bar-town')?.textContent?.trim();
      const value = row.querySelector(':scope > strong')?.textContent?.trim();
      if (town && value) map.set(town, value);
    });
    return map;
  }

  function updateTownCards() {
    const grid = document.querySelector('#compare-territori .topic-town-card-grid');
    if (!grid) return;

    const metricKey = activeMetricKey();
    const metricLabel = document.querySelector('#compare-definition .indicator-definition h2')?.textContent?.trim() || 'Indicatore selezionato';
    const values = currentValueMap();

    [...grid.children]
      .sort((a, b) => {
        const an = a.querySelector('.topic-town-card-copy strong')?.textContent?.trim() || '';
        const bn = b.querySelector('.topic-town-card-copy strong')?.textContent?.trim() || '';
        return an.localeCompare(bn, 'it');
      })
      .forEach(card => grid.append(card));

    [...grid.children].forEach(card => {
      const copy = card.querySelector('.topic-town-card-copy');
      const name = copy?.querySelector('strong')?.textContent?.trim();
      const image = card.querySelector('.topic-town-card-media img');
      if (!name || !copy) return;

      card.href = `${location.origin}${location.pathname.replace(/\/confronta\/demografia\/$/, `/comuni/${name.toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replaceAll(' ','-')}/`)}?tema=demografia&indicatore=${encodeURIComponent(metricKey)}`;

      if (image && !image.dataset.a5PhotoApplied) {
        const photo = commonsPhotoUrl(name);
        if (photo) {
          image.dataset.a5Fallback = image.src;
          image.src = photo;
          image.alt = name;
          image.referrerPolicy = 'no-referrer';
          image.onerror = () => {
            image.onerror = null;
            image.src = image.dataset.a5Fallback || image.src;
            image.alt = '';
          };
          image.dataset.a5PhotoApplied = 'true';
        }
      }

      copy.querySelector('.a5-town-current-value')?.remove();
      const value = values.get(name);
      if (!value) return;

      const detail = document.createElement('span');
      detail.className = 'a5-town-current-value';
      detail.innerHTML = `<b>${value}</b><small>${metricLabel}</small>`;
      copy.insertBefore(detail, copy.querySelector('small'));
    });
  }

  function apply() {
    if (!isTargetPage()) return;
    document.body.classList.add('a5-demografia-recovery');
    moveDefinitionToSidebar();
    decorateAndMoveActions();
    updateContextualInsight();
    updateToolLayout();
    updateTownCards();
  }

  let scheduled = false;
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      apply();
    });
  };

  const observer = new MutationObserver(schedule);
  observer.observe(document.getElementById('app') || document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'hidden', 'aria-selected']
  });

  document.addEventListener('click', schedule, true);
  document.addEventListener('change', schedule, true);
  window.addEventListener('popstate', schedule);

  schedule();
})();
