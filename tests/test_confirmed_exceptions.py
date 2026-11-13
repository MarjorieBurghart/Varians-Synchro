"""Pair-local textual absences and safe conversion of uncertain suggestions."""
import copy
import tempfile
import unittest
from pathlib import Path

from varians_synchro.core import new_project, create_witness, save_project, load_project
from varians_synchro.physical_alignment import (
    physical_lines, add_pair_link, create_pair_session, pair_progress, is_revisable_automatic)
from varians_synchro.exceptions import (
    preview_confirmed_absence, confirm_absence, pair_exception_summary)
from varians_synchro.varians_export import make_varians_alignments


def page(w, number, texts):
    sid = f"source_{w['id']}_{number}"
    pid = f"{w['id']}_p{number}"
    w['alto_sources'].append({'id':sid, 'path':f'/tmp/{sid}.xml',
        'pages':[{'alto_page_id':pid, 'width':'1000','height':'1600','lines':[
            {'alto_id':f'{pid}_l{i}', 'text':value,
             'bbox':{'HPOS':20,'VPOS':30+i*70,'WIDTH':400,'HEIGHT':50}}
            for i,value in enumerate(texts,1)]}]})
    w['pages'].append({'id':pid,'label':f'f. {number}r','image_kind':'local',
        'image_path':f'/tmp/{pid}.jpg',
        'alto_binding':{'source_id':sid,'page_index':0,'verified':True}})


