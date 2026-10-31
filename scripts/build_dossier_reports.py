#!/usr/bin/env python3
"""Dossier tematici in forma di relazione divulgativa.

Dossier: «Abitare in Versilia» (casa e affitti) e «Lavorare in Versilia»
(lavoro e redditi). Ogni cifra viene da una
risposta calcolata dal motore A6 sullo stesso catalogo del sito; le frasi sono
modelli fissi che dichiarano periodo, confronto e limiti, senza attribuire
cause. I testi «Perché conta» sono editoriali e non contengono numeri.

La pagina è generata dentro la shell nativa del sito, con una versione per la
Versilia e una per ciascun Comune (selettore), un PDF della versione Versilia e
un CSV dei dati usati. Nessun collegamento a GitHub, nessun JSON scaricabile.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import html
import io
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from a7_query_workbench import QueryWorkbench
from site_chrome import extract_native_shell

ROOT = Path(__file__).resolve().parents[1]
LIMITS = ROOT / 'experiments/a7-guided-explorer/limits-it.mjs'
CSS = ROOT / 'assets/dossier-report.css'
JS = ROOT / 'assets/dossier-report.js'
BASE_URL = 'https://osservatorioversilia.it/dossier/'
EXAMPLE_M2 = 80
SOURCE_NAMES = [
    ('MATPEN', 'Istat — Pendolarismo per lavoro, Censimento 2021'),
    ('DICA_ASIA', 'Istat — Registro delle unità locali delle imprese (ASIA)'),
    ('risultati-economici-delle-imprese', 'Istat — Risultati economici delle imprese sul territorio'),
    ('SDMXWS', 'Istat — Censimento permanente: occupazione e disoccupazione'),
    ('PERMPOP/SUBCOM', 'Istat — Censimento permanente della popolazione e delle abitazioni'),
    ('Capacity', 'Istat — Capacità degli esercizi ricettivi'),
    ('capacita-degli-esercizi', 'Istat — Capacità degli esercizi ricettivi'),
    ('agenziaentrate.gov.it', 'Agenzia delle Entrate — Osservatorio del mercato immobiliare (OMI)'),
    ('finanze.gov.it', 'Ministero dell’Economia e delle Finanze — Dichiarazioni dei redditi su base comunale'),
    ('demo.istat.it', 'Istat — Popolazione residente e bilancio demografico'),
    ('ars.toscana.it', 'Agenzia regionale di sanità della Toscana (ARS)'),
    ('dati.salute.gov.it', 'Ministero della Salute — Anagrafe delle farmacie'),
    ('dati.toscana.it', 'Regione Toscana — Servizi educativi per la prima infanzia'),
    ('dati.istruzione.it', 'Ministero dell’Istruzione e del Merito — Open data della scuola'),
    ('invalsi', 'INVALSI — Risultati delle prove nazionali'),
    ('misura-comune', 'Istat — Spesa dei Comuni per i servizi sociali'),
    ('regione.toscana.it', 'Regione Toscana — Movimento turistico nelle strutture ricettive'),
    ('openbdap.rgs.mef.gov.it', 'Ragioneria Generale dello Stato — Rendiconti dei Comuni (OpenBDAP)'),
    ('erplucca.it', 'ERP Lucca — Bilanci e rendiconti dell’edilizia residenziale pubblica'),
]
TENS = ['nessuna', 'una', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove']


# ---------------------------------------------------------------------------
# Formattazione italiana: al massimo due decimali, separatori it-IT.

def num(value: float, decimals: int = 0) -> str:
    text = f'{value:,.{decimals}f}'
    return text.replace(',', ' ').replace('.', ',').replace(' ', '.')


def pct(value: float, decimals: int = 1) -> str:
    return num(value, decimals) + '%'


def signed(value: float, decimals: int = 1) -> str:
    shown = round(value, decimals)
    return ('+' if shown > 0 else '−' if shown < 0 else '') + num(abs(shown), decimals)


def _elides(text: str) -> bool:
    """«otto», «undici», «ottanta»…: davanti a queste cifre l’articolo si apostrofa."""
    whole = text.split(',')[0].replace('.', '')
    return text.startswith('8') or whole == '11' or whole.startswith('11') and len(whole) in (4, 7)


def il(text: str) -> str:
    return ('l’' if _elides(text) else 'il ') + text


def al(text: str) -> str:
    return ('all’' if _elides(text) else 'al ') + text


def del_(text: str) -> str:
    whole = text.split(',')[0].replace('.', '')
    if whole == '0':
        return 'dello ' + text
    return ('dell’' if _elides(text) or whole == '1' else 'del ') + text


def dal(text: str) -> str:
    return ('dall’' if _elides(text) else 'dal ') + text


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def slug(name: str) -> str:
    return re.sub(r'[^a-z]+', '-', name.lower()).strip('-')


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' e ' + names[-1]


def ordinal(rank: int) -> str:
    return f'{rank}°'


def source_name(url: str) -> str:
    for pattern, name in SOURCE_NAMES:
        if pattern in url:
            return name
    raise ValueError('fonte_senza_nome_pubblico:' + url)


# ---------------------------------------------------------------------------
# Accesso al motore: soltanto risposte calcolate, avvertenze raccolte.

@dataclass
class Measure:
    key: str
    metric: str
    dimension: str
    label: str
    unit: str
    decimals: int
    period: str
    values: dict[str, float]
    ranking: list[tuple[str, float, int]]
    source: str
    benchmarks: dict[str, float] = field(default_factory=dict)
    versilia: float | None = None
    warnings: list[str] = field(default_factory=list)

    def fmt(self, value: float) -> str:
        return {'eur': lambda v: num(v) + ' €', 'eurm2': lambda v: num(v) + ' €/m²',
                'eurm2month': lambda v: num(v, 2) + ' €/m² al mese', 'percent': lambda v: pct(v, self.decimals),
                'per1000': lambda v: num(v) + ' ogni 1.000 abitanti', 'decimal': lambda v: num(v, self.decimals),
                'change': lambda v: signed(v) + '%', 'points': lambda v: num(v, 1) + ' punti',
                'per1000s': lambda v: signed(v, self.decimals) + ' ogni 1.000 abitanti', 'count': lambda v: num(v),
                'nights': lambda v: num(v, 2) + ' notti', 'per100': lambda v: num(v, 1) + ' ogni 100',
                'years': lambda v: num(v, 1) + ' anni',
                'per1000old': lambda v: num(v, 1) + ' ogni 1.000 anziani'}[self.unit](value)

    def short(self, value: float) -> str:
        return {'eurm2month': lambda v: num(v, 2) + ' €', 'per1000': lambda v: num(v), 'per1000s': lambda v: signed(v, self.decimals), 'per100': lambda v: num(v, 1),
                'years': lambda v: num(v, 1), 'per1000old': lambda v: num(v, 1),
                'eurm2': lambda v: num(v) + ' €'}.get(self.unit, self.fmt)(value)

    def rank(self, code: str) -> int:
        return next(r for c, _, r in self.ranking if c == code)


class Engine:
    def __init__(self, catalog: Path):
        self.workbench = QueryWorkbench(catalog)
        self.engine = self.workbench.engine
        self.codes = sorted(self.engine.codes)
        self.names = {t['code']: t['name'] for t in self.engine.catalog['towns']}
        self.answers = 0

    def ask(self, request: dict) -> dict:
        response = self.engine.query(request)
        if response['status'] != 'computed':
            raise ValueError(('risposta_non_calcolata', request, response.get('reasons')))
        self.answers += 1
        return response

    def measure(self, key, metric, dimension, label, unit, decimals=1, benchmarks=(), versilia=False,
                partial=False) -> Measure:
        """partial=True accetta Comuni senza dato (per esempio senza scuole di quel grado): la pagina lo dichiara."""
        selector = {'metric': metric, 'dimension': dimension, 'towns': self.codes}
        extra = {'allowPartial': True} if partial else {}
        compare = self.ask({'operation': 'compare', 'selectors': [selector], **extra})
        observations = [o for o in compare['observations'] if o['value'] is not None]
        periods = {o['period'] for o in observations}
        assert len(periods) == 1 and (partial or len(observations) == len(self.codes)), (key, periods)
        ranked = [r for r in self.ask({'operation': 'rank', 'selectors': [selector], **extra})['result']['ranking']
                  if r['value'] is not None]
        values = {o['geography']: o['value'] for o in observations}
        assert {r['geography']: r['value'] for r in ranked} == values, key
        sources = {o['source'] for o in observations}
        measure = Measure(key, metric, dimension, label, unit, decimals, periods.pop(), values,
                          [(r['geography'], r['value'], r['rank']) for r in ranked], sorted(sources)[0],
                          warnings=list(compare['warnings']))
        for scope in benchmarks:
            gap = self.ask({'operation': 'benchmark_gap', 'benchmark': scope,
                            'selectors': [dict(selector, towns=[next(iter(values))])]})
            measure.benchmarks[scope] = gap['result']['benchmarkValue']
            measure.warnings += [w for w in gap['warnings'] if w not in measure.warnings]
        if versilia:
            ratio = self.ask({'operation': 'weighted_ratio', 'selectors': [selector], **extra})
            measure.versilia = ratio['result']['value']
            measure.warnings += [w for w in ratio['warnings'] if w not in measure.warnings]
        return measure

    def change(self, key, metric, dimension, label, start, end) -> Measure:
        """Variazione percentuale per Comune fra due periodi, una richiesta A6 per Comune."""
        values, sources, warnings = {}, set(), []
        for code in self.codes:
            response = self.ask({'operation': 'relative_change', 'selectors': [
                {'metric': metric, 'dimension': dimension, 'towns': [code], 'periods': [start, end]}]})
            values[code] = response['result']['value']
            sources |= {o['source'] for o in response['observations']}
            warnings += [w for w in response['warnings'] if w not in warnings]
        ordered = sorted(values.items(), key=lambda item: -item[1])
        ranking = [(code, value, 1 + sum(v > value for v in values.values())) for code, value in ordered]
        return Measure(key, metric, dimension, label, 'change', 1, f'{start}-{end}', values, ranking,
                       sorted(sources)[0], warnings=warnings)


# ---------------------------------------------------------------------------
# Componenti di pagina.

BENCH_LABEL = {'tuscany': 'Toscana', 'italy': 'Italia', 'versilia': 'Versilia'}


def bar_chart(m: Measure, names: dict[str, str], title: str, note: str = '') -> str:
    missing = [names[c] for c in sorted(names) if c not in m.values]
    if missing:
        note = (note + ' ' if note else '') + f'Dato non disponibile per {join_names(missing)}.'
    refs = dict(m.benchmarks)
    if m.versilia is not None:
        refs = {'versilia': m.versilia, **refs}
    every = [v for _, v, _ in m.ranking] + list(refs.values())
    low, high = min(0.0, *every), max(0.0, *every)
    span = (high - low) or 1
    scale = lambda v: (v - low) / span * 100
    zero = scale(0)
    bar = lambda v: (f'class="dr-bar{" dr-bar-neg" if v < 0 else ""}" '
                     f'style="left:{min(zero, scale(v)):.2f}%;width:{abs(scale(v) - zero):.2f}%"')
    rows = ''.join(
        f'<div class="dr-row" data-town="{code}"><span class="dr-name" style="grid-row:{i}">{esc(names[code])}</span>'
        f'<span class="dr-track" style="grid-row:{i}"><span {bar(value)}></span></span>'
        f'<span class="dr-val" style="grid-row:{i}">{esc(m.short(value))}</span></div>'
        for i, (code, value, _) in enumerate(m.ranking, 1))
    lines = ''.join(f'<span class="dr-ref dr-ref-{scope}" style="left:{scale(value):.2f}%"></span>'
                    for scope, value in refs.items())
    if low < 0:
        lines += f'<span class="dr-ref dr-zero" style="left:{zero:.2f}%"></span>'
    legend = ''.join(f'<li class="dr-key dr-key-{scope}">{BENCH_LABEL[scope]} <b>{esc(m.short(value))}</b></li>'
                     for scope, value in refs.items())
    table = ''.join(f'<tr><th scope="row">{esc(names[code])}</th><td>{esc(m.fmt(value))}</td></tr>'
                    for code, value, _ in m.ranking)
    table += ''.join(f'<tr><th scope="row">{BENCH_LABEL[s]}</th><td>{esc(m.fmt(v))}</td></tr>' for s, v in refs.items())
    return f'''<figure class="dr-chart" aria-labelledby="fig-{m.key}">
<figcaption id="fig-{m.key}"><strong>{esc(title)}</strong><span>{esc(m.label)} · {esc(period_label(m.period))}</span></figcaption>
<div class="dr-bars" aria-hidden="true"><div class="dr-refs" style="grid-row:1 / span {len(m.ranking)}">{lines}</div>{rows}</div>
{f'<ul class="dr-legend" aria-hidden="true">{legend}</ul>' if legend else ''}
<div class="dr-sr"><table><caption>{esc(title)} — {esc(period_label(m.period))}</caption><tbody>{table}</tbody></table></div>
{f'<p class="dr-fig-note">{esc(note)}</p>' if note else ''}
</figure>'''


def period_label(period: str) -> str:
    match = re.fullmatch(r'(\d{4})-S([12])', period)
    if match:
        return f'{match.group(2)}° semestre {match.group(1)}'
    school = re.fullmatch(r'(\d{4})[-/](\d{2})', period)
    if school:
        return f'anno scolastico {school.group(1)}/{school.group(2)}'
    return period


def town_blocks(texts: dict[str, str]) -> str:
    return ''.join(f'<p class="dr-town-text" data-town="{code}" hidden>{text}</p>' for code, text in texts.items())


def chapter(number: int, ident: str, title: str, question: str, body: str, why: str) -> str:
    return f'''<section class="dr-chapter" id="{ident}" aria-labelledby="{ident}-title">
<p class="dr-chapter-num">{number:02d}</p>
<h2 id="{ident}-title">{esc(title)}</h2>
<p class="dr-question">{esc(question)}</p>
{body}
<aside class="dr-why"><h3>Perché conta</h3><p>{why}</p></aside>
</section>'''


# ---------------------------------------------------------------------------
# Dossier «Abitare in Versilia».

def casa(engine: Engine) -> dict:
    N = engine.names
    m = {
        'sale': engine.measure('sale', 'omiResidential', 'saleMean', 'Quotazione media di vendita, €/m²', 'eurm2', 0),
        'rent': engine.measure('rent', 'omiResidential', 'rentMean', 'Quotazione media di affitto, €/m² al mese', 'eurm2month', 2),
        'vacant': engine.measure('vacant', 'vacantHomes', 'total', 'Abitazioni non occupate da residenti, % sul totale',
                                 'percent', 1, benchmarks=('tuscany', 'italy')),
        'nonocc': engine.measure('nonocc', 'nonOccupiedHomesPer1000', 'total',
                                 'Abitazioni non occupate da residenti ogni 1.000 abitanti', 'per1000', 0,
                                 benchmarks=('tuscany', 'italy'), versilia=True),
        'single': engine.measure('single', 'singleHouseholds', 'total', 'Famiglie di una sola persona, % sulle famiglie',
                                 'percent', 1, benchmarks=('tuscany', 'italy')),
        'income': engine.measure('income', 'income', 'total', 'Reddito imponibile medio per dichiarante, euro',
                                 'eur', 0, benchmarks=('tuscany', 'italy')),
        'real': engine.measure('real', 'incomeVsInflation', 'total',
                               'Variazione del reddito medio dal 2016, al netto dell’inflazione', 'change', 1,
                               benchmarks=('tuscany', 'italy')),
        'low': engine.measure('low', 'incomeDistribution', 'macro:0', 'Dichiaranti fino a 15.000 €, % dei dichiaranti',
                              'percent', 1, versilia=True),
        'erp': engine.measure('erp', 'erpArrears', 'nativeRatio',
                              'Importi non pagati sul fatturato agli inquilini, % cumulata', 'percent', 1, versilia=True),
        'beds': engine.measure('beds', 'tourismBedsPer1000', 'total', 'Posti letto turistici ogni 1.000 abitanti',
                               'per1000', 0, benchmarks=('tuscany', 'italy'), versilia=True),
    }
    codes = engine.codes
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]

    # 01 — prezzi
    sale, rent = m['sale'], m['rent']
    median = sorted(sale.values.values())[len(codes) // 2]
    middle = [nm(c) for c, v, _ in sale.ranking if v == median]
    sale_text = (
        f'Le quotazioni dell’Osservatorio del mercato immobiliare indicano, per il {period_label(sale.period)}, '
        f'valori di vendita compresi fra <b>{sale.fmt(lo("sale")[1])}</b> a {nm(lo("sale")[0])} e '
        f'<b>{sale.fmt(hi("sale")[1])}</b> a {nm(hi("sale")[0])}. '
        f'A metà della graduatoria {"si trovano" if len(middle) > 1 else "si trova"} {join_names(middle)}, '
        f'con {sale.fmt(median)}.')
    rent_text = (
        f'Lo stesso divario si ritrova negli affitti: da <b>{rent.fmt(lo("rent")[1])}</b> a {nm(lo("rent")[0])} '
        f'a <b>{rent.fmt(hi("rent")[1])}</b> a {nm(hi("rent")[0])}.')
    example = ''.join(
        f'<tr data-town="{c}"><th scope="row">{esc(nm(c))}</th><td>{num(sale.values[c] * EXAMPLE_M2 / 1000)} mila €</td>'
        f'<td>{num(rent.values[c] * EXAMPLE_M2)} €</td></tr>' for c, _, _ in sale.ranking)
    towns_prices = {c: (
        f'<b>{esc(nm(c))}</b>: vendita {sale.fmt(sale.values[c])} ({ordinal(sale.rank(c))} su 7), affitto '
        f'{rent.fmt(rent.values[c])} ({ordinal(rent.rank(c))} su 7). Per {EXAMPLE_M2} m² le quotazioni corrispondono '
        f'a circa {num(sale.values[c] * EXAMPLE_M2 / 1000)} mila euro di valore o {num(rent.values[c] * EXAMPLE_M2)} € '
        f'di affitto al mese.') for c in codes}
    ch1 = chapter(1, 'prezzi', 'Quanto costa una casa', 'Comprare o prendere in affitto: quanto cambia da un Comune all’altro?',
        f'<p>{sale_text}</p>{bar_chart(sale, N, "Vendita: quotazione media al metro quadro")}'
        f'<p>{rent_text}</p>{bar_chart(rent, N, "Affitto: quotazione media al metro quadro, al mese")}'
        f'''<div class="dr-example"><h3>Un esempio: un appartamento di {EXAMPLE_M2} m²</h3>
<p>Moltiplicando le quotazioni per {EXAMPLE_M2} metri quadri si ottiene un ordine di grandezza, non un prezzo:
il valore reale dipende da zona, stato e caratteristiche dell’immobile.</p>
<table><thead><tr><th scope="col">Comune</th><th scope="col">Valore</th><th scope="col">Affitto al mese</th></tr></thead><tbody>{example}</tbody></table></div>'''
        + town_blocks(towns_prices),
        'Le quotazioni OMI sono il riferimento pubblico più usato per orientarsi fra prezzi e affitti. Non sono i prezzi '
        'delle compravendite né i canoni dei contratti, ma misurano tutti i Comuni con lo stesso metro: per questo aiutano '
        'a capire quanto il mercato della casa cambi a pochi chilometri di distanza, dalla costa ai paesi dell’entroterra.')

    # 02 — case non abitate da residenti
    vac, non = m['vacant'], m['nonocc']
    above = [c for c, v, _ in vac.ranking if v > vac.benchmarks['tuscany']]
    top2 = [c for c, _, _ in vac.ranking[:2]]
    extremes = {hi('sale')[0], lo('sale')[0]}
    vac_text = (
        f'Nel {vac.period} in {len(above)} Comuni su 7 la quota di abitazioni non occupate da residenti è più alta della '
        f'media toscana ({pct(vac.benchmarks["tuscany"])}). A {join_names([nm(c) for c in top2])} supera il '
        f'{num(min(vac.values[c] for c in top2) // 10 * 10)}%: più di {TENS[int(min(vac.values[c] for c in top2) // 10)]} case su dieci.'
        + (' Sono i due Comuni agli estremi opposti per quotazioni immobiliari: '
           'lo stesso dato può nascere da situazioni molto diverse.' if set(top2) == extremes else '')
        + f' Il valore più basso è a {nm(lo("vacant")[0])} ({pct(lo("vacant")[1])}).')
    non_text = (
        f'Rapportate agli abitanti, in Versilia ci sono <b>{num(non.versilia)} abitazioni non occupate da residenti ogni '
        f'1.000 abitanti</b>, contro {num(non.benchmarks["tuscany"])} in Toscana e {num(non.benchmarks["italy"])} in Italia.')
    towns_vac = {c: (
        f'<b>{esc(nm(c))}</b>: {pct(vac.values[c])} delle abitazioni non è occupata da residenti '
        f'({ordinal(vac.rank(c))} su 7; Toscana {pct(vac.benchmarks["tuscany"])}), cioè {num(non.values[c])} '
        f'abitazioni ogni 1.000 abitanti.') for c in codes}
    ch2 = chapter(2, 'case-vuote', 'Le case dove non vive nessun residente', 'Quante abitazioni non sono la casa di chi abita qui tutto l’anno?',
        f'<p>{vac_text}</p>{bar_chart(vac, N, "Abitazioni non occupate da residenti")}<p>{non_text}</p>'
        f'{bar_chart(non, N, "Abitazioni non occupate da residenti, rapportate agli abitanti")}' + town_blocks(towns_vac),
        'Una casa non occupata da residenti non è necessariamente vuota: può essere una seconda casa, un alloggio per le '
        'vacanze, un’abitazione affittata a chi non ha la residenza o una casa inutilizzata. I dati non distinguono fra '
        'questi casi. Dicono però quanta parte del patrimonio abitativo non è disponibile per chi vuole vivere qui tutto '
        'l’anno, e quanto questo pesi in Versilia rispetto al resto della regione.')

    # 03 — famiglie
    single = m['single']
    over_t = [c for c, v, _ in single.ranking if v > single.benchmarks['tuscany']]
    single_text = (
        f'Nel {single.period} le famiglie composte da una sola persona vanno {dal(pct(lo("single")[1]))} di '
        f'{nm(lo("single")[0])} <b>{al(pct(hi("single")[1]))}</b> di {nm(hi("single")[0])}. '
        f'{len(over_t)} Comuni su 7 superano la media toscana ({pct(single.benchmarks["tuscany"])}) e italiana '
        f'({pct(single.benchmarks["italy"])}).' if all(single.values[c] > single.benchmarks['italy'] for c in over_t) else
        f'Nel {single.period} le famiglie di una sola persona vanno {dal(pct(lo("single")[1]))} {al(pct(hi("single")[1]))}.')
    towns_single = {c: (f'<b>{esc(nm(c))}</b>: {pct(single.values[c])} delle famiglie è composta da una sola persona '
                        f'({ordinal(single.rank(c))} su 7; Toscana {pct(single.benchmarks["tuscany"])}).') for c in codes}
    ch3 = chapter(3, 'famiglie', 'Chi abita le case', 'Quante persone vivono da sole?',
        f'<p>{single_text}</p>{bar_chart(single, N, "Famiglie di una sola persona")}' + town_blocks(towns_single),
        'Il numero e la dimensione delle famiglie orientano il bisogno di case: più nuclei piccoli significano più '
        'abitazioni richieste a parità di abitanti, e più persone che sostengono da sole affitto, mutuo e spese. '
        'Vivere da soli non vuol dire essere soli: il dato descrive la composizione delle famiglie, non le relazioni.')

    # 04 — redditi
    inc, real, low = m['income'], m['real'], m['low']
    all_above = all(v > real.benchmarks['tuscany'] and v > real.benchmarks['italy'] for v in real.values.values())
    inc_text = (
        f'Nel {inc.period} il reddito imponibile medio dichiarato va da {inc.fmt(lo("income")[1])} a '
        f'{nm(lo("income")[0])} a <b>{inc.fmt(hi("income")[1])}</b> a {nm(hi("income")[0])}. '
        f'{len([v for v in inc.values.values() if v > inc.benchmarks["tuscany"]])} Comuni su 7 superano la media '
        f'toscana ({inc.fmt(inc.benchmarks["tuscany"])}).')
    real_text = (
        f'Tolto l’aumento dei prezzi, dal 2016 al {real.period} il reddito medio è cresciuto '
        + (f'<b>in tutti i sette Comuni più che in Toscana ({signed(real.benchmarks["tuscany"])}%) e in Italia '
           f'({signed(real.benchmarks["italy"])}%)</b>' if all_above else 'in misura diversa da Comune a Comune')
        + f': da {signed(lo("real")[1])}% a {nm(lo("real")[0])} a {signed(hi("real")[1])}% a {nm(hi("real")[0])}.')
    low_text = (
        f'Le medie però non raccontano tutto: in Versilia <b>{pct(low.versilia)} dei dichiaranti</b> denuncia meno di '
        f'15.000 euro l’anno, più di una persona su tre.')
    towns_income = {c: (
        f'<b>{esc(nm(c))}</b>: reddito medio {inc.fmt(inc.values[c])} ({ordinal(inc.rank(c))} su 7), '
        f'{signed(real.values[c])}% dal 2016 al netto dell’inflazione; {il(pct(low.values[c]))} dei dichiaranti '
        f'è sotto i 15.000 euro.') for c in codes}
    ch4 = chapter(4, 'redditi', 'Con quali redditi', 'Quanto dichiarano le famiglie che devono pagare la casa?',
        f'<p>{inc_text}</p>{bar_chart(inc, N, "Reddito imponibile medio per dichiarante")}'
        f'<p>{real_text}</p>{bar_chart(real, N, "Crescita del reddito medio dal 2016, al netto dell’inflazione")}'
        f'<p>{low_text}</p>{bar_chart(low, N, "Dichiaranti con meno di 15.000 euro")}' + town_blocks(towns_income),
        'Il costo della casa pesa in modo diverso a seconda di quanto si guadagna. I redditi dichiarati non sono il '
        'reddito disponibile delle famiglie e non comprendono tutte le entrate, ma permettono di confrontare i Comuni '
        'fra loro e con il resto del Paese. La quota di redditi bassi ricorda che dietro una media alta possono esserci '
        'molte persone con possibilità limitate.')

    # 05 — case popolari
    erp = m['erp']
    erp_text = (
        f'Per le case popolari gestite da ERP Lucca, alla fine del {erp.period} risultava non pagato '
        f'<b>{pct(erp.versilia)}</b> di quanto fatturato negli anni agli inquilini dei sette Comuni per canoni e spese. '
        f'Il valore va {dal(pct(lo("erp")[1]))} di {nm(lo("erp")[0])} {al(pct(hi("erp")[1]))} di {nm(hi("erp")[0])}.')
    towns_erp = {c: (f'<b>{esc(nm(c))}</b>: {pct(erp.values[c])} degli importi fatturati agli inquilini delle case popolari '
                     f'risulta non pagato ({ordinal(erp.rank(c))} su 7 per quota più alta).') for c in codes}
    ch5 = chapter(5, 'case-popolari', 'Le case popolari', 'Quanto pesano gli affitti non pagati nell’edilizia pubblica?',
        f'<p>{erp_text}</p>{bar_chart(erp, N, "Morosità cumulata nelle case popolari")}' + town_blocks(towns_erp),
        'La morosità è uno dei pochi segnali pubblici sulle difficoltà delle famiglie che vivono in affitto. È un dato '
        'contabile e cumulato negli anni: non dice quante famiglie sono in difficoltà né perché, e non misura la '
        'qualità della gestione. Va letto insieme agli altri capitoli, non da solo.')

    # 06 — turismo
    beds = m['beds']
    beds_text = (
        f'Nel {beds.period} la Versilia contava <b>{num(beds.versilia)} posti letto turistici ogni 1.000 abitanti</b>, '
        f'contro {num(beds.benchmarks["tuscany"])} in Toscana e {num(beds.benchmarks["italy"])} in Italia. '
        f'A {nm(hi("beds")[0])} sono {num(hi("beds")[1])}, a {nm(lo("beds")[0])} {num(lo("beds")[1])}.')
    towns_beds = {c: (f'<b>{esc(nm(c))}</b>: {num(beds.values[c])} posti letto turistici ogni 1.000 abitanti '
                      f'({ordinal(beds.rank(c))} su 7; Toscana {num(beds.benchmarks["tuscany"])}).') for c in codes}
    ch6 = chapter(6, 'turismo', 'Turismo e abitare', 'Quanto spazio occupa l’ospitalità turistica rispetto ai residenti?',
        f'<p>{beds_text}</p>{bar_chart(beds, N, "Posti letto turistici rispetto agli abitanti")}' + town_blocks(towns_beds),
        'Alberghi, campeggi, case vacanza e altre strutture ricettive convivono con le abitazioni dei residenti. '
        'Il rapporto fra posti letto e abitanti dà la misura di questa convivenza. Non comprende gli alloggi privati '
        'affittati ai turisti senza forma d’impresa, che le statistiche ufficiali non contano nello stesso modo.')

    # In sintesi
    key_points = [
        (f'{num(lo("sale")[1])}–{num(hi("sale")[1])} €/m²',
         f'Le quotazioni di vendita fra il Comune meno caro ({nm(lo("sale")[0])}) e il più caro ({nm(hi("sale")[0])}).', 'prezzi'),
        (num(non.versilia),
         f'Abitazioni non occupate da residenti ogni 1.000 abitanti. In Toscana sono {num(non.benchmarks["tuscany"])}.', 'case-vuote'),
        (f'{pct(hi("single")[1])}',
         f'Le famiglie di una persona sola a {nm(hi("single")[0])}, il valore più alto dei sette Comuni.', 'famiglie'),
        (f'{len(codes)} su {len(codes)}' if all_above else signed(hi('real')[1]) + '%',
         f'Comuni dove dal 2016, tolta l’inflazione, il reddito medio è cresciuto più che in Toscana '
         f'({signed(real.benchmarks["tuscany"])}%) e in Italia ({signed(real.benchmarks["italy"])}%).'
         if all_above else f'Crescita del reddito medio dal 2016 al netto dell’inflazione, a {nm(hi("real")[0])}.', 'redditi'),
        (pct(low.versilia), 'Dei dichiaranti in Versilia ha un reddito sotto i 15.000 euro.', 'redditi'),
        (num(beds.versilia), f'Posti letto turistici ogni 1.000 abitanti: in Toscana {num(beds.benchmarks["tuscany"])}.', 'turismo'),
    ]
    towns_summary = {}
    for c in codes:
        towns_summary[c] = (
            f'<ul class="dr-town-list">'
            f'<li><span>Vendita</span><b>{sale.fmt(sale.values[c])}</b><em>{ordinal(sale.rank(c))} su 7</em></li>'
            f'<li><span>Affitto</span><b>{rent.short(rent.values[c])}/m² al mese</b><em>{ordinal(rent.rank(c))} su 7</em></li>'
            f'<li><span>Case non occupate da residenti</span><b>{pct(vac.values[c])}</b><em>Toscana {pct(vac.benchmarks["tuscany"])}</em></li>'
            f'<li><span>Famiglie di una persona</span><b>{pct(single.values[c])}</b><em>Toscana {pct(single.benchmarks["tuscany"])}</em></li>'
            f'<li><span>Reddito medio</span><b>{inc.fmt(inc.values[c])}</b><em>Toscana {inc.fmt(inc.benchmarks["tuscany"])}</em></li>'
            f'<li><span>Case popolari, importi non pagati</span><b>{pct(erp.values[c])}</b><em>Versilia {pct(erp.versilia)}</em></li>'
            f'<li><span>Posti letto turistici ogni 1.000 abitanti</span><b>{num(beds.values[c])}</b><em>Toscana {num(beds.benchmarks["tuscany"])}</em></li>'
            f'</ul>')

    unknown = [
        'Quanto si paga davvero: le quotazioni OMI sono valori di riferimento, non i prezzi delle compravendite né i '
        'canoni dei contratti registrati.',
        'Come cambiano i prezzi nel tempo: è disponibile un solo semestre di quotazioni confrontabili.',
        'Quanto pesa l’affitto sul reddito: quotazioni e redditi misurano cose diverse e non si possono dividere fra loro '
        'senza introdurre errori.',
        'Quante case sono usate per affitti brevi: gli alloggi privati non imprenditoriali non sono contati.',
        'Quante famiglie aspettano una casa popolare: le graduatorie comunali non sono ancora fra i dati raccolti.',
    ]
    return dict(
        slug='casa', title='Abitare in Versilia', unknown_topic='sulla casa', theme='abitare',
        theme_label='Tutti i dati sull’abitare',
        method=f'Gli esempi per {EXAMPLE_M2} m² sono semplici moltiplicazioni delle quotazioni, utili come ordine di grandezza.', eyebrow='Dossier · Casa e affitti',
        lead='Quanto costano le case, quante non sono abitate da residenti, chi ci vive e con quali redditi: '
             'una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Prezzi e affitti, case non abitate da residenti, famiglie, redditi, case popolari e turismo nei sette '
                    'Comuni della Versilia, con confronti con Toscana e Italia.',
        periods=f'Quotazioni OMI del {period_label(sale.period)}, censimento {vac.period}, redditi {inc.period}, '
                f'case popolari {erp.period}, strutture turistiche {beds.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('prezzi', 'Quanto costa una casa'), ('case-vuote', 'Le case dove non vive nessun residente'),
             ('famiglie', 'Chi abita le case'), ('redditi', 'Con quali redditi'), ('case-popolari', 'Le case popolari'),
             ('turismo', 'Turismo e abitare')])


def summary_item(label: str, value: str, note: str) -> str:
    return f'<li><span>{esc(label)}</span><b>{esc(value)}</b><em>{esc(note)}</em></li>'


def count_words(n: int, total: int) -> str:
    if n == total:
        return 'tutti i sette Comuni' if total == 7 else f'tutti i {total} Comuni'
    return f'{n} Comuni su {total}' if n != 1 else f'1 Comune su {total}'


# ---------------------------------------------------------------------------
# Dossier «Lavorare in Versilia».

def lavoro(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    TI = ('tuscany', 'italy')
    m = {
        'emp': engine.measure('emp', 'employmentRate', 'total', 'Occupati fra i residenti di 25-64 anni, %',
                              'percent', 1, benchmarks=TI),
        'unemp': engine.measure('unemp', 'unemploymentRate', 'total',
                                'Disoccupati fra i residenti attivi di 25-64 anni, %', 'percent', 1, benchmarks=TI),
        'youth': engine.measure('youth', 'unemploymentRate', 'age:15-24|sex:total',
                                'Disoccupati fra i giovani attivi di 15-24 anni, %', 'percent', 1),
        'female': engine.measure('female', 'femaleEmploymentRate', 'total', 'Donne occupate fra 15 e 64 anni, %',
                                 'percent', 1, benchmarks=TI, versilia=True),
        'gap': engine.measure('gap', 'employmentGenderGap', 'total',
                              'Differenza fra occupazione maschile e femminile, punti percentuali', 'points', 1,
                              benchmarks=TI),
        'growth': engine.measure('growth', 'localEmployeesChange', 'total',
                                 'Variazione degli addetti nelle imprese del Comune', 'change', 1, benchmarks=TI),
        'size': engine.measure('size', 'employeesPerLocalUnit', 'total', 'Addetti medi per sede d’impresa',
                               'decimal', 2, benchmarks=TI, versilia=True),
        'balance': engine.measure('balance', 'commuterBalanceRate', 'total',
                                  'Lavoratori in entrata meno lavoratori in uscita, ogni 1.000 abitanti', 'per1000s', 0,
                                  versilia=True),
        'self': engine.measure('self', 'selfContainment', 'total',
                               'Pendolari residenti che lavorano nel proprio Comune, %', 'percent', 1,
                               benchmarks=TI, versilia=True),
        'wage': engine.measure('wage', 'averageGrossRemunerationPerEmployee', 'total',
                               'Retribuzione lorda media per dipendente delle imprese, euro', 'eur', 0, benchmarks=TI),
        'prod': engine.measure('prod', 'labourProductivity', 'total', 'Valore aggiunto per addetto delle imprese, euro',
                               'eur', 0, benchmarks=TI),
        'job_income': engine.measure('job_income', 'incomeSourceProfile', 'source:employment',
                                     'Reddito medio dichiarato da lavoro dipendente, euro', 'eur', 0,
                                     benchmarks=TI, versilia=True),
        'pension': engine.measure('pension', 'pensionIncomeShare', 'total',
                                  'Quota dei redditi dichiarati che viene da pensioni, %', 'percent', 1,
                                  benchmarks=TI, versilia=True),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    above = lambda k, scope: [c for c, v, _ in m[k].ranking if v > m[k].benchmarks[scope]]
    below = lambda k, scope: [c for c, v, _ in m[k].ranking if v < m[k].benchmarks[scope]]
    total = len(codes)

    # 01 — quanti lavorano
    emp, unemp = m['emp'], m['unemp']
    emp_above_t, emp_above_i = above('emp', 'tuscany'), above('emp', 'italy')
    emp_text = (
        f'Nel {emp.period}, fra i residenti di 25-64 anni, la quota di occupati va {dal(pct(lo("emp")[1]))} di '
        f'{nm(lo("emp")[0])} <b>{al(pct(hi("emp")[1]))}</b> di {nm(hi("emp")[0])}. '
        + (f'<b>Nessun Comune raggiunge la media toscana</b> ({pct(emp.benchmarks["tuscany"])}); '
           if not emp_above_t else f'{count_words(len(emp_above_t), total)} superano la media toscana '
                                    f'({pct(emp.benchmarks["tuscany"])}); ')
        + f'{count_words(len(emp_above_i), total)} superano quella italiana ({pct(emp.benchmarks["italy"])}).')
    unemp_above_t = above('unemp', 'tuscany')
    unemp_text = (
        f'Anche la disoccupazione è più alta della media toscana ({pct(unemp.benchmarks["tuscany"])}) in '
        f'{count_words(len(unemp_above_t), total)}: va {dal(pct(lo("unemp")[1]))} di '
        f'{nm(lo("unemp")[0])} <b>{al(pct(hi("unemp")[1]))}</b> di {nm(hi("unemp")[0])}.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: lavora {il(pct(emp.values[c]))} dei residenti di 25-64 anni '
                  f'({ordinal(emp.rank(c))} su 7; Toscana {pct(emp.benchmarks["tuscany"])}); la disoccupazione è '
                  f'{al(pct(unemp.values[c]))}.') for c in codes}
    ch1 = chapter(1, 'occupazione', 'Quante persone lavorano', 'Quanti residenti hanno un lavoro e quanti lo cercano?',
        f'<p>{emp_text}</p>{bar_chart(emp, N, "Tasso di occupazione, 25-64 anni")}'
        f'<p>{unemp_text}</p>{bar_chart(unemp, N, "Tasso di disoccupazione, 25-64 anni")}' + town_blocks(towns1),
        'Il tasso di occupazione è la misura più diretta di quante persone in età da lavoro hanno un impiego. '
        'Descrive i residenti, ovunque lavorino, e non i posti di lavoro presenti nel Comune. Una quota più bassa può '
        'dipendere da molti fattori, dall’età della popolazione al lavoro stagionale, che i dati annuali non '
        'distinguono.')

    # 02 — giovani e donne
    youth, female, gap = m['youth'], m['female'], m['gap']
    gap_all_above = all(v > gap.benchmarks['tuscany'] for v in gap.values.values())
    youth_text = (
        f'Fra i giovani di 15-24 anni che lavorano o cercano lavoro, la disoccupazione va {dal(pct(lo("youth")[1]))} di '
        f'{nm(lo("youth")[0])} <b>{al(pct(hi("youth")[1]))}</b> di {nm(hi("youth")[0])}.')
    female_text = (
        f'In Versilia lavora <b>{il(pct(female.versilia))} delle donne fra 15 e 64 anni</b>, contro '
        f'{il(pct(female.benchmarks["tuscany"]))} in Toscana e {il(pct(female.benchmarks["italy"]))} in Italia '
        f'(dati {female.period}). ')
    gap_text = (
        (f'In tutti i sette Comuni la distanza fra uomini e donne è più ampia che in Toscana '
         f'({num(gap.benchmarks["tuscany"], 1)} punti): ' if gap_all_above else
         f'La distanza fra uomini e donne è di {num(gap.benchmarks["tuscany"], 1)} punti in Toscana; ')
        + f'va da {num(lo("gap")[1], 1)} punti a {nm(lo("gap")[0])} a <b>{num(hi("gap")[1], 1)} punti</b> a '
          f'{nm(hi("gap")[0])}.')
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: disoccupazione giovanile {al(pct(youth.values[c]))}; lavora '
                  f'{il(pct(female.values[c]))} delle donne, {num(gap.values[c], 1)} punti in meno degli uomini.')
              for c in codes}
    ch2 = chapter(2, 'giovani-donne', 'Giovani e donne', 'Chi fa più fatica a trovare lavoro?',
        f'<p>{youth_text}</p>{bar_chart(youth, N, "Disoccupazione giovanile, 15-24 anni", "Fra i giovani molti studiano: il tasso si calcola solo su chi lavora o cerca lavoro.")}'
        f'<p>{female_text}{gap_text}</p>{bar_chart(female, N, "Donne occupate, 15-64 anni")}'
        f'{bar_chart(gap, N, "Distanza fra occupazione maschile e femminile")}' + town_blocks(towns2),
        'Giovani e donne sono i gruppi in cui si vedono prima le difficoltà del mercato del lavoro locale. Una '
        'distanza ampia fra uomini e donne può riflettere carichi di cura, servizi per l’infanzia, orari e '
        'stagionalità dei settori: i dati ne misurano l’ampiezza, non le cause.')

    # 03 — dove si lavora
    growth, size = m['growth'], m['size']
    grew = [c for c, v, _ in growth.ranking if v > 0]
    fell = [c for c, v, _ in growth.ranking if v < 0]
    growth_text = (
        f'Fra il 2018 e il 2023 gli addetti delle imprese con sede nel territorio sono aumentati in '
        f'{count_words(len(grew), total)}, e in {len(above("growth", "tuscany"))} più della media '
        f'toscana ({signed(growth.benchmarks["tuscany"])}%). La crescita più forte è a {nm(hi("growth")[0])} '
        f'(<b>{signed(hi("growth")[1])}%</b>)'
        + (f', mentre a {join_names([nm(c) for c in fell])} gli addetti sono diminuiti '
           f'({"; ".join(signed(growth.values[c]) + "%" for c in fell)}).' if fell else '.'))
    size_text = (
        f'Le imprese sono piccole: in media <b>{num(size.versilia, 2)} addetti per sede</b> in Versilia, contro '
        f'{num(size.benchmarks["tuscany"], 2)} in Toscana e {num(size.benchmarks["italy"], 2)} in Italia.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: addetti delle imprese {signed(growth.values[c])}% dal 2018 al 2023 '
                  f'(Toscana {signed(growth.benchmarks["tuscany"])}%), in media {num(size.values[c], 2)} per sede.')
              for c in codes}
    ch3 = chapter(3, 'imprese', 'Dove si lavora', 'Le imprese del territorio stanno creando lavoro?',
        f'<p>{growth_text}</p>{bar_chart(growth, N, "Addetti delle imprese, variazione 2018-2023")}'
        f'<p>{size_text}</p>{bar_chart(size, N, "Addetti medi per sede d’impresa")}' + town_blocks(towns3),
        'Gli addetti delle imprese misurano il lavoro che si svolge nel Comune, chiunque lo faccia: residenti o '
        'pendolari. Imprese piccole sono una caratteristica del tessuto economico locale; il dato non dice nulla '
        'sulla loro solidità o sulla qualità del lavoro offerto.')

    # 04 — pendolari
    bal, slf = m['balance'], m['self']
    pos = [c for c, v, _ in bal.ranking if v > 0]
    neg = [c for c, v, _ in bal.ranking if v < 0]
    bal_text = (
        f'Al censimento del {bal.period} {join_names([nm(c) for c in pos])} '
        f'{"attiravano" if len(pos) > 1 else "attirava"} più lavoratori di quanti ne uscissero: '
        f'{nm(hi("balance")[0])} su tutti, con un saldo di <b>{signed(hi("balance")[1], 0)} ogni 1.000 abitanti</b>. '
        f'Da {join_names([nm(c) for c in neg])} invece si usciva per lavorare più di quanto si entrasse: a '
        f'{nm(lo("balance")[0])} il saldo era {signed(lo("balance")[1], 0)}.')
    slf_text = (
        f'Fra i residenti che si spostano ogni giorno per lavoro, quelli che restano nel proprio Comune vanno '
        f'{dal(pct(lo("self")[1]))} di {nm(lo("self")[0])} <b>{al(pct(hi("self")[1]))}</b> di {nm(hi("self")[0])} '
        f'(Versilia {pct(slf.versilia)}, Toscana {pct(slf.benchmarks["tuscany"])}).')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: saldo fra lavoratori in entrata e in uscita {signed(bal.values[c], 0)} ogni '
                  f'1.000 abitanti; {il(pct(slf.values[c]))} dei pendolari residenti lavora nel Comune.') for c in codes}
    ch4 = chapter(4, 'pendolari', 'Chi arriva e chi parte', 'Dove si lavora rispetto a dove si vive?',
        f'<p>{bal_text}</p>{bar_chart(bal, N, "Saldo fra lavoratori in entrata e in uscita", "Barre verso destra: entrano più lavoratori di quanti escano. Verso sinistra: ne escono di più.")}'
        f'<p>{slf_text}</p>{bar_chart(slf, N, "Pendolari che lavorano nel proprio Comune")}' + town_blocks(towns4),
        'Il saldo pendolare distingue i Comuni che offrono lavoro a chi vive altrove da quelli in cui si vive ma si '
        'lavora fuori. Conta per i trasporti, per i servizi e per il bilancio dei Comuni. È però una fotografia del '
        '2021: non dice come si spostano le persone oggi, né con quali mezzi.')

    # 05 — salari e produttività
    wage, prod = m['wage'], m['prod']
    wage_below = below('wage', 'tuscany')
    prod_all_below = not above('prod', 'tuscany') and not above('prod', 'italy')
    wage_text = (
        f'Nel {wage.period} la retribuzione lorda media per dipendente delle imprese locali andava da '
        f'{wage.fmt(lo("wage")[1])} a {nm(lo("wage")[0])} a <b>{wage.fmt(hi("wage")[1])}</b> a {nm(hi("wage")[0])}. '
        f'{count_words(len(wage_below), total)[:1].upper()}{count_words(len(wage_below), total)[1:]} restano sotto la media toscana ({wage.fmt(wage.benchmarks["tuscany"])}).')
    prod_text = (
        (f'Il valore aggiunto per addetto è <b>sotto la media toscana ({prod.fmt(prod.benchmarks["tuscany"])}) e '
         f'italiana ({prod.fmt(prod.benchmarks["italy"])}) in tutti i sette Comuni</b>' if prod_all_below else
         f'Il valore aggiunto per addetto va confrontato con la media toscana ({prod.fmt(prod.benchmarks["tuscany"])})')
        + f': da {prod.fmt(lo("prod")[1])} a {nm(lo("prod")[0])} a {prod.fmt(hi("prod")[1])} a {nm(hi("prod")[0])}.')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: retribuzione lorda media {wage.fmt(wage.values[c])} per dipendente '
                  f'({ordinal(wage.rank(c))} su 7); valore aggiunto {prod.fmt(prod.values[c])} per addetto.')
              for c in codes}
    ch5 = chapter(5, 'salari', 'Quanto rende il lavoro', 'Quanto pagano e quanto producono le imprese locali?',
        f'<p>{wage_text}</p>{bar_chart(wage, N, "Retribuzione lorda media per dipendente")}'
        f'<p>{prod_text}</p>{bar_chart(prod, N, "Valore aggiunto per addetto")}' + town_blocks(towns5),
        'Retribuzioni e valore aggiunto per addetto descrivono la struttura delle imprese: settori, dimensioni, '
        'stagionalità. Sono valori lordi e nominali, calcolati sulle imprese dell’industria e dei servizi, senza '
        'agricoltura e pubblica amministrazione. Non sono lo stipendio di una persona tipo, ma permettono di '
        'confrontare il territorio con la regione e con il Paese.')

    # 06 — redditi
    job, pen = m['job_income'], m['pension']
    job_text = (
        f'Chi dichiara redditi da lavoro dipendente riceve in media <b>{job.fmt(job.versilia)}</b> in Versilia, '
        f'contro {job.fmt(job.benchmarks["tuscany"])} in Toscana e {job.fmt(job.benchmarks["italy"])} in Italia '
        f'(redditi {job.period}). Si va da {job.fmt(lo("job_income")[1])} a {nm(lo("job_income")[0])} a '
        f'{job.fmt(hi("job_income")[1])} a {nm(hi("job_income")[0])}.')
    pen_text = (
        f'Le pensioni valgono <b>{il(pct(pen.versilia))}</b> dei redditi dichiarati in Versilia '
        f'({pct(pen.benchmarks["tuscany"])} in Toscana): {dal(pct(lo("pension")[1]))} di {nm(lo("pension")[0])} '
        f'al {pct(hi("pension")[1])} di {nm(hi("pension")[0])}.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: reddito medio da lavoro dipendente {job.fmt(job.values[c])}; le pensioni '
                  f'sono {il(pct(pen.values[c]))} dei redditi dichiarati.') for c in codes}
    ch6 = chapter(6, 'redditi', 'Redditi da lavoro e pensioni', 'Da dove vengono i redditi delle famiglie?',
        f'<p>{job_text}</p>{bar_chart(job, N, "Reddito medio da lavoro dipendente")}'
        f'<p>{pen_text}</p>{bar_chart(pen, N, "Peso delle pensioni sui redditi dichiarati")}' + town_blocks(towns6),
        'I redditi dichiarati mostrano quanto conta il lavoro rispetto alle pensioni nell’economia delle famiglie. '
        'Una persona può avere più redditi, e i valori sono quelli dichiarati al fisco in termini nominali: non '
        'misurano il reddito disponibile né il lavoro non dichiarato.')

    key_points = [
        ((f'{len(below("emp", "tuscany"))} su {total}'),
         f'Comuni con un tasso di occupazione (25-64 anni) sotto la media toscana del {pct(emp.benchmarks["tuscany"])}.',
         'occupazione'),
        (pct(hi('youth')[1]), f'I giovani di 15-24 anni attivi senza lavoro a {nm(hi("youth")[0])}, il valore più alto.',
         'giovani-donne'),
        (pct(female.versilia), f'Le donne occupate in Versilia fra 15 e 64 anni. In Toscana sono '
                               f'{il(pct(female.benchmarks["tuscany"]))}.', 'giovani-donne'),
        (f'{len(grew)} su {total}', 'Comuni dove gli addetti delle imprese sono cresciuti fra il 2018 e il 2023.', 'imprese'),
        (signed(hi('balance')[1], 0), f'Il saldo dei lavoratori in entrata a {nm(hi("balance")[0])}, ogni 1.000 '
                                      f'abitanti: il Comune che attira più lavoro.', 'pendolari'),
        (f'{len(wage_below)} su {total}', f'Comuni con una retribuzione media sotto la media toscana '
                                          f'({wage.fmt(wage.benchmarks["tuscany"])}).', 'salari'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Occupati 25-64 anni', pct(emp.values[c]), f'Toscana {pct(emp.benchmarks["tuscany"])}'),
        summary_item('Disoccupati 25-64 anni', pct(unemp.values[c]), f'Toscana {pct(unemp.benchmarks["tuscany"])}'),
        summary_item('Donne occupate', pct(female.values[c]), f'Toscana {pct(female.benchmarks["tuscany"])}'),
        summary_item('Addetti delle imprese 2018-2023', signed(growth.values[c]) + '%',
                     f'Toscana {signed(growth.benchmarks["tuscany"])}%'),
        summary_item('Saldo pendolare ogni 1.000 abitanti', signed(bal.values[c], 0), f'Versilia {signed(bal.versilia, 0)}'),
        summary_item('Retribuzione media per dipendente', wage.fmt(wage.values[c]),
                     f'Toscana {wage.fmt(wage.benchmarks["tuscany"])}'),
        summary_item('Reddito medio da lavoro dipendente', job.fmt(job.values[c]),
                     f'Toscana {job.fmt(job.benchmarks["tuscany"])}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanto pesa il lavoro stagionale: i dati sono annuali e non mostrano come cambia l’occupazione fra estate e '
        'inverno.',
        'Che tipo di contratti ci sono: tempo determinato, part-time e lavoro autonomo non sono distinti a livello '
        'comunale.',
        'Quanto lavoro non è dichiarato: per definizione non compare nelle fonti ufficiali.',
        'Dove vanno e da dove vengono i pendolari: i totali comunali non indicano i Comuni di origine e destinazione, '
        'e la fotografia è del 2021.',
        'Quanto guadagnano i lavoratori di un settore preciso, come il turismo: le retribuzioni sono medie di tutte '
        'le imprese.',
    ]
    return dict(
        slug='lavoro', title='Lavorare in Versilia', eyebrow='Dossier · Lavoro e redditi',
        unknown_topic='sul lavoro', theme='lavoro', theme_label='Tutti i dati sul lavoro',
        lead='Quante persone lavorano, chi fa più fatica, dove si crea lavoro, quanto rende e da dove vengono i redditi: '
             'una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Occupazione e disoccupazione, giovani e donne, imprese, pendolari, retribuzioni e redditi nei sette '
                    'Comuni della Versilia, con confronti con Toscana e Italia.',
        periods=f'Occupazione {emp.period}, donne occupate {female.period}, imprese {period_label(growth.period)}, '
                f'pendolari {bal.period}, retribuzioni {wage.period}, redditi {job.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('occupazione', 'Quante persone lavorano'), ('giovani-donne', 'Giovani e donne'),
             ('imprese', 'Dove si lavora'), ('pendolari', 'Chi arriva e chi parte'), ('salari', 'Quanto rende il lavoro'),
             ('redditi', 'Redditi da lavoro e pensioni')])


# ---------------------------------------------------------------------------
# Dossier «La Versilia dei turisti».

def turismo(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    m = {
        'presences': engine.measure('presences', 'tourismPresences', 'total', 'Presenze turistiche (notti trascorse)',
                                    'count', 0),
        'arrivals': engine.measure('arrivals', 'tourismArrivals', 'total', 'Arrivi turistici', 'count', 0),
        'intensity': engine.measure('intensity', 'tourismIntensity', 'total', 'Presenze turistiche per abitante',
                                    'decimal', 1, benchmarks=('tuscany',), versilia=True),
    }
    pres = m['presences']
    series_years = [o['period'] for o in engine.ask({'operation': 'series', 'selectors': [
        {'metric': 'tourismPresences', 'dimension': 'total', 'towns': [codes[0]]}]})['observations']]
    first, last = series_years[0], series_years[-1]
    m['change'] = engine.change('change', 'tourismPresences', 'total', 'Variazione percentuale delle presenze',
                                first, last)
    m.update({
        'stay': engine.measure('stay', 'tourismAverageStay', 'total', 'Permanenza media, notti per arrivo', 'nights', 2,
                               benchmarks=('tuscany',), versilia=True),
        'foreign': engine.measure('foreign', 'foreignTourismShare', 'total',
                                  'Presenze di turisti residenti all’estero, %', 'percent', 1, benchmarks=('tuscany',)),
        'season': engine.measure('season', 'tourismSeasonality', 'total',
                                 'Presenze concentrate nei tre mesi di punta, %', 'percent', 1, benchmarks=('tuscany',)),
        'beds': engine.measure('beds', 'tourismBedsPer1000', 'total', 'Posti letto turistici ogni 1.000 abitanti',
                               'per1000', 0, benchmarks=('tuscany', 'italy'), versilia=True),
        'structures': engine.measure('structures', 'tourismStructuresPer1000', 'total',
                                     'Strutture ricettive ogni 1.000 abitanti', 'decimal', 1,
                                     benchmarks=('tuscany', 'italy'), versilia=True),
        'spend': engine.measure('spend', 'tourismDevelopmentMissionExpenditurePerResident', 'total',
                                'Spesa comunale per sviluppo e valorizzazione del turismo, euro per abitante', 'eur', 0,
                                versilia=True),
    })
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    arr, inten, chg = m['arrivals'], m['intensity'], m['change']

    # 01 — quanti turisti
    top = pres.ranking[0]
    pres_text = (
        f'Nel {pres.period} le presenze più alte nelle strutture ricettive sono a {nm(top[0])} '
        f'(<b>{num(top[1])} notti</b>), poi a {nm(pres.ranking[1][0])} ({num(pres.ranking[1][1])}) e a '
        f'{nm(pres.ranking[2][0])} ({num(pres.ranking[2][1])}). Negli altri Comuni il turismo nelle strutture è molto '
        f'più contenuto: a {nm(lo("presences")[0])} le notti sono state {num(lo("presences")[1])}.')
    inten_text = (
        f'Rapportate agli abitanti, in Versilia le presenze sono <b>{num(inten.versilia, 1)} per residente</b>, contro '
        f'{num(inten.benchmarks["tuscany"], 1)} in Toscana. A {nm(hi("intensity")[0])} sono {num(hi("intensity")[1], 1)}: '
        f'il Comune dove il turismo pesa di più rispetto alla popolazione.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {num(pres.values[c])} presenze e {num(arr.values[c])} arrivi nel {pres.period}, '
                  f'{num(inten.values[c], 1)} presenze per abitante (Toscana {num(inten.benchmarks["tuscany"], 1)}).')
              for c in codes}
    ch1 = chapter(1, 'quanti', 'Quanti turisti', 'Quanto turismo passa dalle strutture ricettive di ogni Comune?',
        f'<p>{pres_text}</p>{bar_chart(pres, N, "Presenze turistiche nelle strutture ricettive")}'
        f'<p>{inten_text}</p>{bar_chart(inten, N, "Presenze turistiche per abitante")}' + town_blocks(towns1),
        'Le presenze contano le notti trascorse nelle strutture ricettive registrate: alberghi, campeggi, case vacanza '
        'gestite come impresa. Rapportarle agli abitanti dice quanto il turismo pesa sulla vita di un Comune. Non '
        'comprendono gli affitti brevi fra privati né chi visita la Versilia in giornata.')

    # 02 — come cambia
    up = [c for c, v, _ in chg.ranking if round(v, 1) > 0]
    down = [c for c, v, _ in chg.ranking if round(v, 1) < 0]
    flat = [c for c in codes if c not in up and c not in down]
    chg_text = (
        f'Fra il {first} e il {last} le presenze sono aumentate in {count_words(len(up), total)} e diminuite in '
        f'{count_words(len(down), total)}'
        + (f'; a {join_names([nm(c) for c in flat])} sono rimaste invariate. ' if flat else '. ')
        + (f'Il calo più forte è a {nm(lo("change")[0])} (<b>{signed(lo("change")[1])}%</b>)' if down else '')
        + (f'{"; la" if down else "La"} crescita più forte a {nm(hi("change")[0])} ({signed(hi("change")[1])}%).'
           if up else '.'))
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: presenze {signed(chg.values[c])}% fra il {first} e il {last}.') for c in codes}
    ch2 = chapter(2, 'andamento', 'Come cambiano le presenze', f'Il turismo nelle strutture cresce o cala dal {first}?',
        f'<p>{chg_text}</p>{bar_chart(chg, N, f"Variazione delle presenze, {first}-{last}", f"I dati {last} sono provvisori.")}'
        + town_blocks(towns2),
        'Un calo delle presenze nelle strutture registrate non significa per forza meno turisti: una parte '
        'dell’ospitalità può spostarsi verso forme che queste statistiche non contano, come gli affitti brevi. Due o '
        'tre anni sono un periodo breve: il dato va seguito nel tempo prima di trarne conclusioni.')

    # 03 — chi arriva e quanto resta
    stay, foreign = m['stay'], m['foreign']
    stay_text = (
        f'Chi arriva in Versilia resta in media <b>{num(stay.versilia, 1)} notti</b>, contro {num(stay.benchmarks["tuscany"], 1)} '
        f'in Toscana: da {num(lo("stay")[1], 1)} a {nm(lo("stay")[0])} a {num(hi("stay")[1], 1)} a {nm(hi("stay")[0])}.')
    foreign_text = (
        f'I turisti residenti all’estero valgono {dal(pct(lo("foreign")[1]))} delle presenze a {nm(lo("foreign")[0])} '
        f'{al(pct(hi("foreign")[1]))} a {nm(hi("foreign")[0])}; in Toscana sono {il(pct(foreign.benchmarks["tuscany"]))}.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: permanenza media {num(stay.values[c], 1)} notti; {il(pct(foreign.values[c]))} '
                  f'delle presenze è di turisti residenti all’estero.') for c in codes}
    ch3 = chapter(3, 'chi-arriva', 'Chi arriva e quanto resta', 'Soggiorni lunghi o brevi, turisti italiani o stranieri?',
        f'<p>{stay_text}</p>{bar_chart(stay, N, "Permanenza media")}'
        f'<p>{foreign_text}</p>{bar_chart(foreign, N, "Presenze di turisti residenti all’estero")}' + town_blocks(towns3),
        'La durata del soggiorno e la provenienza descrivono il tipo di turismo: vacanze lunghe o fine settimana, '
        'mercato italiano o internazionale. «Straniero» qui vuol dire residente all’estero, non cittadinanza.')

    # 04 — stagionalità
    season = m['season']
    season_above = [c for c, v, _ in season.ranking if v > season.benchmarks['tuscany']]
    season_text = (
        f'Nei tre mesi di punta si concentra {dal(pct(lo("season")[1]))} delle presenze annue a {nm(lo("season")[0])} '
        f'{al(pct(hi("season")[1]))} a <b>{nm(hi("season")[0])}</b>. In {count_words(len(season_above), total)} la '
        f'concentrazione è più alta della media toscana ({pct(season.benchmarks["tuscany"])}).')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(season.values[c]))} delle presenze cade nei tre mesi di punta '
                  f'(Toscana {pct(season.benchmarks["tuscany"])}).') for c in codes}
    ch4 = chapter(4, 'stagioni', 'Una stagione sola?', 'Quanto il turismo si concentra in pochi mesi?',
        f'<p>{season_text}</p>{bar_chart(season, N, "Presenze nei tre mesi di punta")}' + town_blocks(towns4),
        'Più il turismo è concentrato, più il territorio vive due vite diverse: servizi, lavoro, traffico e rifiuti '
        'cambiano molto fra estate e inverno. La misura considera i tre mesi con più presenze in ciascun Comune, che '
        'non sono necessariamente giugno, luglio e agosto.')

    # 05 — dove si dorme
    beds, struct = m['beds'], m['structures']
    beds_text = (
        f'Nel {beds.period} la Versilia contava <b>{num(beds.versilia)} posti letto ogni 1.000 abitanti</b>, contro '
        f'{num(beds.benchmarks["tuscany"])} in Toscana e {num(beds.benchmarks["italy"])} in Italia: da '
        f'{num(lo("beds")[1])} a {nm(lo("beds")[0])} a {num(hi("beds")[1])} a {nm(hi("beds")[0])}.')
    struct_text = (
        f'Le strutture ricettive sono {num(struct.versilia, 1)} ogni 1.000 abitanti ({num(struct.benchmarks["tuscany"], 1)} '
        f'in Toscana); a {nm(hi("structures")[0])} {num(hi("structures")[1], 1)}.')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: {num(beds.values[c])} posti letto e {num(struct.values[c], 1)} strutture ricettive '
                  f'ogni 1.000 abitanti.') for c in codes}
    ch5 = chapter(5, 'ospitalita', 'Dove si dorme', 'Quanta ospitalità c’è rispetto ai residenti?',
        f'<p>{beds_text}</p>{bar_chart(beds, N, "Posti letto turistici ogni 1.000 abitanti")}'
        f'<p>{struct_text}</p>{bar_chart(struct, N, "Strutture ricettive ogni 1.000 abitanti")}' + town_blocks(towns5),
        'Posti letto e strutture misurano la capacità di accoglienza: quanto il territorio è attrezzato per ospitare. '
        'Molte strutture piccole e pochi posti letto indicano un’ospitalità diffusa, fatta di case vacanza e '
        'affittacamere; pochi grandi alberghi danno il risultato opposto.')

    # 06 — spesa dei Comuni
    spend = m['spend']
    spend_text = (
        f'Nel {spend.period} i sette Comuni hanno impegnato per sviluppo e valorizzazione del turismo nel complesso '
        f'<b>{num(spend.versilia)} € per abitante</b>: da {num(lo("spend")[1])} € a {nm(lo("spend")[0])} a '
        f'{num(hi("spend")[1])} € a {nm(hi("spend")[0])}.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: {num(spend.values[c])} € per abitante impegnati per il turismo nel '
                  f'{spend.period} (Versilia {num(spend.versilia)} €).') for c in codes}
    ch6 = chapter(6, 'spesa', 'Quanto spendono i Comuni', 'Quanto investono le amministrazioni nel turismo?',
        f'<p>{spend_text}</p>{bar_chart(spend, N, "Spesa comunale per il turismo per abitante")}' + town_blocks(towns6),
        'È la spesa che ogni Comune classifica nel proprio bilancio alla voce dedicata al turismo: eventi, promozione, '
        'uffici informazioni, a volte opere. I Comuni non classificano tutti allo stesso modo, e una spesa più alta non '
        'dice nulla sui risultati ottenuti.')

    key_points = [
        (num(top[1]), f'Le presenze turistiche registrate a {nm(top[0])} nel {pres.period}, il valore più alto.', 'quanti'),
        (num(inten.versilia, 1), f'Presenze per abitante in Versilia. In Toscana sono {num(inten.benchmarks["tuscany"], 1)}.',
         'quanti'),
        (signed(lo('change')[1]) + '%', f'La variazione delle presenze a {nm(lo("change")[0])} fra il {first} e il {last}.',
         'andamento'),
        (num(stay.versilia, 1), f'Notti di permanenza media in Versilia, contro {num(stay.benchmarks["tuscany"], 1)} in Toscana.',
         'chi-arriva'),
        (pct(hi('season')[1]), f'Le presenze di {nm(hi("season")[0])} concentrate in soli tre mesi.', 'stagioni'),
        (num(beds.versilia), f'Posti letto turistici ogni 1.000 abitanti: in Toscana {num(beds.benchmarks["tuscany"])}.',
         'ospitalita'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Presenze turistiche', num(pres.values[c]), f'{ordinal(pres.rank(c))} su 7'),
        summary_item('Presenze per abitante', num(inten.values[c], 1), f'Toscana {num(inten.benchmarks["tuscany"], 1)}'),
        summary_item(f'Variazione {first}-{last}', signed(chg.values[c]) + '%', f'{ordinal(chg.rank(c))} su 7'),
        summary_item('Permanenza media', num(stay.values[c], 1) + ' notti', f'Toscana {num(stay.benchmarks["tuscany"], 1)}'),
        summary_item('Turisti dall’estero', pct(foreign.values[c]), f'Toscana {pct(foreign.benchmarks["tuscany"])}'),
        summary_item('Presenze nei tre mesi di punta', pct(season.values[c]), f'Toscana {pct(season.benchmarks["tuscany"])}'),
        summary_item('Posti letto ogni 1.000 abitanti', num(beds.values[c]), f'Toscana {num(beds.benchmarks["tuscany"])}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanti turisti dormono negli affitti brevi fra privati: non sono contati nelle presenze ufficiali.',
        'Quante persone visitano la Versilia in giornata, senza pernottare.',
        'Quanto spendono i turisti e quanto resta all’economia locale.',
        'Quanti visitatori ci sono nei giorni di punta: le presenze sono totali annui, non affollamento giornaliero.',
        'Gli effetti del turismo su prezzi delle case, traffico e servizi: i dati mostrano coincidenze, non cause.',
    ]
    return dict(
        slug='turismo', title='La Versilia dei turisti', eyebrow='Dossier · Turismo',
        unknown_topic='sul turismo', theme='economia', theme_label='Tutti i dati sull’economia',
        lead='Quanti turisti arrivano, come cambiano le presenze, quanto restano, quanto il turismo si concentra '
             'd’estate e quanta ospitalità c’è: una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Presenze e arrivi, andamento, permanenza, turisti stranieri, stagionalità, posti letto e spesa dei '
                    'Comuni per il turismo nei sette Comuni della Versilia.',
        periods=f'Movimento turistico {pres.period} (provvisorio), confronto {first}-{last}, posti letto {beds.period}, '
                f'bilanci comunali {spend.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('quanti', 'Quanti turisti'), ('andamento', 'Come cambiano le presenze'), ('chi-arriva', 'Chi arriva e quanto resta'),
             ('stagioni', 'Una stagione sola?'), ('ospitalita', 'Dove si dorme'), ('spesa', 'Quanto spendono i Comuni')])


# ---------------------------------------------------------------------------
# Dossier «Invecchiare in Versilia».

def anziani(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    TI = ('tuscany', 'italy')
    old_years = [o['period'] for o in engine.ask({'operation': 'series', 'selectors': [
        {'metric': 'oldAgeIndex', 'dimension': 'total', 'towns': [codes[0]]}]})['observations']]
    first, last = old_years[0], old_years[-1]
    m = {
        'old': engine.measure('old', 'oldAgeIndex', 'total', 'Indice di vecchiaia: residenti di 65 anni e più ogni 100 '
                              'sotto i 15 anni', 'decimal', 0),
        'old_change': engine.change('old_change', 'oldAgeIndex', 'total', 'Variazione percentuale dell’indice di vecchiaia',
                                    first, last),
        'dependency': engine.measure('dependency', 'dependencyIndices', 'part:elderly',
                                     'Residenti di 65 anni e più ogni 100 persone di 15-64 anni', 'per100', 1,
                                     benchmarks=TI, versilia=True),
        'very_old': engine.measure('very_old', 'ageDistribution', 'age:85+', 'Residenti di 85 anni e più, % della popolazione',
                                   'percent', 1, benchmarks=TI, versilia=True),
        'natural': engine.measure('natural', 'naturalDemographicDynamics', 'part:balance',
                                  'Nati meno morti, ogni 1.000 abitanti', 'per1000s', 1, benchmarks=TI, versilia=True),
        'pop_change': engine.measure('pop_change', 'populationChange', 'total', 'Variazione della popolazione residente',
                                     'change', 1, benchmarks=TI, versilia=True),
        'life': engine.measure('life', 'lifeExpectancy', 'total', 'Speranza di vita alla nascita, anni', 'years', 1,
                               benchmarks=('tuscany', 'versilia')),
        'home_care': engine.measure('home_care', 'elderlyHomeCare', 'sex:total',
                                    'Anziani assistiti a domicilio, tasso standardizzato ogni 1.000', 'per1000old', 1,
                                    benchmarks=('tuscany', 'versilia')),
        'pharmacies': engine.measure('pharmacies', 'pharmaciesPer1000', 'total', 'Farmacie ogni 1.000 abitanti',
                                     'decimal', 2, benchmarks=TI),
        'social': engine.measure('social', 'socialSpendingPerResident', 'total',
                                 'Spesa dei Comuni per i servizi sociali, euro per abitante', 'eur', 0, benchmarks=TI),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    old, chg, dep, very = m['old'], m['old_change'], m['dependency'], m['very_old']

    # 01 — quanti anziani
    all_up = all(v > 0 for v in chg.values.values())
    old_text = (
        f'All’inizio del {old.period} in ogni Comune della Versilia ci sono molti più anziani che bambini: l’indice di '
        f'vecchiaia va da {num(lo("old")[1])} a {nm(lo("old")[0])} a <b>{num(hi("old")[1])}</b> a {nm(hi("old")[0])}: '
        f'qui ci sono {num(hi("old")[1] / 100, 1)} residenti di 65 anni e più per ogni ragazzo sotto i 15 anni.'
        if all(v > 100 for v in old.values.values()) else
        f'L’indice di vecchiaia va da {num(lo("old")[1])} a {nm(lo("old")[0])} a {num(hi("old")[1])} a {nm(hi("old")[0])}.')
    chg_text = (
        (f'Dal {first} l’indice è cresciuto <b>in tutti i sette Comuni</b>: ' if all_up else f'Dal {first} l’indice è cambiato: ')
        + f'da {signed(lo("old_change")[1])}% a {nm(lo("old_change")[0])} a {signed(hi("old_change")[1])}% a '
          f'{nm(hi("old_change")[0])}.')
    dep_text = (
        f'In Versilia ci sono <b>{num(dep.versilia, 1)} residenti di 65 anni e più ogni 100 persone in età da lavoro</b>, '
        f'contro {num(dep.benchmarks["tuscany"], 1)} in Toscana e {num(dep.benchmarks["italy"], 1)} in Italia.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: indice di vecchiaia {num(old.values[c])} ({signed(chg.values[c])}% dal {first}); '
                  f'{num(dep.values[c], 1)} anziani ogni 100 persone di 15-64 anni.') for c in codes}
    ch1 = chapter(1, 'quanti', 'Quanti anziani', 'Quanto è anziana la popolazione e quanto in fretta invecchia?',
        f'<p>{old_text} {chg_text}</p>{bar_chart(old, N, "Indice di vecchiaia")}'
        f'{bar_chart(chg, N, f"Variazione dell’indice di vecchiaia, {first}-{last}")}'
        f'<p>{dep_text}</p>{bar_chart(dep, N, "Anziani ogni 100 persone in età da lavoro")}' + town_blocks(towns1),
        'L’indice di vecchiaia mette a confronto chi ha più di 65 anni con chi ne ha meno di 15: dice quanto pesa '
        'ogni generazione. Il rapporto con le persone in età da lavoro dà un’idea di quante persone attive ci sono per '
        'ogni anziano, anche se non tutte lavorano davvero.')

    # 02 — i grandi anziani
    very_text = (
        f'Le persone di 85 anni e più sono {il(pct(very.versilia))} dei residenti in Versilia, contro '
        f'{il(pct(very.benchmarks["tuscany"]))} in Toscana e {il(pct(very.benchmarks["italy"]))} in Italia. '
        f'La quota più alta è a {nm(hi("very_old")[0])}: <b>{pct(hi("very_old")[1])}</b>.')
    towns2 = {c: f'<b>{esc(nm(c))}</b>: {il(pct(very.values[c]))} dei residenti ha 85 anni o più.' for c in codes}
    ch2 = chapter(2, 'grandi-anziani', 'I grandi anziani', 'Quante persone hanno più di 85 anni?',
        f'<p>{very_text}</p>{bar_chart(very, N, "Residenti di 85 anni e più")}' + town_blocks(towns2),
        'Dopo gli 85 anni crescono il bisogno di assistenza, di cure a casa e di servizi vicini. È la fascia d’età '
        'che più dipende dall’organizzazione del territorio: trasporti, medici, farmacie, aiuto domestico.')

    # 03 — nascite e morti
    nat, pop = m['natural'], m['pop_change']
    all_neg = all(v < 0 for v in nat.values.values())
    nat_text = (
        (f'Nel {nat.period} in tutti i sette Comuni i morti hanno superato i nati: ' if all_neg else f'Nel {nat.period} ')
        + f'in Versilia il saldo naturale è di <b>{signed(nat.versilia)} ogni 1.000 abitanti</b>, contro '
          f'{signed(nat.benchmarks["tuscany"])} in Toscana e {signed(nat.benchmarks["italy"])} in Italia.')
    pop_text = (
        f'Fra il {period_label(pop.period).split("-")[0]} e il {period_label(pop.period).split("-")[-1]} la popolazione '
        f'della Versilia è {"calata" if pop.versilia < 0 else "cresciuta"} {del_(num(abs(pop.versilia), 1) + "%")} '
        f'({signed(pop.benchmarks["tuscany"])}% in Toscana): '
        f'da {signed(lo("pop_change")[1])}% a {nm(lo("pop_change")[0])} a {signed(hi("pop_change")[1])}% a '
        f'{nm(hi("pop_change")[0])}.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: nati meno morti {signed(nat.values[c])} ogni 1.000 abitanti nel {nat.period}; '
                  f'popolazione {signed(pop.values[c])}% dal {period_label(pop.period).split("-")[0]}.') for c in codes}
    ch3 = chapter(3, 'nascite-morti', 'Più morti che nati', 'La popolazione si rinnova?',
        f'<p>{nat_text}</p>{bar_chart(nat, N, "Saldo naturale: nati meno morti", "Dati Istat provvisori.")}'
        f'<p>{pop_text}</p>{bar_chart(pop, N, "Variazione della popolazione residente")}' + town_blocks(towns3),
        'Il saldo naturale misura il ricambio fra generazioni. Quando è negativo, la popolazione resta stabile solo se '
        'arrivano nuovi residenti. È una tendenza comune a gran parte dell’Italia, che in Versilia si somma a una '
        'popolazione già più anziana della media.')

    # 04 — salute
    life = m['life']
    life_text = (
        f'Nel {life.period} la speranza di vita alla nascita era di <b>{num(life.benchmarks["versilia"], 1)} anni</b> nella '
        f'zona Versilia e di {num(life.benchmarks["tuscany"], 1)} in Toscana: da {num(lo("life")[1], 1)} anni a '
        f'{nm(lo("life")[0])} a {num(hi("life")[1], 1)} a {nm(hi("life")[0])}.')
    towns4 = {c: f'<b>{esc(nm(c))}</b>: speranza di vita alla nascita {num(life.values[c], 1)} anni ({life.period}).' for c in codes}
    ch4 = chapter(4, 'salute', 'Quanto si vive', 'Si vive più a lungo qui che nel resto della Toscana?',
        f'<p>{life_text}</p>{bar_chart(life, N, "Speranza di vita alla nascita", "Nei Comuni piccoli il dato può variare molto da un anno all’altro.")}'
        + town_blocks(towns4),
        'La speranza di vita riassume in un numero le condizioni di salute di una popolazione. Nei Comuni piccoli '
        'pochi decessi bastano a spostarla di molto, quindi le differenze vanno lette con prudenza e seguite nel tempo.')

    # 05 — assistenza
    care, ph = m['home_care'], m['pharmacies']
    care_text = (
        f'Nel {care.period} gli anziani assistiti a domicilio erano {num(care.benchmarks["versilia"], 1)} ogni 1.000 nella '
        f'zona Versilia, contro <b>{num(care.benchmarks["tuscany"], 1)} in Toscana</b>: da {num(lo("home_care")[1], 1)} a '
        f'{nm(lo("home_care")[0])} a {num(hi("home_care")[1], 1)} a {nm(hi("home_care")[0])}.')
    ph_text = (
        f'Le farmacie sono {num(ph.benchmarks["tuscany"], 2)} ogni 1.000 abitanti in Toscana; in Versilia vanno da '
        f'{num(lo("pharmacies")[1], 2)} a {nm(lo("pharmacies")[0])} a {num(hi("pharmacies")[1], 2)} a '
        f'{nm(hi("pharmacies")[0])} (si contano anche succursali e dispensari stagionali).')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: {num(care.values[c], 1)} anziani assistiti a domicilio ogni 1.000 '
                  f'(Toscana {num(care.benchmarks["tuscany"], 1)}); {num(ph.values[c], 2)} farmacie ogni 1.000 abitanti.')
              for c in codes}
    ch5 = chapter(5, 'assistenza', 'Cure vicino a casa', 'Quanti anziani ricevono assistenza a domicilio?',
        f'<p>{care_text}</p>{bar_chart(care, N, "Anziani assistiti a domicilio", "Tasso standardizzato per età: permette di confrontare Comuni con popolazioni diverse.")}'
        f'<p>{ph_text}</p>{bar_chart(ph, N, "Farmacie ogni 1.000 abitanti")}' + town_blocks(towns5),
        'L’assistenza domiciliare permette agli anziani di restare a casa propria. Il dato conta le persone assistite, '
        'non quante ne avrebbero bisogno: un valore basso può indicare meno bisogno, meno offerta o altre forme di '
        'aiuto, per esempio badanti pagate dalle famiglie.')

    # 06 — spesa sociale
    soc = m['social']
    soc_below = [c for c, v, _ in soc.ranking if v < soc.benchmarks['tuscany']]
    soc_text = (
        f'Nel {soc.period} i Comuni hanno speso per i servizi sociali da {num(lo("social")[1])} € per abitante a '
        f'{nm(lo("social")[0])} a <b>{num(hi("social")[1])} €</b> a {nm(hi("social")[0])}. '
        f'{count_words(len(soc_below), total)[:1].upper()}{count_words(len(soc_below), total)[1:]} restano sotto la media '
        f'toscana ({num(soc.benchmarks["tuscany"])} €).')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: {num(soc.values[c])} € per abitante di spesa sociale nel {soc.period} '
                  f'(Toscana {num(soc.benchmarks["tuscany"])} €).') for c in codes}
    ch6 = chapter(6, 'spesa-sociale', 'Quanto spendono i Comuni', 'Quante risorse vanno ai servizi sociali?',
        f'<p>{soc_text}</p>{bar_chart(soc, N, "Spesa dei Comuni per i servizi sociali per abitante")}' + town_blocks(towns6),
        'La spesa sociale comprende servizi per anziani, disabili, famiglie, minori e persone in difficoltà, anche '
        'gestiti in forma associata. È l’ultimo anno disponibile a livello comunale; non misura il bisogno né la '
        'qualità dei servizi, ma indica quante risorse i Comuni mettono in campo.')

    key_points = [
        (num(hi('old')[1]), f'Anziani ogni 100 ragazzi sotto i 15 anni a {nm(hi("old")[0])}, il valore più alto.', 'quanti'),
        (f'{len([v for v in chg.values.values() if v > 0])} su {total}',
         f'Comuni dove l’indice di vecchiaia è cresciuto dal {first} al {last}.', 'quanti'),
        (pct(very.versilia), f'Residenti con 85 anni o più in Versilia. In Italia sono {il(pct(very.benchmarks["italy"]))}.',
         'grandi-anziani'),
        (signed(nat.versilia), f'Nati meno morti ogni 1.000 abitanti in Versilia nel {nat.period}: in Toscana '
                               f'{signed(nat.benchmarks["tuscany"])}.', 'nascite-morti'),
        (num(care.benchmarks['versilia'], 1), f'Anziani assistiti a domicilio ogni 1.000 nella zona Versilia, contro '
                                              f'{num(care.benchmarks["tuscany"], 1)} in Toscana.', 'assistenza'),
        (f'{len(soc_below)} su {total}', f'Comuni con una spesa sociale per abitante sotto la media toscana '
                                         f'({num(soc.benchmarks["tuscany"])} €).', 'spesa-sociale'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Indice di vecchiaia', num(old.values[c]), f'{signed(chg.values[c])}% dal {first}'),
        summary_item('Anziani ogni 100 in età da lavoro', num(dep.values[c], 1), f'Toscana {num(dep.benchmarks["tuscany"], 1)}'),
        summary_item('Residenti di 85 anni e più', pct(very.values[c]), f'Toscana {pct(very.benchmarks["tuscany"])}'),
        summary_item('Nati meno morti ogni 1.000 abitanti', signed(nat.values[c]), f'Toscana {signed(nat.benchmarks["tuscany"])}'),
        summary_item('Speranza di vita', num(life.values[c], 1) + ' anni', f'Toscana {num(life.benchmarks["tuscany"], 1)}'),
        summary_item('Anziani assistiti a domicilio ogni 1.000', num(care.values[c], 1),
                     f'Toscana {num(care.benchmarks["tuscany"], 1)}'),
        summary_item('Spesa sociale per abitante', num(soc.values[c]) + ' €', f'Toscana {num(soc.benchmarks["tuscany"])} €'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanti anziani vivono da soli: il dato sulle famiglie di una persona non distingue l’età.',
        'Quanti anziani non autosufficienti non ricevono aiuto: i dati contano chi è assistito, non chi ne avrebbe bisogno.',
        'Quante famiglie si affidano a badanti o assistenti private.',
        'Quanto si aspetta per una visita o un posto in una residenza per anziani.',
        'Come stanno davvero gli anziani: i dati di salute disponibili sono medie su tutta la popolazione.',
    ]
    return dict(
        slug='anziani', title='Invecchiare in Versilia', eyebrow='Dossier · Anziani e salute',
        unknown_topic='sulla terza età', theme='demografia', theme_label='Tutti i dati sulla popolazione',
        lead='Quanti anziani ci sono, quanto in fretta invecchia la popolazione, quanto si vive e quanta assistenza c’è: '
             'una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Indice di vecchiaia, grandi anziani, nascite e morti, speranza di vita, assistenza domiciliare e spesa '
                    'sociale nei sette Comuni della Versilia, con confronti con Toscana e Italia.',
        periods=f'Popolazione {old.period}, bilancio demografico {nat.period}, speranza di vita {life.period}, '
                f'assistenza domiciliare {care.period}, spesa sociale {soc.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('quanti', 'Quanti anziani'), ('grandi-anziani', 'I grandi anziani'), ('nascite-morti', 'Più morti che nati'),
             ('salute', 'Quanto si vive'), ('assistenza', 'Cure vicino a casa'), ('spesa-sociale', 'Quanto spendono i Comuni')])


# ---------------------------------------------------------------------------
# Dossier «Crescere in Versilia».

def scuola(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    TI = ('tuscany', 'italy')
    m = {
        'nursery': engine.measure('nursery', 'earlyChildhoodPotentialCapacityRate', 'total',
                                  'Posti nei servizi per la prima infanzia ogni 100 bambini fra 3 e 36 mesi',
                                  'percent', 1, benchmarks=('tuscany',), versilia=True),
        'full_time': engine.measure('full_time', 'primaryFullTimeShare', 'total',
                                    'Alunni della primaria a tempo pieno, %', 'percent', 1, benchmarks=TI, versilia=True),
        'class_size': engine.measure('class_size', 'studentsPerClass', 'total', 'Alunni per classe', 'decimal', 1,
                                     benchmarks=TI, versilia=True),
        'old_buildings': engine.measure('old_buildings', 'schoolBuildingAge', 'part:builtBy1970',
                                        'Edifici scolastici costruiti entro il 1970, %', 'percent', 1,
                                        benchmarks=TI, versilia=True),
        'canteen': engine.measure('canteen', 'schoolBuildingFacilities', 'part:canteen',
                                  'Edifici scolastici con mensa, %', 'percent', 1, benchmarks=TI, versilia=True),
        'g5_ita': engine.measure('g5_ita', 'invalsiResults', 'view:g5-italiano',
                                 'Punteggio medio INVALSI di italiano, quinta primaria', 'decimal', 0,
                                 benchmarks=TI, partial=True),
        'g5_mat': engine.measure('g5_mat', 'invalsiResults', 'view:g5-matematica',
                                 'Punteggio medio INVALSI di matematica, quinta primaria', 'decimal', 0,
                                 benchmarks=TI, partial=True),
        'diploma': engine.measure('diploma', 'diplomaPlus', 'total',
                                  'Residenti di 25-64 anni con almeno il diploma, %', 'percent', 1),
        'spend': engine.measure('spend', 'educationMissionExpenditurePerResident', 'total',
                                'Spesa comunale per istruzione e diritto allo studio, euro per abitante', 'eur', 0,
                                versilia=True),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    cap = lambda text: text[:1].upper() + text[1:]

    # 01 — nidi
    nur = m['nursery']
    none = [c for c, v, _ in nur.ranking if v == 0]
    nur_text = (
        f'Nell’{period_label(nur.period)} in Versilia c’erano <b>{num(nur.versilia, 1)} posti nei servizi per la prima '
        f'infanzia ogni 100 bambini</b> fra 3 e 36 mesi, contro {num(nur.benchmarks["tuscany"], 1)} in Toscana. Si va da '
        f'{num(hi("nursery")[1], 1)} a {nm(hi("nursery")[0])}'
        + (f' a nessun posto a {join_names([nm(c) for c in none])}.' if none else
           f' a {num(lo("nursery")[1], 1)} a {nm(lo("nursery")[0])}.'))
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {num(nur.values[c], 1)} posti ogni 100 bambini fra 3 e 36 mesi '
                  f'(Toscana {num(nur.benchmarks["tuscany"], 1)}).') for c in codes}
    ch1 = chapter(1, 'nidi', 'I primi anni', 'Quanti posti al nido ci sono per i bambini piccoli?',
        f'<p>{nur_text}</p>{bar_chart(nur, N, "Posti nei servizi per la prima infanzia", "Comprende nidi e altri servizi educativi, pubblici e privati.")}'
        + town_blocks(towns1),
        'Il nido conta per lo sviluppo dei bambini e per il lavoro dei genitori, soprattutto delle madri. Un Comune '
        'senza posti non significa per forza famiglie senza servizio: i bambini possono frequentare strutture nei Comuni '
        'vicini. Il dato misura l’offerta, non le iscrizioni né le liste d’attesa.')

    # 02 — tempo pieno e classi
    ft, cls = m['full_time'], m['class_size']
    ft_text = (
        f'Nella scuola primaria il tempo pieno riguarda <b>{il(pct(ft.versilia))} degli alunni</b> in Versilia, contro '
        f'{il(pct(ft.benchmarks["tuscany"]))} in Toscana e {il(pct(ft.benchmarks["italy"]))} in Italia: '
        f'{dal(pct(lo("full_time")[1]))} di {nm(lo("full_time")[0])} {al(pct(hi("full_time")[1]))} di {nm(hi("full_time")[0])}.')
    cls_text = (
        f'Le classi hanno in media {num(cls.versilia, 1)} alunni ({num(cls.benchmarks["tuscany"], 1)} in Toscana), '
        f'da {num(lo("class_size")[1], 1)} a {nm(lo("class_size")[0])} a {num(hi("class_size")[1], 1)} a {nm(hi("class_size")[0])}.')
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: tempo pieno per {il(pct(ft.values[c]))} degli alunni della primaria; '
                  f'{num(cls.values[c], 1)} alunni per classe.') for c in codes}
    ch2 = chapter(2, 'tempo-pieno', 'Tempo pieno e classi', 'Quanti bambini restano a scuola anche il pomeriggio?',
        f'<p>{ft_text}</p>{bar_chart(ft, N, "Alunni della primaria a tempo pieno")}'
        f'<p>{cls_text}</p>{bar_chart(cls, N, "Alunni per classe")}' + town_blocks(towns2),
        'Il tempo pieno allunga la giornata scolastica e aiuta le famiglie in cui entrambi i genitori lavorano. I dati '
        'riguardano le scuole che si trovano nel Comune, frequentate anche da bambini di altri Comuni; nei Comuni '
        'piccoli poche classi bastano a cambiare molto la percentuale.')

    # 03 — edifici
    old, can = m['old_buildings'], m['canteen']
    old_text = (
        f'In Versilia {il(pct(old.versilia))} degli edifici scolastici è stato costruito entro il 1970, contro '
        f'{il(pct(old.benchmarks["tuscany"]))} in Toscana: {dal(pct(lo("old_buildings")[1]))} di {nm(lo("old_buildings")[0])} '
        f'{al(pct(hi("old_buildings")[1]))} di {nm(hi("old_buildings")[0])}.')
    can_text = (
        f'Le scuole con mensa sono {il(pct(can.versilia))}, più che in Toscana ({pct(can.benchmarks["tuscany"])}) e in Italia '
        f'({pct(can.benchmarks["italy"])}).' if can.versilia > can.benchmarks['tuscany'] else
        f'Le scuole con mensa sono {il(pct(can.versilia))} ({pct(can.benchmarks["tuscany"])} in Toscana).')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(old.values[c]))} degli edifici scolastici è costruito entro il 1970; '
                  f'{il(pct(can.values[c]))} ha la mensa.') for c in codes}
    ch3 = chapter(3, 'edifici', 'Gli edifici', 'In che scuole studiano i ragazzi?',
        f'<p>{old_text}</p>{bar_chart(old, N, "Edifici scolastici costruiti entro il 1970")}'
        f'<p>{can_text}</p>{bar_chart(can, N, "Edifici scolastici con mensa")}' + town_blocks(towns3),
        'Gli edifici più vecchi richiedono più manutenzione e interventi di adeguamento, ma l’anno di costruzione non '
        'dice da solo se una scuola è sicura: molti edifici sono stati ristrutturati. Sono informazioni dichiarate '
        'dalle scuole all’anagrafe dell’edilizia scolastica.')

    # 04 — apprendimenti
    ita, mat = m['g5_ita'], m['g5_mat']
    ita_above = [c for c in ita.values if ita.values[c] > ita.benchmarks['tuscany']]
    mat_above = [c for c in mat.values if mat.values[c] > mat.benchmarks['tuscany']]
    inv_text = (
        f'Nelle prove INVALSI dell’{period_label(ita.period)}, gli alunni di quinta primaria hanno ottenuto in italiano '
        f'punteggi da {num(lo("g5_ita")[1])} a {nm(lo("g5_ita")[0])} a {num(hi("g5_ita")[1])} a {nm(hi("g5_ita")[0])} '
        f'(Toscana {num(ita.benchmarks["tuscany"])}); in matematica da {num(lo("g5_mat")[1])} a {nm(lo("g5_mat")[0])} a '
        f'{num(hi("g5_mat")[1])} a {nm(hi("g5_mat")[0])} (Toscana {num(mat.benchmarks["tuscany"])}). Sopra la media toscana: '
        f'{len(ita_above)} Comuni in italiano, {len(mat_above)} in matematica.')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: punteggio medio INVALSI di quinta primaria {num(ita.values[c])} in italiano e '
                  f'{num(mat.values[c])} in matematica (Toscana {num(ita.benchmarks["tuscany"])} e {num(mat.benchmarks["tuscany"])}).'
                  if c in ita.values and c in mat.values else
                  f'<b>{esc(nm(c))}</b>: per la quinta primaria il risultato INVALSI non è pubblicato.') for c in codes}
    ch4 = chapter(4, 'apprendimenti', 'Cosa imparano', 'Come vanno le prove nazionali di italiano e matematica?',
        f'<p>{inv_text}</p>{bar_chart(ita, N, "INVALSI italiano, quinta primaria", "Punteggi su scala nazionale con media 200 nel primo anno di rilevazione.")}'
        f'{bar_chart(mat, N, "INVALSI matematica, quinta primaria")}' + town_blocks(towns4),
        'Le prove INVALSI misurano alcune competenze di base con lo stesso metro in tutta Italia. Riguardano le scuole '
        'del Comune, non i bambini residenti, e in un Comune con poche classi il risultato dipende da pochi alunni: '
        'differenze di pochi punti non vanno lette come una classifica.')

    # 05 — titoli di studio
    dip = m['diploma']
    dip_text = (
        f'Nel {dip.period} fra i residenti di 25-64 anni ha almeno il diploma {dal(pct(lo("diploma")[1]))} di '
        f'{nm(lo("diploma")[0])} {al(pct(hi("diploma")[1]))} di <b>{nm(hi("diploma")[0])}</b>.')
    towns5 = {c: f'<b>{esc(nm(c))}</b>: {il(pct(dip.values[c]))} dei residenti di 25-64 anni ha almeno il diploma.' for c in codes}
    ch5 = chapter(5, 'titoli', 'Gli adulti e lo studio', 'Quanti adulti hanno almeno un diploma?',
        f'<p>{dip_text}</p>{bar_chart(dip, N, "Residenti di 25-64 anni con almeno il diploma")}' + town_blocks(towns5),
        'Il titolo di studio degli adulti dice molto sull’ambiente in cui crescono i ragazzi e sulle possibilità del '
        'mercato del lavoro locale. Non misura le competenze, né quanto il lavoro svolto corrisponda agli studi fatti.')

    # 06 — spesa
    sp = m['spend']
    sp_text = (
        f'Nel {sp.period} i sette Comuni hanno impegnato per istruzione e diritto allo studio nel complesso '
        f'<b>{num(sp.versilia)} € per abitante</b>: da {num(lo("spend")[1])} € a {nm(lo("spend")[0])} a '
        f'{num(hi("spend")[1])} € a {nm(hi("spend")[0])}.')
    towns6 = {c: f'<b>{esc(nm(c))}</b>: {num(sp.values[c])} € per abitante per istruzione nel {sp.period}.' for c in codes}
    ch6 = chapter(6, 'spesa', 'Quanto spendono i Comuni', 'Quanto investono le amministrazioni nella scuola?',
        f'<p>{sp_text}</p>{bar_chart(sp, N, "Spesa comunale per istruzione per abitante")}' + town_blocks(towns6),
        'I Comuni pagano edifici, mense, trasporto scolastico, servizi per l’infanzia e assistenza agli alunni. La '
        'spesa comprende anche gli investimenti: un anno con un cantiere importante, come la costruzione di una nuova '
        'scuola, fa salire molto il valore senza che cambino i servizi di tutti i giorni.')

    key_points = [
        (num(nur.versilia, 1), f'Posti al nido ogni 100 bambini fra 3 e 36 mesi in Versilia. In Toscana '
                               f'{num(nur.benchmarks["tuscany"], 1)}.', 'nidi'),
        (f'{len(none)} su {total}' if none else num(lo('nursery')[1], 1),
         'Comuni senza posti nei servizi per la prima infanzia.' if none else 'Il valore più basso.', 'nidi'),
        (pct(ft.versilia), f'Alunni della primaria a tempo pieno, contro {il(pct(ft.benchmarks["tuscany"]))} in Toscana.',
         'tempo-pieno'),
        (pct(old.versilia), 'Edifici scolastici costruiti entro il 1970.', 'edifici'),
        (pct(can.versilia), f'Scuole con mensa. In Italia sono {il(pct(can.benchmarks["italy"]))}.', 'edifici'),
        (f'{num(sp.versilia)} €', 'Spesa dei Comuni per istruzione per abitante nel complesso della Versilia.', 'spesa'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Posti al nido ogni 100 bambini', num(nur.values[c], 1), f'Toscana {num(nur.benchmarks["tuscany"], 1)}'),
        summary_item('Tempo pieno nella primaria', pct(ft.values[c]), f'Toscana {pct(ft.benchmarks["tuscany"])}'),
        summary_item('Alunni per classe', num(cls.values[c], 1), f'Toscana {num(cls.benchmarks["tuscany"], 1)}'),
        summary_item('Edifici costruiti entro il 1970', pct(old.values[c]), f'Toscana {pct(old.benchmarks["tuscany"])}'),
        summary_item('INVALSI italiano, quinta primaria', num(ita.values[c]) if c in ita.values else 'non pubblicato',
                     f'Toscana {num(ita.benchmarks["tuscany"])}'),
        summary_item('Adulti con almeno il diploma', pct(dip.values[c]), f'{ordinal(dip.rank(c))} su 7'),
        summary_item('Spesa per istruzione per abitante', num(sp.values[c]) + ' €', f'Versilia {num(sp.versilia)} €'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanti bambini restano in lista d’attesa per il nido e quanto pagano le famiglie.',
        'Quanti ragazzi lasciano la scuola prima del diploma: a livello comunale non c’è un dato pubblico completo.',
        'Dove vanno a scuola i ragazzi delle superiori: molti studiano in Comuni diversi da quello in cui vivono.',
        'Lo stato reale di sicurezza degli edifici: l’età di costruzione non basta a dirlo.',
        'I risultati INVALSI delle medie e delle superiori per tutti i Comuni: dove ci sono poche scuole non sono pubblicati.',
    ]
    return dict(
        slug='scuola', title='Crescere in Versilia', eyebrow='Dossier · Scuola e infanzia',
        unknown_topic='sulla scuola', theme='istruzione', theme_label='Tutti i dati sull’istruzione',
        lead='Posti al nido, tempo pieno, edifici scolastici, risultati delle prove nazionali, titoli di studio e spesa dei '
             'Comuni: una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Servizi per la prima infanzia, tempo pieno, classi, edifici scolastici, prove INVALSI, titoli di studio '
                    'e spesa per l’istruzione nei sette Comuni della Versilia.',
        periods=f'Servizi per l’infanzia e scuole {period_label(nur.period)}, prove INVALSI {period_label(ita.period)}, '
                f'titoli di studio {dip.period}, bilanci comunali {sp.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('nidi', 'I primi anni'), ('tempo-pieno', 'Tempo pieno e classi'), ('edifici', 'Gli edifici'),
             ('apprendimenti', 'Cosa imparano'), ('titoli', 'Gli adulti e lo studio'), ('spesa', 'Quanto spendono i Comuni')])


DOSSIERS = {'casa': casa, 'lavoro': lavoro, 'turismo': turismo, 'anziani': anziani, 'scuola': scuola}


# ---------------------------------------------------------------------------
# Pagina, CSV e PDF.

def limits() -> dict:
    return json.loads(LIMITS.read_text(encoding='utf-8').split('export default', 1)[1].strip().rstrip(';'))


def write_csv(dossier: dict, names: dict[str, str], path: Path) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Indicatore', 'Territorio', 'Periodo', 'Valore', 'Unità', 'Fonte'])
    unit = {'eur': 'euro', 'eurm2': 'euro al m²', 'eurm2month': 'euro al m² al mese', 'percent': '%',
            'per1000': 'ogni 1.000 abitanti', 'decimal': 'persone', 'change': 'variazione %',
            'points': 'punti percentuali', 'per1000s': 'ogni 1.000 abitanti', 'count': 'numero', 'nights': 'notti',
            'per100': 'ogni 100 persone di 15-64 anni', 'years': 'anni', 'per1000old': 'ogni 1.000 residenti di 65 anni e più'}
    for measure in dossier['measures'].values():
        rows = [(names[c], v) for c, v, _ in measure.ranking]
        if measure.versilia is not None:
            rows.append(('Versilia', measure.versilia))
        rows += [(BENCH_LABEL[s], v) for s, v in measure.benchmarks.items()]
        for territory, value in rows:
            writer.writerow([measure.label, territory, period_label(measure.period),
                             num(value, 0 if measure.unit in ('eur', 'count') else max(measure.decimals, 2)).replace('.', ''),
                             unit[measure.unit], source_name(measure.source)])
    path.write_bytes(b'\xef\xbb\xbf' + buffer.getvalue().encode('utf-8'))


def render(dossier: dict, engine: Engine, dist: Path, page: Path, built: str) -> str:
    names = engine.names
    shell = extract_native_shell(dist, page)
    styles = '\n'.join(line for line in shell.styles.splitlines() if 'secondary-pages-ui.css' not in line)
    url = BASE_URL + dossier['slug'] + '/'
    options = ''.join(f'<option value="{slug(names[c])}" data-code="{c}">{esc(names[c])}</option>'
                      for c in sorted(engine.codes, key=lambda c: names[c]))
    points = ''.join(f'<li><a href="#{anchor}"><b>{esc(big)}</b><span>{esc(text)}</span></a></li>'
                     for big, text, anchor in dossier['key_points'])
    town_cards = ''.join(
        f'<div class="dr-town-card" data-town="{c}" hidden><h3>{esc(names[c])} in breve</h3>{body}'
        f'<p class="dr-town-more"><a href="../../comuni/{slug(names[c])}/">Tutti i dati di {esc(names[c])}</a></p></div>'
        for c, body in dossier['towns_summary'].items())
    toc = ''.join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in dossier['toc'])
    readings = limits()['warnings']
    sources = {}
    for measure in dossier['measures'].values():
        link, items, cautions = sources.setdefault(source_name(measure.source), (measure.source, [], []))
        items.append(f'{measure.label} ({period_label(measure.period)})')
        for code in measure.warnings:
            if code not in readings:
                raise ValueError('avvertenza_senza_lettura_italiana:' + code)
            if readings[code] not in cautions:
                cautions.append(readings[code])
    source_items = ''.join(
        f'<li><a href="{esc(link)}" rel="noreferrer" target="_blank">{esc(name)}</a><span>{esc("; ".join(items))}</span>'
        f'<ul class="dr-notes">{"".join(f"<li>{esc(t)}</li>" for t in cautions)}</ul></li>'
        for name, (link, items, cautions) in sources.items())
    unknown = ''.join(f'<li>{esc(t)}</li>' for t in dossier['unknown'])
    title = f'{dossier["title"]} · Dossier · Osservatorio Versilia'
    pdf = f'{dossier["slug"]}-versilia.pdf'
    csv_name = f'{dossier["slug"]}-dati.csv'
    structured = json.dumps({'@context': 'https://schema.org', '@type': 'Report', 'name': dossier['title'],
                             'description': dossier['description'], 'url': url, 'inLanguage': 'it',
                             'publisher': {'@type': 'Organization', 'name': 'Osservatorio Versilia'}}, ensure_ascii=False)
    structured_hash = base64.b64encode(hashlib.sha256(structured.encode()).digest()).decode()
    return f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'sha256-{structured_hash}'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'">
<title>{esc(title)}</title><meta name="description" content="{esc(dossier['description'])}">
{social(title, dossier['description'], url)}
<link rel="canonical" href="{url}"><script type="application/ld+json">{structured}</script>
<link rel="icon" href="../../favicon.svg" type="image/svg+xml"><link rel="manifest" href="../../site.webmanifest">
{styles}<link rel="stylesheet" href="../report.css"><meta name="theme-color" content="#0F3654">
</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
{shell.header}<div id="app"><main id="dossier" class="dr" data-dossier="{dossier['slug']}">
<header class="dr-hero"><div class="dr-wrap">
<nav class="dr-crumbs" aria-label="Percorso pagina"><a href="../../">Home</a> · <a href="../">Dossier</a></nav>
<p class="dr-eyebrow">{esc(dossier['eyebrow'])}</p>
<h1>{esc(dossier['title'])}</h1>
<p class="dr-lead">{esc(dossier['lead'])}</p>
<p class="dr-meta">Relazione dell’Osservatorio Versilia · catalogo dati aggiornato al {built}<br>{esc(dossier['periods'])}</p>
<div class="dr-actions"><a class="dr-btn" href="{pdf}" download>Scarica il report (PDF)</a><a class="dr-btn dr-btn-ghost" href="{csv_name}" download>Scarica i dati (CSV per Excel)</a></div>
</div></header>
<div class="dr-picker" hidden><div class="dr-wrap"><label for="dr-town">Leggi il dossier per</label>
<select id="dr-town"><option value="">Tutta la Versilia</option>{options}</select>
<button type="button" class="dr-share" hidden>Copia il link</button><span class="dr-share-ok" role="status"></span></div></div>
<div class="dr-wrap dr-body">
<nav class="dr-toc" aria-label="Indice del dossier"><p>Indice</p><ol>{toc}<li><a href="#non-sappiamo">Cosa non sappiamo</a></li><li><a href="#fonti">Fonti e metodo</a></li></ol></nav>
<div class="dr-content">
<section class="dr-summary" aria-labelledby="sintesi"><h2 id="sintesi">In sintesi</h2><ol class="dr-points">{points}</ol>{town_cards}</section>
{''.join(dossier['chapters'])}
<section class="dr-chapter dr-unknown" id="non-sappiamo" aria-labelledby="non-sappiamo-title"><h2 id="non-sappiamo-title">Cosa non sappiamo</h2>
<p>Alcune domande importanti {esc(dossier['unknown_topic'])} non hanno ancora una risposta nei dati pubblici disponibili:</p><ul>{unknown}</ul></section>
<section class="dr-chapter dr-sources" id="fonti" aria-labelledby="fonti-title"><h2 id="fonti-title">Fonti e metodo</h2>
<p>Tutti i numeri di questo dossier sono calcolati dall’Osservatorio sugli stessi dati pubblicati nelle schede del sito.
I confronti con Toscana e Italia compaiono solo dove le misure sono confrontabili. Per la Versilia nel suo insieme si
usano i totali dei sette Comuni, non la media dei loro valori.{(' ' + esc(dossier['method'])) if dossier.get('method') else ''}</p>
<h3>Fonti e note sui dati</h3><ul class="dr-source-list">{source_items}</ul>
<p class="dr-more">Vuoi esplorare altri dati? <a href="../../confronta/{dossier['theme']}/">{esc(dossier['theme_label'])}</a> · <a href="../../stato-dati/">Stato dei dati</a> · <a href="../../segnala/">Segnala un errore</a></p>
</section>
</div></div></main></div>{shell.footer}
<script src="{esc(shell.app_bundle)}" defer></script><script src="../report.js" defer></script>
</body></html>'''


def social(title: str, description: str, url: str) -> str:
    image = 'https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg'
    alt = 'Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia'
    og = {'og:title': title, 'og:description': description, 'og:type': 'article', 'og:locale': 'it_IT',
          'og:url': url, 'og:site_name': 'Osservatorio Versilia', 'og:image': image, 'og:image:alt': alt}
    twitter = {'card': 'summary_large_image', 'title': title, 'description': description, 'site': '@OssVersilia',
               'image': image, 'image:alt': alt}
    return '\n'.join([f'<meta property="{k}" content="{esc(v)}">' for k, v in og.items()]
                     + [f'<meta name="twitter:{k}" content="{esc(v)}">' for k, v in twitter.items()])


INDEX_LEAD = ('Relazioni sui grandi temi della Versilia: che cosa dicono i dati pubblici sulla casa, sul lavoro, sul '
              'turismo, sugli anziani e sulla scuola, per tutto il territorio e Comune per Comune.')


def index_card(d: dict) -> str:
    big, text, _ = d['key_points'][0]
    return (f'<li class="dr-card"><a class="dr-card-link" href="{d["slug"]}/">'
            f'<p class="dr-eyebrow">{esc(d["eyebrow"].split(" · ", 1)[-1])}</p>'
            f'<h2>{esc(d["title"])}</h2><p class="dr-card-lead">{esc(d["lead"].split(": una lettura")[0])}.</p>'
            f'<p class="dr-card-figure"><b>{esc(big)}</b><span>{esc(text)}</span></p>'
            f'<span class="dr-card-more">Leggi il dossier</span></a>'
            f'<p class="dr-card-files"><a href="{d["slug"]}/{d["slug"]}-versilia.pdf" download>PDF</a> · '
            f'<a href="{d["slug"]}/{d["slug"]}-dati.csv" download>Dati CSV</a></p></li>')


def render_index(dossiers: list[dict], dist: Path, page: Path, built: str) -> str:
    shell = extract_native_shell(dist, page)
    styles = '\n'.join(line for line in shell.styles.splitlines() if 'secondary-pages-ui.css' not in line)
    url = BASE_URL
    title = 'Dossier · Osservatorio Versilia'
    description = ('Relazioni divulgative sui dati pubblici dei sette Comuni della Versilia: casa, lavoro, turismo, '
                   'anziani e scuola.')
    cards = ''.join(index_card(d) for d in dossiers)
    structured = json.dumps({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Dossier',
                             'description': description, 'url': url, 'inLanguage': 'it',
                             'hasPart': [{'@type': 'Report', 'name': d['title'], 'url': BASE_URL + d['slug'] + '/'}
                                         for d in dossiers]}, ensure_ascii=False)
    structured_hash = base64.b64encode(hashlib.sha256(structured.encode()).digest()).decode()
    head = (
        '<!doctype html>\n<html lang="it"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' '
        f'\'sha256-{structured_hash}\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; connect-src '
        f'\'self\'; base-uri \'none\'; form-action \'none\'; object-src \'none\'">\n'
        f'<title>{esc(title)}</title><meta name="description" content="{esc(description)}">\n'
        f'{social(title, description, url)}\n'
        f'<link rel="canonical" href="{url}"><script type="application/ld+json">{structured}</script>\n'
        '<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="manifest" href="../site.webmanifest">\n'
        f'{styles}<link rel="stylesheet" href="report.css"><meta name="theme-color" content="#0F3654">\n'
        '</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">\n')
    body = (
        f'{shell.header}<div id="app"><main id="dossier" class="dr dr-index">\n'
        '<header class="dr-hero"><div class="dr-wrap">\n'
        '<nav class="dr-crumbs" aria-label="Percorso pagina"><a href="../">Home</a> · <span>Dossier</span></nav>\n'
        '<p class="dr-eyebrow">Osservatorio Versilia</p>\n<h1>Dossier</h1>\n'
        f'<p class="dr-lead">{esc(INDEX_LEAD)}</p>\n'
        '<p class="dr-meta">Ogni dossier ha una versione per la Versilia e una per ciascun Comune, un PDF da scaricare '
        f'e i dati in formato CSV · catalogo dati aggiornato al {built}</p>\n</div></header>\n'
        f'<div class="dr-wrap dr-index-body"><ul class="dr-cards">{cards}</ul>\n'
        '<p class="dr-more">Hai una domanda precisa? <a href="../chiedi/">Chiedi alla Versilia</a> · '
        '<a href="../stato-dati/">Stato dei dati</a> · <a href="../segnala/">Segnala un errore</a></p>\n'
        f'</div></main></div>{shell.footer}\n'
        f'<script src="{esc(shell.app_bundle)}" defer></script>\n</body></html>')
    return head + body


def write_pdf(page: Path, target: Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Senza script: la versione Versilia è già tutta nell'HTML e il runtime del
        # sito non deve sostituire la pagina aperta da file locale.
        tab = browser.new_page(java_script_enabled=False)
        tab.goto(page.resolve().as_uri(), wait_until='load')
        tab.emulate_media(media='print')
        tab.pdf(path=str(target), format='A4', print_background=True,
                margin=dict(top='16mm', bottom='16mm', left='14mm', right='14mm'),
                display_header_footer=True, header_template='<span></span>',
                footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#61717b">'
                                'Osservatorio Versilia · osservatorioversilia.it · pagina <span class="pageNumber"></span> di '
                                '<span class="totalPages"></span></div>')
        browser.close()


def build(dist: Path = ROOT / 'dist', pdf: bool = True) -> list[Path]:
    engine = Engine(dist / 'data/site-data.json')
    folder = dist / 'dossier'
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CSS, folder / 'report.css')
    shutil.copyfile(JS, folder / 'report.js')
    # Data deterministica: quella del catalogo, non quella della build.
    built = engine.engine.catalog['updated']
    pages, made = [], []
    for key, make in DOSSIERS.items():
        dossier = make(engine)
        made.append(dossier)
        target = folder / dossier['slug'] / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(dossier, engine, dist, target, built), encoding='utf-8')
        write_csv(dossier, engine.names, target.parent / f'{dossier["slug"]}-dati.csv')
        if pdf:
            write_pdf(target, target.parent / f'{dossier["slug"]}-versilia.pdf')
        pages.append(target)
    index = folder / 'index.html'
    index.write_text(render_index(made, dist, index, built), encoding='utf-8')
    # Lanciati il 31 ottobre 2026: indicizzabili e nella sitemap.
    from site_chrome import ensure_sitemap_entries
    base = 'https://osservatorioversilia.it/dossier/'
    ensure_sitemap_entries(dist, (base, *(f"{base}{d['slug']}/" for d in made)))
    return [index] + pages


if __name__ == '__main__':
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist'
    for page in build(dist):
        print('Dossier generato: ' + str(page))
