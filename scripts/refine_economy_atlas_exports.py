#!/usr/bin/env python3
"""Aggiunge export CSV e stampa/PDF alla pagina canonica dell'Atlante Economia."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "assets" / "economy-atlas.js"
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
'''


def main() -> None:
    text = RUNTIME.read_text(encoding="utf-8")
    if MARKER in text:
        print("Azioni export Atlante già presenti.")
        return
    if text.count(TAIL) != 1:
        raise RuntimeError(f"Tail Atlante inattesa: {text.count(TAIL)} occorrenze")
    text = text.replace(TAIL, EXPORT_JS + "\nrenderAll();\nensureAtlasExportActions();\n\n    }\n  }\n  if(!customElements.get('ov-economy-atlas'))", 1)
    RUNTIME.write_text(text, encoding="utf-8")
    print("Atlante: azioni standard Scarica CSV e Stampa / PDF materializzate.")


if __name__ == "__main__":
    main()
