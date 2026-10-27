#!/usr/bin/env python3
"""Etichette italiane per i dettagli (dimensioni) e i periodi mostrati in «Chiedi».

Sono soltanto parole per la lettura pubblica: non cambiano richieste, dati o
calcoli. Le chiavi originali restano nell'evidenza. Un codice non previsto
qui fa fallire il gate `test_a7_plain_language.py` invece di comparire a video.
"""
from __future__ import annotations

import base64
import gzip
import json
import re
from datetime import date
from pathlib import Path

SEX = {'men': 'uomini', 'women': 'donne', 'total': 'uomini e donne'}
HAZARD = {'P1': 'pericolosità bassa', 'P2': 'pericolosità media', 'P3': 'pericolosità elevata',
          'P4': 'pericolosità molto elevata', 'P3+P4': 'pericolosità elevata e molto elevata',
          'AA': 'aree di attenzione'}
HAZARD_KIND = {'residentsPct': 'quota di residenti esposti', 'residents': 'residenti esposti',
               'areaPct': 'quota di territorio', 'areaKm2': 'superficie (km²)'}
FAMILY = {'europee': 'Elezioni europee', 'politiche_camera': 'Elezioni politiche (Camera)',
          'referendum': 'Referendum', 'regionali_toscana': 'Elezioni regionali'}
SUBJECT = {'italiano': 'italiano', 'matematica': 'matematica', 'inglese-reading': 'inglese (lettura)',
           'inglese-listening': 'inglese (ascolto)'}
GRADE = {'g2': '2ª primaria', 'g5': '5ª primaria', 'g8': '3ª media', 'g10': '2ª superiore', 'g13': '5ª superiore'}
QUALITY = {'excellent': 'eccellente', 'good': 'buona', 'sufficient': 'sufficiente', 'poor': 'scarsa', 'total': 'totale'}
SHORE = {'erosion': 'in erosione', 'stable': 'stabile', 'advance': 'in avanzamento', 'total': 'totale'}
BAND = {'le0': 'reddito nullo o negativo', '0to10k': 'fino a 10.000 €', '10to15k': '10.000–15.000 €',
        '15to26k': '15.000–26.000 €', '26to55k': '26.000–55.000 €', '55to75k': '55.000–75.000 €',
        '75to120k': '75.000–120.000 €', 'over120k': 'oltre 120.000 €'}
MACRO = {'0': 'fino a 15.000 €', '1': '15.000–26.000 €', '2': '26.000–55.000 €', '3': 'oltre 55.000 €'}
SOURCE = {'employment': 'lavoro dipendente', 'pension': 'pensione', 'selfEmployment': 'lavoro autonomo',
          'entrepreneurOrdinary': 'impresa (contabilità ordinaria)',
          'entrepreneurSimplified': 'impresa (contabilità semplificata)',
          'participation': 'partecipazione in società', 'buildings': 'fabbricati'}
HECTARES = {'agricultural': 'aree agricole', 'anpil': 'ANPIL', 'artificialized': 'aree artificiali',
            'forest': 'boschi', 'forest_seminatural_total': 'boschi e aree seminaturali',
            'natura2000': 'Natura 2000', 'parksReserves': 'parchi e riserve', 'permanent_crops': 'colture permanenti',
            'ramsar': 'zone Ramsar', 'seminativi': 'seminativi', 'seminatural_nonforest': 'aree seminaturali non boscate',
            'total': 'totale', 'urban_green_cartographic': 'verde urbano', 'water': 'acque', 'wetlands': 'zone umide',
            'zps': 'ZPS', 'zsc': 'ZSC'}
MEASURE = {'incidents': 'incidenti', 'injured': 'feriti', 'injury': 'indice di lesività', 'mortality': 'indice di mortalità',
           'meanMen': 'media uomini', 'meanWomen': 'media donne', 'meanTotalRgs': 'media complessiva',
           'totalDays': 'giorni totali'}
