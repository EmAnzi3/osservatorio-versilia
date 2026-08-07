(() => {
  'use strict';

  const number0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 });
  const number1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number2 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 2 });
  const esc = value => String(value ?? '').replace(/[&<>"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
  const slug = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  function dataUrl() {
    const path = location.pathname;
    const marker = path.match(/^(.*?)(?:comuni|confronta)\//);
    const prefix = marker ? marker[1] : path.replace(/[^/]*$/, '');
    return `${prefix}data/site-data.json`;
  }

  async function loadData() {
    const response = await fetch(dataUrl(), { cache: 'no-store' });
    if (!response.ok) throw new Error(`site-data.json HTTP ${response.status}`);
    return response.json();
  }

  function topBars(items, measure) {
    const key = measure === 'localUnits' ? 'localUnits' : 'employees';
    const label = measure === 'localUnits' ? 'unità locali' : 'addetti';
    const max = Math.max(...items.map(item => Number(item[key] || 0)), 1);
    return `<div class="ateco-bar-list">${items.map(item => {
      const value = Number(item[key] || 0);
      const companion = measure === 'localUnits'
        ? `${number2.format(Number(item.employees || 0))} addetti medi annui`
        : `${number0.format(Number(item.localUnits || 0))} unità locali`;
      return `<div class="ateco-bar-row"><div class="ateco-bar-head"><span><b>${esc(item.code)}</b> ${esc(item.label)}</span><strong>${measure === 'localUnits' ? number0.format(value) : number2.format(value)}</strong></div><div class="ateco-bar-track"><span style="width:${value / max * 100}%"></span></div><small>${esc(label)} · ${esc(companion)}</small></div>`;
    }).join('')}</div>`;
  }

  function townMarkup(data, town) {
    const ateco = data.ateco;
    const item = ateco?.towns?.[town.code];
    if (!item) return '';
    return `<section id="ateco-town-module" class="ateco-module topic-deep-dive"><div class="deep-heading"><div><span class="overline">ISTAT ASIA-UL · ${esc(ateco.year)}</span><h3>Struttura produttiva per settore ATECO</h3></div><p>Ripartizione delle unità locali e degli addetti per divisione ATECO/NACE Rev.2 a 2 cifre.</p></div>
      <div class="ateco-top-grid"><div><h4>Top 10 per unità locali</h4>${topBars(item.topByLocalUnits || [], 'localUnits')}</div><div><h4>Top 10 per addetti</h4>${topBars(item.topByEmployees || [], 'employees')}</div></div>
      <details class="detail-disclosure ateco-full"><summary><span>Mostra tutti i settori ATECO</span><small>${number0.format((item.sectors || []).length)} divisioni con presenza nel Comune</small></summary><div class="ateco-table-wrap"><table class="ateco-table"><thead><tr><th>ATECO</th><th>Settore</th><th>Unità locali</th><th>Quota UL</th><th>Addetti</th><th>Quota addetti</th></tr></thead><tbody>${(item.sectors || []).map(sector => `<tr><td>${esc(sector.code)}</td><td>${esc(sector.label)}</td><td>${number0.format(Number(sector.localUnits || 0))}</td><td>${sector.localUnitsShare == null ? 'n.d.' : `${number1.format(sector.localUnitsShare)}%`}</td><td>${number2.format(Number(sector.employees || 0))}</td><td>${sector.employeesShare == null ? 'n.d.' : `${number1.format(sector.employeesShare)}%`}</td></tr>`).join('')}</tbody></table></div></details>
      <p class="ateco-source-note">Fonte: <a href="${esc(ateco.sourceUrl)}" target="_blank" rel="noreferrer">${esc(ateco.source)} ↗</a>. ${esc(ateco.caveat)}</p></section>`;
  }

  function insertTown(data) {
    const main = document.querySelector('main.town-profile');
    if (!main || main.dataset.theme !== 'economia') {
      document.getElementById('ateco-town-module')?.remove();
      return;
    }
    const match = location.pathname.match(/\/comuni\/([^/]+)\//);
    if (!match) return;
    const town = data.towns.find(item => slug(item.name) === match[1]);
    if (!town || document.getElementById('ateco-town-module')) return;
    const anchor = document.querySelector('#town-topic .topic-deep-dive') || document.querySelector('#town-topic .all-indicators');
    if (!anchor) return;
    anchor.insertAdjacentHTML('afterend', townMarkup(data, town));
  }

  function sectorCatalog(data) {
    const map = new Map();
    Object.values(data.ateco?.towns || {}).forEach(town => (town.sectors || []).forEach(sector => map.set(sector.code, sector.label)));
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1], 'it'));
  }

  function compareRows(data, code, measure) {
    return data.towns.map(town => {
      const item = data.ateco?.towns?.[town.code];
      const sector = item?.sectors?.find(row => row.code === code);
      return {
        town: town.name,
        value: Number(sector?.[measure] || 0),
        share: sector?.[measure === 'localUnits' ? 'localUnitsShare' : 'employeesShare'],
      };
    }).sort((a, b) => b.value - a.value || a.town.localeCompare(b.town, 'it'));
  }

  function updateCompare(data, measure) {
    const select = document.getElementById('ateco-sector-select');
    const target = document.getElementById('ateco-compare-result');
    if (!select || !target) return;
    const rows = compareRows(data, select.value, measure);
    const max = Math.max(...rows.map(row => row.value), 1);
    const unit = measure === 'localUnits' ? 'unità locali' : 'addetti';
    target.innerHTML = `<div class="ateco-compare-bars">${rows.map(row => `<div class="ateco-compare-row"><div class="ateco-bar-head"><span>${esc(row.town)}</span><strong>${measure === 'localUnits' ? number0.format(row.value) : number2.format(row.value)}</strong></div><div class="ateco-bar-track"><span style="width:${row.value / max * 100}%"></span></div><small>${row.share == null ? 'Quota n.d.' : `${number1.format(row.share)}% del totale comunale`} · ${unit}</small></div>`).join('')}</div>`;
    document.querySelectorAll('[data-ateco-measure]').forEach(button => button.classList.toggle('active', button.dataset.atecoMeasure === measure));
  }

  function insertCompare(data) {
    if (!location.pathname.includes('/confronta/economia/') || document.getElementById('ateco-compare-module')) return;
    const sectors = sectorCatalog(data);
    if (!sectors.length) return;
    const anchor = document.getElementById('compare-benchmark');
    if (!anchor) return;
    anchor.insertAdjacentHTML('afterend', `<section id="ateco-compare-module" class="ateco-module ateco-compare page-width"><div class="section-heading"><div><span class="overline">Struttura produttiva · ${esc(data.ateco.year)}</span><h2>Confronta un settore ATECO</h2></div><p>Seleziona una divisione ATECO a 2 cifre e confronta unità locali e addetti nei sette Comuni.</p></div><div class="ateco-compare-controls"><label for="ateco-sector-select">Settore</label><select id="ateco-sector-select">${sectors.map(([code, label]) => `<option value="${esc(code)}">${esc(code)} · ${esc(label)}</option>`).join('')}</select><div class="scale-switch" role="group" aria-label="Misura ATECO"><button type="button" class="active" data-ateco-measure="localUnits">Unità locali</button><button type="button" data-ateco-measure="employees">Addetti</button></div></div><div id="ateco-compare-result"></div><p class="ateco-source-note">Fonte: <a href="${esc(data.ateco.sourceUrl)}" target="_blank" rel="noreferrer">${esc(data.ateco.source)} ↗</a>. ${esc(data.ateco.caveat)}</p></section>`);
    let measure = 'localUnits';
    document.getElementById('ateco-sector-select')?.addEventListener('change', () => updateCompare(data, measure));
    document.querySelectorAll('[data-ateco-measure]').forEach(button => button.addEventListener('click', () => {
      measure = button.dataset.atecoMeasure;
      updateCompare(data, measure);
    }));
    updateCompare(data, measure);
  }

  async function boot() {
    if (!location.pathname.includes('/confronta/economia/') && !location.pathname.includes('/comuni/')) return;
    try {
      const data = await loadData();
      if (!data.ateco) return;
      insertCompare(data);
      insertTown(data);
      const observer = new MutationObserver(() => insertTown(data));
      observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-theme'] });
    } catch (error) {
      console.warn('ATECO module unavailable:', error);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
