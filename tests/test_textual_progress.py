"""Realistic regressions for V0.7.1 text-quantity progress alignment."""
import copy
import time
import unittest

from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import (create_pair_session, add_pair_link,
    pair_progress, replace_revisable_pair_proposals, physical_lines)
from varians_synchro.textual_progress import (_chars, _weights, _partition,
    suggest_textual_progress)
from test_reading_stream import add_test_page


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.p = new_project('Quantite')
        self.a = create_witness(self.p, 'Mu')
        self.b = create_witness(self.p, 'F')
        add_test_page(self.a, '1v', 'a1', [('c1', ['start','x'*90, 'x'*20,'x'*90,'x'*60,'end'])])
        add_test_page(self.b, '4v', 'b1', [('c1', ['start','y'*32, 'y'*35,'y'*28,'y'*34,
                                                   'y'*33,'y'*31,'y'*36,'y'*31,'end'])])
        self.s = create_pair_session(self.p,'Mu','F')
        self.al = physical_lines(self.a)
        self.bl = physical_lines(self.b)
        add_pair_link(self.p,self.s,[self.al[0]['id']],[self.bl[0]['id']])
        add_pair_link(self.p,self.s,[self.al[-1]['id']],[self.bl[-1]['id']])

    def test_exact_coverage_and_line_length_without_geometry_competition(self):
        data = suggest_textual_progress(self.p,self.s)
        self.assertEqual(data['calculated_intervals'],1)
        self.assertEqual((data['reference_covered'],data['target_covered']),(4,8))
        self.assertEqual([len(p['target_ids']) for p in data['proposals']],[3,1,2,2])
        self.assertTrue(all(g['evidence']['reference_method']=='htr' for g in data['proposals']))
        self.assertTrue(all(g['state']=='uncertain' for g in data['proposals']))
        self.assertEqual(len({uid for p in data['proposals'] for uid in p['target_ids']}),8)

    def test_manual_and_validated_groups_never_overwritten(self):
        old = add_pair_link(self.p,self.s,[self.al[2]['id']],[self.bl[4]['id']],
                            state='uncertain',origin='manual')
        snapshot = copy.deepcopy(self.s['links'])
        result = suggest_textual_progress(self.p,self.s)
        self.assertEqual(snapshot,self.s['links'])
        self.assertTrue(result['proposals'])
        self.assertFalse(any(self.al[2]['id'] in x['reference_ids'] for x in result['proposals']))
        self.assertFalse(any(self.bl[4]['id'] in x['target_ids'] for x in result['proposals']))
        saved = replace_revisable_pair_proposals(self.p,self.s,result['proposals'])
        self.assertGreater(saved['added'],0)
        self.assertIn(old['id'],[x['id'] for x in self.s['links']])
        self.assertEqual(len([x for x in self.s['links'] if x['state']=='validated']),2)

    def test_existing_machine_groups_recalculated_explicitly(self):
        old = add_pair_link(self.p,self.s,[self.al[1]['id']],[self.bl[1]['id']],
                            state='uncertain',origin='automatic-htr-htr')
        draft = suggest_textual_progress(self.p,self.s)
        self.assertIn(old['id'], [l['id'] for l in self.s['links']])
        saved = replace_revisable_pair_proposals(self.p,self.s,draft['proposals'])
        self.assertEqual(saved['replaced'],1)
        self.assertNotIn(old['id'],[l['id'] for l in self.s['links']])
        self.assertEqual(pair_progress(self.p,self.s)['target_unresolved'],0)
        self.assertEqual(pair_progress(self.p,self.s)['reference_unresolved'],0)

    def test_explicit_absence_excluded_from_proposals(self):
        uid = self.bl[3]['id']
        add_pair_link(self.p,self.s,[],[uid],kind='absence')
        data = suggest_textual_progress(self.p,self.s)
        self.assertNotIn(uid,[x for p in data['proposals'] for x in p['target_ids']])
        self.assertEqual(data['target_covered'],7)

    def test_ignored_lines_excluded(self):
        self.b['ignored_line_ids']=[self.bl[2]['id']]
        data=suggest_textual_progress(self.p,self.s)
        self.assertEqual(data['target_covered'],7)
        self.assertNotIn(self.bl[2]['id'],[uid for p in data['proposals'] for uid in p['target_ids']])

    def test_cross_folio_order_and_multiline_anchors(self):
        p = new_project()
        a = create_witness(p,'A');b = create_witness(p,'B')
        add_test_page(a,'1v','a1',[('c1',['start','aaa','bbb'])])
        add_test_page(a,'2r','a2',[('c1',['ccc','ddd','eee','end'])])
        add_test_page(b,'4v','b1',[('c1',['start','111','222','333','444'])])
        add_test_page(b,'5r','b2',[('c1',['555','666','777','888','999','end'])])
        s=create_pair_session(p,'A','B')
        al=physical_lines(a);bl=physical_lines(b)
        add_pair_link(p,s,[al[0]['id']],[bl[0]['id']])
        add_pair_link(p,s,[al[-2]['id'],al[-1]['id']],[bl[-2]['id'],bl[-1]['id']])
        result=suggest_textual_progress(p,s)
        self.assertEqual(result['reference_covered'],4)
        self.assertEqual(result['target_covered'],8)
        self.assertEqual(result['calculated_intervals'],1)
        self.assertEqual(len(result['warnings']),0)

    def test_one_sided_gap_is_not_an_automatic_absence(self):
        self.s['links'].pop()
        add_pair_link(self.p,self.s,[self.al[1]['id']],[self.bl[-1]['id']])
        result = suggest_textual_progress(self.p,self.s)
        self.assertEqual(result['proposals'],[])
        self.assertIn('one_sided_gap',[warning['reason'] for warning in result['warnings']])
        self.assertFalse(any(x['kind']=='absence' for x in self.s['links']))

    def test_crossed_human_anchors_block_only_the_local_interval(self):
        self.s['links'].pop()
        add_pair_link(self.p,self.s,[self.al[2]['id']],[self.bl[2]['id']])
        add_pair_link(self.p,self.s,[self.al[3]['id']],[self.bl[4]['id']])
        add_pair_link(self.p,self.s,[self.al[4]['id']],[self.bl[3]['id']])
        add_pair_link(self.p,self.s,[self.al[-1]['id']],[self.bl[-1]['id']])
        snapshot=copy.deepcopy(self.s['links'])
        out=suggest_textual_progress(self.p,self.s)
        self.assertIn('crossing_or_overlapping_anchors',[x['reason'] for x in out['warnings']])
        self.assertEqual(snapshot,self.s['links'])
        self.assertTrue(out['proposals'])  # safe segments still processed

    def test_quantity_estimation_fallback_and_htr_gibberish(self):
        base={'page_id':'p','region_id':'left','bbox':{'WIDTH':100}}
        lines=[dict(base,id='1',text='a'*50),dict(base,id='2',text='',bbox={'WIDTH':50}),
               dict(base,id='3',text='z'*2000,bbox={'WIDTH':25}),dict(base,id='4',text='')]
        weights, methods = _weights(lines)
        self.assertEqual(methods,['htr','geometry','geometry','geometry'])
        self.assertLess(weights[2],weights[0])
        self.assertTrue(all(w>0 for w in weights))
        no_geometry=[dict(page_id='p',region_id='',bbox={},id=str(i),text='') for i in range(3)]
        weights,methods = _weights(no_geometry)
        self.assertEqual(methods,['uniform']*3)
        self.assertEqual(weights,[1.]*3)
        self.assertEqual(_chars('Aé 19 !!!'),4)

    def test_high_ratio_and_performance_no_rejection(self):
        p = [{'id':f'a{i}','text':str(i)*20,'page_id':'pa','bbox':{'WIDTH':100}} for i in range(3)]
        q = [{'id':f'b{i}','text':str(i)*20,'page_id':'pb','bbox':{'WIDTH':100}} for i in range(100)]
        result=_partition(p,q)
        self.assertEqual(len(result),3)
        self.assertEqual(sum(map(lambda x:len(x['target_ids']),result)),100)
        q = q*5
        for i,line in enumerate(q):line['id']=f'b{i}'
        p = [dict(line,id=f'a{i}') for i,line in enumerate(p*166)][:498]
        t=time.perf_counter()
        proposal=_partition(p,q)
        self.assertLess(time.perf_counter()-t,2.0)
        self.assertEqual(sum(len(x['reference_ids']) for x in proposal),498)
        self.assertEqual(sum(len(x['target_ids']) for x in proposal),500)


if __name__=='__main__': unittest.main()
