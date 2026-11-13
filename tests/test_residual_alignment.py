"""Regression tests for small unaligned gaps next to already aligned groups."""
import copy
import unittest
from varians_synchro.core import new_project,create_witness,save_project,load_project
from varians_synchro.physical_alignment import (create_pair_session,add_pair_link)
from varians_synchro.residual_alignment import (suggest_residual_extensions,
                                                apply_residual_extensions)
from test_full_column_interpolation import witness_page


def fixture(*, columns=1):
    project=new_project()
    wa=create_witness(project,'A'); wb=create_witness(project,'B')
    aa=witness_page(wa,17,columns=columns)
    bb=witness_page(wb,17,columns=columns)
    session=create_pair_session(project,'A','B')
    return project, session, aa, bb


def link(project,session,a,b,aa,bb,origin='interpolated-geometry',state='uncertain'):
    return add_pair_link(project,session,[aa[f'A-c0-l{i}']['id'] for i in a],
                         [bb[f'B-c0-l{i}']['id'] for i in b],
                         origin=origin,state=state)


class ResidualTests(unittest.TestCase):
    def test_extend_tentative_group_one_sided_gap(self):
        project,session,aa,bb=fixture()
        # The target has all these lines linked already, while A has 4 orphans.
        base=link(project,session,[3],[1,2,3],aa,bb)
        neighbour=link(project,session,[8],[4,5,6,7,8],aa,bb)
        # B contains no remaining free line near either group.
        before=copy.deepcopy(session['links'])
        result=suggest_residual_extensions(project,session)
        self.assertEqual(session['links'],before)
        self.assertGreater(len(result['proposals']),0, result)
        claimed={uid for p in result['proposals'] for uid in p['reference_add_ids']}
        expected={aa[f'A-c0-l{i}']['id'] for i in (4,5,6,7)}
        self.assertTrue(claimed & expected, result)
        saved=apply_residual_extensions(project,session,result['proposals'])
        self.assertGreaterEqual(saved['lines_added'],1)
        self.assertEqual(len(session['links']),2)
        self.assertTrue(all(item['state']=='uncertain' for item in session['links']))
        self.assertEqual({item['id'] for item in session['links']},{base['id'],neighbour['id']})
        again=suggest_residual_extensions(project,session)
        # Existing links never get a line added twice.
        for p in again['proposals']:
            self.assertFalse(set(p['reference_add_ids']) & claimed)

    def test_protect_manual_and_validated_links(self):
        project,session,aa,bb=fixture()
        link(project,session,[5],[4,5,6],aa,bb,origin='manual',state='validated')
        link(project,session,[9],[7,8,9],aa,bb,origin='interpolated-geometry',state='validated')
        before=copy.deepcopy(session['links'])
        result=suggest_residual_extensions(project,session)
        self.assertEqual(result['proposals'],[])
        self.assertGreater(result['diagnostics']['protected'],0)
        self.assertEqual(session['links'],before)

    def test_ignored_line_never_suggested(self):
        project,session,aa,bb=fixture()
        link(project,session,[5],[3,4,5],aa,bb)
        link(project,session,[11],[6,7,8,9,10,11],aa,bb)
        project['witnesses'][0]['ignored_line_ids']=[aa['A-c0-l6']['id']]
        outcome=suggest_residual_extensions(project,session)
        self.assertNotIn(aa['A-c0-l6']['id'],
            {uid for item in outcome['proposals'] for uid in item['reference_add_ids']})

    def test_atomic_stale_preview(self):
        project,session,aa,bb=fixture()
        original=link(project,session,[3],[1,2,3],aa,bb)
        link(project,session,[8],[4,5,6,7,8],aa,bb)
        result=suggest_residual_extensions(project,session)
        self.assertTrue(result['proposals'])
        original['state']='validated'
        frozen=copy.deepcopy(session)
        with self.assertRaises(ValueError):
            apply_residual_extensions(project,session,result['proposals'])
        self.assertEqual(session,frozen)

    def test_conflicting_picks_are_atomic(self):
        project,session,aa,bb=fixture()
        link(project,session,[3],[1,2,3],aa,bb)
        link(project,session,[8],[4,5,6,7,8],aa,bb)
        outcome=suggest_residual_extensions(project,session)
        self.assertTrue(outcome['proposals'])
        duplicate=copy.deepcopy(outcome['proposals'][0])
        frozen=copy.deepcopy(session)
        with self.assertRaises(ValueError):
            apply_residual_extensions(project,session,
                                      [outcome['proposals'][0],duplicate])
        self.assertEqual(session,frozen)

    def test_reimported_alto_after_preview_is_rejected(self):
        project,session,aa,bb=fixture()
        link(project,session,[3],[1,2,3],aa,bb)
        link(project,session,[8],[4,5,6,7,8],aa,bb)
        proposals=suggest_residual_extensions(project,session)['proposals']
        self.assertTrue(proposals)
        src=project['witnesses'][0]['alto_sources'][0]['pages'][0]['lines']
        src[4]['bbox']['HPOS']='700'  # Source changed after preview
        frozen=copy.deepcopy(session)
        with self.assertRaises(ValueError):
            apply_residual_extensions(project,session,proposals)
        self.assertEqual(session,frozen)

    def test_no_cross_column(self):
        project,session,aa,bb=fixture(columns=2)
        link(project,session,[5],[4,5,6],aa,bb)
        result=suggest_residual_extensions(project,session)
        for p in result['proposals']:
            self.assertTrue(all(uid in {v['id'] for k,v in aa.items() if '-c0-' in k}
                                for uid in p['reference_add_ids']))

    def test_saving_and_reloading_residual_group(self):
        import tempfile
        from pathlib import Path
        project,session,aa,bb=fixture()
        link(project,session,[3],[1,2,3],aa,bb)
        link(project,session,[8],[4,5,6,7,8],aa,bb)
        result=suggest_residual_extensions(project,session)
        applied=apply_residual_extensions(project,session,result['proposals'])
        self.assertGreater(applied['lines_added'],0)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project.vsynch'
            save_project(project,path)
            loaded=load_project(path)
        self.assertEqual(loaded['pair_sessions'][0]['links'],session['links'])

    def test_no_suggestions_if_target_has_open_nearby_line(self):
        project,session,aa,bb=fixture()
        link(project,session,[5],[5],aa,bb)
        # Both sides have nearby free lines, so better to run pair interpolation.
        result=suggest_residual_extensions(project,session)
        self.assertEqual(result['proposals'],[])
        self.assertGreater(result['diagnostics']['both_sides_open'],0)


if __name__=='__main__': unittest.main()
