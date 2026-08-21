#!/usr/bin/env python3
import unittest
from datetime import date
import opportunity_radar_v025 as v025
class T(unittest.TestCase):
 def setUp(self):self.c={'sources':{'official':{'priority':100},'mirror':{'priority':50}}}
 def item(self,s,title='Bando test',deadline='2026-09-30'):return {'source_id':s,'title':title,'deadline_at':deadline,'url':f'https://{s}.test/bando','municipality_eligibility':{'Massarosa':{'status':'eligible','reason':'ok'}},'presentation':{'source_label':s}}
 def test_dedup_prefers_primary(self):
  r,s=v025.deduplicate([self.item('mirror'),self.item('official')],self.c);self.assertEqual(len(r),1);self.assertEqual(r[0]['source_id'],'official');self.assertEqual(set(r[0]['also_seen_in']),{'official','mirror'});self.assertEqual(s['recordsCollapsed'],1)
 def test_deadline_prevents_false_dedup(self):self.assertEqual(len(v025.deduplicate([self.item('official',deadline='2026-09-30'),self.item('mirror',deadline='2026-10-30')],self.c)[0]),2)
 def test_future_disappearance_hold(self):
  a,h=v025.harden_continuity([],{'opportunities':[self.item('official')],'archive':[]},date(2026,8,22));self.assertEqual(a,[]);self.assertEqual(len(h),1)
 def test_expired_archives(self):
  a,h=v025.harden_continuity([],{'opportunities':[self.item('official',deadline='2026-08-20')],'archive':[]},date(2026,8,22));self.assertEqual(h,[]);self.assertEqual(len(a),1)
 def test_reopen_removes_archive(self):
  x=self.item('official');old=v025._archive_compact(x,date(2026,8,20));a,h=v025.harden_continuity([x],{'archive':[old]},date(2026,8,22));self.assertEqual((a,h),([],[]))
 def test_overlay_0_6(self):
  rules,_=v025.load_overlay();p,r=v025.predict_backtest_case({'source_id':'regione-toscana','title':'Anno educativo e scolastico 2026-2027, contributi ai Comuni per percorsi formativi per la qualità del Sistema integrato 0-6 anni'},rules);self.assertEqual(p,'operational');self.assertEqual(r,'rt-sistema-integrato-0-6-2026')
 def test_backtest_threshold_and_known_gap(self):
  rules,_=v025.load_overlay();r=v025.run_backtest(v025.DEFAULT_BACKTEST,rules);self.assertTrue(r['passed']);self.assertGreaterEqual(r['precision'],.95);self.assertGreaterEqual(r['recall'],.85);self.assertIn('Bando per contributo a musei ed ecomusei di rilevanza regionale 2026',{x['title'] for x in r['unresolved']})
 def test_coverage(self):
  reg=v025.load_json(v025.DEFAULT_COVERAGE);run={'sources':[{'sourceId':'regione-toscana','status':'ok','freshness':{'status':'current'}},{'sourceId':'fondazione-cr-lucca','status':'ok','freshness':{'status':'current'}},{'sourceId':'pa-digitale-2026','status':'ok','freshness':{'status':'stale'}}]};c=v025.build_coverage(run,reg);self.assertEqual(c['summary']['healthyActive'],2);self.assertEqual(c['summary']['degraded'],1);self.assertGreaterEqual(c['summary']['planned'],4)
if __name__=='__main__':unittest.main()