PART = {
    'structural': 'indice di dipendenza strutturale', 'elderly': 'anziani', 'recoveryPerResident': 'recupero per residente',
    'recoveryTotal': 'recupero totale', 'daitContribution': 'contributo statale', 'arrivals': 'arrivi',
    'departures': 'partenze', 'balance': 'saldo', 'births': 'nascite', 'deaths': 'decessi', 'forest': 'boschi',
    'seminativi': 'seminativi', 'permanent_crops': 'colture permanenti',
    'seminatural_nonforest': 'aree seminaturali non boscate', 'urban_green_cartographic': 'verde urbano',
    'yes': 'sì', 'no': 'no', 'undefined': 'non indicato', 'builtBy1970': 'costruiti entro il 1970',
    'before1800': 'prima del 1800', 'canteen': 'mensa', 'gym': 'palestra', 'fullOccupancy': 'agibilità',
    'cpi': 'certificato prevenzione incendi', 'scia': 'SCIA antincendio', 'renewal': 'rinnovo antincendio',
    'schoolBus': 'scuolabus', 'urban': 'trasporto urbano', 'interurban': 'trasporto extraurbano',
    'families-minors': 'famiglie e minori', 'disability': 'disabilità', 'addictions': 'dipendenze',
    'immigration': 'immigrazione', 'poverty-hardship': 'povertà e disagio', 'multiuser': 'più utenze',
    'degurba': 'grado di urbanizzazione', 'littoral': 'comune litoraneo', 'coastalZone': 'zona costiera',
}
VIEW = {
    'normalized': 'in rapporto ai residenti', 'hectares': 'ettari', 'percent': 'percentuale',
    'sqmPerResident': 'm² per residente', 'net': 'netto', 'gross': 'lordo', 'full': 'rete completa',
    'managed': 'rete gestita', 'density': 'densità', 'length': 'lunghezza', 'adminMunicipal': 'strade comunali',
    'adminProvincial': 'strade provinciali', 'adminRegional': 'strade regionali', 'adminState': 'strade statali',
    'adminPrivate': 'strade private', 'paved': 'strade asfaltate', 'unpaved': 'strade non asfaltate',
    'pavementUnclassified': 'fondo non classificato', 'protectedKm': 'costa protetta (km)', 'coastKm': 'costa (km)',
    'analysedKm': 'costa analizzata (km)', 'tourist': 'concessioni turistiche', 'touristDue': 'canoni turistici',
    'minimumCount': 'concessioni con canone minimo', 'expiryMissing': 'scadenza non indicata',
    'mean': 'canone medio', 'touristMean': 'canone medio turistico', 'median': 'canone mediano',
    'active': 'attivi', 'closed': 'chiusi', 'all': 'tutti',
    'state_active': 'siti attivi', 'state_inactive': 'siti inattivi', 'state_suspended': 'siti sospesi',
    'state_expired': 'autorizzazione scaduta', 'state_restoration': 'in ripristino', 'state_closed': 'siti chiusi',
    'state_nd': 'stato non indicato', 'type_ordinary': 'cave ordinarie', 'type_restoreworks': 'opere di ripristino',
    'type_recovery': 'recupero', 'prod_ornamental': 'materiali ornamentali', 'prod_industrial': 'materiali industriali',
    'prod_construction': 'materiali per costruzioni',
    'g_ha': 'giacimenti (ettari)', 'g_pct': 'giacimenti (%)', 'g_n': 'giacimenti (numero)',
    'gp_ha': 'giacimenti potenziali (ettari)', 'gp_pct': 'giacimenti potenziali (%)', 'gp_n': 'giacimenti potenziali (numero)',
    'acc_ha': 'aree di cava (ettari)', 'acc_pct': 'aree di cava (%)', 'acc_n': 'aree di cava (numero)',
    'mos': 'materiali ornamentali storici', 'pmos': 'potenziali materiali ornamentali storici', 'sed': 'siti estrattivi dismessi',
}
SHARE = {'g': 'quota giacimenti', 'gp': 'quota giacimenti potenziali', 'acc': 'quota aree di cava',
         'touristDue': 'quota canoni turistici', 'tourist': 'quota concessioni turistiche', 'minimum': 'quota canone minimo',
         'active': 'quota attivi', 'operational': 'quota operativa', 'all': 'quota sul totale campioni',
         'routine': 'quota campioni di routine', 'supplementary': 'quota campioni suppletivi'}
