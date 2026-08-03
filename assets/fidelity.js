(() => {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const numberFormatters = new Map();

  function parseItalianNumber(text) {
    let value = String(text || '').trim().replace(/\u00a0/g, ' ');
    value = value.replace(/[^0-9,.-]/g, '');
    if (!value) return Number.NaN;

    const commas = (value.match(/,/g) || []).length;
    const dots = (value.match(/\./g) || []).length;

    if (commas && dots) {
      if (value.lastIndexOf(',') > value.lastIndexOf('.')) {
        value = value.replace(/\./g, '').replace(',', '.');
      } else {
        value = value.replace(/,/g, '');
      }
    } else if (commas) {
      value = commas > 1
        ? value.replace(/,/g, '')
        : value.replace(',', '.');
    } else if (dots) {
      const tail = value.split('.').at(-1) || '';
      if (dots > 1 || tail.length === 3) value = value.replace(/\./g, '');
    }

    return Number(value);
  }

  function decimalsFromSample(sample) {
    const match = String(sample || '').match(/-?[0-9.]+,([0-9]+)/);
    return match ? Math.min(match[1].length, 2) : 0;
  }

  function unitSuffix(sample) {
    const text = String(sample || '').toLocaleLowerCase('it');
    if (text.includes('mln €')) return ' mln €';
    if (text.includes('€')) return ' €';
    if (text.includes('%')) return '%';
    if (text.includes(' anni')) return ' anni';
    if (text.includes(' kg')) return ' kg';
    if (text.includes(' ha')) return ' ha';
    const every = text.match(/ ogni\s+[0-9.]+/);
    return every ? every[0] : '';
  }

  function formatAxisValue(value, sample) {
    const decimals = decimalsFromSample(sample);
    const key = String(decimals);
    if (!numberFormatters.has(key)) {
      numberFormatters.set(key, new Intl.NumberFormat('it-IT', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
        useGrouping: true
      }));
    }
    return `${numberFormatters.get(key).format(value)}${unitSuffix(sample)}`;
  }

  function addYAxisLabels(chart) {
    const svg = chart.querySelector('svg');
    if (!svg || svg.querySelector('.chart-y-label')) return;

    const points = [...svg.querySelectorAll('.chart-point')].map(group => {
      const dot = group.querySelector('.chart-dot');
      const label = group.getAttribute('aria-label') || '';
      const sample = label.split(':').slice(1).join(':').trim();
      return {
        y: Number(dot?.getAttribute('cy')),
        value: parseItalianNumber(sample),
        sample
      };
    }).filter(point => Number.isFinite(point.y) && Number.isFinite(point.value));

    const grids = [...svg.querySelectorAll('.chart-grid')];
    if (points.length < 2 || !grids.length) return;

    const meanY = points.reduce((sum, point) => sum + point.y, 0) / points.length;
    const meanValue = points.reduce((sum, point) => sum + point.value, 0) / points.length;
    const covariance = points.reduce((sum, point) => sum + (point.y - meanY) * (point.value - meanValue), 0);
    const variance = points.reduce((sum, point) => sum + (point.y - meanY) ** 2, 0);
    if (!variance) return;

    const slope = covariance / variance;
    const intercept = meanValue - slope * meanY;
    const sample = points[0].sample;
    const firstGridX = Math.min(...grids.map(line => Number(line.getAttribute('x1'))).filter(Number.isFinite));
    const labelX = Number.isFinite(firstGridX) ? firstGridX - 8 : 44;

    grids.forEach(line => {
      const y = Number(line.getAttribute('y1'));
      if (!Number.isFinite(y)) return;
      const text = document.createElementNS(SVG_NS, 'text');
      text.setAttribute('class', 'chart-label chart-y-label');
      text.setAttribute('x', String(labelX));
      text.setAttribute('y', String(y + 4));
      text.setAttribute('text-anchor', 'end');
      text.textContent = formatAxisValue(intercept + slope * y, sample);
      line.parentNode.insertBefore(text, line.nextSibling);
    });
  }

  function enhanceCharts(root = document) {
    root.querySelectorAll?.('.trend-chart').forEach(addYAxisLabels);
  }

  let scheduled = false;
  function scheduleEnhancement() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      enhanceCharts();
    });
  }

  const observer = new MutationObserver(scheduleEnhancement);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scheduleEnhancement();
})();
