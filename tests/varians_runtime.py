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

Sans Varians : le test est ignoré, sauf si ``VARIANS_REQUIRED`` est défini
(c'est le cas dans la CI, qui récupère Varians) ; il échoue alors.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


def open_in_varians(project_xml):
    """Ce que Varians lit en ouvrant ``project_xml`` : pour chaque témoin, ses
    pages, ses clés de lignes (``page::ligne``) dans l'ordre où Varians les
    parcourt, le texte de ces lignes et, hors pivot, les clés du pivot citées ;
    puis le bilan des ``<lb/>`` du pivot (``pivot_lb_index``). En cas d'échec
    d'ouverture : ``{"error": …}``."""
    root = require_varians()
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONUTF8='1')
    completed = subprocess.run([sys.executable, '-c', _OPEN, str(root), str(project_xml)],
                               cwd=str(root), env=env, capture_output=True, text=True,
                               encoding='utf-8', timeout=300)
    lines = [line for line in completed.stdout.splitlines() if line.startswith('{')]
    if not lines:
        raise AssertionError('Varians n’a rien rendu :\n' + completed.stdout + completed.stderr)
    return json.loads(lines[-1])
