"""Ouvrir un projet exporté avec le vrai code de Varians (essais de compatibilité).

Le code source de Varians est cherché dans ``VARIANS_SOURCE``, sinon à côté
de ce dépôt (``../Varians``). L'ouverture se fait dans un processus Python à
part, depuis le dossier de Varians : ses modules (``project_config``,
``i18n``…) ne se mêlent pas à ceux de Varians-Synchro.

Elle reprend les étapes de la fenêtre de Varians à l'ouverture d'un projet
(``MainWindow.__init__``) : lecture du project.xml, du JSON d'alignement de
chaque témoin, règles des fichiers ALTO/PAGE puis des images (IIIF compris),
copie de travail IIIF, lignes du pivot et des autres témoins ; enfin, le
rattachement des ``<lb edRef="#pivot"/>`` de l'édition aux lignes du pivot.
``open_in_varians_window`` ouvre aussi le projet dans la vraie fenêtre de
Varians (sans écran), comme le ferait l'utilisateur.

Sans Varians : le test est ignoré, sauf si ``VARIANS_REQUIRED`` est défini
(c'est le cas dans la CI, qui récupère Varians) ; il échoue alors.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_OPEN = r'''
import json, sys, traceback
root, project_path = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
try:
    import xml.etree.ElementTree as ET
    from project_config import load_project, has_line_synchronization
    from witness_resource_refresh import read_alignment_json
    from alto_import import apply_witness_alto_policy
    from image_sources import apply_witness_image_policy
    from iiif_local import apply_working_copy
    from witness_sync import flatten_primary, flatten_secondary
    from web_viewer.tei_line_anchors import build_pivot_lb_index

    project = load_project(project_path)
    result = {"witnesses": {}}
    pivot_keys = []
    for w in project.witnesses:
        cache = (read_alignment_json(w.alignment) if has_line_synchronization(w)
                 else {"meta": {"witness": w.id, "role": w.role}, "pages": []})
        cache = apply_witness_alto_policy(
            cache, getattr(w, "alto_source_type", "auto"),
            [x.path for x in getattr(w, "alto_files", ())], project.root_dir,
            w.id, w.role, strict_no_ordinal=(getattr(w, "image_source_type", "") == "iiif"))
        cache = apply_witness_image_policy(
            cache, getattr(w, "image_source_type", "auto"),
            getattr(w, "image_source_value", None), project.root_dir,
            getattr(w, "image_files", ()), w.id,
            getattr(w, "iiif_selection_mode", "all"),
            getattr(w, "iiif_selected_canvases", ()),
            getattr(w, "iiif_ocr_links", ()),
            getattr(w, "iiif_page_links", ()))
        if getattr(w, "iiif_local_copy", False) and w.image_source_type == "iiif":
            cache = apply_working_copy(cache, project.root_dir, w.id)
        if w.is_base:
            items, _ = flatten_primary(cache)
            pivot_keys = [item["key"] for item in items]
            entry = {"keys": pivot_keys}
        else:
            items, by_base = flatten_secondary(cache)
            entry = {"keys": [item["key"] for item in items],
                     "base_keys": sorted(by_base)}
        entry["pages"] = [str(page.get("id")) for page in cache.get("pages", [])]
        entry["texts"] = [str(item["l"].get("alto") or "") for item in items]
        result["witnesses"][w.id] = entry
    edition = ET.parse(project.edition).getroot()
    _, report = build_pivot_lb_index(edition, project.base_witness, pivot_keys)
    result["pivot_lb_index"] = report.as_dict()
    print(json.dumps(result))
except Exception as exc:
    print(json.dumps({"error": f"{type(exc).__name__}: {exc}",
                      "trace": traceback.format_exc()}))
    sys.exit(1)
'''


_PREPARE = r"""
import json, sys, traceback
root, project_path, include_lb = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
sys.path.insert(0, root)
try:
    from pathlib import Path
    from project_config import load_project
    from project_management import WitnessDraft, minimal_tei_text
    from tei_facsimile import project_facsimile_pages, sync_facsimile_text
    from tei_pivot_scaffold import build_pivot_plan, render_pivot_scaffold, scaffold_is_empty

    project = load_project(project_path)
    source = Path(project.edition).read_text(encoding='utf-8-sig')
    blank = minimal_tei_text(project.title, [WitnessDraft(w.id, w.label) for w in project.witnesses],
                             project.base_witness, language='fr', schema_mode='auto')
    # « Paramètres du projet » → OK : Varians complète d'abord le <facsimile>
    # (une <surface> par image), puis prépare le pivot (project_actions).
    surfaces = project_facsimile_pages(project.witnesses, project.root_dir, project.edition)
    synced = sync_facsimile_text(source, surfaces)[0] if surfaces else source
    plan = build_pivot_plan(project.witnesses, project.base_witness, project.root_dir,
                            project.edition)
    print(json.dumps({
        'empty': scaffold_is_empty(source), 'same_as_varians_blank': source == blank,
        'pages': [[page.label, page.line_count] for page in plan.pages],
        'prepared': render_pivot_scaffold(synced, plan, include_lb=include_lb)}))
except Exception as exc:
    print(json.dumps({"error": f"{type(exc).__name__}: {exc}",
                      "trace": traceback.format_exc()}))
    sys.exit(1)
