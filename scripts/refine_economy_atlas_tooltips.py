#!/usr/bin/env python3
"""Allinea i tooltip dell'Atlante al contratto visuale dei grafici OV."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "assets" / "economy-atlas.js"
MARKER = "/* ov-site-tooltip-contract */"


def exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"Tooltip Atlante {label}: attese {expected} occorrenze, trovate {count}")
    return text.replace(old, new, expected)


def main() -> None:
    text = RUNTIME.read_text(encoding="utf-8")
    if MARKER in text:
        print("Tooltip Atlante già allineati a OV.")
        return

    bootstrap = r'''    _init(root) {

/* ov-site-tooltip-contract */
const atlasTooltipStyle=document.createElement('style');
atlasTooltipStyle.textContent=`.ov-site-tooltip{position:fixed;z-index:10000;pointer-events:none;min-width:132px;max-width:230px;padding:8px 12px;border-radius:8px;background:var(--ink);color:#fff;box-shadow:0 6px 9px rgba(16,47,69,.18);font-family:var(--sans);line-height:1.25}.ov-site-tooltip[hidden]{display:none!important}.ov-site-tooltip .chart-tooltip-year{display:block;opacity:.75;font-size:9px;font-weight:600}.ov-site-tooltip .chart-tooltip-value{display:block;margin-top:3px;font-size:11px;font-weight:800}.lrow[data-atlas-tooltip]{position:relative;outline:none}.lrow[data-atlas-tooltip]:focus-visible{box-shadow:0 0 0 2px var(--blue)}.trenddot[data-atlas-tooltip]:focus,.slice[data-atlas-tooltip]:focus{outline:none}`;
root.prepend(atlasTooltipStyle);
function ensureAtlasTooltip(){let tip=root.querySelector('.ov-site-tooltip');if(!tip){tip=document.createElement('div');tip.className='ov-site-tooltip';tip.hidden=true;tip.innerHTML='<span class="chart-tooltip-year"></span><strong class="chart-tooltip-value"></strong>';root.appendChild(tip)}return tip}
function hideAtlasTooltip(){const tip=root.querySelector('.ov-site-tooltip');if(tip)tip.hidden=true}
function showAtlasTooltip(target){const tip=ensureAtlasTooltip();tip.querySelector('.chart-tooltip-year').textContent=target.dataset.tipTitle||'';tip.querySelector('.chart-tooltip-value').textContent=target.dataset.tipValue||'';tip.hidden=false;tip.style.left='0px';tip.style.top='0px';const r=target.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;let x=Math.max(8,Math.min(window.innerWidth-w-8,r.left+r.width/2-w/2));let y=r.top-h-10;if(y<8)y=Math.min(window.innerHeight-h-8,r.bottom+10);tip.style.left=`${Math.round(x)}px`;tip.style.top=`${Math.round(y)}px`}
function wireAtlasTooltips(){root.querySelectorAll('[data-atlas-tooltip]').forEach(el=>{if(el.dataset.atlasTooltipWired==='1')return;el.dataset.atlasTooltipWired='1';if(!el.hasAttribute('tabindex'))el.setAttribute('tabindex','0');el.addEventListener('mouseenter',()=>showAtlasTooltip(el));el.addEventListener('mouseleave',hideAtlasTooltip);el.addEventListener('focus',()=>showAtlasTooltip(el));el.addEventListener('blur',hideAtlasTooltip);el.addEventListener('keydown',e=>{if(e.key==='Escape'){hideAtlasTooltip();el.blur()}})});}

const LABELS='''
    text = exact(text, "    _init(root) {\n\n\nconst LABELS=", bootstrap, "bootstrap")

    text = exact(
        text,
        "p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.innerHTML=`<title>${n.d?displayCode(n.d):n.sec} · ${n.label||''}</title>`;p.onclick=()=>selectNode(n.sec,n.d);",
        "p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.setAttribute('data-atlas-tooltip','1');p.dataset.tipTitle=n.d?`${n.sec} · ${displayCode(n.d)}`:`Sezione ${n.sec}`;p.dataset.tipValue=n.label||'';p.setAttribute('aria-label',`${p.dataset.tipTitle}: ${p.dataset.tipValue}`);p.onclick=()=>selectNode(n.sec,n.d);",
        "donut navigazione",
    )
    text = exact(
        text,
        "p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');\n    p.innerHTML=`<title>${item.node.d?displayCode(item.node.d):item.node.sec} · ${item.node.label||''} — ${fmt(item.value)} UL · ${fmt(pct*100,1)}%</title>`;\n    p.onclick=()=>selectNode(item.node.sec,item.node.d);",
        "p.setAttribute('stroke-width','42');p.setAttribute('class','slice');p.setAttribute('tabindex','0');p.setAttribute('data-atlas-tooltip','1');\n    p.dataset.tipTitle=item.node.d?`${item.node.sec} · ${displayCode(item.node.d)}`:`Sezione ${item.node.sec}`;p.dataset.tipValue=`${fmt(item.value)} UL · ${fmt(pct*100,1)}%`;p.setAttribute('aria-label',`${p.dataset.tipTitle}: ${item.node.label||''} — ${p.dataset.tipValue}`);\n    p.onclick=()=>selectNode(item.node.sec,item.node.d);",
        "donut composizione",
    )

    old_lrow = 'data-town="${x.t.slug}" title="${escapeHtml(x.t.name)} · ${metricUnit()}: ${metricFmt(v)}"'
    new_lrow = 'data-town="${x.t.slug}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(x.t.name)}" data-tip-value="${escapeHtml(metricUnit()+\': \'+metricFmt(v))}" aria-label="${escapeHtml(x.t.name+\': \'+metricUnit()+\' \'+metricFmt(v))}"'
    text = exact(text, old_lrow, new_lrow, "lollipop", expected=2)

    history = re.compile(r'<circle class="trenddot" cx="\$\{p\.x\}" cy="\$\{p\.y\}" r="3\.2" stroke="\$\{color\}"><title>\$\{escapeHtml\(t\.name\)\} · \$\{p\.yr\}: \$\{fmt\(p\.v\)\} UL</title></circle>')
    replacement = '<circle class="trenddot" cx="${p.x}" cy="${p.y}" r="3.2" stroke="${color}" tabindex="0" data-atlas-tooltip="1" data-tip-title="${escapeHtml(t.name+\' · \'+p.yr)}" data-tip-value="${escapeHtml(fmt(p.v)+\' UL\')}" aria-label="${escapeHtml(t.name+\' · \'+p.yr+\': \'+fmt(p.v)+\' UL\')}"></circle>'
    text, count = history.subn(replacement, text)
    if count != 2:
        raise RuntimeError(f"Tooltip Atlante storico: attese 2 occorrenze, trovate {count}")

    text = exact(
        text,
        "let o=$('#oneTown');if(o)o.onclick=()=>{let s=state.detailTown||towns[0].slug;state.visible=new Set([s]);renderAnalysis()};\n}",
        "let o=$('#oneTown');if(o)o.onclick=()=>{let s=state.detailTown||towns[0].slug;state.visible=new Set([s]);renderAnalysis()};wireAtlasTooltips();\n}",
        "wire analisi",
    )
    text = exact(
        text,
        "function renderAll(){renderSelectors();renderCrumbs();renderDonut();renderAnalysis()}",
        "function renderAll(){renderSelectors();renderCrumbs();renderDonut();renderAnalysis();wireAtlasTooltips()}",
        "wire rendering",
    )

    if "<title>" in text:
        raise RuntimeError("Tooltip SVG nativi ancora presenti nell'Atlante")
    RUNTIME.write_text(text, encoding="utf-8")
    print("Tooltip Atlante allineati al contratto OV: navy, 8px, 9/11px, hover e focus.")


if __name__ == "__main__":
    main()
