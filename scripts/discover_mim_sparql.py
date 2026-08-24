#!/usr/bin/env python3
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import re, html

BASE='https://dati.istruzione.it/opendata/opendata/sparql/endpoint/'
CODES=['EDIANAGRAFESTA2021','EDICONSICUREZZASTA2021','EDISUPBARARCSTA2021','EDIAMBFUNZSTA2021','EDIETAORIGINESTA2021','EDICOLLEGAMENTISTA2021']

def get(url):
    req=Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', errors='replace')

text=get(BASE)
for code in CODES:
    print('\n===',code,'===')
    for m in re.finditer(r'''href\s*=\s*["']([^"']+)["']''', text, re.I):
        href=html.unescape(m.group(1))
        if code.lower() in href.lower():
            u=urljoin(BASE,href)
            print('LINK',u)
            page=get(u)
            for i,line in enumerate(page.splitlines()):
                low=line.lower()
                if any(k in low for k in ('textarea','sparql','endpoint','exportservlet','ajax','form','dataset=')):
                    if 'head' in low and len(line)>5000:
                        continue
                    print(f'{i+1}: {line[:2500]}')
            break