"""


_WINDOW = r"""
import json, os, sys, traceback, urllib.request
root, project_path = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
try:
    # Sans réseau (avant d'importer Varians, dont les modules gardent urlopen).
    def _no_network(*args, **kwargs):
        raise OSError('réseau coupé pendant l’essai de compatibilité')
    urllib.request.urlopen = _no_network
    from pathlib import Path
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
    app = QApplication([])
    # Toute boîte modale est notée, jamais affichée (elle bloquerait l'essai).
    dialogs = []
    def _box(kind):
        def show(parent, title, text, *args, **kwargs):
            dialogs.append([kind, title, text])
            return QMessageBox.StandardButton.No if kind == 'question' else QMessageBox.StandardButton.Ok
        return staticmethod(show)
    for kind in ('question', 'warning', 'critical', 'information'):
        setattr(QMessageBox, kind, _box(kind))
    QMessageBox.exec = lambda box: dialogs.append(['box', box.windowTitle(), box.text()]) or 0
    QDialog.exec = lambda dialog: dialogs.append(['dialog', dialog.windowTitle(), '']) or 0
    import app_context
    # Réglages de Varians dans le dossier personnel prêté, jamais dans ceux
    # de l'utilisateur (ni dans le registre Windows).
    app_context.SETTINGS_FILE_OVERRIDE = Path(os.environ['HOME']) / 'varians.ini'
    import editeur_tei
    window = editeur_tei.MainWindow(Path(project_path))
    window.show()
    QTimer.singleShot(1500, app.quit)
    app.exec()
    print(json.dumps({
        'version': app_context.APP_VERSION, 'title': window.windowTitle(),
        'panels': sorted(window.panels), 'edition': window.editor.toPlainText(),
        'dialogs': dialogs}))
    window.close()
except Exception as exc:
    print(json.dumps({"error": f"{type(exc).__name__}: {exc}",
                      "trace": traceback.format_exc()}))
    sys.exit(1)
"""


def varians_source():
    """Dossier du code source de Varians, ou None."""
    candidates = [os.environ.get('VARIANS_SOURCE'), ROOT.parent / 'Varians', ROOT.parent / 'varians']
    for candidate in candidates:
        if candidate and (Path(candidate) / 'project_config.py').is_file():
            return Path(candidate).resolve()
    return None


def require_varians():
    """Le dossier de Varians ; sinon le test est ignoré, ou échoue si
    ``VARIANS_REQUIRED`` est défini."""
    found = varians_source()
    if found is None:
        message = 'code source de Varians introuvable (VARIANS_SOURCE)'
        if os.environ.get('VARIANS_REQUIRED'):
            pytest.fail(message)
        pytest.skip(message)
    return found


def _run(script, *args, home=None):
    """Lance ``script`` avec le vrai code de Varians, dans un processus à part
    (depuis le dossier de Varians), et rend le JSON qu'il écrit. ``home`` :
    dossier personnel prêté à Varians (ses réglages et caches), à la place de
    celui de l'utilisateur."""
    root = require_varians()
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONUTF8='1')
    if home is not None:
        for name in ('HOME', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'XDG_CONFIG_HOME',
                     'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME'):
            env[name] = str(home)
    completed = subprocess.run([sys.executable, '-c', script, str(root), *map(str, args)],
                               cwd=str(root), env=env, capture_output=True, text=True,
                               encoding='utf-8', timeout=300)
    lines = [line for line in completed.stdout.splitlines() if line.startswith('{')]
    if not lines:
        raise AssertionError('Varians n’a rien rendu :\n' + completed.stdout + completed.stderr)
    return json.loads(lines[-1])


def open_in_varians(project_xml):
    """Ce que Varians lit en ouvrant ``project_xml`` : pour chaque témoin, ses
    pages, ses clés de lignes (``page::ligne``) dans l'ordre où Varians les
    parcourt, le texte de ces lignes et, hors pivot, les clés du pivot citées ;
    puis le bilan des ``<lb/>`` du pivot (``pivot_lb_index``). En cas d'échec
    d'ouverture : ``{"error": …}``."""
    return _run(_OPEN, project_xml)


def open_in_varians_window(project_xml):
    """Ouvre ``project_xml`` dans la vraie fenêtre de Varians (sans écran ni
    réseau, réglages et dossier personnel temporaires) et rend ce qu'elle
    montre : ``version`` de Varians, ``title`` de la fenêtre, ``panels``
    (sigles des témoins affichés), ``edition`` (le texte de l'édition dans
    l'éditeur) et ``dialogs`` (boîtes ouvertes, notées sans être
    affichées). En cas d'échec d'ouverture : ``{"error": …}``."""
    with tempfile.TemporaryDirectory() as home:
        return _run(_WINDOW, project_xml, home=home)


def prepare_pivot_in_varians(project_xml, *, include_lb=True):
    """Ce que fait Varians quand on coche, dans « Paramètres du projet »,
    « Préparer les <pb/> du témoin pivot dans la TEI vide » (et « Générer
    aussi les <lb/>… ») puis OK : <facsimile> complété, puis pivot préparé.
    Rend ``empty`` (l'édition est-elle vide pour Varians ?),
    ``same_as_varians_blank`` (est-elle identique à celle d'une « transcription
    vierge » de Varians ?), ``pages`` ([libellé, nombre de <lb/>]) et
    ``prepared`` (le texte de l'édition préparée, sans l'écrire)."""
    return _run(_PREPARE, project_xml, '1' if include_lb else '0')
