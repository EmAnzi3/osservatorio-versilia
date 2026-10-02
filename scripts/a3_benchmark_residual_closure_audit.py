#!/usr/bin/env python3
"""Derived residual diagnosis; never relabels the matrix or declares acquisition."""
from __future__ import annotations
import argparse, collections, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def diagnose(metric, profile, metric_id, evidence):
    meta = metric.get('meta') or {}
    for path in sorted((ROOT / 'data/source-snapshots').glob('a3-*-benchmark-*.json')):
        snapshot = json.loads(path.read_text())
        blocked = (snapshot.get('blocked') or {}).get(metric_id)
        if isinstance(blocked, str):
            return 'DOCUMENTED_SOURCE_OR_DEFINITION_BLOCKER', blocked, str(path.relative_to(ROOT))
    reference = metric.get('sourceUrl') or ''
    if profile == 'openbdap-annual':
        snapshot = evidence['profiles'][profile]['evidenceSnapshot']
        raw = json.loads((ROOT / snapshot).read_text())
        blocked = (raw.get('blocked') or {}).get(metric_id)
        if blocked:
            missing = ', '.join(f"{x['name']} ({x['code']})" for x in raw.get('missingMunicipalities', []))
            return 'INCOMPLETE_COVERAGE', blocked['reason'] + '; missing: ' + missing, snapshot
        reason = (raw.get('notAttempted') or {}).get(metric_id)
        if reason:
            return 'DEFINITION_OR_SOURCE_CONTRACT_UNRESOLVED', reason, snapshot
    if meta.get('ordinalScale'):
        return 'ORDINAL_SCALE_INCOMPATIBLE_WITH_CARDINAL_SCALAR', (metric.get('method') or {}).get('caveat','') + ' Nessun benchmark regionale/nazionale omogeneo certificato.', reference
    if meta.get('compositeType') and meta['compositeType'] != 'sexBreakdown':
        return 'COMPOSITE_METRIC_INCOMPATIBLE_WITH_SCALAR_BENCHMARK', f"Contratto {meta['compositeType']}: il benchmark scalare non identifica componente/scenario/unità selezionati; il confronto tematico esclude i compositi da benchmarkMarkup. Nessuna modifica A5 autorizzata.", 'assets/app-parts/03.txt'
    observed = evidence['profiles'].get(profile) or {}
    if metric_id in (observed.get('blocked') or {}):
        return 'SOURCE_AGGREGATION_OR_COVERAGE_UNRESOLVED', observed['blocked'][metric_id], f"workflow {observed['workflowRun']} / artifact {observed['artifactId']}"
    if profile == 'istat-commuting-irregular' and observed.get('error'):
        return 'ENDPOINT_UNRESOLVED', observed['error'], f"workflow {observed['workflowRun']} / artifact {observed['artifactId']}"
    if profile == 'aci-istat-annual' and observed.get('error'):
        return 'MUNICIPAL_GRANULARITY_UNAVAILABLE_IN_TESTED_WORKBOOK', observed['error'], f"workflow {observed['workflowRun']} / artifact {observed['artifactId']}"
    return 'REQUIRES_SOURCE_AUDIT', 'Fonte/definizione aggregata e riconciliazione comunale non ancora certificate: non è prova di indisponibilità del dato.', reference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--backlog', type=Path, required=True)
    parser.add_argument('--json-output', type=Path, required=True)
    parser.add_argument('--markdown-output', type=Path, required=True)
    args = parser.parse_args()
    site = json.loads(args.data.read_text())
    backlog = json.loads(args.backlog.read_text())
    evidence = json.loads((ROOT / 'data/source-snapshots/a3-benchmark-residual-evidence.json').read_text())
    rows = []
    for profile in backlog['profiles']:
        for pair in profile['pairs']:
            mid = pair['metricId']
            if mid not in site['metrics']: raise RuntimeError(f'Residual metric absent: {mid}')
            category, reason, proof = diagnose(site['metrics'][mid], profile['sourceProfileId'], mid, evidence)
            rows.append({'metricId':mid, 'sourceProfileId':profile['sourceProfileId'], 'matrixState':'AVAILABLE_MISSING', 'diagnosis':category, 'reason':reason, 'evidence':proof})
    if len(rows) != backlog['summary']['availableMissing'] or len({x['metricId'] for x in rows}) != len(rows):
        raise RuntimeError('Residual audit/backlog coverage mismatch')
    counts = dict(sorted(collections.Counter(x['diagnosis'] for x in rows).items()))
    unresolved = counts.get('REQUIRES_SOURCE_AUDIT',0)
    # A diagnosis documents a present blocker, not proof that every source route is exhausted.
    payload = {'schemaVersion':1, 'dimension':'benchmark_toscana_italia', 'residualCount':len(rows), 'diagnosisCounts':counts,
        'documentedBlockers':len(rows)-unresolved, 'requiresSourceAudit':unresolved, 'closureReady':False,
        'closureReason':'Source exhaustion and all remaining acquisitions are not certified; diagnosis does not change matrix states or count as ACQUIRED.', 'rows':rows}
    args.json_output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    lines=['# A3 benchmark — residual closure audit', '', f"Residui: **{len(rows)}** · blocchi documentati: **{len(rows)-unresolved}** · audit fonte ancora necessario: **{unresolved}**", '', '**A3 non chiusa.** Le diagnosi non modificano stati della matrice né contatori di acquisizione.', '', '| Indicatore | Diagnosi | Evidenza |', '|---|---|---|']
    lines += [f"| `{x['metricId']}` | {x['diagnosis']} | {x['reason'].replace('|','/').replace(chr(10),' ')} — {x['evidence']} |" for x in rows]
    args.markdown_output.write_text('\n'.join(lines)+'\n')
    print(f'A3 residual audit: {len(rows)} rows; {len(rows)-unresolved} documented blockers; {unresolved} require source audit; closureReady=false.')

if __name__ == '__main__': main()
