(() => {
  'use strict';

  const loader = document.currentScript;
  const ROOT = new URL('../', loader?.src || location.href);
  const CONFIG = {
    climateTemperatureTrend50y: { seriesKey: 'temperature', latestYear: 2025, unit: 'celsius', dataset: 'climate' },
    climatePrecipitationTrend50y: { seriesKey: 'precipitation', latestYear: 2025, unit: 'mm', dataset: 'climate' },
    climateTminTrend: { seriesKey: 'tmin', latestYear: 2015, unit: 'celsius', dataset: 'minmax' },
    climateTmaxTrend: { seriesKey: 'tmax', latestYear: 2015, unit: 'celsius', dataset: 'minmax' }
  };
  const fmt2 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmt0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 });
  const escapeHtml = value => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const slug = value => String(value || '').toLocaleLowerCase('it').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const formatValue = (value, unit) => unit === 'mm'
    ? `${fmt0.format(Number(value))} mm`
    : `${fmt2.format(Number(value))} °C`;
  const formatSigned = (value, unit) => `${Number(value) > 0 ? '+' : ''}${formatValue(value, unit)}`;

  let climate = null;
  let minmax = null;
  let scheduled = false;

  async function loadData() {
    [climate, minmax] = await Promise.all([
      fetch(new URL('data/meteo-clima-poc.json', ROOT)).then(response => response.json()),
      fetch(new URL('data/meteo-clima-minmax-poc.json', ROOT)).then(response => response.json())
    ]);
  }

  function currentKey() {
    return new URL(location.href).searchParams.get('indicatore') || '';
  }

  function sync() {
    if (document.body.dataset.page !== 'town') return;
    const key = currentKey();
    const cfg = CONFIG[key];
    if (!cfg || !climate || !minmax) return;

    const card = document.querySelector('main.town-profile .versilia-position');
    if (!card) return;
    const source = cfg.dataset === 'minmax' ? minmax : climate;
    const rows = Object.entries(source.municipalities).map(([town, series]) => {
      const values = series[cfg.seriesKey] || [];
      let index = series.years.findIndex(year => Number(year) === cfg.latestYear);
      if (index < 0) index = values.length - 1;
      return { town, townSlug: slug(town), value: Number(values[index]) };
    }).filter(row => Number.isFinite(row.value));
    if (!rows.length) return;

    const townSlug = document.body.dataset.town || '';
    const row = rows.find(item => item.townSlug === townSlug);
    if (!row) return;
    const average = rows.reduce((sum, item) => sum + item.value, 0) / rows.length;
    const delta = row.value - average;
    const direction = delta > 0 ? 'sopra' : delta < 0 ? 'sotto' : 'in linea con';
    const fingerprint = `${key}|${townSlug}|${cfg.latestYear}|${delta.toFixed(6)}|${average.toFixed(6)}`;

    if (card.dataset.ovClimateVersilia === fingerprint && card.textContent.includes('Rispetto alla Versilia')) {
      card.hidden = false;
      return;
    }

    card.hidden = false;
    card.dataset.ovClimateVersilia = fingerprint;
    card.innerHTML = `<span class="overline">Rispetto alla Versilia</span><strong>${escapeHtml(formatSigned(delta, cfg.unit))}</strong><p>${direction} la media semplice dei sette comuni nell’anno ${cfg.latestYear}. Il confronto descrive uno scostamento, non una classifica.</p><div><span>Media semplice dei 7 comuni</span><b>${escapeHtml(formatValue(average, cfg.unit))}</b></div>`;
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      scheduled = false;
      sync();
    }));
  }

  loadData().then(() => {
    schedule();
    [120, 350, 800, 1600].forEach(delay => window.setTimeout(schedule, delay));
    const target = document.getElementById('town-topic');
    if (target) new MutationObserver(schedule).observe(target, { childList: true, subtree: true });
  }).catch(error => console.warn('Confronto climatico con la Versilia non disponibile', error));

  document.addEventListener('click', event => {
    if (event.target.closest('[data-metric],[data-profile-theme]')) window.setTimeout(schedule, 0);
  }, true);
})();
