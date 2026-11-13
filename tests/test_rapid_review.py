"""V0.7.2 independent review queue, protection, ordering and local preview."""
import copy
import unittest

from test_reading_stream import add_test_page
from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import (create_pair_session, physical_lines,
    add_pair_link, replace_revisable_pair_proposals)
from varians_synchro.rapid_review import (
    ordered_links, review_counts, pending_ids, following_anchor_interval,
    suggestions_for_interval, validate_checked)
from varians_synchro.textual_progress import suggest_textual_progress


class RapidReviewTests(unittest.TestCase):
    def setUp(self):
        self.p = new_project('Révision')
        self.a = create_witness(self.p, 'Mu')
        self.b = create_witness(self.p, 'F')
        add_test_page(self.a,'2v','a1',[('c1',['a0','a1','a2','a3'])])
        add_test_page(self.a,'3r','a2',[('c1',['a4','a5','a6','a7'])])
        add_test_page(self.b,'14v','b1',[('c1',['b0','b1','b2','b3','b4'])])
        add_test_page(self.b,'15r','b2',[('c1',['b5','b6','b7','b8','b9'])])
        self.s=create_pair_session(self.p,'Mu','F')
        self.al=physical_lines(self.a)
        self.bl=physical_lines(self.b)
        self.first=add_pair_link(self.p,self.s,[self.al[0]['id']],[self.bl[0]['id']])
        self.mid=add_pair_link(self.p,self.s,[self.al[4]['id']],[self.bl[5]['id']])
        self.last=add_pair_link(self.p,self.s,[self.al[7]['id']],[self.bl[9]['id']])
        self.out=suggest_textual_progress(self.p,self.s)
        self.assertTrue(self.out['proposals'])
        self.saved=replace_revisable_pair_proposals(self.p,self.s,self.out['proposals'])
        self.assertTrue(self.saved['added'])

    def test_filter_is_sorted_without_changing_stored_links(self):
        before=copy.deepcopy(self.s)
        links=ordered_links(self.p,self.s)
        self.assertEqual(links[0]['id'],self.first['id'])
        self.assertEqual(links[-1]['id'],self.last['id'])
        pending=ordered_links(self.p,self.s,'pending')
        self.assertTrue(all(l['state'] != 'validated' for l in pending))
        self.assertEqual(pending_ids(self.p,self.s),[l['id'] for l in pending])
        self.assertEqual(review_counts(self.s)['pending'],len(pending))
        self.assertEqual(self.s,before)

    def test_validate_only_selected_does_not_change_other_drafts(self):
        pending=pending_ids(self.p,self.s)
        selected=pending[0]
        before={l['id']:(l['state'],l['origin'],l['reference_ids'][:]) for l in self.s['links']}
        self.assertEqual(validate_checked(self.p,self.s,[selected]),1)
        for l in self.s['links']:
            if l['id'] == selected:
                self.assertEqual(l['state'],'validated')
                self.assertIn('reviewed_at',l)
            else:
                self.assertEqual((l['state'],l['origin'],l['reference_ids']),before[l['id']])

    def test_stale_batch_fails_atomically(self):
        ids=pending_ids(self.p,self.s)[:2]
        self.a['alto_sources'][0]['pages'][0]['lines'][1]['text']='CHANGED'
        before=copy.deepcopy(self.s['links'])
        with self.assertRaises(ValueError):
            validate_checked(self.p,self.s,ids)
        self.assertEqual(self.s['links'],before)

    def test_missing_and_absence_fails_atomically(self):
        one=pending_ids(self.p,self.s)[0]
        with self.assertRaises(ValueError):
            validate_checked(self.p,self.s,[one,'not_a_link'])
        self.assertEqual(next(l['state'] for l in self.s['links'] if l['id']==one),'uncertain')
        absence=add_pair_link(self.p,self.s,[],[self.bl[8]['id']],kind='absence') if not any(self.bl[8]['id'] in x['target_ids'] for x in self.s['links']) else None
        if absence:
            with self.assertRaises(ValueError):
                validate_checked(self.p,self.s,[absence['id']])

    def test_local_interval_filters_other_gap_and_crossfolio(self):
        first=following_anchor_interval(self.p,self.s,self.first['id'])
        second=following_anchor_interval(self.p,self.s,self.mid['id'])
        self.assertEqual(first,(self.first['id'],self.mid['id']))
        self.assertEqual(second,(self.mid['id'],self.last['id']))
        a=suggestions_for_interval(self.out,*first)
        b=suggestions_for_interval(self.out,*second)
        self.assertTrue(a)
        self.assertTrue(b)
        self.assertEqual(len(a)+len(b),len(self.out['proposals']))
        before=copy.deepcopy(self.s['links'])
        # Local previews are read-only and cannot replace other intervals.
        self.assertEqual(suggestions_for_interval(self.out, 'bogus', 'bogus'),[])
        self.assertEqual(self.s['links'],before)

    def test_local_commit_never_replaces_other_interval(self):
        interval = following_anchor_interval(self.p, self.s, self.first['id'])
        local = suggestions_for_interval(self.out, *interval)
        self.assertTrue(local)
        outside = {l['id']: copy.deepcopy(l) for l in self.s['links']
                   if l['id'] in (self.mid['id'], self.last['id'])
                   or (l.get('evidence', {}).get('interval_start') == self.mid['id'])}
        before_session = copy.deepcopy(self.s)
        changed = replace_revisable_pair_proposals(self.p, self.s, local)
        self.assertGreaterEqual(changed['added'],1)
        after = {l['id']: l for l in self.s['links']}
        for uid, original in outside.items():
            self.assertIn(uid, after)
            self.assertEqual(after[uid], original)
        self.assertNotEqual(self.s, before_session)

    def test_validating_new_anchor_splits_future_segments(self):
        chosen=pending_ids(self.p,self.s)[0]
        validate_checked(self.p,self.s,[chosen])
        result=suggest_textual_progress(self.p,self.s)
        self.assertEqual(next(l['state'] for l in self.s['links'] if l['id']==chosen),'validated')
        self.assertFalse(any(chosen in p['reference_ids'] for p in result['proposals']))
        self.assertGreaterEqual(len(result['proposals']),1)

if __name__=='__main__':
    unittest.main()
