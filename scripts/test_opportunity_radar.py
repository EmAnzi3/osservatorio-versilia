#!/usr/bin/env python3
from __future__ import annotations
import json,tempfile,unittest
from datetime import date
from pathlib import Path
import opportunity_radar as radar

TOWNS=['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']
REGION='''<h3><a href="/amianto">Bando Amianto Edifici Pubblici 2026</a></h3><p>Contributi destinati agli Enti Locali. Dotazione: ... euro. Scadenza presentazione domande 31.08.2026.</p><h3><a href="/voucher">Voucher</a></h3><p>Bando rivolto ai liberi professionisti. Scadenza presentazione domande 15.09.2026.</p><h3><a href="/generic">Premialità ai Poli Tecnici Professionali 2026</a></h3><p>Scadenza presentazione domande 12.10.2026.</p>'''
FOND='''<script type="application/ld+json">{"@graph":[{"@type":["Grant","CreativeWork"],"name":"Bando 2026 Progett-Azioni","url":"https://x/sociale","description":"Progettazione sociale degli enti pubblici.","datePublished":"2026-06-16","expires":"2026-09-11"},{"@type":["Grant","CreativeWork"],"name":"Bando 2026 Progettare per il futuro &#8211; opere pubbliche","url":"https://x/opere","description":"Progettazione di opere pubbliche.","datePublished":"2026-06-15","expires":"2026-09-11"}]}</script><h2>INFORMAZIONI E CONTATTI</h2>'''
DETAIL={'https://x/sociale':'<p>Partnership di soggetti pubblici e privati del Terzo settore.</p>','https://x/opere':'<p>Amministrazioni pubbliche locali della Provincia di Lucca; Unioni dei Comuni. Importo massimo € 30.000.</p>'}
PAD=json.dumps([{'titolo':'Cloud - Comuni','misura':'Cloud','data_inizio_bando':'2026-09-01','data_fine_bando':'2026-11-30','stato':'APERTO','totale_importo_stanziato':10000000,'soggetti_destinatari':'Comuni'},{'titolo':'Cloud - Scuole','misura':'Cloud','data_inizio_bando':'2026-09-01','data_fine_bando':'2026-11-30','stato':'APERTO','totale_importo_stanziato':1,'soggetti_destinatari':'Scuole'}])

class OpportunityRadarTest(unittest.TestCase):
 def setUp(self):self.today=date(2026,8,21)
 def src(self,id,name='X',typ=None):return {'id':id,'name':name,'publisher':name,'url':'https://x/list','_towns':TOWNS,**({'type':typ} if typ else {})}
 def test_dates(self):self.assertEqual(radar.parse_date('11 Settembre 2026'),date(2026,9,11));self.assertEqual(radar.parse_date('31.08.2026'),date(2026,8,31))
 def test_money_parser_never_crashes_on_punctuation(self):self.assertEqual(radar.money('Dotazione: ... euro'),(None,None));self.assertEqual(radar.money('Budget € 2,5 milioni'),(2500000.0,None));self.assertEqual(radar.money('Importo massimo € 30.000'),(None,30000.0))
 def test_regione_filter_is_conservative(self):
  x=radar.collect_html(self.src('rt'),self.today,REGION);self.assertEqual([i['title'] for i in x],['Bando Amianto Edifici Pubblici 2026','Premialità ai Poli Tecnici Professionali 2026']);self.assertEqual(x[0]['eligibility'],'eligible');self.assertEqual(x[1]['eligibility'],'review')
 def test_fondazione_uses_jsonld_and_detail_eligibility(self):
  s=self.src('fcrl');s['detailEnrichment']=True;x=radar.collect_grants(s,self.today,FOND,lambda u:DETAIL[u]);self.assertEqual(len(x),2);by={i['title']:i for i in x};self.assertEqual(by['Bando 2026 Progett-Azioni']['eligibility'],'conditional');op=next(i for i in x if 'opere pubbliche' in i['title']);self.assertEqual(op['eligibility'],'eligible');self.assertEqual(op['deadline_at'],'2026-09-11');self.assertEqual(op['max_contribution_eur'],30000.0);self.assertNotIn('INFORMAZIONI E CONTATTI',by)
 def test_padigitale_uses_official_beneficiary_field(self):
  x=radar.collect_pad(self.src('pad'),self.today,PAD);self.assertEqual(len(x),1);self.assertEqual(x[0]['eligibility'],'eligible');self.assertEqual(x[0]['funding_total_eur'],10000000.0);self.assertEqual(x[0]['themes'],['digitale'])
 def test_run_combines_sources(self):
  cfg={'schemaVersion':1,'municipalities':TOWNS,'sources':[{'id':'rt','name':'RT','publisher':'RT','url':'https://x/rt','type':'html_cards'},{'id':'f','name':'F','publisher':'F','url':'https://x/f','type':'jsonld_grants','detailEnrichment':True},{'id':'p','name':'P','publisher':'P','url':'https://x/p','type':'padigitale_json'}]}
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'c.json';path.write_text(json.dumps(cfg));r=radar.run(path,self.today,{'rt':REGION,'f':FOND,'p':PAD},DETAIL)
  self.assertEqual(r['counts']['total'],5);self.assertEqual(r['counts']['eligible'],3);self.assertEqual(r['counts']['conditional'],1);self.assertEqual(r['counts']['review'],1);self.assertTrue(all(s['status']=='ok' for s in r['sources']))

if __name__=='__main__':unittest.main()
