"""Review-only composition of existing labour/income plans for seven towns.

No public routes, adapters, canonical cases or catalogs are changed. Queries
derive from existing verified case IDs; each expanded response is independently
checked before it can enter the report. The output is a derived review artifact.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from semantic_query_engine import ROOT, QueryEngine
from semantic_question_suite import check_expected
from semantic_methodological_checks import MethodologicalVerifier
from build_territorial_dossier_evidence import portable_evidence
from build_a7_static_pilot import encode
from a7_education_editorial import PUBLISHER, WEBSITE, LICENSE_URL, REUSE_NOTE, number

# Presentation choices reference the canonical plans; they are not an inventory
# of metric definitions or operations. Those remain in the engine/program.
COMPARISONS = ('census_employment_primary', 'business_asia_cumulative',
    'business_asia_employment', 'business_frame_industry_va',
    'business_frame_industry_wages', 'mef_incomeSourceProfile_total',
    'mef_incomeDistribution_total')
HISTORIES = ('business_frame_services_history', 'real_income_total_series_046018')
E = html.escape


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def build(catalog):
    engine = QueryEngine(catalog, layer='effective')
    verifier = MethodologicalVerifier(catalog, ROOT)
    program_path = ROOT/'ci/territorial-dossier-program.json'
    cases_path = ROOT/'ci/semantic-verified-questions.json'
    dossiers = {d['id']:d for d in json.loads(program_path.read_text())['dossiers']}
    canonical = {c['id']:c for c in json.loads(cases_path.read_text())['questions']}
    plans = [dossiers[key]['centralPlan'] for key in ('lavoro', 'redditi')]
    admitted = {ref for p in plans for ref in p['requiredCaseRefs']+p['contextCaseRefs']}
    if not set(COMPARISONS+HISTORIES) <= admitted:
        raise ValueError('work_plan_reference_changed')
    towns = {t['code']:t['name'] for t in engine.catalog['towns']}
    evidence = {}
    for cid in COMPARISONS+HISTORIES:
        original = canonical[cid]
        baseline = engine.query(original['query'])
        errors = check_expected(baseline,original['expected'])+verifier.verify(baseline)
        if errors:raise ValueError('work_unverified_baseline:'+cid+':'+str(errors))
        groups = [list(towns)] if cid in COMPARISONS else [[code] for code in towns]
        for codes in groups:
            query = copy.deepcopy(original['query'])
            query['selectors'][0]['towns'] = codes
            response = engine.query(query)
            errors = verifier.verify(response)
            if response['status']!='computed' or errors:
                raise ValueError('work_unverified_extension:'+cid+':'+str(errors))
            expected_codes = set(codes)
            if {o['geography'] for o in response['observations']} != expected_codes:
                raise ValueError('work_coverage_mismatch:'+cid)
            key = cid if cid in COMPARISONS else cid+':'+codes[0]
            evidence[key] = portable_evidence(dict(originCaseId=cid,query=query,response=response,
                reference=original['reference'],verification='PASS'))
    model = dict(schemaVersion=1,stage='review_only_not_public',
        title='Vivere e lavorare: attività, residenti e redditi',towns=towns,
        catalogSha256=engine.catalog_hash,engineSha256=engine.module_hash,
        programSha256=hashlib.sha256(program_path.read_bytes()).hexdigest(),
        casesSha256=hashlib.sha256(cases_path.read_bytes()).hexdigest(),evidence=evidence,
        sourcePlans=[p['id'] for p in plans],
        competences=dossiers['lavoro']['competences'],
        optionsToInvestigate=dossiers['lavoro']['optionsToInvestigate'],
        missingData=list(dict.fromkeys(g for key in ('lavoro','redditi')
            for g in dossiers[key]['centralPlan']['missingData'])),
        boundary='Residenti occupati, addetti sul luogo di lavoro e dichiaranti fiscali sono popolazioni diverse. '
            'Le misure conservano i propri periodi. I confronti descrittivi non identificano effetti delle politiche, '
            'transizioni individuali, reddito disponibile familiare o bisogno di sostegno.')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    date=datetime.fromisoformat(subprocess.check_output(['git','show','-s','--format=%cI',commit],cwd=ROOT,text=True).strip()).astimezone(timezone.utc)
    model.update(repositoryCommit=commit,editionDate=date.strftime('%d/%m/%Y'),pdfDate=date.strftime('%Y%m%d%H%M%S'),
        rendererSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        stylesheetSha256=hashlib.sha256((ROOT/'experiments/a7-work-income-preview/print.css').read_bytes()).hexdigest())
    labels={row['parts'][0]['label'] for row in engine.catalog['metrics']['incomeDistribution']['rows']}
    if len(labels)!=1:raise ValueError('work_income_macro_labels_differ')
    model['incomeMacroLabel']=labels.pop()
    model['priceIndexSource']=json.loads((ROOT/'data/source-snapshots/nic-italia-2016-2024.json').read_text())['sourceUrl']
    model['evidenceSha256'] = digest(evidence)
    validate(model)
    return model


def rows(model, cid, code=None):
    entry=model['evidence'][cid if code is None else cid+':'+code]
    if entry['verification']!='PASS':raise ValueError('work_unverified_evidence')
    return entry['response']['observations']


def focus(model,cid,code):
    found=[o for o in rows(model,cid) if o['geography']==code]
    if len(found)!=1:raise ValueError('work_focus_ambiguous')
    return found[0]


def validate(model):
    if digest(model['evidence'])!=model['evidenceSha256']:
        raise ValueError('work_evidence_integrity_mismatch')
    if len(model['towns'])!=7:raise ValueError('work_territories_mismatch')
    for cid in COMPARISONS:
        obs=rows(model,cid)
        if len(obs)!=7 or {o['geography'] for o in obs}!=set(model['towns']):
            raise ValueError('work_coverage_mismatch:'+cid)
        first=obs[0]
        for o in obs:
            if any(o[k]!=first[k] for k in ('metric','period','dimension','unit','population','definition','method','source')):
                raise ValueError('work_incomparable_rows:'+cid)
    for code in model['towns']:
        for cid in HISTORIES:
            obs=rows(model,cid,code)
            if not obs or {o['geography'] for o in obs}!={code}:
                raise ValueError('work_history_coverage_mismatch')
            periods=[o['period'] for o in obs]
            if periods!=sorted(set(periods)):
                raise ValueError('work_history_period_mismatch')
    return model


def source(o):
    host=urlparse(o['source']).hostname or ''
    publisher='MEF' if 'finanze.gov.it' in host else 'Istat'
    return f'<a href="{E(o["source"],quote=True)}">{publisher}</a>'


def chart(model,cid,code,title,note,suffix='',decimals=1):
    obs=rows(model,cid);valid=[o['value'] for o in obs if o['value'] is not None]
    if any(not math.isfinite(v) for v in valid):raise ValueError('work_nonfinite_value')
    signed=any(v<0 for v in valid)
    maximum=100 if cid=='census_employment_primary' else max([abs(v) for v in valid]+[1])
    scale=50 if signed else 100
    bars=[]
    for o in sorted(obs,key=lambda o:model['towns'][o['geography']]):
        v=o['value'];name=model['towns'][o['geography']]
        if v is None:graphic='<span class="missing">Non disponibile</span>'
        else:
            width=scale*abs(v)/maximum
            left=(50-width if v<0 else 50) if signed else 0
            graphic=f'<span class="track {"signed" if signed else ""}"><span class="bar {"negative" if v<0 else ""}" style="left:{left:.8f}%;width:{width:.8f}%" data-value="{v}"></span></span>'
        bars.append(f'<li class="{"focus" if o["geography"]==code else ""}"><span>{E(name)}</span>{graphic}<strong>{number(v,decimals)}{suffix if v is not None else ""}</strong></li>')
    domain=f'-{number(maximum,decimals)} a +{number(maximum,decimals)}' if signed else f'0 a {number(maximum,decimals)}'
    return f'<figure><h3>{E(title)}</h3><p>{E(note)}</p><small>{E(obs[0]["period"])} · {len(valid)} valori disponibili su 7</small><ul class="bars">'+''.join(bars)+f'</ul><small>Scala da {domain}{suffix}. Comuni in ordine alfabetico; {E(model["towns"][code])} evidenziato. Elaborazione: {PUBLISHER} · Fonte: {source(obs[0])}.</small></figure>'


def history(model,code):
    obs=rows(model,'real_income_total_series_046018',code)
    vals=[o['value'] for o in obs]
    if any(v is None for v in vals):raise ValueError('work_missing_history_not_interpolated')
    lo=min(vals+[0]);hi=max(vals+[0]);span=max(1,hi-lo)
    def y(v):return 130-100*(v-lo)/span
    points=' '.join(f'{30+i*57},{y(v):.4f}' for i,v in enumerate(vals))
    labels=''.join(f'<text x="{30+i*57}" y="155" text-anchor="middle">{E(o["period"])}</text>' for i,o in enumerate(obs))
    dots=''.join(f'<circle cx="{30+i*57}" cy="{y(v):.4f}" r="3"/><text x="{30+i*57}" y="{y(v)-9:.4f}" text-anchor="middle">{number(v)}%</text>' for i,v in enumerate(vals))
    return f'<figure><h3>Reddito imponibile medio e prezzi: il percorso dal 2016</h3><p>Variazione cumulata rispetto al 2016, corretta con l’indice nazionale dei prezzi NIC. Non è la variazione rispetto all’anno precedente.</p><svg viewBox="0 0 520 170" role="img" aria-label="Serie annuale del reddito imponibile medio corretto per NIC"><line x1="20" x2="500" y1="{y(0)}" y2="{y(0)}" stroke="#a8b9bd"/><polyline points="{points}" fill="none" stroke="#176c69" stroke-width="3"/>{dots}{labels}</svg><small>Popolazioni fiscali diverse fra anni; indice prezzi Italia, non prezzi locali o potere d’acquisto individuale. Elaborazione: {PUBLISHER} · Fonte: {source(obs[-1])} e Istat NIC.</small></figure>'


def chapters(model,code):
    validate(model)
    town=model['towns'][code]
    emp=focus(model,'census_employment_primary',code)
    change=focus(model,'business_asia_cumulative',code)
    employees=focus(model,'business_asia_employment',code)
    wages=focus(model,'business_frame_industry_wages',code)
    mef=focus(model,'mef_incomeSourceProfile_total',code)
    income=focus(model,'mef_incomeDistribution_total',code)
    services=model['evidence']['business_frame_services_history:'+code]['response']
    original=services['observations'];delta=services['result']['value']
    direction='aumentate' if change['value']>0 else 'diminuite' if change['value']<0 else 'rimaste stabili'
    cards=''.join(f'<div><span>{E(label)}</span><strong>{number(value,dec)}{suffix}</strong><small>{E(period)}</small></div>' for label,value,dec,suffix,period in [
        ('RESIDENTI CHE LAVORANO',emp['value'],1,'%',emp['period']+' · residenti 25–64 anni'),
        ('UNITÀ LOCALI ASIA',change['value'],1,'%',change['period']+' · variazione cumulata'),
        ('ADDETTI SUL TERRITORIO',employees['value'],2,'',employees['period']+' · media annua')])
    overview=f'<div class="opening"><h2>Tre prospettive sul cambiamento</h2><p>Un’attività che apre, una persona che trova lavoro, un reddito che cambia: sono aspetti collegati nella vita quotidiana, ma le statistiche li osservano da punti di vista diversi.</p></div><div class="cards">{cards}</div><p>A {E(town)} le unità locali ASIA sono {direction} nel periodo {E(change["period"])}. Il tasso di occupazione descrive invece i residenti nel {E(emp["period"])}: i due dati non dimostrano che le nuove attività abbiano creato lavoro per chi abita nel Comune.</p>'
    sections=[('sintesi','Vivere e lavorare a '+town,overview+chart(model,'census_employment_primary',code,'Quanto è diffuso il lavoro tra i residenti?','Occupati fra i residenti di 25–64 anni. Il confronto descrive questa fascia di età, non la disoccupazione né i posti di lavoro nel Comune.','%'))]
    sections.append(('attivita','Le attività e il lavoro sul territorio',
        chart(model,'business_asia_cumulative',code,'Come sono cambiate le unità locali','Variazione cumulata ASIA fra 2018 e 2023. I valori negativi indicano una diminuzione nello stesso intervallo.','%')+
        chart(model,'business_asia_employment',code,'Quanti addetti sono localizzati nel Comune?','Media annua ASIA per luogo di lavoro. Gli addetti possono risiedere altrove; i valori assoluti dipendono anche dalla dimensione del territorio.',decimals=2)))
    sections.append(('produzione','Industria e servizi: due letture della produzione',
        chart(model,'business_frame_industry_va',code,'Il valore aggiunto dell’industria','Milioni di euro nominali. È una misura della produzione localizzata Frame SBS, non il PIL comunale né una misura per residente.',' mln €',2)+
        f'<h3>Il cambiamento dei servizi a {E(town)}</h3><div class="endpoints"><div><span>{E(original[0]["period"])}</span><strong>{number(original[0]["value"],2)} mln €</strong></div><div><span>{E(original[-1]["period"])}</span><strong>{number(original[-1]["value"],2)} mln €</strong></div></div><p>La differenza nominale calcolata dal motore è <strong>{number(delta,2)} milioni di euro</strong>. Non è crescita a prezzi costanti e non dimostra passaggi di lavoratori fra industria e servizi.</p><small>Fonte {source(original[0])} e {source(original[-1])}. ASIA, Frame SBS e Registro Imprese hanno universi diversi: i loro stock non si sommano e non formano una serie unica.</small>'))
    sections.append(('retribuzioni','Retribuzioni e redditi da lavoro',
        chart(model,'business_frame_industry_wages',code,'La retribuzione media nell’industria','Retribuzione lorda per dipendente industriale nelle unità locali. Non descrive tutti gli occupati residenti né distribuzione, orario o durata dei contratti.',' €',0)+
        chart(model,'mef_incomeSourceProfile_total',code,'Il reddito dichiarato da lavoro dipendente e assimilati','MEF, anno d’imposta 2024. Ammontare della fonte lavoro dipendente e assimilati diviso per le frequenze dei contribuenti del Comune con quella fonte; non reddito disponibile familiare.',' €',0)))
    coverage=next(e['bandCoverage'] for e in income['evidence'] if 'bandCoverage' in e)
    missing=coverage['missingBandFrequencyCells']
    coverage_text=(f'Le celle di frequenza mancanti sono {missing}: restano mancanti, senza diventare zero. Il totale delle frequenze di reddito complessivo riportato separatamente è {number(coverage["reportedTotalIncomeFrequency"],0)}; la differenza con le frequenze note delle fasce è {number(coverage["differenceVsReportedTotal"],0)}, senza attribuirle una causa non dichiarata dalla fonte.' if missing else 'Le otto celle di frequenza delle fasce sono disponibili nella fonte per questo Comune.')
    sections.append(('redditi','Redditi, prezzi e informazioni che mancano',history(model,code)+
        f'<h3>Le fasce di reddito: una copertura da leggere</h3><p>A {E(town)} la quota della fascia «{E(model["incomeMacroLabel"])}» è <strong>{number(income["value"])}%</strong>, usando {number(income["numerator"],0)} frequenze note su {number(income["denominator"],0)} frequenze note. {coverage_text}</p><p>Il denominatore comprende soltanto le frequenze pubblicate disponibili. Non è una stima della povertà, delle famiglie a basso reddito o delle persone che necessitano di sostegno.</p><small>Anno d’imposta {E(income["period"])} · Fonte: {source(income)}. Per il sostegno alle famiglie servono anche composizione dei nuclei, ISEE, patrimonio, affitti e costi essenziali.</small>'))
    source_list=(f'<li>Istat, occupazione dei residenti · {E(emp["period"])} · {source(emp)}</li>'
        f'<li>Istat ASIA, unità locali e addetti · 2018–2023 · {source(change)}</li>'
        f'<li>Istat Frame SBS, industria/servizi · {source(original[0])} ({E(original[0]["period"])}) e {source(wages)} ({E(wages["period"])})</li>'
        f'<li>MEF, fonte lavoro dipendente e fasce · anno d’imposta {E(mef["period"])} · {source(mef)}</li>'
        f'<li>MEF, serie del reddito imponibile · 2016–2024 · {source(rows(model,"real_income_total_series_046018",code)[-1])}</li>'
        f'<li>Istat NIC, prezzi nazionali · 2016–2024 · <a href="{E(model["priceIndexSource"],quote=True)}">Istat NIC</a></li>')
    sections.append(('scelte','Dalle evidenze alle scelte',
        '<h3>Le domande da approfondire</h3><ul><li>Quali professionalità cercano le imprese e quali barriere incontrano i residenti?</li><li>Accessibilità, trasporti, orari e servizi alle famiglie limitano l’incontro fra domanda e offerta?</li><li>Quali nuclei affrontano costi essenziali non sostenibili, oltre quanto mostrano i redditi fiscali?</li></ul>'+
        '<h3>Chi coinvolgere</h3><p>'+E(model['competences'])+'</p><h3>Opzioni per l’istruttoria</h3><p>'+E(model['optionsToInvestigate'])+'</p>'+
        '<h3>Come verificare un eventuale intervento</h3><p>Definire destinatari, accessi, completamenti, esiti occupazionali a distanza e costi per partecipante. Raccogliere una baseline e un confronto adeguato: un miglioramento comunale prima/dopo, da solo, non dimostra l’effetto della politica.</p>'+
        '<h3>Che cosa non misuriamo ancora</h3><p>Qualità e durata dei contratti, profili richiesti, transizioni individuali, reddito disponibile dei nuclei, patrimonio e costi essenziali. Sono fabbisogni informativi, non dati già acquisiti.</p>'+
        '<details open><summary>Fonti, periodi e metodo</summary><ul>'+source_list+'</ul><p>'+E(model['boundary'])+'</p><p>Confronti fra i sette Comuni descrittivi: non sono territori certificati come equivalenti. Evidenze congelate, non congiuntura attuale. Nessuna graduatoria politica.</p></details>'))
    return sections


def report_html(model,code):
    town=model['towns'][code]
    logo=(ROOT/'assets/brand-mark.svg').read_text()
    sections=[]
    for index,(_,title,body) in enumerate(chapters(model,code)):
        brand=f'<header>{logo}<div><strong>{PUBLISHER}</strong><span>{WEBSITE}</span></div><b>{E(town)}<br>LAVORO E REDDITI</b></header>' if index==0 else f'<p class="kicker">{E(town.upper())} · LAVORO E REDDITI</p>'
        edition=f'<p class="edition">Bozza per revisione · Edizione del {model["editionDate"]}. Periodi dei dati indicati nelle singole misure.</p>' if index==0 else ''
        sections.append(f'<section>{brand}<h1>{E(title)}</h1>{edition}{body}</section>')
    sections[-1]=sections[-1].replace('</section>','<h3>Attribuzione e riuso</h3><p>'+E(REUSE_NOTE)+f' <a href="{LICENSE_URL}">CC BY 4.0</a>.</p><p>Pubblicazione civica indipendente. Bozza di composizione per revisione, non ancora integrata nella lettura pubblica A7. Per usi ufficiali consultare le fonti originarie.</p><small>Versione sorgente: {model["repositoryCommit"]}. Impronta delle evidenze: {model["evidenceSha256"]}. Richieste e provenienza integrali nel pacchetto di verifica allegato alla bozza.</small></section>')
    css=(ROOT/'experiments/a7-work-income-preview/print.css').read_text()
    return '<!doctype html><html lang="it"><meta charset="utf-8"><meta name="author" content="'+PUBLISHER+'"><title>'+E(town)+' - Lavoro e redditi</title><style>'+css+'</style><main>'+''.join(sections)+'</main></html>'


def write_reports(model,output):
    from playwright.sync_api import sync_playwright
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            for code,town in model['towns'].items():
                page=browser.new_page();page.set_content(report_html(model,code));page.emulate_media(media='print')
                path=output/('Lavoro-'+town.lower().replace(' ','-')+'.pdf')
                page.pdf(path=str(path),format='A4',print_background=True,tagged=True,
                    display_header_footer=True,margin={'top':'14mm','bottom':'17mm','left':'16mm','right':'16mm'},
                    header_template='<span></span>',footer_template=f'<div style="font:8px Arial;color:#405968;width:100%;margin:0 16mm;display:flex;justify-content:space-between"><span>{PUBLISHER} · {WEBSITE}<br>{E(town)} · Bozza lavoro e redditi</span><span>Pagina <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
                page.close()
                b=path.read_bytes();b=re.sub(rb'/(CreationDate|ModDate) \(D:\d{14}\+00\x27?00\x27?\)',lambda m:b'/'+m[1]+b" (D:"+model['pdfDate'].encode()+b"+00'00')",b);path.write_bytes(b)
        finally:browser.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--pdf',action='store_true');args=p.parse_args()
    model=build(args.catalog);args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'work-income.json').write_text(encode(model))
    if args.pdf:write_reports(model,args.output_dir)
    print(encode(dict(status='PASS',towns=len(model['towns']),requests=len(model['evidence']),evidenceSha256=model['evidenceSha256'],scope='review only; no public integration')))


if __name__=='__main__':main()
