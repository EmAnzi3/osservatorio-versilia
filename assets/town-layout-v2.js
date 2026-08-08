(() => {
  'use strict';

  const ENABLE_TOWN_LAYOUT_V2 = true;
  if (!ENABLE_TOWN_LAYOUT_V2) return;

  let scheduled = false;

  function themeLabel(root) {
    const overline = root.querySelector('.town-topic-heading .overline')?.textContent?.trim() || '';
    return overline.replace(/^\s*\d+\s*·\s*/, '').trim() || 'Tema';
  }

  function townName() {
    return document.querySelector('.town-identity h1')?.textContent?.trim() || 'Comune';
  }

  function buildPicker(root, controls) {
    const active = controls.querySelector('[data-metric].active, [data-metric][aria-selected="true"]');
    if (!active) return null;
    const activeGroup = active.closest('.metric-group');
    const activeSection = activeGroup?.querySelector('.metric-group-heading strong')?.textContent?.trim() || '';
    const activeMetric = active.dataset.metric || '';

    const details = document.createElement('details');
    details.className = 'town-v2-picker';
    details.dataset.activeMetric = activeMetric;
    details.innerHTML = `
      <summary>
        <span class="town-v2-picker-current">
          <small>Indicatore selezionato</small>
          <strong>${active.textContent.trim()}</strong>
          <em>${activeSection}</em>
        </span>
        <span class="town-v2-picker-action">Cambia indicatore <i aria-hidden="true">⌄</i></span>
      </summary>
      <div class="town-v2-picker-panel" role="group" aria-label="Scegli un indicatore"></div>`;

    const panel = details.querySelector('.town-v2-picker-panel');
    controls.querySelectorAll(':scope > .metric-group').forEach(group => {
      const sectionName = group.querySelector('.metric-group-heading strong')?.textContent?.trim() || '';
      const sectionDescription = group.querySelector('.metric-group-heading > span')?.textContent?.trim() || '';
      const section = document.createElement('section');
      section.className = 'town-v2-picker-group';
      section.innerHTML = `<div><strong>${sectionName}</strong>${sectionDescription ? `<small>${sectionDescription}</small>` : ''}</div><div class="town-v2-picker-buttons"></div>`;
      const buttons = section.querySelector('.town-v2-picker-buttons');
      group.querySelectorAll('.metric-group-buttons [data-metric]').forEach(source => {
        const button = document.createElement('button');
        button.type = 'button';
        button.dataset.townV2Metric = source.dataset.metric;
        button.className = source.dataset.metric === activeMetric ? 'active' : '';
        button.textContent = source.textContent.trim();
        button.addEventListener('click', () => {
          details.removeAttribute('open');
          source.click();
        });
        buttons.appendChild(button);
      });
      panel.appendChild(section);
    });

    return details;
  }

  function enhanceTownTopic() {
    scheduled = false;
    const root = document.getElementById('town-topic');
    if (!root || !root.querySelector('.town-topic-heading')) return;

    const controls = root.querySelector(':scope > .metric-switch.metric-catalog');
    const active = controls?.querySelector('[data-metric].active, [data-metric][aria-selected="true"]');
    const activeMetric = active?.dataset.metric || '';
    if (!controls || !activeMetric) return;

    root.classList.add('town-layout-v2');
    controls.classList.add('town-v2-source-controls');
    controls.setAttribute('aria-hidden', 'true');

    let picker = root.querySelector(':scope > .town-v2-picker');
    if (!picker || picker.dataset.activeMetric !== activeMetric) {
      picker?.remove();
      picker = buildPicker(root, controls);
      if (picker) controls.insertAdjacentElement('afterend', picker);
    }

    const allIndicators = root.querySelector(':scope > .all-indicators');
    if (allIndicators) {
      allIndicators.classList.add('town-v2-overview');
      const heading = allIndicators.querySelector('.section-heading h3');
      const copy = allIndicators.querySelector('.section-heading > p');
      const wantedHeading = `Quadro della ${themeLabel(root).toLocaleLowerCase('it')} a ${townName()}`;
      if (heading && heading.textContent !== wantedHeading) heading.textContent = wantedHeading;
      if (copy) copy.textContent = 'Panoramica degli indicatori del tema. Seleziona una carta per approfondire il dato.';
    }
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(enhanceTownTopic);
  }

  const app = document.getElementById('app');
  if (!app) return;
  new MutationObserver(schedule).observe(app, { childList: true, subtree: true });
  schedule();
})();
