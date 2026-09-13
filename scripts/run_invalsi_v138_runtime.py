#!/usr/bin/env python3
"""Esegue la patch runtime INVALSI sugli hook reali della pipeline v1.37.

La v1.37 genera alcuni rami profile con etichette duplicate. Inoltre il renderer
visuale condiviso viene già riscritto dalle release precedenti: per v1.38 il
lollipop mantiene Toscana come unico riferimento grafico; Italia resta nel
pannello benchmark e nello storico. Gli altri matcher restano fail-closed.
"""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/'scripts'/'patch_invalsi_v138_runtime.py'
APP03=ROOT/'assets/app-parts/03.txt'


def patch_invalsi_town_first_render() -> None:
    """Rende Toscana/Italia corretti già nel markup iniziale della scheda comune."""
    a03=APP03.read_text(encoding='utf-8')
    marker="metric.meta.compositeType==='invalsiProfile'?'Scostamento dalla Toscana':'Rispetto alla Versilia'"
    if marker in a03:
        return
    old='<span class="overline">Rispetto alla Versilia</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${html(summaryDelta.direction)}</small></strong><p>Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.</p>'
    new='<span class="overline">${metric.meta.compositeType===\'invalsiProfile\'?\'Scostamento dalla Toscana\':\'Rispetto alla Versilia\'}</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${metric.meta.compositeType===\'invalsiProfile\'?\'rispetto alla Toscana\':html(summaryDelta.direction)}</small></strong><p>${metric.meta.compositeType===\'invalsiProfile\'?`Italia: ${html(formatValue(invalsiPart(metric.nationalBenchmark,defaultTerritoryChoice).value,invalsiPart(metric.nationalBenchmark,defaultTerritoryChoice).unit||summary.unit))}. Il Comune identifica il plesso, non la residenza dello studente.`:\'Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.\'}</p>'
    count=a03.count(old)
    if count!=1:
        raise RuntimeError(f'v1.38 runner: markup comunale generico inatteso ({count})')
    APP03.write_text(a03.replace(old,new,1),encoding='utf-8')


def main():
    source=PATCH.read_text(encoding='utf-8')
    replacements=(
        (
            'label Toscana compare',
            '    a03=patch(a03,\'compositeCompareAggregate\',lambda b:once(b,"label:`Versilia · ${part.label || metric.meta.label}`","label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",\'label Toscana compare\'))\n',
            '    a03=patch(a03,\'compositeCompareAggregate\',lambda b:b.replace("label:`Versilia · ${part.label || metric.meta.label}`","label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",1))\n',
        ),
        (
            'label Toscana town',
            '    a03=patch(a03,\'compositeSelectionAggregate\',lambda b:once(b,"return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};","return {label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};",\'label Toscana town\'))\n',
            '    a03=patch(a03,\'compositeSelectionAggregate\',lambda b:b.replace("return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};","return {label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)};",1))\n',
        ),
        (
            'visual Toscana',
            '    vg=patch(vg,\'compositeAggregateFor\',lambda b:once(b,"label:`Versilia · ${part.label || metric.meta.label}`","label:type===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",\'visual Toscana\'))\n',
            '    vg=patch(vg,\'compositeAggregateFor\',lambda b:b.replace("label:`Versilia · ${part.label || metric.meta.label}`","label:type===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",1))\n',
        ),
        (
            'town visual grammar exclusion',
            '    vg=all_(vg,"\'roadNetworkProfile\'].includes(type)","\'roadNetworkProfile\',\'invalsiProfile\'].includes(type)",\'visual profile\')\n',
            '    vg=all_(vg,"\'roadNetworkProfile\'].includes(type)","\'roadNetworkProfile\',\'invalsiProfile\'].includes(type)",\'visual profile\')\n    vg=once(vg,"[\'distribution\',\'agricultureProfile\',\'ratioProfile\',\'financialProfile\',\'hydroRisk\',\'territorialClassification\',\'landCoverProfile\'].includes(metric.meta?.compositeType)","[\'distribution\',\'agricultureProfile\',\'ratioProfile\',\'financialProfile\',\'hydroRisk\',\'territorialClassification\',\'landCoverProfile\',\'invalsiProfile\'].includes(metric.meta?.compositeType)",\'town visual grammar exclusion\')\n',
        ),
        (
            'single visual reference',
            "    vg=patch(vg,'enhanceComparison',compare_vg)\n",
            "    # Toscana resta il riferimento grafico del lollipop; Italia è resa nel pannello benchmark/storico.\n",
        ),
        (
            'idempotence sentinel',
            "        for token in ('invalsiProfile','invalsi_score','nationalBenchmark','data-invalsi-national-reference'):\n",
            "        for token in ('invalsiProfile','invalsi_score','nationalBenchmark','invalsi-benchmark-detail'):\n",
        ),
    )
    for label,old,new in replacements:
        count=source.count(old)
        if count!=1:
            raise RuntimeError(f'v1.38 runner: sorgente hook {label} diversa dal contratto ({count})')
        source=source.replace(old,new,1)
    env={'__name__':'__main__','__file__':str(PATCH),'__cached__':None,'__doc__':None,'__loader__':None,'__package__':'','__spec__':None}
    exec(compile(source,str(PATCH),'exec'),env)
    patch_invalsi_town_first_render()


if __name__=='__main__': main()
