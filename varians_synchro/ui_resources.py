"""Fenêtre « Ajouter un témoin… » / « Modifier le témoin et ses ressources » : sigle, images, XML, TEI et Manifests IIIF, appliqués d’un bloc."""
from __future__ import annotations

import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QFrame, QGroupBox, QHBoxLayout, QLineEdit,
                               QListWidgetItem, QScrollArea, QVBoxLayout, QWidget)

from .i18n import tr
from .ui_batch_binding import BatchBindingDialog
from .ui_widgets import (_run_modal, QDialog, QFileDialog, QInputDialog, QLabel, QListWidget,
                         QMessageBox, QPushButton)


class WitnessResourceDialog(QDialog):
    """One modal transaction for witness and optional documentary resources."""
    def __init__(self, project, witness=None, parent=None):
        super().__init__(parent)
        self.original_project = project
        self.original_witness = witness
        self.staged_project = None
        self.pending = {'images': [], 'xml_files': [], 'tei_files': [], 'manifests': []}
        self.setWindowTitle(tr('resources.witness.edit' if witness else 'resources.witness.new'))
        self.resize(790, 690)
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
                self.retry_button.setEnabled(bool(self._unavailable()))
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
        footer.addStretch(1)
        accept = QPushButton(tr('resources.witness.confirm'))
        accept.clicked.connect(self.commit)
        accept.setToolTip(tr('ui.resources.save.tip'))
        footer.addWidget(accept)
        cancel = QPushButton(tr('resources.cancel'))
        cancel.clicked.connect(self.reject)
        cancel.setToolTip(tr('ui.resources.cancel.tip'))
        footer.addWidget(cancel)

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

    def _unavailable(self):
        """Manifests IIIF enregistrés du témoin qui n'avaient pas répondu."""
        from .resource_workflow import unavailable_manifests
        return unavailable_manifests(self.original_witness) if self.original_witness else []

    def refresh_lists(self):
        unavailable = self._unavailable()
        for category, lst in self.lists.items():
            lst.clear()
            for path in self._existing(category):
                if path in self.pending[category]:
                    continue                      # à réessayer : montré plus bas
                if category == 'manifests' and path in unavailable:
                    text = f"⚠  {path} — {tr('resources.witness.manifest_unavailable')}"
                else:
                    text = '✓  ' + str(path)
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, None)
                lst.addItem(item)
            for path in self.pending[category]:
                item = QListWidgetItem(('↻  ' if path in unavailable else '+  ') + str(path))
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                lst.addItem(item)

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
        try:
            staged = self.stage_current()
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), str(exc))
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
        elif path is None:
            QMessageBox.information(self, tr('resources.witness.edit'),
                                    tr('resources.witness.existing_protected'))

    def build_stage(self):
        from .resource_workflow import apply_witness_draft
        # Build from a fresh snapshot; existing resources remain identical.
        draft = copy.deepcopy(self.original_project)
        apply_witness_draft(draft, identifier=self.sigil.text(),
                            label=self.label_edit.text(), is_pivot=self.pivot.isChecked(),
                            **self.pending)
        self.staged_project = draft
        self._staged_identity = (self.sigil.text(), self.label_edit.text(),
                                 self.pivot.isChecked(), repr(self.pending))
        return draft

    def stage_current(self):
        identity = (self.sigil.text(), self.label_edit.text(),
                    self.pivot.isChecked(), repr(self.pending))
        return self.staged_project if self.staged_project is not None and self._staged_identity == identity else self.build_stage()

    def preview_bindings(self):
        try:
            staged = self.stage_current()
            witness = next(w for w in staged['witnesses'] if w['id'] == self.sigil.text().strip())
            if not witness['pages'] or not witness['alto_sources']:
                QMessageBox.information(self, tr('resources.binding.title'),
                                        tr('resources.binding.missing'))
                return
            dialog = BatchBindingDialog(witness, self)
            _run_modal(dialog)
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), str(exc))

    def commit(self):
        try:
            staged = self.stage_current()
            # All imports and matching were applied to the draft only.
            self.original_project.clear()
            self.original_project.update(staged)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.witness.edit'), str(exc))
