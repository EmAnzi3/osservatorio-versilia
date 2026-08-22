#!/usr/bin/env python3
from __future__ import annotations
import unittest
import build_opportunity_preview_v03 as v03
import build_opportunity_preview as old

def item(source='regione-toscana'):
 label='Fondazione Cassa di Risparmio di Lucca' if source=='fondazione-cr-lucca' else 'Regione Toscana';fav='https://www.fondazionecarilucca.it/favicon.ico' if source=='fondazione-cr-lucca' else 'https://www.regione.toscana.it/favicon.ico'
 return {'title':'Bando test','source_id':source,'source_name':label,'publisher':label,'url':'https://example.test/bando','deadline_at':'2026-09-30','deadline_time':'13:00','eligibility':'eligible','access_mode':'direct','applicant_type':'comune','municipality_role':'direct_applicant','geographic_scope':'toscana','final_beneficiaries':'comunita locale','project_requirements':'','presentation':{'source_label':label,'source_mark':'FCRL' if source=='fondazione-cr-lucca' else 'RT','source_class':'fondazione' if source=='fondazione-cr-lucca' else 'regione','source_favicon':fav,'category':'ambiente','description':'Breve descrizione'},'municipality_eligibility':{town:{'status':'eligible','reason':'Ammesso'} for town in old.TOWNS}}
def payload():
 return {'referenceDate':'2026-08-22','opportunities':[item(),item('fondazione-cr-lucca')],'archive':[],'sourceCoverage':{'summary':{'configured':9,'active':8,'degraded':1},'rows':[{'source_id':'regione-toscana','label':'Regione Toscana','monitoringStatus':'active','role':'primary','runtimeStatus':'ok','favicon':'https://www.regione.toscana.it/favicon.ico'},{'source_id':'gse','label':'GSE','monitoringStatus':'active','role':'discovery','runtimeStatus':'ok','favicon':'https://www.gse.it/favicon.ico'},{'source_id':'pa-digitale-2026','label':'PA Digitale 2026','monitoringStatus':'degraded','role':'supplementary','runtimeStatus':'ok','favicon':'https://www.padigitale2026.gov.it/favicon.ico'}]},'discoveryQueue':[{'title':'Interno'}]}
class PreviewV03Test(unittest.TestCase):
 def test_dynamic_overview_and_monitoring(self):
  page=v03.render_page(payload());self.assertIn('Anteprima v0.3',page);self.assertIn('op-overview-shell',page);self.assertEqual(page.count('class="op-stat '),4);self.assertIn('>9<',page);self.assertIn('GSE',page);self.assertIn('Discovery',page)
 def test_favicons_and_quick_filters(self):
  page=v03.render_page(payload());self.assertIn('https://www.regione.toscana.it/favicon.ico',page);self.assertIn('op-source-fallback',page);self.assertIn('data-op-source-quick="regione-toscana"',page);self.assertIn('data-op-source-quick="fondazione-cr-lucca"',page)
 def test_icons_are_added_to_operational_fields(self):
  page=v03.render_page(payload());self.assertGreaterEqual(page.count('class="op-meta-icon"'),8);self.assertIn('30/09/2026 · ore 13:00',page)
 def test_internal_discovery_is_not_rendered(self):
  page=v03.render_page(payload());self.assertNotIn('>Interno<',page);self.assertNotIn('Quality gate',page);self.assertNotIn('Da verificare',page)
if __name__=='__main__':unittest.main()
