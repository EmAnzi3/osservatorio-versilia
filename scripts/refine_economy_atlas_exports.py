#!/usr/bin/env python3
"""Aggiunge export CSV e stampa/PDF alla pagina canonica dell'Atlante Economia."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "assets" / "economy-atlas.js"
REGISTRY = ROOT / "data" / "source-registry.json"
MARKER = "/* ov-atlas-export-actions */"
TAIL = "renderAll();\n\n    }\n  }\n  if(!customElements.get('ov-economy-atlas'))"

EXPORT_JS = r'''
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
  const standaloneStyle=document.createElement('style');
  standaloneStyle.id='atlas-standalone-ui-style';
  standaloneStyle.textContent=`.hero{position:relative;width:100vw;min-height:365px;margin-left:calc(50% - 50vw);display:grid;grid-template-columns:80px minmax(0,1fr);align-content:center;gap:28px;padding:46px max(24px,calc((100vw - 1240px)/2));border:0;color:#fff;background:linear-gradient(90deg,rgba(6,31,49,.95) 0%,rgba(6,31,49,.84) 38%,rgba(6,31,49,.48) 69%,rgba(6,31,49,.18) 100%),url('https://upload.wikimedia.org/wikipedia/commons/4/40/11_Piacenza%2C_Italy_-_%E3%82%B7%E3%83%A7%E3%83%83%E3%83%94%E3%83%B3%E3%82%B0_%E3%82%A4%E3%82%BF%E3%83%AA%E3%82%A2.jpg') center 54%/cover no-repeat;overflow:hidden}.hero:before{content:'';position:absolute;left:max(24px,calc((100vw - 1240px)/2));top:0;width:72px;height:4px;background:#ffdb4d}.hero:after{content:'Attività commerciali · Wikimedia Commons';position:absolute;right:max(14px,calc((100vw - 1240px)/2));bottom:12px;padding:5px 8px;border-radius:6px;background:rgba(5,31,48,.62);color:rgba(255,255,255,.78);font-size:8px;font-weight:600}.hero>*{position:relative;z-index:2}.hero-symbol{width:68px;height:68px;border:1px solid rgba(255,255,255,.38);border-radius:20px 20px 20px 7px;background:rgba(255,255,255,.14);color:#ffdb4d;display:grid;place-items:center;font:800 18px var(--mono);backdrop-filter:blur(8px)}.hero .overline{color:#ffdb4d}.hero h1{color:#fff;text-shadow:0 3px 22px rgba(0,0,0,.24)}.hero p{max-width:780px;color:rgba(255,255,255,.91);font-size:15px;line-height:1.58;margin:0}.hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.meta-pill{background:rgba(5,31,48,.50);border:1px solid rgba(255,255,255,.24);border-radius:999px;padding:8px 11px;color:#fff;font-size:10px;font-weight:750;backdrop-filter:blur(8px)}.meta-pill strong{color:#ffdb4d}@media(max-width:680px){.hero{min-height:390px;grid-template-columns:44px minmax(0,1fr);align-content:end;gap:14px;padding:36px 20px 34px}.hero:before{left:20px;width:54px}.hero:after{right:9px;bottom:8px;font-size:7px}.hero-symbol{width:44px;height:44px;border-radius:13px 13px 13px 4px;font-size:13px}.hero h1{font-size:47px}.hero p{font-size:13px}}`;
  root.prepend(standaloneStyle);
  const explorer=root.querySelector('.explorer');if(!explorer)return;
  const style=document.createElement('style');
  style.id='atlas-data-actions-style';
  style.textContent=`.data-actions{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 18px}.data-actions button{min-height:30px;display:inline-flex;align-items:center;justify-content:center;border:1px solid #c9d3d1;border-radius:7px;background:#fbf7f0;color:#102f45;padding:5px 8px;font-size:7px;font-weight:760;line-height:1;white-space:nowrap;cursor:pointer}.data-actions button:hover,.data-actions button:focus-visible{border-color:#145b78;background:#e4eff2;outline:none}.data-actions [data-download]::before,.data-actions [data-print]::before{display:inline-grid;place-items:center;flex:0 0 17px;width:17px;height:17px;margin-right:5px;border-radius:2px;color:#fff;font-family:Arial,sans-serif;font-weight:800;line-height:1}.data-actions [data-download]::before{content:'X';background:#217346;font-size:8px}.data-actions [data-print]::before{content:'PDF';background:#b84b34;font-size:5px}.atlas-export-actions{margin:0 0 18px}@media print{.data-actions{display:none!important}}`;
  root.prepend(style);
  const bar=document.createElement('div');
  bar.className='data-actions atlas-export-actions';
  bar.setAttribute('aria-label','Azioni Atlante');
  bar.innerHTML=`<button type="button" id="atlasDownloadCsv" data-download>Scarica CSV</button><button type="button" id="atlasPrint" data-print>Stampa / PDF</button>`;
  explorer.insertAdjacentElement('beforebegin',bar);
  bar.querySelector('#atlasDownloadCsv').onclick=downloadAtlasCsv;
  bar.querySelector('#atlasPrint').onclick=()=>window.print();
}
'''


def normalize_registry_counts() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    total = int(registry["expectedMetricCount"])
    external = int(registry["expectedExternalMetricCount"])
    registry["expectedInlineMetricCount"] = total - external
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    normalize_registry_counts()
    text = RUNTIME.read_text(encoding="utf-8")
    if MARKER in text:
        print("Azioni export Atlante già presenti; conteggi registry normalizzati.")
        return
    if text.count(TAIL) != 1:
        raise RuntimeError(f"Tail Atlante inattesa: {text.count(TAIL)} occorrenze")
    text = text.replace(TAIL, EXPORT_JS + "\nrenderAll();\nensureAtlasExportActions();\n\n    }\n  }\n  if(!customElements.get('ov-economy-atlas'))", 1)
    RUNTIME.write_text(text, encoding="utf-8")
    print("Atlante: azioni standard Scarica CSV e Stampa / PDF materializzate; registry inline normalizzato.")


if __name__ == "__main__":
    main()
