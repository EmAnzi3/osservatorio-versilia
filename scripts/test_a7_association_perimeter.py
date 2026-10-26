#!/usr/bin/env python3
"""A7.5.4 — perimetro preparato degli incroci: revisione e misura sul catalogo effettivo.

Il perimetro coincide con le associazioni che A6 calcola fra le domande
verificate. Non è una ricerca di coppie e non ordina coefficienti: se A6 rende
calcolabile un'altra coppia, questo gate fallisce e chiede una revisione esplicita
invece di allargare il perimetro da solo. Il motivo è riscritto in italiano come
nuova richiesta esatta; selettori, asse e metodo restano quelli verificati e il
risultato numerico deve coincidere con quello della richiesta originale.
"""
import argparse
import copy
import json
import re
import tempfile
from pathlib import Path

from a7_query_workbench import QueryWorkbench, validate_plan
from build_a7_query_runtime import build
from build_territorial_dossier_evidence import portable_evidence
from semantic_query_engine import ROOT
from semantic_question_suite import QUESTIONS, check_expected

PERIMETER = ROOT/'ci/a7-association-perimeter.json'
# Costo misurato il 26/10/2026: 6 componenti, +39 KB gzip di blocchi e +4,5 KB di
# manifest rispetto allo stesso runtime senza piano. Il margine evita falsi
# allarmi da variazioni di compressione, non autorizza nuove componenti.
MAX_ASSOCIATION_GZIP_BYTES = 80_000
MAX_ASSOCIATION_RELEASE_BYTES = 12_000
ENGLISH = re.compile(r'\b(the|and|no|of|with|retained|interpretation|descriptive|example|technical)\b', re.I)


def without_purpose(request):
    clone = copy.deepcopy(request)
    clone.pop('purpose', None)
    return clone


def without_purpose_echo(value):
    """La risposta ripete il motivo dichiarato; ogni altro campo deve coincidere."""
    if isinstance(value, dict):
        return {k: without_purpose_echo(v) for k, v in value.items() if k != 'purpose'}
    if isinstance(value, list):
        return [without_purpose_echo(v) for v in value]
    return value


def verify(catalog):
    plan = json.loads(PERIMETER.read_text(encoding='utf-8'))
    validate_plan(plan)
    verified = [q for q in json.loads(QUESTIONS.read_text(encoding='utf-8'))['questions']
                if (q.get('query') or {}).get('operation') == 'correlation']
    computable = [q for q in verified if q['expected']['status'] == 'computed']
    by_id = {q['id']: q for q in verified}
    ids = [step['id'] for step in plan['steps']]
    assert ids == [q['id'] for q in computable], (
        'perimetro_da_rivedere: le associazioni calcolabili verificate in A6 sono cambiate', ids)

    workbench = QueryWorkbench(catalog)
    for step in plan['steps']:
        case = by_id[step['id']]
        request = step['request']
        assert without_purpose(request) == without_purpose(case['query']), ('richiesta_modificata', step['id'])
        purpose = request['purpose']
        assert purpose.strip() == purpose and 40 <= len(purpose) <= 240, ('motivo', step['id'])
        assert not ENGLISH.search(purpose), ('motivo_non_italiano', step['id'], purpose)
        assert re.search(r'\bnessun[ao]?\b', purpose), ('motivo_senza_limite_causale', step['id'])
        italian = workbench.engine.query(copy.deepcopy(request))
        original = workbench.engine.query(copy.deepcopy(case['query']))
        assert italian['status'] == 'computed', (step['id'], italian.get('reasons'))
        assert not check_expected(italian, case['expected']), step['id']
        assert italian['result']['n'] == len(workbench.engine.codes), step['id']
        assert without_purpose_echo(portable_evidence(italian)) == without_purpose_echo(portable_evidence(original)), (
            'risultato_diverso_dalla_richiesta_verificata', step['id'])

    with tempfile.TemporaryDirectory(prefix='a7-perimeter-') as folder:
        base = Path(folder)
        _, without = build(catalog, base/'senza', metrics=['population'], max_views=1, profiles=('current',))
        _, with_plan = build(catalog, base/'con', metrics=['population'], max_views=1, profiles=('current',),
                             association_plan=plan)
    assert with_plan['profiles']['association'] == len(plan['steps'])
    assert with_plan['statuses'].get('not_computable', 0) == without['statuses'].get('not_computable', 0)
    added_gzip = with_plan['gzipBytes'] - without['gzipBytes']
    added_release = with_plan['releaseBytes'] - without['releaseBytes']
    assert 0 < added_gzip <= MAX_ASSOCIATION_GZIP_BYTES, added_gzip
    assert 0 < added_release <= MAX_ASSOCIATION_RELEASE_BYTES, added_release
    return dict(components=len(plan['steps']), addedGzipBytes=added_gzip, addedReleaseBytes=added_release)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT/'dist/data/site-data.json')
    report = verify(parser.parse_args().catalog)
    print('A7 perimetro incroci PASS: '
          f"{report['components']} associazioni calcolabili verificate, motivi in italiano, risultati invariati; "
          f"+{report['addedGzipBytes']} byte gzip di risposte, +{report['addedReleaseBytes']} byte di manifest")


if __name__ == '__main__':
    main()
