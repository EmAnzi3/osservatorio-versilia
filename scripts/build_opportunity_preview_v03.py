#!/usr/bin/env python3
"""Materializza la preview v0.3 sopra il renderer stabile v0.2.4."""
from __future__ import annotations
import argparse, html, re
from pathlib import Path
from typing import Any
import build_opportunity_preview as old
from site_chrome import synchronize_native_page

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DATA=ROOT/'reports'/'runtime'/'opportunities-v03.json'
DEFAULT_DIST=ROOT/'dist'
TARGET_ROUTE='opportunita-preview'

BASE_CARD=old.card_markup
BASE_ARCHIVE=old.archive_markup

ICONS={
 'briefcase':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M3 12h18M10 12v2h4v-2"/></svg>',
 'radar':'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/><path d="M12 12 18.5 5.5"/></svg>',
 'map':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 6 5-2 8 3 5-2v13l-5 2-8-3-5 2Z"/><path d="M8 4v13M16 7v13"/></svg>',
 'archive':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16v13H4zM3 3h18v4H3z"/><path d="M9 11h6"/></svg>',
 'calendar':'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
 'building':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V7l8-4 8 4v14"/><path d="M8 10h2M14 10h2M8 14h2M14 14h2M9 21v-3h6v3"/></svg>',
 'user':'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
 'pin':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>'
}

def esc(v:Any)->str:return html.escape(str(v or ''),quote=True)
def source_meta(item):
 m=dict(item.get('presentation') or {});label=str(m.get('source_label') or item.get('publisher') or item.get('source_name') or 'Fonte');m['source_label']=label;m['source_favicon']=str(m.get('source_favicon') or '');m['source_mark']=str(m.get('source_mark') or ''.join(x[:1].upper() for x in label.split()[:3]) or 'F');return m
def source_icon(meta,compact=False):
 cls='op-source-icon is-compact' if compact else 'op-source-icon';fav=meta.get('source_favicon') or '';img=f'<img class="op-source-favicon" src="{esc(fav)}" alt="" decoding="sync" referrerpolicy="no-referrer">' if fav else ''
 return f'<span class="{cls}"><span class="op-source-fallback">{esc(meta.get("source_mark") or "F")}</span>{img}</span>'
def augment_card(item):
 text=BASE_CARD(item);m=source_meta(item)
 text=re.sub(r'<span class="op-source-mark[^>]*>.*?</span>',source_icon(m),text,count=1,flags=re.S)
 for label,key in [('Scadenza','calendar'),('Ruolo del Comune','building'),('Chi presenta domanda','user'),('Ambito','pin')]:
  text=text.replace(f'<dt>{label}</dt>',f'<dt><span class="op-meta-icon">{ICONS[key]}</span>{label}</dt>')
 return text
def augment_archive(item):
 text=BASE_ARCHIVE(item);m={'source_label':item.get('source_label'),'source_mark':item.get('source_mark') or 'F','source_favicon':item.get('source_favicon') or ''}
 return re.sub(r'<span class="op-source-mark[^>]*>.*?</span>',source_icon(m,True),text,count=1,flags=re.S)
def status_label(row):
 if row.get('monitoringStatus')=='degraded' or row.get('runtimeStatus')=='degraded':return 'Degradata','degraded'
 if row.get('runtimeStatus')=='error':return 'Errore','error'
 if row.get('role')=='discovery':return 'Discovery','discovery'
 if row.get('runtimeStatus')=='ok':return 'Attiva','active'
 return 'Monitorata','neutral'
def monitor_markup(row):
 label,status=status_label(row);meta={'source_mark':''.join(x[:1].upper() for x in str(row.get('label') or 'F').split()[:3]),'source_favicon':row.get('favicon') or ''}
 return f'<div class="op-monitor-source" data-monitor-status="{status}">{source_icon(meta,True)}<span class="op-monitor-copy"><strong>{esc(row.get("label") or row.get("source_id"))}</strong><small><i></i>{label}</small></span></div>'
def quick_markup(source_id,meta):return f'<button type="button" class="op-source-quick" data-op-source-quick="{esc(source_id)}">{source_icon(meta,True)}<span>{esc(meta["source_label"])}</span></button>'