SINGLE = {
    'total': 'Dato complessivo', 'territoryTotal': 'Totale del territorio', 'nativeRatio': 'calcolato dai conteggi',
    'count': 'numero', 'nominal': 'valori nominali', 'staff': 'dipendenti', 'residents': 'residenti',
    'headcount': 'personale in servizio', 'hires': 'assunzioni', 'cessations': 'cessazioni',
    'saleMean': 'vendita (media €/m²)', 'rentMean': 'affitto (media €/m² al mese)', 'ratePercent': 'aliquota (%)',
    'concludedProjects': 'progetti conclusi', 'selectedProjects': 'progetti selezionati', 'fundingEuro': 'risorse (€)',
    'registeredEntities': 'enti iscritti', 'normalized': 'in rapporto ai residenti',
}
LAYER = {'area': 'elementi areali', 'line': 'elementi lineari', 'point': 'elementi puntuali'}
SECTOR = {'industry': 'industria', 'services': 'servizi'}
FUEL = {'benzina': 'benzina', 'gasolio': 'gasolio'}
STAT = {'min': 'valore minimo', 'mean': 'valore medio', 'max': 'valore massimo'}
MONTHS = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
          'settembre', 'ottobre', 'novembre', 'dicembre']


def age(value):
    m = re.fullmatch(r'(\d+)-(\d+)', value)
    if m:
        return f'{m[1]}–{m[2]} anni'
    m = re.fullmatch(r'(\d+)(?:plus|\+)', value)
    if m:
        return f'{m[1]} anni e oltre'
    m = re.fullmatch(r'age(\d+)to(\d+)', value)
    if m:
        return f'{m[1]}–{m[2]} anni'
    m = re.fullmatch(r'age(\d+)plus', value)
    if m:
        return f'{m[1]} anni e oltre'
    m = re.fullmatch(r'under(\d+)', value)
    if m:
        return f'meno di {m[1]} anni'
    raise KeyError(value)


def invalsi(value):
    grade, _, subject = value.partition('-')
    return GRADE[grade] + (' · ' + SUBJECT[subject] if subject else '')


def ateco_label(code, taxonomy):
    letter, _, digits = code.partition(' ')
    if not digits:
        return taxonomy[letter]
    groups = [digits[:2]] + ([digits[2:4]] if len(digits) >= 4 else [digits[2:]] if len(digits) == 3 else []) + ([digits[4:]] if len(digits) > 4 else [])
    dotted = '.'.join(g for g in groups if g)
    return dotted + ' ' + taxonomy[dotted]


def sentence(text):
    text = text.strip()
    text = text[:1] + text[1:].lower() if text.isupper() else text
    head, _, rest = text.partition(' ')
    return head + (' ' + rest[:1].upper() + rest[1:] if rest else '')


