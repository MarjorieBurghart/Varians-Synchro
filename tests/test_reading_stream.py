"""J1 regression: streams, boundaries across folios, edits, legacy link integrity."""
import copy
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from varians_synchro.core import (new_project, create_witness, save_project,
    load_project, inspect_alto, inspect_line_source, add_image_source)
from varians_synchro.imaging import create_pages
from varians_synchro.physical_alignment import physical_lines, add_pair_link, create_pair_session
from varians_synchro.reading_stream import (reading_stream, anchor_intervals,
    set_page_order, set_region_order, set_line_order, reset_page_line_order,
    ReadingOrderError, page_regions)


def add_test_page(w, folio, page_id, regions):
    source_id = w['id']+'_'+page_id
    lines = []
    for r, texts in regions:
        for j, txt in enumerate(texts):
            lines.append({'alto_id': f'{r}.{j}', 'region_id': r,
                          'text': txt, 'bbox': {'HPOS': '25', 'VPOS':str(j*40),
                                               'WIDTH':'300', 'HEIGHT':'29'}})
    w['alto_sources'].append({'id': source_id, 'path':'/nonexistent/test.xml',
        'pages':[{'width':'1000','height':'1600','lines':lines}],
        'line_count':len(lines),'htr_line_count':len(lines)})
    w['pages'].append({'id':page_id,'label':folio,'image_kind':'local',
        'image_path':'/nonexistent/test.jpg',
        'alto_binding':{'source_id':source_id,'page_index':0}})


