"""Fenêtre principale de Varians-Synchro : projet et témoins, pages, synchronisation, avancement et exports."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QListWidgetItem,
                               QMessageBox as QtMessageBox, QPlainTextEdit, QSplitter,
                               QStackedWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .core import check_alto_files, load_project, new_project, save_project, VERSION
from .i18n import get_language, language_labels, set_language, tr
from .physical_alignment import (create_pair_session, pair_progress, physical_lines,
                                 verify_pair_sessions)
from .project_state import ProjectChangeTracker
from .ui_batch_binding import BatchBindingDialog
from .ui_pages import PagesDialog
from .ui_pair import PairDialog
from .ui_resources import WitnessResourceDialog
from .ui_scope import SingleWitnessScopeDialog
from .ui_tei_binding import TEIPhysicalBindingDialog
from .ui_widgets import (_run_modal, QComboBox, QDialog, QFileDialog, QInputDialog, QLabel,
                         QListWidget, QMainWindow, QMessageBox, QPushButton, QTreeWidget)


class _PairList(QListWidget):
    """Liste des paires alignées (étape 3) : un double-clic ou la touche
    Entrée émettent ``opened`` pour la ligne choisie. Entrée est traitée ici :
    sous macOS, elle n'« active » pas un élément de liste."""
    opened = Signal(object)

    def __init__(self):
        super().__init__()
        self.itemDoubleClicked.connect(self.opened.emit)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.currentItem() is not None:
            self.opened.emit(self.currentItem())
            return
        super().keyPressEvent(event)


class GuidedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = new_project()
        self.path = None
        self._changes = ProjectChangeTracker(self.project)
        self._suppress_close_confirmation = False
        self.setWindowTitle('Varians-Synchro V' + VERSION + tr('ui.atelier.dalignement.2') + '[*]')
        screen = QApplication.primaryScreen()
        bounds = screen.availableGeometry() if screen else None
        self.resize(min(1100, max(450, int(bounds.width() * .93))) if bounds else 1050,
                    min(740, max(340, int(bounds.height() * .89))) if bounds else 690)
        central = QWidget();self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.addWidget(QLabel('<h2>Varians-Synchro</h2>'))
        top = QHBoxLayout();root.addLayout(top)
        for text,callback in [('Nouveau projet',self.new),('Ouvrir .vsynch',self.open),('Enregistrer',self.save)]:
            button = QPushButton(text);button.clicked.connect(callback);top.addWidget(button)
        self.name_label = QLabel();top.addWidget(self.name_label,1)
        help_button = QPushButton(tr('help.open'))
        help_button.setToolTip(tr('help.title'))
        help_button.clicked.connect(self.open_user_manual)
        top.addWidget(help_button)
        top.addWidget(QLabel(tr('common.language')))
        self.language_box = QComboBox()
        self.language_box.setObjectName('languageSelector')
        for language, label in language_labels().items():
            self.language_box.addItem(label, language)
        self.language_box.setCurrentIndex(max(0, self.language_box.findData(get_language())))
        self.language_box.currentIndexChanged.connect(self.change_language)
        top.addWidget(self.language_box)
        splitter = QSplitter();root.addWidget(splitter,1)
        self.nav = QListWidget();self.nav.setFixedWidth(240)
        for text in (tr('navigation.project'), tr('navigation.pages'),
                     tr('navigation.alignment'), tr('navigation.progress')):
            self.nav.addItem(text)
        splitter.addWidget(self.nav)
        self.stack = QStackedWidget();splitter.addWidget(self.stack)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self._build_project_tab()
        self._build_pages_tab()
        self._build_alignment_tab()
        self._build_progress_tab()
        root.addWidget(QLabel('Les sources ne sont jamais modifiées. Enregistrez votre projet .vsynch après les opérations.'))
        self.nav.setCurrentRow(0)
        self.refresh()

    def open_user_manual(self):
        from pathlib import Path
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtWidgets import QMessageBox
        path = Path(__file__).resolve().parent.parent / 'docs' / 'user' / (get_language() + '.md')
        if not path.is_file() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            QMessageBox.warning(self, tr('help.title'), tr('help.missing'))

    def change_language(self):
        requested = self.language_box.currentData()
        if requested == get_language():
            return
        set_language(requested)
        from PySide6.QtCore import QSettings
        QSettings('Varians', 'Varians-Synchro').setValue('language', requested)
        # Rebuild only UI widgets, retaining the exact project in memory
        # (including unsaved links). Avoid restarting Qt under Spyder.
        replacement = type(self)()
        replacement.project = self.project
        replacement.path = self.path
        # The UI is being rebuilt, not closed by the user. Preserve the
        # saved baseline AND unsaved changes; never ask to save or discard.
        replacement._changes = self._changes
        replacement.refresh()
        app = QApplication.instance()
        app._varians_synchro_window = replacement
        replacement.show()
        self._suppress_close_confirmation = True
        self.close()

    def _update_save_indicator(self):
        changed = self._changes.is_modified(self.project)
        self.setWindowModified(changed)
        name = 'Projet : ' + self.project['name'] + (f'  ·  {Path(self.path).name}' if self.path else '  ·  ' + tr('project.unsaved_file'))
        self.name_label.setText(name + (tr('project.unsaved_marker') if changed else ''))

    def _confirm_save_or_discard(self) -> bool:
        """True iff losing the current in-memory state is authorized.

        Cancel is the safe default. Save cancellation or an I/O error
        must also prevent closing/replacing the project.
        """
        if not self._changes.is_modified(self.project):
            return True
        prompt = QtMessageBox(self)
        prompt.setIcon(QtMessageBox.Icon.Warning)
        prompt.setWindowTitle(tr('project.unsaved.title'))
        prompt.setText(tr('project.unsaved.question', name=self.project.get('name', '')))
        prompt.setInformativeText(tr('project.unsaved.explanation'))
        prompt.setStandardButtons(QtMessageBox.StandardButton.Save |
                                  QtMessageBox.StandardButton.Discard |
                                  QtMessageBox.StandardButton.Cancel)
        prompt.button(QtMessageBox.StandardButton.Save).setText(tr('project.unsaved.save'))
        prompt.button(QtMessageBox.StandardButton.Discard).setText(tr('project.unsaved.discard'))
        prompt.button(QtMessageBox.StandardButton.Cancel).setText(tr('project.unsaved.cancel'))
        prompt.setDefaultButton(QtMessageBox.StandardButton.Cancel)
        outcome = prompt.exec()
        if outcome == QtMessageBox.StandardButton.Save:
            return self.save()
        return outcome == QtMessageBox.StandardButton.Discard

    def closeEvent(self, event):
        if self._suppress_close_confirmation or self._confirm_save_or_discard():
            event.accept()
        else:
            event.ignore()

    def notice(self, title, detail):
        QMessageBox.information(self,title,detail)

    def operation(self, task):
        try:
            task()
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self,tr('Opération impossible'),str(exc))

    def _build_project_tab(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.addWidget(QLabel(tr('resources.project.heading')))
        help_text = QLabel(tr('resources.project.intro'))
        help_text.setWordWrap(True)
        main.addWidget(help_text)
        actions = QHBoxLayout()
        main.addLayout(actions)
        add = QPushButton(tr('resources.witness.new'))
        add.setObjectName('addWitnessResourcesButton')
        add.clicked.connect(self.add_witness)
        add.setToolTip(tr('ui.resources.add.tip'))
        actions.addWidget(add)
        actions.addStretch(1)
        self.inventory = QTreeWidget()
        self.inventory.setObjectName('witnessInventory')
        self.inventory.setHeaderLabels([tr('resources.project.witness'),
                                        tr('resources.project.status')])
        self.inventory.itemClicked.connect(self.edit_inventory_item)
        main.addWidget(self.inventory, 1)
        self.stack.addWidget(page)

    def edit_inventory_item(self, item, column=0):
        witness_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not witness_id:
            parent = item.parent()
            witness_id = parent.data(0, Qt.ItemDataRole.UserRole) if parent else None
        if not witness_id:
            return
        witness = next((w for w in self.project['witnesses'] if w['id'] == witness_id), None)
        if witness:
            dialog = WitnessResourceDialog(self.project, witness, self)
            if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                self.refresh()
                self._select_pivot()

    def _select_pivot(self):
        pivot = self.project.get('pivot_witness_id')
        if pivot:
            index = self.reference_box.findData(pivot)
            if index >= 0:
                self.reference_box.setCurrentIndex(index)

    def _build_pages_tab(self):
        page = QWidget()
        main = QVBoxLayout(page)
        heading = QLabel('ui.xml.check_heading')
        main.addWidget(heading)
        introduction = QLabel(tr('pages.order.tab_help'))
        introduction.setWordWrap(True)
        main.addWidget(introduction)
        main.addWidget(QLabel(tr('ui.pages.actions.help')))
        actions = (
            ('pages.order.open', 'openPageOrderButton', self.manage_pages, 'ui.pages.manage.tip'),
            ('resources.binding.title', 'batchBindingButton', self.batch_bind_from_pages, 'ui.pages.batch.tip'),
            ('tei.scope.action', 'openSingleWitnessScopeButton', self.open_single_witness_scope, 'ui.pages.scope.tip'),
            ('tei.binding.action', 'openTeiPhysicalBindingButton', self.open_tei_binding, 'ui.pages.tei.tip'),
        )
        for pair in (actions[:2], actions[2:]):
            row = QHBoxLayout()
            for label, name, callback, tooltip in pair:
                button = QPushButton(tr(label))
                button.setObjectName(name)
                button.setToolTip(tr(tooltip))
                button.clicked.connect(callback)
                row.addWidget(button, 1)
            main.addLayout(row)
        self.page_info = QPlainTextEdit()
        self.page_info.setReadOnly(True)
        main.addWidget(self.page_info, 1)
        self.stack.addWidget(page)

    def open_single_witness_scope(self):
        available = [w['id'] for w in self.project.get('witnesses', [])
                     if physical_lines(w)]
        if not available:
            QMessageBox.information(self, tr('tei.scope.title'), tr('tei.scope.no_pages'))
            return
        chosen, ok = QInputDialog.getItem(self, tr('tei.scope.title'),
            tr('tei.binding.witness'), available, 0, False)
        if not ok:
            return
        dialog = SingleWitnessScopeDialog(self.project, chosen, self)
        if _run_modal(dialog) == QDialog.DialogCode.Accepted:
            self.refresh()

    def open_tei_binding(self):
        dialog = TEIPhysicalBindingDialog(self.project, self)
        if _run_modal(dialog) == QDialog.DialogCode.Accepted:
            self.refresh()

    def _build_alignment_tab(self):
        page=QWidget();main=QVBoxLayout(page)
        main.addWidget(QLabel('<h3>' + tr('ui.alignment.heading') + '</h3>'))
        explanation = QLabel(tr('ui.alignment.intro'))
        explanation.setWordWrap(True)
        main.addWidget(explanation)
        self.align_info=QLabel();self.align_info.setWordWrap(True);main.addWidget(self.align_info)
        selectors=QHBoxLayout();main.addLayout(selectors)
        selectors.addWidget(QLabel('Pivot technique :'))
        self.reference_box=QComboBox();selectors.addWidget(self.reference_box,1)
        selectors.addWidget(QLabel('Témoin à aligner :'))
        self.target_box=QComboBox();selectors.addWidget(self.target_box,1)
        b=QPushButton('ui.xml.open_alignment')
        b.setToolTip(tr('ui.alignment.open.tip'))
        b.clicked.connect(self.open_physical_alignment)
        main.addWidget(b)
        # Une ligne par paire : double-clic ou Entrée l'ouvrent, un clic la
        # choisit dans les deux menus.
        self.align_status = _PairList()
        self.align_status.setToolTip(tr('ui.alignment.list.tip'))
        self.align_status.currentItemChanged.connect(self._choose_listed_pair)
        self.align_status.opened.connect(self._open_listed_pair)
        main.addWidget(self.align_status, 1)
        hint = QLabel(tr('ui.alignment.list.tip'))
        hint.setWordWrap(True)
        main.addWidget(hint)
        self.stack.addWidget(page)

    def export_varians_json(self):
        # Export both strictly validated and working/proposed link collections.
        # This is a physical-reference export, not a fictitious TEI edition.
        try:
            from .varians_export import export_varians_alignments, inspect_varians_export
            names = [w['id'] for w in self.project.get('witnesses', [])]
            if not names:
                QMessageBox.warning(self, tr('export.varians.title'), tr('export.varians.no_witness'))
                return
            default = self.project.get('pivot_witness_id') or self.reference_box.currentData()
            reference, ok = QInputDialog.getItem(self, tr('export.varians.title'),
                tr('export.varians.choose_base'), names,
                names.index(default) if default in names else 0, False)
            if not ok:
                return
            warning = QMessageBox.question(self, tr('export.varians.title'),
                tr('export.varians.warning'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if warning != QMessageBox.StandardButton.Yes:
                return
            audit = inspect_varians_export(self.project, reference)
            totals = audit['witnesses']
            if not totals:
                QMessageBox.warning(self, tr('export.varians.title'),
                                    tr('export.varians.only_base'))
                return
            issues = []
            for wid, data in totals.items():
                count = data['working_linked_lines']
                strict = data['validated_linked_lines']
                if count == 0:
                    cause = tr('export.varians.reason.' + (data['reason'] or 'no_exportable_correspondence'))
                    issues.append(f'{wid}: 0 / 0 — {cause}')
                elif strict == 0:
                    issues.append(f'{wid}: 0 / {count} — ' + tr('export.varians.reason.working_only'))
            if issues:
                msg = (tr('export.varians.audit_warning', base=reference)
                       + '\n\n' + '\n'.join(issues) + '\n\n'
                       + tr('export.varians.audit_confirmation'))
                confirmed = QMessageBox.question(self, tr('export.varians.title'), msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if confirmed != QMessageBox.StandardButton.Yes:
                    return
            directory = QFileDialog.getExistingDirectory(
                self, tr('export.varians.choose_empty'))
            if not directory:
                return
            reports = export_varians_alignments(self.project, reference, directory)
            summary = '; '.join(
                f'{wid}: {item["validated_linked_lines"]} / {item["working_linked_lines"]}'
                for wid, item in reports['audit']['witnesses'].items())
            QMessageBox.information(self, tr('export.varians.title'),
                tr('export.varians.success', path=directory, summary=summary))
        except Exception as exc:
            QMessageBox.critical(self, tr('export.varians.title'), str(exc))

    def _build_progress_tab(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.addWidget(QLabel('<h3>' + tr('ui.final.heading') + '</h3>'))
        explanation = QLabel(tr('ui.final.intro'))
        explanation.setWordWrap(True)
        main.addWidget(explanation)
        actions = QHBoxLayout()
        refresh_button = QPushButton(tr('ui.final.refresh'))
        refresh_button.clicked.connect(self.refresh)
        actions.addWidget(refresh_button)
        audit_button = QPushButton(tr('audit.action'))
        audit_button.setObjectName('auditProjectButton')
        audit_button.setToolTip(tr('ui.final.audit.help'))
        audit_button.clicked.connect(self.audit_project_integrity)
        actions.addWidget(audit_button)
        main.addLayout(actions)
        export_actions = QHBoxLayout()
        export_button = QPushButton(tr('export.varians.action'))
        export_button.setObjectName('exportVariansJsonButton')
        export_button.setToolTip(tr('ui.final.export_json.tip'))
        export_button.clicked.connect(self.export_varians_json)
        export_actions.addWidget(export_button)
        project_button = QPushButton(tr('ui.final.export_project.action'))
        project_button.setObjectName('exportVariansProjectButton')
        project_button.setToolTip(tr('ui.final.export_project.tip'))
        project_button.clicked.connect(self.export_varians_project)
        export_actions.addWidget(project_button)
        main.addLayout(export_actions)
        explanation = QLabel(tr('ui.final.audit.help'))
        explanation.setWordWrap(True)
        main.addWidget(explanation)
        self.progress = QPlainTextEdit()
        self.progress.setReadOnly(True)
        main.addWidget(self.progress, 1)
        self.stack.addWidget(page)

    def export_varians_project(self):
        """Build a Varians project in an empty folder; never modify sources."""
        from .varians_project_export import export_varians_project
        base = self.project.get('pivot_witness_id') or self.reference_box.currentData()
        has_tei = any(r.get('kind') == 'tei' and r.get('witness_id') == base
                      for r in self.project.get('text_resources', []))
        # Without a TEI edition, the project gets the blank edition Varians
        # creates for a new transcription; Varians prepares the pivot in it.
        blank = '' if has_tei else (tr('ui.final.export_project.no_tei') + '\n\n' +
                                    tr('ui.final.export_project.prepare_pivot') + '\n\n')
        decision = QMessageBox.question(
            self, tr('ui.final.export_project.action'),
            blank + tr('ui.final.export_project.confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if decision != QMessageBox.StandardButton.Yes:
            return
        folder = QFileDialog.getExistingDirectory(self, tr('export.varians.choose_empty'))
        if not folder:
            return
        try:
            export_varians_project(self.project, base, folder)
        except Exception as exc:
            QMessageBox.critical(self, tr('ui.final.export_project.action'), str(exc))
        else:
            QMessageBox.information(self, tr('ui.final.export_project.action'),
                tr('ui.final.export_project.success', path=str(Path(folder) / 'project.xml'))
                + ('' if has_tei else '\n\n' + tr('ui.final.export_project.prepare_pivot')))

    def audit_project_integrity(self):
        """Editorial preflight in plain language; data and links remain untouched."""
        try:
            from .validation import audit_project
            base = self.project.get('pivot_witness_id') or self.reference_box.currentData()
            report = audit_project(self.project, base_witness_id=base, check_paths=True)
            headline = tr('ui.final.audit.summary', errors=report['errors'],
                          warnings=report['warnings'])
            summary = [headline, '']
            for wid, stats in report['summary']['witnesses'].items():
                summary.append(tr('ui.final.audit.witness', witness=wid,
                    active=stats['active_lines'], total=stats['physical_lines'],
                    mapped=stats['mapped_pages'], pages=stats['pages']))
            for pair, stats in report['summary']['pairs'].items():
                summary.append(tr('ui.final.audit.pair', pair=pair,
                    groups=stats.get('correspondences', 0),
                    validated=stats.get('validated', 0),
                    absences=stats.get('confirmed_absences', 0)))
            summary.append('')
            if report['messages']:
                for issue in report['messages']:
                    key = 'ui.audit.issue.' + issue['code']
                    translated = tr(key)
                    detail = translated if translated != key else issue['code'].replace('_', ' ')
                    subject = issue.get('witness') or issue.get('pair') or ''
                    extra = issue.get('detail', '')
                    severity = tr('ui.final.audit.severity.' + issue['severity'])
                    summary.append(f"{severity} — {subject} : {detail}" +
                                   (f" ({extra})" if extra else ''))
            else:
                summary.append(tr('ui.final.audit.noissues'))
            self.progress.setPlainText('\n'.join(summary))
            QMessageBox.information(self, tr('audit.title'), headline + '\n' +
                                    tr('audit.details'))
        except Exception as exc:
            QMessageBox.critical(self, tr('audit.title'), str(exc))

    def refresh(self):
        from .resource_workflow import resource_summary
        self._update_save_indicator()
        self.inventory.clear()
        all_rows = []
        for w in self.project['witnesses']:
            info = resource_summary(self.project, w['id'])
            pivot = ' · ' + tr('resources.witness.pivot_label') if info['pivot'] else ''
            state = tr('resources.project.linked', linked=info['mapped'], pages=info['pages'])
            row = QTreeWidgetItem([f"{w['id']} — {w['label']}" + pivot, state])
            row.setData(0, Qt.ItemDataRole.UserRole, w['id'])
            self.inventory.addTopLevelItem(row)
            for source in w['image_sources']:
                if source['kind'] == 'iiif':
                    detail = (tr('resources.project.manifest_unavailable')
                              if source.get('status') == 'unavailable'
                              else tr('resources.project.manifest_loaded',
                                      pages=len((source.get('manifest') or {}).get('canvases', []))))
                    item = QTreeWidgetItem(row, [tr('resources.witness.manifests'), detail])
                    item.setToolTip(0, str(source['reference']))
                else:
                    item = QTreeWidgetItem(row, [tr('resources.witness.images') + ' · '
                                             + Path(source['reference']).name,
                                             tr('resources.project.image_loaded')])
                    item.setToolTip(0, str(source['reference']))
            for src in w['alto_sources']:
                QTreeWidgetItem(row, [src.get('kind', 'alto').upper() + ' · '
                                          + Path(src['path']).name,
                    tr('resources.project.xml_loaded', lines=src['line_count'])])
            from .tei_binding import tei_binding_status
            for r in self.project.get('text_resources', []):
                if r.get('kind') == 'tei' and r.get('witness_id') == w['id']:
                    QTreeWidgetItem(row, ['TEI · ' + Path(r['path']).name,
                        (tr('tei.binding.status.' + tei_binding_status(self.project, w['id'], r['id'])['status'])
                         if r.get('tei_binding') else tr('resources.project.tei_pending'))])
            all_rows.append(f"{w['id']}: {info['pages']} pages, {info['mapped']} avec XML, "
                            f"{len(physical_lines(w))} lignes")
        self.inventory.expandAll()
        self.page_info.setPlainText('\n'.join(all_rows) if all_rows
                                    else tr('resources.project.no_witness'))
        olda = self.reference_box.currentData()
        oldb = self.target_box.currentData()
        for selector, selection in ((self.reference_box, olda), (self.target_box, oldb)):
            selector.blockSignals(True)
            selector.clear()
            for w in self.project['witnesses']:
                selector.addItem(f"{w['id']} ({len(physical_lines(w))} lignes XML)", w['id'])
            index = selector.findData(selection)
            if (selector is self.reference_box and index < 0
                    and self.project.get('pivot_witness_id')):
                index = selector.findData(self.project['pivot_witness_id'])
            if index >= 0:
                selector.setCurrentIndex(index)
            selector.blockSignals(False)
        if oldb is None and self.target_box.count() > 1:
            self.target_box.setCurrentIndex(1)
        self.align_info.setText(tr('resources.project.alignment_help'))
        self._list_pairs()
        report = '\n'.join(all_rows) + '\n\n'
        report += tr('ui.final.physical_sessions', count=len(self.project.get('pair_sessions', []))) + '\n'
        legacy_count = len(self.project.get('alignment_sessions', []))
        if legacy_count:
            report += tr('ui.final.legacy_sessions', count=legacy_count) + '\n'
        problems = verify_pair_sessions(self.project) + check_alto_files(self.project)
        report += '\n'.join(problems) if problems else tr('ui.final.no_problems')
        self.progress.setPlainText(report)
        self._update_save_indicator()

    def new(self):
        value, ok = QInputDialog.getText(self, tr('project.new'), tr('project.title'))
        if not ok:
            return
        from .core import save_project
        filename = (value.strip() or tr('project.default_name')) + '.vsynch'
        path, _ = QFileDialog.getSaveFileName(self, tr('resources.project.choose_path'),
                                              filename, 'Projet Varians-Synchro (*.vsynch)')
        if not path:
            return
        if not path.lower().endswith('.vsynch'):
            path += '.vsynch'
        if self.path and Path(path).resolve() == Path(self.path).resolve():
            QMessageBox.warning(self, tr('project.new'), tr('resources.project.current_path'))
            return
        if not self._confirm_save_or_discard():
            return
        new_data = new_project(value.strip() or tr('project.default_name'))
        try:
            save_project(new_data, path)
        except Exception as exc:
            QMessageBox.critical(self, tr('project.save_error'), str(exc))
            return
        # Only replace the in-memory document after the new file is saved.
        self.project = new_data
        self.path = path
        self._changes.reset(self.project)
        self.refresh()

    def open(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('ui.ouvrir.un.projet'), '', 'Projet (*.vsynch)')
        if not path:
            return
        try:
            incoming = load_project(path)
        except Exception as exc:
            QMessageBox.critical(self, tr('project.open_error'), str(exc))
            return
        if not self._confirm_save_or_discard():
            return
        # The previous indentation made this assignment unreachable:
        # the window displayed an empty project while pointing at the
        # selected .vsynch file. Never reset the saved baseline before
        # replacing the in-memory document.
        self.project = incoming
        self.path = path
        self._changes.reset(self.project)
        self.refresh()

    def save(self) -> bool:
        """Return False on Save As cancellation or write failure."""
        path = self.path or QFileDialog.getSaveFileName(
            self, tr('common.save'), 'projet.vsynch',
            'Projet Varians-Synchro (*.vsynch)')[0]
        if not path:
            return False
        try:
            save_project(self.project, path)
        except Exception as exc:
            QMessageBox.critical(self, tr('project.save_error'), str(exc))
            return False
        self.path = path
        self._changes.mark_saved(self.project)
        self._update_save_indicator()
        return True

    def choose_witness(self):
        opts=[f"{w['id']} — {w['label']}" for w in self.project['witnesses']]
        if not opts:
            self.notice(tr('Témoins'),'Créez d’abord un témoin.');return None
        chosen,ok=QInputDialog.getItem(self,'Témoin','Choisissez un témoin',opts,0,False)
        return self.project['witnesses'][opts.index(chosen)] if ok else None

    def add_witness(self):
        dialog = WitnessResourceDialog(self.project, parent=self)
        if _run_modal(dialog) == QDialog.DialogCode.Accepted:
            self.refresh()
            self._select_pivot()

    def batch_bind_from_pages(self):
        witness = self.choose_witness()
        if witness is None:
            return
        try:
            dialog = BatchBindingDialog(witness, self)
            if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, tr('resources.binding.title'), str(exc))

    def manage_pages(self):
        w=self.choose_witness()
        if w is None:return
        dlg=PagesDialog(self.project,w,self);_run_modal(dlg);self.refresh()

    def _list_pairs(self):
        """Une ligne par paire enregistrée, avec l'identifiant de sa session
        (aucun pour une ligne d'erreur ou « aucune synchronisation »). La
        ligne choisie est gardée ; les menus ne bougent pas."""
        pairs = self.align_status
        current = pairs.currentItem()
        kept = current.data(Qt.ItemDataRole.UserRole) if current is not None else None
        pairs.blockSignals(True)
        pairs.clear()
        for session in self.project.get('pair_sessions', []):
            try:
                progress = pair_progress(self.project, session)
            except ValueError as exc:
                pairs.addItem(QListWidgetItem(str(exc)))
                continue
            item = QListWidgetItem(tr(
                'ui.alignment.pair_status', reference=session['reference_witness_id'],
                target=session['target_witness_id'], groups=progress['links'],
                reference_covered=progress['reference_covered'],
                reference_total=progress['reference_total'],
                target_covered=progress['target_covered'], target_total=progress['target_total']))
            item.setData(Qt.ItemDataRole.UserRole, session['id'])
            pairs.addItem(item)
            if session['id'] == kept:
                pairs.setCurrentItem(item)
        if not pairs.count():
            pairs.addItem(QListWidgetItem(tr('resources.project.no_alignment')))
        pairs.blockSignals(False)

    def _listed_session(self, item):
        sid = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return next((s for s in self.project.get('pair_sessions', []) if sid and s['id'] == sid), None)

    def _choose_listed_pair(self, item, _previous=None):
        """Un clic sur une paire la met dans les deux menus, dans son sens."""
        session = self._listed_session(item)
        if session is None:
            return
        for box, wid in ((self.reference_box, session['reference_witness_id']),
                         (self.target_box, session['target_witness_id'])):
            index = box.findData(wid)
            if index >= 0:
                box.setCurrentIndex(index)

    def _open_listed_pair(self, item):
        """Double-clic ou Entrée : la synchronisation de la paire, comme le bouton."""
        session = self._listed_session(item)
        if session is not None:
            self._open_pair(session['reference_witness_id'], session['target_witness_id'])

    def open_physical_alignment(self):
        a=self.reference_box.currentData();b=self.target_box.currentData()
        if not a or not b:
            self.notice(tr('Alignement'),'Ajoutez au moins deux témoins.');return
        self._open_pair(a, b)

    def _open_pair(self, a, b):
        try:
            session=create_pair_session(self.project,a,b)
            dlg=PairDialog(self.project,session,self);_run_modal(dlg);self.refresh()
        except Exception as exc:
            QMessageBox.warning(self,tr('Synchronisation'),str(exc))
