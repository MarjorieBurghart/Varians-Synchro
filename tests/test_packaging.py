# -*- coding: utf-8 -*-
"""Version prête à l'emploi (V0.8.6.0) : recette PyInstaller
(packaging/varians_synchro.spec) et script de construction
(packaging/build.py), sur le modèle de Varians.

La construction elle-même (PyInstaller, quelques minutes) est faite par le
workflow « Binaries » sur Windows, macOS et Linux ; ici, ce qui se vérifie
sans construire : l'archive (nom, dossier, liens symboliques et droits
gardés), la plateforme, le contrôle du rapport de « --self-test », que la
recette emporte tous les dossiers lus par le code, et ce qui est posé à côté
de l'exécutable (LISEZMOI ×7, licences, projet d'exemple)."""
from __future__ import annotations

import ast
import importlib.util
import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'varians_synchro'


def _build():
    spec = importlib.util.spec_from_file_location('varians_synchro_packaging_build', ROOT / 'packaging' / 'build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec_constant(name):
    tree = ast.parse((ROOT / 'packaging' / 'varians_synchro.spec').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'{name} absent de varians_synchro.spec')


def test_archive_and_platform_names():
    build = _build()
    assert build.archive_name('0.8.6.0', 'windows-x64') == 'Varians-Synchro-0.8.6.0-windows-x64.zip'
    assert build.platform_tag('win32', 'AMD64') == 'windows-x64'
    assert build.platform_tag('darwin', 'arm64') == 'macos-arm64'
    assert build.platform_tag('darwin', 'x86_64') == 'macos-x64'
    assert build.platform_tag('linux', 'x86_64') == 'linux-x64'
    assert build.platform_tag('linux', 'aarch64') == 'linux-arm64'


def test_version_is_the_application_version():
    from varians_synchro.core import VERSION
    assert _build().app_version() == VERSION


def test_executable_inside_the_built_folder(tmp_path):
    build = _build()
    assert build.executable_path(tmp_path, 'win32') == tmp_path / 'Varians-Synchro.exe'
    assert build.executable_path(tmp_path, 'linux') == tmp_path / 'Varians-Synchro'
    assert build.executable_path(tmp_path, 'darwin') == \
        tmp_path / 'Varians-Synchro.app' / 'Contents' / 'MacOS' / 'Varians-Synchro'


def test_the_recipe_ships_every_folder_the_code_reads():
    """Les données sont lues à côté du paquet (``Path(__file__).parent.parent
    / 'i18n'``…) : un dossier ainsi lu, ou vérifié par ``--self-test``, qui
    manquerait à la recette manquerait à la version prête à l'emploi."""
    folders = set(_spec_constant('DATA_FOLDERS'))
    read = set()
    for path in sorted(CODE.glob('*.py')):
        read |= set(re.findall(r"parent\.parent\s*/\s*'(\w+)'", path.read_text(encoding='utf-8')))
    read.discard('run')             # spyder_launch : run.py, relancé seulement depuis Spyder
    from varians_synchro.self_test import DEMO
    assert read and read | {DEMO} <= folders, sorted(read | {DEMO} - folders)
    assert all((ROOT / folder).is_dir() for folder in folders)
    # Aucune donnée dans le paquet lui-même : la recette n'en emporte pas.
    data = [p.name for p in CODE.rglob('*') if p.is_file() and p.suffix not in {'.py', '.pyc'}]
    assert data == []


def test_the_build_expects_every_check_of_the_self_test():
    from varians_synchro.self_test import CHECKS
    assert _build().EXPECTED_CHECKS == CHECKS


def test_the_self_test_report_is_checked():
    build = _build()
    good = {'ok': True, 'frozen': True, 'version': '0.8.6.0',
            'checks': [{'name': name, 'ok': True, 'detail': ''} for name in build.EXPECTED_CHECKS]}
    assert build.report_problems(good, '0.8.6.0') == []
    assert build.report_problems(dict(good, ok=False), '0.8.6.0')
    assert build.report_problems(dict(good, frozen=False), '0.8.6.0')
    assert build.report_problems(dict(good, version='0.8.5.6'), '0.8.6.0')
    failed = dict(good, checks=good['checks'][:-1] + [{'name': 'window', 'ok': False, 'detail': 'xcb'}])
    assert any('window' in problem for problem in build.report_problems(failed, '0.8.6.0'))
    # Une vérification qui n'a pas eu lieu (fenêtre) est un échec.
    partial = dict(good, checks=good['checks'][:-1])
    assert any('window' in problem for problem in build.report_problems(partial, '0.8.6.0'))


@pytest.mark.skipif(os.name == 'nt', reason='liens symboliques et droits Unix')
def test_the_archive_keeps_its_folder_symlinks_and_permissions(tmp_path):
    """Le zip garde le dossier « Varians-Synchro-<version>/ », les droits
    d'exécution et les liens symboliques (bibliothèques Qt sous Linux et
    macOS) : décompressé, Varians-Synchro se lance."""
    build = _build()
    top = 'Varians-Synchro-0.8.6.0'
    folder = tmp_path / top
    (folder / '_internal' / 'lib').mkdir(parents=True)
    program = folder / 'Varians-Synchro'
    program.write_bytes(b'#!/bin/sh\n')
    program.chmod(0o755)
    (folder / '_internal' / 'lib' / 'libQt6Core.so.6').write_bytes(b'ELF')
    os.symlink('libQt6Core.so.6', folder / '_internal' / 'lib' / 'libQt6Core.so')
    os.symlink('_internal/lib', folder / 'lib')
    archive = tmp_path / 'Varians-Synchro.zip'
    build.zip_folder(folder, archive)
    with zipfile.ZipFile(archive) as zf:
        infos = {info.filename: info for info in zf.infolist()}
        assert all(name.startswith(f'{top}/') for name in infos)
        mode = infos[f'{top}/Varians-Synchro'].external_attr >> 16
        assert stat.S_ISREG(mode) and mode & 0o111
        link = infos[f'{top}/_internal/lib/libQt6Core.so']
        assert stat.S_ISLNK(link.external_attr >> 16)
        assert zf.read(link) == b'libQt6Core.so.6'
        directory_link = infos[f'{top}/lib']
        assert stat.S_ISLNK(directory_link.external_attr >> 16)
        assert zf.read(directory_link) == b'_internal/lib'
        # Le contenu du dossier pointé n'est pas emporté deux fois.
        assert f'{top}/lib/libQt6Core.so.6' not in infos
        assert zf.read(f'{top}/_internal/lib/libQt6Core.so.6') == b'ELF'


def test_the_archive_has_its_checksum(tmp_path):
    build = _build()
    archive = tmp_path / 'Varians-Synchro-0.8.6.0-linux-x64.zip'
    archive.write_bytes(b'abc')
    checksum = build.write_checksum(archive)
    assert checksum.name == 'Varians-Synchro-0.8.6.0-linux-x64.zip.sha256'
    assert checksum.read_text(encoding='ascii') == (
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  Varians-Synchro-0.8.6.0-linux-x64.zip\n')


@pytest.mark.skipif(sys.platform == 'win32', reason='Linux, macOS')
def test_bundled_certificates_only_when_the_system_ones_are_missing(monkeypatch):
    """Crochet d'exécution : certificats de certifi (manifestes et images
    IIIF) seulement si ceux du système ne sont pas où OpenSSL les cherche ;
    SSL_CERT_FILE respecté."""
    import ssl
    import types
    source = (ROOT / 'packaging' / 'rthook_certificates.py').read_text(encoding='utf-8')
    fake_certifi = types.SimpleNamespace(where=lambda: '/certifi/cacert.pem')
    monkeypatch.setitem(sys.modules, 'certifi', fake_certifi)

    def run(paths, environment):
        monkeypatch.setattr(ssl, 'get_default_verify_paths', lambda: paths)
        for name in ('SSL_CERT_FILE', 'SSL_CERT_DIR'):
            monkeypatch.delenv(name, raising=False)
        for name, value in environment.items():
            monkeypatch.setenv(name, value)
        exec(compile(source, 'rthook_certificates.py', 'exec'), {'__name__': '__main__'})
        return os.environ.get('SSL_CERT_FILE')

    missing = types.SimpleNamespace(cafile=None, capath=None)
    assert run(missing, {}) == '/certifi/cacert.pem'
    assert run(missing, {'SSL_CERT_FILE': '/mine.pem'}) == '/mine.pem'
    present = types.SimpleNamespace(cafile=__file__, capath=None)
    assert run(present, {}) is None


@pytest.mark.skipif(os.name == 'nt', reason='liens symboliques Unix')
def test_a_broken_link_in_the_built_folder_is_found(tmp_path):
    """Un lien symbolique vers une bibliothèque retirée par la recette ne
    doit pas partir dans l'archive : la construction le refuse."""
    build = _build()
    (tmp_path / 'lib').mkdir()
    (tmp_path / 'lib' / 'libQt6Core.so.6').write_bytes(b'ELF')
    os.symlink('lib/libQt6Core.so.6', tmp_path / 'libQt6Core.so.6')
    assert build.broken_links(tmp_path) == []
    os.symlink('lib/libQt6Pdf.so.6', tmp_path / 'libQt6Pdf.so.6')
    assert build.broken_links(tmp_path) == ['libQt6Pdf.so.6']


README_FILES = {'fr': 'LISEZMOI.txt', 'en': 'README.txt', 'de': 'LIESMICH.txt', 'ja': 'README-ja.txt',
                'cs': 'README-cs.txt', 'it': 'LEGGIMI.txt', 'ru': 'README-ru.txt'}


def test_the_archive_explains_itself_in_seven_languages(tmp_path):
    """À côté de Varians-Synchro : le LISEZMOI dans les sept langues de
    l'interface (installation et premier lancement non signé sur chaque
    système, projet d'exemple, mise à jour, vérification, licences), à la
    version construite."""
    build = _build()
    build.add_documents(tmp_path, '0.8.6.0', system='linux')
    for language, name in README_FILES.items():
        text = (tmp_path / name).read_text(encoding='utf-8')
        assert '{version}' not in text and 'Varians-Synchro-0.8.6.0-linux-x64.zip' in text, language
        for command in ('Varians-Synchro.exe', 'xattr -dr com.apple.quarantine /Applications/Varians-Synchro.app',
                        'start /wait Varians-Synchro.exe --self-test',
                        '/Applications/Varians-Synchro.app/Contents/MacOS/Varians-Synchro --self-test',
                        './Varians-Synchro --self-test', 'Get-FileHash', 'demo_local_ALTO',
                        'https://github.com/MarjorieBurghart/Varians-Synchro/releases',
                        'https://github.com/MarjorieBurghart/Varians-Synchro/issues', 'https://code.qt.io',
                        'licences'):
            assert command in text, (language, command)
    assert sorted(p.name for p in tmp_path.glob('*.txt')) == sorted(README_FILES.values())


def test_the_readmes_name_the_buttons_as_varians_synchro_shows_them():
    """« Ouvrir le guide utilisateur » (F1), « Langue » : les libellés de la
    fenêtre, pris dans les catalogues de l'interface."""
    for language, name in README_FILES.items():
        strings = {node.get('key'): node.text for node in ET.parse(ROOT / 'i18n' / f'{language}.xml').getroot()}
        text = (ROOT / 'packaging' / 'readme' / name).read_text(encoding='utf-8')
        assert strings['help.open'] in text and '(F1)' in text, language
        assert strings['common.language'].rstrip(' :：') in text, language


def test_the_example_project_is_set_beside_the_program(tmp_path):
    """Le dossier ``demo_local_ALTO`` (« Premier essai » du guide) est posé
    à côté de l'exécutable, tel qu'il est dans les sources."""
    build = _build()
    build.add_documents(tmp_path, '0.8.6.0', system='linux')

    def files(folder):
        return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert files(tmp_path / 'demo_local_ALTO') == files(ROOT / 'demo_local_ALTO')


def test_the_archive_carries_the_licence_texts(tmp_path):
    build = _build()
    build.add_documents(tmp_path, '0.8.6.0', system='linux')
    licences = tmp_path / 'licences'
    expected = {'LGPL-3.0.txt': 'LESSER GENERAL PUBLIC LICENSE', 'GPL-3.0.txt': 'GNU GENERAL PUBLIC LICENSE',
                'LGPL-2.1.txt': 'Version 2.1', 'MPL-2.0.txt': 'Mozilla Public License Version 2.0',
                'Python.txt': 'PYTHON SOFTWARE FOUNDATION LICENSE'}
    for name, words in expected.items():
        assert words in (licences / name).read_text(encoding='utf-8'), name


def test_windows_readmes_open_in_any_editor(tmp_path):
    """Sous Windows : fins de ligne CRLF et marque UTF-8 (Bloc-notes)."""
    build = _build()
    build.add_documents(tmp_path, '0.8.6.0', system='win32')
    data = (tmp_path / 'LISEZMOI.txt').read_bytes()
    assert data.startswith(b'\xef\xbb\xbf') and b'\r\n' in data and b'\n' not in data.replace(b'\r\n', b'')


def test_the_windowed_program_starts_without_a_console(monkeypatch):
    """Version Windows construite sans console : ``sys.stderr`` vaut None.
    Le lanceur démarre quand même (``faulthandler`` demande une sortie)."""
    pytest.importorskip('PySide6')
    import varians_synchro.gui
    spec = importlib.util.spec_from_file_location('varians_synchro_launcher', ROOT / 'run.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher, 'in_spyder_kernel', lambda: False)
    monkeypatch.setattr(varians_synchro.gui, 'main', lambda: 0)
    monkeypatch.setattr(sys, 'stderr', None)
    assert launcher.main() == 0


def test_the_binaries_workflow_builds_for_every_system_and_each_release():
    """Workflow « Binaries » : Windows, macOS (Apple Silicon et Intel),
    Linux ; à chaque release publiée et à la main ; mêmes dépendances que
    la recette ; la fenêtre vérifiée avec le module d'affichage du système ;
    seul l'envoi à la release peut écrire dans le dépôt."""
    text = (ROOT / '.github' / 'workflows' / 'binaries.yml').read_text(encoding='utf-8')
    for runner in ('windows-latest', 'macos-latest', 'macos-15-intel', 'ubuntu-22.04'):
        assert f'os: {runner}' in text
    for display in ('windows', 'cocoa', 'xcb'):
        assert f'display: {display}' in text
    assert '  release:\n    types: [published]\n' in text
    assert '  workflow_dispatch:\n' in text
    assert 'python -m pip install -r requirements.txt -r packaging/requirements.txt' in text
    assert 'xvfb-run -a python packaging/build.py' in text
    assert 'gh release upload "$TAG"' in text and '"Varians-Synchro-$version-"*' in text
    assert 'permissions:\n  contents: read\n' in text and text.count('contents: write') == 1


def test_the_workflows_use_actions_that_run_on_node_24():
    """Node.js 20 est abandonné sur les serveurs de GitHub : les actions
    sont à une version qui tourne sur Node.js 24 (checkout v5,
    setup-python v6, upload-artifact v6, download-artifact v7 ou plus)."""
    minimum = {'actions/checkout': 5, 'actions/setup-python': 6, 'actions/upload-artifact': 6,
               'actions/download-artifact': 7}
    found = []
    for workflow in sorted((ROOT / '.github' / 'workflows').glob('*.yml')):
        for action, major in re.findall(r'uses:\s*([\w.-]+/[\w.-]+)@v(\d+)', workflow.read_text(encoding='utf-8')):
            assert action in minimum, (workflow.name, action)
            assert int(major) >= minimum[action], (workflow.name, action, major)
            found.append(action)
    assert set(found) == set(minimum)
