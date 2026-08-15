#!/usr/bin/env python3
"""Extract/audit municipal MEF average income, tax years 2011-2024."""
from __future__ import annotations
import argparse,csv,io,json,re,unicodedata,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL=('https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
     'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.zip')
TOWNS=['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']
MISSING={'','-','n.d.','nd'}

def norm(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if not unicodedata.combining(c)).lower().strip()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def stem(h):
    # Older MEF files append "in euro" to amount columns but not frequency columns.
    return re.sub(r' (ammontare(?: in euro)?|importo(?: in euro)?|frequenza|numero)$','',norm(h))

def decode(raw):
    for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
        try:return raw.decode(enc)
        except UnicodeDecodeError:pass
    raise RuntimeError('encoding CSV MEF non riconosciuto')

def clean(v):return (v or '').strip().replace('\u00a0','').replace(' ','').lower()

def num(v):
    s=clean(v)
    if s in MISSING:raise ValueError(f'valore mancante {v!r}')
    if ',' in s and '.' in s:s=s.replace('.','').replace(',','.')
    elif ',' in s:s=s.replace(',','.')
    return float(s)

def paired(amount_raw,frequency_raw,year,town,label):
    am=clean(amount_raw) in MISSING; fm=clean(frequency_raw) in MISSING
    if am and fm:return 0.0,0
    if am!=fm:raise RuntimeError(f'{year} {town} {label}: coppia incompleta {amount_raw!r}/{frequency_raw!r}')
    amount=num(amount_raw); frequency=int(round(num(frequency_raw)))
    # Amount can be negative in the official <=0 income class; frequency cannot.
    if frequency<0:raise RuntimeError(f'{year} {town} {label}: frequenza negativa')
    return amount,frequency

def town_header(headers):
    nn={h:norm(h) for h in headers}; exact=[h for h,n in nn.items() if n in {'denominazione comune','denominazione del comune','comune'}]
    if exact:return exact[0]
    c=[h for h,n in nn.items() if 'comune' in n and 'codice' not in n]
    if len(c)!=1:raise RuntimeError(f'colonna comune ambigua: {c}')
    return c[0]

def province_header(headers):
    nn={h:norm(h) for h in headers}; c=[h for h,n in nn.items() if n in {'sigla provincia','provincia'}]
    return c[0] if c else None

def income_columns(headers):
    nn={h:norm(h) for h in headers}
    direct_amount=[h for h,n in nn.items() if n in {'reddito complessivo ammontare','reddito complessivo ammontare in euro','reddito complessivo importo','reddito complessivo importo in euro'}]
    direct_freq=[h for h,n in nn.items() if n in {'reddito complessivo frequenza','reddito complessivo numero'}]
    class_amount=[h for h,n in nn.items() if n.startswith('reddito complessivo ') and (' ammontare' in n or ' importo' in n) and h not in direct_amount]
    class_freq=[h for h,n in nn.items() if n.startswith('reddito complessivo ') and (' frequenza' in n or ' numero' in n) and h not in direct_freq]
    if len(direct_amount)>1 or len(direct_freq)>1:raise RuntimeError('totale reddito complessivo ambiguo')
    if bool(direct_amount)!=bool(direct_freq):raise RuntimeError('totale reddito complessivo incompleto')
    if not (direct_amount and direct_freq) and not (class_amount and class_freq):raise RuntimeError('reddito complessivo non ricostruibile')
    if class_amount or class_freq:
        aa={stem(h) for h in class_amount}; ff={stem(h) for h in class_freq}
        if aa!=ff:raise RuntimeError(f'classi non allineate; solo ammontare={sorted(aa-ff)}; solo frequenza={sorted(ff-aa)}')
    return (direct_amount[0] if direct_amount else None,direct_freq[0] if direct_freq else None,class_amount,class_freq)

