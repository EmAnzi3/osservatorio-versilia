(() => {
  'use strict';

  const script = document.currentScript;
  const ROOT = new URL('../', script?.src || location.href);
  const history = window.OVUXHistory;
  if (!history) throw new Error('OVUXHistory non disponibile: le pagine editoriali devono usare il toolkit grafico canonico.');

  const slug = value => String(value || '').toLocaleLowerCase('it').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  function exactHistory(metric, selectedSlug = '') {
    const series = history.comparableSeries(metric);
    const host = document.createElement('div');
    host.className = 'editorial-exact-history';
    host.dataset.ovCanonicalChart = 'history';
    host.innerHTML = history.historicalChartMarkup(metric, series, selectedSlug);
    history.wireHistorySelection(host, selectedSlug, false);
    return host;
  }

  function exactComparison(metric, selectedSlug = '') {
    const host = document.createElement('div');
    host.className = 'editorial-exact-comparison';
    host.dataset.ovCanonicalChart = 'comparison';
    host.innerHTML = history.comparisonBarsMarkup(metric, selectedSlug);
    return host;
  }

  async function upgradeReading() {
    if (document.body.dataset.reading !== 'una-versilia-che-cambia') return false;
    const populationChapter = document.querySelector('[data-story-chapter="population"]');
    const agingChapter = document.querySelector('[data-story-chapter="aging"]');
    if (!populationChapter || !agingChapter) return false;
    if (document.querySelector('[data-editorial-canonical-ready="reading"]')) return true;

    const response = await fetch(new URL('data/site-data.json', ROOT));
    if (!response.ok) throw new Error(`site-data: ${response.status}`);
    const data = await response.json();
    const population = data.metrics.population;
    const change = data.metrics.populationChange;
    const aging = data.metrics.oldAgeIndex;

    const rows = population.rows.filter(row => row?.series?.years?.length >= 2);
    const years = rows[0].series.years;
    const totals = years.map((year, index) => rows.reduce((sum, row) => sum + Number(row.series.values[index]), 0));
    const totalMetric = {
      meta: { ...population.meta, key: 'populationTotalReading', label: 'Residenti complessivi dei sette Comuni', shortLabel: 'Residenti complessivi', unit: 'number' },
      rows: [{ town: 'Versilia', slug: 'versilia', series: { years, values: totals } }]
    };

    const oldPopulation = populationChapter.querySelector('.story-canonical-chart');
    if (oldPopulation) {
      const oldA11y = oldPopulation.nextElementSibling?.classList?.contains('chart-a11y-table') ? oldPopulation.nextElementSibling : null;
      const exact = exactHistory(totalMetric, 'versilia');
      oldPopulation.replaceWith(exact);
      oldA11y?.remove();
    }

    const oldChange = populationChapter.querySelector('.story-change-bars');
    if (oldChange) oldChange.replaceWith(exactComparison(change));

    const oldAging = agingChapter.querySelector('.story-aging-explorer');
    if (oldAging) oldAging.replaceWith(exactHistory(aging));

    const oldAgingComparison = agingChapter.querySelector('.story-canonical-bars');
    if (oldAgingComparison) oldAgingComparison.replaceWith(exactComparison(aging));

    const marker = document.createElement('i');
    marker.hidden = true;
    marker.dataset.editorialCanonicalReady = 'reading';
    document.getElementById('reading-app')?.append(marker);
    return true;
  }

  const CLIMATE = {
    temperature: { dataset: 'climate', field: 'temperature', label: 'Temperatura media annua', unitLabel: '°C', displayUnit: 'index' },
    tmin: { dataset: 'minmax', field: 'tmin', label: 'Temperatura minima media annua', unitLabel: '°C', displayUnit: 'index' },
    tmax: { dataset: 'minmax', field: 'tmax', label: 'Temperatura massima media annua', unitLabel: '°C', displayUnit: 'index' },
    precipitation: { dataset: 'climate', field: 'precipitation', label: 'Precipitazioni annue', unitLabel: 'mm', displayUnit: 'number' }
  };
  let climateData = null;
  let climateObserver = null;
  let climateBusy = false;

  async function loadClimate() {
    if (climateData) return climateData;
    const [climate, minmax] = await Promise.all([
      fetch(new URL('data/meteo-clima-poc.json', ROOT)).then(r => { if (!r.ok) throw new Error(`climate: ${r.status}`); return r.json(); }),
      fetch(new URL('data/meteo-clima-minmax-poc.json', ROOT)).then(r => { if (!r.ok) throw new Error(`minmax: ${r.status}`); return r.json(); })
    ]);
    climateData = { climate, minmax };
    return climateData;
  }

  async function renderClimateExact() {
    if (!document.getElementById('climate-workspace') || climateBusy) return false;
    const chartHost = document.getElementById('climate-chart');
    const townSelect = document.getElementById('climate-town');
    const active = document.querySelector('[data-climate-metric].active');
    if (!chartHost || !townSelect || !active?.dataset?.climateMetric) return false;
    climateBusy = true;
    try {
      const datasets = await loadClimate();
      const key = active.dataset.climateMetric;
      const def = CLIMATE[key];
      const source = datasets[def.dataset];
      const towns = Object.keys(source.municipalities).sort((a, b) => a.localeCompare(b, 'it'));
      const rows = towns.map(town => {
        const entry = source.municipalities[town];
        const allYears = entry.years.map(Number);
        const start = allYears.findIndex(year => year >= 1975);
        return {
          town,
          slug: slug(town),
          series: { years: allYears.slice(start), values: entry[def.field].slice(start).map(Number) }
        };
      });
      const metric = {
        meta: { key: `climate-${key}`, label: def.label, shortLabel: def.label, unit: def.displayUnit, source: source.methodology?.source || 'Dati climatici Osservatorio Versilia' },
        rows
      };
      const selectedSlug = slug(townSelect.value);
      const exact = exactHistory(metric, selectedSlug);
      exact.dataset.climateMetricExact = key;
      const unit = document.createElement('p');
      unit.className = 'climate-canonical-unit';
      unit.textContent = `Unità: ${def.unitLabel} · stessa scala, legenda e tooltip del grafico storico canonico del sito`;
      exact.prepend(unit);
      if (climateObserver) climateObserver.disconnect();
      chartHost.replaceChildren(exact);
      if (climateObserver) climateObserver.observe(chartHost, { childList: true, subtree: true });
      document.getElementById('climate-workspace').dataset.editorialCanonicalReady = 'climate';
      return true;
    } finally {
      climateBusy = false;
    }
  }

  function installClimate() {
    const chartHost = document.getElementById('climate-chart');
    if (!chartHost) return false;
    climateObserver = new MutationObserver(() => {
      const exact = chartHost.querySelector('[data-climate-metric-exact]');
      const active = document.querySelector('[data-climate-metric].active')?.dataset?.climateMetric;
      if (!exact || exact.dataset.climateMetricExact !== active) queueMicrotask(() => renderClimateExact().catch(console.error));
    });
    climateObserver.observe(chartHost, { childList: true, subtree: true });
    document.getElementById('climate-town')?.addEventListener('change', () => setTimeout(() => renderClimateExact().catch(console.error), 0));
    document.querySelectorAll('[data-climate-metric]').forEach(button => button.addEventListener('click', () => setTimeout(() => renderClimateExact().catch(console.error), 0)));
    renderClimateExact().catch(console.error);
    return true;
  }

  function start() {
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      const readingDone = document.body.dataset.reading === 'una-versilia-che-cambia' ? upgradeReading().catch(console.error) : true;
      const climateDone = document.getElementById('climate-workspace') ? installClimate() : true;
      if ((readingDone === true || document.querySelector('[data-editorial-canonical-ready="reading"]')) && climateDone === true || attempts > 80) clearInterval(timer);
    }, 100);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