class ExceptionTests(unittest.TestCase):
    def setUp(self):
        self.p = new_project('absences')
        self.a = create_witness(self.p,'Mu')
        self.b = create_witness(self.p,'F')
        page(self.a,1,['a0','a1','a2','a3'])
        page(self.a,2,['a4','a5'])
        page(self.b,1,['b0','b1','b2','b3'])
        page(self.b,2,['b4','b5'])
        self.s = create_pair_session(self.p,'Mu','F')
        self.al = [x['id'] for x in physical_lines(self.a)]
        self.bl = [x['id'] for x in physical_lines(self.b)]

    def _automatic(self, refs, targets):
        return add_pair_link(self.p,self.s,refs,targets,kind='correspondence',
            state='uncertain',origin='automatic-textual-progress')

    def test_free_single_and_multiple_across_folios(self):
        preview = preview_confirmed_absence(self.p,self.s,'reference',self.al[3:5])
        self.assertEqual(preview['new_absence_groups'],1)
        self.assertEqual(preview['missing_in'],'F')
        self.assertEqual(self.s['links'],[])
        result = confirm_absence(self.p,self.s,preview)
        self.assertEqual(result['groups_created'],1)
        absence = self.s['links'][0]
        self.assertEqual(absence['reference_ids'], self.al[3:5])
        self.assertEqual(absence['target_ids'],[])
        self.assertEqual(absence['kind'],'absence')
        self.assertEqual(absence['state'],'validated')
        self.assertEqual(absence['evidence']['missing_in'],'F')
        self.assertEqual(pair_exception_summary(self.p,self.s)['reference_absent_lines'],2)
        self.assertEqual(pair_progress(self.p,self.s)['reference_unresolved'],4)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'saved.vsynch'
            save_project(self.p,path)
            p2=load_project(path)
            self.assertEqual(p2['pair_sessions'][0]['links'][0]['evidence'],absence['evidence'])

    def test_disjoint_runs_split(self):
        prev=preview_confirmed_absence(self.p,self.s,'reference', [self.al[4],self.al[0],self.al[2]])
        self.assertEqual(prev['new_absence_groups'],3)
        confirm_absence(self.p,self.s,prev)
        self.assertEqual([l['reference_ids'] for l in self.s['links']],
                         [[self.al[0]],[self.al[2]],[self.al[4]]])

    def test_target_side_pair_specific(self):
        prev=preview_confirmed_absence(self.p,self.s,'target', [self.bl[0],self.bl[1]])
        confirm_absence(self.p,self.s,prev)
        self.assertEqual(self.s['links'][0]['target_ids'],self.bl[:2])
        self.assertEqual(self.s['links'][0]['reference_ids'],[])
        self.assertEqual(pair_exception_summary(self.p,self.s)['target_absent_lines'],2)
        c=create_witness(self.p,'A')
        page(c,1,['ac0'])
        other=create_pair_session(self.p,'Mu','A')
        link=add_pair_link(self.p,other,[self.al[0]],[physical_lines(c)[0]['id']])
        self.assertEqual(link['kind'],'correspondence')

    def test_partial_automatic_group_is_trimmed(self):
        old=self._automatic(self.al[:3],self.bl[:2])
        before_id=old['id']
        prev=preview_confirmed_absence(self.p,self.s,'reference',[self.al[1]])
        self.assertEqual(prev['automatic_groups_affected'],1)
        result=confirm_absence(self.p,self.s,prev)
        self.assertEqual(result['automatic_groups_changed'],1)
        kept=next(x for x in self.s['links'] if x['id']==before_id)
        self.assertEqual(kept['reference_ids'],[self.al[0],self.al[2]])
        self.assertEqual(kept['target_ids'],self.bl[:2])
        self.assertEqual(kept['state'],'uncertain')
        self.assertTrue(is_revisable_automatic(kept))
        self.assertIn('confirmed_absence_edits', kept['evidence'])
        self.assertEqual(len(self.s['links']),2)

    def test_automatic_group_deleted_when_side_empty(self):
        old=self._automatic([self.al[0]],[self.bl[0],self.bl[1]])
        prev=preview_confirmed_absence(self.p,self.s,'reference',[self.al[0]])
        confirm_absence(self.p,self.s,prev)
        self.assertEqual(len(self.s['links']),1)
        self.assertNotEqual(self.s['links'][0]['id'],old['id'])
        self.assertEqual(pair_progress(self.p,self.s)['target_unresolved'],6)

    def test_manual_and_validated_protected_atomic(self):
        add_pair_link(self.p,self.s,[self.al[0]],[self.bl[0]])
        before=copy.deepcopy(self.s)
        with self.assertRaisesRegex(ValueError,'Dissociez'):
            preview_confirmed_absence(self.p,self.s,'reference',[self.al[0]])
        self.assertEqual(self.s,before)
        old2=self._automatic([self.al[1]],[self.bl[1]])
        old2['state']='validated'
        before=copy.deepcopy(self.s)
        with self.assertRaisesRegex(ValueError,'Dissociez'):
            preview_confirmed_absence(self.p,self.s,'target',[self.bl[1]])
        self.assertEqual(self.s,before)

    def test_ignored_and_existing_absence_protected(self):
        self.a['ignored_line_ids']=[self.al[0]]
        with self.assertRaisesRegex(ValueError,'ignorée'):
            preview_confirmed_absence(self.p,self.s,'reference',[self.al[0]])
        self.a['ignored_line_ids']=[]
        prev=preview_confirmed_absence(self.p,self.s,'reference',[self.al[1]])
        confirm_absence(self.p,self.s,prev)
        with self.assertRaisesRegex(ValueError,'Dissociez'):
            preview_confirmed_absence(self.p,self.s,'reference',[self.al[1]])

    def test_preview_stale_due_to_new_link_is_rejected(self):
        prev=preview_confirmed_absence(self.p,self.s,'reference',[self.al[1]])
        self._automatic([self.al[3]],[self.bl[3]])
        before=copy.deepcopy(self.s)
        with self.assertRaisesRegex(ValueError,'périmée'):
            confirm_absence(self.p,self.s,prev)
        self.assertEqual(self.s,before)

    def test_preview_stale_due_to_changed_text_or_scope(self):
        prev=preview_confirmed_absence(self.p,self.s,'reference',[self.al[1]])
        self.a['alto_sources'][0]['pages'][0]['lines'][1]['text']='Changed'
        before=copy.deepcopy(self.s)
        with self.assertRaisesRegex(ValueError,'périmée'):
            confirm_absence(self.p,self.s,prev)
        self.assertEqual(self.s,before)
        self.a['alto_sources'][0]['pages'][0]['lines'][1]['text']='a1'
        self.a['ignored_line_ids']=[self.al[4]]
        with self.assertRaisesRegex(ValueError,'périmée'):
            confirm_absence(self.p,self.s,prev)

    def test_export_does_not_invent_base_keys_for_absence(self):
        prev=preview_confirmed_absence(self.p,self.s,'target',[self.bl[0]])
        confirm_absence(self.p,self.s,prev)
        cor=add_pair_link(self.p,self.s,[self.al[1]],[self.bl[1]])
        cache,report=make_varians_alignments(self.p,'Mu',include_uncertain=False)
        rows={line['alto_id']: line for pg in cache['F']['pages'] for line in pg['lines']}
        self.assertFalse(rows['F_p1_l1'].get('base_keys'))
        self.assertTrue(rows['F_p1_l2'].get('base_keys'))
        self.assertEqual(cor['kind'],'correspondence')
        self.assertEqual(report['per_witness']['F']['secondary_side_absent_lines'],1)
        self.assertEqual(report['per_witness']['F']['confirmed_absence_groups'],1)

if __name__ == '__main__': unittest.main()