def render_page(payload):
 original_card,original_archive=old.card_markup,old.archive_markup
 old.card_markup,old.archive_markup=augment_card,augment_archive
 try: page=old.render_page(payload)
 finally: old.card_markup,old.archive_markup=original_card,original_archive
 page=page.replace('v0.2.4','v0.3')
 page=page.replace('<link rel="stylesheet" href="../assets/opportunity-preview.css">','<link rel="stylesheet" href="../assets/opportunity-preview.css">\n  <link rel="stylesheet" href="../assets/opportunity-preview-v03.css">')
 page=page.replace('<script src="../assets/opportunity-preview.js" defer></script>','<script src="../assets/opportunity-preview.js" defer></script>\n  <script src="../assets/opportunity-preview-v03.js" defer></script>')
 opportunities=list(payload.get('opportunities') or []);archive=list(payload.get('archive') or []);coverage=payload.get('sourceCoverage') or {};rows=list(coverage.get('rows') or []);summary=coverage.get('summary') or {}
 monitored=int(summary.get('configured') or len(rows));active=int(summary.get('active') or 0);degraded=int(summary.get('degraded') or 0)
 overview=f'''<section class="method-detail page-width op-overview" aria-label="Quadro operativo"><div class="op-overview-shell"><div class="op-overview-heading"><div><span class="section-number">01</span><h2>Quadro operativo</h2></div><p>Un colpo d'occhio su opportunità, fonti monitorate e copertura territoriale.</p></div><div class="op-overview-grid"><article class="op-stat op-stat-open"><span class="op-stat-icon">{ICONS['briefcase']}</span><div><small>Opportunità aperte</small><strong>{len(opportunities)}</strong><span>Solo bandi con ruolo comunale documentato</span></div></article><article class="op-stat op-stat-sources"><span class="op-stat-icon">{ICONS['radar']}</span><div><small>Fonti monitorate</small><strong>{monitored}</strong><span>{active} attive · {degraded} degradate</span></div></article><article class="op-stat op-stat-towns"><span class="op-stat-icon">{ICONS['map']}</span><div><small>Comuni coperti</small><strong>{len(old.TOWNS)}</strong><span>Tutta la Versilia amministrativa</span></div></article><article class="op-stat op-stat-archive"><span class="op-stat-icon">{ICONS['archive']}</span><div><small>In archivio</small><strong>{len(archive)}</strong><span>Storico compatto con fonte ufficiale</span></div></article></div><div class="op-monitor"><div class="op-monitor-head"><strong>Fonti monitorate</strong><span>I canali discovery restano interni finché il bando non è verificato.</span></div><div class="op-monitor-list">{''.join(monitor_markup(x) for x in rows)}</div></div></div></section>'''
 page=re.sub(r'<section class="method-detail page-width" aria-label="Riepilogo opportunità">.*?</section>',overview,page,count=1,flags=re.S)
 sources={}
 for item in opportunities:
  m=source_meta(item);sources[old.slug(str(item.get('source_id') or m['source_label']))]=m
 shortcuts='<div class="op-source-shortcuts" aria-label="Filtri rapidi per fonte">'+''.join(quick_markup(k,m) for k,m in sorted(sources.items(),key=lambda p:p[1]['source_label']))+'</div>'
 page=page.replace('<section class="method-detail page-width">\n      <div class="section-heading"><div><span class="section-number">02</span><h2>Filtra le opportunità</h2>', '<section class="method-detail page-width op-filter-panel">\n      <div class="section-heading"><div><span class="section-number">02</span><h2>Filtra le opportunità</h2>',1)
 page=page.replace('      <div class="op-preview-controls">',f'      {shortcuts}\n      <div class="op-preview-controls">',1)
 page=page.replace('<main class="editorial-page op-preview-main" data-opportunity-preview>','<main class="editorial-page op-preview-main" data-opportunity-preview data-total-opportunities="%d">'%len(opportunities),1)
 return page

def build(payload_path:Path,dist:Path)->Path:
 if not (dist/'progetto'/'index.html').exists():raise SystemExit('Build statica canonica assente: eseguire prima scripts/build_static_brand.py')
 payload=old.load_payload(payload_path);target=dist/TARGET_ROUTE/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(render_page(payload),encoding='utf-8')
 try:synchronize_native_page(dist,target)
 except RuntimeError as exc:raise SystemExit(str(exc)) from exc
 sitemap=(dist/'sitemap.xml').read_text(encoding='utf-8') if (dist/'sitemap.xml').exists() else ''
 if 'opportunita-preview' in sitemap:raise SystemExit('La preview non deve comparire nella sitemap')
 text=target.read_text(encoding='utf-8')
 if 'Anteprima v0.3' not in text or 'name="robots" content="noindex,nofollow,noarchive"' not in text:raise SystemExit('Preview v0.3/noindex non materializzata correttamente')
 for token in ('Quality gate','Perché compare:','>Da verificare<','discoveryQueue'):
  if token in text:raise SystemExit('La preview espone ancora concetti tecnici interni')
 return target

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=DEFAULT_DATA);p.add_argument('--dist',type=Path,default=DEFAULT_DIST);a=p.parse_args();print(f'Preview opportunità v0.3 materializzata: {build(a.data,a.dist)}')
if __name__=='__main__':main()
