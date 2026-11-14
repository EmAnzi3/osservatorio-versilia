(() => {
  'use strict';
let DATA=null;
let EMBEDDED_ATECO={};
const SCRIPT_URL=document.currentScript?.src||document.baseURI;
const ROOT=new URL('../',SCRIPT_URL);
let ATLAS_META=null;
const dataUrl=name=>new URL('data/economy-atlas/'+name,ROOT).href;
let atlasLoadPromise=null;
async function unzipBase64Gzip(text){
  const binary=atob(String(text).replace(/\s/g,''));
  const bytes=new Uint8Array(binary.length);
  for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  if(!('DecompressionStream' in window)) throw new Error('Browser non compatibile con la decompressione del dataset.');
  const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return JSON.parse(await new Response(stream).text());
}
async function ensureAtlasData(){
  if(DATA&&Object.keys(EMBEDDED_ATECO).length) return;
  if(!atlasLoadPromise) atlasLoadPromise=(async()=>{
    const metadata=await fetch(dataUrl('metadata.json'),{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`Metadata Atlante non disponibile: ${r.status}`);return r.json()}); ATLAS_META=metadata;
    const readParts=names=>Promise.all((names||[]).map(name=>fetch(dataUrl(name),{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`Risorsa Atlante non disponibile: ${name}`);return r.text()})));
    const [dataParts,taxonomyParts]=await Promise.all([readParts(metadata.files),readParts(metadata.taxonomy_files)]);
    [DATA,EMBEDDED_ATECO]=await Promise.all([unzipBase64Gzip(dataParts.join('')),unzipBase64Gzip(taxonomyParts.join(''))]);
    if(DATA?.v!==2) throw new Error('Formato dataset Atlante non supportato.');
  })();
  return atlasLoadPromise;
}
  const STYLE = "\n:host{display:block;min-width:0;\n  --paper:#f4eee2;--surface:#fff;--ink:#102f45;--muted:#61717b;--blue:#145b78;--blue-soft:#e4eff2;\n  --theme:#ad6247;--theme-soft:#f3e3da;--line:#d5dddb;--sage:#5f8b78;--gold:#c89b3c;--shadow:0 20px 60px rgba(16,47,69,.08);\n  --radius:18px;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:Geist,Inter,ui-sans-serif,system-ui,-apple-system,\"Segoe UI\",Arial,sans-serif;\n}\n*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(circle at 8% 8%,rgba(238,200,101,.12),transparent 26rem),radial-gradient(circle at 92% 28%,rgba(173,98,71,.08),transparent 30rem),var(--paper);color:var(--ink);font-family:var(--sans)}\nbutton,input,select{font:inherit;color:inherit}button{cursor:pointer}.page{width:min(1240px,calc(100% - 48px));margin:auto}.site-header{position:sticky;top:0;z-index:50;border-bottom:1px solid rgba(16,47,69,.1);background:rgba(244,238,226,.93);backdrop-filter:blur(16px)}.site-head{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:11px;font-weight:800}.mark{width:35px;height:35px;border-radius:11px 11px 11px 4px;background:var(--blue);color:white;display:grid;place-items:center;font-size:15px;box-shadow:0 8px 22px rgba(20,91,120,.2)}.brand small{display:block;color:var(--muted);font-weight:600;font-size:9px;letter-spacing:.03em}.proto-tag{font:700 10px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--theme);background:var(--theme-soft);padding:8px 11px;border-radius:999px}\n.breadcrumbs{padding-top:24px;font-size:11px;color:#74838b;display:flex;gap:8px}.hero{display:grid;grid-template-columns:80px 1fr;gap:28px;padding:42px 0 46px;border-bottom:1px solid #cbd4d2}.hero-symbol{width:68px;height:68px;border-radius:20px 20px 20px 7px;background:var(--theme-soft);color:var(--theme);display:grid;place-items:center;font:800 18px var(--mono)}.overline{text-transform:uppercase;letter-spacing:.1em;font-size:9px;font-weight:800;color:var(--theme)}h1{font-size:clamp(48px,7vw,82px);line-height:.9;letter-spacing:-.065em;margin:10px 0 18px}.hero p{max-width:780px;color:#4e6572;font-size:16px;line-height:1.6;margin:0}.hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.meta-pill{background:#fff;border:1px solid rgba(16,47,69,.13);border-radius:999px;padding:8px 11px;font-size:10px;font-weight:750}.meta-pill strong{color:var(--theme)}\n\n.taxonomy-audit{display:flex;align-items:flex-start;gap:10px;margin-bottom:18px;padding:11px 13px;border:1px solid #d6dfdc;border-radius:12px;background:#f7f9f8;font-size:10px;line-height:1.45;color:#50646e}.taxonomy-audit::before{content:\"\";width:8px;height:8px;flex:0 0 8px;margin-top:3px;border-radius:50%;background:#c89b3c;box-shadow:0 0 0 4px rgba(200,155,60,.12)}.taxonomy-audit.ok{background:#f0f7f3;border-color:#cce0d5;color:#315d49}.taxonomy-audit.ok::before{background:#5f8b78;box-shadow:0 0 0 4px rgba(95,139,120,.13)}.taxonomy-audit.error{background:#fbf1ed;border-color:#e6cabe;color:#7b4937}.taxonomy-audit.error::before{background:#ad6247;box-shadow:0 0 0 4px rgba(173,98,71,.12)}.taxonomy-audit strong{color:inherit}.taxonomy-audit details{margin-top:5px}.taxonomy-audit summary{cursor:pointer;font-weight:800}.taxonomy-audit code{font:700 9px var(--mono)}\n.explorer{padding:34px 0 70px}.search-card{background:#fff;border:1px solid rgba(16,47,69,.13);border-radius:22px;box-shadow:var(--shadow);padding:24px}.search-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:end}.field{position:relative;display:grid;gap:7px}.field>span,.selector label{font-size:10px;font-weight:800;color:#4f636d}.search-wrap{position:relative}.search-wrap input{width:100%;height:50px;border:1px solid #c7d2d0;border-radius:13px;padding:0 44px 0 15px;background:#fff;outline:none}.search-wrap input:focus,.selector select:focus{border-color:var(--theme);box-shadow:0 0 0 3px rgba(173,98,71,.11)}.search-icon{position:absolute;right:15px;top:50%;transform:translateY(-50%);color:var(--muted)}.clear{height:42px;border:1px solid #cbd4d2;background:#fff;border-radius:11px;padding:0 14px;font-size:11px;font-weight:800}.clear:hover{background:#f8faf9}.results{position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:30;background:#fff;border:1px solid #cbd4d2;border-radius:14px;box-shadow:0 18px 45px rgba(16,47,69,.17);max-height:360px;overflow:auto;padding:6px}.result{width:100%;display:grid;grid-template-columns:90px 1fr auto;gap:10px;align-items:center;text-align:left;background:transparent;border:0;border-radius:10px;padding:11px}.result:hover{background:#f4f7f5}.result-code{font:800 11px var(--mono);color:var(--theme)}.result-name{font-size:12px;line-height:1.35}.result-level{font-size:9px;color:var(--muted)}.quick-area{margin-top:14px}.quick-title{font-size:10px;font-weight:800;color:#4f636d;margin-bottom:8px}.quick{display:flex;flex-wrap:wrap;gap:8px}.quick button{display:inline-flex;align-items:center;gap:7px;border:1px solid #d1d9d7;background:#f8faf9;border-radius:999px;padding:7px 10px;font-size:10px;font-weight:750;max-width:340px}.quick button span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.quick button b{flex:0 0 auto;color:var(--theme);font-size:9px}.quick button:hover{background:var(--theme-soft);border-color:#d6b2a4}.selectors{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:22px;padding-top:20px;border-top:1px solid #e4e9e7}.selector{display:grid;gap:6px}.selector select{width:100%;height:43px;border:1px solid #cbd4d2;border-radius:11px;background:#fff;padding:0 11px;outline:none}.selector select:disabled{background:#f5f7f6;color:#9ba6a2}.pathbar{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-top:18px;padding:14px 16px;border-radius:14px;background:#f6f8f7}.crumbs{display:flex;flex-wrap:wrap;align-items:center;gap:6px}.crumb{border:0;background:transparent;padding:3px 0;font-size:10px;font-weight:750;color:#596b73}.crumb.current{color:var(--ink);font-weight:850}.sep{color:#a2adaa;font-size:10px}.node-status{white-space:nowrap;font-size:9px;font-weight:800;padding:6px 9px;border-radius:999px}.node-status.direct{background:#e4f1eb;color:#32654e}.node-status.nav{background:#f3e3da;color:#8b553f}\n.main-grid{display:grid;grid-template-columns:minmax(0,.96fr) minmax(0,1.04fr);gap:22px;margin-top:22px}.panel{min-width:0;background:#fff;border:1px solid rgba(16,47,69,.13);border-radius:20px;padding:22px;box-shadow:0 14px 44px rgba(16,47,69,.05)}.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.panel-head h2{margin:4px 0 4px;font-size:20px;letter-spacing:-.03em}.panel-head p{margin:0;color:var(--muted);font-size:11px;line-height:1.5}.mode-tabs,.switch{display:inline-flex;gap:4px;border:1px solid #d3dcda;padding:4px;border-radius:11px;background:#f7f9f8}.mode-tabs button,.switch button{border:0;background:transparent;border-radius:8px;padding:7px 9px;font-size:9px;font-weight:800;white-space:nowrap}.mode-tabs button.active,.switch button.active{background:#fff;box-shadow:0 2px 8px rgba(16,47,69,.08);color:var(--theme)}.mode-tabs button[disabled]{cursor:not-allowed;color:#9ca8a4}.lock{font-size:8px}\n.donut-layout{display:grid;grid-template-columns:minmax(240px,.8fr) minmax(250px,1.2fr);gap:18px;align-items:center}.donut-wrap{position:relative;aspect-ratio:1;max-width:340px;margin:auto;width:100%}.donut-wrap svg{width:100%;height:100%;overflow:visible}.donut-center{position:absolute;inset:25%;display:grid;place-content:center;text-align:center;pointer-events:none}.donut-center strong{font-size:24px;letter-spacing:-.04em}.donut-center span{font-size:9px;color:var(--muted);line-height:1.35}.slice{transition:opacity .15s,stroke-width .15s;cursor:pointer}.slice:hover{opacity:.78}.child-list{display:grid;gap:6px;max-height:385px;overflow:auto;padding-right:3px}.child{border:1px solid #e0e6e4;background:#fff;border-radius:11px;padding:9px 10px;display:grid;grid-template-columns:56px minmax(0,1fr);gap:8px;text-align:left;align-items:start}.child:hover{border-color:#c9d6d2;background:#f9fbfa}.child code{font:800 10px var(--mono);color:var(--theme)}.child span{font-size:10px;line-height:1.35}.child em{font-style:normal;font-size:8px;padding:4px 6px;border-radius:999px;background:#edf3f0;color:#426251}.child em.navonly{background:#f3e7e0;color:#8b604c}.empty{border:1px dashed #ccd6d3;border-radius:14px;padding:24px;color:var(--muted);font-size:11px;line-height:1.55;text-align:center}\n.right-head{align-items:center}.tab-switch{display:inline-flex;border:1px solid #d2dbd9;background:#f7f9f8;border-radius:11px;padding:4px;gap:3px}.tab-switch button{border:0;background:transparent;padding:8px 12px;border-radius:8px;font-size:10px;font-weight:850}.tab-switch button.active{background:var(--ink);color:#fff}.selected-title{padding:14px 15px;background:#f6f8f7;border-radius:13px;margin-bottom:15px}.selected-title code{font:800 10px var(--mono);color:var(--theme)}.selected-title h3{font-size:15px;margin:5px 0 3px;line-height:1.25}.selected-title p{font-size:9px;color:var(--muted);margin:0}.hierarchy-context{display:grid;gap:5px;margin-top:11px;padding-top:10px;border-top:1px solid #e2e7e5}.hierarchy-row{display:grid;grid-template-columns:72px 66px minmax(0,1fr);gap:8px;align-items:start;font-size:9px;line-height:1.35}.hierarchy-level{color:var(--muted);font-weight:750}.hierarchy-code{font:800 9px var(--mono);color:var(--theme)}.hierarchy-name{color:#344d5a}.hierarchy-row.current .hierarchy-name,.hierarchy-row.current .hierarchy-code{font-weight:850;color:var(--ink)}.metric-row{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:11px}.metric-row>span{font-size:9px;color:var(--muted);font-weight:800}.mini-switch{display:flex;gap:5px;flex-wrap:wrap}.mini-switch button{border:1px solid #d3dcda;background:#fff;border-radius:999px;padding:6px 8px;font-size:8px;font-weight:800}.mini-switch button.active{background:var(--theme-soft);border-color:#d5b0a1;color:#7f4d39}.lollipops{display:grid;gap:8px}.lrow{display:grid;grid-template-columns:112px minmax(120px,1fr) 64px;gap:10px;align-items:center;min-height:34px;border-radius:9px;padding:4px 5px}.lrow.clickable:hover,.lrow.selected{background:#f5f8f6}.lname{font-size:10px;font-weight:750}.track{height:2px;background:#dde4e1;position:relative}.stem{position:absolute;left:0;top:0;height:2px;background:var(--theme);width:var(--pct)}.dot{position:absolute;left:var(--pct);top:50%;width:10px;height:10px;border-radius:50%;background:var(--theme);transform:translate(-50%,-50%);border:2px solid #fff;box-shadow:0 0 0 1px var(--theme)}.lrow.zero .dot{background:#fff;box-shadow:0 0 0 1.5px var(--theme);left:0}.lrow.zero .stem{width:0}.lrow.nd .track{height:0;border-top:2px dotted #bdc8c4;background:none}.lrow.nd .dot,.lrow.nd .stem{display:none}.lvalue{text-align:right;font:800 10px var(--mono)}.lvalue small{display:block;font:600 7px var(--sans);color:var(--muted);margin-top:2px}.detail-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid #e1e7e5;margin-top:16px;padding-top:15px}.detail-heading h4{margin:0;font-size:11px}.town-select{border:1px solid #d1dad8;background:#fff;border-radius:9px;padding:6px 8px;font-size:9px}.kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:10px}.kpi{border:1px solid #e1e7e5;border-radius:11px;padding:10px;background:#fff;min-height:72px}.kpi span{display:block;color:var(--muted);font-size:8px;line-height:1.2}.kpi strong{display:block;margin-top:6px;font-size:15px;letter-spacing:-.03em}.kpi small{font-size:7px;color:#7b8983}.legend-note{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;font-size:8px;color:var(--muted)}.legend-note span{display:flex;align-items:center;gap:5px}.legend-dot{width:8px;height:8px;border-radius:50%;background:var(--theme)}.legend-zero{width:8px;height:8px;border-radius:50%;border:1.5px solid var(--theme);background:#fff}.legend-nd{width:12px;border-top:2px dotted #9ca9a4}\n.history-controls{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;margin-bottom:10px}.town-chips{display:flex;flex-wrap:wrap;gap:6px}.town-chip{border:1px solid #d4dcda;background:#fff;border-radius:999px;padding:6px 8px;font-size:8px;font-weight:800}.town-chip.off{opacity:.45}.history-tools{display:flex;gap:6px}.history-tools button{border:1px solid #d4dcda;background:#fff;border-radius:8px;padding:6px 8px;font-size:8px;font-weight:800}.history-chart{width:100%;min-height:330px;border:1px solid #e1e7e5;border-radius:13px;background:#fff;padding:8px}.history-chart svg{width:100%;height:auto;display:block}.gridline{stroke:#e4e9e7;stroke-width:1}.axistext{font-size:9px;fill:#78867f}.breakline{stroke:#ad7f54;stroke-width:1.5;stroke-dasharray:4 4}.breaktext{fill:#8a6542;font-size:8px;font-weight:800}.trendline{fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}.trenddot{stroke-width:1.5;fill:#fff}.history-foot{margin-top:10px;border-radius:10px;background:#f6f8f7;padding:10px 12px;font-size:9px;line-height:1.5;color:var(--muted)}.prehistory{display:inline-flex;align-items:center;gap:6px;margin-top:8px;font-size:8px;color:#8a9792}.prehistory button{border:1px solid #d6dddb;background:#f3f5f4;color:#a1aaa7;border-radius:7px;padding:5px 7px;cursor:not-allowed}\n.method{margin-top:22px;border:1px solid rgba(16,47,69,.12);border-radius:18px;background:#fff}.method summary{cursor:pointer;padding:16px 18px;font-size:11px;font-weight:850}.method-content{padding:0 18px 18px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.method-content div{background:#f7f9f8;border-radius:12px;padding:12px}.method-content strong{font-size:10px}.method-content p{font-size:9px;color:var(--muted);line-height:1.55;margin:6px 0 0}\n@media(max-width:980px){.main-grid{grid-template-columns:1fr}.donut-layout{grid-template-columns:.85fr 1.15fr}.selectors{grid-template-columns:repeat(2,1fr)}}\n@media(max-width:680px){.page{width:min(100% - 28px,1240px)}.site-head{min-height:62px}.proto-tag{display:none}.hero{grid-template-columns:44px 1fr;gap:14px;padding:30px 0 34px}.hero-symbol{width:44px;height:44px;border-radius:13px 13px 13px 4px;font-size:13px}.hero h1{font-size:47px}.hero p{font-size:13px}.search-card,.panel{padding:16px;border-radius:17px}.search-top{grid-template-columns:1fr}.clear{justify-self:start}.selectors{grid-template-columns:1fr}.pathbar{align-items:flex-start;display:grid}.node-status{justify-self:start}.donut-layout{grid-template-columns:1fr}.donut-wrap{max-width:285px}.child-list{max-height:300px}.panel-head{display:grid}.right-head{display:flex}.kpis{grid-template-columns:repeat(2,1fr)}.lrow{grid-template-columns:92px minmax(80px,1fr) 58px}.method-content{grid-template-columns:1fr}.brand span:last-child{font-size:12px}}\n";
  const HERO = "<section class=\"hero\">\n<div class=\"hero-symbol\">AT</div>\n<div><span class=\"overline\">Economia · Registro Imprese</span><h1>Atlante delle attività economiche</h1><p>Esplora la presenza delle attività economiche nei sette Comuni della Versilia, dalla Sezione alla massima granularità disponibile. La classificazione orienta la navigazione; i confronti usano sempre il valore del codice esatto restituito dalla fonte.</p><div class=\"hero-meta\"><span class=\"meta-pill\"><strong>1.228</strong> codici interrogabili</span><span class=\"meta-pill\"><strong>2014–2025</strong> serie principale</span><span class=\"meta-pill\"><strong>7 Comuni</strong> + Toscana</span><span class=\"meta-pill\">ATECO 2007 · agg. 2022</span></div></div>\n</section>";
  const EXPLORER = "<section class=\"explorer\">\n<div class=\"search-card\">\n<div class=\"search-top\">\n<label class=\"field\"><span>Cerca attività o codice ATECO</span><div class=\"search-wrap\"><input autocomplete=\"off\" id=\"search\" placeholder=\"es. nautica, marmo, stabilimenti balneari, 30.12\"/><span class=\"search-icon\">⌕</span><div class=\"results\" hidden=\"\" id=\"results\"></div></div></label>\n<button class=\"clear\" id=\"clear\">Pulisci selezione</button>\n</div>\n<div class=\"quick-area\"><div class=\"quick-title\">Top 5 attività per UL attive in Versilia · 2025</div><div class=\"quick\">\n<button data-code=\"I 561011\" title=\"56.10.11 · Ristorazione con somministrazione\"><span>Ristorazione con somministrazione</span><b>1.814 UL</b></button>\n<button data-code=\"F 433901\" title=\"43.39.01 · Attività non specializzate di lavori edili (muratori)\"><span>Lavori edili non specializzati (muratori)</span><b>698 UL</b></button>\n<button data-code=\"F 412\" title=\"41.2 · Costruzione di edifici residenziali e non residenziali\"><span>Costruzione di edifici</span><b>663 UL</b></button>\n<button data-code=\"I 563\" title=\"56.3 · Bar e altri esercizi simili senza cucina\"><span>Bar e altri esercizi senza cucina</span><b>585 UL</b></button>\n<button data-code=\"L 6831\" title=\"68.31 · Attività di mediazione immobiliare\"><span>Mediazione immobiliare</span><b>461 UL</b></button>\n</div></div>\n<div class=\"selectors\" id=\"selectors\"></div>\n<div class=\"pathbar\"><div class=\"crumbs\" id=\"crumbs\"></div><span class=\"node-status nav\" id=\"status\">Navigazione</span></div>\n</div>\n<div class=\"main-grid\">\n<section class=\"panel\">\n<div class=\"panel-head\"><div><span class=\"overline\">Esplorazione gerarchica</span><h2>Naviga la classificazione</h2><p>Click sul grafico, sulla lista o sui selettori: tutto resta sincronizzato. I passaggi con una sola scelta vengono attraversati automaticamente.</p></div><div class=\"mode-tabs\"><button class=\"active\" id=\"modeComposition\">Composizione %</button><button id=\"modeNavigation\">Navigazione</button></div></div>\n<div class=\"donut-layout\"><div class=\"donut-wrap\"><svg aria-label=\"Navigatore gerarchico ATECO\" id=\"donut\" viewbox=\"0 0 320 320\"></svg><div class=\"donut-center\" id=\"donutCenter\"></div></div><div class=\"child-list\" id=\"children\"></div></div>\n</section>\n<section class=\"panel\" id=\"analysisPanel\">\n<div class=\"panel-head right-head\"><div><span class=\"overline\">Confronto territoriale</span><h2 id=\"analysisHeading\">Il nodo nei sette Comuni</h2></div><div class=\"tab-switch\"><button class=\"active\" id=\"tabCurrent\">Attuale</button><button id=\"tabHistory\">Storico</button></div></div>\n<div id=\"analysis\"></div>\n</section>\n</div>\n<details class=\"method\"><summary>Fonte e metodo</summary><div class=\"method-content\"><div><strong>Fonte</strong><p>Banca dati Imprese della Regione Toscana / Registro Imprese InfoCamere. Classificazione ATECO 2007 aggiornamento 2022.</p></div><div><strong>Lettura dei valori</strong><p>0 indica un valore osservato pari a zero; n.d. indica un dato non restituito o non disponibile. La specializzazione confronta il peso dell’attività nel Comune con quello osservato in Toscana.</p></div><div><strong>Ambito</strong><p>L’Atlante descrive presenza, specializzazione, peso regionale e artigianato. Gli addetti restano nella lettura Istat ASIA.</p></div></div></details>\n</section>";
  class OVEconomyAtlas extends HTMLElement {
    async connectedCallback() {
      if (this.shadowRoot) return;
      const root = this.attachShadow({mode:'open'});
      root.innerHTML = `<style>:host{display:block}.atlas-loading{font:600 14px/1.4 system-ui;padding:28px 0;color:#61717b}</style><div class="atlas-loading" role="status">Caricamento Atlante…</div>`;
      try { await ensureAtlasData(); }
      catch(error){ console.error(error); root.innerHTML=`<div role="alert" style="padding:24px 0;font:600 14px/1.5 system-ui;color:#8b2f2f">Atlante temporaneamente non disponibile.</div>`; return; }
      root.innerHTML = `<style>${STYLE}
        :host{display:block;--paper:#f4eee2;--surface:#fff;--ink:#102f45;--muted:#61717b;--blue:#145b78;--blue-soft:#e4eff2;--theme:#ad6247;--theme-soft:#f3e3da;--line:#d5dddb;--sage:#5f8b78;--gold:#c89b3c;--shadow:0 20px 60px rgba(16,47,69,.08);--radius:18px;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
        .site-header,.breadcrumbs{display:none!important}
        .page{width:100%;}
        .hero{padding-top:24px;}
        :host([embedded]) .hero{display:none!important}
        :host([embedded]) .explorer{padding-top:0}
        :host([mode="town"]) .hero{grid-template-columns:64px 1fr;padding:28px 0 32px;}
        :host([mode="town"]) .hero-symbol{width:56px;height:56px;border-radius:16px 16px 16px 6px;font-size:15px}
        :host([mode="town"]) h1{font-size:clamp(32px,5vw,54px);line-height:.96}
        :host([mode="town"]) .hero p{font-size:14px;}
      </style><div class="page">${HERO}${EXPLORER}</div>`;
      const townSlug=this.getAttribute('town')||'';
      if(townSlug){
        this.setAttribute('mode','town');
        const townName={'camaiore':'Camaiore','forte-dei-marmi':'Forte dei Marmi','massarosa':'Massarosa','pietrasanta':'Pietrasanta','seravezza':'Seravezza','stazzema':'Stazzema','viareggio':'Viareggio'}[townSlug]||townSlug;
        const title=root.querySelector('.hero h1');
        if(title) title.textContent=`Atlante delle attività economiche · ${townName}`;
        const intro=root.querySelector('.hero p');
        if(intro) intro.textContent=`Esplora le attività economiche di ${townName} dalla Sezione alla massima granularità disponibile, mantenendo il confronto con gli altri Comuni della Versilia e con la Toscana.`;
        const over=root.querySelector('.hero .overline');
        if(over) over.textContent=`Economia · ${townName} · Registro Imprese`;
      }
      this._init(root);
    }
    _init(root) {

/* ov-site-tooltip-contract */
const atlasTooltipStyle=document.createElement('style');
atlasTooltipStyle.textContent=`.ov-site-tooltip{position:fixed;z-index:10000;pointer-events:none;min-width:132px;max-width:230px;padding:8px 12px;border-radius:8px;background:var(--ink);color:#fff;box-shadow:0 6px 9px rgba(16,47,69,.18);font-family:var(--font-geist-sans,Geist,Inter,ui-sans-serif,system-ui);line-height:1.25}.ov-site-tooltip[hidden]{display:none!important}.ov-site-tooltip .chart-tooltip-year{display:block;opacity:.75;font-size:9px;font-weight:600}.ov-site-tooltip .chart-tooltip-value{display:block;margin-top:3px;font-size:11px;font-weight:800}.lrow[data-atlas-tooltip]{position:relative;outline:none}.lrow[data-atlas-tooltip]:focus-visible{box-shadow:0 0 0 2px var(--blue)}.trenddot[data-atlas-tooltip]:focus,.slice[data-atlas-tooltip]:focus{outline:none}`;
root.prepend(atlasTooltipStyle);
function ensureAtlasTooltip(){let tip=root.querySelector('.ov-site-tooltip');if(!tip){tip=document.createElement('div');tip.className='ov-site-tooltip';tip.hidden=true;tip.innerHTML='<span class="chart-tooltip-year"></span><strong class="chart-tooltip-value"></strong>';root.appendChild(tip)}return tip}
function hideAtlasTooltip(){const tip=root.querySelector('.ov-site-tooltip');if(tip)tip.hidden=true}
function showAtlasTooltip(target){const tip=ensureAtlasTooltip();tip.querySelector('.chart-tooltip-year').textContent=target.dataset.tipTitle||'';tip.querySelector('.chart-tooltip-value').textContent=target.dataset.tipValue||'';tip.hidden=false;tip.style.left='0px';tip.style.top='0px';const r=target.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;let x=Math.max(8,Math.min(window.innerWidth-w-8,r.left+r.width/2-w/2));let y=r.top-h-10;if(y<8)y=Math.min(window.innerHeight-h-8,r.bottom+10);tip.style.left=`${Math.round(x)}px`;tip.style.top=`${Math.round(y)}px`}
function wireAtlasTooltips(){root.querySelectorAll('[data-atlas-tooltip]').forEach(el=>{if(el.dataset.atlasTooltipWired==='1')return;el.dataset.atlasTooltipWired='1';if(!el.hasAttribute('tabindex'))el.setAttribute('tabindex','0');el.addEventListener('mouseenter',()=>showAtlasTooltip(el));el.addEventListener('mouseleave',hideAtlasTooltip);el.addEventListener('focus',()=>showAtlasTooltip(el));el.addEventListener('blur',hideAtlasTooltip);el.addEventListener('keydown',e=>{if(e.key==='Escape'){hideAtlasTooltip();el.blur()}})});}

const LABELS={"A":"Agricoltura, silvicoltura e pesca","B":"Estrazione di minerali da cave e miniere","C":"Attività manifatturiere","D":"Fornitura di energia elettrica, gas, vapore e aria condizionata","E":"Fornitura di acqua; reti fognarie, gestione rifiuti e risanamento","F":"Costruzioni","G":"Commercio all'ingrosso e al dettaglio; riparazione di autoveicoli e motocicli","H":"Trasporto e magazzinaggio","I":"Servizi di alloggio e ristorazione","J":"Servizi di informazione e comunicazione","K":"Attività finanziarie e assicurative","L":"Attività immobiliari","M":"Attività professionali, scientifiche e tecniche","N":"Noleggio, agenzie di viaggio, servizi di supporto alle imprese","O":"Amministrazione pubblica e difesa","P":"Istruzione","Q":"Sanità e assistenza sociale","R":"Attività artistiche, sportive, di intrattenimento e divertimento","S":"Altre attività di servizi","T":"Attività di famiglie e convivenze come datori di lavoro","U":"Organizzazioni ed organismi extraterritoriali","C 30":"Fabbricazione di altri mezzi di trasporto","C 301":"Costruzione di navi e imbarcazioni","C 3011":"Costruzione di navi e di strutture galleggianti","C 3012":"Costruzione di imbarcazioni da diporto e sportive","C 33":"Riparazione, manutenzione ed installazione di macchine ed apparecchiature","C 331":"Riparazione e manutenzione di prodotti in metallo, macchine ed apparecchiature","C 3315":"Riparazione e manutenzione di navi e imbarcazioni","C 23":"Fabbricazione di altri prodotti della lavorazione di minerali non metalliferi","C 237":"Taglio, modellatura e finitura di pietre","C 2370":"Taglio, modellatura e finitura di pietre","C 23701":"Segagione e lavorazione delle pietre e del marmo","C 23702":"Lavorazione artistica del marmo e di altre pietre affini, lavori in mosaico","B 08":"Altre attività di estrazione di minerali da cave e miniere","B 081":"Estrazione di pietra, sabbia e argilla","B 0811":"Estrazione di pietre ornamentali e da costruzione, calcare, gesso, creta e ardesia","R 93":"Attività sportive, di intrattenimento e di divertimento","R 932":"Attività ricreative e di divertimento","R 9329":"Altre attività ricreative e di divertimento","R 93292":"Gestione di stabilimenti balneari: marittimi, lacuali e fluviali","G 47":"Commercio al dettaglio, escluso quello di autoveicoli e motocicli","G 477":"Commercio al dettaglio di altri prodotti in esercizi specializzati","G 4778":"Commercio al dettaglio di altri prodotti in esercizi specializzati","G 47783":"Commercio al dettaglio di oggetti d'arte, culto e decorazione","G 477831":"Commercio al dettaglio di oggetti d'arte, incluse le gallerie d'arte","A 01":"Coltivazioni agricole e produzione di prodotti animali, caccia e servizi connessi","A 02":"Silvicoltura ed utilizzo di aree forestali","A 03":"Pesca e acquacoltura","B 05":"Estrazione di carbone","B 06":"Estrazione di petrolio greggio e gas naturale","B 07":"Estrazione di minerali metalliferi","B 09":"Servizi di supporto all’estrazione","C 10":"Industrie alimentari","C 11":"Industria delle bevande","C 13":"Industrie tessili","C 14":"Confezione di articoli di abbigliamento","C 16":"Industria del legno e dei prodotti in legno","C 18":"Stampa e riproduzione di supporti registrati","C 20":"Fabbricazione di prodotti chimici","C 21":"Fabbricazione di prodotti farmaceutici","C 22":"Fabbricazione di articoli in gomma e materie plastiche","C 24":"Metallurgia","C 25":"Fabbricazione di prodotti in metallo","C 26":"Fabbricazione di computer, prodotti di elettronica e ottica","C 27":"Fabbricazione di apparecchiature elettriche","C 28":"Fabbricazione di macchinari ed apparecchiature nca","C 29":"Fabbricazione di autoveicoli, rimorchi e semirimorchi","C 31":"Fabbricazione di mobili","C 32":"Altre industrie manifatturiere","F 41":"Costruzione di edifici","F 42":"Ingegneria civile","F 43":"Lavori di costruzione specializzati","G 45":"Commercio e riparazione di autoveicoli e motocicli","G 46":"Commercio all'ingrosso","I 55":"Alloggio","I 56":"Attività dei servizi di ristorazione","L 68":"Attività immobiliari","M 69":"Attività legali e contabilità","M 71":"Attività degli studi di architettura e ingegneria","N 77":"Attività di noleggio e leasing operativo","N 79":"Agenzie di viaggio e tour operator","Q 86":"Assistenza sanitaria","R 90":"Attività creative, artistiche e di intrattenimento","S 96":"Altre attività di servizi per la persona"};
// Etichette locali minime per il primo rendering; la tassonomia completa viene caricata dalla fonte ufficiale ISTAT.
// Le altre etichette vengono idratate dalla tassonomia ufficiale; in assenza di rete
// NON si eredita mai la descrizione della sezione, per evitare etichette false/generiche.
Object.assign(LABELS,{
  'L 68':'Attività immobiliari',
  'L 681':'Compravendita di beni immobili effettuata su beni propri',
  'L 6810':'Compravendita di beni immobili effettuata su beni propri',
  'L 68100':'Compravendita di beni immobili effettuata su beni propri',
  'L 682':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 6820':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 68200':'Affitto e gestione di immobili di proprietà o in leasing',
  'L 682001':'Locazione immobiliare di beni propri o in leasing (affitto)',
  'L 682002':'Affitto di aziende',
  'L 683':'Attività immobiliari per conto terzi',
  'L 6831':'Attività di mediazione immobiliare',
  'L 68310':'Attività di mediazione immobiliare',
  'L 683100':'Attività di mediazione immobiliare',
  'L 6832':'Gestione di immobili per conto terzi',
  'L 68320':'Amministrazione di condomini e gestione di beni immobili per conto terzi',
  'L 683200':'Amministrazione di condomini e gestione di beni immobili per conto terzi'
});
const LEVELS={0:'Sezione',2:'Divisione',3:'Gruppo',4:'Classe',5:'Categoria',6:'Sottocategoria'};
const PALETTE=['#ad6247','#145b78','#5f8b78','#c89b3c','#6f6690','#3e7180','#b65358','#6b7b4d','#9a6b18','#587489','#8c5e76','#477b69'];
const towns=DATA.t.map((x,i)=>({slug:x[0],name:x[1],i}));
const years=DATA.y; const latest=years.length-1;
const exact=new Map();
DATA.c.forEach(r=>exact.set(r[0],r));
const sections=Object.entries(DATA.s);
const nodes=new Map();
function displayCode(d){if(!d)return'';if(d.length===2)return d;if(d.length===3)return d.slice(0,2)+'.'+d.slice(2);if(d.length===4)return d.slice(0,2)+'.'+d.slice(2);if(d.length===5)return d.slice(0,2)+'.'+d.slice(2,4)+'.'+d.slice(4);return d.slice(0,2)+'.'+d.slice(2,4)+'.'+d.slice(4)}
function key(sec,d=''){return d?sec+' '+d:sec}
function nodeLabel(sec,d=''){return LABELS[key(sec,d)]||(d?'':(LABELS[sec]||''))}
function ensure(sec,d=''){let k=key(sec,d);if(!nodes.has(k))nodes.set(k,{key:k,sec,d,label:nodeLabel(sec,d),hasData:d?exact.has(k):false});return nodes.get(k)}
sections.forEach(([s])=>ensure(s,''));
DATA.c.forEach(r=>{let m=r[0].match(/^([A-Z])\s+(\d+)$/);if(!m)return;let [_,s,d]=m;ensure(s,'');for(let L of [2,3,4,5,6])if(d.length>=L)ensure(s,d.slice(0,L));});
function childNodes(sec,d=''){
  if(!sec)return sections.map(([s])=>ensure(s,'')).filter(n=>[...nodes.values()].some(x=>x.sec===n.sec&&x.d));
  const next={0:2,2:3,3:4,4:5,5:6}[d.length]; if(!next)return[];
  const seen=new Map(); for(const n of nodes.values()){if(n.sec!==sec||n.d.length!==next)continue;if(d&& !n.d.startsWith(d))continue;seen.set(n.d,n)}
  return [...seen.values()].sort((a,b)=>a.d.localeCompare(b.d,'it',{numeric:true}));
}
function ancestors(sec,d){let arr=[];if(!sec)return arr;arr.push(ensure(sec,''));for(let L of [2,3,4,5,6])if(d.length>=L)arr.push(ensure(sec,d.slice(0,L)));return arr}
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[’']/g,' ').replace(/\s+/g,' ').trim()}
const aliases={nautica:['C 3012','C 3315'],marmo:['B 0811','C 23701','C 23702'],balneari:['R 93292'],'stabilimenti balneari':['R 93292'],'gallerie d arte':['G 477831'],'galleria d arte':['G 477831']};

const taxonomyState={status:'loaded',source:'ISTAT ATECO 2007–2022',missing:[],resolved:0,total:0,error:''};
function applyEmbeddedTaxonomy(){
  let resolved=0;
  for(const n of nodes.values()){
    const code=n.d?displayCode(n.d):n.sec;
    const label=EMBEDDED_ATECO[code]||'';
    if(label){n.label=label;LABELS[n.key]=label;resolved++;}
  }
  taxonomyState.total=nodes.size;taxonomyState.resolved=resolved;
  taxonomyState.missing=[...nodes.values()].filter(n=>!String(n.label||'').trim());
  taxonomyState.status=taxonomyState.missing.length?'incomplete':'loaded';
}
function setTaxonomyAudit(){return;}

function taxonomyReady(){return taxonomyState.status==='loaded'&&!taxonomyState.missing.length}
function rawToPretty(raw){let m=raw.match(/^([A-Z])\s+(\d+)$/);return m?m[1]+' · '+displayCode(m[2]):raw}
function fmt(v,d=0){if(v===null||v===undefined||Number.isNaN(v))return'n.d.';return new Intl.NumberFormat('it-IT',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v)}
const initialTown=root.host?.getAttribute('town')||'';const initialTownMeta=towns.find(t=>t.slug===initialTown)||null;const state={sec:'',d:'',tab:'current',metric:'active',detailTown:initialTown,visible:new Set(initialTown?[initialTown]:towns.map(t=>t.slug)),leftMode:'composition'};
const $=s=>root.querySelector(s);
function currentNode(){if(!state.sec)return null;return ensure(state.sec,state.d)}
function descendSingleton(sec,d=''){
  let cur=d,guard=0;
  while(sec&&guard++<8){
    const kids=childNodes(sec,cur);
    if(kids.length!==1)break;
    cur=kids[0].d;
  }
  return cur;
}
function taxonomyReady(){return taxonomyState.status==='loaded'&&!taxonomyState.missing.length}
function selectNode(sec,d='',autoAdvance=true){state.sec=sec;state.d=autoAdvance&&sec?descendSingleton(sec,d):d;state.detailTown=initialTown||'';renderAll()}
function clearAll(){state.sec='';state.d='';state.tab='current';state.metric='active';state.detailTown=initialTown||'';$('#search').value='';$('#results').hidden=true;renderAll()}
function renderSelectors(){
  const taxonomyLocked=false;
  const defs=[['Sezione',0],['Divisione',2],['Gruppo',3],['Classe',4],['Categoria',5],['Sottocategoria',6]];let out='';
  defs.forEach(([name,L],idx)=>{
    let opts=[],disabled=false,selected='';
    if(L===0){opts=sections.map(([s])=>ensure(s,''));selected=state.sec}
    else{
      let parentLen={2:0,3:2,4:3,5:4,6:5}[L];let parentD=parentLen?state.d.slice(0,parentLen):'';
      if(!state.sec || (parentLen&&state.d.length<parentLen)){disabled=true}else opts=childNodes(state.sec,parentD);
      if(state.d.length>=L)selected=state.d.slice(0,L);
    }
    disabled=disabled||taxonomyLocked;
    let ph=`${name}`;out+=`<div class="selector"><label>${name}</label><select data-level="${L}" ${disabled?'disabled':''}><option value="">${L===0?'Tutte le sezioni':'—'}</option>${opts.map(n=>`<option value="${L===0?n.sec:n.d}" ${selected===(L===0?n.sec:n.d)?'selected':''} ${L===0&&!childNodes(n.sec,'').length?'disabled':''}>${L===0?n.sec:displayCode(n.d)}${n.label?' · '+escapeHtml(n.label):''}</option>`).join('')}</select></div>`;
  });
  $('#selectors').innerHTML=out;
  $('#selectors').querySelectorAll('select').forEach(sel=>sel.onchange=()=>{
    const L=+sel.dataset.level,v=sel.value;
    if(L===0){state.sec=v;state.d=v?descendSingleton(v,''):''}
    else if(v){state.d=descendSingleton(state.sec,v)}
    else{const parentLen={2:0,3:2,4:3,5:4,6:5}[L];state.d=parentLen?state.d.slice(0,parentLen):''}
    state.detailTown='';renderAll();
  });
}
function escapeHtml(s){return String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}
function renderCrumbs(){
  let parts=[`<button class="crumb ${!state.sec?'current':''}" data-root="1">Tutte le attività</button>`];
  if(state.sec){for(const n of ancestors(state.sec,state.d)){parts.push('<span class="sep">›</span>');parts.push(`<button class="crumb ${n.d===state.d?'current':''}" data-sec="${n.sec}" data-d="${n.d}" title="${escapeHtml(n.label)}">${n.d?displayCode(n.d):n.sec}</button>`);}}
  $('#crumbs').innerHTML=parts.join('');$('#crumbs').querySelectorAll('button').forEach(b=>b.onclick=()=>b.dataset.root?clearAll():selectNode(b.dataset.sec,b.dataset.d,false));
  let n=currentNode(),st=$('#status');if(n&&n.hasData){st.className='node-status direct';st.textContent='Valore disponibile'}else{st.className='node-status nav';st.textContent=state.sec?'Continua a esplorare':'Navigazione ATECO'}
}
function arcPath(cx,cy,r,a0,a1){let x0=cx+r*Math.cos(a0),y0=cy+r*Math.sin(a0),x1=cx+r*Math.cos(a1),y1=cy+r*Math.sin(a1),large=(a1-a0)>Math.PI?1:0;return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`}
function renderDonut(){
  const mode=state.leftMode||'composition';
  root.querySelector('#modeComposition')?.classList.toggle('active',mode==='composition');
  root.querySelector('#modeNavigation')?.classList.toggle('active',mode==='navigation');
  let kids=childNodes(state.sec,state.d),svg=$('#donut'),center=$('#donutCenter');svg.innerHTML='';
  if(mode==='navigation'){
    if(!kids.length){svg.innerHTML='<circle cx="160" cy="160" r="118" fill="none" stroke="#e4e9e7" stroke-width="36"/><circle cx="160" cy="160" r="112" fill="none" stroke="#ad6247" stroke-width="2" stroke-dasharray="3 6"/>';center.innerHTML=`<strong>${state.d?displayCode(state.d):state.sec||'—'}</strong><span>massima granularità<br>disponibile</span>`;$('#children').innerHTML='<div class="empty">Non ci sono livelli successivi nel set di codici disponibile.</div>';return;}
    const gap=Math.min(.025,0.42/kids.length),step=Math.PI*2/kids.length,r=116;
    kids.forEach((n,i)=>{let a0=-Math.PI/2+i*step+gap,a1=-Math.PI/2+(i+1)*step-gap;let p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',arcPath(160,160,r,a0,a1));p.setAttribute('fill','none');p.setAttribute('stroke',PALETTE[i%PALETTE.length]);p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.setAttribute('data-atlas-tooltip','1');p.dataset.tipTitle=n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`;p.dataset.tipValue=n.label||'';p.setAttribute('aria-label',`${p.dataset.tipTitle}: ${p.dataset.tipValue}`);p.onclick=()=>selectNode(n.sec,n.d);p.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectNode(n.sec,n.d)}};svg.appendChild(p)});
    let here=currentNode();center.innerHTML=state.sec?`<strong>${state.d?displayCode(state.d):state.sec}</strong><span>${escapeHtml(here?.label||'')}<br><b>${kids.length}</b> voci successive</span>`:`<strong>${kids.length}</strong><span>sezioni navigabili<br>su ${DATA.c.length.toLocaleString('it-IT')} codici</span>`;
    $('#children').innerHTML=kids.map(n=>`<button class="child" data-sec="${n.sec}" data-d="${n.d}"><code>${n.d?displayCode(n.d):n.sec}</code><span>${escapeHtml(n.label||'')}</span></button>`).join('');
    $('#children').querySelectorAll('.child').forEach(b=>b.onclick=()=>selectNode(b.dataset.sec,b.dataset.d));
    return;
  }
  const items=compositionChildren();
  const usable=items.filter(x=>x.value!==null);
  const total=sumNullable(usable.map(x=>x.value));
  if(!usable.length || total===null || total<=0){
    svg.innerHTML='<circle cx="160" cy="160" r="118" fill="none" stroke="#e4e9e7" stroke-width="36"/><circle cx="160" cy="160" r="112" fill="none" stroke="#ad6247" stroke-width="2" stroke-dasharray="3 6"/>';
    center.innerHTML=`<strong>${state.d?displayCode(state.d):state.sec||'Versilia'}</strong><span>nessuna UL attiva<br>aggregabile</span>`;
    $('#children').innerHTML='<div class="empty">Non ci sono valori aggregabili per la composizione percentuale a questo livello.</div>';
    return;
  }
  let cursor=-Math.PI/2;
  usable.forEach((item,i)=>{
    const pct=item.value/total,span=pct*Math.PI*2,gap=Math.min(.02,0.35/usable.length),a0=cursor+gap,a1=cursor+span-gap;cursor+=span;
    if(a1<=a0)return;
    let p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',arcPath(160,160,116,a0,a1));p.setAttribute('fill','none');p.setAttribute('stroke',PALETTE[i%PALETTE.length]);p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.setAttribute('data-atlas-tooltip','1');
    p.dataset.tipTitle=item.node.d?`${item.node.sec} · ${displayCode(item.node.d)}`:`Sezione ${item.node.sec}`;p.dataset.tipValue=`${fmt(item.value)} UL · ${fmt(pct*100,1)}%`;p.setAttribute('aria-label',`${p.dataset.tipTitle}: ${item.node.label||''} — ${p.dataset.tipValue}`);
    p.onclick=()=>selectNode(item.node.sec,item.node.d);p.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectNode(item.node.sec,item.node.d)}};svg.appendChild(p);
  });
  const totalCurrent=compositionTotalForCurrent();
  const here=currentNode();
  center.innerHTML=state.sec
    ?`<strong>${displayCode(state.d)}</strong><span>${escapeHtml(here?.label||'')}<br><b>${fmt(totalCurrent)}</b> UL attive</span>`
    :`<strong>Versilia</strong><span>composizione per sezione<br><b>${fmt(total)}</b> UL attive</span>`;
  $('#children').innerHTML=items.map((item,idx)=>{
    const v=item.value,p=v===null||total===null||total===0?null:(v/total*100); const stateClass=v===null?'nd':v===0?'zero':'';
    return `<button class="child ${stateClass}" data-sec="${item.node.sec}" data-d="${item.node.d}"><code>${item.node.d?displayCode(item.node.d):item.node.sec}</code><span>${escapeHtml(item.node.label||'')}</span><small>${v===null?'n.d.':fmt(v)+' UL · '+fmt(p,1)+'%'}</small></button>`;
  }).join('');
  $('#children').querySelectorAll('.child').forEach(b=>b.onclick=()=>selectNode(b.dataset.sec,b.dataset.d));
}
function getRow(){let n=currentNode();return n&&n.hasData?exact.get(n.key):null}
function met(row,townIdx,yi=latest){let a=row[3+townIdx][0][yi],art=yi===latest?row[3+townIdx][1]:null,ra=row[1][yi],tt=DATA.tt[townIdx][yi],rt=DATA.rt[yi];let lq=(a===null||ra===null||!ra||!tt||!rt)?null:(a/tt)/(ra/rt);let weight=(a===null||ra===null||!ra)?null:a/ra*100;let share=(a===null||art===null)?null:(a===0?(art===0?0:null):art/a*100);return{a,art,ra,lq,weight,share}}
function metricValue(m){return state.metric==='active'?m.a:state.metric==='lq'?m.lq:m.weight}
function metricFmt(v){if(v===null)return'n.d.';if(state.metric==='active')return fmt(v,0);if(state.metric==='lq')return fmt(v,2)+'×';return fmt(v,2)+'%'}
function metricUnit(){return state.metric==='active'?'UL':state.metric==='lq'?'LQ':'peso Toscana'}

