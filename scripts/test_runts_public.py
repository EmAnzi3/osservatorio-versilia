"""Current RUNTS stock: fixed counts, denominators and hostile snapshots."""
import copy
import json
from pathlib import Path
from update_runts_public import apply, ROOT, SNAPSHOT


def main():
    data = json.loads((ROOT/'data/site-data.json').read_text())
    snapshot = json.loads((ROOT/SNAPSHOT).read_text())
    original = copy.deepcopy(data)
    result = apply(data, snapshot)
    assert data == original
    fixed = {'046005':85,'046013':24,'046018':53,'046024':67,'046028':50,'046030':13,'046033':173}
    metric = result['metrics']['thirdSector']
    assert metric['meta']['year'] == '2026-10-11'
    for r in metric['rows']:
        assert r['registeredEntities'] == fixed[r['code']]
        assert r['value'] == fixed[r['code']] / r['residentPopulation'] * 1000
        assert r['populationReference'] == '2026-01-01' and r['series'] is None
    assert sum(fixed.values()) == 465
    assert metric['aggregate']['value'] == 465 / 158520 * 1000
    for k in data['metrics']:
        if k != 'thirdSector':assert result['metrics'][k] == data['metrics'][k]
    assert apply(result, snapshot) == result
    attacks = [lambda s:s['rows'].pop(), lambda s:s['rows'][0].update(code=s['rows'][1]['code']),
        lambda s:s['rows'][0].update(count=True), lambda s:s['rows'][0].update(count=-1),
        lambda s:s['rows'][0].update(population=1), lambda s:s['rows'][0].update(populationReference='2025-01-01'),
        lambda s:s['rows'][0].update(per1000=999), lambda s:s['versilia'].update(count=464),
        lambda s:s.update(sourceSha256=''),lambda s:s.update(referenceDate='2999-01-01')]
    for attack in attacks:
        broken=copy.deepcopy(snapshot);attack(broken)
        try:apply(data,broken)
        except (ValueError,KeyError):pass
        else:raise AssertionError('Invalid RUNTS snapshot accepted')
    print('RUNTS PASS: 465 entities, 7/7 dated denominators, no inferred history; ten hostile cases and idempotence.')


if __name__ == '__main__':main()
