"""Regression tests: reverse page order and mixed IIIF/local documentary sources."""
import unittest

from varians_synchro.core import new_project, create_witness, add_image_source
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.page_order import folio_key, ordered_pages
from varians_synchro.physical_alignment import physical_lines, line_uid, create_pair_session, add_pair_link


class PageOrderTests(unittest.TestCase):
    def setUp(self):
        self.w = create_witness(new_project(), 'A')

    def test_recognizes_folio_labels(self):
        self.assertEqual(folio_key('1r'), (1, 0))
        self.assertEqual(folio_key('f. 1v'), (1, 1))
        self.assertEqual(folio_key('ms_f014v.jpg'), (14, 1))
        self.assertEqual(folio_key('002r'), (2, 0))

    def test_reversely_imported_local_folios_are_sorted(self):
        for file in ('2r.jpg', '1v.jpg', '1r.jpg'):
            add_image_source(self.w, 'local', '/tmp/' + file)
        pages = create_pages(self.w)
        self.assertEqual([p['label'] for p in pages], ['1r', '1v', '2r'])
        # Old saved project with reverse list must also read in correct order.
        self.w['pages'] = list(reversed(pages))
        self.assertEqual([p['label'] for p in ordered_pages(self.w)], ['1r', '1v', '2r'])

    def test_local_filename_natural_order(self):
        for file in ('scan_10.jpg', 'scan_2.jpg', 'scan_1.jpg'):
            add_image_source(self.w, 'local', '/tmp/' + file)
        self.assertEqual([p['label'] for p in create_pages(self.w)],
                         ['scan_1', 'scan_2', 'scan_10'])

    def test_iiif_manifest_canvas_order_is_authoritative(self):
        source = add_image_source(self.w, 'iiif', 'https://example.org/manifest')
        source['manifest'] = {'canvases': [
            {'id':'canvas-2','label':'2r','index':2},
            {'id':'canvas-0','label':'1r','index':0},
            {'id':'canvas-1','label':'1v','index':1},
        ]}
        pages = create_pages(self.w)
        self.assertEqual([p['id'] for p in pages], ['canvas-0','canvas-1','canvas-2'])
        self.w['pages'] = list(reversed(pages))
        self.assertEqual([p['id'] for p in ordered_pages(self.w)],
                         ['canvas-0','canvas-1','canvas-2'])

    def test_physical_lines_use_documentary_order_on_legacy_project(self):
        for file in ('2r.jpg', '1v.jpg', '1r.jpg'):
            add_image_source(self.w, 'local', '/tmp/' + file)
        pages = create_pages(self.w)
        for i, p in enumerate(pages):
            source = {'id': 'alto' + str(i), 'path': 'not-needed',
                      'pages': [{'width': '1000', 'height': '1500', 'lines': [
                          {'alto_id': 'line', 'text': '', 'bbox': {'HPOS': '0', 'VPOS': '0',
                                                                 'WIDTH': '100', 'HEIGHT': '20'}}]}]}
            self.w['alto_sources'].append(source)
            bind_alto(self.w, p['id'], source['id'])
        first_id = pages[0]['id']
        self.w['pages'].reverse()
        lines = physical_lines(self.w)
        self.assertEqual([x['page_label'] for x in lines], ['1r', '1v', '2r'])
        self.assertEqual(lines[0]['id'], line_uid('A', first_id, 1))

    def test_explicit_order_must_cover_all_pages(self):
        for file in ('2r.jpg', '1v.jpg', '1r.jpg'):
            add_image_source(self.w, 'local', '/tmp/' + file)
        pages = create_pages(self.w)
        for i, p in enumerate(pages):
            p['reading_order'] = 2-i
        self.assertEqual([p['label'] for p in ordered_pages(self.w)], ['2r','1v','1r'])


if __name__ == '__main__':
    unittest.main()
