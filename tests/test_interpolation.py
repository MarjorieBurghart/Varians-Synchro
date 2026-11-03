"""Conservative, column-local geometry tests with and without HTR."""
import unittest
from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import (physical_lines, create_pair_session,
                                                add_pair_link, apply_pair_proposals)
from varians_synchro.interpolation import suggest_between_anchors


def add_column(witness, count, *, page='f1r', column=0, reverse=False, htr=False):
    srcid=f'{witness["id"]}-{page}-{column}'
    lines=[]
    for i in range(count):
        lines.append({'alto_id':f'{srcid}-l{i}', 'text': f'Beatus Germanus textus number {i} test' if htr else '',
                      'bbox': {'HPOS':str(120+column*1100), 'VPOS':str(120+80*i),
                               'WIDTH':'800', 'HEIGHT':'53'}})
    witness['alto_sources'].append({'id':srcid, 'path':'/tmp/mock',
       'pages':[{'alto_page_id':srcid,'width':'2300','height':'3400','lines':lines}],
       'line_count':count, 'htr_line_count':sum(bool(x['text']) for x in lines)})
    witness['pages'].append({'id':srcid,'label':page,'image_kind':'local','image_path':'/tmp/x.jpg',
        'alto_binding':{'source_id':srcid,'page_index':0,'verified':True}})


class InterpolationTests(unittest.TestCase):
    def setUp(self):
        self.project=new_project()
        self.a=create_witness(self.project,'A')
        self.b=create_witness(self.project,'B')
        add_column(self.a,12)
        add_column(self.b,14)
        self.s=create_pair_session(self.project,'A','B')
        self.la=physical_lines(self.a)
        self.lb=physical_lines(self.b)

    def anchor(self,i,j):
        return add_pair_link(self.project,self.s,[self.la[i]['id']],[self.lb[j]['id']])

    def test_no_htr_geometry_suggests_not_validates(self):
        first=self.anchor(0,0)
        last=self.anchor(11,13)
        result=suggest_between_anchors(self.project,self.s)
        self.assertEqual(result['intervals'],1)
        self.assertGreater(len(result['proposals']),5)
        self.assertTrue(all(p['state']=='uncertain' for p in result['proposals']))
        self.assertTrue(all(p['origin']=='interpolated-geometry' for p in result['proposals']))
        self.assertTrue(all(not p['evidence']['htr_corrob'] for p in result['proposals']))
        self.assertEqual(len(self.s['links']),2)
        saved=apply_pair_proposals(self.project,self.s,result['proposals'])
        self.assertEqual(saved['added'],len(result['proposals']))
        self.assertEqual(self.s['links'][0]['id'],first['id'])
        self.assertEqual(self.s['links'][1]['id'],last['id'])
        self.assertEqual(sum(l['state']=='validated' for l in self.s['links']),2)
        # Every intervening physical line must appear once, and only once.
        linked_a=[uid for l in self.s['links'] for uid in l['reference_ids']]
        linked_b=[uid for l in self.s['links'] for uid in l['target_ids']]
        self.assertEqual(len(linked_a),len(self.la))
        self.assertEqual(len(linked_b),len(self.lb))
        self.assertEqual(len(linked_a),len(set(linked_a)))
        self.assertEqual(len(linked_b),len(set(linked_b)))

    def test_one_anchor_does_not_guess(self):
        self.anchor(0,0)
        result=suggest_between_anchors(self.project,self.s)
        self.assertEqual(result['proposals'],[])
        self.assertTrue(result['warnings'])

    def test_crossing_anchors_refused(self):
        self.anchor(0,13)
        self.anchor(11,0)
        result=suggest_between_anchors(self.project,self.s)
        self.assertEqual(result['proposals'],[])
        self.assertEqual(result['skipped_intervals'],1)

    def test_existing_link_between_anchors_is_not_overwritten(self):
        self.anchor(0,0)
        self.anchor(11,13)
        keep=self.anchor(5,6)
        result=suggest_between_anchors(self.project,self.s)
        self.assertTrue(result['proposals'])
        self.assertTrue(all(self.la[5]['id'] not in p['reference_ids'] for p in result['proposals']))
        self.assertTrue(all(self.lb[6]['id'] not in p['target_ids'] for p in result['proposals']))
        self.assertEqual(len(self.s['links']),3)
        self.assertEqual(self.s['links'][2]['id'],keep['id'])

    def test_different_pages_cannot_be_interpolated(self):
        a=self.project['witnesses'][0]
        b=self.project['witnesses'][1]
        add_column(a,5,page='f1v')
        add_column(b,5,page='f1v')
        self.la=physical_lines(a);self.lb=physical_lines(b)
        self.anchor(8,9)
        self.anchor(13,16)
        result=suggest_between_anchors(self.project,self.s)
        self.assertFalse(result['proposals'])
        self.assertEqual(result['skipped_intervals'],1)

    def test_geometry_has_no_text_dependency(self):
        for w in (self.a,self.b):
            for line in w['alto_sources'][0]['pages'][0]['lines']:
                line['text']='obviously wrong ♢♢'
        self.anchor(0,0)
        self.anchor(11,13)
        result=suggest_between_anchors(self.project,self.s)
        self.assertTrue(result['proposals'])
        self.assertTrue(all(l['confidence'] <= .60 for l in result['proposals']))

if __name__=='__main__': unittest.main()
