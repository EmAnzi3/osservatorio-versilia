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
APP_ICONS = ROOT / 'assets/app-parts/00.txt'
BASE_URL = 'https://osservatorioversilia.it/dossier/'
EXAMPLE_M2 = 80
SOURCE_NAMES = [
    # Le voci più specifiche prima: vince la prima che corrisponde.
    ('pnrrPerSitoWeb', 'Regione Toscana — Open data PNRR (dati del sistema di monitoraggio ReGiS)'),
    ('74533d22-b1c2-4d89-b1b9-b98e6c9713ff', 'SIOPE — Pagamenti dei Comuni (open data BDAP)'),
    ('manutenzione-del-reticolo-idrografico', 'Regione Toscana — Piani delle attività di bonifica'),
    ('cbtoscananord.it', 'Consorzio 1 Toscana Nord — Portale delle manutenzioni'),
    ('idrogeo.isprambiente.it', 'ISPRA — Piattaforma IdroGEO: pericolosità da alluvioni e frane'),
    ('dati.lamma.toscana.it', 'Consorzio LaMMA — Serie climatiche ricostruite (LaMMA ed ERA5-Land)'),
    ('indicatoriambientali.isprambiente.it/it/coste', 'ISPRA — Indicatori ambientali: coste'),
    ('arpat.toscana.it/pubblicazione/il-controllo-delle-acque-di-balneazione',
     'ARPAT — Controllo delle acque di balneazione'),
    ('bandierablu.org', 'FEE Italia — Bandiere Blu'),
    ('catasto-rifiuti.isprambiente.it/index.php?pg=findComune',
     'ISPRA — Catasto dei rifiuti: produzione e raccolta differenziata'),
    ('esploradati.istat.it', 'Istat — Censimento delle acque per uso civile'),
    ('sisbon.regione.toscana.it', 'Regione Toscana — Anagrafe dei siti oggetto di bonifica (SISBON)'),
    ('rt-oraritb', 'Regione Toscana — Orari del trasporto pubblico (GTFS di autobus e treni)'),
    ('MATPEN', 'Istat — Pendolarismo per lavoro, Censimento 2021'),
    ('DICA_ASIA', 'Istat — Registro delle unità locali delle imprese (ASIA)'),
    ('risultati-economici-delle-imprese', 'Istat — Risultati economici delle imprese sul territorio'),
    ('SDMXWS', 'Istat — Censimento permanente: occupazione e disoccupazione'),
    ('censimenti/popolazione-e-abitazioni', 'Istat — Censimento permanente: occupati che lavorano fuori Comune'),
    ('aci.gov.it', 'ACI — Autoritratto, parco veicolare'),
    ('piattaformaunicanazionale.it', 'Piattaforma Unica Nazionale dei punti di ricarica (MASE)'),
    ('geo.agcom.it', 'AGCOM — Mappa della banda larga'),
    ('percorsi/metodo', 'Osservatorio Versilia — Inventario dei percorsi pubblici'),
    ('PERMPOP/SUBCOM', 'Istat — Censimento permanente della popolazione e delle abitazioni'),
    ('Capacity', 'Istat — Capacità degli esercizi ricettivi'),
    ('capacita-degli-esercizi', 'Istat — Capacità degli esercizi ricettivi'),
    ('agenziaentrate.gov.it', 'Agenzia delle Entrate — Osservatorio del mercato immobiliare (OMI)'),
    ('nuova_addcomirpef', 'Ministero dell’Economia e delle Finanze — Addizionale comunale all’IRPEF'),
    ('nuova_at', 'Ministero dell’Economia e delle Finanze — Delibere e tariffe TARI dei Comuni'),
    ('finanze.gov.it', 'Ministero dell’Economia e delle Finanze — Dichiarazioni dei redditi su base comunale'),
    ('demo.istat.it', 'Istat — Popolazione residente e bilancio demografico'),
    ('ars.toscana.it', 'Agenzia regionale di sanità della Toscana (ARS)'),
    ('dati.salute.gov.it', 'Ministero della Salute — Anagrafe delle farmacie'),
    ('dati.toscana.it', 'Regione Toscana — Servizi educativi per la prima infanzia'),
    ('dati.istruzione.it', 'Ministero dell’Istruzione e del Merito — Open data della scuola'),
    ('invalsi', 'INVALSI — Risultati delle prove nazionali'),
    ('misura-comune', 'Istat — Spesa dei Comuni per i servizi sociali'),
    ('indicatori-comunali', 'Regione Toscana — Indicatori comunali per le politiche locali (Istat, ICT nelle PA locali)'),
    ('regione.toscana.it', 'Regione Toscana — Movimento turistico nelle strutture ricettive'),
    ('openbdap.rgs.mef.gov.it', 'Ragioneria Generale dello Stato — Rendiconti dei Comuni (OpenBDAP)'),
    ('bdap-opendata.rgs', 'Ragioneria Generale dello Stato — Rendiconti dei Comuni (open data BDAP)'),
    ('siope.it', 'SIOPE — Incassi e pagamenti delle amministrazioni pubbliche'),
    ('contoannuale.rgs', 'Ragioneria Generale dello Stato — Conto annuale del personale'),
    ('catasto-rifiuti', 'ISPRA — Catasto dei rifiuti: costi del servizio'),
    ('erplucca.it', 'ERP Lucca — Bilanci e rendiconti dell’edilizia residenziale pubblica'),
]
# Stesso indirizzo di fonte per letture diverse: il nome pubblico segue l'indicatore.
SOURCE_BY_METRIC = {'publicWorks': 'Ragioneria Generale dello Stato — Monitoraggio delle opere pubbliche (BDAP)'}
MONTHS = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre',
          'novembre', 'dicembre']
