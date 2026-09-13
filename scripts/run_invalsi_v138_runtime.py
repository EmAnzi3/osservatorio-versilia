#!/usr/bin/env python3
"""Esegue la patch runtime INVALSI adattando solo gli hook noti della v1.37.

La v1.37 genera alcuni rami profile con etichette testualmente duplicate nella
stessa funzione. Per quei soli tre hook usiamo la prima occorrenza del ramo
profile; tutti gli altri matcher della patch v1.38 restano fail-closed.
"""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/'scripts'/'patch_invalsi_v138_runtime.py'


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
    )
    for label,old,new in replacements:
        count=source.count(old)
        if count!=1:
            raise RuntimeError(f'v1.38 runner: sorgente hook {label} diversa dal contratto ({count})')
        source=source.replace(old,new,1)
    env={'__name__':'__main__','__file__':str(PATCH),'__cached__':None,'__doc__':None,'__loader__':None,'__package__':'','__spec__':None}
    exec(compile(source,str(PATCH),'exec'),env)


if __name__=='__main__': main()
