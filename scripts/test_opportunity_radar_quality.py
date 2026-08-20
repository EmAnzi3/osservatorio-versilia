#!/usr/bin/env python3
from datetime import date
import unittest
import opportunity_radar_quality as quality

TOWNS=['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']

class OpportunityRadarQualityTest(unittest.TestCase):
 def test_region_uses_only_beneficiary_section(self):
  source={'id':'rt','name':'RT','publisher':'RT','url':'https://x/list','_towns':TOWNS,'detailEnrichment':True}
  listing='<h3><a href="/pmi">Bando PMI</a></h3><p>Scadenza presentazione domande 30.09.2026.</p><h3><a href="/park">Bando parcheggi</a></h3><p>Scadenza presentazione domande 30.11.2026.</p><h3>Risultati: 166 Bandi</h3>'
  detail={'https://x/pmi':'<h2>Destinatari / beneficiari del bando</h2><p>PMI e imprese.</p>','https://x/park':'<h2>Destinatari / beneficiari del bando</h2><p>Comuni della Toscana.</p>'}
  items=quality.collect_html(source,date(2026,8,21),listing,lambda u:detail[u])
  self.assertEqual(len(items),1);self.assertEqual(items[0]['title'],'Bando parcheggi');self.assertEqual(items[0]['eligibility'],'eligible')

 def test_footer_does_not_contaminate_fondazione(self):
  source={'id':'f','name':'F','publisher':'F','url':'https://x/f','_towns':TOWNS,'detailEnrichment':True}
  listing='<script type="application/ld+json">{"@type":"Grant","name":"Progett-Azioni","url":"https://x/social","description":"Progettazione sociale degli enti pubblici.","datePublished":"2026-06-16","expires":"2026-09-11"}</script>'
  detail='<h2>Destinatari</h2><p>Partnership di soggetti pubblici e privati.</p><footer>Comuni e territori</footer>'
  items=quality.collect_grants(source,date(2026,8,21),listing,lambda u:detail)
  self.assertEqual(items[0]['eligibility'],'conditional')

if __name__=='__main__':unittest.main()
