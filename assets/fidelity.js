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

  function axisFormat(sample) {
    const text = String(sample || '').toLocaleLowerCase('it');
    const decimalMatch = text.match(/-?[0-9.]+,([0-9]+)/);
    let decimals = decimalMatch ? Math.min(decimalMatch[1].length, 2) : 0;
    let suffix = '';

    /* The original ChatGPT Sites chart deliberately abbreviates these
       long units on the ordinate and shows only one decimal place. */
    if (text.includes(' anni') || text.includes(' ogni ')) {
      decimals = 1;
    } else if (text.includes('mln €')) {
      decimals = 1;
      suffix = ' mln €';
    } else if (text.includes('€')) {
      decimals = 0;
      suffix = ' €';
    } else if (text.includes('%')) {
      decimals = 1;
      suffix = '%';
    } else if (text.includes(' kg')) {
      decimals = 0;
      suffix = ' kg';
    } else if (text.includes(' ha')) {
      decimals = 2;
      suffix = ' ha';
    }

    return { decimals, suffix };
  }

  function formatAxisValue(value, sample) {
    const { decimals, suffix } = axisFormat(sample);
    const key = String(decimals);
    if (!numberFormatters.has(key)) {
      numberFormatters.set(key, new Intl.NumberFormat('it-IT', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
        useGrouping: 'always'
      }));
    }
    return `${numberFormatters.get(key).format(value)}${suffix}`;
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

    /* Recover the exact linear scale already used to draw the existing SVG.
       This keeps labels aligned even though the GitHub reconstruction uses
       slightly different chart margins from the original React component. */
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

  function stickyOffset(includeThemeNavigation = false) {
    const headerHeight = document.getElementById('site-header-mount')?.getBoundingClientRect().height || 70;
    const themeHeight = includeThemeNavigation
      ? document.querySelector('.town-profile .town-context-nav')?.getBoundingClientRect().height || 0
      : 0;
    return headerHeight + themeHeight + 12;
  }

  function scrollToUpdatedData(target, includeThemeNavigation = false) {
    if (!target) return;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const top = target.getBoundingClientRect().top + window.scrollY - stickyOffset(includeThemeNavigation);
    window.scrollTo({
      top: Math.max(0, top),
      behavior: reduceMotion ? 'auto' : 'smooth'
    });
  }

  function installMobileThemeJump() {
    document.addEventListener('click', event => {
      const homeTheme = event.target.closest?.('.theme-card');
      if (homeTheme) {
        requestAnimationFrame(() => requestAnimationFrame(() => {
          scrollToUpdatedData(document.getElementById('home-explorer'));
        }));
        return;
      }

      const townTheme = event.target.closest?.('[data-profile-theme]');
      if (townTheme) {
        requestAnimationFrame(() => requestAnimationFrame(() => {
          scrollToUpdatedData(document.getElementById('town-topic'), true);
        }));
      }
    });
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
  installMobileThemeJump();
  scheduleEnhancement();
})();