const aggregateCache=new Map();
function sumNullable(values){
  let sum=0,has=false;
  values.forEach(v=>{if(v!==null&&v!==undefined){sum+=v;has=true;}});
  return has?sum:null;
}
function emptyAggregate(){return{vers:years.map(()=>null),region:years.map(()=>null),towns:towns.map(()=>years.map(()=>null)),art:towns.map(()=>null)};}
function aggregateNode(sec,d=''){
  const k=key(sec,d); if(aggregateCache.has(k)) return aggregateCache.get(k);
  const kids=childNodes(sec,d);
  let result;
  if(kids.length){
    const childAggs=kids.map(ch=>aggregateNode(ch.sec,ch.d));
    result={
      vers: years.map((_,yi)=>sumNullable(childAggs.map(a=>a.vers[yi]))),
      region: years.map((_,yi)=>sumNullable(childAggs.map(a=>a.region[yi]))),
      towns: towns.map((t,ti)=>years.map((_,yi)=>sumNullable(childAggs.map(a=>a.towns[ti][yi])))),
      art: towns.map((t,ti)=>sumNullable(childAggs.map(a=>a.art[ti])))
    };
  } else {
    const row=exact.get(k);
    if(!row){result=emptyAggregate();}
    else {
      const townsSeries=towns.map(t=>row[3+t.i][0].slice());
      result={
        vers: years.map((_,yi)=>sumNullable(townsSeries.map(series=>series[yi]))),
        region: row[1].slice(),
        towns: townsSeries,
        art: towns.map(t=>row[3+t.i][1])
      };
    }
  }
  aggregateCache.set(k,result);
  return result;
}
function compositionChildren(){
  const kids=state.sec?childNodes(state.sec,state.d):sections.map(([s])=>ensure(s,''));
  return kids.map(n=>{const agg=aggregateNode(n.sec,n.d);return {node:n,value:agg.vers[latest]};});
}
function compositionTotalForCurrent(){
  if(!state.sec){const items=compositionChildren();return sumNullable(items.map(x=>x.value));}
  return aggregateNode(state.sec,state.d).vers[latest];
}
function derivedMet(n,townIdx,yi=latest){
  const agg=aggregateNode(n.sec,n.d),a=agg.towns[townIdx][yi],art=yi===latest?agg.art[townIdx]:null,ra=agg.region[yi],tt=DATA.tt[townIdx][yi],rt=DATA.rt[yi];
  const lq=(a===null||ra===null||!ra||!tt||!rt)?null:(a/tt)/(ra/rt);
  const weight=(a===null||ra===null||!ra)?null:a/ra*100;
  const share=(a===null||art===null)?null:(a===0?(art===0?0:null):art/a*100);
  return{a,art,ra,lq,weight,share};
}

