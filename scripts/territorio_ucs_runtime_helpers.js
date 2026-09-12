  /* OV TERRITORIO UCS RUNTIME v1.36.0 */
  function degurbaExplainerMarkup() {
    return `<div class="degurba-explainer">
      <div class="land-cover-subheading"><span class="overline">Come si legge DEGURBA</span><h4>Grado di urbanizzazione Istat / Eurostat</h4></div>
      <p>DEGURBA classifica i Comuni in base a dove vive la popolazione nella griglia territoriale. Non è un punteggio e il numero della classe non esprime una graduatoria di qualità.</p>
      <div class="degurba-class-grid">
        <article><strong>1</strong><span>Città o zone densamente popolate</span></article>
        <article><strong>2</strong><span>Piccole città e sobborghi o zone a densità intermedia</span></article>
        <article><strong>3</strong><span>Zone rurali o scarsamente popolate</span></article>
      </div>
      <p class="aggregate-note">Nel perimetro dell’Osservatorio sei Comuni sono in classe 2 e Stazzema è in classe 3; nessuno dei sette è in classe 1.</p>
    </div>`;
  }

  function territorialClassificationTownMarkup(metric,row) {
    const c=row.classification||{};
    const yesNo=value=>value?'Sì':'No';
    return `<div class="territorial-classification-grid">
      <article><span>Litoraneità</span><strong>${yesNo(c.littoral)}</strong><small>${c.littoral?'Comune direttamente litoraneo':'Comune non direttamente litoraneo'}</small></article>
      <article><span>Zona costiera Istat</span><strong>${yesNo(c.coastalZone)}</strong><small>${c.coastalZone?'Ricade nella zona costiera':'Non ricade nella zona costiera'}</small></article>
      <article><span>DEGURBA</span><strong>${html(String(c.degurba||'n.d.'))}</strong><small>${html(c.degurbaLabel||'n.d.')}</small></article>
    </div>
    <p class="aggregate-note territorial-classification-note">Litoraneità e zona costiera sono classificazioni distinte: un Comune può non confinare con il mare e ricadere comunque nella zona costiera Istat.</p>
    ${degurbaExplainerMarkup()}`;
  }

  function territorialClassificationCompareMarkup(data,metricKey) {
    const metric=data.metrics[metricKey],counts=metric.aggregate?.classificationCounts||{};
    const rows=metric.rows||[];
    return `<div class="territorial-classification-shell">
      <div class="territorial-classification-summary">
        <article><span>Comuni litoranei</span><strong>${html(String(counts.littoral??'n.d.'))}/7</strong></article>
        <article><span>In zona costiera</span><strong>${html(String(counts.coastalZone??'n.d.'))}/7</strong></article>
        <article><span>DEGURBA 2</span><strong>${html(String(counts.degurba2??'n.d.'))}/7</strong><small>Densità intermedia</small></article>
        <article><span>DEGURBA 3</span><strong>${html(String(counts.degurba3??'n.d.'))}/7</strong><small>Scarsamente popolata</small></article>
      </div>
      <div class="territorial-classification-list" role="table" aria-label="Classificazioni territoriali dei sette Comuni">
        <div class="territorial-classification-head" role="row"><span>Comune</span><span>Litoraneo</span><span>Zona costiera</span><span>DEGURBA</span></div>
        ${rows.map(row=>{const c=row.classification||{},q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a role="row" href="${route(`comuni/${row.slug}/?${q}`)}"><strong>${html(row.town)}</strong><span>${c.littoral?'Sì':'No'}</span><span>${c.coastalZone?'Sì':'No'}</span><span><b>${html(String(c.degurba||'n.d.'))}</b><small>${html(c.degurbaLabel||'')}</small></span></a>`;}).join('')}
      </div>
      <p class="composite-compare-note">Le classi DEGURBA sono categoriali e non vengono mediate. Il riepilogo Versilia usa esclusivamente conteggi di Comuni per classe.</p>
      ${degurbaExplainerMarkup()}
    </div>`;
  }

  function landCoverDefinitions(metric) {
    return metric.categoryDefinitions||[];
  }

  function landCoverCategory(metric,key) {
    return landCoverDefinitions(metric).find(item=>item.key===key)||landCoverDefinitions(metric)[0]||{};
  }

  function landCoverOptionsMarkup(metric,selected) {
    const defs=landCoverDefinitions(metric),macro=defs.filter(item=>item.level==='macro'),detail=defs.filter(item=>item.level==='detail');
    const options=list=>list.map(item=>`<option value="${html(item.key)}" ${item.key===selected?'selected':''}>${html(item.shortLabel||item.label)}</option>`).join('');
    return `<optgroup label="Macroclassi">${options(macro)}</optgroup><optgroup label="Dettaglio">${options(detail)}</optgroup>`;
  }

  function landCoverSeriesValues(source,key,unit) {
    const series=source?.coverSeries?.[key]||{};
    return unit==='hectares'?(series.ha||[]):(series.pct||[]);
  }

  function landCoverFormat(value,unit) {
    const numeric=Number(value);
    if(!Number.isFinite(numeric)) return 'n.d.';
    return unit==='hectares'?formatValue(numeric,'hectares'):formatValue(numeric,'percent');
  }

  function landCoverNiceScaleMax(values,unit) {
    const raw=Math.max(...(values||[]).map(value=>Math.max(0,Number(value)||0)),0);
    if(raw<=0) return 1;
    const magnitude=Math.pow(10,Math.floor(Math.log10(raw)));
    const normalized=raw/magnitude;
    const factor=normalized<=1?1:normalized<=2?2:normalized<=2.5?2.5:normalized<=5?5:10;
    const nice=factor*magnitude;
    return unit==='percent'?Math.min(100,nice):nice;
  }

  function landCoverScaleAxisMarkup(scaleMax,unit) {
    const zero=unit==='hectares'?'0 ha':'0%';
    return `<div class="land-cover-compare-axis" aria-hidden="true"><span>${zero}</span><span>scala del grafico</span><span>${html(landCoverFormat(scaleMax,unit))}</span></div>`;
  }

  function landCoverChartMarkup(metric,source,categoryKey='artificialized',unit='percent',label='Territorio') {
    const def=landCoverCategory(metric,categoryKey),values=landCoverSeriesValues(source,categoryKey,unit),years=metric.landCoverYears||[];
    const complete=values.length===years.length&&values.every(value=>Number.isFinite(Number(value)));
    const chart=complete?seriesChart({years,values},unit,`${def.label||metric.meta.label} · ${label}`):'<p>Serie non disponibile.</p>';
    const first=values[0],last=values.at(-1),delta=Number(last)-Number(first);
    const deltaLabel=Number.isFinite(delta)?`${delta>0?'+':''}${landCoverFormat(delta,unit)}`:'n.d.';
    const caveat=def.caveat?`<p class="aggregate-note land-cover-caveat"><b>Nota:</b> ${html(def.caveat)}</p>`:'';
    const readingNote=unit==='hectares'
      ? 'La linea mostra gli ettari cartografati nella classe selezionata per ciascuna annualità UCS.'
      : 'La linea mostra la quota della classe selezionata sulla superficie UCS del Comune per ciascuna annualità.';
    return `<div class="land-cover-chart-content" data-land-cover-chart-content>
      <div class="land-cover-series-heading"><span class="overline">Andamento 2007–2019</span><strong>${html(def.shortLabel||def.label||'Copertura')}</strong><small>${html(readingNote)}</small></div>
      ${chart}
      <div class="land-cover-series-summary">
        <article><span>2007</span><strong>${html(landCoverFormat(first,unit))}</strong></article>
        <article><span>2019</span><strong>${html(landCoverFormat(last,unit))}</strong></article>
        <article><span>Variazione 2007→2019</span><strong>${html(deltaLabel)}</strong><small>Differenza della lettura selezionata</small></article>
      </div>${caveat}
    </div>`;
  }

  function landCoverMacro2019Markup(metric,source) {
    const parts=source?.parts||[];
    if(!parts.length) return '';
    return `<div class="land-cover-composition"><div class="land-cover-subheading"><span class="overline">Composizione 2019</span><h4>Macroclassi UCS</h4></div>${compositePartLegend(metric)}${compositeStackMarkup(parts,{ariaLabel:'Composizione UCS 2019'})}</div>`;
  }

  function landCoverTransformationMarkup(source,label='Territorio') {
    const t=source?.transformation||{};
    return `<div class="land-cover-transformation"><span class="overline">Trasformazione 2007→2019</span><strong>${html(landCoverFormat(t.changedPct,'percent'))}</strong><small>${html(landCoverFormat(t.changedHa,'hectares'))} · superficie in cui cambia la macroclasse UCS di livello 1 · ${html(label)}</small></div>`;
  }

  function landCoverTownMarkup(metric,row,category='artificialized',unit='percent') {
    return `<div class="land-cover-shell land-cover-town-shell" data-land-cover-town-shell>
      <div class="land-cover-controls" aria-label="Selettori del grafico">
        <label><span>Copertura</span><select data-land-cover-town-category>${landCoverOptionsMarkup(metric,category)}</select></label>
        <label><span>Unità</span><select data-land-cover-town-unit><option value="percent" ${unit==='percent'?'selected':''}>%</option><option value="hectares" ${unit==='hectares'?'selected':''}>ha</option></select></label>
      </div>
      <div class="land-cover-chart-host" data-land-cover-town-chart>${landCoverChartMarkup(metric,row,category,unit,row.town)}</div>
      ${landCoverMacro2019Markup(metric,row)}
      ${landCoverTransformationMarkup(row,row.town)}
      <p class="aggregate-note">Le percentuali comunali usano come denominatore l'intera superficie UCS del Comune nello stesso anno. Le sottoclassi non si sommano ai macrogruppi di cui fanno parte.</p>
    </div>`;
  }

  function landCoverCompareRows(data,metricKey,category,year,unit) {
    const metric=data.metrics[metricKey],years=metric.landCoverYears||[],index=Math.max(0,years.indexOf(Number(year)));
    const rows=metric.rows.map(row=>{const values=landCoverSeriesValues(row,category,unit);return {...row,displayValue:values[index]};})
      .sort((a,b)=>(Number(b.displayValue)||0)-(Number(a.displayValue)||0));
    const scaleMax=landCoverNiceScaleMax(rows.map(row=>row.displayValue),unit);
    const markup=rows.map((row,rank)=>{
      const q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey}),formatted=landCoverFormat(row.displayValue,unit);
      const width=Math.max(0,Math.min(100,(Number(row.displayValue)||0)/scaleMax*100));
      return `<a class="bar-row" href="${route(`comuni/${row.slug}/?${q}`)}" aria-label="${html(row.town)}: ${html(formatted)}"><span class="bar-rank">${rank+1}</span><span class="bar-town">${html(row.town)}</span><span class="bar-track"><span class="bar-fill" style="width:${width}%"></span><span class="bar-hover-label">${html(row.town)} · ${html(formatted)}</span></span><strong>${html(formatted)}</strong></a>`;
    }).join('');
    return {markup,scaleMax};
  }

  function landCoverTransformationCompareMarkup(metric) {
    const rows=[...(metric.rows||[])].sort((a,b)=>(Number(b.transformation?.changedPct)||0)-(Number(a.transformation?.changedPct)||0));
    const scaleMax=landCoverNiceScaleMax(rows.map(row=>row.transformation?.changedPct),'percent');
    const rowsMarkup=rows.map((row,index)=>{
      const t=row.transformation||{},q=new URLSearchParams({tema:metric.meta.theme,indicatore:metric.meta.key});
      const width=Math.max(0,Math.min(100,(Number(t.changedPct)||0)/scaleMax*100));
      return `<a class="bar-row" href="${route(`comuni/${row.slug}/?${q}`)}"><span class="bar-rank">${index+1}</span><span class="bar-town">${html(row.town)}</span><span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span><strong>${html(landCoverFormat(t.changedPct,'percent'))}</strong></a>`;
    }).join('');
    return `<div class="land-cover-transform-compare"><div class="land-cover-subheading"><span class="overline">Trasformazione 2007→2019</span><h4>Superficie che cambia macroclasse UCS</h4></div><div class="land-cover-compare-list">${rowsMarkup}</div>${landCoverScaleAxisMarkup(scaleMax,'percent')}<p class="aggregate-note">Versilia: <b>${html(landCoverFormat(metric.aggregate?.transformation?.changedPct,'percent'))}</b> (${html(landCoverFormat(metric.aggregate?.transformation?.changedHa,'hectares'))}). Il valore Versilia è Σ ha cambiati / Σ ha UCS, non la media delle percentuali comunali.</p></div>`;
  }

  function landCoverCompareMarkup(data,metricKey,view={}) {
    const metric=data.metrics[metricKey];
    const category=view.landCoverCategory||'artificialized';
    const year=Number(view.landCoverYear)||2019;
    const unit=view.landCoverUnit||'percent';
    const def=landCoverCategory(metric,category),years=metric.landCoverYears||[];
    const index=Math.max(0,years.indexOf(year));
    const aggregateValues=landCoverSeriesValues(metric.aggregate,category,unit);
    const aggregateValue=aggregateValues[index];
    const comparison=landCoverCompareRows(data,metricKey,category,year,unit);
    return `<div class="land-cover-shell land-cover-compare-shell" data-land-cover-compare-shell>
      <div class="land-cover-controls" aria-label="Selettori del grafico">
        <label><span>Copertura</span><select data-land-cover-compare-category>${landCoverOptionsMarkup(metric,category)}</select></label>
        <label><span>Anno</span><select data-land-cover-compare-year>${years.map(item=>`<option value="${item}" ${item===year?'selected':''}>${item}</option>`).join('')}</select></label>
        <label><span>Unità</span><select data-land-cover-compare-unit><option value="percent" ${unit==='percent'?'selected':''}>%</option><option value="hectares" ${unit==='hectares'?'selected':''}>ha</option></select></label>
      </div>
      <div class="land-cover-aggregate-reading"><span>Versilia · ${html(def.shortLabel||def.label||'')}</span><strong>${html(landCoverFormat(aggregateValue,unit))}</strong><small>${html(String(year))} · aggregato da superfici</small></div>
      <div class="land-cover-compare-list">${comparison.markup}</div>
      ${landCoverScaleAxisMarkup(comparison.scaleMax,unit)}
      <p class="composite-compare-note">La quota Versilia è calcolata come Σ ettari della categoria / Σ ettari UCS dei sette Comuni. Non viene usata la media aritmetica delle percentuali comunali.</p>
      ${landCoverTransformationCompareMarkup(metric)}
    </div>`;
  }

