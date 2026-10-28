#!/usr/bin/env python3
"""Dossier tematici in forma di relazione divulgativa.

Prototipo: «Abitare in Versilia» (casa e affitti). Ogni cifra viene da una
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
SOURCE_NAMES = {
    'agenziaentrate.gov.it': 'Agenzia delle Entrate — Osservatorio del mercato immobiliare (OMI)',
    'esploradati.istat.it': 'Istat — Censimento permanente e capacità ricettiva',
    'istat.it': 'Istat — Censimento permanente e capacità ricettiva',
    'finanze.gov.it': 'Ministero dell’Economia e delle Finanze — Dichiarazioni dei redditi su base comunale',
    'erplucca.it': 'ERP Lucca — Bilanci e rendiconti dell’edilizia residenziale pubblica',
}
TENS = ['nessuna', 'una', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove']


# ---------------------------------------------------------------------------
# Formattazione italiana: al massimo due decimali, separatori it-IT.

def num(value: float, decimals: int = 0) -> str:
    text = f'{value:,.{decimals}f}'
    return text.replace(',', ' ').replace('.', ',').replace(' ', '.')


def pct(value: float, decimals: int = 1) -> str:
    return num(value, decimals) + '%'


def signed(value: float, decimals: int = 1) -> str:
    return ('+' if value > 0 else '−' if value < 0 else '') + num(abs(value), decimals)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def slug(name: str) -> str:
    return re.sub(r'[^a-z]+', '-', name.lower()).strip('-')


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' e ' + names[-1]


def ordinal(rank: int) -> str:
    return f'{rank}°'


def source_name(url: str) -> str:
    host = re.sub(r'^https?://', '', url).split('/')[0]
    for key, name in SOURCE_NAMES.items():
        if host.endswith(key):
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
                'per1000': lambda v: num(v) + ' ogni 1.000 abitanti', 'decimal': lambda v: num(v, 2),
                'change': lambda v: signed(v) + '%'}[self.unit](value)

    def short(self, value: float) -> str:
        return {'eurm2month': lambda v: num(v, 2) + ' €', 'per1000': lambda v: num(v),
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

    def measure(self, key, metric, dimension, label, unit, decimals=1, benchmarks=(), versilia=False) -> Measure:
        selector = {'metric': metric, 'dimension': dimension, 'towns': self.codes}
        compare = self.ask({'operation': 'compare', 'selectors': [selector]})
        observations = compare['observations']
        periods = {o['period'] for o in observations}
        assert len(periods) == 1 and len(observations) == len(self.codes), (key, periods)
        ranked = self.ask({'operation': 'rank', 'selectors': [selector]})['result']['ranking']
        values = {o['geography']: o['value'] for o in observations}
        assert {r['geography']: r['value'] for r in ranked} == values, key
        sources = {o['source'] for o in observations}
        measure = Measure(key, metric, dimension, label, unit, decimals, periods.pop(), values,
                          [(r['geography'], r['value'], r['rank']) for r in ranked], sorted(sources)[0],
                          warnings=list(compare['warnings']))
        for scope in benchmarks:
            gap = self.ask({'operation': 'benchmark_gap', 'benchmark': scope,
                            'selectors': [dict(selector, towns=[self.codes[0]])]})
            measure.benchmarks[scope] = gap['result']['benchmarkValue']
            measure.warnings += [w for w in gap['warnings'] if w not in measure.warnings]
        if versilia:
            ratio = self.ask({'operation': 'weighted_ratio', 'selectors': [selector]})
            measure.versilia = ratio['result']['value']
            measure.warnings += [w for w in ratio['warnings'] if w not in measure.warnings]
        return measure


# ---------------------------------------------------------------------------
# Componenti di pagina.

BENCH_LABEL = {'tuscany': 'Toscana', 'italy': 'Italia', 'versilia': 'Versilia'}


def bar_chart(m: Measure, names: dict[str, str], title: str, note: str = '') -> str:
    refs = dict(m.benchmarks)
    if m.versilia is not None:
        refs = {'versilia': m.versilia, **refs}
    top = max([v for _, v, _ in m.ranking] + list(refs.values()))
    scale = lambda v: max(0.0, v) / top * 100 if top else 0
    rows = ''.join(
        f'<div class="dr-row" data-town="{code}"><span class="dr-name" style="grid-row:{i}">{esc(names[code])}</span>'
        f'<span class="dr-track" style="grid-row:{i}"><span class="dr-bar" style="width:{scale(value):.2f}%"></span></span>'
        f'<span class="dr-val" style="grid-row:{i}">{esc(m.short(value))}</span></div>'
        for i, (code, value, _) in enumerate(m.ranking, 1))
    lines = ''.join(f'<span class="dr-ref dr-ref-{scope}" style="left:{scale(value):.2f}%"></span>'
                    for scope, value in refs.items())
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
        f'Nel {single.period} le famiglie composte da una sola persona vanno dal {pct(lo("single")[1])} di '
        f'{nm(lo("single")[0])} al <b>{pct(hi("single")[1])}</b> di {nm(hi("single")[0])}. '
        f'{len(over_t)} Comuni su 7 superano la media toscana ({pct(single.benchmarks["tuscany"])}) e italiana '
        f'({pct(single.benchmarks["italy"])}).' if all(single.values[c] > single.benchmarks['italy'] for c in over_t) else
        f'Nel {single.period} le famiglie di una sola persona vanno dal {pct(lo("single")[1])} al {pct(hi("single")[1])}.')
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
        f'{signed(real.values[c])}% dal 2016 al netto dell’inflazione; il {pct(low.values[c])} dei dichiaranti '
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
        f'Il valore va dal {pct(lo("erp")[1])} di {nm(lo("erp")[0])} al {pct(hi("erp")[1])} di {nm(hi("erp")[0])}.')
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
        slug='casa', title='Abitare in Versilia', eyebrow='Dossier · Casa e affitti',
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


DOSSIERS = {'casa': casa}


# ---------------------------------------------------------------------------
# Pagina, CSV e PDF.

def limits() -> dict:
    return json.loads(LIMITS.read_text(encoding='utf-8').split('export default', 1)[1].strip().rstrip(';'))


def write_csv(dossier: dict, names: dict[str, str], path: Path) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Indicatore', 'Territorio', 'Periodo', 'Valore', 'Unità', 'Fonte'])
    unit = {'eur': 'euro', 'eurm2': 'euro al m²', 'eurm2month': 'euro al m² al mese', 'percent': '%',
            'per1000': 'ogni 1.000 abitanti', 'decimal': 'persone', 'change': 'variazione %'}
    for measure in dossier['measures'].values():
        rows = [(names[c], v) for c, v, _ in measure.ranking]
        if measure.versilia is not None:
            rows.append(('Versilia', measure.versilia))
        rows += [(BENCH_LABEL[s], v) for s, v in measure.benchmarks.items()]
        for territory, value in rows:
            writer.writerow([measure.label, territory, period_label(measure.period),
                             num(value, max(measure.decimals, 2 if measure.unit != 'eur' else 0)).replace('.', ''),
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
<meta name="robots" content="noindex">
{social(title, dossier['description'], url)}
<link rel="canonical" href="{url}"><script type="application/ld+json">{structured}</script>
<link rel="icon" href="../../favicon.svg" type="image/svg+xml"><link rel="manifest" href="../../site.webmanifest">
{styles}<link rel="stylesheet" href="../report.css"><meta name="theme-color" content="#0F3654">
</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
{shell.header}<div id="app"><main id="dossier" class="dr" data-dossier="{dossier['slug']}">
<header class="dr-hero"><div class="dr-wrap">
<nav class="dr-crumbs" aria-label="Percorso pagina"><a href="../../">Home</a> · <span>Dossier</span></nav>
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
<p>Alcune domande importanti sulla casa non hanno ancora una risposta nei dati pubblici disponibili:</p><ul>{unknown}</ul></section>
<section class="dr-chapter dr-sources" id="fonti" aria-labelledby="fonti-title"><h2 id="fonti-title">Fonti e metodo</h2>
<p>Tutti i numeri di questo dossier sono calcolati dall’Osservatorio sugli stessi dati pubblicati nelle schede del sito.
I confronti con Toscana e Italia compaiono solo dove le misure sono confrontabili. Per la Versilia nel suo insieme si
usano i totali dei sette Comuni, non la media dei loro valori. Gli esempi per {EXAMPLE_M2} m² sono semplici
moltiplicazioni delle quotazioni, utili come ordine di grandezza.</p>
<h3>Fonti e note sui dati</h3><ul class="dr-source-list">{source_items}</ul>
<p class="dr-more">Vuoi esplorare altri dati? <a href="../../confronta/abitare/">Tutti i dati sull’abitare</a> · <a href="../../stato-dati/">Stato dei dati</a> · <a href="../../segnala/">Segnala un errore</a></p>
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
    pages = []
    for key, make in DOSSIERS.items():
        dossier = make(engine)
        target = folder / dossier['slug'] / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(dossier, engine, dist, target, built), encoding='utf-8')
        write_csv(dossier, engine.names, target.parent / f'{dossier["slug"]}-dati.csv')
        if pdf:
            write_pdf(target, target.parent / f'{dossier["slug"]}-versilia.pdf')
        pages.append(target)
    return pages


if __name__ == '__main__':
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist'
    for page in build(dist):
        print('Dossier generato: ' + str(page))
