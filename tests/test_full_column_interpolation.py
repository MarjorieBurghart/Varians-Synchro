"""Regression tests for realistic full-column interpolation with only two anchors."""
import unittest
from collections import Counter

from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import (physical_lines, create_pair_session,
                                                add_pair_link, apply_pair_proposals)
from varians_synchro.interpolation import suggest_between_anchors


def witness_page(witness, count, *, order='reading', columns=1, text=False):
    entries=[]
    for column in range(columns):
        for idx in range(count):
            width = 840
            x = 120 + 1150*column
            # Significant paragraph indentation and occasional short lines.
            if idx in (4, 10, 22, 31):
                x += 300; width -= 300
            if idx == count - 1:
                x += 540; width = 300
            if idx == 0:
                width = 570
            y = 130 + 65*idx
            entries.append((column, idx, {
                'alto_id':f'{witness["id"]}-c{column}-l{idx}',
                'text': ('INACCURATE HTR XX zz' if text else ''),
                'bbox': {'HPOS':str(x), 'VPOS':str(y),
                         'WIDTH':str(width), 'HEIGHT':'45'},
            }))
    if order == 'row':
        entries.sort(key=lambda v: (v[1],v[0]))
    elif order == 'noisy':
        # Permute adjacent ALTO elements; bounding boxes still carry correct y.
        entries.sort(key=lambda v: (v[0],v[1]))
        entries[12],entries[13]=entries[13],entries[12]
        entries[21],entries[22]=entries[22],entries[21]
    page_id = f'{witness["id"]}-page'
    witness['alto_sources'].append({'id':page_id, 'path':'/tmp/mock',
        'pages':[{'alto_page_id':page_id,'width':str(2500 if columns==2 else 1150),
                  'height':str(count*65+300), 'lines':[x[2] for x in entries]}],
        'line_count':len(entries),'htr_line_count':len(entries) if text else 0})
    witness['pages'].append({'id':page_id,'label':'1r', 'image_kind':'local',
       'image_path':'/tmp/f1r.jpg',
       'alto_binding':{'source_id':page_id, 'page_index':0, 'verified':True}})
    lines = physical_lines(witness)
    return {item['alto_id']:item for item in lines}


