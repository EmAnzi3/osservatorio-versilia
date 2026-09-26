(() => {
  'use strict';

  const SCRIPT_URL = document.currentScript?.src || location.href;
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const numberFormatters = new Map();

  function parseItalianNumber(text) {
    let value = String(text || '').trim().replace(/\u00a0/g, ' ');
    value = value.replace(/[^0-9,.-]/g, '');
    value = value.replace(/[.,]+$/, '');
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
    let unitLabel = '';

    /* The original ChatGPT Sites chart deliberately abbreviates these
       long units on the ordinate and shows only one decimal place. */
    if (text.includes(' anni') || text.includes(' ogni ')) {
      decimals = 1;
    } else if (text.includes('€/ab')) {
      decimals = 2;
      unitLabel = '€/ab.';
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

    return { decimals, suffix, unitLabel };
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
    const { unitLabel } = axisFormat(sample);
    const firstGridX = Math.min(...grids.map(line => Number(line.getAttribute('x1'))).filter(Number.isFinite));
    const labelX = Number.isFinite(firstGridX) ? firstGridX - (unitLabel ? 4 : 8) : 44;

    if (unitLabel) {
      const unit = document.createElementNS(SVG_NS, 'text');
      unit.setAttribute('class', 'chart-label chart-y-unit');
      unit.setAttribute('x', '4');
      unit.setAttribute('y', '15');
      unit.setAttribute('text-anchor', 'start');
      unit.textContent = unitLabel;
      svg.prepend(unit);
    }

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

  const A5_TOOLS_ACTION_METRICS = new Set([
    'bathingWaterQuality',
    'bathingNonCompliantSamples',
    'blueFlagBeaches',
    'shorelineDynamics',
    'rigidDefenceProtectedCoast'
  ]);

  function syncA5CompareSpecialRouteActions() {
    if (document.body.dataset.page !== 'compare') return;
    const main=document.querySelector('main.a5-editorial-pilot');
    const tools=document.getElementById('compare-tools');
    const heading=document.querySelector('.compare-main-column > .compare-panel-heading');
    if (!main || !tools || !heading) return;

    const activeMetric=document.querySelector('.topic-controls [data-metric].active, .topic-controls [data-metric][aria-selected="true"]');
    const metricKey=activeMetric?.dataset.metric || '';
    const slowMobility=metricKey.startsWith('slowMobility');
    const existing=tools.querySelector(':scope > .a5-special-route-actions');

    if (A5_TOOLS_ACTION_METRICS.has(metricKey)) {
      const actions=heading.querySelector(':scope > .data-actions')
        || document.querySelector('#compare-bars .ux-view-toolbar > .data-actions');
      if (actions && actions.parentElement !== tools) tools.append(actions);
    }

    if (!slowMobility) {
      existing?.remove();
      return;
    }

    document.querySelectorAll(
      '.compare-panel-heading .data-actions a[href*="/percorsi/"], #compare-bars .ux-view-toolbar a[href*="/percorsi/"], #compare-tools > .data-actions a[href*="/percorsi/"]'
    ).forEach(link => link.remove());

    if (existing) return;
    const host=document.createElement('div');
    host.className='a5-special-route-actions';
    const link=document.createElement('a');
    link.href=new URL('../percorsi/',SCRIPT_URL).href;
    link.innerHTML='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 18 3.8 20.3A1 1 0 0 1 2.4 19.4V6.2a1 1 0 0 1 .6-.9L9 2.7m0 15.3 6 3.3m-6-3.3V2.7m6 18.6 6-2.7a1 1 0 0 0 .6-.9V4.5a1 1 0 0 0-1.4-.9L15 6m0 15.3V6m0 0L9 2.7" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Esplora la cartografia</span>';
    host.append(link);
    tools.append(host);
  }

  function enhanceCharts(root = document) {
    root.querySelectorAll?.('.trend-chart').forEach(addYAxisLabels);
    syncA5CompareSpecialRouteActions();
    syncA5FinancialCompareHistory();
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

  function scheduleA5CompareContractSync() {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      syncA5CompareSpecialRouteActions();
      syncA5FinancialCompareHistory();
    }));
  }

  document.addEventListener('change', event => {
    if (event.target.closest?.('main.a5-editorial-pilot .compare-chart-toolbar')) {
      scheduleA5CompareContractSync();
    }
  });

  document.addEventListener('click', event => {
    if (event.target.closest?.('main.a5-editorial-pilot [data-composite-choice], main.a5-editorial-pilot [data-composite-scale]')) {
      scheduleA5CompareContractSync();
    }
  });

  installMobileThemeJump();
  scheduleEnhancement();


  /* A5.4 municipal renderer adapter.
     This layer is deliberately additive: release materializers depend on literal
     contracts in app-parts/03.txt and ux-history.js, so A5 composition belongs here. */
  const A5_DEMOGRAPHY_METRICS = new Set([
    'population',
    'ageDistribution',
    'oldAgeIndex',
    'dependencyIndices',
    'foreignResidents',
    'internalResidentialMobility',
    'foreignResidentialMobility',
    'totalResidentialMobility',
    'naturalDemographicDynamics',
    'populationChange'
  ]);
  const a5DataUrl = new URL('../data/site-data.json', SCRIPT_URL).href;
  const a5Number0 = new Intl.NumberFormat('it-IT', { maximumFractionDigits:0, useGrouping:'always' });
  const a5Number1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits:1, maximumFractionDigits:1, useGrouping:'always' });
  let a5Data = null;
  let a5Scheduled = false;

  function a5FinancialChoiceMetric(metric, choice) {
    if (!metric || metric.meta?.compositeType !== 'financialProfile') return metric;
    const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);
    const template=metric.rows?.[0]?.parts?.[index] || metric.aggregate?.parts?.[index] || {};
    const rawUnit=template.unit || metric.meta.unit;
    const unit=rawUnit === 'percent2' ? '%' : rawUnit;
    const number1=new Intl.NumberFormat('it-IT',{minimumFractionDigits:1,maximumFractionDigits:1,useGrouping:'always'});
    const clone={...metric,meta:{...metric.meta,unit,label:template.label || metric.meta.label}};
    clone.rows=(metric.rows || []).map(row=>{
      const part=row.parts?.[index] || {};
      const raw=part.value;
      const value=raw === null || raw === undefined || raw === '' ? undefined : Number(raw);
      let formatted='n.d.';
      if (Number.isFinite(value)) {
        if (unit === 'eurPerResident') formatted=`${number1.format(value)} €/ab.`;
        else if (unit === '%') formatted=`${number1.format(value)}%`;
        else formatted=number1.format(value);
      }
      return {...row,value,formatted,series:part.series || row.series};
    });
    return clone;
  }

  function a5FinancialChoice() {
    return document.querySelector('#compare-bars select[data-composite-component]')?.value || 'part-0';
  }

  function syncA5FinancialCompareHistory() {
    if (!a5Data || document.body.dataset.page !== 'compare' || document.body.dataset.theme !== 'bilanci') return;
    const active=document.querySelector('.topic-controls [data-metric].active, .topic-controls [data-metric][aria-selected="true"]');
    if (active?.dataset.metric !== 'financialDebtProfile') return;
    const metric=a5Data.metrics?.financialDebtProfile;
    const target=document.getElementById('compare-bars');
    const toolkit=window.OVUXHistory;
    if (!metric || !target || !toolkit) return;

    let shell=target.querySelector(':scope > .ux-view-shell');
    const selectedTown=(() => { try { return sessionStorage.getItem('ov-history-town') || ''; } catch { return ''; } })();
    const choice=a5FinancialChoice();
    const viewMetric=a5FinancialChoiceMetric(metric,choice);
    const series=toolkit.comparableSeries(viewMetric);

    if (!shell) {
      const direct=target.querySelector(':scope > .topic-bars');
      if (!direct) return;
      direct.querySelector('.financial-aggregate-history')?.remove();
      const currentMarkup=direct.outerHTML;
      const historyMarkup=toolkit.historicalChartMarkup(viewMetric,series,selectedTown);
      const note='Storico 2019–2025 dei sette Comuni per la lettura selezionata. Nessuna media Versilia sostituisce le serie comunali.';
      target.innerHTML=toolkit.viewShellMarkup(currentMarkup,historyMarkup,Boolean(series),note);
      shell=target.querySelector(':scope > .ux-view-shell');
      if (!shell) return;
      toolkit.wireViewShell(shell,'ov-compare-view',Boolean(series));
      toolkit.wireHistorySelection(shell,selectedTown,true);
      shell.dataset.financialChoice=choice;
      return;
    }

    shell.querySelector('[data-view-pane="current"] .financial-aggregate-history')?.remove();
    if (shell.dataset.financialChoice === choice) return;
    const pane=shell.querySelector('[data-view-pane="history"]');
    if (pane) {
      pane.innerHTML=toolkit.historicalChartMarkup(viewMetric,series,selectedTown);
      toolkit.wireHistorySelection(shell,selectedTown,true);
    }
    const historyButton=shell.querySelector('[data-view-mode="history"]');
    if (historyButton) historyButton.disabled=!series;
    shell.dataset.financialChoice=choice;
  }

  function a5Escape(value) {
    return String(value ?? '')
      .replaceAll('&','&amp;')
      .replaceAll('<','&lt;')
      .replaceAll('>','&gt;')
      .replaceAll('"','&quot;')
      .replaceAll("'",'&#39;');
  }

  function a5MetricKey() {
    return new URL(location.href).searchParams.get('indicatore') || '';
  }

  function a5TownSlug(row) {
    return row?.slug || String(row?.town || '').toLocaleLowerCase('it')
      .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  }

  function a5Format(value, unit) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 'n.d.';
    if (unit === 'years') return `${a5Number1.format(number)} anni`;
    if (unit === 'percent') return `${a5Number1.format(number)}%`;
    if (unit === 'per1000') return `${a5Number1.format(number)} ogni 1.000`;
    if (unit === 'per100') return `${a5Number1.format(number)} ogni 100`;
    if (unit === 'per10k') return `${a5Number1.format(number)} ogni 10.000`;
    if (unit === 'number') return a5Number0.format(number);
    return a5Number1.format(number);
  }

  function a5DefaultView(metric) {
    const type = metric?.meta?.compositeType || '';
    if (type === 'stock') return { choice:'share', scale:'value' };
    if (type === 'mobility') return { choice:'part-2', scale:'rate' };
    if (type === 'securityMeasures') return { choice:'part-0', scale:'value' };
    return { choice:'', scale:'value' };
  }

  function a5Selection(metric, row, choice, scale) {
    const type = metric?.meta?.compositeType || '';
    if (type === 'stock') {
      const count = choice === 'count';
      return {
        value:count ? row?.count : row?.value,
        unit:count ? 'number' : 'percent',
        label:count ? 'Residenti di cittadinanza straniera' : 'Quota di residenti stranieri'
      };
    }
    if (type === 'mobility') {
      const index = Math.max(0,Math.min(2,Number(String(choice || 'part-2').replace('part-','')) || 0));
      const part = row?.parts?.[index] || {};
      return {
        value:scale === 'count' ? part.count : part.value,
        unit:scale === 'count' ? 'number' : 'per1000',
        label:part.label || metric.meta.label,
        part,
        index
      };
    }
    if (type === 'securityMeasures') {
      const index = Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = row?.parts?.[index] || {};
      return {
        value:part.value,
        unit:part.unit || metric.meta.unit,
        label:part.selectorLabel || part.label || metric.meta.label,
        part,
        index
      };
    }
    return { value:row?.value, unit:metric?.meta?.unit, label:metric?.meta?.label };
  }

  function a5Reference(metric, choice, scale) {
    const type = metric?.meta?.compositeType || '';
    if (type === 'stock') {
      if (choice === 'count') {
        const values=(metric.rows || []).map(row=>Number(row.count)).filter(Number.isFinite);
        return {
          value:values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null,
          unit:'number',
          label:`Media semplice dei ${values.length} comuni · residenti stranieri`
        };
      }
      return { value:metric.aggregate?.value, unit:'percent', label:'Versilia · quota residenti stranieri' };
    }
    if (type === 'mobility') {
      const index=Math.max(0,Math.min(2,Number(String(choice || 'part-2').replace('part-','')) || 0));
      const part=metric.aggregate?.parts?.[index] || {};
      if (scale === 'count') {
        const values=(metric.rows || []).map(row=>Number(row.parts?.[index]?.count)).filter(Number.isFinite);
        return {
          value:values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null,
          unit:'number',
          label:`Media semplice dei ${values.length} comuni · ${part.label || metric.meta.label}`
        };
      }
      return { value:part.value, unit:'per1000', label:`Versilia · ${part.label || metric.meta.label}` };
    }
    if (type === 'securityMeasures') {
      const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part=metric.aggregate?.parts?.[index] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}` };
    }
    return { value:metric.aggregate?.value, unit:metric.meta.unit, label:metric.aggregate?.label || 'Versilia' };
  }

  function a5Delta(local, reference, unit) {
    const a=Number(local), b=Number(reference);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return { headline:'n.d.', direction:'confronto non disponibile' };
    const diff=a-b;
    if (Math.abs(diff) < 0.000001) return { headline:a5Format(0,unit), direction:'in linea con la Versilia' };
    return {
      headline:`${diff > 0 ? '+' : '−'}${a5Format(Math.abs(diff),unit)}`,
      direction:diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia'
    };
  }

  function a5TownHref(row, metricKey) {
    const url=new URL(`../${a5TownSlug(row)}/`, location.href);
    url.searchParams.set('tema','demografia');
    url.searchParams.set('indicatore',metricKey);
    return url.href;
  }

  function a5ControlsMarkup(metric, choice, scale) {
    const type=metric?.meta?.compositeType || '';
    if (type === 'stock') {
      return `<div class="compare-view-controls"><div><span class="compare-view-label">Lettura</span><div class="scale-switch compact" role="group" aria-label="Lettura residenti stranieri"><button type="button" data-composite-choice="share" class="${choice === 'share' ? 'active' : ''}">Quota %</button><button type="button" data-composite-choice="count" class="${choice === 'count' ? 'active' : ''}">Valore assoluto</button></div></div></div>`;
    }
    if (type === 'mobility') {
      const parts=metric.rows?.[0]?.parts || [];
      return `<div class="compare-view-controls mobility-view-controls"><label class="compare-choice-select"><span>Voce</span><select data-composite-component>${parts.map((part,index)=>`<option value="part-${index}" ${choice === `part-${index}` ? 'selected' : ''}>${a5Escape(part.label)}</option>`).join('')}</select></label><div><span class="compare-view-label">Unità</span><div class="scale-switch compact" role="group" aria-label="Scala della mobilità residenziale"><button type="button" data-composite-scale="rate" class="${scale === 'rate' ? 'active' : ''}">Ogni 1.000</button><button type="button" data-composite-scale="count" class="${scale === 'count' ? 'active' : ''}">Valore assoluto</button></div></div></div>`;
    }
    if (type === 'securityMeasures') {
      const parts=metric.rows?.[0]?.parts || [];
      return `<div class="compare-view-controls"><label class="compare-choice-select"><span>${a5Escape(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map((part,index)=>`<option value="part-${index}" ${choice === `part-${index}` ? 'selected' : ''}>${a5Escape(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`;
    }
    return '';
  }

  function a5ComparisonRows(metric, metricKey, selectedTown, choice, scale) {
    const rows=(metric.rows || []).map(row=>{
      const selected=a5Selection(metric,row,choice,scale);
      return {row,value:selected.value,unit:selected.unit};
    }).sort((a,b)=>{
      const av=Number(a.value), bv=Number(b.value);
      return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);
    });
    const max=Math.max(...rows.map(item=>Math.abs(Number(item.value)) || 0),0.0001);
    return rows.map((item,index)=>{
      const slug=a5TownSlug(item.row);
      const missing=!Number.isFinite(Number(item.value));
      const formatted=a5Format(item.value,item.unit);
      const width=missing ? 0 : Math.max(1.5,Math.abs(Number(item.value))/max*100);
      return `<a href="${a5Escape(a5TownHref(item.row,metricKey))}" class="bar-row ${slug === selectedTown ? 'selected' : ''}" aria-label="${a5Escape(item.row.town)}: ${a5Escape(formatted)}"><span class="bar-rank">${missing ? '—' : index+1}</span><span class="bar-town">${a5Escape(item.row.town)}</span><span class="bar-track"><span class="bar-fill" style="width:${width}%"></span><span class="bar-hover-label">${a5Escape(item.row.town)} · ${a5Escape(formatted)}</span></span><strong>${a5Escape(formatted)}</strong></a>`;
    }).join('');
  }

  function a5DistributionMarkup(metric, metricKey, selectedTown) {
    const parts=metric.rows?.[0]?.parts || [];
    const legend=`<div class="composite-legend">${parts.map((part,index)=>`<span><i class="composite-swatch part-${index}"></i>${a5Escape(part.label)}</span>`).join('')}</div>`;
    const rows=(metric.rows || []).map(row=>{
      const slug=a5TownSlug(row);
      const rowParts=row.parts || [];
      const stack=`<div class="composite-stack" role="list" aria-label="${a5Escape(metric.meta.label)} · ${a5Escape(row.town)}">${rowParts.map((part,index)=>{
        const value=Math.max(0,Number(part.value)||0);
        const size=value < 3.5 ? ' label-tiny' : value < 6 ? ' label-narrow' : '';
        return `<span class="composite-segment part-${index}${size}" role="listitem" tabindex="0" style="width:${value}%" aria-label="${a5Escape(part.label)}: ${a5Escape(a5Format(value,'percent'))}"><b aria-hidden="true">${a5Escape(a5Format(value,'percent'))}</b><span class="bar-hover-label">${a5Escape(part.label)} · ${a5Escape(a5Format(value,'percent'))}</span></span>`;
      }).join('')}</div>`;
      return `<div class="composite-distribution-row${slug === selectedTown ? ' selected' : ''}"><div class="composite-row-head"><a class="composite-town-link" href="${a5Escape(a5TownHref(row,metricKey))}">${a5Escape(row.town)}</a><span>${a5Escape(metric.meta.summaryLabel || 'Età media')} <b>${a5Escape(a5Format(row.summaryValue,metric.meta.summaryUnit || 'years'))}</b></span></div>${stack}</div>`;
    }).join('');
    return `<div class="topic-bars composite-topic-bars a5-current-family-distribution">${legend}<div class="composite-distribution-list">${rows}</div></div>`;
  }

  function a5SelectableMarkup(metric, metricKey, selectedTown, choice, scale) {
    const type=metric.meta.compositeType;
    return `<div class="topic-bars selectable-topic-bars a5-current-family-${a5Escape(type)}"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${a5ControlsMarkup(metric,choice,scale)}</div><div class="comparison-bars" data-composite-choice="${a5Escape(choice)}" data-composite-scale="${a5Escape(scale)}">${a5ComparisonRows(metric,metricKey,selectedTown,choice,scale)}</div></div>`;
  }


  function a5PrimaryLabel(metric) {
    const explicit = metric?.meta?.primaryLabel || metric?.meta?.shortLabel || metric?.meta?.label;
    return String(explicit || 'Valore dell’indicatore').trim();
  }

  function a5EnsurePrimaryLabel(metric) {
    const primary=document.querySelector('#town-topic .town-metric-primary');
    if (!primary) return null;
    let label=primary.querySelector('[data-composite-primary-label]');
    if (!label) {
      label=document.createElement('span');
      label.className='composite-primary-label a5-primary-label';
      label.dataset.compositePrimaryLabel='';
      primary.insertBefore(label,primary.querySelector('[data-composite-primary-value]') || primary.firstChild);
    } else {
      label.classList.add('a5-primary-label');
    }
    if (!label.textContent.trim()) label.textContent=a5PrimaryLabel(metric);
    return label;
  }

  function a5UpdateSummary(metric, row, choice, scale) {
    if (!['stock','mobility','securityMeasures'].includes(metric?.meta?.compositeType)) return;
    const selection=a5Selection(metric,row,choice,scale);
    const reference=a5Reference(metric,choice,scale);
    const delta=a5Delta(selection.value,reference.value,selection.unit);
    const topic=document.getElementById('town-topic');
    const label=topic?.querySelector('[data-composite-primary-label]');
    const value=topic?.querySelector('[data-composite-primary-value]');
    const position=topic?.querySelector('.versilia-position');
    if (label) label.textContent=selection.label || a5PrimaryLabel(metric);
    if (value) value.textContent=a5Format(selection.value,selection.unit);
    if (!position) return;
    position.classList.add('composite-versilia-position');
    position.innerHTML=`<span class="overline">Rispetto alla Versilia</span><strong data-composite-delta>${a5Escape(delta.headline)}<small>${a5Escape(delta.direction)}</small></strong><p>Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.</p><div><span data-composite-aggregate-label>${a5Escape(reference.label)}</span><b data-composite-aggregate-value>${a5Escape(a5Format(reference.value,reference.unit))}</b></div>`;
  }

  function a5AttachComplementaryDetail(topic, panel, currentPane) {
    let detail=currentPane.querySelector(':scope > .a5-town-current-detail');
    const detached=topic.querySelector(':scope > .a5-town-extra-context.composite-fixed-detail')
      || panel.querySelector(':scope > .composite-fixed-detail');
    if (!detached && detail) return;
    if (!detail) {
      detail=document.createElement('div');
      detail.className='a5-town-current-detail';
      currentPane.append(detail);
    }
    if (detached) {
      detached.classList.remove('a5-town-extra-context');
      detail.append(detached);
    }
  }

  function a5RenderCurrent(metricKey, choiceOverride = '', scaleOverride = '') {
    if (!a5Data || document.body.dataset.page !== 'town') return;
    const main=document.querySelector('main.a5-town-pilot[data-theme="demografia"]');
    if (!main || !A5_DEMOGRAPHY_METRICS.has(metricKey)) return;
    const metric=a5Data.metrics?.[metricKey];
    if (!metric) return;
    const selectedTown=document.body.dataset.town || '';
    const row=(metric.rows || []).find(item=>a5TownSlug(item) === selectedTown);
    const topic=document.getElementById('town-topic');
    const panel=topic?.querySelector(':scope > .history-panel.a5-shared-chart');
    const currentPane=panel?.querySelector('.ux-view-shell [data-view-pane="current"]');
    if (!row || !topic || !panel || !currentPane) return;

    const type=metric.meta.compositeType || '';
    const defaults=a5DefaultView(metric);
    a5EnsurePrimaryLabel(metric);
    let visual=currentPane.querySelector(':scope > .a5-town-current-visual');

    if (!type) {
      if (!visual) {
        visual=document.createElement('div');
        visual.className='a5-town-current-visual a5-current-family-scalar';
        [...currentPane.childNodes].forEach(node=>visual.append(node));
        currentPane.append(visual);
      }
      visual.dataset.a5Metric=metricKey;
      return;
    }

    const previousChoice=visual?.dataset.choice || '';
    const previousScale=visual?.dataset.scale || '';
    const choice=choiceOverride || previousChoice || defaults.choice;
    const scale=scaleOverride || previousScale || defaults.scale;
    const signature=`${metricKey}|${choice}|${scale}`;

    if (!visual) {
      /* Remove the legacy current renderer entirely. Keeping it next to the
         A5 renderer would create a visually plausible but semantically duplicate chart. */
      [...currentPane.childNodes].forEach(node => node.remove());
      visual=document.createElement('div');
      visual.className='a5-town-current-visual';
      currentPane.append(visual);
    }
    if (visual.dataset.a5Signature !== signature) {
      if (type === 'distribution') {
        visual.innerHTML=a5DistributionMarkup(metric,metricKey,selectedTown);
      } else if (['stock','mobility','securityMeasures'].includes(type)) {
        visual.innerHTML=a5SelectableMarkup(metric,metricKey,selectedTown,choice,scale);
      } else {
        return;
      }
      visual.dataset.a5Signature=signature;
      visual.dataset.choice=choice;
      visual.dataset.scale=scale;
    }

    a5AttachComplementaryDetail(topic,panel,currentPane);
    a5UpdateSummary(metric,row,choice,scale);
    main.dataset.a5FidelityReady=metricKey;
  }

  function enhanceA5Town() {
    a5Scheduled=false;
    const metricKey=a5MetricKey();
    if (!A5_DEMOGRAPHY_METRICS.has(metricKey)) return;
    a5RenderCurrent(metricKey);
  }

  function scheduleA5Town() {
    if (a5Scheduled) return;
    a5Scheduled=true;
    requestAnimationFrame(enhanceA5Town);
  }

  document.addEventListener('click', event => {
    const visual=event.target.closest?.('.a5-town-current-visual');
    if (!visual) return;
    const choiceButton=event.target.closest('button[data-composite-choice]');
    const scaleButton=event.target.closest('button[data-composite-scale]');
    if (!choiceButton && !scaleButton) return;
    a5RenderCurrent(
      a5MetricKey(),
      choiceButton?.dataset.compositeChoice || visual.dataset.choice || '',
      scaleButton?.dataset.compositeScale || visual.dataset.scale || ''
    );
  });

  document.addEventListener('change', event => {
    const visual=event.target.closest?.('.a5-town-current-visual');
    if (!visual) return;
    const component=event.target.closest('select[data-composite-component]');
    if (!component) return;
    a5RenderCurrent(a5MetricKey(),component.value,visual.dataset.scale || '');
  });

  window.addEventListener('ov:ux-history-enhanced', () => {
    if (!a5Data) return;
    scheduleA5Town();
  });

  fetch(a5DataUrl,{cache:'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`Dati A5 non disponibili (${response.status})`);
      return response.json();
    })
    .then(payload => {
      a5Data=payload;
      scheduleA5Town();
      scheduleEnhancement();
    })
    .catch(error => console.warn('A5 municipal adapter non applicato:',error));

  /* app.js imports the application module before fidelity.js, but the module
     completes its data fetch/render asynchronously. A pre-rendered town page
     already contains a history panel, so that element alone is not a reliable
     readiness signal for direct links. Wait until the metric requested in the
     URL is the active town control before bootstrapping the climate layer. */
  function loadClimateV3WhenReady(attempt = 0) {
    if (document.querySelector('script[data-ov-climate-v2]')) return;
    const page = document.body.dataset.page;
    const requestedMetric = new URL(location.href).searchParams.get('indicatore');
    const requestedTownMetricReady = !requestedMetric || [...document.querySelectorAll('[data-metric]')].some(button => (
      button.dataset.metric === requestedMetric && button.classList.contains('active')
    ));
    const ready = page === 'town'
      ? Boolean(document.querySelector('.town-profile .history-panel')) && requestedTownMetricReady
      : page === 'compare'
        ? Boolean(document.getElementById('compare-bars'))
        : Boolean(document.querySelector('#app main'));

    if (!ready && attempt < 40) {
      window.setTimeout(() => loadClimateV3WhenReady(attempt + 1), 100);
      return;
    }

    const climateScript = document.createElement('script');
    climateScript.src = new URL('./climate-ux-v3.js?v=20260810-1', SCRIPT_URL).href;
    climateScript.async = false;
    /* Keep the existing marker so the prerender cleanup remains generic for
       the runtime-only climate layer and does not serialize it into HTML. */
    climateScript.dataset.ovClimateV2 = '1';
    climateScript.addEventListener('load', () => {
      const benchmarkScript = document.createElement('script');
      benchmarkScript.src = new URL('./climate-town-benchmark.js?v=20260810-1', SCRIPT_URL).href;
      benchmarkScript.async = false;
      benchmarkScript.dataset.ovClimateV2 = '1';
      document.head.appendChild(benchmarkScript);
    }, { once: true });
    document.head.appendChild(climateScript);
  }

  loadClimateV3WhenReady();
})();