function renderCurrentDerived(n){
  let ms=towns.map(t=>({t,m:derivedMet(n,t.i)})),vals=ms.map(x=>metricValue(x.m)).filter(v=>v!==null),max=Math.max(1,...vals),auto=ms.filter(x=>x.m.a!==null).sort((a,b)=>(b.m.a??-1)-(a.m.a??-1))[0]?.t.slug||towns[0].slug;
  if(!state.detailTown||!towns.some(t=>t.slug===state.detailTown))state.detailTown=auto;
  let detail=ms.find(x=>x.t.slug===state.detailTown)||ms[0],dm=detail.m,total=compositionTotalForCurrent();
  return `<div class="selected-title"><code>${n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>${fmt(total)} UL attive in Versilia · anno 2025</p>${hierarchyContext(n)}</div>
  <div class="metric-row"><span>Metrica del confronto</span><div class="mini-switch"><button data-metric="active" class="${state.metric==='active'?'active':''}">UL attive</button><button data-metric="lq" class="${state.metric==='lq'?'active':''}">Specializzazione</button><button data-metric="weight" class="${state.metric==='weight'?'active':''}">Peso Toscana</button></div></div>
  <div class="lollipops">${ms.map(x=>{let v=metricValue(x.m),cl=v===null?'nd':v===0?'zero':'',pct=v===null||v===0?0:(v/max*100);return `<div class="lrow clickable ${cl} ${x.t.slug===state.detailTown?'selected':''}" data-town="${x.t.slug}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(x.t.name)}" data-tip-value="${escapeHtml(metricUnit()+': '+metricFmt(v))}" aria-label="${escapeHtml(x.t.name+': '+metricUnit()+' '+metricFmt(v))}"><div class="lname">${escapeHtml(x.t.name)}</div><div class="track"><span class="stem" style="--pct:${pct}%"></span><span class="dot" style="--pct:${pct}%"></span></div><div class="lvalue">${metricFmt(v)}<small>${metricUnit()}</small></div></div>`}).join('')}</div>
  <div class="legend-note"><span><i class="legend-dot"></i> valore positivo</span><span><i class="legend-zero"></i> zero osservato</span><span><i class="legend-nd"></i> n.d.</span></div>
  <div class="detail-heading"><h4>Dettaglio analitico</h4><select id="detailTown" class="town-select">${towns.map(t=>`<option value="${t.slug}" ${t.slug===state.detailTown?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select></div>
  <div class="kpis"><div class="kpi"><span>UL attive</span><strong>${fmt(dm.a)}</strong><small>2025</small></div><div class="kpi"><span>UL artigiane</span><strong>${fmt(dm.art)}</strong><small>${dm.share===null?'quota n.d.':fmt(dm.share,1)+'% del nodo'}</small></div><div class="kpi"><span>Specializzazione</span><strong>${dm.lq===null?'n.d.':fmt(dm.lq,2)+'×'}</strong><small>1× = Toscana</small></div><div class="kpi"><span>Peso regionale</span><strong>${dm.weight===null?'n.d.':fmt(dm.weight,2)+'%'}</strong><small>delle UL toscane</small></div><div class="kpi"><span>Riferimento Toscana</span><strong>${fmt(dm.ra)}</strong><small>UL attive · 2025</small></div><div class="kpi"><span>Quota artigiana</span><strong>${dm.share===null?'n.d.':fmt(dm.share,1)+'%'}</strong><small>nel Comune</small></div></div>`;
}
function renderHistoryDerived(n){
  const agg=aggregateNode(n.sec,n.d),W=760,H=350,L=48,R=20,T=26,B=44;let visible=towns.filter(t=>state.visible.has(t.slug));if(!visible.length){state.visible.add(towns[0].slug);visible=[towns[0]]}
  let all=[];visible.forEach(t=>years.forEach((yr,yi)=>{let v=agg.towns[t.i][yi];if(v!==null)all.push(v)}));let ymax=Math.max(1,...all);ymax=Math.ceil(ymax/10)*10;let x=i=>L+i/(years.length-1)*(W-L-R),y=v=>T+(1-v/ymax)*(H-T-B);
  let svg='';for(let j=0;j<=4;j++){let vv=ymax*(4-j)/4,yy=T+j*(H-T-B)/4;svg+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text class="axistext" x="${L-8}" y="${yy+3}" text-anchor="end">${fmt(vv,0)}</text>`}
  years.forEach((yr,i)=>{svg+=`<text class="axistext" x="${x(i)}" y="${H-14}" text-anchor="middle">${String(yr).slice(2)}</text>`});let bi=years.indexOf(2022);if(bi>=0){let bx=x(bi);svg+=`<rect x="${bx-6}" y="${T}" width="12" height="${H-T-B}" fill="#f3e3da" opacity=".55"/><line class="breakline" x1="${bx}" x2="${bx}" y1="${T}" y2="${H-B}"/><text class="breaktext" x="${bx+5}" y="${T+10}">ATECO 2022</text>`}
  visible.forEach(t=>{let pts=years.map((yr,yi)=>{let v=agg.towns[t.i][yi];return v===null?null:{x:x(yi),y:y(v),v,yr}}),color=PALETTE[t.i%PALETTE.length];for(const d of pathFromPoints(pts))svg+=`<path class="trendline" d="${d}" stroke="${color}"/>`;pts.filter(Boolean).forEach(p=>svg+=`<circle class="trenddot" cx="${p.x}" cy="${p.y}" r="3.2" stroke="${color}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(t.name+' · '+p.yr)}" data-tip-value="${escapeHtml(fmt(p.v)+' UL')}" aria-label="${escapeHtml(t.name+' · '+p.yr+': '+fmt(p.v)+' UL')}"></circle>`) });
  return `<div class="selected-title"><code>${n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>Serie annuale delle UL attive · 2014–2025</p>${hierarchyContext(n)}</div><div class="history-controls"><div class="town-chips">${towns.map(t=>`<button class="town-chip ${state.visible.has(t.slug)?'':'off'}" data-vtown="${t.slug}" style="border-color:${PALETTE[t.i%PALETTE.length]}">${escapeHtml(t.name)}</button>`).join('')}</div><div class="history-tools"><button id="allTowns">Tutti</button><button id="oneTown">Solo dettaglio</button></div></div><div class="history-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Serie storiche aggregate 2014-2025">${svg}</svg></div><div class="history-foot"><strong>2022.</strong> La linea evidenzia l’aggiornamento della classificazione ATECO.</div>`;
}
function hierarchyContext(n){
  if(!n)return'';
  return `<div class="hierarchy-context" aria-label="Percorso gerarchico ATECO">${ancestors(n.sec,n.d).map(a=>{
    const level=a.d?LEVELS[a.d.length]:'Sezione', code=a.d?displayCode(a.d):a.sec, current=a.key===n.key?' current':'';
    return `<div class="hierarchy-row${current}"><span class="hierarchy-level">${level}</span><span class="hierarchy-code">${code}</span><span class="hierarchy-name">${escapeHtml(a.label)}</span></div>`;
  }).join('')}</div>`;
}
function renderCurrent(row,n){
  let ms=towns.map(t=>({t,m:met(row,t.i)})),vals=ms.map(x=>metricValue(x.m)).filter(v=>v!==null),max=Math.max(1,...vals),auto=ms.filter(x=>x.m.a!==null).sort((a,b)=>(b.m.a??-1)-(a.m.a??-1))[0]?.t.slug||towns[0].slug;if(!state.detailTown||!towns.some(t=>t.slug===state.detailTown))state.detailTown=auto;
  let detail=ms.find(x=>x.t.slug===state.detailTown) || ms[0],dm=detail.m;
  return `<div class="selected-title"><code>${n.sec} · ${displayCode(n.d)}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>${LEVELS[n.d.length]} · anno 2025</p>${hierarchyContext(n)}</div>
  <div class="metric-row"><span>Metrica del confronto</span><div class="mini-switch"><button data-metric="active" class="${state.metric==='active'?'active':''}">UL attive</button><button data-metric="lq" class="${state.metric==='lq'?'active':''}">Specializzazione</button><button data-metric="weight" class="${state.metric==='weight'?'active':''}">Peso Toscana</button></div></div>
  <div class="lollipops">${ms.map(x=>{let v=metricValue(x.m),cl=v===null?'nd':v===0?'zero':'';let pct=v===null||v===0?0:(v/max*100);return `<div class="lrow clickable ${cl} ${x.t.slug===state.detailTown?'selected':''}" data-town="${x.t.slug}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(x.t.name)}" data-tip-value="${escapeHtml(metricUnit()+': '+metricFmt(v))}" aria-label="${escapeHtml(x.t.name+': '+metricUnit()+' '+metricFmt(v))}"><div class="lname">${escapeHtml(x.t.name)}</div><div class="track"><span class="stem" style="--pct:${pct}%"></span><span class="dot" style="--pct:${pct}%"></span></div><div class="lvalue">${metricFmt(v)}<small>${metricUnit()}</small></div></div>`}).join('')}</div>
  <div class="legend-note"><span><i class="legend-dot"></i> valore positivo</span><span><i class="legend-zero"></i> zero osservato</span><span><i class="legend-nd"></i> n.d.</span></div>
  <div class="detail-heading"><h4>Dettaglio analitico</h4><select id="detailTown" class="town-select">${towns.map(t=>`<option value="${t.slug}" ${t.slug===state.detailTown?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select></div>
  <div class="kpis"><div class="kpi"><span>UL attive</span><strong>${fmt(dm.a)}</strong><small>2025</small></div><div class="kpi"><span>UL artigiane</span><strong>${fmt(dm.art)}</strong><small>${dm.share===null?'quota n.d.':fmt(dm.share,1)+'% del codice'}</small></div><div class="kpi"><span>Specializzazione</span><strong>${dm.lq===null?'n.d.':fmt(dm.lq,2)+'×'}</strong><small>1× = Toscana</small></div><div class="kpi"><span>Peso regionale</span><strong>${dm.weight===null?'n.d.':fmt(dm.weight,2)+'%'}</strong><small>delle UL toscane del codice</small></div><div class="kpi"><span>Riferimento Toscana</span><strong>${fmt(dm.ra)}</strong><small>UL attive · 2025</small></div><div class="kpi"><span>Quota artigiana</span><strong>${dm.share===null?'n.d.':fmt(dm.share,1)+'%'}</strong><small>nel Comune</small></div></div>`;
}
function pathFromPoints(points){let segs=[],cur=[];for(const p of points){if(p)cur.push(p);else if(cur.length){segs.push(cur);cur=[]}}if(cur.length)segs.push(cur);return segs.map(s=>s.map((p,i)=>(i?'L':'M')+p.x.toFixed(1)+' '+p.y.toFixed(1)).join(' '));}
function renderHistory(row,n){
  const W=760,H=350,L=48,R=20,T=26,B=44;let visible=towns.filter(t=>state.visible.has(t.slug));if(!visible.length){state.visible.add(towns[0].slug);visible=[towns[0]]}
  let all=[];visible.forEach(t=>years.forEach((y,yi)=>{let v=row[3+t.i][0][yi];if(v!==null)all.push(v)}));let ymax=Math.max(1,...all);ymax=Math.ceil(ymax/10)*10;let x=i=>L+i/(years.length-1)*(W-L-R),y=v=>T+(1-v/ymax)*(H-T-B);
  let svg='';for(let j=0;j<=4;j++){let vv=ymax*(4-j)/4,yy=T+j*(H-T-B)/4;svg+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text class="axistext" x="${L-8}" y="${yy+3}" text-anchor="end">${fmt(vv,0)}</text>`}
  years.forEach((yr,i)=>{svg+=`<text class="axistext" x="${x(i)}" y="${H-14}" text-anchor="middle">${String(yr).slice(2)}</text>`});let bi=years.indexOf(2022);if(bi>=0){let bx=x(bi);svg+=`<rect x="${bx-6}" y="${T}" width="12" height="${H-T-B}" fill="#f3e3da" opacity=".55"/><line class="breakline" x1="${bx}" x2="${bx}" y1="${T}" y2="${H-B}"/><text class="breaktext" x="${bx+5}" y="${T+10}">ATECO 2022</text>`}
  visible.forEach((t,vi)=>{let pts=years.map((yr,yi)=>{let v=row[3+t.i][0][yi];return v===null?null:{x:x(yi),y:y(v),v,yr}});let color=PALETTE[t.i%PALETTE.length];for(const d of pathFromPoints(pts))svg+=`<path class="trendline" d="${d}" stroke="${color}"/>`;pts.filter(Boolean).forEach(p=>svg+=`<circle class="trenddot" cx="${p.x}" cy="${p.y}" r="3.2" stroke="${color}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(t.name+' · '+p.yr)}" data-tip-value="${escapeHtml(fmt(p.v)+' UL')}" aria-label="${escapeHtml(t.name+' · '+p.yr+': '+fmt(p.v)+' UL')}"></circle>`)});
  return `<div class="selected-title"><code>${n.sec} · ${displayCode(n.d)}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>Serie annuale delle UL attive · 2014–2025</p>${hierarchyContext(n)}</div><div class="history-controls"><div class="town-chips">${towns.map(t=>`<button class="town-chip ${state.visible.has(t.slug)?'':'off'}" data-vtown="${t.slug}" style="border-color:${PALETTE[t.i%PALETTE.length]}">${escapeHtml(t.name)}</button>`).join('')}</div><div class="history-tools"><button id="allTowns">Tutti</button><button id="oneTown">Solo dettaglio</button></div></div><div class="history-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Serie storiche 2014-2025">${svg}</svg></div><div class="history-foot"><strong>2022.</strong> La linea evidenzia l’aggiornamento della classificazione ATECO.</div>`;
}
function renderAnalysis(){
  let n=currentNode(),row=getRow(),box=$('#analysis'),heading=$('#analysisHeading');
  $('#tabCurrent').classList.toggle('active',state.tab==='current');$('#tabHistory').classList.toggle('active',state.tab==='history');
  if(heading)heading.textContent=initialTownMeta?`${initialTownMeta.name} nel confronto territoriale`:(state.leftMode==='composition'?'Il nodo nei sette Comuni':'Il codice nei sette Comuni');
  if(!n){box.innerHTML='<div class="empty"><strong>Seleziona un’attività.</strong><br>Puoi partire dalla ricerca libera, dai selettori o dal grafico ad anello.</div>';return}
  if(state.leftMode==='composition'){
    box.innerHTML=state.tab==='current'?renderCurrentDerived(n):renderHistoryDerived(n);wireAnalysis();return;
  }
  if(!row){box.innerHTML=`<div class="selected-title"><code>${n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`}</code><h3>${escapeHtml(n.label||'Dicitura non disponibile')}</h3><p>${n.d?LEVELS[n.d.length]:'Sezione'}</p>${hierarchyContext(n)}</div><div class="empty"><strong>Per questo livello non è disponibile un valore autonomo.</strong><br>Usa <strong>Composizione %</strong> per leggere la distribuzione delle attività oppure scegli una voce più specifica.</div>`;return}
  box.innerHTML=state.tab==='current'?renderCurrent(row,n):renderHistory(row,n);wireAnalysis();
}
function wireAnalysis(){
  root.querySelectorAll('[data-metric]').forEach(b=>b.onclick=()=>{state.metric=b.dataset.metric;renderAnalysis()});root.querySelectorAll('.lrow[data-town]').forEach(r=>r.onclick=()=>{state.detailTown=r.dataset.town;renderAnalysis()});let ds=$('#detailTown');if(ds)ds.onchange=()=>{state.detailTown=ds.value;renderAnalysis()};root.querySelectorAll('[data-vtown]').forEach(b=>b.onclick=()=>{let s=b.dataset.vtown;state.visible.has(s)?state.visible.delete(s):state.visible.add(s);renderAnalysis()});let a=$('#allTowns');if(a)a.onclick=()=>{state.visible=new Set(towns.map(t=>t.slug));renderAnalysis()};let o=$('#oneTown');if(o)o.onclick=()=>{let s=state.detailTown||towns[0].slug;state.visible=new Set([s]);renderAnalysis()};wireAtlasTooltips();
}
function renderAll(){renderSelectors();renderCrumbs();renderDonut();renderAnalysis();wireAtlasTooltips()}
function searchItems(q){let nq=norm(q),digits=nq.replace(/[^0-9]/g,'');let score=new Map();for(const [alias,raws] of Object.entries(aliases))if(norm(alias).includes(nq)||nq.includes(norm(alias)))raws.forEach((r,i)=>score.set(r,100-i));for(const [raw,row] of exact){let n=nodes.get(raw),code=rawToPretty(raw),label=n?.label||'';let s=0;if(digits&&raw.replace(/\D/g,'').startsWith(digits))s=90;if(nq&&norm(label).includes(nq))s=Math.max(s,80);if(norm(code).includes(nq))s=Math.max(s,85);if(s)score.set(raw,Math.max(score.get(raw)||0,s));}return [...score.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,12).map(([r])=>nodes.get(r))}
$('#search').oninput=e=>{let q=e.target.value.trim(),res=$('#results');if(!q){res.hidden=true;return}let items=searchItems(q);res.innerHTML=items.length?items.map(n=>`<button class="result" data-raw="${n.key}"><span class="result-code">${n.sec} · ${displayCode(n.d)}</span><span class="result-name">${escapeHtml(n.label)}</span><span class="result-level">${LEVELS[n.d.length]}</span></button>`).join(''):'<div class="empty">Nessun risultato.</div>';res.hidden=false;res.querySelectorAll('[data-raw]').forEach(b=>b.onclick=()=>{let n=nodes.get(b.dataset.raw);$('#search').value=`${n.sec} ${displayCode(n.d)} · ${n.label}`;res.hidden=true;selectNode(n.sec,n.d,false)})};
$('#clear').onclick=clearAll;root.querySelector('.quick').onclick=e=>{let b=e.target.closest('button');if(!b)return;if(b.dataset.code){let n=nodes.get(b.dataset.code);if(n){$('#search').value=`${n.sec} ${displayCode(n.d)} · ${n.label}`;selectNode(n.sec,n.d,false)}}else if(b.dataset.q){$('#search').value=b.dataset.q;$('#search').dispatchEvent(new Event('input'));$('#search').focus()}};
$('#tabCurrent').onclick=()=>{state.tab='current';renderAnalysis()};$('#tabHistory').onclick=()=>{state.tab='history';renderAnalysis()};$('#modeComposition').onclick=()=>{state.leftMode='composition';state.detailTown=initialTown||'';renderDonut();renderAnalysis()};$('#modeNavigation').onclick=()=>{state.leftMode='navigation';state.detailTown=initialTown||'';renderDonut();renderAnalysis()};
root.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))$('#results').hidden=true});
applyEmbeddedTaxonomy();

// Territorial context: Versilia or one municipality, selectable from every standalone Atlas view.
fmt = function(v,d=0){if(v===null||v===undefined||Number.isNaN(v))return'n.d.';return new Intl.NumberFormat('it-IT',{useGrouping:'always',minimumFractionDigits:d,maximumFractionDigits:d}).format(v)};
const requestedTerritory = initialTown || new URLSearchParams(location.search).get('comune') || '';
const requestedTerritoryMeta = towns.find(t => t.slug === requestedTerritory) || null;
state.territory = requestedTerritoryMeta?.slug || '';
state.detailTown = state.territory || '';
state.visible = new Set(state.territory ? [state.territory] : towns.map(t => t.slug));

const originalCompositionChildren = compositionChildren;
const originalCompositionTotalForCurrent = compositionTotalForCurrent;
const originalRenderDonut = renderDonut;
const originalRenderCurrentDerived = renderCurrentDerived;
const originalRenderAnalysis = renderAnalysis;
const originalRenderAll = renderAll;
const originalSelectNode = selectNode;
const originalClearAll = clearAll;

function activeTerritoryMeta(){ return towns.find(t => t.slug === state.territory) || null; }
function territoryLabel(){ return activeTerritoryMeta()?.name || 'Versilia'; }
function aggregateValueForTerritory(agg, yi=latest){ const t=activeTerritoryMeta(); return t ? agg.towns[t.i][yi] : agg.vers[yi]; }
compositionChildren = function(){
  const kids=state.sec?childNodes(state.sec,state.d):sections.map(([s])=>ensure(s,''));
  return kids.map(n=>{const agg=aggregateNode(n.sec,n.d);return {node:n,value:aggregateValueForTerritory(agg,latest)};});
};
compositionTotalForCurrent = function(){
  if(!state.sec) return sumNullable(compositionChildren().map(x=>x.value));
  return aggregateValueForTerritory(aggregateNode(state.sec,state.d),latest);
};
selectNode = function(sec,d='',autoAdvance=true){state.sec=sec;state.d=autoAdvance&&sec?descendSingleton(sec,d):d;state.detailTown=state.territory||'';renderAll()};
clearAll = function(){state.sec='';state.d='';state.tab='current';state.metric='active';state.detailTown=state.territory||'';$('#search').value='';$('#results').hidden=true;renderAll()};
renderCurrentDerived = function(n){
  const markup=originalRenderCurrentDerived(n);
  return markup.replace(' UL attive in Versilia · anno 2025',` UL attive in ${escapeHtml(territoryLabel())} · anno 2025`);
};
renderDonut = function(){
  originalRenderDonut();
  if(state.leftMode==='composition'&&!state.sec){ const strong=$('#donutCenter strong'); if(strong) strong.textContent=territoryLabel(); }
};
renderAnalysis = function(){
  if(state.territory&&!state.detailTown) state.detailTown=state.territory;
  originalRenderAnalysis();
  const town=activeTerritoryMeta(),heading=$('#analysisHeading');
  if(heading&&town) heading.textContent=`${town.name} nel confronto territoriale`;
};
function quickValue(raw){
  const row=exact.get(raw); if(!row) return null;
  const t=activeTerritoryMeta();
  return t ? row[3+t.i][0][latest] : sumNullable(towns.map(item=>row[3+item.i][0][latest]));
}
function syncTerritoryContext(){
  const searchTop=$('.search-top');
  if(searchTop&&!$('#territory')){
    searchTop.insertAdjacentHTML('afterbegin',`<label class="field territory-field"><span>Territorio</span><select id="territory" aria-label="Territorio dell'Atlante"><option value="">Versilia</option>${towns.map(t=>`<option value="${t.slug}">${escapeHtml(t.name)}</option>`).join('')}</select></label>`);
    const style=document.createElement('style');style.id='territory-style';style.textContent='.search-top{grid-template-columns:minmax(190px,.34fr) minmax(0,1fr) auto}.territory-field select{width:100%;height:50px;border:1px solid #c7d2d0;border-radius:13px;padding:0 38px 0 13px;background:#fff;outline:none;font-weight:750}.territory-field select:focus{border-color:var(--theme);box-shadow:0 0 0 3px rgba(173,98,71,.11)}.hero-symbol svg{width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}@media(max-width:680px){.search-top{grid-template-columns:1fr}}';root.prepend(style);
    const territory=$('#territory');territory.onchange=()=>{
      state.territory=territory.value;state.detailTown=state.territory||'';state.visible=new Set(state.territory?[state.territory]:towns.map(t=>t.slug));
      if(!root.host?.hasAttribute('embedded')){const url=new URL(location.href);if(state.territory)url.searchParams.set('comune',state.territory);else url.searchParams.delete('comune');history.replaceState(history.state,'',url.pathname+url.search+url.hash)}
      renderAll();
    };
  }
  const territory=$('#territory');if(territory)territory.value=state.territory||'';
  const meta=activeTerritoryMeta();
  const symbol=root.querySelector('.hero-symbol');if(symbol)symbol.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v9h16v-9"/><path d="M3 10h18l-2-5H5l-2 5Z"/><path d="M7 10v1a2 2 0 0 0 4 0v-1m0 0v1a2 2 0 0 0 4 0v-1m0 0v1a2 2 0 0 0 4 0v-1"/><path d="M9 19v-5h6v5"/></svg>';
  const title=root.querySelector('.hero h1');if(title)title.textContent=meta?`Atlante delle attività economiche · ${meta.name}`:'Atlante delle attività economiche';
  const intro=root.querySelector('.hero p');if(intro)intro.textContent=meta?`Esplora le attività economiche di ${meta.name} dalla Sezione alla massima granularità disponibile, mantenendo il confronto con gli altri Comuni della Versilia e con la Toscana.`:'Esplora la presenza delle attività economiche nei sette Comuni della Versilia, dalla Sezione alla massima granularità disponibile. Seleziona un Comune per leggerne la struttura in modo dedicato.';
  const over=root.querySelector('.hero .overline');if(over)over.textContent=meta?`Economia · ${meta.name} · Registro Imprese`:'Economia · Registro Imprese';
  const quickTitle=$('.quick-title');if(quickTitle)quickTitle.textContent=`Accessi rapidi · attività frequenti in ${territoryLabel()} · 2025`;
  root.querySelectorAll('.quick button[data-code]').forEach(button=>{const b=button.querySelector('b'),v=quickValue(button.dataset.code);if(b)b.textContent=v===null?'n.d.':`${fmt(v)} UL`;});
}
renderAll = function(){
  if(state.territory&&!state.detailTown) state.detailTown=state.territory;
  syncTerritoryContext();originalRenderAll();syncTerritoryContext();
};

if(initialTown){
  const townMeta=towns.find(t=>t.slug===initialTown);
  const quickTitle=$('.quick-title');
  if(quickTitle) quickTitle.textContent='Accessi rapidi · attività frequenti in Versilia · 2025';
  const heading=$('#analysisHeading');
  if(heading&&townMeta) heading.textContent=`${townMeta.name} nel confronto territoriale`;
}

/* ov-atlas-export-actions */
function csvCell(value){
  const text=String(value??'');
  return /[;"\r\n]/.test(text)?`"${text.replaceAll('"','""')}"`:text;
}
function csvLevel(n){return n.d?(LEVELS[n.d.length]||'Codice'):'Sezione'}
function csvCode(n){return n.d?`${n.sec} ${displayCode(n.d)}`:n.sec}
function atlasCsvRows(){
  const t=activeTerritoryMeta();
  const territory=t?.name||'Versilia';
  const ordered=[...nodes.values()].filter(n=>n&&n.sec).sort((a,b)=>{
    const ac=`${a.sec} ${a.d||''}`,bc=`${b.sec} ${b.d||''}`;
    return ac.localeCompare(bc,'it',{numeric:true});
  });
  const rows=[['Territorio','Codice ATECO','Livello','Descrizione','Anno','UL attive','UL artigiane (2025)','Fonte']];
  ordered.forEach(n=>{
    const agg=aggregateNode(n.sec,n.d);
    years.forEach((yr,yi)=>{
      const active=t?agg.towns[t.i][yi]:agg.vers[yi];
      const artisan=yi===latest?(t?agg.art[t.i]:sumNullable(agg.art)):null;
      if(active===null&&artisan===null)return;
      rows.push([territory,csvCode(n),csvLevel(n),n.label||'',yr,active??'',artisan??'','Regione Toscana / Registro Imprese InfoCamere']);
    });
  });
  return rows;
}
function downloadAtlasCsv(){
  const rows=atlasCsvRows();
  const csv='\ufeff'+rows.map(row=>row.map(csvCell).join(';')).join('\r\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=`atlante-attivita-economiche-${state.territory||'versilia'}-2014-2025.csv`;
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),0);
}
function ensureAtlasExportActions(){
  if(root.host?.hasAttribute('embedded'))return;
  if(root.querySelector('.atlas-export-actions'))return;
  const explorer=root.querySelector('.explorer');if(!explorer)return;
  const style=document.createElement('style');
  style.id='atlas-data-actions-style';
  style.textContent=`.data-actions{flex-wrap:wrap;gap:7px;margin-top:18px;display:flex}.data-actions button{color:var(--blue);background:#fffaf194;border:1px solid #c4d1d1;border-radius:9px;align-items:center;gap:7px;padding:9px 11px;font-size:10px;font-weight:750;display:inline-flex;cursor:pointer}.data-actions button:hover,.data-actions button:focus-visible{border-color:var(--blue);background:var(--blue-soft)}.atlas-export-actions{margin:0 0 18px}@media print{.data-actions{display:none!important}}`;
  root.prepend(style);
  const bar=document.createElement('div');
  bar.className='data-actions atlas-export-actions';
  bar.setAttribute('aria-label','Azioni Atlante');
  bar.innerHTML=`<button type="button" id="atlasDownloadCsv" data-download>Scarica CSV</button><button type="button" id="atlasPrint" data-print>Stampa / PDF</button>`;
  explorer.insertAdjacentElement('beforebegin',bar);
  bar.querySelector('#atlasDownloadCsv').onclick=downloadAtlasCsv;
  bar.querySelector('#atlasPrint').onclick=()=>window.print();
}

renderAll();
ensureAtlasExportActions();

    }
  }
  if(!customElements.get('ov-economy-atlas')) customElements.define('ov-economy-atlas', OVEconomyAtlas);
})();
