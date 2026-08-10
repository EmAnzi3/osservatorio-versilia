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

  function injectStyles() {
    if (document.getElementById('ov-climate-current-grammar-style')) return;
    const style = document.createElement('style');
    style.id = 'ov-climate-current-grammar-style';
    style.textContent = `
      .ov-climate-current-legend{
        display:flex;align-items:center;gap:18px;margin:0 0 14px;padding:0 2px;
        color:var(--muted);font-size:9px;font-weight:700
      }
      .ov-climate-current-legend span{display:inline-flex;align-items:center;gap:7px}
      .ov-climate-current-legend .ov-legend-dot{width:9px;height:9px;border-radius:50%;background:var(--theme-color,#52785c)}
      .ov-climate-current-legend .ov-legend-mean{width:2px;height:16px;background:#607b88}
      .ov-climate-current-list.uses-versilia-marker{gap:9px}
      .ov-climate-current-list.uses-versilia-marker .ov-climate-current-row{min-height:45px}
      .ov-climate-current-list.uses-versilia-marker .ov-climate-current-track{
        position:relative;height:20px;border-radius:0;background:transparent;overflow:visible
      }
      .ov-climate-current-list.uses-versilia-marker .ov-climate-current-track::before{
        content:'';position:absolute;left:0;right:0;top:9px;height:2px;border-radius:999px;
        background:linear-gradient(to right,
          color-mix(in srgb,var(--theme-color,#52785c) 52%,white) 0 var(--ov-value-position),
          color-mix(in srgb,var(--ink) 8%,transparent) var(--ov-value-position) 100%)
      }
      .ov-climate-current-list.uses-versilia-marker .ov-climate-current-track::after{
        content:'';position:absolute;z-index:1;left:var(--ov-mean-position);top:1px;width:2px;height:18px;
        background:#607b88;transform:translateX(-1px)
      }
      .ov-climate-current-list.uses-versilia-marker .ov-climate-current-track>i{
        z-index:2;top:10px;width:11px;height:11px;margin:-5.5px 0 0 -5.5px;
        background:var(--theme-color,#52785c);border:2px solid var(--surface,#fffaf1);
        box-shadow:0 1px 5px color-mix(in srgb,var(--ink) 22%,transparent)
      }
    `;
    document.head.appendChild(style);
  }

  async function loadData() {
    [climate, minmax] = await Promise.all([
      fetch(new URL('data/meteo-clima-poc.json', ROOT)).then(response => response.json()),
      fetch(new URL('data/meteo-clima-minmax-poc.json', ROOT)).then(response => response.json())
    ]);
  }

  function currentKey() {
    return new URL(location.href).searchParams.get('indicatore') || '';
  }

  function syncCurrentComparisons() {
    document.querySelectorAll('.ov-climate-current-list').forEach(list => {
      const rows = [...list.querySelectorAll('.ov-climate-current-row')];
      if (!rows.length) return;
      const positions = rows.map(row => {
        const dot = row.querySelector('.ov-climate-current-track > i');
        return Number.parseFloat(dot?.style.left || '');
      });
      if (positions.some(value => !Number.isFinite(value))) return;
      const meanPosition = positions.reduce((sum, value) => sum + value, 0) / positions.length;
      const fingerprint = positions.map(value => value.toFixed(4)).join('|');
      if (list.dataset.ovVersiliaMarkers !== fingerprint) {
        list.dataset.ovVersiliaMarkers = fingerprint;
        list.classList.add('uses-versilia-marker');
        rows.forEach((row, index) => {
          const track = row.querySelector('.ov-climate-current-track');
          if (!track) return;
          track.style.setProperty('--ov-value-position', `${positions[index].toFixed(4)}%`);
          track.style.setProperty('--ov-mean-position', `${meanPosition.toFixed(4)}%`);
          track.setAttribute('aria-label', `Valore comunale; media Versilia al ${meanPosition.toFixed(1)}% della scala visualizzata`);
        });
      }
      const parent = list.parentElement;
      if (parent && !parent.querySelector(':scope > .ov-climate-current-legend')) {
        const legend = document.createElement('div');
        legend.className = 'ov-climate-current-legend';
        legend.setAttribute('aria-label', 'Legenda del confronto');
        legend.innerHTML = '<span><i class="ov-legend-dot"></i>Comune</span><span><i class="ov-legend-mean"></i>Media semplice Versilia</span>';
        parent.insertBefore(legend, list);
      }
    });
  }

  function syncTownCard() {
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

    if (card.dataset.ovClimateVersilia === fingerprint && card.textContent.toLocaleLowerCase('it').includes('rispetto alla versilia')) {
      card.hidden = false;
      return;
    }

    card.hidden = false;
    card.dataset.ovClimateVersilia = fingerprint;
    card.innerHTML = `<span class="overline">Rispetto alla Versilia</span><strong>${escapeHtml(formatSigned(delta, cfg.unit))}</strong><p>${direction} la media semplice dei sette comuni nell’anno ${cfg.latestYear}. Il confronto descrive uno scostamento, non una classifica.</p><div><span>Media semplice dei 7 comuni</span><b>${escapeHtml(formatValue(average, cfg.unit))}</b></div>`;
  }

  function sync() {
    syncCurrentComparisons();
    syncTownCard();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      scheduled = false;
      sync();
    }));
  }

  injectStyles();
  loadData().then(() => {
    schedule();
    [120, 350, 800, 1600].forEach(delay => window.setTimeout(schedule, delay));
    const targets = [document.getElementById('town-topic'), document.getElementById('compare-bars')].filter(Boolean);
    targets.forEach(target => new MutationObserver(schedule).observe(target, { childList: true, subtree: true }));
  }).catch(error => console.warn('Confronto climatico con la Versilia non disponibile', error));

  document.addEventListener('click', event => {
    if (event.target.closest('[data-metric],[data-profile-theme],[data-ov-climate-view]')) window.setTimeout(schedule, 0);
  }, true);
})();
