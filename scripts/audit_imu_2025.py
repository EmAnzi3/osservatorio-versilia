#!/usr/bin/env python3
"""Audit 2025 IMU rates for a standardized A/2 second home in Versilia.

Official source: Dipartimento delle Finanze - MEF, Prospetti aliquote IMU 2025.
The comparable category is "Altri fabbricati" (ordinary buildings other than
main homes and cadastral group D). The script extracts the published rate and
calculates tax on a deliberately standardized taxable base of EUR 100,000.
"""
from __future__ import annotations

import argparse, io, json, re, urllib.parse, urllib.request
from pathlib import Path
from pypdf import PdfReader

BASE = 'https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_imu/'
RESULT = BASE + 'risultato.htm?DOWNLOAD=Procedi&anno=2025&cc={code}&cm=O&lista=1&pagina=&pr=&r=2'
TOWNS = {
    'Camaiore': 'B455',
    'Forte dei Marmi': 'D730',
    'Massarosa': 'F035',
    'Pietrasanta': 'G628',
    'Seravezza': 'I622',
    'Stazzema': 'I942',
    'Viareggio': 'L833',
}
UA = {'User-Agent': 'OsservatorioVersilia-data-audit/1.0'}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def pdf_link(html: str, page_url: str) -> str:
    hrefs = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', html, flags=re.I)
    # Prospetti are small DIMUNIC PDFs. Prefer them to regulations/other docs.
    preferred = [h for h in hrefs if 'DIMUNIC' in h.upper()]
    candidates = preferred or hrefs
    if not candidates:
        raise RuntimeError(f'nessun prospetto PDF trovato in {page_url}')
    return urllib.parse.urljoin(page_url, candidates[0])


def extract_text(pdf: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf))
    return '\n'.join((page.extract_text() or '') for page in reader.pages)


def parse_rate(text: str) -> float:
    clean = re.sub(r'\s+', ' ', text.replace('\xa0', ' '))
    # The standardized MEF prospetto prints the category followed by the rate.
    patterns = [
        r'Altri\s+fabbricati.*?Aliquota\s*[:\-]?\s*([0-9]+(?:[,.][0-9]+)?)\s*%',
        r'Altri\s+fabbricati.*?([0-9]+(?:[,.][0-9]+)?)\s*%',
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, flags=re.I)
        if match:
            value = float(match.group(1).replace(',', '.'))
            if 0 <= value <= 2:
                return value
    # Debug context makes schema changes visible in Actions logs.
    match = re.search(r'Altri\s+fabbricati', clean, flags=re.I)
    context = clean[max(0, match.start()-200):match.start()+900] if match else clean[:1200]
    raise RuntimeError(f'aliquota Altri fabbricati non individuata. Contesto: {context}')


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('/tmp/imu-2025.json'))
    args = p.parse_args()
    rows = {}
    for town, code in TOWNS.items():
        page_url = RESULT.format(code=code)
        html = fetch(page_url).decode('utf-8', errors='replace')
        if town.upper() not in re.sub(r'<[^>]+>', ' ', html).upper():
            raise RuntimeError(f'{town}: pagina MEF inattesa')
        doc_url = pdf_link(html, page_url)
        text = extract_text(fetch(doc_url))
        rate = parse_rate(text)
        rows[town] = {
            'belfiore': code,
            'ratePercent': rate,
            'standardTaxableBase': 100000,
            'annualTax': round(100000 * rate / 100, 2),
            'sourcePage': page_url,
            'sourcePdf': doc_url,
        }
        print(f'{town}: {rate:.4f}% -> EUR {rows[town]["annualTax"]:.2f}')
    snapshot = {
        'schemaVersion': 1,
        'year': 2025,
        'source': 'Dipartimento delle Finanze - MEF',
        'category': 'Altri fabbricati',
        'standard': 'Seconda abitazione A/2; base imponibile IMU standardizzata EUR 100.000',
        'coverage': f'{len(rows)}/7',
        'towns': rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if len(rows) != 7:
        raise SystemExit(2)
    print(f'IMU audit OK: {len(rows)}/7; snapshot={args.out}')


if __name__ == '__main__':
    main()