class ContinuousReadingTests(unittest.TestCase):
    def setUp(self):
        self.project = new_project('Refonte')
        self.a = create_witness(self.project,'Mu')
        self.b = create_witness(self.project,'F')
        add_test_page(self.a,'2v','Mu_2v',[('c1',['A1','A2']),('c2',['A3','A4'])])
        add_test_page(self.a,'3r','Mu_3r',[('c1',['A5','A6']),('c2',['A7','A8'])])
        add_test_page(self.b,'14v','F_14v',[('c1',['B1','B2','B3'])])
        add_test_page(self.b,'15r','F_15r',[('c1',['B4','B5','B6']),('c2',['B7','B8','B9'])])
        self.s = create_pair_session(self.project,'Mu','F')
        self.ma = physical_lines(self.a)
        self.fb = physical_lines(self.b)

    def test_cross_folio_and_multi_region_reading_stream(self):
        a = reading_stream(self.a)
        self.assertEqual([x['text'] for x in a],['A1','A2','A3','A4','A5','A6','A7','A8'])
        self.assertEqual([(x['page_label'],x['region_id']) for x in a[3:5]],
                         [('2v','c2'),('3r','c1')])
        self.assertEqual([x['stream_index'] for x in a], list(range(8)))

    def test_ignore_lines_without_renumbering_physical_uid(self):
        ignored = self.ma[1]['id']
        self.a['ignored_line_ids'] = [ignored]
        self.assertNotIn(ignored, [x['id'] for x in reading_stream(self.a)])
        self.assertIn(ignored, [x['id'] for x in reading_stream(self.a,include_ignored=True)])
        self.assertEqual(self.ma,physical_lines(self.a))
        self.assertEqual([x['stream_index'] for x in reading_stream(self.a)],list(range(7)))

    def test_multifolio_validated_anchors_without_any_page_pair(self):
        # Cross-page on each witness, different physical page count and lines.
        add_pair_link(self.project,self.s,[self.ma[0]['id']],[self.fb[0]['id']])
        add_pair_link(self.project,self.s,[self.ma[6]['id']],[self.fb[7]['id']])
        result = anchor_intervals(self.project,self.s)
        self.assertEqual(len(result['intervals']),1)
        gap = result['intervals'][0]
        self.assertEqual((gap['reference_count'],gap['target_count']),(5,6))
        self.assertEqual(gap['reference_pages'],['2v','3r'])
        self.assertEqual(gap['target_pages'],['14v','15r'])
        self.assertFalse(gap['needs_attention'])
        self.assertFalse(result['warnings'])

    def test_multi_line_anchors_across_physical_page_transition(self):
        add_pair_link(self.project,self.s,[self.ma[3]['id'],self.ma[4]['id']],
                      [self.fb[2]['id'],self.fb[3]['id'],self.fb[4]['id']])
        add_pair_link(self.project,self.s,[self.ma[7]['id']],[self.fb[8]['id']])
        result = anchor_intervals(self.project,self.s)
        self.assertEqual(len(result['anchors']),2)
        self.assertEqual((result['intervals'][0]['reference_count'],
                          result['intervals'][0]['target_count']),(2,3))
        self.assertFalse(result['warnings'])

    def test_human_reorders_regions_and_individual_lines_without_uid_changes(self):
        old = {x['id']:x['fingerprint'] for x in physical_lines(self.a)}
        set_region_order(self.a,'Mu_2v',['c2','c1'])
        self.assertEqual([x['text'] for x in reading_stream(self.a)[:4]],['A3','A4','A1','A2'])
        ids = [x['id'] for x in reading_stream(self.a,include_ignored=True) if x['page_id']=='Mu_2v']
        set_line_order(self.a,'Mu_2v',[ids[1],ids[0],ids[2],ids[3]])
        self.assertEqual([x['text'] for x in reading_stream(self.a)[:4]],['A4','A3','A1','A2'])
        reset_page_line_order(self.a,'Mu_2v')
        self.assertEqual([x['text'] for x in reading_stream(self.a)[:4]],['A3','A4','A1','A2'])
        self.assertEqual(old,{x['id']:x['fingerprint'] for x in physical_lines(self.a)})

    def test_page_reorder_across_folios_and_saving_round_trip(self):
        original = [x['id'] for x in physical_lines(self.a)]
        set_page_order(self.a,['Mu_3r','Mu_2v'])
        self.assertEqual(reading_stream(self.a)[0]['page_label'],'3r')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.vsynch'; save_project(self.project,path)
            loaded=load_project(path)
            witness=loaded['witnesses'][0]
            self.assertEqual(reading_stream(witness)[0]['page_label'],'3r')
            self.assertEqual([x['id'] for x in physical_lines(witness)][:4],original[4:])
            self.assertEqual(len(loaded['pair_sessions'][0]['links']),0)

    def test_invalid_or_stale_override_rejected_atomically(self):
        before=copy.deepcopy(self.a)
        with self.assertRaises(ReadingOrderError):
            set_page_order(self.a,['Mu_2v','Mu_2v'])
        self.assertEqual(before,self.a)
        with self.assertRaises(ReadingOrderError):
            set_region_order(self.a,'Mu_2v',['c2','missing'])
        self.assertEqual(before,self.a)
        self.a['pages'][0]['reading_line_order']=['unknown']
        with self.assertRaises(ReadingOrderError):
            reading_stream(self.a)

    def test_crossed_anchor_conflict_is_diagnosed_not_modified(self):
        first=add_pair_link(self.project,self.s,[self.ma[0]['id']],[self.fb[7]['id']])
        second=add_pair_link(self.project,self.s,[self.ma[7]['id']],[self.fb[0]['id']])
        before=copy.deepcopy(self.s['links'])
        data=anchor_intervals(self.project,self.s)
        self.assertEqual(len(data['intervals']),0)
        self.assertEqual(data['warnings'][0]['reason'],'crossing_or_overlapping_anchors')
        self.assertEqual(self.s['links'],before)

    def test_absences_and_ignored_anchors_reported_as_stale(self):
        link=add_pair_link(self.project,self.s,[self.ma[0]['id']],[self.fb[0]['id']])
        add_pair_link(self.project,self.s,[self.ma[7]['id']],[self.fb[8]['id']])
        self.a['ignored_line_ids']=[self.ma[0]['id']]
        result=anchor_intervals(self.project,self.s)
        self.assertEqual(len(result['anchors']),1)
        self.assertEqual(result['warnings'][0]['reason'],'stale_or_ignored_anchor')
        self.assertEqual(self.s['links'][0]['id'],link['id'])

    def test_empty_side_is_diagnostic_not_inferred_absence(self):
        add_pair_link(self.project,self.s,[self.ma[0]['id']],[self.fb[0]['id']])
        add_pair_link(self.project,self.s,[self.ma[1]['id']],[self.fb[6]['id']])
        interval=anchor_intervals(self.project,self.s)['intervals'][0]
        self.assertEqual(interval['reference_count'],0)
        self.assertEqual(interval['target_count'],5)
        self.assertTrue(interval['needs_attention'])
        self.assertFalse(any(link.get('kind')=='absence' for link in self.s['links']))

    def test_existing_uncertain_links_never_mutated_by_preview_or_reorder(self):
        add_pair_link(self.project,self.s,[self.ma[0]['id']],[self.fb[0]['id']])
        add_pair_link(self.project,self.s,[self.ma[7]['id']],[self.fb[8]['id']])
        add_pair_link(self.project,self.s,[self.ma[2]['id']],[self.fb[2]['id']],
                      state='uncertain', origin='automatic-htr-htr')
        before=copy.deepcopy(self.s['links'])
        set_region_order(self.a,'Mu_2v',['c2','c1'])
        anchor_intervals(self.project,self.s)
        self.assertEqual(before,self.s['links'])

    def test_page_refresh_preserves_manual_page_order(self):
        witness = create_witness(new_project(),'R')
        for name in ('1r.jpg','1v.jpg'):
            add_image_source(witness,'local','/tmp/'+name)
        pages=create_pages(witness)
        ids=[p['id'] for p in pages]
        set_page_order(witness,list(reversed(ids)))
        self.assertEqual([p['id'] for p in create_pages(witness)],list(reversed(ids)))

    def test_parsers_keep_original_geometry_plus_region_identity(self):
        alto='''<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page WIDTH="500" HEIGHT="500">
        <PrintSpace><TextBlock ID="col_left"><TextLine ID="a" HPOS="10" VPOS="20" WIDTH="150" HEIGHT="30"><String CONTENT="bonjour"/></TextLine></TextBlock>
        <TextBlock ID="col_right"><TextLine ID="b" HPOS="200" VPOS="20" WIDTH="150" HEIGHT="30"><String CONTENT="salut"/></TextLine></TextBlock>
        </PrintSpace></Page></Layout></alto>'''
        page='''<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"><Page imageWidth="500" imageHeight="500" imageFilename="folio1.png">
        <ReadingOrder><OrderedGroup><RegionRefIndexed regionRef="right" index="0"/><RegionRefIndexed regionRef="left" index="1"/></OrderedGroup></ReadingOrder>
        <TextRegion id="left"><TextLine id="t1"><Coords points="10,20 150,20 150,45 10,45"/><Baseline points="10,38 150,38"/><TextEquiv><Unicode>bonjour</Unicode></TextEquiv></TextLine></TextRegion>
        <TextRegion id="right"><TextLine id="t2"><Coords points="200,20 350,20 350,45 200,45"/><Baseline points="200,38 350,38"/><TextEquiv><Unicode>salut</Unicode></TextEquiv></TextLine></TextRegion>
        </Page></PcGts>'''
        with tempfile.TemporaryDirectory() as tmp:
            pa=Path(tmp)/'a.xml'; pa.write_text(alto,encoding='utf8')
            pb=Path(tmp)/'b.xml'; pb.write_text(page,encoding='utf8')
            a=inspect_alto(pa)['pages'][0]['lines']
            b=inspect_line_source(pb)['pages'][0]['lines']
            self.assertEqual([x['region_id'] for x in a],['col_left','col_right'])
            self.assertEqual([x['region_id'] for x in b],['right','left'])
            self.assertEqual(b[0]['baseline'],[[200.,38.],[350.,38.]])
            self.assertEqual(b[0]['text'],'salut')


if __name__ == '__main__': unittest.main()
