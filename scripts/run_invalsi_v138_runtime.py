#!/usr/bin/env python3
"""Esegue la patch runtime INVALSI adattando solo gli hook noti della v1.37."""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/'scripts'/'patch_invalsi_v138_runtime.py'


def main():
    source=PATCH.read_text(encoding='utf-8')
    rows=source.splitlines(keepends=True)
    hits=[i for i,row in enumerate(rows) if "'label Toscana compare'" in row]
    if len(hits)!=1:
        raise RuntimeError(f'v1.38 runner: hook label Toscana compare inatteso: {len(hits)}')
    i=hits[0]
    old='    a03=patch(a03,\'compositeCompareAggregate\',lambda b:once(b,"label:`Versilia · ${part.label || metric.meta.label}`","label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",\'label Toscana compare\'))\n'
    new='    a03=patch(a03,\'compositeCompareAggregate\',lambda b:b.replace("label:`Versilia · ${part.label || metric.meta.label}`","label:metric.meta.compositeType===\'invalsiProfile\'?`${metric.aggregate?.label||\'Toscana\'} · ${part.label||metric.meta.label}`:`Versilia · ${part.label||metric.meta.label}`",1))\n'
    if rows[i]!=old:
        raise RuntimeError('v1.38 runner: sorgente hook Toscana compare diverso dal contratto')
    rows[i]=new
    source=''.join(rows)
    env={'__name__':'__main__','__file__':str(PATCH),'__cached__':None,'__doc__':None,'__loader__':None,'__package__':'','__spec__':None}
    exec(compile(source,str(PATCH),'exec'),env)


if __name__=='__main__': main()
