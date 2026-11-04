"""Vérification d'une installation de Varians-Synchro.

``Varians-Synchro --self-test RAPPORT.json`` (ou ``python run.py
--self-test RAPPORT.json``) contrôle, sans réseau :

- ``translations`` : les sept catalogues de l'interface, mêmes clés, chacun
  lisible dans sa langue ;
- ``help`` : l'aide dans les sept langues ;
- ``resources`` : les icônes et le projet d'exemple (``demo_local_ALTO``) ;
- ``project`` : le projet d'exemple ouvert, ses fichiers ALTO retrouvés,
  puis enregistré, sur une copie (l'exemple livré n'est jamais modifié) ;
- ``alignment`` : une synchronisation A ↔ B, un groupe, puis « Exporter JSON
  pour Varians » et « Créer un projet Varians pré-renseigné » ;
- ``window`` : le projet dans la fenêtre principale, avec son icône, puis
  fermée.

Elle sert à vérifier, sur chaque système, la version prête à l'emploi
construite par PyInstaller (``packaging/``) : une application Windows sans
console n'a pas de sortie standard, d'où le rapport écrit dans un fichier.
Le code de sortie est 0 si tout va bien, 1 sinon. Aucun réglage de
l'utilisateur n'est écrit, et rien n'est laissé dans le dossier installé.

Le projet d'exemple vérifié est celui des données du programme (à côté du
paquet ``varians_synchro`` ; ``_internal`` dans une version construite),
pas la copie posée pour l'utilisateur à côté de l'exécutable : un paquet
``.app`` glissé dans Applications se vérifie donc toujours.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

LANGUAGES = ('fr', 'en', 'de', 'cs', 'it', 'ru', 'ja')
CHECKS = ('translations', 'help', 'resources', 'project', 'alignment', 'window')
DEMO = 'demo_local_ALTO'


def frozen() -> bool:
    """Version construite par PyInstaller (et non lancée depuis les sources)."""
    return bool(getattr(sys, 'frozen', False))


def _data_folder() -> Path:
    """Dossier des données lues par le code (``i18n``, ``help``, ``icons``,
    projet d'exemple) : à côté du paquet ``varians_synchro`` (``_internal``
    dans une version construite)."""
    return Path(__file__).resolve().parents[1]


def _translations(root):
    import xml.etree.ElementTree as ET
    keys = {}
    for language in LANGUAGES:
        path = root / 'i18n' / f'{language}.xml'
        if not path.is_file():
            raise AssertionError(f'absent : i18n/{language}.xml')
        keys[language] = {node.get('key') for node in ET.parse(path).getroot()}
    different = [language for language, found in keys.items() if found != keys['fr']]
    if different:
        raise AssertionError('catalogues différents du français : ' + ', '.join(different))
    from .i18n import get_language, set_language, tr
    previous = get_language()
    try:
        empty = []
        for language in LANGUAGES:
            set_language(language)
            if not tr('common.save') or tr('common.save') == 'common.save':
                empty.append(language)
    finally:
        set_language(previous)
    if empty:
        raise AssertionError('traductions vides : ' + ', '.join(empty))
    return f'{len(LANGUAGES)} langues, {len(keys["fr"])} messages'


def _help(root):
    missing = [f'help/{language}.html' for language in LANGUAGES
               if not (root / 'help' / f'{language}.html').is_file()]
    if missing:
        raise AssertionError('absent : ' + ', '.join(missing))
    return f'{len(LANGUAGES)} langues'


def _resources(root):
    from .app_icon import ICON_SIZES
    expected = [root / 'icons' / f'varians_synchro_{size}.png' for size in ICON_SIZES]
    expected += [root / DEMO / 'exemple.vsynch']
    missing = [str(path) for path in expected if not path.is_file()]
    if missing:
        raise AssertionError('absent : ' + ', '.join(missing))
    return f'{len(ICON_SIZES)} icônes, projet d\'exemple'


def _project(root, folder):
    """Le projet d'exemple, copié puis ouvert, vérifié et enregistré."""
    from .core import check_alto_files, load_project, save_project
    copy = folder / DEMO
    shutil.copytree(root / DEMO, copy)
    path = copy / 'exemple.vsynch'
    project = load_project(path)
    witnesses = [w['id'] for w in project.get('witnesses', [])]
    if witnesses != ['A', 'B']:
        raise AssertionError(f'témoins inattendus : {witnesses}')
    missing = check_alto_files(project)
    if missing:
        raise AssertionError('; '.join(str(item) for item in missing))
    save_project(project, path)
    return path


