#!/usr/bin/env python3
from __future__ import annotations
import unittest
import opportunity_radar_v03 as radar

class RadarV03Test(unittest.TestCase):
    def test_specialized_regional_sources_reuse_regione_rules(self):
        rules,_,aliases=radar.load_rules();original=radar.v021.matching_rule
        def alias_match(item,selected_rules=None):
            working=dict(item);sid=str(working.get('source_id') or '')
            if sid in aliases: working['source_id']=aliases[sid]
            return original(working,selected_rules)
        radar.v021.matching_rule=alias_match
        try: rule=radar.v021.matching_rule({'source_id':'regione-toscana-fse','title':'Anno educativo e scolastico 2026-2027, contributi ai Comuni per percorsi formativi per la qualità del "Sistema integrato 0-6 anni"'},rules)
        finally: radar.v021.matching_rule=original
        self.assertIsNotNone(rule);self.assertEqual(rule['id'],'rt-sistema-integrato-0-6-2026')

    def test_backtest_v03_passes_and_tests_source_aliases(self):
        rules,_,aliases=radar.load_rules();original=radar.v021.matching_rule
        def alias_match(item,selected_rules=None):
            working=dict(item);sid=str(working.get('source_id') or '')
            if sid in aliases: working['source_id']=aliases[sid]
            return original(working,selected_rules)
        radar.v021.matching_rule=alias_match
        try: report=radar.v025.run_backtest(radar.DEFAULT_BACKTEST,rules)
        finally: radar.v021.matching_rule=original
        self.assertTrue(report['passed']);self.assertEqual(next(x for x in report['rows'] if x['id']=='p14')['prediction'],'operational');self.assertEqual(next(x for x in report['rows'] if x['id']=='n12')['prediction'],'non_operational')

    def test_discovery_candidates_are_internal_only(self):
        source={'id':'anci-toscana','label':'ANCI Toscana','publisher':'ANCI Toscana','territory':'Toscana','includeTerms':['bando','contribut'],'municipalTerms':['comun','edifici pubblici']}
        html='<h3><a href="/bando-test/">Bando edifici pubblici per i Comuni</a></h3><p>Contributi per interventi di riqualificazione.</p><h3><a href="/notizia/">Convegno regionale</a></h3><p>Una giornata di studio.</p>'
        rows=radar.discovery_candidates(source,html,'https://ancitoscana.it/');self.assertEqual(len(rows),1);self.assertTrue(rows[0]['discovery_only']);self.assertEqual(rows[0]['status'],'internal_review')

    def test_coverage_counts_discovery_without_publication(self):
        registry={'sources':{'regione-toscana':{'label':'Regione Toscana','monitoringStatus':'active','role':'primary'},'gse':{'label':'GSE','monitoringStatus':'active','role':'discovery','favicon':'https://www.gse.it/favicon.ico'}},'plannedSources':[]}
        result={'sources':[{'sourceId':'regione-toscana','status':'ok','freshness':{'status':'current','observedDate':'2026-08-22'}}]}
        coverage=radar.build_coverage(result,registry,[{'sourceId':'gse','status':'ok','freshness':{'status':'discovery'}}]);self.assertEqual(coverage['summary']['active'],2);self.assertEqual(coverage['summary']['healthyActive'],2);self.assertEqual(coverage['summary']['discovery'],1)

    def test_source_visuals_attach_favicon(self):
        result={'opportunities':[{'source_id':'regione-toscana-fesr','presentation':{'source_label':'Regione Toscana'}}], 'archive':[]};radar.attach_source_visuals(result,radar.DEFAULT_PRESENTATION);p=result['opportunities'][0]['presentation'];self.assertIn('favicon.ico',p['source_favicon']);self.assertIn('FESR',p['source_label'])

if __name__=='__main__': unittest.main()
