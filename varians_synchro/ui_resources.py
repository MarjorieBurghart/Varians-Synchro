"""Fenêtre « Ajouter un témoin… » / « Modifier le témoin et ses ressources » : sigle, images, XML, TEI et Manifests IIIF, appliqués d’un bloc."""
from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (QCheckBox, QFrame, QGroupBox, QHBoxLayout, QLineEdit,
                               QListWidgetItem, QScrollArea, QVBoxLayout, QWidget)

from .errors import localized, localized_text
from .i18n import tr
from .ui_batch_binding import BatchBindingDialog
from .ui_widgets import (fit_to_screen, _run_modal, start_detached, QDialog, QFileDialog, QInputDialog, QLabel, QListWidget,
                         QMessageBox, QPushButton)


class _ManifestFetcher(QThread):
    """Fetch IIIF Manifests outside the interface thread."""
    def __init__(self, urls, cancel):
        super().__init__()
        self.urls, self.cancel, self.results = list(urls), cancel, {}

    def run(self):
        from . import resource_workflow
        for url in self.urls:
            if self.cancel.is_set():
                return
            try:
                self.results[url] = ('ok', resource_workflow.inspect_manifest(url))
            except Exception as exc:
                self.results[url] = ('error', exc)


class WitnessResourceDialog(QDialog):
    """One modal transaction for witness and optional documentary resources."""
    def __init__(self, project, witness=None, parent=None):
        super().__init__(parent)
        self.original_project = project
        self.original_witness = witness
        self.staged_project = None
        self._manifests = {}      # url -> ('ok', manifest) | ('error', exception)
        self.pending = {'images': [], 'xml_files': [], 'tei_files': [], 'manifests': []}
        self.removals = []        # (kind, id) des ressources enregistrées à retirer
        # Associations faites dans le brouillon (« Associer automatiquement… ») :
        # page (image) -> (chemin du XML, page du XML). Le brouillon est
        # reconstruit à chaque changement ; elles y sont refaites.
        self._draft_bindings = {}
        self.setWindowTitle(tr('resources.witness.edit' if witness else 'resources.witness.new'))
        fit_to_screen(self, 790, 690)
        layout = QVBoxLayout(self)
        hint = QLabel(tr('resources.witness.help'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QHBoxLayout()
        form.addWidget(QLabel(tr('resources.witness.sigil')))
        self.sigil = QLineEdit(witness['id'] if witness else '')
        self.sigil.setObjectName('witnessSigilEdit')
        self.sigil.setReadOnly(witness is not None)  # stable key in historical links
        form.addWidget(self.sigil)
        form.addWidget(QLabel(tr('resources.witness.label')))
        self.label_edit = QLineEdit(witness.get('label', '') if witness else '')
        form.addWidget(self.label_edit, 2)
        layout.addLayout(form)
        self.pivot = QCheckBox(tr('resources.witness.pivot'))
        self.pivot.setChecked(project.get('pivot_witness_id') == (witness or {}).get('id'))
        if witness is not None and self.pivot.isChecked():
            # Décochée, la case ne retirait rien : un projet garde un pivot.
            self.pivot.setEnabled(False)
            self.pivot.setToolTip(tr('resources.witness.pivot_kept.tip'))
        self._initial_pivot = self.pivot.isChecked()
        layout.addWidget(self.pivot)
        self.lists = {}
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_container = QWidget()
        group_content = QVBoxLayout(scroll_container)
        scroll.setWidget(scroll_container)
        layout.addWidget(scroll, 1)
        for category, title, choose in (
            ('images', 'resources.witness.images', self.add_images),
            ('manifests', 'resources.witness.manifests', self.add_manifest),
            ('xml_files', 'resources.witness.xml', self.add_xml),
            ('tei_files', 'resources.witness.tei', self.add_tei)):
            group = QGroupBox(tr(title))
            group_layout = QVBoxLayout(group)
            lst = QListWidget()
            lst.setMaximumHeight(82)
            self.lists[category] = lst
            group_layout.addWidget(lst)
            actions = QHBoxLayout()
            add_button = QPushButton(tr('resources.witness.add'))
            add_button.clicked.connect(choose)
            add_button.setToolTip(tr('ui.resources.add_resource.tip'))
            actions.addWidget(add_button)
            remove = QPushButton(tr('resources.witness.remove_pending'))
            remove.clicked.connect(lambda checked=False, cat=category: self.remove_pending(cat))
            remove.setToolTip(tr('ui.resources.remove_resource.tip'))
            actions.addWidget(remove)
            if category == 'manifests':
                self.retry_button = QPushButton(tr('resources.witness.retry'))
                self.retry_button.setObjectName('retryManifestsButton')
                self.retry_button.setToolTip(tr('resources.witness.retry.tip'))
                self.retry_button.clicked.connect(self.retry_manifests)
                actions.addWidget(self.retry_button)
            actions.addStretch(1)
            group_layout.addLayout(actions)
            if category == 'tei_files':
                tei_note = QLabel(tr('resources.witness.tei_note'))
                tei_note.setWordWrap(True)
                group_layout.addWidget(tei_note)
            group_content.addWidget(group)
        group_content.addStretch(1)
        # Existing sources are displayed, but not removable here to avoid
        # invalidating established image/line links silently.
        self.refresh_lists()
        footer = QHBoxLayout()
        layout.addLayout(footer)
        auto = QPushButton(tr('resources.binding.title') + '…')
        auto.clicked.connect(self.preview_bindings)
        auto.setToolTip(tr('ui.resources.auto.tip'))
        footer.addWidget(auto)
        if witness is not None:
            remove_witness = QPushButton(tr('resources.witness.remove_witness'))
            remove_witness.setObjectName('removeWitnessButton')
            remove_witness.setToolTip(tr('resources.witness.remove_witness.tip'))
            remove_witness.clicked.connect(self.remove_witness)
            footer.addWidget(remove_witness)
        footer.addStretch(1)
        accept = QPushButton(tr('resources.witness.confirm'))
        accept.clicked.connect(self.commit)
        accept.setToolTip(tr('ui.resources.save.tip'))
        footer.addWidget(accept)
        cancel = QPushButton(tr('resources.cancel'))
        cancel.clicked.connect(self.cancel)
        cancel.setToolTip(tr('ui.resources.cancel.tip'))
        footer.addWidget(cancel)

    def has_unsaved_draft(self):
        """Resources added or marked for removal, a sigil or description
        typed or changed, the pivot box changed: Escape, the close button or
        « Cancel » ask first."""
        original = self.original_witness
        if original is None:
            typed = bool(self.sigil.text().strip() or self.label_edit.text().strip())
        else:
            typed = self.label_edit.text().strip() != (original.get('label') or '').strip()
        return (any(self.pending.values()) or bool(self.removals) or typed
                or self.pivot.isChecked() != self._initial_pivot)

    def _existing(self, category):
        if self.original_witness is None:
            return []
        witness = self.original_witness
        if category == 'images':
            return [s['reference'] for s in witness['image_sources'] if s['kind'] == 'local']
        if category == 'manifests':
            return [s['reference'] for s in witness['image_sources'] if s['kind'] == 'iiif']
        if category == 'xml_files':
            return [s['path'] for s in witness['alto_sources']]
        return [r['path'] for r in self.original_project.get('text_resources', [])
                if r.get('kind') == 'tei' and r.get('witness_id') == witness['id']]

    _KINDS = {'images': 'images', 'manifests': 'images', 'xml_files': 'xml', 'tei_files': 'tei'}

    def _existing_ids(self, category):
        """(chemin ou adresse, identifiant) des ressources enregistrées."""
        if self.original_witness is None:
            return []
        witness = self.original_witness
        if category in ('images', 'manifests'):
            kind = 'local' if category == 'images' else 'iiif'
            return [(s['reference'], s['id']) for s in witness['image_sources'] if s['kind'] == kind]
        if category == 'xml_files':
            return [(s['path'], s['id']) for s in witness['alto_sources']]
        return [(r['path'], r['id']) for r in self.original_project.get('text_resources', [])
                if r.get('kind') == 'tei' and r.get('witness_id') == witness['id']]

    def _unavailable(self):
        """Manifests IIIF enregistrés du témoin qui n'avaient pas répondu,
        hors ceux marqués « − » (« Réessayer » levait alors une KeyError)."""
        from .resource_workflow import unavailable_manifests
        if not self.original_witness:
            return []
        removed = {source_id for kind, source_id in self.removals if kind == 'images'}
        ids = dict(self._existing_ids('manifests'))
        return [url for url in unavailable_manifests(self.original_witness) if ids.get(url) not in removed]

    def refresh_lists(self):
        unavailable = self._unavailable()
        for category, lst in self.lists.items():
            lst.clear()
            for path, source_id in self._existing_ids(category):
                if path in self.pending[category]:
                    continue                      # à réessayer : montré plus bas
                removal = (self._KINDS[category], source_id)
                if removal in self.removals:
                    text = '−  ' + str(path)
                elif category == 'manifests' and path in unavailable:
                    text = f"⚠  {path} — {tr('resources.witness.manifest_unavailable')}"
                else:
                    text = '✓  ' + str(path)
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, None)
                # Une chaîne, pas un tuple : un objet Python gardé par Qt serait
                # libéré par Qt après l'arrêt de Python (plantage à la sortie).
                item.setData(Qt.ItemDataRole.UserRole + 1, '\t'.join(removal))
                item.setData(Qt.ItemDataRole.UserRole + 2, str(path))
                if removal in self.removals:
                    item.setToolTip(tr('resources.witness.removal_tip'))
                lst.addItem(item)
            for path in self.pending[category]:
                item = QListWidgetItem(('↻  ' if path in unavailable else '+  ') + str(path))
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                lst.addItem(item)
        if hasattr(self, 'retry_button'):
            self.retry_button.setEnabled(bool(unavailable))

    def retry_manifests(self):
        """Interroge de nouveau les Manifests indisponibles, dans le brouillon
        de la fiche : le projet ne change qu'à « Enregistrer le témoin »."""
        urls = self._unavailable()
        if not urls:
            QMessageBox.information(self, tr('resources.witness.manifests'),
                                    tr('resources.witness.retry_none'))
            return
        for url in urls:
            if url not in self.pending['manifests']:
                self.pending['manifests'].append(url)
        self.staged_project = None
        for url in urls:
            self._manifests.pop(url, None)          # asked again
        try:
            staged = self.stage_current()
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), localized_text(exc))
            return
        witness = next(w for w in staged['witnesses'] if w['id'] == self.original_witness['id'])
        sources = {s['reference']: s for s in witness['image_sources'] if s['kind'] == 'iiif'}
        lines = []
        for url in urls:
            source = sources[url]
            if source.get('status') == 'unavailable':
                lines.append(tr('resources.witness.retry_failed', url=url, error=source.get('error', '')))
                self.pending['manifests'].remove(url)
            else:
                lines.append(tr('resources.witness.retry_loaded', url=url,
                                pages=len((source.get('manifest') or {}).get('canvases', []))))
        if any(url not in self.pending['manifests'] for url in urls):
            self.staged_project = None            # le brouillon ne garde que les réussites
        self.refresh_lists()
        QMessageBox.information(self, tr('resources.witness.manifests'), '\n'.join(lines))

    def add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.images'), '',
                               tr('dialog.filter.images') + ' (*.jpg *.jpeg *.png *.tif *.tiff *.webp)')
        self._add('images', paths)

    def add_xml(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.xml'), '', 'XML (*.xml)')
        self._add('xml_files', paths)

    def add_tei(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.tei'), '',
                               'TEI XML (*.xml *.tei)')
        self._add('tei_files', paths)

    def add_manifest(self):
        url, ok = QInputDialog.getText(self, tr('resources.witness.manifests'),
                                      tr('resources.witness.manifest_url'))
        if ok and url.strip():
            self._add('manifests', [url.strip()])

    def _add(self, category, paths):
        for path in paths:
            known = path in self._existing(category) and path not in self._unavailable()
            if path not in self.pending[category] and not known:
                self.pending[category].append(path)
        self.staged_project = None
        self.refresh_lists()

    def remove_pending(self, category):
        item = self.lists[category].currentItem()
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if path is not None and path in self.pending[category]:
            self.pending[category].remove(path)
            self.staged_project = None
            self.refresh_lists()
        elif path is None and item.data(Qt.ItemDataRole.UserRole + 1):
            self._toggle_removal(item)

    def _toggle_removal(self, item):
        """Retire une ressource enregistrée à « Enregistrer le témoin », après
        avoir dit ce que cela entraîne ; de nouveau « Supprimer » la garde."""
        removal = tuple(item.data(Qt.ItemDataRole.UserRole + 1).split('\t'))
        if removal in self.removals:
            self.removals.remove(removal)
        else:
            from .resource_removal import removal_impact
            try:
                staged = self.stage_current()
                impact = removal_impact(staged, self.original_witness['id'], *removal)
            except Exception as exc:
                QMessageBox.warning(self, tr('resources.witness.edit'), localized_text(exc))
                return
            path = item.data(Qt.ItemDataRole.UserRole + 2)
            text = tr('resources.witness.remove_confirm', name=path if '://' in path else Path(path).name,
                      pages=impact['pages'], lines=impact['lines'], groups=impact['groups'],
                      validated=impact['validated'])
            if impact.get('ignored'):
                text += '\n\n' + tr('resources.witness.remove_ignored', count=impact['ignored'])
            answer = QMessageBox.question(self, tr('resources.witness.edit'), text)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.removals.append(removal)
        self.staged_project = None
        self.refresh_lists()

    def remove_witness(self):
        """Retire le témoin du projet, après avoir dit ce que cela entraîne ;
        refusé pour le pivot."""
        from .resource_removal import removal_impact, remove_witness
        witness_id = self.original_witness['id']
        try:
            impact = removal_impact(self.original_project, witness_id)
        except ValueError as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), localized_text(exc))
            return
        answer = QMessageBox.question(
            self, tr('resources.witness.edit'),
            tr('resources.witness.remove_witness_confirm', witness=witness_id, sessions=impact['sessions'],
               groups=impact['groups'], validated=impact['validated']))
        if answer != QMessageBox.StandardButton.Yes:
            return
        remove_witness(self.original_project, witness_id)
        self.accept()

    def _manifests_to_fetch(self):
        """Manifests ``apply_witness_draft`` would query: new ones, and known
        ones that did not answer; not those fetched already."""
        from .resource_workflow import _manifest_key
        known = {_manifest_key(s['reference']): s for s in (self.original_witness or {}).get('image_sources', [])
                 if s.get('kind') == 'iiif'}
        return [url for url in dict.fromkeys(str(u).strip() for u in self.pending['manifests'] if str(u).strip())
                if url not in self._manifests
                and (known.get(_manifest_key(url)) is None
                     or known[_manifest_key(url)].get('status') == 'unavailable')]

    def _fetch_manifests(self):
        """Fetch the Manifests in a thread of their own, the window going on
        (it froze while a slow server answered), with a cancellable wait."""
        urls = self._manifests_to_fetch()
        if not urls:
            return
        import threading
        from PySide6.QtCore import QEventLoop
        from PySide6.QtWidgets import QProgressDialog
        cancel = threading.Event()
        worker = _ManifestFetcher(urls, cancel)
        progress = QProgressDialog(tr('resources.witness.manifest_loading', count=len(urls)),
                                   tr('common.cancel'), 0, 0, self)
        progress.setWindowTitle(tr('resources.witness.manifests'))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        loop = QEventLoop()
        worker.finished.connect(loop.quit)
        progress.canceled.connect(cancel.set)
        progress.canceled.connect(loop.quit)
        start_detached(worker, self, cancel)
        progress.show()
        if not worker.isFinished():
            loop.exec()
        progress.hide()
        progress.deleteLater()
        for url in urls:
            self._manifests[url] = worker.results.get(url) or (
                'error', localized(ValueError, 'error.resources.manifest_cancelled'))

    def _cached_manifest(self, url):
        kind, value = self._manifests.get(url) or ('ok', None)
        if value is None:
            from . import resource_workflow
            return resource_workflow.inspect_manifest(url)
        if kind == 'error':
            raise value
        return value

    def build_stage(self):
        from .resource_workflow import apply_witness_draft
        self._fetch_manifests()
        # Build from a fresh snapshot; existing resources remain identical.
        draft = copy.deepcopy(self.original_project)
        apply_witness_draft(draft, identifier=self.sigil.text(),
                            label=self.label_edit.text(), is_pivot=self.pivot.isChecked(),
                            new_witness=self.original_witness is None,
                            manifest_loader=self._cached_manifest, **self.pending)
        if self.removals:
            from .resource_removal import remove_resource
            for kind, source_id in self.removals:
                remove_resource(draft, self.sigil.text().strip(), kind, source_id)
        self._replay_bindings(draft)
        self.staged_project = draft
        self._staged_identity = (self.sigil.text(), self.label_edit.text(),
                                 self.pivot.isChecked(), repr(self.pending), repr(self.removals))
        return draft

    @staticmethod
    def _page_key(page):
        """A page known across rebuilds of the draft: a new image's page gets
        a new identifier each time, its file stays the same."""
        if page.get('image_kind') == 'local':
            return ('local', str(page.get('image_path')))
        return ('iiif', str(page['id']))

    def _replay_bindings(self, draft):
        """Redo in a rebuilt draft the bindings made in this card, for pages
        still unbound whose XML page is still there and free."""
        if not self._draft_bindings:
            return
        from .reading_stream import rebind_page
        witness = next((w for w in draft['witnesses'] if w['id'] == self.sigil.text().strip()), None)
        if witness is None:
            return
        sources = {str(s['path']): s for s in witness.get('alto_sources', [])}
        for page in list(witness.get('pages', [])):
            target = self._draft_bindings.get(self._page_key(page))
            if target is None or page.get('alto_binding'):
                continue
            source = sources.get(target[0])
            if source is None or target[1] >= len(source.get('pages', [])):
                continue
            try:
                rebind_page(witness, page['id'], source['id'], target[1])
            except ValueError:
                continue                          # page XML prise entre-temps

    def stage_current(self):
        identity = (self.sigil.text(), self.label_edit.text(),
                    self.pivot.isChecked(), repr(self.pending), repr(self.removals))
        return self.staged_project if self.staged_project is not None and self._staged_identity == identity else self.build_stage()

    def preview_bindings(self):
        try:
            staged = self.stage_current()
            witness = next(w for w in staged['witnesses'] if w['id'] == self.sigil.text().strip())
            if not witness['pages'] or not witness['alto_sources']:
                QMessageBox.information(self, tr('resources.binding.title'),
                                        tr('resources.binding.missing'))
                return
            before = {p['id'] for p in witness['pages'] if p.get('alto_binding')}
            dialog = BatchBindingDialog(witness, self)
            _run_modal(dialog)
            paths = {s['id']: str(s['path']) for s in witness['alto_sources']}
            for page in witness['pages']:
                binding = page.get('alto_binding')
                if binding and page['id'] not in before and binding['source_id'] in paths:
                    self._draft_bindings[self._page_key(page)] = (paths[binding['source_id']],
                                                                  binding['page_index'])
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), localized_text(exc))

    def commit(self):
        try:
            staged = self.stage_current()
            # All imports and matching were applied to the draft only.
            self.original_project.clear()
            self.original_project.update(staged)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), localized_text(exc))
