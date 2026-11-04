"""Chemins relatifs dans un projet .vsynch : lus par rapport au dossier du
projet. L'exemple livré (demo_local_ALTO/) s'ouvre ainsi tel quel, où que
soit le dépôt ; il pointait vers des chemins de l'environnement où il
avait été créé (/mnt/data/…)."""
import json
import shutil
import sys
from pathlib import Path

from varians_synchro.core import check_alto_files, load_project, new_project, save_project
from varians_synchro.physical_alignment import (create_pair_session, physical_lines,
                                                suggest_htr_pair_alignment)

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'demo_local_ALTO' / 'exemple.vsynch'


def _project_with(paths):
    project = new_project('Chemins')
    project['witnesses'].append({
        'id': 'A', 'label': 'A',
        'image_sources': [{'id': 'i', 'kind': 'local', 'reference': paths['image']},
                          {'id': 'w', 'kind': 'iiif', 'reference': 'https://example.org/manifest.json'}],
        'alto_sources': [{'id': 'x', 'path': paths['xml'], 'pages': []}],
        'pages': [{'id': 'p', 'label': '1r', 'image_kind': 'local', 'image_path': paths['image']}],
        'hd_downloads': [{'directory': paths['hd'], 'pages': []}],
    })
    project['text_resources'].append({'id': 't', 'kind': 'tei', 'path': paths['tei'],
                                      'witness_id': 'A'})
    return project


def _paths(project):
    witness = project['witnesses'][0]
    return {'image': witness['image_sources'][0]['reference'],
            'iiif': witness['image_sources'][1]['reference'],
            'xml': witness['alto_sources'][0]['path'],
            'page': witness['pages'][0]['image_path'],
            'hd': witness['hd_downloads'][0]['directory'],
            'tei': project['text_resources'][0]['path']}


def test_relative_paths_are_read_from_the_project_folder(tmp_path):
    folder = tmp_path / 'projet'
    folder.mkdir()
    save_project(_project_with({'image': 'images/A.png', 'xml': 'A.xml', 'hd': 'HD',
                                'tei': '../edition.xml'}), folder / 'p.vsynch')
    loaded = _paths(load_project(folder / 'p.vsynch'))
    base = folder.resolve()
    assert loaded == {'image': str(base / 'images' / 'A.png'), 'page': str(base / 'images' / 'A.png'),
                      'xml': str(base / 'A.xml'), 'hd': str(base / 'HD'),
                      'tei': str(tmp_path.resolve() / 'edition.xml'),
                      'iiif': 'https://example.org/manifest.json'}


def test_absolute_paths_and_urls_are_left_as_they_are(tmp_path):
    for absolute in ('/data/A.png', r'C:\Manuscrits\A.png', r'\\serveur\partage\A.png'):
        save_project(_project_with({'image': absolute, 'xml': absolute, 'hd': absolute,
                                    'tei': absolute}), tmp_path / 'p.vsynch')
        loaded = _paths(load_project(tmp_path / 'p.vsynch'))
        assert set(loaded.values()) == {absolute, 'https://example.org/manifest.json'}, absolute


def test_a_windows_relative_path_is_read_on_every_system(tmp_path):
    save_project(_project_with({'image': r'images\A.png', 'xml': 'A.xml', 'hd': 'HD',
                                'tei': 'e.xml'}), tmp_path / 'p.vsynch')
    assert _paths(load_project(tmp_path / 'p.vsynch'))['image'] == \
        str(tmp_path.resolve() / 'images' / 'A.png')


def test_the_shipped_demo_holds_only_relative_paths():
    data = json.loads(DEMO.read_text(encoding='utf-8'))
    for witness in data['witnesses']:
        for value in ([s['reference'] for s in witness['image_sources']] +
                      [s['path'] for s in witness['alto_sources']] +
                      [p['image_path'] for p in witness['pages']]):
            assert not Path(value).is_absolute() and '/mnt/' not in value, value


def test_the_shipped_demo_opens_as_is_even_once_moved(tmp_path):
    moved = tmp_path / 'ailleurs' / 'demo'
    shutil.copytree(DEMO.parent, moved)
    for project_file in (DEMO, moved / DEMO.name):
        project = load_project(project_file)
        for witness in project['witnesses']:
            assert Path(witness['pages'][0]['image_path']).is_file()
            assert Path(witness['pages'][0]['image_path']).parent == project_file.parent.resolve()
        assert check_alto_files(project) == []
        a, b = project['witnesses']
        assert [len(physical_lines(w)) for w in (a, b)] == [3, 3]
        # De quoi essayer la fenêtre « Propositions HTR–HTR ».
        assert suggest_htr_pair_alignment(project, create_pair_session(project, 'A', 'B'))['proposals']


def test_the_demo_generator_writes_relative_paths(tmp_path):
    sys.path.insert(0, str(ROOT))
    try:
        import creer_demo
    finally:
        sys.path.remove(str(ROOT))
    output = creer_demo.main(tmp_path / 'demo')
    text = output.read_text(encoding='utf-8')
    assert str(tmp_path) not in text
    assert check_alto_files(load_project(output)) == []