def read_year(year):
    url=URL.format(year=year); req=urllib.request.Request(url,headers={'User-Agent':'OsservatorioVersilia-data-audit/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r:payload=r.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        members=[n for n in z.namelist() if n.lower().endswith(('.csv','.txt'))]
        if len(members)!=1:raise RuntimeError(f'{year}: file archivio inattesi {members}')
        member=members[0];text=decode(z.read(member))
    try:delim=csv.Sniffer().sniff(text[:10000],delimiters=';,\t|').delimiter
    except csv.Error:delim=';'
    reader=csv.DictReader(io.StringIO(text),delimiter=delim);headers=reader.fieldnames or [];th=town_header(headers);ph=province_header(headers)
    try:da,df,ca,cf=income_columns(headers)
    except Exception as exc:raise RuntimeError(f'{year}: {exc}; colonne={[h for h in headers if "reddito complessivo" in norm(h)]}') from exc
    cf_by={stem(h):h for h in cf};wanted={norm(t):t for t in TOWNS};found={};equivalence=[]
    for row in reader:
        town=wanted.get(norm(row.get(th,'')))
        if not town:continue
        if ph and norm(row.get(ph,'')) not in {'lu','lucca'}:continue
        class_amount=class_frequency=None
        if ca:
            class_amount=0.0;class_frequency=0
            for ah in ca:
                label=stem(ah);a,f=paired(row.get(ah,''),row.get(cf_by[label],''),year,town,label);class_amount+=a;class_frequency+=f
        if da and df:
            amount=num(row.get(da,''));frequency=int(round(num(row.get(df,''))); method='direct-total'
            if ca:
                ad=round(amount-class_amount,6);fd=frequency-class_frequency;equivalence.append({'town':town,'amountDelta':ad,'frequencyDelta':fd})
                if abs(ad)>0.01 or fd!=0:raise RuntimeError(f'{year} {town}: totale != somma classi ({ad}; {fd})')
        else:amount=class_amount;frequency=class_frequency;method='sum-income-classes'
        if amount is None or not frequency or frequency<=0:raise RuntimeError(f'{year} {town}: totale non valido')
        found[town]={'amount':amount,'frequency':frequency,'average':round(amount/frequency,2)}
    missing=[t for t in TOWNS if t not in found]
    if missing:raise RuntimeError(f'{year}: comuni mancanti {missing}')
    return {'year':year,'url':url,'archiveMember':member,'delimiter':delim,'method':'direct-total' if da else 'sum-income-classes','headers':{'town':th,'province':ph,'directAmount':da,'directFrequency':df,'classAmounts':ca,'classFrequencies':cf},'equivalenceChecks':equivalence,'towns':found}

def current_income():
    data=json.loads((ROOT/'data/site-data.json').read_text(encoding='utf-8'));out={}
    for row in data['metrics']['income']['rows']:out[row['town']]={int(y):float(v) for y,v in zip(row['series']['years'],row['series']['values'])}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=2011);p.add_argument('--end',type=int,default=2024);p.add_argument('--out',type=Path,default=Path('/tmp/mef-income-history.json'));a=p.parse_args()
    years=[read_year(y) for y in range(a.start,a.end+1)];current=current_income();towns={t:{str(x['year']):x['towns'][t] for x in years} for t in TOWNS};checks=[]
    for y in (2023,2024):
        if a.start<=y<=a.end:
            for t in TOWNS:
                ext=towns[t][str(y)]['average'];cur=current.get(t,{}).get(y);delta=None if cur is None else round(ext-cur,2)
                checks.append({'town':t,'year':y,'extracted':ext,'current':cur,'delta':delta,'status':'no-current-value' if cur is None else ('match' if abs(delta)<=0.02 else 'mismatch')})
    snap={'schemaVersion':6,'source':'Dipartimento delle Finanze - MEF','definition':'Reddito complessivo - Ammontare / Reddito complessivo - Frequenza','taxYears':[x['year'] for x in years],'schemaByYear':{str(x['year']):{k:x[k] for k in ('url','archiveMember','delimiter','method','headers','equivalenceChecks')} for x in years},'towns':towns,'checksAgainstCurrentSite':checks}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    mism=[c for c in checks if c['status']=='mismatch']
    print(f'MEF income audit: {a.start}-{a.end}; '+', '.join(f"{x["year"]}={x["method"]}" for x in years))
    for t in TOWNS:print(t+': '+', '.join(f"{y}:{towns[t][str(y)]['average']:.2f}" for y in range(a.start,a.end+1)))
    print(f'Checks existing 2023/2024: {len(checks)-len(mism)} ok, {len(mism)} mismatch; snapshot={a.out}')
    if mism:print(json.dumps(mism,ensure_ascii=False,indent=2));raise SystemExit(2)
if __name__=='__main__':main()
