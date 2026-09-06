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
  style.id='atlas-export-style';
  style.textContent=`.atlas-export-actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin:0 0 18px}.atlas-export-actions button{display:inline-flex;align-items:center;gap:7px;min-height:38px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--ink);font:750 12px/1 var(--sans);cursor:pointer;box-shadow:0 3px 10px rgba(16,47,69,.04)}.atlas-export-actions button:hover{border-color:var(--blue);color:var(--blue)}.atlas-export-actions button:focus-visible{outline:2px solid var(--blue);outline-offset:2px}.atlas-export-actions svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}@media(max-width:680px){.atlas-export-actions{justify-content:flex-start}.atlas-export-actions button{flex:1;justify-content:center}}@media print{.atlas-export-actions{display:none!important}}`;
  root.prepend(style);
  const bar=document.createElement('div');
  bar.className='atlas-export-actions';
  bar.setAttribute('aria-label','Azioni Atlante');
  bar.innerHTML=`<button type="button" id="atlasDownloadCsv"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 19h14"/></svg><span>Scarica CSV</span></button><button type="button" id="atlasPrint"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9V4h10v5"/><path d="M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"/><path d="M7 14h10v6H7z"/></svg><span>Stampa / PDF</span></button>`;
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
    print("Atlante: Scarica CSV e Stampa / PDF materializzati.")


if __name__ == "__main__":
    main()
