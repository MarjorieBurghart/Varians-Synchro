"""Projet reçu : chemins qui sortent de son dossier ou désignent un partage
réseau (red team B3, A7).

À l'ouverture, Varians-Synchro lisait tous les fichiers désignés par le
projet, même hors de son dossier (« ../../Documents/… ») ou sur un partage
réseau (sous Windows, un accès réseau peut transmettre l'empreinte de
connexion) ; « Exporter un projet Varians » copiait la TEI désignée dans le
dossier exporté. Décision : à l'ouverture, ces chemins sont listés et l'on
demande s'il faut les lire ; si l'on refuse, ces fichiers sont traités comme
introuvables, et le projet garde leurs chemins à l'enregistrement.

Varians-Synchro n'écrit jamais lui-même de « .. ».
"""
import json
from pathlib import Path

from varians_synchro.core import (create_witness, load_project, new_project, save_project,
                                  suspicious_paths)


def _write(tmp_path, paths):
    folder = tmp_path / 'recu'
    folder.mkdir()
    (folder / 'local.xml').write_text('<x/>', encoding='utf-8')
    project = new_project('Reçu')
    witness = create_witness(project, 'A')
    witness['alto_sources'] = [{'id': f's{n}', 'path': p, 'pages': [], 'line_count': 0}
                               for n, p in enumerate(paths)]
    data = json.loads(json.dumps(project))
    (folder / 'projet.vsynch').write_text(json.dumps(data), encoding='utf-8')
    return folder / 'projet.vsynch'


def test_paths_leaving_the_folder_or_naming_a_share_are_listed(tmp_path):
    path = _write(tmp_path, ['local.xml', '../../Documents/prive.xml', '\\\\serveur\\partage\\x.xml',
                             '//serveur/partage/y.xml', 'sous/dossier/../ok.xml'])
    assert suspicious_paths(path) == ['../../Documents/prive.xml', '\\\\serveur\\partage\\x.xml',
                                      '//serveur/partage/y.xml']


def test_refused_paths_are_missing_files_but_saved_back_unchanged(tmp_path):
    path = _write(tmp_path, ['local.xml', '../../Documents/prive.xml'])
    (tmp_path / 'Documents').mkdir()
    (tmp_path / 'Documents' / 'prive.xml').write_text('secret', encoding='utf-8')
    project = load_project(path, refused=suspicious_paths(path))
    sources = project['witnesses'][0]['alto_sources']
    assert Path(sources[0]['path']) == path.parent / 'local.xml'
    assert not Path(sources[1]['path']).exists()               # traité comme introuvable
    save_project(project, path)
    saved = json.loads(path.read_text(encoding='utf-8'))
    assert [s['path'] for s in saved['witnesses'][0]['alto_sources']] == ['local.xml', '../../Documents/prive.xml']
    assert '_refused_paths' not in saved


def test_accepted_paths_are_read_as_before(tmp_path):
    path = _write(tmp_path, ['../../Documents/prive.xml'])
    project = load_project(path)                  # recu/../../Documents : à côté du dossier de tmp_path
    assert Path(project['witnesses'][0]['alto_sources'][0]['path']) == \
        Path(path.parent).resolve().parent.parent / 'Documents' / 'prive.xml'


def test_a_backslash_in_a_file_name_is_not_saved_as_a_relative_path(tmp_path):
    """A7 (Linux, macOS) : « f1\\recto.jpg » était écrit tel quel puis relu
    comme « f1/recto.jpg »."""
    import os
    if os.sep == '\\':
        return
    folder = tmp_path / 'p'
    (folder / 'images').mkdir(parents=True)
    odd = folder / 'images' / 'f1\\recto.jpg'
    odd.write_bytes(b'x')
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    witness['pages'] = [{'id': 'p1', 'label': '1r', 'image_kind': 'local', 'image_path': str(odd)}]
    save_project(project, folder / 'projet.vsynch')
    assert Path(load_project(folder / 'projet.vsynch')['witnesses'][0]['pages'][0]['image_path']) == odd


def test_a_symbolic_link_in_the_folder_keeps_the_path_relative(tmp_path):
    """A7 : l'ouverture suivait les liens symboliques ; ouvrir puis enregistrer
    sans rien changer rendait absolu un chemin relatif."""
    folder = tmp_path / 'p'
    folder.mkdir()
    (tmp_path / 'scans').mkdir()
    (tmp_path / 'scans' / 'f1.jpg').write_bytes(b'x')
    try:
        (folder / 'images').symlink_to(tmp_path / 'scans', target_is_directory=True)
    except OSError:
        return
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    witness['pages'] = [{'id': 'p1', 'label': '1r', 'image_kind': 'local', 'image_path': 'images/f1.jpg'}]
    (folder / 'projet.vsynch').write_text(json.dumps(project), encoding='utf-8')
    save_project(load_project(folder / 'projet.vsynch'), folder / 'projet.vsynch')
    saved = json.loads((folder / 'projet.vsynch').read_text(encoding='utf-8'))
    assert saved['witnesses'][0]['pages'][0]['image_path'] == 'images/f1.jpg'


def test_saved_files_follow_the_umask(tmp_path):
    """A8 : le premier .vsynch était créé en 0600 (fichier temporaire) ; une
    équipe sur un partage ne pouvait pas le lire."""
    import os
    import stat
    if os.name != 'posix':
        return
    previous = os.umask(0o022)
    try:
        save_project(new_project('Essai'), tmp_path / 'projet.vsynch')
    finally:
        os.umask(previous)
    assert stat.S_IMODE((tmp_path / 'projet.vsynch').stat().st_mode) == 0o644


def test_a_tei_nested_too_deeply_is_refused_with_a_message(tmp_path):
    """B6 : une TEI de 11 Ko imbriquée sur 1 200 niveaux levait une
    RecursionError non rattrapée ; la fenêtre principale ne pouvait plus se
    rafraîchir."""
    import pytest
    from varians_synchro.errors import localized_text
    from varians_synchro.i18n import tr
    from varians_synchro.tei_binding import extract_witness_tei
    tei = tmp_path / 'profonde.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>' + '<seg>' * 1200 + 'x'
                   + '</seg>' * 1200 + '</body></text></TEI>', encoding='utf-8')
    with pytest.raises(ValueError) as refused:
        extract_witness_tei(tei, 'A')
    assert localized_text(refused.value) == tr('error.tei_binding.too_deep')


def test_opening_asks_before_reading_files_outside_the_folder(tmp_path, monkeypatch):
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    import pytest
    pytest.importorskip('PySide6')
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from varians_synchro import ui_main_window
    from varians_synchro.i18n import tr
    path = _write(tmp_path, ['local.xml', '../../Documents/prive.xml'])
    asked = []
    monkeypatch.setattr(ui_main_window.QMessageBox, 'question', staticmethod(
        lambda parent, title, text, *a, **k: asked.append((title, text)) or ui_main_window.QtMessageBox.StandardButton.No))
    monkeypatch.setattr(ui_main_window.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (str(path), '')))
    monkeypatch.setattr(ui_main_window.GuidedWindow, '_trusted_paths', staticmethod(lambda: []))
    window = ui_main_window.GuidedWindow()
    try:
        window.open()
        assert [title for title, _ in asked] == [tr('project.paths.title')]
        assert '../../Documents/prive.xml' in asked[0][1]
        sources = window.project['witnesses'][0]['alto_sources']
        assert not Path(sources[1]['path']).exists() and window.project['_refused_paths']
    finally:
        window._suppress_close_confirmation = True
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