TENS = ['nessuna', 'una', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove']


# ---------------------------------------------------------------------------
# Formattazione italiana: al massimo due decimali, separatori it-IT.

def num(value: float, decimals: int = 0) -> str:
    text = f'{value:,.{decimals}f}'
    return text.replace(',', ' ').replace('.', ',').replace(' ', '.')


def money(value: float) -> str:
    """Euro con i centesimi solo quando ci sono: 144,50 ma 240."""
    return num(value, 2) if round(value, 2) != round(value) else num(round(value))


def pct(value: float, decimals: int = 1) -> str:
    return num(value, decimals) + '%'


def signed(value: float, decimals: int = 1) -> str:
    shown = round(value, decimals)
    return ('+' if shown > 0 else '−' if shown < 0 else '') + num(abs(shown), decimals)


def _elides(text: str) -> bool:
    """«otto», «undici», «ottanta»…: davanti a queste cifre l’articolo si apostrofa."""
    whole = text.split(',')[0].replace('.', '')
    return text.startswith('8') or whole in ('1', '11') or whole.startswith('11') and len(whole) in (4, 7)


def _zero(text: str) -> bool:
    return text.split(',')[0] == '0'


def il(text: str) -> str:
    return ('lo ' if _zero(text) else 'l’' if _elides(text) else 'il ') + text


def al(text: str) -> str:
    return ('allo ' if _zero(text) else 'all’' if _elides(text) else 'al ') + text


def del_(text: str) -> str:
    whole = text.split(',')[0].replace('.', '')
    if whole == '0':
        return 'dello ' + text
    return ('dell’' if _elides(text) or whole == '1' else 'del ') + text


def dal(text: str) -> str:
    return ('dallo ' if _zero(text) else 'dall’' if _elides(text) else 'dal ') + text


def sul(text: str) -> str:
    return ('sullo ' if _zero(text) else 'sull’' if _elides(text) else 'sul ') + text


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def slug(name: str) -> str:
    return re.sub(r'[^a-z]+', '-', name.lower()).strip('-')


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' e ' + names[-1]


def ordinal(rank: int) -> str:
    return f'{rank}°'


def measure_source(measure) -> str:
    return SOURCE_BY_METRIC.get(measure.metric) or source_name(measure.source)


def source_name(url: str) -> str:
    for pattern, name in SOURCE_NAMES:
        if pattern in url:
            return name
    raise ValueError('fonte_senza_nome_pubblico:' + url)


# ---------------------------------------------------------------------------
# Icone e colori dei temi: gli stessi tracciati e la stessa palette del sito.

# Il turismo nel sito sta dentro «Economia»: colore del tema, icona propria.
EXTRA_ICONS = {'turismo': '<path d="M22 12a10.06 10.06 1 0 0-20 0Z"></path><path d="M12 12v8a2 2 0 0 0 4 0"></path>'
                          '<path d="M12 2v1"></path>'}


def theme_icons() -> dict[str, str]:
    """Tracciati SVG di themeSvgPaths, letti dal runtime del sito per non duplicarli."""
    block = APP_ICONS.read_text(encoding='utf-8').split('const themeSvgPaths = {', 1)[1].split('\n  };', 1)[0]
    icons = {k: v.replace('\\"', '"') for k, v in re.findall(r"^\s*(\w+): '(.*)',?$", block, re.M)}
    if len(icons) < 11:
        raise ValueError('icone_tema_non_trovate')
    return icons


def dossier_icon(dossier: dict, size: int = 26) -> str:
    paths = EXTRA_ICONS.get(dossier['slug']) or theme_icons()[dossier['theme']]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true" focusable="false">{paths}</svg>')


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
        return {'eur': lambda v: num(v) + ' €', 'eurc': lambda v: money(v) + ' €', 'eurm2': lambda v: num(v) + ' €/m²',
                'eurm2month': lambda v: num(v, 2) + ' €/m² al mese', 'percent': lambda v: pct(v, self.decimals),
                'per1000': lambda v: num(v) + ' ogni 1.000 abitanti', 'decimal': lambda v: num(v, self.decimals),
                'change': lambda v: signed(v) + '%', 'points': lambda v: num(v, 1) + ' punti',
                'per1000s': lambda v: signed(v, self.decimals) + ' ogni 1.000 abitanti', 'count': lambda v: num(v),
                'nights': lambda v: num(v, 2) + ' notti', 'per100': lambda v: num(v, 1) + ' ogni 100',
                'years': lambda v: num(v, 1) + ' anni', 'hours': lambda v: num(v, 1) + ' ore',
                'rate1000': lambda v: num(v, self.decimals) + ' ogni 1.000 abitanti',
                'per1000old': lambda v: num(v, 1) + ' ogni 1.000 anziani',
                'celsius': lambda v: num(v, 1) + ' °C', 'celsiusdelta': lambda v: signed(v, 1) + ' °C',
                'mm': lambda v: num(v) + ' mm', 'kg': lambda v: num(v) + ' kg'}[self.unit](value)

    def short(self, value: float) -> str:
        return {'eurm2month': lambda v: num(v, 2) + ' €', 'per1000': lambda v: num(v), 'per1000s': lambda v: signed(v, self.decimals), 'per100': lambda v: num(v, 1),
                'years': lambda v: num(v, 1), 'hours': lambda v: num(v, 1), 'rate1000': lambda v: num(v, self.decimals), 'per1000old': lambda v: num(v, 1),
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
    day = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', period)
    if day:
        return f'{int(day.group(3))} {MONTHS[int(day.group(2)) - 1]} {day.group(1)}'
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


# ---------------------------------------------------------------------------
# Dossier «Muoversi in Versilia».

def mobilita(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    TI = ('tuscany', 'italy')
    m = {
        'outside': engine.measure('outside', 'outsideMunicipality', 'total',
                                  'Occupati residenti che lavorano in un altro Comune, %', 'percent', 1),
        'outbound': engine.measure('outbound', 'outboundCommutersRate', 'total',
                                   'Residenti che escono dal Comune per lavorare, ogni 1.000 abitanti', 'per1000', 0,
                                   benchmarks=TI, versilia=True),
        'inbound': engine.measure('inbound', 'inboundCommutersRate', 'total',
                                  'Lavoratori che entrano da altri Comuni, ogni 1.000 abitanti', 'per1000', 0,
                                  benchmarks=TI, versilia=True),
        'trips': engine.measure('trips', 'scheduledTplTripsPer1000', 'view:normalized',
                                'Corse programmate di autobus e treni, ogni 1.000 abitanti', 'rate1000', 1),
        'span': engine.measure('span', 'tplServiceSpan', 'total',
                               'Ore fra la prima e l’ultima partenza programmata', 'hours', 1),
        'stops': engine.measure('stops', 'activeTplAccessPoints', 'view:normalized',
                                'Punti di fermata serviti, ogni 1.000 abitanti', 'rate1000', 1),
        'cars': engine.measure('cars', 'motorization', 'total', 'Automobili ogni 1.000 abitanti', 'per1000', 0,
                               benchmarks=TI),
        'old_cars': engine.measure('old_cars', 'pollutingCars', 'total',
                                   'Automobili delle classi più inquinanti (Euro 0-3), %', 'percent', 1, benchmarks=TI),
        'ev': engine.measure('ev', 'evPoints', 'total', 'Punti di ricarica pubblici per auto elettriche, ogni 1.000 abitanti',
                             'rate1000', 2),
        'ftth': engine.measure('ftth', 'ftthCoverageDesi', 'total',
                               'Famiglie raggiunte dalla fibra fino all’edificio, %', 'percent', 1, benchmarks=TI),
        'routes': engine.measure('routes', 'slowMobilityRoutes', 'total',
                                 'Sentieri, cammini e percorsi in bici che attraversano il Comune', 'count', 0),
        'bike': engine.measure('bike', 'slowMobilityBici', 'total', 'Percorsi in bici che attraversano il Comune',
                               'count', 0),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]

    # 01 — pendolari
    out, outb, inb = m['outside'], m['outbound'], m['inbound']
    majority = [c for c, v, _ in out.ranking if v > 50]
    out_text = (
        f'Nel {out.period} lavorava fuori dal proprio Comune una quota di occupati che va '
        f'{dal(pct(lo("outside")[1]))} di {nm(lo("outside")[0])} {al(pct(hi("outside")[1]))} di <b>{nm(hi("outside")[0])}</b>'
        + (f': a {join_names([nm(c) for c in majority])} più di metà dei lavoratori si sposta ogni giorno in un altro '
           f'Comune.' if majority else '.'))
    flow_text = (
        f'In rapporto alla popolazione, in Versilia escono per lavoro <b>{num(outb.versilia)} residenti ogni 1.000 '
        f'abitanti</b> ({num(outb.benchmarks["tuscany"])} in Toscana) e ne entrano {num(inb.versilia)} da altri Comuni '
        f'({num(inb.benchmarks["tuscany"])} in Toscana). Il Comune che attira più lavoratori da fuori è '
        f'<b>{nm(hi("inbound")[0])}</b>, con {num(hi("inbound")[1])} ingressi ogni 1.000 abitanti; quello da cui si '
        f'esce di più è {nm(hi("outbound")[0])}, con {num(hi("outbound")[1])}.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(out.values[c]))} degli occupati residenti lavora in un altro Comune; '
                  f'ogni 1.000 abitanti escono {num(outb.values[c])} lavoratori e ne entrano {num(inb.values[c])}.')
              for c in codes}
    ch1 = chapter(1, 'pendolari', 'Chi parte e chi arriva', 'Quante persone si spostano ogni giorno per lavorare?',
        f'<p>{out_text}</p>{bar_chart(out, N, "Occupati che lavorano fuori dal proprio Comune")}'
        f'<p>{flow_text}</p>{bar_chart(outb, N, "Residenti che escono per lavorare")}'
        f'{bar_chart(inb, N, "Lavoratori che entrano da altri Comuni")}'
        '<p>Il saldo fra chi entra e chi esce e quanto lavoro resta dentro ogni Comune sono nel dossier '
        '<a href="../lavoro/#pendolari">Lavorare in Versilia</a>.</p>' + town_blocks(towns1),
        'Gli spostamenti per lavoro decidono gli orari del traffico, la domanda di autobus e treni e quanto tempo le '
        'famiglie passano in viaggio. Il censimento conta solo chi va al lavoro, non studenti, turisti o chi si sposta '
        'per fare la spesa o per curarsi; e i flussi sono di qualche anno fa, rapportati alla popolazione di oggi.')

    # 02 — trasporto pubblico
    trp, spn = m['trips'], m['span']
    long_day = [c for c, v, _ in spn.ranking if v >= 22]
    short_day = sorted((c for c in codes if c not in long_day), key=lambda c: spn.values[c])
    trp_text = (
        f'Nel giorno feriale d’estate preso come riferimento ({period_label(trp.period)}) gli orari ufficiali '
        f'prevedevano da <b>{num(lo("trips")[1], 1)} corse di autobus e treni ogni 1.000 abitanti</b> a '
        f'{nm(lo("trips")[0])} a {num(hi("trips")[1], 1)} a {nm(hi("trips")[0])}.')
    spn_text = (
        (f'Il servizio copre quasi tutta la giornata, 22 ore o più fra la prima e l’ultima partenza, a '
         f'{join_names([nm(c) for c in long_day])}' if long_day else 'Nessun Comune ha corse lungo tutta la giornata')
        + (f'; a {join_names([nm(c) for c in short_day])} la giornata si ferma prima, con '
           + ', '.join(f'{num(spn.values[c], 1)} ore a {nm(c)}' for c in short_day) + '.' if short_day else '.'))
    stops = m['stops']
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: {num(trp.values[c], 1)} corse ogni 1.000 abitanti, {num(spn.values[c], 1)} '
                  f'ore fra la prima e l’ultima partenza, {num(stops.values[c], 1)} punti di fermata ogni 1.000 abitanti.')
              for c in codes}
    ch2 = chapter(2, 'trasporto-pubblico', 'Autobus e treni', 'Quante corse passano e per quante ore al giorno?',
        f'<p>{trp_text}</p>{bar_chart(trp, N, "Corse di autobus e treni programmate", "Una corsa conta per ogni Comune in cui ferma: un treno che attraversa la Versilia vale per ciascuno dei Comuni serviti.")}'
        f'<p>{spn_text}</p>{bar_chart(spn, N, "Durata della giornata di servizio")}'
        f'{bar_chart(stops, N, "Punti di fermata serviti")}' + town_blocks(towns2),
        'Sono gli orari programmati di un solo giorno feriale d’estate, non il servizio di tutto l’anno, i ritardi o i '
        'passeggeri. Molte corse sono in poche ore, per cui una giornata lunga non vuol dire autobus frequenti; e una '
        'fermata nell’elenco ufficiale non dice quanto sia comoda da raggiungere a piedi.')

    # 03 — automobili
    car, old = m['cars'], m['old_cars']
    old_above = [c for c in codes if old.values[c] > old.benchmarks['tuscany']]
    car_text = (
        f'Nel {car.period} si va da {num(lo("cars")[1])} automobili ogni 1.000 abitanti a {nm(lo("cars")[0])} a '
        f'<b>{num(hi("cars")[1])} a {nm(hi("cars")[0])}</b>, contro {num(car.benchmarks["tuscany"])} in Toscana e '
        f'{num(car.benchmarks["italy"])} in Italia.')
    old_text = (
        f'Le automobili delle classi più vecchie e inquinanti, da Euro 0 a Euro 3, sono '
        f'{dal(pct(lo("old_cars")[1]))} di {nm(lo("old_cars")[0])} {al(pct(hi("old_cars")[1]))} di {nm(hi("old_cars")[0])}: '
        f'sopra la media toscana ({pct(old.benchmarks["tuscany"])}) in {count_words(len(old_above), total)}, mentre in '
        f'Italia sono {il(pct(old.benchmarks["italy"]))}.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: {num(car.values[c])} automobili ogni 1.000 abitanti; '
                  f'{il(pct(old.values[c]))} è di classe Euro 0-3.') for c in codes}
    ch3 = chapter(3, 'automobili', 'Le automobili', 'Quante auto ci sono e quanto sono vecchie?',
        f'<p>{car_text}</p>{bar_chart(car, N, "Automobili ogni 1.000 abitanti")}'
        f'<p>{old_text}</p>{bar_chart(old, N, "Automobili Euro 0-3")}' + town_blocks(towns3),
        'Tante auto per abitante indicano spesso che, per spostarsi, alternative comode non ci sono. Le auto più vecchie '
        'inquinano di più e rischiano limitazioni alla circolazione. I veicoli sono contati dove è residente il '
        'proprietario: le auto aziendali e a noleggio possono risultare intestate altrove.')

    # 04 — ricarica elettrica
    ev = m['ev']
    ev_text = (
        f'Nel {ev.period} i punti di ricarica pubblici per auto elettriche vanno da {num(lo("ev")[1], 2)} ogni 1.000 '
        f'abitanti a {nm(lo("ev")[0])} a <b>{num(hi("ev")[1], 2)} a {nm(hi("ev")[0])}</b>.')
    towns4 = {c: f'<b>{esc(nm(c))}</b>: {num(ev.values[c], 2)} punti di ricarica pubblici ogni 1.000 abitanti.'
              for c in codes}
    ch4 = chapter(4, 'ricarica', 'Ricarica elettrica', 'Dove si può ricaricare un’auto elettrica?',
        f'<p>{ev_text}</p>{bar_chart(ev, N, "Punti di ricarica pubblici")}' + town_blocks(towns4),
        'Chi non ha un garage dipende dalle colonnine pubbliche per passare all’elettrico. Il dato conta i punti attivi '
        'registrati nella piattaforma nazionale, non la loro potenza né quanto sono usati; nei Comuni turistici le '
        'colonnine servono anche i visitatori, non solo i residenti.')

    # 05 — fibra
    ft = m['ftth']
    ft_below = [c for c in codes if ft.values[c] < ft.benchmarks['tuscany']]
    ft_none = [c for c in codes if ft.values[c] < 1]
    ft_text = (
        f'Secondo AGCOM, {al(period_label(ft.period))} la fibra fino all’edificio raggiungeva {il(pct(hi("ftth")[1]))} '
        f'delle famiglie a <b>{nm(hi("ftth")[0])}</b>'
        + (f', ma quasi nessuna a {join_names([nm(c) for c in ft_none])}' if ft_none else
           f' e {il(pct(lo("ftth")[1]))} a {nm(lo("ftth")[0])}')
        + f'. In Toscana la quota è {il(pct(ft.benchmarks["tuscany"]))}, in Italia {il(pct(ft.benchmarks["italy"]))}: '
          f'sono sotto la media toscana {count_words(len(ft_below), total)}.')
    towns5 = {c: f'<b>{esc(nm(c))}</b>: {il(pct(ft.values[c]))} delle famiglie è raggiunto dalla fibra fino all’edificio '
                 f'(Toscana {pct(ft.benchmarks["tuscany"])}).' for c in codes}
    ch5 = chapter(5, 'fibra', 'Internet veloce', 'Quante famiglie possono avere la fibra fino a casa?',
        f'<p>{ft_text}</p>{bar_chart(ft, N, "Famiglie raggiunte dalla fibra fino all’edificio")}' + town_blocks(towns5),
        'Una buona connessione permette di lavorare e studiare da casa, e quindi di spostarsi meno. Il dato dice dove la '
        'rete è disponibile secondo gli operatori, non quante famiglie l’hanno attivata né la velocità reale; dove la '
        'fibra non arriva all’edificio ci possono essere altre tecnologie, più lente.')

    # 06 — percorsi
    rt, bk = m['routes'], m['bike']
    rt_text = (
        f'L’inventario dei percorsi pubblici verificati conta da {num(lo("routes")[1])} sentieri, cammini e percorsi in '
        f'bici che attraversano {nm(lo("routes")[0])} a <b>{num(hi("routes")[1])} a {nm(hi("routes")[0])}</b>; '
        f'quelli in bici sono da {num(lo("bike")[1])} a {num(hi("bike")[1])} per Comune. Uno stesso percorso può '
        f'attraversare più Comuni, perciò i numeri non si sommano.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: {num(rt.values[c])} percorsi pubblici attraversano il Comune, di cui '
                  f'{num(bk.values[c])} in bici.') for c in codes}
    ch6 = chapter(6, 'percorsi', 'A piedi e in bici', 'Quanti percorsi ci sono per camminare e pedalare?',
        f'<p>{rt_text}</p>{bar_chart(rt, N, "Percorsi pubblici che attraversano il Comune")}'
        f'{bar_chart(bk, N, "Percorsi in bici")}' + town_blocks(towns6),
        'Sentieri e ciclovie servono al tempo libero e al turismo, e in parte anche agli spostamenti di tutti i giorni. '
        'L’inventario conta i percorsi, non i chilometri, e non dice se sono sicuri, illuminati o adatti a chi va al '
        'lavoro o a scuola.')

    key_points = [
        (num(outb.versilia), f'Residenti che escono dal Comune per lavorare, ogni 1.000 abitanti della Versilia. In '
                             f'Toscana {num(outb.benchmarks["tuscany"])}.', 'pendolari'),
        (num(hi('inbound')[1]), f'Lavoratori che entrano ogni 1.000 abitanti a {nm(hi("inbound")[0])}, il Comune che ne '
                                f'attira di più.', 'pendolari'),
        (f'{num(lo("trips")[1], 1)}–{num(hi("trips")[1], 1)}',
         f'Corse di autobus e treni ogni 1.000 abitanti in un giorno feriale d’estate, da {nm(lo("trips")[0])} a '
         f'{nm(hi("trips")[0])}.', 'trasporto-pubblico'),
        (num(hi('cars')[1]), f'Automobili ogni 1.000 abitanti a {nm(hi("cars")[0])}, il valore più alto. In Toscana '
                             f'{num(car.benchmarks["tuscany"])}.', 'automobili'),
        (num(hi('ev')[1], 2), f'Punti di ricarica pubblici ogni 1.000 abitanti a {nm(hi("ev")[0])}; negli altri Comuni '
                              f'al massimo {num(m["ev"].ranking[1][1], 2)}.', 'ricarica'),
        (f'{len(ft_below)} su {total}', f'Comuni con la fibra fino all’edificio sotto la media toscana '
                                        f'({pct(ft.benchmarks["tuscany"])} delle famiglie).', 'fibra'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Occupati che lavorano fuori Comune', pct(out.values[c]), f'{ordinal(out.rank(c))} su 7'),
        summary_item('Lavoratori in entrata ogni 1.000 abitanti', num(inb.values[c]), f'Toscana {num(inb.benchmarks["tuscany"])}'),
        summary_item('Corse di autobus e treni ogni 1.000 abitanti', num(trp.values[c], 1), f'{ordinal(trp.rank(c))} su 7'),
        summary_item('Automobili ogni 1.000 abitanti', num(car.values[c]), f'Toscana {num(car.benchmarks["tuscany"])}'),
        summary_item('Automobili Euro 0-3', pct(old.values[c]), f'Toscana {pct(old.benchmarks["tuscany"])}'),
        summary_item('Punti di ricarica ogni 1.000 abitanti', num(ev.values[c], 2), f'{ordinal(ev.rank(c))} su 7'),
        summary_item('Famiglie raggiunte dalla fibra', pct(ft.values[c]), f'Toscana {pct(ft.benchmarks["tuscany"])}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quante persone usano davvero autobus e treni: gli orari dicono quante corse ci sono, non quanti passeggeri.',
        'Come si spostano studenti, anziani e turisti: i dati sul pendolarismo riguardano solo chi va al lavoro.',
        'Quanto traffico c’è d’estate e quanto tempo si perde in coda.',
        'Quanti chilometri di piste ciclabili ci sono in ogni Comune e in che stato sono.',
        'Quanto spendono le famiglie per muoversi, fra carburante, abbonamenti e manutenzione dell’auto.',
        'Quante famiglie hanno attivato la fibra e a che velocità navigano davvero.',
    ]
    return dict(
        slug='mobilita', title='Muoversi in Versilia', eyebrow='Dossier · Mobilità e collegamenti',
        unknown_topic='sulla mobilità', theme='mobilita', theme_label='Tutti i dati sulla mobilità',
        lead='Pendolari, autobus e treni, automobili, ricarica elettrica, fibra e percorsi a piedi e in bici: una lettura '
             'dei dati pubblici sui sette Comuni della Versilia.',
        description='Pendolarismo per lavoro, corse di autobus e treni, automobili, punti di ricarica, copertura in fibra e '
                    'percorsi a piedi e in bici nei sette Comuni della Versilia, con confronti con Toscana e Italia.',
        periods=f'Pendolarismo {out.period}, orari del trasporto pubblico {period_label(trp.period)}, automobili '
                f'{car.period}, punti di ricarica {ev.period}, fibra {period_label(ft.period)}, percorsi '
                f'{period_label(rt.period)}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('pendolari', 'Chi parte e chi arriva'), ('trasporto-pubblico', 'Autobus e treni'),
             ('automobili', 'Le automobili'), ('ricarica', 'Ricarica elettrica'), ('fibra', 'Internet veloce'),
             ('percorsi', 'A piedi e in bici')])


def bilanci(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    eur = lambda key, metric, label, dimension='total': engine.measure(key, metric, dimension, label, 'eur', 0,
                                                                         versilia=True)
    m = {
        'revenue': eur('revenue', 'currentRevenueAccruedPerResident', 'Entrate correnti accertate per residente'),
        'own': engine.measure('own', 'ownRevenueShare', 'total', 'Entrate proprie sul totale delle entrate correnti, %',
                              'percent', 1, versilia=True),
        'collect': engine.measure('collect', 'currentCollectionCapacity', 'total',
                                  'Entrate correnti incassate sul totale accertato, %', 'percent', 1, versilia=True),
        'spend': eur('spend', 'currentExpenditureCommittedPerResident', 'Spesa corrente impegnata per residente'),
        'social': eur('social', 'socialMissionExpenditurePerResident',
                      'Spesa per diritti sociali e famiglie, per residente'),
        'school': eur('school', 'educationMissionExpenditurePerResident',
                      'Spesa per istruzione e diritto allo studio, per residente'),
        'capital': eur('capital', 'capitalExpenditureCommittedPerResident',
                       'Spesa per investimenti impegnata per residente'),
        'capay': eur('capay', 'capitalPayments', 'Pagamenti per investimenti, per residente'),
        'result': eur('result', 'availableAdministrationResultPerResident',
                      'Parte disponibile del risultato di amministrazione, per residente'),
        'rigid': engine.measure('rigid', 'rigidExpenditureShare', 'total',
                                'Spese rigide (personale, debito, disavanzo) sulle entrate correnti, %', 'percent', 1),
        'paycap': engine.measure('paycap', 'currentPaymentCapacity', 'total',
                                 'Spesa corrente pagata sul totale impegnato, %', 'percent', 1, versilia=True),
        'debt': eur('debt', 'financialDebtProfile', 'Debito per mutui e prestiti, per residente', 'part:debtPerResident'),
        'interest': engine.measure('interest', 'financialDebtProfile', 'part:interestShare',
                                   'Interessi sul debito, % delle entrate correnti', 'percent', 1, versilia=True),
        'irpef': engine.measure('irpef', 'municipalIrpef', 'income:30000',
                                'Addizionale comunale IRPEF su un reddito imponibile di 30.000 €', 'eurc', 0),
        'tari': engine.measure('tari', 'tariStandardHousehold', 'total',
                               'TARI annua per una famiglia di 3 persone in 100 m²', 'eur', 0),
        'waste': engine.measure('waste', 'wasteServiceCost', 'total',
                                'Costo del servizio rifiuti per abitante', 'eur', 0, benchmarks=('tuscany',)),
        'staff': engine.measure('staff', 'municipalEmployeesPer1000', 'total',
                                'Dipendenti comunali ogni 1.000 abitanti', 'rate1000', 1, benchmarks=('tuscany',),
                                versilia=True),
        'staff55': engine.measure('staff55', 'municipalStaffAgeStructure', 'age:age55plus',
                                  'Dipendenti comunali con 55 anni o più, %', 'percent', 1, versilia=True),
        'online': engine.measure('online', 'municipalOnlineServicesAdvanced', 'total',
                                 'Servizi comunali completamente online, %', 'percent', 1, benchmarks=('tuscany',)),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    second = lambda k: m[k].ranking[1]
    nm = lambda code: N[code]
    euro = lambda v: num(v) + ' euro'
    cents = lambda v: money(v) + ' euro'

    # 01 — entrate
    rev, own, col = m['revenue'], m['own'], m['collect']
    rev_text = (
        f'Nel rendiconto {rev.period} i Comuni della Versilia hanno accertato in media <b>{euro(rev.versilia)} di entrate '
        f'correnti per residente</b>: tributi, trasferimenti ed entrate extratributarie come multe, canoni e tariffe. Si '
        f'va da {euro(lo("revenue")[1])} di {nm(lo("revenue")[0])} a {euro(hi("revenue")[1])} di '
        f'<b>{nm(hi("revenue")[0])}</b>; dopo {nm(hi("revenue")[0])} viene {nm(second("revenue")[0])} con '
        f'{euro(second("revenue")[1])}.')
    own_text = (
        f'Le entrate proprie (tributi ed extratributarie) sono {il(pct(own.versilia))} del totale in Versilia: '
        f'{dal(pct(lo("own")[1]))} di {nm(lo("own")[0])}, che dipende di più dai trasferimenti, '
        f'{al(pct(hi("own")[1]))} di {nm(hi("own")[0])}. Delle entrate correnti accertate, nello stesso anno i Comuni '
        f'ne hanno incassate {il(pct(col.versilia))}: {dal(pct(lo("collect")[1]))} di {nm(lo("collect")[0])} '
        f'{al(pct(hi("collect")[1]))} di {nm(hi("collect")[0])}.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {euro(rev.values[c])} di entrate correnti per residente, '
                  f'{il(pct(own.values[c]))} proprie; incassato nell’anno {il(pct(col.values[c]))} di quanto accertato.')
              for c in codes}
    ch1 = chapter(1, 'entrate', 'Quanto entra', 'Quante risorse ha ogni Comune e da dove arrivano?',
        f'<p>{rev_text}</p>{bar_chart(rev, N, "Entrate correnti per residente")}'
        f'<p>{own_text}</p>{bar_chart(own, N, "Quota delle entrate proprie")}'
        f'{bar_chart(col, N, "Entrate correnti incassate nell’anno")}' + town_blocks(towns1),
        'Le entrate correnti pagano i servizi di tutti i giorni. Sono divise per i residenti, ma nei Comuni turistici '
        'le pagano e le usano anche proprietari di seconde case, imprese e visitatori: per questo i valori per '
        'residente dei Comuni della costa possono risultare molto alti. Accertare un’entrata vuol dire averne diritto, '
        'non averla già incassata.')

    # 02 — spesa corrente e servizi
    sp, so, sc = m['spend'], m['social'], m['school']
    sp_text = (
        f'La spesa corrente impegnata, cioè quella per far funzionare servizi e uffici, è stata in media di '
        f'<b>{euro(sp.versilia)} per residente</b>, da {euro(lo("spend")[1])} di {nm(lo("spend")[0])} '
        f'a {euro(hi("spend")[1])} di {nm(hi("spend")[0])}.')
    so_text = (
        f'Per i servizi sociali e le famiglie, compresi asili nido e assistenza agli anziani, i Comuni hanno impegnato '
        f'{euro(so.versilia)} per residente: il valore più alto è a {nm(hi("social")[0])} ({euro(hi("social")[1])}), '
        f'il più basso a {nm(lo("social")[0])} ({euro(lo("social")[1])}). Per scuola e diritto allo studio, mense e '
        f'trasporto scolastico compresi, la media è {euro(sc.versilia)}, da {euro(lo("school")[1])} a '
        f'{nm(lo("school")[0])} a {euro(hi("school")[1])} a {nm(hi("school")[0])}.')
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: spesa corrente {euro(sp.values[c])} per residente, di cui '
                  f'{euro(so.values[c])} per sociale e famiglie e {euro(sc.values[c])} per scuola e diritto allo studio.')
              for c in codes}
    ch2 = chapter(2, 'spesa', 'Dove vanno i soldi', 'Quanto spendono i Comuni per i servizi?',
        f'<p>{sp_text}</p>{bar_chart(sp, N, "Spesa corrente per residente")}'
        f'<p>{so_text}</p>{bar_chart(so, N, "Spesa per sociale e famiglie")}'
        f'{bar_chart(sc, N, "Spesa per istruzione e diritto allo studio")}' + town_blocks(towns2),
        'Spendere di più non vuol dire per forza offrire servizi migliori, né spendere di meno essere più efficienti: '
        'contano quanti utenti ci sono, come è organizzato il servizio e se è gestito da un altro ente, come '
        'un’unione dei Comuni o un’azienda sanitaria. I dati dicono quanto è stato impegnato, non che cosa hanno '
        'ricevuto i cittadini.')

    # 03 — investimenti
    cp, py = m['capital'], m['capay']
    cp_text = (
        f'Per opere e investimenti (strade, scuole, edifici, verde) i Comuni hanno impegnato in media '
        f'<b>{euro(cp.versilia)} per residente</b>, da {euro(lo("capital")[1])} di {nm(lo("capital")[0])} '
        f'a {euro(hi("capital")[1])} di {nm(hi("capital")[0])}. I pagamenti effettivi per investimenti '
        f'registrati nell’anno sono stati {euro(py.versilia)} per residente.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: {euro(cp.values[c])} per residente impegnati per investimenti, '
                  f'{euro(py.values[c])} pagati nell’anno.') for c in codes}
    ch3 = chapter(3, 'investimenti', 'Gli investimenti', 'Quanto investono i Comuni in opere pubbliche?',
        f'<p>{cp_text}</p>{bar_chart(cp, N, "Investimenti impegnati per residente")}'
        f'{bar_chart(py, N, "Investimenti pagati per residente")}' + town_blocks(towns3),
        'Gli investimenti cambiano molto da un anno all’altro: basta una grande opera, o un finanziamento del PNRR, per '
        'far salire il valore di un Comune. Impegni e pagamenti non coincidono, perché un cantiere si paga a stati di '
        'avanzamento, anche negli anni successivi.')

    # 04 — equilibrio dei conti
    rs, rg, pc = m['result'], m['rigid'], m['paycap']
    deficit = [c for c, v, _ in rs.ranking if v < 0]
    rs_text = (
        f'Alla chiusura dei conti, la parte del risultato di amministrazione libera da vincoli era in media di '
        f'{euro(rs.versilia)} per residente. '
        + (f'A {join_names([nm(c) for c in deficit])} era negativa: un disavanzo che il Comune deve recuperare negli '
           f'anni successivi.' if deficit else 'In nessun Comune era negativa.'))
    rg_text = (
        f'Le spese rigide, cioè personale, rate dei prestiti ed eventuale recupero del disavanzo, assorbivano '
        f'{dal(pct(lo("rigid")[1]))} delle entrate correnti a {nm(lo("rigid")[0])} '
        f'{al(pct(hi("rigid")[1]))} a <b>{nm(hi("rigid")[0])}</b>. Della spesa corrente impegnata, i Comuni ne hanno '
        f'pagata nell’anno {il(pct(pc.versilia))}, {dal(pct(lo("paycap")[1]))} di {nm(lo("paycap")[0])} '
        f'{al(pct(hi("paycap")[1]))} di {nm(hi("paycap")[0])}.')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: parte disponibile del risultato {euro(rs.values[c])} per residente; spese '
                  f'rigide {il(pct(rg.values[c]))} delle entrate correnti; pagato nell’anno {il(pct(pc.values[c]))} '
                  f'della spesa corrente.') for c in codes}
    ch4 = chapter(4, 'equilibrio', 'I conti in ordine', 'Quanto margine hanno i bilanci comunali?',
        f'<p>{rs_text}</p>{bar_chart(rs, N, "Parte disponibile del risultato di amministrazione")}'
        f'<p>{rg_text}</p>{bar_chart(rg, N, "Spese rigide sulle entrate correnti")}' + town_blocks(towns4),
        'Un risultato disponibile positivo può essere usato, con molte regole, per nuove spese; uno negativo obbliga a '
        'rientrare. Più alte sono le spese rigide, meno spazio resta per scegliere. Sono indicatori del bilancio, non '
        'un giudizio sulla gestione, e non dicono quanto il Comune potrà spendere davvero l’anno dopo.')

    # 05 — debito
    db, it = m['debt'], m['interest']
    no_debt = [c for c in codes if db.values[c] == 0]
    db_text = (
        f'Alla fine del {db.period} il debito per mutui e prestiti era in media di <b>{euro(db.versilia)} per '
        f'residente</b>. I più indebitati sono {nm(hi("debt")[0])}, con {euro(hi("debt")[1])}, e '
        f'{nm(second("debt")[0])}, con {euro(second("debt")[1])}'
        + (f'; {join_names([nm(c) for c in no_debt])} non ha debiti di questo tipo.' if len(no_debt) == 1 else
           f'; {join_names([nm(c) for c in no_debt])} non hanno debiti di questo tipo.' if no_debt else '.'))
    it_text = (
        f'Gli interessi pagati sui prestiti valgono in media {il(pct(it.versilia))} delle entrate correnti, fino '
        f'{al(pct(hi("interest")[1]))} di {nm(hi("interest")[0])}.')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: debito per mutui e prestiti {euro(db.values[c])} per residente; interessi '
                  f'{il(pct(it.values[c]))} delle entrate correnti.') for c in codes}
    ch5 = chapter(5, 'debito', 'Il debito', 'Quanto pesano mutui e prestiti?',
        f'<p>{db_text}</p>{bar_chart(db, N, "Debito per mutui e prestiti, per residente")}'
        f'<p>{it_text}</p>{bar_chart(it, N, "Interessi sulle entrate correnti")}' + town_blocks(towns5),
        'I Comuni possono indebitarsi solo per investire, e ogni rata toglie risorse ai servizi degli anni successivi. '
        'Il dato conta i prestiti, non tutti gli altri debiti verso fornitori; per Massarosa non comprende le passività '
        'del dissesto del 2019, gestite fuori dal bilancio ordinario.')

    # 06 — tasse e tariffe
    ir, ta, ws = m['irpef'], m['tari'], m['waste']
    ir_text = (
        f'Con un reddito imponibile di 30.000 euro, l’addizionale comunale IRPEF del {ir.period} va da '
        f'{cents(lo("irpef")[1])} a {nm(lo("irpef")[0])} a <b>{cents(hi("irpef")[1])} a '
        f'{join_names([nm(c) for c, v, _ in ir.ranking if v == hi("irpef")[1]])}</b>.')
    ta_text = (
        f'La TARI per una stessa famiglia di tre persone in una casa di 100 m², senza riduzioni, va da '
        f'{euro(lo("tari")[1])} a {nm(lo("tari")[0])} a <b>{euro(hi("tari")[1])} a {nm(hi("tari")[0])}</b>. Il costo '
        f'complessivo del servizio rifiuti nel {ws.period} va da {euro(lo("waste")[1])} per abitante a '
        f'{nm(lo("waste")[0])} a {euro(hi("waste")[1])} a {nm(hi("waste")[0])}, contro {euro(ws.benchmarks["tuscany"])} '
        f'nei Comuni toscani.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: addizionale IRPEF {cents(ir.values[c])} su 30.000 euro di reddito; TARI '
                  f'{euro(ta.values[c])} per 3 persone in 100 m²; servizio rifiuti {euro(ws.values[c])} per abitante.')
              for c in codes}
    ch6 = chapter(6, 'tasse', 'Tasse e tariffe', 'Quanto chiede il Comune a una famiglia tipo?',
        f'<p>{ir_text}</p>{bar_chart(ir, N, "Addizionale comunale IRPEF su 30.000 € di reddito")}'
        f'<p>{ta_text}</p>{bar_chart(ta, N, "TARI di una famiglia di 3 persone in 100 m²")}'
        f'{bar_chart(ws, N, "Costo del servizio rifiuti per abitante")}' + town_blocks(towns6),
        'Sono casi tipo, utili per confrontare le scelte dei Comuni, non il conto di una famiglia reale: esenzioni, '
        'riduzioni e situazioni personali cambiano l’importo. Il costo del servizio rifiuti per abitante è più alto '
        'dove ci sono molti turisti e seconde case, perché i rifiuti prodotti da chi non è residente vengono divisi '
        'per i soli residenti.')

    # 07 — personale e servizi online
    st, s55, on = m['staff'], m['staff55'], m['online']
    on_below = [c for c in codes if on.values[c] < on.benchmarks['tuscany']]
    st_text = (
        f'Nel {st.period} lavoravano nei Comuni della Versilia <b>{num(st.versilia, 1)} dipendenti ogni 1.000 '
        f'abitanti</b> (in Toscana {num(st.benchmarks["tuscany"], 1)}), da {num(lo("staff")[1], 1)} di '
        f'{nm(lo("staff")[0])} a {num(hi("staff")[1], 1)} di {nm(hi("staff")[0])}. Ha 55 anni o più '
        f'{il(pct(s55.versilia))} del personale, fino {al(pct(hi("staff55")[1]))} di {nm(hi("staff55")[0])}.')
    on_text = (
        f'Secondo l’ultima rilevazione Istat ({on.period}), i servizi che si possono chiedere e completare online '
        f'andavano {dal(pct(lo("online")[1]))} di {nm(lo("online")[0])} {al(pct(hi("online")[1]))} di '
        f'<b>{nm(hi("online")[0])}</b>; in Toscana la media era {il(pct(on.benchmarks["tuscany"]))}'
        + (f', e sotto questa media c’erano {join_names([nm(c) for c in on_below])}.' if on_below else '.'))
    towns7 = {c: (f'<b>{esc(nm(c))}</b>: {num(st.values[c], 1)} dipendenti comunali ogni 1.000 abitanti, '
                  f'{il(pct(s55.values[c]))} con 55 anni o più; servizi completamente online {il(pct(on.values[c]))}.')
              for c in codes}
    ch7 = chapter(7, 'personale', 'Chi lavora in Comune', 'Quanto personale hanno i Comuni e quanti servizi sono online?',
        f'<p>{st_text}</p>{bar_chart(st, N, "Dipendenti comunali ogni 1.000 abitanti")}'
        f'{bar_chart(s55, N, "Dipendenti con 55 anni o più")}'
        f'<p>{on_text}</p>{bar_chart(on, N, "Servizi comunali completamente online")}' + town_blocks(towns7),
        'Il personale serve a far funzionare uffici e servizi, ma molti Comuni ne affidano una parte ad aziende o '
        'unioni, e chi lavora lì non è contato. Un organico anziano annuncia pensionamenti e la necessità di nuove '
        'assunzioni. Il dato sui servizi online è di qualche anno fa e conta i servizi offerti, non quanti cittadini '
        'li usano.')

    key_points = [
        (euro(rev.versilia), f'Entrate correnti per residente nel {rev.period}, media dei Comuni della Versilia; da '
                             f'{euro(lo("revenue")[1])} a {nm(lo("revenue")[0])} a {euro(hi("revenue")[1])} a '
                             f'{nm(hi("revenue")[0])}.', 'entrate'),
        (euro(cp.versilia), 'Investimenti impegnati per residente, media dei Comuni della Versilia.', 'investimenti'),
        (pct(hi('rigid')[1]), f'Entrate correnti assorbite da personale, prestiti e disavanzo a {nm(hi("rigid")[0])}, '
                              f'il valore più alto.', 'equilibrio'),
        (euro(db.versilia), 'Debito per mutui e prestiti per residente, media dei Comuni della Versilia.', 'debito'),
        (f'{num(lo("tari")[1])}–{num(hi("tari")[1])} euro', f'TARI annua di una famiglia di 3 persone in 100 m², da '
                                                         f'{nm(lo("tari")[0])} a {nm(hi("tari")[0])}.', 'tasse'),
        (f'{len(on_below)} su {total}', f'Comuni sotto la media toscana per servizi completamente online '
                                        f'({pct(on.benchmarks["tuscany"])}).', 'personale'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Entrate correnti per residente', euro(rev.values[c]), f'Versilia {euro(rev.versilia)}'),
        summary_item('Spesa corrente per residente', euro(sp.values[c]), f'Versilia {euro(sp.versilia)}'),
        summary_item('Investimenti impegnati per residente', euro(cp.values[c]), f'Versilia {euro(cp.versilia)}'),
        summary_item('Spese rigide sulle entrate correnti', pct(rg.values[c]), f'{ordinal(rg.rank(c))} su 7'),
        summary_item('Debito per residente', euro(db.values[c]), f'Versilia {euro(db.versilia)}'),
        summary_item('TARI famiglia tipo', euro(ta.values[c]), f'{ordinal(ta.rank(c))} su 7'),
        summary_item('Servizi completamente online', pct(on.values[c]), f'Toscana {pct(on.benchmarks["tuscany"])}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanti cittadini usano ogni servizio e quanto costa ciascuna prestazione: i bilanci dicono quanto si spende, '
        'non per quante persone.',
        'Quanto i servizi sono di buona qualità: tempi di attesa, soddisfazione degli utenti, risultati.',
        'Di quante risorse avrebbe bisogno ogni Comune per i servizi essenziali (i fabbisogni standard).',
        'Quanto delle risorse disponibili è vincolato a scopi precisi e quanto può essere davvero speso liberamente.',
        'A che punto sono i cantieri finanziati: gli impegni non dicono quando un’opera sarà finita.',
        'Quanto pagano davvero le famiglie di tasse e tariffe comunali, tenendo conto di esenzioni e riduzioni.',
    ]
    return dict(
        slug='bilanci', title='I conti dei Comuni', eyebrow='Dossier · Bilanci e servizi',
        unknown_topic='sui conti dei Comuni', theme='bilanci', theme_label='Tutti i dati su bilanci e amministrazione',
        lead='Entrate, spesa per i servizi, investimenti, debito, tasse locali e personale: una lettura dei bilanci '
             'pubblici dei sette Comuni della Versilia.',
        description='Entrate e spese, investimenti, equilibrio dei conti, debito, addizionale IRPEF e TARI, personale e '
                    'servizi online dei sette Comuni della Versilia, dai rendiconti ufficiali.',
        periods=f'Rendiconti {rev.period}, tasse e tariffe {ir.period}, costo dei rifiuti {ws.period}, personale '
                f'{st.period}, servizi online {on.period}.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6, ch7], key_points=key_points,
        towns_summary=towns_summary, unknown=unknown,
        toc=[('entrate', 'Quanto entra'), ('spesa', 'Dove vanno i soldi'), ('investimenti', 'Gli investimenti'),
             ('equilibrio', 'I conti in ordine'), ('debito', 'Il debito'), ('tasse', 'Tasse e tariffe'),
             ('personale', 'Chi lavora in Comune')])


# ---------------------------------------------------------------------------
# Dossier «Ambiente e rischi in Versilia».

STAZZEMA, SERAVEZZA = '046030', '046028'


def ambiente(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    TI = ('tuscany', 'italy')
    m = {
        'flood2': engine.measure('flood2', 'floodExposure', 'residentsPct:P2',
                                 'Residenti in aree a pericolosità media di alluvione, %', 'percent', 1, versilia=True),
        'floodn': engine.measure('floodn', 'floodExposure', 'residents:P2',
                                 'Residenti in aree a pericolosità media di alluvione, numero', 'count', 0),
        'flood3': engine.measure('flood3', 'floodExposure', 'residentsPct:P3',
                                 'Residenti in aree a pericolosità elevata di alluvione, %', 'percent', 1, versilia=True),
        'slide': engine.measure('slide', 'landslideExposure', 'residentsPct:P3+P4',
                                'Residenti in aree a pericolosità elevata o molto elevata di frana, %', 'percent', 1,
                                versilia=True),
        'slidearea': engine.measure('slidearea', 'landslideExposure', 'areaPct:P3+P4',
                                    'Territorio a pericolosità elevata o molto elevata di frana, %', 'percent', 1,
                                    versilia=True),
        'temp': engine.measure('temp', 'climateTemperatureTrend50y', 'total', 'Temperatura media annua, °C',
                               'celsius', 1),
        'tempd': engine.measure('tempd', 'climateTemperatureTrend50y', 'trend:1975-2025',
                                'Aumento stimato della temperatura media fra il 1975 e il 2025, °C', 'celsiusdelta', 1),
        'rain': engine.measure('rain', 'climatePrecipitationTrend50y', 'total', 'Pioggia caduta nell’anno, mm', 'mm', 0),
        'raind': engine.measure('raind', 'climatePrecipitationTrend50y', 'trend_percent:1975-2025',
                                'Variazione stimata della pioggia annua fra il 1975 e il 2025, %', 'change', 1),
        'erosion': engine.measure('erosion', 'shorelineDynamics', 'share:erosion',
                                  'Spiaggia naturale arretrata di oltre 5 metri, % dei km analizzati', 'percent', 1,
                                  versilia=True, partial=True),
        'advance': engine.measure('advance', 'shorelineDynamics', 'share:advance',
                                  'Spiaggia naturale avanzata di oltre 5 metri, % dei km analizzati', 'percent', 1,
                                  versilia=True, partial=True),
        'rigid': engine.measure('rigid', 'rigidDefenceProtectedCoast', 'total',
                                'Costa protetta da scogliere e altre opere rigide, %', 'percent', 1,
                                benchmarks=TI, versilia=True, partial=True),
        'bath': engine.measure('bath', 'bathingWaterQuality', 'share:areas:excellent',
                               'Acque di balneazione in classe eccellente, % delle aree', 'percent', 1,
                               versilia=True, partial=True),
        'samples': engine.measure('samples', 'bathingNonCompliantSamples', 'share:routine',
                                  'Campioni di routine fuori dai limiti di legge, %', 'percent', 1,
                                  versilia=True, partial=True),
        'flags': engine.measure('flags', 'blueFlagBeaches', 'total', 'Località con la Bandiera Blu', 'count', 0,
                                partial=True),
        'recycling': engine.measure('recycling', 'recycling', 'total', 'Raccolta differenziata, % dei rifiuti urbani',
                                    'percent', 1, benchmarks=TI),
        'waste': engine.measure('waste', 'wastePerResident', 'total', 'Rifiuti urbani per abitante, kg l’anno', 'kg',
                                0, benchmarks=TI),
        'losses': engine.measure('losses', 'waterNetworkLosses', 'total',
                                 'Acqua potabile persa nella rete di distribuzione, %', 'percent', 1,
                                 benchmarks=TI, versilia=True),
        'sites': engine.measure('sites', 'remediationProceedings', 'view:active',
                                'Siti con procedimento di bonifica aperto', 'count', 0),
        'sites_all': engine.measure('sites_all', 'remediationProceedings', 'view:all',
                                    'Siti con procedimento di bonifica, aperto o chiuso', 'count', 0),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    coast = [c for c in codes if c in m['rigid'].values]
    inland = [c for c in codes if c not in coast]
    inland_names = join_names([nm(c) for c in sorted(inland, key=lambda c: nm(c))])

    # 01 — alluvioni
    f2, fn, f3 = m['flood2'], m['floodn'], m['flood3']
    majority = [c for c, v, _ in f2.ranking if v > 50]
    f2_text = (
        f'Secondo la mappa ISPRA del {f2.period}, in Versilia vive in aree a <b>pericolosità media di alluvione</b> '
        f'{il(pct(f2.versilia))} dei residenti: sono zone che un fiume o un canale può allagare con eventi poco '
        f'frequenti ma possibili. La quota va {dal(pct(lo("flood2")[1]))} di {nm(lo("flood2")[0])} '
        f'{al(pct(hi("flood2")[1]))} di <b>{nm(hi("flood2")[0])}</b>'
        + (f', dove riguarda più di metà degli abitanti, {num(fn.values[majority[0]])} persone.' if majority else '.')
        + (f' Per numero di persone seguono {nm(fn.ranking[1][0])} ({num(fn.ranking[1][1])}) e {nm(fn.ranking[2][0])} '
           f'({num(fn.ranking[2][1])}).' if majority and fn.ranking[0][0] == majority[0] else
           f' In numero di persone, il Comune con più residenti in queste aree è {nm(fn.ranking[0][0])} '
           f'({num(fn.ranking[0][1])}).'))
    f3_text = (
        f'Nelle aree a <b>pericolosità elevata</b>, dove gli allagamenti sono più frequenti, vive {il(pct(f3.versilia))} '
        f'dei residenti della Versilia, fino {al(pct(hi("flood3")[1]))} di {nm(hi("flood3")[0])}. Le aree a pericolosità '
        f'elevata sono comprese in quelle a pericolosità media: le due quote non si sommano.')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(f2.values[c]))} dei residenti ({num(fn.values[c])} persone) vive in '
                  f'aree a pericolosità media di alluvione, {il(pct(f3.values[c]))} in aree a pericolosità elevata.')
              for c in codes}
    ch1 = chapter(1, 'alluvioni', 'Le alluvioni', 'Quante persone vivono dove fiumi e canali possono esondare?',
        f'<p>{f2_text}</p>{bar_chart(f2, N, "Residenti in aree a pericolosità media di alluvione")}'
        f'{bar_chart(fn, N, "Residenti in aree a pericolosità media di alluvione, in numero di persone")}'
        f'<p>{f3_text}</p>{bar_chart(f3, N, "Residenti in aree a pericolosità elevata di alluvione")}'
        + town_blocks(towns1),
        'Sapere quante persone abitano nelle zone allagabili aiuta a preparare i piani di protezione civile, a decidere '
        'dove fare manutenzione e opere e a informare chi ci vive. La mappa dice dove l’acqua può arrivare, non quando '
        'né con quali danni: per questo serve conoscere anche lo stato degli argini, dei canali e delle case. I '
        'residenti sono quelli contati dal censimento sui confini delle aree.')

    # 02 — frane
    sl, sa = m['slide'], m['slidearea']
    none_ = [c for c, v, _ in sl.ranking if v < 0.05]
    sl_text = (
        f'Le aree a pericolosità di frana elevata o molto elevata coprono {il(pct(sa.versilia))} del territorio della '
        f'Versilia (mappa ISPRA del {sl.period}) e ospitano {il(pct(sl.versilia))} dei residenti. Il Comune più esposto '
        f'è <b>{nm(hi("slide")[0])}</b>, dove in queste aree vive {il(pct(hi("slide")[1]))} degli abitanti; seguono '
        f'{nm(sl.ranking[1][0])} ({pct(sl.ranking[1][1])}) e {nm(sl.ranking[2][0])} ({pct(sl.ranking[2][1])}).'
        + (f' A {join_names([nm(c) for c in none_])} la quota è praticamente nulla.' if none_ else ''))
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(sl.values[c]))} dei residenti vive in aree a pericolosità di frana '
                  f'elevata o molto elevata, che coprono {il(pct(sa.values[c]))} del territorio comunale.')
              for c in codes}
    ch2 = chapter(2, 'frane', 'Le frane', 'Dove il terreno può franare, e quante persone ci abitano?',
        f'<p>{sl_text}</p>{bar_chart(sl, N, "Residenti in aree a pericolosità di frana elevata o molto elevata")}'
        f'{bar_chart(sa, N, "Territorio a pericolosità di frana elevata o molto elevata")}' + town_blocks(towns2),
        'Sulle colline e sulle Apuane le frane possono isolare paesi e interrompere strade e servizi. La mappa indica '
        'dove il terreno è più instabile, non dove una frana avverrà né quali edifici sono a rischio: per questo servono '
        'studi locali, monitoraggi e manutenzione dei versanti e delle strade.')

    # 03 — clima
    tp, td, rn, rd = m['temp'], m['tempd'], m['rain'], m['raind']
    tp_text = (
        f'Nel {tp.period} la temperatura media annua andava da {tp.fmt(lo("temp")[1])} a {nm(lo("temp")[0])}'
        + (', il Comune più in montagna,' if lo('temp')[0] == STAZZEMA else '')
        + f' a {tp.fmt(hi("temp")[1])} a {nm(hi("temp")[0])}. Fra il 1975 e il 2025 la retta che '
        f'descrive l’andamento delle temperature indica <b>un aumento di circa {num(round(sum(td.values.values()) / total, 0))} '
        f'gradi in tutti i sette Comuni</b>, da {td.fmt(lo("tempd")[1])} a {td.fmt(hi("tempd")[1])}.')
    rn_text = (
        f'La pioggia del {rn.period} va da {rn.fmt(lo("rain")[1])} a {nm(lo("rain")[0])} a <b>{rn.fmt(hi("rain")[1])} a '
        f'{nm(hi("rain")[0])}</b>' + (': piove di più verso le montagne.' if hi('rain')[0] in (STAZZEMA, SERAVEZZA) else '.')
        + f' Nei cinquant’anni fino al 2025 la tendenza della '
        f'pioggia annua è in lieve calo ovunque, da {rd.fmt(hi("raind")[1])} a {nm(hi("raind")[0])} a '
        f'{rd.fmt(lo("raind")[1])} a {nm(lo("raind")[0])}.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: temperatura media {tp.fmt(tp.values[c])} nel {tp.period}, '
                  f'{td.fmt(td.values[c])} dal 1975 secondo la tendenza; pioggia {rn.fmt(rn.values[c])} nell’anno, '
                  f'tendenza {rd.fmt(rd.values[c])} in cinquant’anni.') for c in codes}
    ch3 = chapter(3, 'clima', 'Il clima che cambia', 'Quanto è aumentata la temperatura e come cambia la pioggia?',
        f'<p>{tp_text}</p>{bar_chart(tp, N, "Temperatura media annua")}'
        f'{bar_chart(td, N, "Aumento stimato della temperatura media dal 1975 al 2025")}'
        f'<p>{rn_text}</p>{bar_chart(rn, N, "Pioggia caduta nell’anno")}'
        f'{bar_chart(rd, N, "Variazione stimata della pioggia annua dal 1975 al 2025")}' + town_blocks(towns3),
        'Estati più calde pesano sulla salute degli anziani, sulle scuole, sui consumi di energia e sull’acqua. Le serie '
        'sono ricostruite su una griglia di celle a partire da modelli e osservazioni, non misurate da una stazione nel '
        'Comune; la tendenza riassume cinquant’anni e non prevede il clima dei prossimi anni né gli eventi estremi, '
        'come i temporali molto intensi.')

    # 04 — costa
    er, ad, rg = m['erosion'], m['advance'], m['rigid']
    er_text = (
        f'Fra il 2006 e il 2020 ISPRA ha confrontato la linea di riva dei tratti di spiaggia naturale. In Versilia è '
        f'<b>avanzata di oltre 5 metri</b> {sul(pct(ad.versilia))} dei chilometri analizzati ed è arretrata di oltre '
        f'5 metri {sul(pct(er.versilia))}. Il Comune con la quota più alta di spiaggia arretrata è '
        f'{nm(hi("erosion")[0])} ({pct(hi("erosion")[1])}).')
    rg_text = (
        f'Le scogliere e le altre opere rigide proteggono {il(pct(rg.versilia))} della costa della Versilia, contro '
        f'{il(pct(rg.benchmarks["tuscany"]))} della Toscana e {il(pct(rg.benchmarks["italy"]))} dell’Italia; il valore '
        f'più alto è a {nm(hi("rigid")[0])} ({pct(hi("rigid")[1])}). I ripascimenti, cioè la sabbia riportata sulle '
        f'spiagge, non sono contati fra le opere rigide.')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: spiaggia naturale avanzata {sul(pct(ad.values[c]))} dei chilometri '
                  f'analizzati e arretrata {sul(pct(er.values[c]))}; '
                  + (f'opere di difesa rigide {sul(pct(rg.values[c]))} della costa.' if rg.values[c] > 0 else
                     'nessuna opera di difesa rigida sulla costa.')) if c in coast else
              f'<b>{esc(nm(c))}</b> non ha un tratto di costa sul mare: i dati di questo capitolo non lo riguardano.'
              for c in codes}
    ch4 = chapter(4, 'costa', 'La costa', 'La spiaggia avanza o arretra, e quanto è protetta da opere?',
        f'<p>{er_text}</p>{bar_chart(ad, N, "Spiaggia naturale avanzata di oltre 5 metri, 2006-2020")}'
        f'{bar_chart(er, N, "Spiaggia naturale arretrata di oltre 5 metri, 2006-2020")}'
        f'<p>{rg_text}</p>{bar_chart(rg, N, "Costa protetta da scogliere e altre opere rigide")}' + town_blocks(towns4),
        f'La spiaggia è il primo patrimonio economico della costa e anche una difesa naturale dalle mareggiate. I dati '
        f'riguardano i quattro Comuni sul mare, non {inland_names}. Le misure confrontano due fotografie: dicono come '
        f'si è spostata la riva, non perché né a che ritmo anno per anno, e la presenza di opere non dice se funzionano.')

    # 05 — mare
    bt, sm, fl = m['bath'], m['samples'], m['flags']
    flag_towns = [c for c, v, _ in fl.ranking if v > 0]
    bt_text = (
        f'Le acque di balneazione sono classificate da ARPAT sugli esiti delle stagioni dal {bt.period[:4]} al '
        f'{bt.period[-4:]}. '
        f'In Versilia è in classe <b>eccellente</b> {il(pct(bt.versilia))} delle aree controllate: '
        f'{il(pct(hi("bath")[1]))} a {nm(hi("bath")[0])}, {il(pct(lo("bath")[1]))} a {nm(lo("bath")[0])}.')
    sm_text = (
        f'Nella stagione {sm.period} {il(pct(sm.versilia))} dei campioni di routine ha superato almeno un limite di '
        f'legge, da {pct(lo("samples")[1])} a {nm(lo("samples")[0])} a {pct(hi("samples")[1])} a '
        f'{nm(hi("samples")[0])}: un singolo campione fuori limite porta di solito a un divieto temporaneo, non '
        f'cambia da solo la classe dell’area. Nel {fl.period} le località con la Bandiera Blu sono '
        + join_names([f'{num(fl.values[c])} a {nm(c)}' for c in flag_towns]) + '.')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: {il(pct(bt.values[c]))} delle aree di balneazione in classe eccellente; '
                  f'{il(pct(sm.values[c]))} dei campioni di routine {sm.period} fuori limite; '
                  f'{num(fl.values[c])} località con la Bandiera Blu {fl.period}.') if c in coast else
              f'<b>{esc(nm(c))}</b> non ha acque di balneazione sul mare.' for c in codes}
    ch5 = chapter(5, 'mare', 'Il mare', 'Quanto è pulita l’acqua dove si fa il bagno?',
        f'<p>{bt_text}</p>{bar_chart(bt, N, "Aree di balneazione in classe eccellente")}'
        f'<p>{sm_text}</p>{bar_chart(sm, N, "Campioni di routine fuori dai limiti di legge")}' + town_blocks(towns5),
        'La qualità del mare conta per la salute di chi fa il bagno e per il turismo. La classe riassume quattro '
        'stagioni e non dice com’è l’acqua oggi: per sapere se si può fare il bagno valgono i cartelli e le ordinanze '
        'in spiaggia. La Bandiera Blu tiene conto anche di servizi e gestione, non solo della qualità dell’acqua.')

    # 06 — rifiuti e acqua
    rc, ws, ls = m['recycling'], m['waste'], m['losses']
    rc_below = [c for c in codes if rc.values[c] < rc.benchmarks['tuscany']]
    rc_text = (
        f'Nel {rc.period} la raccolta differenziata andava {dal(pct(lo("recycling")[1]))} di {nm(lo("recycling")[0])} '
        f'{al(pct(hi("recycling")[1]))} di <b>{nm(hi("recycling")[0])}</b>; in Toscana era {il(pct(rc.benchmarks["tuscany"]))}, '
        f'in Italia {il(pct(rc.benchmarks["italy"]))}'
        + (f'. Sotto la media toscana {"c’è" if len(rc_below) == 1 else "ci sono"} {join_names([nm(c) for c in rc_below])}.'
           if rc_below else '.')
        + f' I rifiuti per abitante vanno da {ws.fmt(lo("waste")[1])} a {nm(lo("waste")[0])} a '
          f'<b>{ws.fmt(hi("waste")[1])} a {nm(hi("waste")[0])}</b> (in Toscana {ws.fmt(ws.benchmarks["tuscany"])}): nei '
          f'Comuni turistici una parte dei rifiuti è prodotta da chi non vi risiede ma viene divisa fra i soli residenti.')
    ls_text = (
        f'Secondo l’ultimo censimento Istat delle acque ({ls.period}), la rete di distribuzione perdeva in Versilia '
        f'{il(pct(ls.versilia))} dell’acqua immessa (Toscana {pct(ls.benchmarks["tuscany"])}, Italia '
        f'{pct(ls.benchmarks["italy"])}), da {pct(lo("losses")[1])} a {nm(lo("losses")[0])} a '
        f'<b>{pct(hi("losses")[1])} a {nm(hi("losses")[0])}</b>.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: raccolta differenziata {al(pct(rc.values[c]))} e {ws.fmt(ws.values[c])} di '
                  f'rifiuti per abitante nel {rc.period}; nel {ls.period} la rete idrica perdeva {il(pct(ls.values[c]))} '
                  f'dell’acqua immessa.') for c in codes}
    ch6 = chapter(6, 'rifiuti-acqua', 'Rifiuti e acqua', 'Quanto si ricicla e quanta acqua si perde nei tubi?',
        f'<p>{rc_text}</p>{bar_chart(rc, N, "Raccolta differenziata")}'
        f'{bar_chart(ws, N, "Rifiuti urbani per abitante")}'
        f'<p>{ls_text}</p>{bar_chart(ls, N, "Acqua persa nella rete di distribuzione")}'
        '<p>Quanto costa il servizio rifiuti e quanto paga una famiglia di TARI è nel dossier '
        '<a href="../bilanci/#tasse">I conti dei Comuni</a>.</p>' + town_blocks(towns6),
        'Raccolta differenziata e acqua sono servizi di tutti i giorni, pagati in bolletta. La raccolta differenziata '
        'misura quanto si separa, non quanto viene poi davvero riciclato. Le perdite della rete sono di qualche anno fa '
        'e comprendono sia i tubi che perdono sia l’acqua che sfugge ai contatori.')

    # 07 — bonifiche
    st, sa_ = m['sites'], m['sites_all']
    st_sum = sum(st.values.values())
    st_text = (
        f'{"All’" if re.match(r"(8|11) ", period_label(st.period)) else "Al "}{period_label(st.period)} l’anagrafe regionale contava in Versilia <b>{num(st_sum)} siti con un '
        f'procedimento di bonifica ancora aperto</b>, su {num(sum(sa_.values.values()))} siti registrati in tutto. Il '
        f'numero più alto è a {nm(hi("sites")[0])} ({num(hi("sites")[1])} aperti su {num(sa_.values[hi("sites")[0]])}), '
        f'il più basso a {nm(lo("sites")[0])} ({num(lo("sites")[1])}).')
    towns7 = {c: (f'<b>{esc(nm(c))}</b>: {num(st.values[c])} siti con procedimento di bonifica aperto, '
                  f'{num(sa_.values[c])} registrati in tutto.') for c in codes}
    ch7 = chapter(7, 'bonifiche', 'I siti da bonificare', 'Quanti terreni contaminati, o sospetti tali, sono in attesa?',
        f'<p>{st_text}</p>{bar_chart(st, N, "Siti con procedimento di bonifica aperto")}' + town_blocks(towns7),
        'Un procedimento si apre quando un terreno o una falda possono essere inquinati, per esempio dopo una perdita '
        'da un serbatoio o la chiusura di un’attività. Il numero dice quante pratiche sono in corso, non quanto è grave '
        'l’inquinamento: un procedimento chiuso non vuol dire per forza che il sito sia stato bonificato.')

    key_points = [
        (pct(f2.versilia), f'Dei residenti della Versilia vive in aree a pericolosità media di alluvione; a '
                           f'{nm(hi("flood2")[0])} {il(pct(hi("flood2")[1]))}.', 'alluvioni'),
        (pct(hi('slide')[1]), f'Dei residenti di {nm(hi("slide")[0])} vive in aree a pericolosità di frana elevata o '
                              f'molto elevata.', 'frane'),
        (f'{td.fmt(lo("tempd")[1])} / {td.fmt(hi("tempd")[1])}',
         'Aumento stimato della temperatura media fra il 1975 e il 2025, in tutti i sette Comuni.', 'clima'),
        (pct(rg.versilia), f'Della costa protetta da scogliere e opere rigide; in Toscana '
                           f'{il(pct(rg.benchmarks["tuscany"]))}.', 'costa'),
        (pct(bt.versilia), 'Delle acque di balneazione della Versilia in classe eccellente.', 'mare'),
        (pct(ls.versilia), f'Dell’acqua potabile persa nella rete di distribuzione; in Toscana '
                           f'{il(pct(ls.benchmarks["tuscany"]))}.', 'rifiuti-acqua'),
    ]
    towns_summary = {}
    for c in codes:
        items = [
            summary_item('Residenti in aree di alluvione a pericolosità media', pct(f2.values[c]),
                         f'Versilia {pct(f2.versilia)}'),
            summary_item('Residenti in aree di frana a pericolosità elevata', pct(sl.values[c]),
                         f'Versilia {pct(sl.versilia)}'),
            summary_item('Aumento stimato della temperatura dal 1975', td.fmt(td.values[c]), f'{tp.fmt(tp.values[c])} nel {tp.period}'),
        ]
        if c in coast:
            items += [summary_item('Costa protetta da opere rigide', pct(rg.values[c]), f'Versilia {pct(rg.versilia)}'),
                      summary_item('Aree di balneazione eccellenti', pct(bt.values[c]), f'Versilia {pct(bt.versilia)}')]
        items += [summary_item('Raccolta differenziata', pct(rc.values[c]), f'Toscana {pct(rc.benchmarks["tuscany"])}'),
                  summary_item('Acqua persa nella rete', pct(ls.values[c]), f'Versilia {pct(ls.versilia)}'),
                  summary_item('Siti con bonifica aperta', num(st.values[c]), f'{ordinal(st.rank(c))} su 7')]
        towns_summary[c] = '<ul class="dr-town-list">' + ''.join(items) + '</ul>'
    unknown = [
        'Quanto sono vulnerabili case, strade e servizi nelle aree pericolose, e quali danni ci si può aspettare: le '
        'mappe indicano la pericolosità, non il rischio per il singolo edificio.',
        'Quanti residenti vivono oggi nelle aree pericolose: le mappe usano la popolazione dei censimenti.',
        'Quali opere di difesa e manutenzione sono state fatte, e con quali risultati.',
        'Quanto fa caldo nelle diverse zone dei paesi e delle città, e quante persone soffrono le ondate di calore.',
        'Qual è la qualità dell’aria: in buona parte dei Comuni non ci sono centraline di misura.',
        'Quali inquinanti ci sono nei siti da bonificare e a che punto sono i lavori.',
    ]
    return dict(
        slug='ambiente', title='Ambiente e rischi in Versilia', eyebrow='Dossier · Ambiente, clima e rischio',
        unknown_topic='sull’ambiente', theme='ambiente', theme_label='Tutti i dati sull’ambiente',
        lead='Alluvioni e frane, clima, costa e mare, rifiuti, acqua e siti da bonificare: una lettura dei dati pubblici '
             'sui sette Comuni della Versilia.',
        description='Residenti nelle aree a pericolosità di alluvione e frana, temperature e pioggia, spiagge e opere di '
                    'difesa, qualità del mare, raccolta differenziata, perdite idriche e bonifiche nei sette Comuni '
                    'della Versilia.',
        periods=f'Mappe di pericolosità ISPRA {f2.period} (alluvioni) e {sl.period} (frane), clima fino al {tp.period}, '
                f'costa {er.period}, balneazione {bt.period}, rifiuti {rc.period}, rete idrica {ls.period}, bonifiche '
                f'{period_label(st.period)}.',
        method='Le quote di residenti in aree pericolose usano la popolazione del censimento indicata dalla fonte: 2011 '
               'per le alluvioni, 2021 per le frane. Per clima e Bandiere Blu non si calcola un valore unico della '
               'Versilia.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6, ch7], key_points=key_points,
        towns_summary=towns_summary, unknown=unknown,
        toc=[('alluvioni', 'Le alluvioni'), ('frane', 'Le frane'), ('clima', 'Il clima che cambia'), ('costa', 'La costa'),
             ('mare', 'Il mare'), ('rifiuti-acqua', 'Rifiuti e acqua'), ('bonifiche', 'I siti da bonificare')])


