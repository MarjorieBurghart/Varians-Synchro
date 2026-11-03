"""Regression tests for the TEI-free workflow, including migration from 0.5.x."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from varians_synchro.core import new_project, create_witness, save_project, load_project
from varians_synchro.physical_alignment import (
    physical_lines, line_uid, create_pair_session, add_pair_link, remove_pair_link,
    set_pair_link_states, pair_progress, verify_pair_sessions,
    suggest_htr_pair_alignment, apply_pair_proposals)


def add_page(w, lines, page_id=None):
    page_id=page_id or w['id']+'-page1'
    source_id='ALTO-'+w['id']
    w['alto_sources'].append({
        'id':source_id,'path':'/tmp/'+w['id']+'.xml',
        'pages':[{'alto_page_id':'page-1','width':'1000','height':'1800','lines':[
            {'alto_id':f'{w["id"]}-{i}', 'text':text,
             'bbox': {'HPOS':'10','VPOS':str(20+100*i),'WIDTH':'800','HEIGHT':'65'}}
            for i,text in enumerate(lines,1)]}],
        'line_count':len(lines),'htr_line_count':sum(bool(t) for t in lines),
    })
    w['pages'].append({'id':page_id,'label':'f. 1r','image_kind':'local',
                       'image_path':'/tmp/not-needed.jpg',
                       'alto_binding':{'source_id':source_id,'page_index':0,'verified':True}})


class PhysicalAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.project=new_project('ALTO seuls')
        self.a=create_witness(self.project,'A')
        self.b=create_witness(self.project,'B')
        add_page(self.a,['Beatus Germanus in hac vita','multis miraculis claruit','et populum docuit'])
        add_page(self.b,['Beatus Germanus in','hac vita multis miraculis','claruit et populum docuit'])
        self.session=create_pair_session(self.project,'A','B')
        self.la=physical_lines(self.a)
        self.lb=physical_lines(self.b)

    def test_no_tei_needed(self):
        self.assertEqual(self.project['text_resources'],[])
        self.assertEqual(len(self.la),3)
        self.assertEqual(len(self.lb),3)
        self.assertEqual(len(self.project['pair_sessions']),1)

    def test_deterministic_identifiers(self):
        self.assertEqual(self.la[0]['id'],line_uid('A','A-page1',1))
        self.assertEqual(self.la,physical_lines(self.a))
        self.assertNotEqual(self.la[0]['id'],self.lb[0]['id'])

    def test_multiline_and_absences(self):
        link=add_pair_link(self.project,self.session,[self.la[0]['id']],
                           [self.lb[0]['id'],self.lb[1]['id']])
        self.assertEqual(link['state'],'validated')
        add_pair_link(self.project,self.session,[self.la[1]['id']],[],kind='absence')
        add_pair_link(self.project,self.session,[],[self.lb[2]['id']],kind='absence')
        p=pair_progress(self.project,self.session)
        self.assertEqual(p['reference_covered'],2)
        self.assertEqual(p['target_covered'],3)
        self.assertEqual(p['stale_references'],0)

    def test_conflicts_and_distinct_missing(self):
        add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[0]['id']])
        with self.assertRaises(ValueError):
            add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[1]['id']])
        with self.assertRaises(ValueError):
            add_pair_link(self.project,self.session,[],[],kind='absence')
        with self.assertRaises(ValueError):
            add_pair_link(self.project,self.session,[],[],kind='correspondence')
        self.assertEqual(pair_progress(self.project,self.session)['reference_unresolved'],2)

    def test_bulk_validation_atomic(self):
        l=add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[0]['id']],state='proposed')
        before=copy.deepcopy(self.session)
        with self.assertRaises(ValueError):
            set_pair_link_states(self.session,[l['id'],'missing'],'validated')
        self.assertEqual(self.session,before)
        self.assertEqual(set_pair_link_states(self.session,[l['id']],'validated'),1)
        self.assertIn('reviewed_at',l)
        remove_pair_link(self.session,l['id'])
        self.assertEqual(self.session['links'],[])

    def test_reversed_pair_reuses_session(self):
        self.assertIs(create_pair_session(self.project,'B','A'),self.session)
        self.assertEqual(len(self.project['pair_sessions']),1)

    def test_mutations_are_reported_not_silently_deleted(self):
        add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[0]['id']])
        self.b['alto_sources'][0]['pages'][0]['lines'][0]['text']='Different revised HTR'
        self.assertEqual(pair_progress(self.project,self.session)['stale_references'],1)
        self.assertEqual(len(self.session['links']),1)
        self.assertTrue(verify_pair_sessions(self.project))

    def test_htr_pair_suggestions_and_protected_manual(self):
        keep=add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[0]['id']])
        result=suggest_htr_pair_alignment(self.project,self.session,min_support=.10)
        self.assertEqual(self.session['links'][0]['id'],keep['id'])
        for candidate in result['proposals']:
            self.assertNotIn(self.la[0]['id'],candidate['reference_ids'])
            self.assertNotIn(self.lb[0]['id'],candidate['target_ids'])
        count_before=len(self.session['links'])
        outcome=apply_pair_proposals(self.project,self.session,result['proposals'])
        self.assertEqual(len(self.session['links']),count_before+outcome['added'])
        for link in self.session['links'][1:]:
            self.assertNotEqual(link['state'],'validated')
            self.assertEqual(link['origin'],'automatic-htr-htr')

    def test_htr_pair_without_transcription(self):
        result=suggest_htr_pair_alignment(self.project,self.session,min_support=.05)
        self.assertGreater(len(result['proposals']),0)
        self.assertEqual(self.project['text_resources'],[])
        self.assertEqual(self.project['alignment_sessions'],[])

    def test_no_htr_no_false_positive(self):
        for witness in (self.a,self.b):
            for ln in witness['alto_sources'][0]['pages'][0]['lines']:
                ln['text']=''
        result=suggest_htr_pair_alignment(self.project,self.session)
        self.assertEqual(result['proposals'],[])

    def test_roundtrip_and_legacy_project(self):
        add_pair_link(self.project,self.session,[self.la[0]['id']],[self.lb[0]['id']])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project.vsynch'
            save_project(self.project,path)
            loaded=load_project(path)
            self.assertEqual(loaded['pair_sessions'],self.project['pair_sessions'])
            self.assertEqual(verify_pair_sessions(loaded),[])
            # Legacy 0.5.x files did not have a pair_sessions key.
            legacy=copy.deepcopy(self.project)
            legacy.pop('pair_sessions')
            legacy.pop('workflow_preference')
            path.write_text(json.dumps(legacy),encoding='utf-8')
            loaded=load_project(path)
            self.assertEqual(loaded.get('alignment_sessions'),[])
            self.assertEqual(loaded.get('pair_sessions',[]),[])
            self.assertEqual(loaded['workflow_preference'],'alto_only')
            s=create_pair_session(loaded,'A','B')
            self.assertEqual(s['kind'],'physical-pair')


if __name__=='__main__':
    unittest.main()
