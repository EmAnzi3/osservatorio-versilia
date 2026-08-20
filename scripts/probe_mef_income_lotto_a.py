#!/usr/bin/env python3
"""Probe del dataset MEF comunale per la seconda tranche Lotto A.

Scarica l'archivio ufficiale 2025 a.i. 2024, individua in modo difensivo
intestazioni e righe dei sette Comuni e salva un artifact leggibile prima di
qualsiasi materializzazione nel catalogo pubblico.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'audit-artifacts' / 'mef-income-lotto-a.json'
SOURCE_PAGE = 'https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes'
SOURCE_ZIP = (
    'https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
    'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800'
)
TOWNS = [
    'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta',
    'Seravezza', 'Stazzema', 'Viareggio',
]


def norm(value: object) -> str:
    text = unicodedata.normalize('NFD', str(value or '').strip().lower())
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-LottoA/1.0'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def decode(raw: bytes) -> tuple[str, str]:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError('Impossibile decodificare il CSV MEF')


def parse_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]], dict]:
    text, encoding = decode(raw)
    sample = text[:10000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=';,\t|')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = [str(h or '').strip() for h in (reader.fieldnames or [])]
    rows = []
    for row in reader:
        rows.append({str(k or '').strip(): str(v or '').strip() for k, v in row.items()})
    return headers, rows, {'encoding': encoding, 'delimiter': delimiter, 'rowCount': len(rows)}


def score_name_header(header: str) -> int:
    h = norm(header)
    score = 0
    if 'comune' in h: score += 4
    if 'denominazione' in h or 'descrizione' in h: score += 3
    if h == 'comune': score += 2
    if 'codice' in h: score -= 4
    return score


def find_name_header(headers: list[str], rows: list[dict[str, str]]) -> str:
    candidates = sorted(headers, key=score_name_header, reverse=True)
    town_norms = {norm(town) for town in TOWNS}
    for header in candidates:
        if score_name_header(header) <= 0:
            continue
        values = {norm(row.get(header)) for row in rows}
        if len(town_norms & values) >= 5:
            return header
    # Fallback: prova tutte le colonne, utile se il MEF usa un'etichetta inattesa.
    for header in headers:
        values = {norm(row.get(header)) for row in rows}
        if len(town_norms & values) >= 5:
            return header
    raise RuntimeError('Colonna denominazione Comune non individuata')


def select_towns(rows: list[dict[str, str]], name_header: str) -> dict[str, dict[str, str]]:
    by_name: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_name.setdefault(norm(row.get(name_header)), []).append(row)
    selected = {}
    for town in TOWNS:
        matches = by_name.get(norm(town), [])
        if len(matches) != 1:
            raise RuntimeError(f'{town}: attese 1 riga, trovate {len(matches)}')
        selected[town] = matches[0]
    return selected


def columns_matching(headers: list[str], *, all_terms=(), any_terms=(), reject_terms=()) -> list[str]:
    result = []
    for header in headers:
        h = norm(header)
        if all_terms and not all(norm(term) in h for term in all_terms):
            continue
        if any_terms and not any(norm(term) in h for term in any_terms):
            continue
        if reject_terms and any(norm(term) in h for term in reject_terms):
            continue
        result.append(header)
    return result


def classify(headers: list[str]) -> dict[str, list[str]]:
    amount_words = ('ammontare', 'importo')
    frequency_words = ('frequenza', 'numero')
    return {
        'taxpayers': columns_matching(headers, all_terms=('contribuenti',), any_terms=frequency_words),
        'pension': columns_matching(headers, all_terms=('reddito', 'pensione')),
        'pensionAmount': columns_matching(headers, all_terms=('reddito', 'pensione'), any_terms=amount_words),
        'totalIncome': columns_matching(headers, all_terms=('reddito', 'complessivo')),
        'totalIncomeAmount': columns_matching(headers, all_terms=('reddito', 'complessivo'), any_terms=amount_words,
                                                    reject_terms=('minore', 'maggiore', 'da ', 'fino', 'oltre')),
        'employment': columns_matching(headers, all_terms=('reddito',), any_terms=('lavoro dipendente', 'dipendente e assimilati')),
        'selfEmployment': columns_matching(headers, all_terms=('reddito',), any_terms=('lavoro autonomo',)),
        'entrepreneur': columns_matching(headers, all_terms=('reddito',), any_terms=('imprenditore', 'impresa')),
        'participation': columns_matching(headers, all_terms=('reddito', 'partecipazione')),
        'buildings': columns_matching(headers, all_terms=('reddito', 'fabbricati')),
        'incomeBands': [
            header for header in headers
            if 'reddito complessivo' in norm(header)
            and any(token in norm(header) for token in ('minore', 'da ', 'oltre', 'fino', 'zero', '10000', '15000', '26000', '55000', '75000', '120000'))
        ],
        'frequencyColumns': [header for header in headers if any(word in norm(header) for word in frequency_words)],
        'amountColumns': [header for header in headers if any(word in norm(header) for word in amount_words)],
    }


def main() -> None:
    body = download(SOURCE_ZIP)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if not candidates:
            raise RuntimeError(f'Nessun CSV/TXT nell’archivio: {archive.namelist()}')
        # Preferisce il file più grande: evita eventuali readme accessori.
        name = max(candidates, key=lambda item: archive.getinfo(item).file_size)
        headers, rows, parsing = parse_csv(archive.read(name))

    name_header = find_name_header(headers, rows)
    towns = select_towns(rows, name_header)
    classified = classify(headers)

    artifact = {
        'schemaVersion': 1,
        'source': {
            'publisher': 'Dipartimento delle Finanze — MEF',
            'dataset': 'Redditi e principali variabili IRPEF su base comunale',
            'reference': '2025 a.i. 2024',
            'published': '2026-04-23',
            'pageUrl': SOURCE_PAGE,
            'downloadUrl': SOURCE_ZIP,
            'archiveMember': name,
        },
        'parsing': {**parsing, 'nameHeader': name_header, 'headerCount': len(headers)},
        'headers': headers,
        'classifiedColumns': classified,
        'towns': towns,
        'checks': {
            'coverage': f'{len(towns)}/7',
            'hasTaxpayerColumn': bool(classified['taxpayers']),
            'hasPensionColumns': bool(classified['pension']),
            'hasPensionAmountColumn': bool(classified['pensionAmount']),
            'hasTotalIncomeColumns': bool(classified['totalIncome']),
            'hasIncomeBands': len(classified['incomeBands']) >= 7,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(artifact['checks'], ensure_ascii=False))
    print('Colonna Comune:', name_header)
    print('Colonne pensione:', classified['pension'])
    print('Colonne reddito complessivo:', classified['totalIncome'])
    print('Colonne fasce:', classified['incomeBands'])


if __name__ == '__main__':
    main()