def _alignment(path, folder):
    """Une synchronisation A ↔ B et ses deux exports vers Varians."""
    from .core import load_project
    from .physical_alignment import add_pair_link, create_pair_session, pair_indices
    from .varians_export import export_varians_alignments
    from .varians_project_export import export_varians_project
    project = load_project(path)
    session = create_pair_session(project, 'A', 'B')
    reference, target = pair_indices(project, session)
    add_pair_link(project, session, list(reference)[:1], list(target)[:1])
    export_varians_alignments(project, 'A', folder / 'json')
    if not (folder / 'json' / 'validated' / 'B.json').is_file():
        raise AssertionError('validated/B.json absent')
    result = export_varians_project(project, 'A', folder / 'varians')
    if not Path(result['project_file']).is_file():
        raise AssertionError('project.xml absent')
    return f'{len(session["links"])} groupe, deux exports'


def _window(path):
    from PySide6.QtWidgets import QApplication
    from .app_icon import application_icon
    from .core import VERSION, load_project
    from .project_state import ProjectChangeTracker
    from .ui_main_window import GuidedWindow
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setWindowIcon(application_icon())
    window = GuidedWindow()
    try:
        window.project = load_project(path)
        window.path = str(path)
        window._changes = ProjectChangeTracker(window.project)
        window.refresh()
        window.show()
        for _ in range(20):
            app.processEvents()
        if VERSION not in window.windowTitle():
            raise AssertionError(f'titre inattendu : {window.windowTitle()}')
        if window.inventory.topLevelItemCount() != 2:
            raise AssertionError('témoins absents de la liste')
        if window.windowIcon().isNull():
            raise AssertionError('icône de Varians-Synchro non chargée')
        return f'{window.inventory.topLevelItemCount()} témoins affichés'
    finally:
        window._suppress_close_confirmation = True
        window.close()
        window.deleteLater()
        app.processEvents()


def run(report_path=None, *, root=None, only=CHECKS) -> int:
    """Vérifie l'installation et écrit le rapport JSON dans ``report_path``
    (sinon sur la sortie standard) ; 0 si tout va bien, 1 sinon. ``root`` :
    dossier des données à vérifier (par défaut, celles de ce programme)."""
    from .core import VERSION
    data = Path(root) if root else _data_folder()
    checks, state = [], {}
    with tempfile.TemporaryDirectory(prefix='varians-synchro-self-test-') as temporary:
        folder = Path(temporary)

        def check(name, function):
            if name not in only:
                return
            try:
                detail = function()
                if name == 'project':
                    state['project'], detail = detail, 'projet d\'exemple ouvert et enregistré'
                checks.append({'name': name, 'ok': True, 'detail': str(detail)})
            except Exception as error:
                checks.append({'name': name, 'ok': False,
                               'detail': f'{error}\n{traceback.format_exc()[-2000:]}'})

        def with_project(function):
            def checked():
                if 'project' not in state:
                    raise AssertionError('pas de projet (vérification « project » en échec)')
                return function(state['project'])
            return checked

        check('translations', lambda: _translations(data))
        check('help', lambda: _help(data))
        check('resources', lambda: _resources(data))
        check('project', lambda: _project(data, folder))
        check('alignment', with_project(lambda path: _alignment(path, folder)))
        check('window', with_project(_window))
    ok = bool(checks) and all(item['ok'] for item in checks)
    report = {'ok': ok, 'version': VERSION, 'frozen': frozen(), 'executable': sys.executable,
              'platform': sys.platform, 'checks': checks}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if report_path:
        Path(report_path).write_text(text, encoding='utf-8')
    elif sys.stdout is not None:
        print(text)
    return 0 if ok else 1
