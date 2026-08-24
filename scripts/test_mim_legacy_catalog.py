#!/usr/bin/env python3
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import re, html

home='https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Edilizia%20Scolastica'
req=Request(home,headers={'User-Agent':'Mozilla/5.0'})
with urlopen(req,timeout=60) as r:
    text=r.read().decode('utf-8',errors='replace')
    print('HOME',r.status,r.geturl(),r.headers.get('Content-Type'),len(text))
links=[]
for m in re.finditer(r'''href\s*=\s*["']([^"']+\.csv[^"']*)["']''',text,re.I):
    href=html.unescape(m.group(1))
    links.append(urljoin(home,href))
print('CSV_LINKS',len(links))
for u in links:
    if '202425' in u and any(c in u for c in ['EDIANAGRAFESTA2021','EDICONSICUREZZASTA2021','EDISUPBARARCSTA2021','EDIAMBFUNZSTA2021','EDIETAORIGINESTA2021','EDICOLLEGAMENTISTA2021']):
        print('MATCH',u)
        req=Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':home})
        with urlopen(req,timeout=60) as r:
            head=r.read(600)
            print('RESP',r.status,r.geturl(),r.headers.get('Content-Type'),r.headers.get('Content-Length'),repr(head[:250]))