def part_label(key, value, taxonomy):
    if key == 'sex': return SEX[value]
    if key == 'age': return age(value)
    if key == 'family': return FAMILY[value]
    if key in HAZARD_KIND: return HAZARD_KIND[key] + ' · ' + HAZARD[value]
    if key == 'history':
        kind, _, cls = value.partition(':')
        return 'Serie storica · ' + HAZARD_KIND[kind] + ' · ' + HAZARD[cls]
    if key == 'view':
        if re.fullmatch(r'g\d+(-.+)?', value): return invalsi(value)
        return VIEW[value]
    if key == 'level': return 'livello ' + value.split('-')[1]
    if key == 'part':
        if re.fullmatch(r'\d{4}-\d{4}', value): return 'costruiti fra il ' + value.replace('-', ' e il ')
        return PART[value]
    if key == 'share':
        kind, _, quality = value.partition(':')
        if quality: return ('quota aree' if kind == 'areas' else 'quota km di costa') + ' · ' + QUALITY[quality]
        return 'quota ' + SHORE[value] if value in SHORE else SHARE[value]
    if key == 'count':
        kind, _, quality = value.partition(':'); return 'numero di aree · ' + QUALITY[quality]
    if key == 'kilometres': return 'km di costa · ' + (QUALITY.get(value) or SHORE[value])
    if key in ('nonCompliant', 'samples'):
        return ('campioni non conformi' if key == 'nonCompliant' else 'campioni') + ' · ' + {'all': 'tutti', 'routine': 'di routine', 'supplementary': 'suppletivi'}[value]
    if key == 'hectares': return 'ettari · ' + HECTARES[value]
    if key == 'measure': return MEASURE[value]
    if key == 'band': return BAND[value]
    if key == 'macro': return 'fascia ' + MACRO[value]
    if key == 'source': return SOURCE[value]
    if key == 'layer': return LAYER[value]
    if key == 'sector': return SECTOR[value]
    if key == 'fuel': return FUEL[value] + ' · ultimo giorno disponibile'
    if key == 'monthly': return FUEL[value] + ' · media mensile'
    if key == 'stat': return STAT[value]
    if key == 'trend': return 'variazione ' + value.replace('-', '–')
    if key == 'trend_percent': return 'variazione percentuale ' + value.replace('-', '–')
    if key == 'days': return 'giorni di formazione · ' + SEX[value]
    if key == 'income': return 'reddito di ' + f'{int(value):,}'.replace(',', '.') + ' €'
    if key == 'effectiveRate': return 'aliquota effettiva su ' + f'{int(value):,}'.replace(',', '.') + ' €'
    if key == 'ateco': return 'ATECO ' + sentence(ateco_label(value, taxonomy))
    raise KeyError(f'{key}:{value}')


def dimension_label(dimension, taxonomy=None):
    if dimension in SINGLE:
        return SINGLE[dimension][:1].upper() + SINGLE[dimension][1:]
    labels = []
    for token in dimension.split('|'):
        if token in ('active', 'artisan'):
            labels.append('unità locali attive' if token == 'active' else 'imprese artigiane'); continue
        if token in SINGLE:
            labels.append(SINGLE[token].lower() if token == 'total' else SINGLE[token]); continue
        key, sep, value = token.partition(':')
        if not sep:
            raise KeyError(token)
        labels.append(part_label(key, value, taxonomy or {}))
    text = ' · '.join(labels)
    return text[:1].upper() + text[1:]


def period_label(period):
    period = str(period)
    m = re.fullmatch(r'([a-z_]+)-(\d{4})(\d{2})(\d{2})(?:-q(\d+))?', period)
    if m and m[1] in FAMILY:
        d = date(int(m[2]), int(m[3]), int(m[4]))
        text = f'{FAMILY[m[1]]} · {d.day} {MONTHS[d.month - 1]} {d.year}'
        return text + (f' · quesito {m[5]}' if m[5] else '')
    m = re.fullmatch(r'(\d{4})-S([12])', period)
    if m:
        return f'{m[2]}° semestre {m[1]}'
    m = re.fullmatch(r'PRC-(\d{4})', period)
    if m:
        return f'Piano regionale cave {m[1]}'
    m = re.fullmatch(r'(\d{4})-(map|census)/(\d{4})-boundaries', period)
    if m:
        return f'{m[1]} ({"mappa" if m[2] == "map" else "censimento"}) · confini {m[3]}'
    return None


def ateco_taxonomy(dist):
    folder = Path(dist)/'data/economy-atlas'
    parts = sorted(folder.glob('ateco-taxonomy-*.b64'))
    if not parts:
        return {}
    return json.loads(gzip.decompress(base64.b64decode(b''.join(p.read_bytes().strip() for p in parts))))


TECHNICAL = re.compile(r'\w:\w|[|_]|\b[a-z]+[A-Z][a-zA-Z]*\b|nativeRatio')


def is_public(text):
    return bool(text) and not TECHNICAL.search(text)