class WholeColumnTests(unittest.TestCase):
    def test_complete_column_with_short_ragged_lines_no_htr(self):
        project=new_project()
        a=create_witness(project,'A'); b=create_witness(project,'B')
        la=witness_page(a,52,order='noisy')
        lb=witness_page(b,57)
        session=create_pair_session(project,'A','B')
        anchors=[]
        for i,j in ((0,0),(51,56)):
            anchors.append(add_pair_link(project,session,
                [la[f'A-c0-l{i}']['id']], [lb[f'B-c0-l{j}']['id']]))
        before=[dict(x) for x in session['links']]
        result=suggest_between_anchors(project,session)
        self.assertEqual(result['intervals'],1, result['warnings'])
        self.assertGreater(len(result['proposals']),25)
        self.assertEqual(session['links'],before)
        ids_a=[x for link in result['proposals'] for x in link['reference_ids']]
        ids_b=[x for link in result['proposals'] for x in link['target_ids']]
        self.assertEqual(len(ids_a),50)
        self.assertEqual(len(ids_b),55)
        self.assertEqual(len(ids_a),len(set(ids_a)))
        self.assertEqual(len(ids_b),len(set(ids_b)))
        self.assertTrue(all(link['state']=='uncertain' for link in result['proposals']))
        self.assertTrue(all(link['origin']=='interpolated-geometry' for link in result['proposals']))
        self.assertTrue(all(link['confidence'] <= .6 for link in result['proposals']))
        self.assertEqual(apply_pair_proposals(project,session,result['proposals'])['added'],len(result['proposals']))
        self.assertEqual(session['links'][:2],anchors)

    def test_non_overlapping_short_anchors_with_broad_internal_lines(self):
        project=new_project()
        a=create_witness(project,'A'); b=create_witness(project,'B')
        la=witness_page(a,31); lb=witness_page(b,33)
        # Both bounding lines are short and mutually disjoint in X.
        for w in (a,b):
            rows=w['alto_sources'][0]['pages'][0]['lines']
            rows[0]['bbox'].update(HPOS='120', WIDTH='190')
            rows[-1]['bbox'].update(HPOS='790', WIDTH='130')
        session=create_pair_session(project,'A','B')
        add_pair_link(project,session,[la['A-c0-l0']['id']],[lb['B-c0-l0']['id']])
        add_pair_link(project,session,[la['A-c0-l30']['id']],[lb['B-c0-l32']['id']])
        result=suggest_between_anchors(project,session)
        self.assertEqual(result['intervals'],1,result['warnings'])
        self.assertEqual(sum(len(l['reference_ids']) for l in result['proposals']),29)
        self.assertEqual(sum(len(l['target_ids']) for l in result['proposals']),31)

    def test_two_columns_interleaved_in_alto_both_completed(self):
        project=new_project()
        a=create_witness(project,'A'); b=create_witness(project,'B')
        la=witness_page(a,40,order='row',columns=2)
        lb=witness_page(b,44,order='row',columns=2)
        session=create_pair_session(project,'A','B')
        for c in (0,1):
            for i,j in ((0,0),(39,43)):
                add_pair_link(project,session,[la[f'A-c{c}-l{i}']['id']],[lb[f'B-c{c}-l{j}']['id']])
        result=suggest_between_anchors(project,session)
        self.assertEqual(result['intervals'],2,result['warnings'])
        ids_a=[x for link in result['proposals'] for x in link['reference_ids']]
        ids_b=[x for link in result['proposals'] for x in link['target_ids']]
        self.assertEqual(len(ids_a),76)
        self.assertEqual(len(ids_b),84)
        self.assertEqual(len(ids_a),len(set(ids_a)))
        self.assertEqual(len(ids_b),len(set(ids_b)))
        # No proposals may merge columns.  Note ALTO IDs are preserved even
        # though the original textline order was interleaved by y.
        reverse_a={v['id']:k for k,v in la.items()}
        reverse_b={v['id']:k for k,v in lb.items()}
        for link in result['proposals']:
            ca={reverse_a[x].split('-')[1] for x in link['reference_ids']}
            cb={reverse_b[x].split('-')[1] for x in link['target_ids']}
            self.assertEqual(len(ca),1)
            self.assertEqual(ca,cb)

    def test_no_interpolation_across_pages(self):
        project=new_project()
        a=create_witness(project,'A'); b=create_witness(project,'B')
        la=witness_page(a,15)
        lb=witness_page(b,15)
        session=create_pair_session(project,'A','B')
        add_pair_link(project,session,[la['A-c0-l0']['id']],[lb['B-c0-l0']['id']])
        # Last anchor on a different page (both witnesses) should not imply
        # any interpolation over a folio boundary.
        for witness in (a,b):
            src = witness['alto_sources'][0]
            witness['pages'].append({'id':witness['id']+'-other', 'label':'1v', 'image_kind':'local',
                'image_path':'/tmp/f1v.jpg',
                'alto_binding':{'source_id':src['id'], 'page_index':0, 'verified':True}})
        aa=physical_lines(a)[-1]; bb=physical_lines(b)[-1]
        add_pair_link(project,session,[aa['id']],[bb['id']])
        result=suggest_between_anchors(project,session)
        self.assertEqual(result['proposals'],[])
        self.assertTrue(result['warnings'])

    def test_partially_occupied_column_keeps_manual_link(self):
        project=new_project()
        a=create_witness(project,'A'); b=create_witness(project,'B')
        la=witness_page(a,40); lb=witness_page(b,43)
        session=create_pair_session(project,'A','B')
        for i,j in ((0,0),(39,42)):
            add_pair_link(project,session,[la[f'A-c0-l{i}']['id']],[lb[f'B-c0-l{j}']['id']])
        # A provisional 1:n link must not be overwritten.
        protected=add_pair_link(project,session,[la['A-c0-l20']['id']],
             [lb['B-c0-l21']['id'],lb['B-c0-l22']['id']],state='uncertain',origin='automatic-htr-htr')
        original=list(session['links'])
        result=suggest_between_anchors(project,session)
        self.assertGreater(len(result['proposals']),20)
        self.assertEqual(original,session['links'])
        self.assertTrue(all(protected['reference_ids'][0] not in p['reference_ids']
                            for p in result['proposals']))
        self.assertTrue(all(not set(protected['target_ids']).intersection(p['target_ids'])
                            for p in result['proposals']))
        self.assertEqual(apply_pair_proposals(project, session, result['proposals'])['added'],len(result['proposals']))
        self.assertEqual(session['links'][2],protected)
        self.assertIn('incertains', ' '.join(result['warnings']))


if __name__=='__main__':
    unittest.main()