# ---------------------------------------------------------------------------
# Dossier «Chi vive in Versilia».

def demografia(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    TI = ('tuscany', 'italy')
    m = {
        'pop': engine.measure('pop', 'population', 'total', 'Residenti al 1° gennaio, numero', 'count', 0),
        'chg': engine.measure('chg', 'populationChange', 'total', 'Variazione dei residenti dal 2019', 'change', 1,
                              benchmarks=TI, versilia=True),
        'births': engine.measure('births', 'naturalDemographicDynamics', 'part:births', 'Nati ogni 1.000 abitanti',
                                 'rate1000', 1, benchmarks=TI, versilia=True),
        'deaths': engine.measure('deaths', 'naturalDemographicDynamics', 'part:deaths', 'Morti ogni 1.000 abitanti',
                                 'rate1000', 1, benchmarks=TI, versilia=True),
        'nat': engine.measure('nat', 'naturalDemographicDynamics', 'part:balance', 'Nati meno morti, ogni 1.000 abitanti',
                              'per1000s', 1, benchmarks=TI, versilia=True),
        'tot': engine.measure('tot', 'totalResidentialMobility', 'part:balance',
                              'Iscritti meno cancellati per trasferimento di residenza, ogni 1.000 abitanti', 'per1000s', 1,
                              benchmarks=TI, versilia=True),
        'int': engine.measure('int', 'internalResidentialMobility', 'part:balance',
                              'Saldo dei trasferimenti con gli altri Comuni italiani, ogni 1.000 abitanti', 'per1000s', 1,
                              benchmarks=TI, versilia=True),
        'intin': engine.measure('intin', 'internalResidentialMobility', 'part:arrivals',
                                'Arrivati da altri Comuni italiani, ogni 1.000 abitanti', 'rate1000', 1,
                                benchmarks=TI, versilia=True),
        'intout': engine.measure('intout', 'internalResidentialMobility', 'part:departures',
                                 'Partiti verso altri Comuni italiani, ogni 1.000 abitanti', 'rate1000', 1,
                                 benchmarks=TI, versilia=True),
        'for': engine.measure('for', 'foreignResidentialMobility', 'part:balance',
                              'Saldo dei trasferimenti con l’estero, ogni 1.000 abitanti', 'per1000s', 1,
                              benchmarks=TI, versilia=True),
        'frn': engine.measure('frn', 'foreignResidents', 'total', 'Residenti con cittadinanza straniera, %', 'percent', 1,
                              benchmarks=TI, versilia=True),
        'frnc': engine.measure('frnc', 'foreignResidents', 'count', 'Residenti con cittadinanza straniera, numero',
                               'count', 0),
        'kids': engine.measure('kids', 'ageDistribution', 'age:0-14', 'Residenti sotto i 15 anni, %', 'percent', 1,
                               benchmarks=TI, versilia=True),
        'young': engine.measure('young', 'ageDistribution', 'age:20-34', 'Residenti fra 20 e 34 anni, %', 'percent', 1,
                                benchmarks=TI, versilia=True),
        'hh': engine.measure('hh', 'householdSize', 'total', 'Componenti medi per famiglia', 'decimal', 2),
        'single': engine.measure('single', 'singleHouseholds', 'total', 'Famiglie di una sola persona, %', 'percent', 1,
                                 benchmarks=TI),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    T = lambda k, d=1: num(m[k].benchmarks['tuscany'], d)
    I = lambda k, d=1: num(m[k].benchmarks['italy'], d)
    pop, chg = m['pop'], m['chg']
    pop_sum = sum(pop.values.values())
    start, end = period_label(chg.period).split('-')[0], period_label(chg.period).split('-')[-1]

    # 01 — quanti siamo
    up = [c for c, v, _ in chg.ranking if v > 0]
    down = [c for c, v, _ in chg.ranking if v < 0]
    pop_text = (
        f'All’inizio del {pop.period} in Versilia vivono <b>{num(pop_sum)} persone</b>. {nm(hi("pop")[0])} da sola ne '
        f'conta {num(hi("pop")[1])}, {il(pct(hi("pop")[1] / pop_sum * 100, 0))} del totale; il Comune più piccolo è '
        f'{nm(lo("pop")[0])}, con {num(lo("pop")[1])} residenti.')
    chg_text = (
        f'Fra il {start} e il {end} la popolazione della Versilia è '
        f'{"calata" if chg.versilia < 0 else "cresciuta"} {del_(num(abs(chg.versilia), 1) + "%")}, '
        f'{"meno" if abs(chg.versilia) < abs(chg.benchmarks["tuscany"]) else "più"} che in Toscana '
        f'({signed(chg.benchmarks["tuscany"])}%) e in Italia ({signed(chg.benchmarks["italy"])}%). '
        + (f'Crescono di poco {join_names([nm(c) for c in up])}; ' if up else 'Nessun Comune cresce; ')
        + (f'calano soprattutto {join_names([nm(c) for c in down[-2:]])} '
           f'({", ".join(signed(chg.values[c]) + "%" for c in down[-2:])}).' if len(down) >= 2 else
           f'cala {nm(down[0])} ({signed(chg.values[down[0]])}%).' if down else 'nessuno cala.'))
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: {num(pop.values[c])} residenti nel {pop.period}, '
                  f'{signed(chg.values[c])}% rispetto al {start}.') for c in codes}
    ch1 = chapter(1, 'quanti', 'Quanti siamo', 'Quante persone vivono in Versilia e quante ce n’erano qualche anno fa?',
        f'<p>{pop_text}</p>{bar_chart(pop, N, "Residenti al 1° gennaio")}'
        f'<p>{chg_text}</p>{bar_chart(chg, N, f"Variazione dei residenti, {start}-{end}")}' + town_blocks(towns1),
        'Il numero di residenti decide molte cose: quanti posti servono a scuola, quanti medici di famiglia, quanti '
        'soldi arrivano ai Comuni dallo Stato. I residenti non sono però tutte le persone presenti: in Versilia d’estate '
        'ci sono molti più turisti e proprietari di seconde case.')

    # 02 — nascite e morti
    bi, de, nat = m['births'], m['deaths'], m['nat']
    births_text = (
        f'Nel {bi.period} in Versilia sono nati <b>{num(bi.versilia, 1)} bambini ogni 1.000 abitanti</b>, '
        f'{"meno" if bi.versilia < bi.benchmarks["tuscany"] else "più"} che in Toscana ({T("births")}) e in Italia '
        f'({I("births")}): da {num(lo("births")[1], 1)} a {nm(lo("births")[0])} a {num(hi("births")[1], 1)} a '
        f'{nm(hi("births")[0])}. I morti sono stati {num(de.versilia, 1)} ogni 1.000 abitanti (Toscana {T("deaths")}).')
    all_neg = all(v < 0 for v in nat.values.values())
    nat_text = (
        ('In tutti i sette Comuni i morti superano i nati. ' if all_neg else '')
        + f'In Versilia il saldo fra nati e morti è di <b>{signed(nat.versilia)} ogni 1.000 abitanti</b> (Toscana '
          f'{signed(nat.benchmarks["tuscany"])}), con il valore più basso a {nm(lo("nat")[0])} ({signed(lo("nat")[1])}). '
          'Il dossier <a href="../anziani/">Invecchiare in Versilia</a> segue lo stesso dato dal lato degli anziani.')
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: {num(bi.values[c], 1)} nati e {num(de.values[c], 1)} morti ogni 1.000 abitanti '
                  f'nel {bi.period}, saldo {signed(nat.values[c])}.') for c in codes}
    ch2 = chapter(2, 'nascite', 'Poche nascite', 'Quanti bambini nascono?',
        f'<p>{births_text}</p>{bar_chart(bi, N, "Nati ogni 1.000 abitanti", "Dati Istat provvisori.")}'
        f'{bar_chart(de, N, "Morti ogni 1.000 abitanti", "Dati Istat provvisori.")}'
        f'<p>{nat_text}</p>{bar_chart(nat, N, "Saldo naturale: nati meno morti")}' + town_blocks(towns2),
        'Le nascite di oggi sono gli iscritti alla scuola fra sei anni e i lavoratori fra venticinque. Quando i nati '
        'sono molti meno dei morti, la popolazione resta stabile solo se arrivano nuovi residenti da fuori.')

    # 03 — chi arriva e chi parte
    tot, it, fo, iin, iout = m['tot'], m['int'], m['for'], m['intin'], m['intout']
    neg_int = [c for c, v, _ in it.ranking if v < 0]
    tot_text = (
        f'Nel {tot.period} in Versilia '
        f'{"sono arrivati più nuovi residenti di quanti ne siano partiti" if tot.versilia > 0 else "sono partiti più residenti di quanti ne siano arrivati"}: '
        f'il saldo dei trasferimenti è di '
        f'<b>{signed(tot.versilia)} ogni 1.000 abitanti</b> (Toscana {signed(tot.benchmarks["tuscany"])}, Italia '
        f'{signed(tot.benchmarks["italy"])}). Con gli altri Comuni italiani '
        f'il saldo è di {signed(it.versilia)} (Toscana {signed(it.benchmarks["tuscany"])}), con l’estero di '
        f'{signed(fo.versilia)} (Toscana {signed(fo.benchmarks["tuscany"])}).')
    int_text = (
        f'Ogni anno si spostano molte persone in entrambe le direzioni: in Versilia sono arrivati da altri Comuni '
        f'{num(iin.versilia, 1)} residenti ogni 1.000 abitanti e ne sono partiti {num(iout.versilia, 1)}. '
        + (f'Fa eccezione {nm(neg_int[0])}, dove le partenze superano gli arrivi: {num(iout.values[neg_int[0]], 1)} '
           f'partiti e {num(iin.values[neg_int[0]], 1)} arrivati ogni 1.000 abitanti.' if len(neg_int) == 1 else
           f'Fanno eccezione {join_names([nm(c) for c in neg_int])}, dove le partenze superano gli arrivi: '
           + '; '.join(f'a {nm(c)} {num(iout.values[c], 1)} partiti e {num(iin.values[c], 1)} arrivati ogni 1.000 abitanti'
                       for c in neg_int) + '.'
           if neg_int else 'In tutti i sette Comuni gli arrivi superano le partenze.'))
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: saldo dei trasferimenti {signed(tot.values[c])} ogni 1.000 abitanti nel '
                  f'{tot.period}; con l’Italia {signed(it.values[c])}, con l’estero {signed(fo.values[c])}.') for c in codes}
    ch3 = chapter(3, 'arrivi', 'Chi arriva e chi parte', 'Si viene a vivere in Versilia o se ne va via?',
        f'<p>{tot_text}</p>{bar_chart(tot, N, "Saldo dei trasferimenti di residenza")}'
        f'<p>{int_text}</p>{bar_chart(it, N, "Saldo con gli altri Comuni italiani")}'
        f'{bar_chart(fo, N, "Saldo con l’estero")}' + town_blocks(towns3),
        f'Chi arriva e chi parte cambia la popolazione quanto chi nasce e chi muore. Sono però flussi diversi, qui '
        f'misurati in anni diversi ({tot.period} e {nat.period}): non si sommano per ricostruire la variazione dei '
        'residenti né per prevederla. Contano solo i cambi di residenza registrati in anagrafe: chi vive qui senza '
        'spostare la residenza, o chi si trasferisce senza comunicarlo, non compare.')

    # 04 — stranieri
    fr, frc = m['frn'], m['frnc']
    fr_sum = sum(frc.values.values())
    fr_text = (
        f'All’inizio del {fr.period} i residenti con cittadinanza straniera in Versilia erano <b>{num(fr_sum)}</b>, '
        f'{il(pct(fr.versilia))} della popolazione: '
        + (f'{"meno" if fr.versilia < fr.benchmarks["tuscany"] else "più"} che in Toscana ({pct(fr.benchmarks["tuscany"])}) '
           f'e in Italia ({pct(fr.benchmarks["italy"])}). '
           if (fr.versilia < fr.benchmarks["tuscany"]) == (fr.versilia < fr.benchmarks["italy"]) else
           f'{"meno" if fr.versilia < fr.benchmarks["tuscany"] else "più"} che in Toscana ({pct(fr.benchmarks["tuscany"])}) '
           f'e {"meno" if fr.versilia < fr.benchmarks["italy"] else "più"} che in Italia ({pct(fr.benchmarks["italy"])}). ')
        + f'La quota più alta è a {nm(hi("frn")[0])} ({pct(hi("frn")[1])}), la più bassa a {nm(lo("frn")[0])} '
        f'({pct(lo("frn")[1])}).')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: {num(frc.values[c])} residenti stranieri, {il(pct(fr.values[c]))} della '
                  f'popolazione (Toscana {pct(fr.benchmarks["tuscany"])}).') for c in codes}
    ch4 = chapter(4, 'stranieri', 'I residenti stranieri', 'Quante persone con cittadinanza straniera vivono qui?',
        f'<p>{fr_text}</p>{bar_chart(fr, N, "Residenti con cittadinanza straniera")}'
        f'{bar_chart(frc, N, "Residenti con cittadinanza straniera, numero")}' + town_blocks(towns4),
        'Il dato conta la cittadinanza, non il luogo di nascita: chi è nato all’estero ed è diventato italiano non è '
        'compreso, mentre lo sono i figli di stranieri nati in Italia che non hanno ancora la cittadinanza. Una quota bassa '
        'può dipendere sia da quante persone arrivano dall’estero sia da quante, nel tempo, sono diventate italiane.')

    # 05 — giovani
    ki, yo = m['kids'], m['young']
    ki_below = [c for c, v, _ in ki.ranking if v < ki.benchmarks['tuscany']]
    ki_text = (
        f'All’inizio del {ki.period} i ragazzi sotto i 15 anni sono {il(pct(ki.versilia))} dei residenti della '
        f'Versilia, contro {il(pct(ki.benchmarks["tuscany"]))} in Toscana e {il(pct(ki.benchmarks["italy"]))} in Italia. '
        f'{count_words(len(ki_below), total)[:1].upper()}{count_words(len(ki_below), total)[1:]} restano sotto la media '
        f'toscana; la quota va {dal(pct(lo("kids")[1]))} a {nm(lo("kids")[0])} {al(pct(hi("kids")[1]))} a '
        f'{nm(hi("kids")[0])}.')
    yo_text = (
        f'Le persone fra 20 e 34 anni, l’età in cui si cerca casa e lavoro e si fanno figli, sono '
        f'<b>{il(pct(yo.versilia))}</b> dei residenti (Toscana {pct(yo.benchmarks["tuscany"])}, Italia '
        f'{pct(yo.benchmarks["italy"])}): {dal(pct(lo("young")[1]))} a {nm(lo("young")[0])} {al(pct(hi("young")[1]))} a '
        f'{nm(hi("young")[0])}.')
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: sotto i 15 anni {il(pct(ki.values[c]))} dei residenti, fra 20 e 34 anni '
                  f'{il(pct(yo.values[c]))}.') for c in codes}
    ch5 = chapter(5, 'giovani', 'Bambini e giovani', 'Quanti sono i più giovani?',
        f'<p>{ki_text}</p>{bar_chart(ki, N, "Residenti sotto i 15 anni")}'
        f'<p>{yo_text}</p>{bar_chart(yo, N, "Residenti fra 20 e 34 anni")}' + town_blocks(towns5),
        'Bambini e giovani adulti sono la parte della popolazione che terrà in piedi scuole, lavoro e servizi nei '
        'prossimi decenni. Una quota bassa di 20-34enni può indicare che i giovani se ne vanno per studio, lavoro o per '
        'il costo della casa.')

    # 06 — famiglie
    hh, si = m['hh'], m['single']
    hh_text = (
        f'Nel {hh.period} una famiglia conta in media da {num(lo("hh")[1], 2)} persone a {nm(lo("hh")[0])} a '
        f'{num(hi("hh")[1], 2)} a {nm(hi("hh")[0])}. Le famiglie di una sola persona vanno '
        f'{dal(pct(lo("single")[1]))} a {nm(lo("single")[0])} {al(pct(hi("single")[1]))} a {nm(hi("single")[0])}, '
        f'contro {il(pct(si.benchmarks["tuscany"]))} in Toscana e {il(pct(si.benchmarks["italy"]))} in Italia. '
        'Il dossier <a href="../casa/">Abitare in Versilia</a> legge questi dati insieme alle case e agli affitti.')
    towns6 = {c: (f'<b>{esc(nm(c))}</b>: {num(hh.values[c], 2)} persone per famiglia; famiglie di una sola persona '
                  f'{pct(si.values[c])} (Toscana {pct(si.benchmarks["tuscany"])}).') for c in codes}
    ch6 = chapter(6, 'famiglie', 'Le famiglie', 'Come sono fatte le famiglie?',
        f'<p>{hh_text}</p>{bar_chart(hh, N, "Componenti medi per famiglia")}'
        f'{bar_chart(si, N, "Famiglie di una sola persona")}' + town_blocks(towns6),
        'Famiglie più piccole vogliono dire più case per lo stesso numero di abitanti e più persone che vivono da sole, '
        'spesso anziani. Sono dati del censimento permanente, aggiornati con qualche anno di ritardo.')

    key_points = [
        (num(pop_sum), f'Residenti in Versilia all’inizio del {pop.period}.', 'quanti'),
        (f'{signed(chg.versilia)}%', f'Variazione dei residenti dal {start}; in Toscana {signed(chg.benchmarks["tuscany"])}%.',
         'quanti'),
        (num(bi.versilia, 1), f'Nati ogni 1.000 abitanti nel {bi.period}, contro {T("births")} in Toscana.', 'nascite'),
        (signed(tot.versilia), f'Saldo dei trasferimenti di residenza ogni 1.000 abitanti nel {tot.period}: arrivano più '
                               'persone di quante ne partano.' if tot.versilia > 0 else
                               f'Saldo dei trasferimenti di residenza ogni 1.000 abitanti nel {tot.period}.', 'arrivi'),
        (pct(fr.versilia), f'Residenti con cittadinanza straniera; in Toscana {il(pct(fr.benchmarks["tuscany"]))}.',
         'stranieri'),
        (pct(ki.versilia), f'Residenti sotto i 15 anni; in Italia {il(pct(ki.benchmarks["italy"]))}.', 'giovani'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Residenti', num(pop.values[c]), f'{signed(chg.values[c])}% dal {start}'),
        summary_item('Nati ogni 1.000 abitanti', num(bi.values[c], 1), f'Toscana {T("births")}'),
        summary_item('Saldo dei trasferimenti ogni 1.000 abitanti', signed(tot.values[c]),
                     f'Toscana {signed(tot.benchmarks["tuscany"])}'),
        summary_item('Residenti stranieri', pct(fr.values[c]), f'Toscana {pct(fr.benchmarks["tuscany"])}'),
        summary_item('Residenti sotto i 15 anni', pct(ki.values[c]), f'Toscana {pct(ki.benchmarks["tuscany"])}'),
        summary_item('Componenti medi per famiglia', num(hh.values[c], 2), f'{ordinal(hh.rank(c))} su {total}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quante persone vivono davvero in Versilia nei mesi estivi, fra turisti, lavoratori stagionali e proprietari di '
        'seconde case.',
        'Dove vanno e da dove arrivano i residenti che si trasferiscono, e quanti anni hanno.',
        'Quanti giovani se ne vanno per studio o lavoro senza spostare la residenza.',
        'Quanti residenti sono nati all’estero: i dati contano la cittadinanza, non il luogo di nascita.',
        'Come cambierà la popolazione nei prossimi anni: le previsioni Istat non scendono al livello dei singoli Comuni.',
    ]
    return dict(
        slug='demografia', title='Chi vive in Versilia', eyebrow='Dossier · Popolazione',
        unknown_topic='sulla popolazione', theme='demografia', theme_label='Tutti i dati sulla popolazione',
        lead='Quante persone ci vivono, quanti bambini nascono, chi arriva e chi parte, quanti sono gli stranieri, i '
             'giovani e come sono fatte le famiglie: una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Residenti, nascite e morti, trasferimenti di residenza, cittadini stranieri, bambini e giovani, '
                    'dimensione delle famiglie nei sette Comuni della Versilia, con confronti con Toscana e Italia.',
        periods=f'Residenti {pop.period}, nascite e morti {bi.period}, trasferimenti {tot.period}, stranieri {fr.period}, '
                f'età {ki.period}, famiglie {hh.period}.',
        method='Il numero totale di residenti e di stranieri della Versilia è la somma dei valori dei sette Comuni.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5, ch6], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('quanti', 'Quanti siamo'), ('nascite', 'Poche nascite'), ('arrivi', 'Chi arriva e chi parte'),
             ('stranieri', 'I residenti stranieri'), ('giovani', 'Bambini e giovani'), ('famiglie', 'Le famiglie')])


# ---------------------------------------------------------------------------
# Dossier «Investimenti e opere in Versilia».

def investimenti(engine: Engine) -> dict:
    N = engine.names
    codes = engine.codes
    total = len(codes)
    m = {
        'pnrr': engine.measure('pnrr', 'pnrrFunding', 'nativeRatio',
                               'Fondi PNRR dei progetti di cui il Comune è attuatore, euro per abitante', 'eur', 0,
                               versilia=True),
        'pnrre': engine.measure('pnrre', 'pnrrFunding', 'fundingEuro',
                                'Fondi PNRR dei progetti di cui il Comune è attuatore, euro', 'eur', 0),
        'done': engine.measure('done', 'pnrrConcluded', 'nativeRatio',
                               'Progetti PNRR del Comune in fase di conclusione, %', 'percent', 1, versilia=True),
        'sel': engine.measure('sel', 'pnrrConcluded', 'selectedProjects', 'Progetti PNRR di cui il Comune è attuatore, numero',
                              'count', 0),
        'donen': engine.measure('donen', 'pnrrConcluded', 'concludedProjects',
                                'Progetti PNRR del Comune in fase di conclusione, numero', 'count', 0),
        'works': engine.measure('works', 'publicWorks', 'total',
                                'Valore delle opere pubbliche monitorate in BDAP, euro per abitante', 'eur', 0),
        'capc': engine.measure('capc', 'capitalExpenditureCommittedPerResident', 'total',
                               'Spesa per investimenti impegnata nell’anno, euro per abitante', 'eur', 0, versilia=True),
        'capp': engine.measure('capp', 'capitalPayments', 'total',
                               'Pagamenti per investimenti nell’anno, euro per abitante', 'eur', 0, versilia=True),
        'pabn': engine.measure('pabn', 'pabProgrammedInterventions', 'total',
                               'Interventi di manutenzione di fossi e canali programmati nel 2026, numero', 'count', 0),
        'pabv': engine.measure('pabv', 'pabProgrammedMaintenanceValue', 'total',
                               'Valore della manutenzione di fossi e canali programmata nel 2026, euro', 'eur', 0),
        'pabs': engine.measure('pabs', 'pabInterventionsCompleted', 'share:operational',
                               'Interventi di manutenzione registrati come conclusi, % di quelli nel portale', 'percent', 1,
                               versilia=True),
        'pabd': engine.measure('pabd', 'pabInterventionsCompleted', 'total',
                               'Interventi di manutenzione registrati come conclusi, numero', 'count', 0),
    }
    hi = lambda k: m[k].ranking[0]
    lo = lambda k: m[k].ranking[-1]
    nm = lambda code: N[code]
    eur = lambda v: num(v) + ' €'
    mln = lambda v: num(v / 1e6, 1) + ' milioni di euro'

    # 01 — i fondi PNRR
    pn, pe = m['pnrr'], m['pnrre']
    pe_sum = sum(pe.values.values())
    day = period_label(pn.period)
    pn_text = (
        f'Al {day} i sette Comuni risultano responsabili, come soggetti attuatori, di progetti PNRR per '
        f'<b>{mln(pe_sum)}</b>: {eur(pn.versilia)} per abitante in Versilia. In valore assoluto il primo è '
        f'{nm(hi("pnrre")[0])}, con {mln(hi("pnrre")[1])}. Per abitante, invece, il valore più alto è a '
        f'{nm(hi("pnrr")[0])} ({eur(hi("pnrr")[1])}) e il più basso a {nm(lo("pnrr")[0])} ({eur(lo("pnrr")[1])}).')
    towns1 = {c: (f'<b>{esc(nm(c))}</b>: progetti PNRR per {mln(pe.values[c])}, {eur(pn.values[c])} per abitante '
                  f'({ordinal(pn.rank(c))} su {total}).') for c in codes}
    ch1 = chapter(1, 'pnrr', 'I fondi del PNRR', 'Quanti fondi del PNRR gestiscono i Comuni?',
        f'<p>{pn_text}</p>{bar_chart(pn, N, "Fondi PNRR per abitante", f"Fotografia della Regione Toscana al {day}.")}'
        f'{bar_chart(pe, N, "Fondi PNRR, euro")}' + town_blocks(towns1),
        'Il dato conta i fondi assegnati ai progetti di cui il Comune è responsabile, non i soldi già pagati né tutti i '
        'progetti PNRR sul territorio: quelli gestiti da Regione, Provincia, scuole, aziende sanitarie o gestori dei '
        'servizi non sono compresi. Nei Comuni piccoli un solo progetto grande basta a far salire molto il valore per '
        'abitante.')

    # 02 — a che punto sono
    dn, se, dc = m['done'], m['sel'], m['donen']
    se_sum, dc_sum = sum(se.values.values()), sum(dc.values.values())
    dn_text = (
        f'Dei <b>{num(se_sum)} progetti PNRR</b> di cui i Comuni sono attuatori, {num(dc_sum)} risultano nella fase '
        f'«conclusione» del sistema nazionale di monitoraggio: {il(pct(dn.versilia))}. La quota va '
        f'{dal(pct(lo("done")[1]))} a {nm(lo("done")[0])} {al(pct(hi("done")[1]))} a '
        f'{join_names([nm(c) for c, v, _ in dn.ranking if v == hi("done")[1]])}. Il Comune con più progetti è '
        f'{nm(hi("sel")[0])}, con {num(hi("sel")[1])}.')
    towns2 = {c: (f'<b>{esc(nm(c))}</b>: {num(dc.values[c])} progetti in fase di conclusione su {num(se.values[c])}, '
                  f'{il(pct(dn.values[c]))}.') for c in codes}
    ch2 = chapter(2, 'avanzamento', 'A che punto sono i progetti', 'Quanti progetti PNRR sono arrivati alla fine?',
        f'<p>{dn_text}</p>{bar_chart(dn, N, "Progetti PNRR in fase di conclusione")}'
        f'{bar_chart(se, N, "Progetti PNRR di cui il Comune è attuatore")}' + town_blocks(towns2),
        'La fase «conclusione» è uno stato amministrativo registrato nel sistema di monitoraggio: non dice se l’opera è '
        'stata collaudata, se è aperta e se le persone la usano. Per sapere che cosa hanno prodotto i progetti servono '
        'i dati sui tempi, sui costi finali e sui risultati di ciascuno.')

    # 03 — le opere pubbliche
    wk = m['works']
    wk_text = (
        f'Nella banca dati delle amministrazioni pubbliche del Ministero dell’Economia (BDAP) il valore delle opere '
        f'pubbliche monitorate va da {eur(lo("works")[1])} per abitante a {nm(lo("works")[0])} a '
        f'{eur(hi("works")[1])} a {nm(hi("works")[0])}. È un valore complessivo, che somma opere avviate in '
        'anni diversi e in fasi diverse: non è quanto si spende in un anno.')
    towns3 = {c: (f'<b>{esc(nm(c))}</b>: opere pubbliche monitorate per {eur(wk.values[c])} per abitante '
                  f'({ordinal(wk.rank(c))} su {total}).') for c in codes}
    ch3 = chapter(3, 'opere', 'Le opere pubbliche', 'Quanto valgono le opere pubbliche dei Comuni?',
        f'<p>{wk_text}</p>{bar_chart(wk, N, "Opere pubbliche monitorate per abitante")}' + town_blocks(towns3),
        'Il monitoraggio delle opere pubbliche registra ogni progetto con il suo codice unico, dal finanziamento alla '
        'fine dei lavori. Il valore per abitante dà un’idea del peso delle opere rispetto alla dimensione del Comune, '
        'ma non dice quante sono concluse né se i costi sono stati rispettati.')

    # 04 — gli investimenti nei bilanci
    cc, cp = m['capc'], m['capp']
    cc_text = (
        f'Nel {cc.period} i Comuni della Versilia hanno impegnato per investimenti <b>{eur(cc.versilia)} per '
        f'abitante</b>: da {eur(lo("capc")[1])} a {nm(lo("capc")[0])} a {eur(hi("capc")[1])} a '
        f'{nm(hi("capc")[0])}. Nello stesso anno hanno pagato per investimenti {eur(cp.versilia)} per abitante, da '
        f'{eur(lo("capp")[1])} a {nm(lo("capp")[0])} a {eur(hi("capp")[1])} a {nm(hi("capp")[0])}. Il dossier '
        '<a href="../bilanci/">I conti dei Comuni</a> legge il resto dei bilanci.')
    towns4 = {c: (f'<b>{esc(nm(c))}</b>: {eur(cc.values[c])} per abitante impegnati per investimenti nel {cc.period}, '
                  f'{eur(cp.values[c])} pagati.') for c in codes}
    ch4 = chapter(4, 'bilanci', 'Gli investimenti nei bilanci', 'Quanto spendono i Comuni per investire?',
        f'<p>{cc_text}</p>{bar_chart(cc, N, "Spesa per investimenti impegnata per abitante")}'
        f'{bar_chart(cp, N, "Pagamenti per investimenti per abitante")}' + town_blocks(towns4),
        'Gli impegni dicono quanto il Comune si è obbligato a spendere nell’anno; i pagamenti quanto è uscito davvero '
        'dalla cassa, anche per impegni presi negli anni precedenti. Un’opera grande può far salire molto un solo anno, '
        'quindi il dato va letto insieme agli anni vicini.')

    # 05 — fossi e canali
    pn_, pv, ps, pd = m['pabn'], m['pabv'], m['pabs'], m['pabd']
    zero = [c for c, v, _ in ps.ranking if v == 0]
    pab_text = (
        f'Nel {pn_.period} il piano delle attività di bonifica del Consorzio 1 Toscana Nord programma in Versilia '
        f'interventi di manutenzione ordinaria di fossi, canali e argini: da {num(lo("pabn")[1])} interventi a '
        f'{nm(lo("pabn")[0])} a {num(hi("pabn")[1])} a {nm(hi("pabn")[0])}, per un valore programmato che va da '
        f'{eur(lo("pabv")[1])} a {nm(lo("pabv")[0])} a {eur(hi("pabv")[1])} a {nm(hi("pabv")[0])}.')
    ps_text = (
        f'Al {period_label(ps.period)} il portale delle manutenzioni del Consorzio registra come conclusi '
        f'<b>{il(pct(ps.versilia))}</b> degli interventi presenti per la Versilia. La quota più alta è a {nm(hi("pabs")[0])} ({pct(hi("pabs")[1])})'
        + (f'; a {join_names([nm(c) for c in zero])} il portale non registra ancora lavori conclusi.' if zero else '.'))
    towns5 = {c: (f'<b>{esc(nm(c))}</b>: {num(pn_.values[c])} interventi programmati nel {pn_.period} per '
                  f'{eur(pv.values[c])}; {num(pd.values[c])} registrati come conclusi al {period_label(ps.period)} '
                  f'({pct(ps.values[c])}).') for c in codes}
    ch5 = chapter(5, 'fossi', 'Fossi e canali', 'Quanta manutenzione dei corsi d’acqua è programmata e quanta è fatta?',
        f'<p>{pab_text}</p>{bar_chart(pn_, N, "Interventi di manutenzione programmati")}'
        f'{bar_chart(pv, N, "Valore della manutenzione programmata")}'
        f'<p>{ps_text}</p>{bar_chart(ps, N, "Interventi registrati come conclusi", "Quota degli interventi presenti nel portale del Consorzio.")}'
        + town_blocks(towns5),
        'La manutenzione di fossi e canali la fa il Consorzio di bonifica, non il Comune, ma serve a ridurre gli '
        'allagamenti: il dossier <a href="../ambiente/">Ambiente e rischi in Versilia</a> mostra quanti residenti '
        'vivono nelle aree a pericolosità di alluvione. Il piano dice che cosa è programmato; lo stato dei lavori viene '
        'dal portale del Consorzio, che può essere aggiornato in ritardo, e una parte dei lavori si fa più avanti '
        'nell’anno.')

    key_points = [
        (num(pe_sum / 1e6, 1) + ' mln €', f'Fondi PNRR dei progetti di cui i sette Comuni sono attuatori, al {day}.', 'pnrr'),
        (eur(hi('pnrr')[1]), f'Fondi PNRR per abitante a {nm(hi("pnrr")[0])}, il valore più alto.', 'pnrr'),
        (pct(dn.versilia), f'Progetti PNRR dei Comuni nella fase «conclusione»: {num(dc_sum)} su {num(se_sum)}.',
         'avanzamento'),
        (eur(hi('works')[1]), f'Opere pubbliche monitorate per abitante a {nm(hi("works")[0])}.', 'opere'),
        (eur(cc.versilia), f'Spesa per investimenti impegnata per abitante in Versilia nel {cc.period}.', 'bilanci'),
        (pct(ps.versilia), f'Interventi di manutenzione di fossi e canali registrati come conclusi al '
                           f'{period_label(ps.period)}.', 'fossi'),
    ]
    towns_summary = {c: '<ul class="dr-town-list">' + ''.join([
        summary_item('Fondi PNRR per abitante', eur(pn.values[c]), f'Versilia {eur(pn.versilia)}'),
        summary_item('Progetti PNRR in fase di conclusione', pct(dn.values[c]),
                     f'{num(dc.values[c])} su {num(se.values[c])}'),
        summary_item('Opere pubbliche monitorate per abitante', eur(wk.values[c]), f'{ordinal(wk.rank(c))} su {total}'),
        summary_item('Investimenti impegnati per abitante', eur(cc.values[c]), f'Versilia {eur(cc.versilia)}'),
        summary_item('Manutenzioni di fossi e canali concluse', pct(ps.values[c]), f'Versilia {pct(ps.versilia)}'),
    ]) + '</ul>' for c in codes}
    unknown = [
        'Quanti progetti PNRR sono davvero finiti, collaudati e aperti al pubblico, e con quali risultati.',
        'Quanto sono costate alla fine le opere rispetto a quanto previsto, e con quali ritardi.',
        'Quali opere si trovano in ciascun Comune: i dati seguono l’ente responsabile, non il luogo dei lavori.',
        'Quanto si spende ogni anno per la manutenzione di strade, scuole ed edifici pubblici.',
        'Quanto la manutenzione di fossi e canali riduce davvero gli allagamenti.',
    ]
    return dict(
        slug='investimenti', title='Investimenti e opere in Versilia', eyebrow='Dossier · Investimenti, PNRR e opere',
        unknown_topic='sugli investimenti', theme='comunita', theme_label='Tutti i dati su comunità e welfare',
        lead='Quanti fondi del PNRR gestiscono i Comuni e a che punto sono i progetti, quante opere pubbliche sono '
             'monitorate, quanto investono i bilanci e quanta manutenzione di fossi e canali è programmata e fatta: '
             'una lettura dei dati pubblici sui sette Comuni della Versilia.',
        description='Fondi e avanzamento dei progetti PNRR, opere pubbliche monitorate, spesa per investimenti nei '
                    'bilanci e manutenzione di fossi e canali nei sette Comuni della Versilia.',
        periods=f'PNRR al {day}, opere pubbliche {wk.period}, bilanci {cc.period}, manutenzione di fossi e canali: piano '
                f'{pn_.period} e stato dei lavori al {period_label(ps.period)}.',
        method='Per questi dati non esiste un confronto ufficiale con Toscana e Italia. I fondi e il numero di progetti '
               'PNRR della Versilia sono la somma dei sette Comuni; per la manutenzione di fossi e canali non si somma '
               'nulla, perché un intervento può riguardare più Comuni.',
        measures=m, chapters=[ch1, ch2, ch3, ch4, ch5], key_points=key_points, towns_summary=towns_summary,
        unknown=unknown,
        toc=[('pnrr', 'I fondi del PNRR'), ('avanzamento', 'A che punto sono i progetti'), ('opere', 'Le opere pubbliche'),
             ('bilanci', 'Gli investimenti nei bilanci'), ('fossi', 'Fossi e canali')])


DOSSIERS = {'casa': casa, 'lavoro': lavoro, 'turismo': turismo, 'anziani': anziani, 'scuola': scuola, 'mobilita': mobilita, 'bilanci': bilanci, 'ambiente': ambiente, 'demografia': demografia, 'investimenti': investimenti}


# ---------------------------------------------------------------------------
# Pagina, CSV e PDF.

def limits() -> dict:
    return json.loads(LIMITS.read_text(encoding='utf-8').split('export default', 1)[1].strip().rstrip(';'))


def write_csv(dossier: dict, names: dict[str, str], path: Path) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Indicatore', 'Territorio', 'Periodo', 'Valore', 'Unità', 'Fonte'])
    unit = {'eur': 'euro', 'eurc': 'euro', 'eurm2': 'euro al m²', 'eurm2month': 'euro al m² al mese', 'percent': '%',
            'per1000': 'ogni 1.000 abitanti', 'decimal': 'persone', 'change': 'variazione %',
            'points': 'punti percentuali', 'per1000s': 'ogni 1.000 abitanti', 'count': 'numero', 'nights': 'notti',
            'per100': 'ogni 100 persone di 15-64 anni', 'years': 'anni', 'hours': 'ore', 'rate1000': 'ogni 1.000 abitanti', 'per1000old': 'ogni 1.000 residenti di 65 anni e più',
            'celsius': 'gradi centigradi', 'celsiusdelta': 'variazione in gradi centigradi', 'mm': 'millimetri',
            'kg': 'kg per abitante'}
    for measure in dossier['measures'].values():
        rows = [(names[c], v) for c, v, _ in measure.ranking]
        if measure.versilia is not None:
            rows.append(('Versilia', measure.versilia))
        rows += [(BENCH_LABEL[s], v) for s, v in measure.benchmarks.items()]
        for territory, value in rows:
            writer.writerow([measure.label, territory, period_label(measure.period),
                             num(value, 0 if measure.unit in ('eur', 'count') else max(measure.decimals, 2)).replace('.', ''),
                             unit[measure.unit], measure_source(measure)])
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
        link, items, cautions = sources.setdefault(measure_source(measure), (measure.source, [], []))
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
{shell.header}<div id="app"><main id="dossier" class="dr" data-dossier="{dossier['slug']}" data-dr-theme="{dossier['theme']}">
<header class="dr-hero"><div class="dr-wrap">
<nav class="dr-crumbs" aria-label="Percorso pagina"><a href="../../">Home</a> · <a href="../">Dossier</a></nav>
<p class="dr-eyebrow"><span class="dr-icon">{dossier_icon(dossier, 22)}</span>{esc(dossier['eyebrow'])}</p>
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
              'turismo, sugli anziani, sulla scuola, sulla mobilità, sui conti dei Comuni, sull’ambiente, sulla popolazione e sugli investimenti, per tutto il territorio e Comune per Comune.')


def index_card(d: dict) -> str:
    big, text, _ = d['key_points'][0]
    return (f'<li class="dr-card" data-dr-theme="{d["theme"]}"><a class="dr-card-link" href="{d["slug"]}/">'
            f'<p class="dr-eyebrow"><span class="dr-icon">{dossier_icon(d, 24)}</span>'
            f'{esc(d["eyebrow"].split(" · ", 1)[-1])}</p>'
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
                   'anziani, scuola, mobilità, bilanci comunali, ambiente, popolazione e investimenti.')
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
