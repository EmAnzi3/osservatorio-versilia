#!/usr/bin/env python3
"""RGS source contract: homonymous municipalities must retain separate employer IDs."""
from __future__ import annotations

import acquire_a3_benchmark_rgs_conto_annuale_annual as worker
import acquire_a3_benchmark_rgs_staff_per_resident as staff
import copy
import json


def main():
    def row(code, label, kind="COMUNI"):
        return {"Codice Ente BDAP":code,"Descrizione Ente":label,
                "Descrizione Tipo Istituzione":kind}

    # Castro (LE/BG): one label, distinct employers and independent dataset coverage.
    a="434642930537432001"; b="647142930520231302"
    rows=[row(a,"COMUNE DI CASTRO"),row(a,"Comune di Castro"),
          row(b,"COMUNE DI CASTRO"),row("900","UNIONE", "UNIONE DI COMUNI")]
    grouped=worker.groups(rows)
    assert set(grouped)=={a,b} and len(grouped[a])==2 and len(grouped[b])==1
    selector={"mode":"bdap-anagrafe","field":"Codice Ente BDAP"}
    regions={a:{"code":"16","label":"PUGLIA"},b:{"code":"03","label":"LOMBARDIA"}}
    codes,missing=worker.scope_codes(rows,selector,False,regions)
    assert codes=={a,b} and not missing
    codes,missing=worker.scope_codes(rows,selector,False,{a:regions[a]})
    assert codes=={a} and missing=={b}
    codes,missing=worker.scope_codes(rows,selector,True,
                                    {a:{"code":"09","label":"TOSCANA"},b:regions[b]})
    assert codes=={a} and not missing
    # An age record for one Castro cannot cover the other employer.
    age=worker.groups([row(a,"COMUNE DI CASTRO")])
    assert b not in age and a in age
    for invalid in (None,""," ","not-an-id"):
        try:
            worker.groups([row(invalid,"COMUNE DI CASTRO")])
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"Missing/invalid employer ID accepted: {invalid!r}")
    assert set(worker.groups([row(a+".0","COMUNE DI CASTRO")]))=={a}
    snapshot=json.loads(staff.FROZEN.read_text())
    metric=json.loads((staff.ROOT/'data/site-data.json').read_text())['metrics']['municipalEmployeesPer1000']
    staff.validate_snapshot(metric,snapshot)
    cases=[
        lambda m,s:s.update(referenceYear=2025),
        lambda m,s:s.update(sourceUrl='https://example.com/'),
        lambda m,s:s['source'].update(staffSha256='0'*64),
        lambda m,s:s['source'].update(populationZipBase64='AA=='),
        lambda m,s:s['geographies'].pop(),
        lambda m,s:s['explicitZeroEmployers'].pop(),
        lambda m,s:s['explicitZeroEmployers'][0].update(staff=False),
        lambda m,s:s['explicitZeroEmployers'][0].update(referenceDate='2023-12-31'),
        lambda m,s:s['explicitZeroEmployers'][0].update(pdfBase64='AA=='),
        lambda m,s:s['raw']['tuscany'].update(staff=23256),
        lambda m,s:s['benchmarks']['municipalEmployeesPer1000'].update(italy=0),
        lambda m,s:s['benchmarks']['municipalEmployeesPer1000'].update(tuscany=True),
        lambda m,s:s['benchmarks']['municipalEmployeesPer1000'].update(formula='residenti 2026'),
        lambda m,s:m['rows'].append(copy.deepcopy(m['rows'][0])),
        lambda m,s:m['rows'][0].update(residentPopulation=21782),
        lambda m,s:m['rows'][0].update(staffAt31Dec=True),
        lambda m,s:m['rows'][0].update(value=4.0),
        lambda m,s:m['meta'].update(year='2025'),
        lambda m,s:m['meta'].update(unit='count'),
    ]
    for index,mutate in enumerate(cases):
        m,s=copy.deepcopy(metric),copy.deepcopy(snapshot);mutate(m,s)
        try:staff.validate_snapshot(m,s)
        except (RuntimeError,ValueError):pass
        else:raise AssertionError(f'Invalid staff candidate accepted: {index}')
    for invalid in ('',' ',None,True,'NaN','-1','1.5'):
        try:staff.integer(invalid)
        except (RuntimeError,ValueError):pass
        else:raise AssertionError(f'Invalid native count accepted: {invalid!r}')
    print(f"RGS contract PASS: homonyms separated; 273/273 cohort, 7/7 components; {len(cases)} invalid candidates rejected")


if __name__=="__main__":
    main()
