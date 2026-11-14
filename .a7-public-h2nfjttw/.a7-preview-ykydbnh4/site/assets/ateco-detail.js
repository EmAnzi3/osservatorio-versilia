(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const ROOT = new URL('../', SCRIPT_URL);
  const VERSION = '20260824-v116';
  const number0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 });
  const number1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const number2 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const dataPromise = fetch(new URL(`data/site-data.json?v=${VERSION}`, ROOT))
    .then(response => {
      if (!response.ok) throw new Error(`Errore dati ${response.status}`);
      return response.json();
    })
    .catch(error => {
      console.warn('Dettaglio ATECO non disponibile', error);
      return null;
    });

  const escapeHtml = value => String(value ?? '').replace(/[&<>\"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;' })[char]);
  const slugify = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  function townByPath(data) {
    const match = location.pathname.match(/\/comuni\/([^/]+)\/?/);
    if (!match) return null;
    return data.towns.find(town => slugify(town.name) === match[1]) || null;
  }

  function sectorRows(data, code, measure) {
    return data.towns.map(town => {
      const sector = data.details?.[town.code]?.economy?.atecoSectors?.find(item => item.code === code);
      return { town, sector, value: Number(sector?.[measure] || 0) };
    }).sort((a, b) => b.value - a.value || a.town.name.localeCompare(b.town.name, 'it'));
  }

  function renderCompareRows(data, root) {
    const select = root.querySelector('[data-ateco-sector]');
    const code = select?.value || root.dataset.sector;
    const measure = root.dataset.measure || 'localUnits';
    const meta = data.economyAteco;
    const rows = sectorRows(data, code, measure);
    const max = Math.max(...rows.map(row => row.value), 1);
    const label = meta.labels?.[code] || `ATECO ${code}`;
    const unit = measure === 'workers' ? 'addetti medi annui' : 'unità locali';
    root.dataset.sector = code;
    root.querySelector('[data-ateco-definition]').innerHTML = `<strong>ATECO ${escapeHtml(code)} · ${escapeHtml(label)}</strong><span>${escapeHtml(unit)} · ${escapeHtml(meta.year)}</span>`;
    root.querySelector('[data-ateco-bars]').innerHTML = rows.map((row, index) => {
      const formatted = measure === 'workers' ? number2.format(row.value) : number0.format(row.value);
      const townSlug = slugify(row.town.name);
      return `<a class="ateco-bar-row" href="${new URL(`comuni/${townSlug}/?tema=economia&indicatore=localUnits`, ROOT).pathname}">
        <span class="ateco-rank">${index + 1}</span><span class="ateco-town">${escapeHtml(row.town.name)}</span>
        <span class="ateco-track"><i style="width:${Math.max(1, row.value / max * 100)}%"></i></span><strong>${escapeHtml(formatted)}</strong></a>`;
    }).join('');
    root.querySelectorAll('[data-ateco-measure]').forEach(button => button.classList.toggle('active', button.dataset.atecoMeasure === measure));
  }

  function enhanceCompare(data) {
    const main = document.querySelector('main[data-theme="economia"]');
    const benchmark = document.getElementById('compare-benchmark');
    if (!main || !benchmark || !data.economyAteco?.sectorCodes?.length) {
      document.getElementById('ateco-compare')?.remove();
      return;
    }
    if (document.getElementById('ateco-compare')) return;
    const meta = data.economyAteco;
    const first = meta.sectorCodes.includes('43') ? '43' : meta.sectorCodes[0];
    const panel = document.createElement('section');
    panel.id = 'ateco-compare';
    panel.className = 'ateco-panel page-width';
    panel.dataset.sector = first;
    panel.dataset.measure = 'localUnits';
    panel.innerHTML = `<div class="section-heading compact"><div><span class="overline">Struttura produttiva · ${escapeHtml(meta.year)}</span><h2>Confronta un settore ATECO</h2></div><p>${escapeHtml(meta.classification)} · copertura ${escapeHtml(meta.coverage)}</p></div>
      <div class="ateco-toolbar"><label><span>Divisione ATECO</span><select data-ateco-sector>${meta.sectorCodes.map(code => `<option value="${escapeHtml(code)}" ${code === first ? 'selected' : ''}>${escapeHtml(code)} · ${escapeHtml(meta.labels?.[code] || `ATECO ${code}`)}</option>`).join('')}</select></label>
      <div class="ateco-toggle" role="group" aria-label="Misura ATECO"><button type="button" data-ateco-measure="localUnits" class="active">Unità locali</button><button type="button" data-ateco-measure="workers">Addetti</button></div></div>
      <div class="ateco-definition" data-ateco-definition></div><div class="ateco-bars" data-ateco-bars></div>
      <p class="ateco-note">${escapeHtml(meta.note)} <a href="${escapeHtml(meta.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ISTAT ASIA-UL ↗</a></p>`;
    benchmark.insertAdjacentElement('afterend', panel);
    panel.querySelector('[data-ateco-sector]').addEventListener('change', () => renderCompareRows(data, panel));
    panel.querySelectorAll('[data-ateco-measure]').forEach(button => button.addEventListener('click', () => {
      panel.dataset.measure = button.dataset.atecoMeasure;
      renderCompareRows(data, panel);
    }));
    renderCompareRows(data, panel);
  }

  function sectorList(items, measure) {
    const max = Math.max(...items.map(item => Number(item?.[measure] || 0)), 1);
    return `<div class="ateco-top-list">${items.map(item => {
      const value = Number(item?.[measure] || 0);
      const formatted = measure === 'workers' ? number2.format(value) : number0.format(value);
      const secondary = measure === 'workers' ? `${number0.format(item.localUnits)} unità locali` : `${number2.format(item.workers)} addetti`;
      return `<div class="ateco-top-row"><div><span><b>${escapeHtml(item.code)}</b> · ${escapeHtml(item.label)}</span><strong>${escapeHtml(formatted)}</strong></div><span class="ateco-mini-track"><i style="width:${Math.max(1, value / max * 100)}%"></i></span><small>${escapeHtml(secondary)}</small></div>`;
    }).join('')}</div>`;
  }

  function enhanceTown(data) {
    const main = document.querySelector('main.town-profile[data-theme="economia"]');
    if (!main) {
      document.getElementById('ateco-town-detail')?.remove();
      return;
    }
    const town = townByPath(data);
    const economy = town && data.details?.[town.code]?.economy;
    const sectors = economy?.atecoSectors || [];
    if (!town || !sectors.length) return;
    if (document.getElementById('ateco-town-detail')) return;
    const topWorkers = (economy.topSectors || sectors.slice().sort((a, b) => b.workers - a.workers).slice(0, 10)).slice(0, 10);
    const topUnits = (economy.topSectorsByUnits || sectors.slice().sort((a, b) => b.localUnits - a.localUnits).slice(0, 10)).slice(0, 10);
    const rows = sectors.slice().sort((a, b) => a.code.localeCompare(b.code)).map(item => `<tr><td><b>${escapeHtml(item.code)}</b></td><td>${escapeHtml(item.label)}</td><td>${number0.format(item.localUnits)}</td><td>${number2.format(item.workers)}</td><td>${item.localUnitShare == null ? '—' : `${number1.format(item.localUnitShare)}%`}</td><td>${item.workerShare == null ? '—' : `${number1.format(item.workerShare)}%`}</td></tr>`).join('');
    const section = document.createElement('section');
    section.id = 'ateco-town-detail';
    section.className = 'ateco-town-detail';
    section.innerHTML = `<div class="deep-heading"><div><span class="overline">ISTAT ASIA-UL · ${escapeHtml(economy.atecoYear || 2023)}</span><h3>Ripartizione per settore ATECO</h3></div><p>${escapeHtml(data.economyAteco?.classification || 'Divisioni ATECO a 2 cifre')}. Unità locali e addetti riferiti al luogo di lavoro.</p></div>
      <div class="ateco-top-columns"><div><h4>Top 10 per unità locali</h4>${sectorList(topUnits, 'localUnits')}</div><div><h4>Top 10 per addetti</h4>${sectorList(topWorkers, 'workers')}</div></div>
      <details class="ateco-table-disclosure"><summary><span>Mostra tutte le divisioni ATECO</span><small>${number0.format(sectors.length)} divisioni con valori</small></summary><div class="ateco-table-scroll"><table class="ateco-table"><thead><tr><th>ATECO</th><th>Divisione</th><th>Unità locali</th><th>Addetti</th><th>Quota UL</th><th>Quota addetti</th></tr></thead><tbody>${rows}</tbody></table></div></details>
      <p class="ateco-note">Le unità locali non coincidono con le imprese giuridiche. Gli addetti sono medie annue. <a href="${escapeHtml(economy.atecoSourceUrl || data.economyAteco?.sourceUrl || '')}" target="_blank" rel="noreferrer">Fonte originale ↗</a></p>`;
    const existing = main.querySelector('.topic-deep-dive');
    if (existing) existing.insertAdjacentElement('afterend', section);
    else main.querySelector('#town-topic')?.append(section);
  }

  let scheduled = false;
  function schedule(data) {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      enhanceCompare(data);
      enhanceTown(data);
    });
  }

  dataPromise.then(data => {
    if (!data) return;
    schedule(data);
    const observer = new MutationObserver(() => schedule(data));
    observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-theme'] });
  });
})();
