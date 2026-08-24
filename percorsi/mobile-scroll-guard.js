(() => {
  'use strict';

  const BREAKPOINT = 820;
  const media = window.matchMedia(`(max-width:${BREAKPOINT}px)`);
  const originalMapFactory = L.map;
  let percorsiMap = null;

  function configureMapForViewport() {
    if (!percorsiMap) return;
    const mobile = media.matches;
    const container = percorsiMap.getContainer();

    if (mobile) {
      percorsiMap.dragging?.enable();
      percorsiMap.touchZoom?.enable();
      percorsiMap.scrollWheelZoom?.disable();
      container.dataset.mobileMapInteractive = 'true';
      delete container.dataset.mobileScrollSafe;
    } else {
      percorsiMap.dragging?.enable();
      percorsiMap.touchZoom?.enable();
      percorsiMap.scrollWheelZoom?.enable();
      delete container.dataset.mobileScrollSafe;
      delete container.dataset.mobileMapInteractive;
    }
  }

  L.map = function (...args) {
    percorsiMap = originalMapFactory.apply(this, args);
    window.__ovPercorsiMap = percorsiMap;
    configureMapForViewport();
    return percorsiMap;
  };

  if (typeof media.addEventListener === 'function') {
    media.addEventListener('change', configureMapForViewport);
  } else if (typeof media.addListener === 'function') {
    media.addListener(configureMapForViewport);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const back = document.getElementById('mapReturnToList');
    if (!back) return;
    back.addEventListener('click', () => {
      const target = document.querySelector('.resultsHead');
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();
