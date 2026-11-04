"""Enregistrement : chemins relatifs pour les fichiers rangés sous le dossier
du projet.

Un fichier situé dans le dossier du .vsynch ou en dessous est écrit en
chemin relatif (« images/A.png », séparateur « / ») : le projet peut être
déplacé ou copié avec ses fichiers et se rouvre tel quel. Un fichier ailleurs
(autre dossier, autre disque) garde son chemin absolu, une URL ne change pas.
En mémoire, les chemins restent absolus : l'export et l'interface n'en voient
aucune différence.
"""
import json
import shutil
from pathlib import Path

from test_relative_paths import _paths, _project_with
from varians_synchro.core import load_project, save_project


def _saved(path):
    return _paths(json.loads(Path(path).read_text(encoding='utf-8')))


def _files(folder, outside):
    (folder / 'images').mkdir(parents=True)
    (folder / 'images' / 'A.png').write_bytes(b'png')
    (folder / 'A.xml').write_text('<alto/>', encoding='utf-8')
    (folder / 'HD').mkdir()
    outside.mkdir(parents=True)
    (outside / 'edition.xml').write_text('<TEI/>', encoding='utf-8')
    return {'image': str(folder / 'images' / 'A.png'), 'xml': str(folder / 'A.xml'),
            'hd': str(folder / 'HD'), 'tei': str(outside / 'edition.xml')}


def test_files_under_the_project_folder_are_saved_relative(tmp_path):
    folder = tmp_path / 'projet'
    absolute = _files(folder, tmp_path / 'ailleurs')
    project = _project_with(absolute)
    save_project(project, folder / 'p.vsynch')
    assert _saved(folder / 'p.vsynch') == {
        'image': 'images/A.png', 'page': 'images/A.png', 'xml': 'A.xml', 'hd': 'HD',
        'tei': absolute['tei'], 'iiif': 'https://example.org/manifest.json'}
    assert _paths(project)['image'] == absolute['image']      # la mémoire ne change pas


def test_a_moved_project_folder_opens_with_its_files(tmp_path):
    folder = tmp_path / 'projet'
    _files(folder, tmp_path / 'ailleurs')
    save_project(_project_with({'image': str(folder / 'images' / 'A.png'), 'xml': str(folder / 'A.xml'),
                                'hd': str(folder / 'HD'), 'tei': str(tmp_path / 'ailleurs' / 'edition.xml')}),
                 folder / 'p.vsynch')
    moved = tmp_path / 'copie' / 'projet'
    shutil.copytree(folder, moved)
    shutil.rmtree(folder)
    loaded = _paths(load_project(moved / 'p.vsynch'))
    assert Path(loaded['image']) == (moved / 'images' / 'A.png').resolve()
    assert Path(loaded['image']).is_file() and Path(loaded['xml']).is_file()
    assert Path(loaded['tei']).is_file()                       # resté absolu


def test_saving_elsewhere_recomputes_the_paths(tmp_path):
    folder = tmp_path / 'projet'
    absolute = _files(folder, tmp_path / 'ailleurs')
    project = _project_with(absolute)
    save_project(project, folder / 'p.vsynch')
    save_project(load_project(folder / 'p.vsynch'), tmp_path / 'ailleurs' / 'q.vsynch')
    saved = _saved(tmp_path / 'ailleurs' / 'q.vsynch')
    assert saved['tei'] == 'edition.xml'
    assert Path(saved['image']).is_absolute()
    assert Path(saved['image']).resolve() == Path(absolute['image']).resolve()


def test_saving_reopening_and_saving_again_changes_nothing(tmp_path):
    folder = tmp_path / 'projet'
    _files(folder, tmp_path / 'ailleurs')
    first = folder / 'p.vsynch'
    save_project(_project_with({'image': str(folder / 'images' / 'A.png'), 'xml': str(folder / 'A.xml'),
                                'hd': str(folder / 'HD'), 'tei': str(tmp_path / 'ailleurs' / 'edition.xml')}),
                 first)
    before = first.read_text(encoding='utf-8')
    save_project(load_project(first), first)
    assert first.read_text(encoding='utf-8') == before
