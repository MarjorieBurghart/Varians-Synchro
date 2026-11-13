# Interface PySide6 et internationalisation

## Composition UI

`gui.main()` crée l'application Qt et instancie la fenêtre rendue par `guided_ui.make_guided_window()` (`ui_main_window.GuidedWindow`) ; chaque fenêtre de l'interface a son module `ui_*` (liste dans `03_CARTE_DU_CODE.md`). `viewer.py` fournit des widgets de visualisation et de sélection de lignes, zoom et chargement d'images ; `qt_lifecycle.py` encapsule le cycle de vie. `QSettings('Varians', 'Varians-Synchro')` conserve la langue de l'application. Le projet courant, son chemin et les modifications non sauvegardées sont des **données du document**, pas une préférence QSettings.

Le code des fenêtres est dense, celui de `ui_pair.py` surtout. Ses quatre fenêtres de propositions passent par `ui_proposals.ProposalReviewDialog` ; leur comportement (présélection, confirmation, sélection vide) est décrit par `tests/test_pair_proposals_qt.py`. Préserver les frontières « lecture → prévisualisation → confirmation → mutation → sauvegarde » lors de tout découpage. Éviter d'importer PySide6 dans les modules métier, et dans `guided_ui.py` hors de `make_guided_window` ; cela permet audits et tests sans serveur graphique (`tests/test_ui_modules.py`).

## Contrats ergonomiques

- Créer un projet et l'enregistrer immédiatement, sans demander de configuration TEI ou de Manifests.
- La fiche témoin doit rester transactionnelle : fermeture/annulation sans mutation partielle.
- À l'ouverture d'un nouveau projet, **ne pas** écraser `self.project` tant que lecture et validation n'ont pas réussi. À la création, ne pas remplacer le document courant si le dialogue est annulé. Régressions traitées historiquement en v0.8.1.2.
- Le changement de langue reconstruit l'interface mais **ne remplace pas le projet actif**. Vérifier les modifications non enregistrées et les sélections.
- Une sélection de lignes comporte le clic exclusif simple, Ctrl+clic additif et Maj+clic plage selon l'ordre réel ; l'état de surlignage ne doit pas changer les liens enregistrés.
- Les interactions de téléchargement/réseau ne doivent pas bloquer le fil UI ; signaler annulation et téléchargement achevé distinctement.
- Un appel différé (« quand la boucle d'événements reprend la main ») passe par `ui_widgets.call_soon(fenêtre, fonction)`, jamais par `QTimer.singleShot(0, …)` : ce dernier appelait la fonction même après la destruction de la fenêtre (vignettes demandées juste avant la fermeture), d'où « Internal C++ object already deleted ». La forme `QTimer.singleShot(0, fenêtre, fonction)` n'existe pas dans PySide6 6.6, version minimale. Test : `tests/test_deferred_calls_qt.py`.

## Fenêtre « Liaison TEI » : brouillon

`TEIPhysicalBindingDialog` travaille sur une copie du projet : « Réanalyser le fichier TEI » et la liaison ne touchent que ce brouillon ; « Appliquer » reporte les ressources TEI dans le projet, « Annuler » ferme sans rien changer. Test : `tests/test_tei_binding_cancel_qt.py`.

## Erreurs imprévues

`error_report.install()` (appelé par `gui.main`) pose un crochet sur `sys.excepthook` : une exception levée dans une action de l'interface (slot Qt) reste écrite dans la console ou le journal, et un message « Action impossible » s'affiche en plus (`error.unexpected.*`, traduit ; le texte de l'erreur l'est s'il figure dans les catalogues). Auparavant, rien ne se passait à l'écran. Test : `tests/test_error_report_qt.py`.

Journal des erreurs : `gui.main` l'ouvre d'abord (`error_log_ui.install_for_application`), avant ce crochet. Le fichier `varians-synchro.log` (dossier : `error_log.log_dir`, ou `VARIANS_SYNCHRO_LOG_DIR`) reçoit les exceptions non rattrapées (fil principal et autres fils), les erreurs montrées (`errors.localized_text`, avec leur pile si elles ont été levées) et les Manifests IIIF qui n'ont pas répondu (`resource_workflow`). La boîte « Action impossible » dit alors où le détail est noté (`error_log.noted`) et son bouton « Journal des erreurs » ouvre le dossier, comme celui de la fenêtre d'aide (`error_log_ui.open_log_folder`). Le journal ne gêne jamais : s'il ne peut pas être écrit, rien ne change. Pendant les tests, il va dans un dossier temporaire (`tests/conftest.py`). Tests : `tests/test_error_log.py`, `test_error_log_sources.py`, `test_error_log_qt.py`.

## Aide intégrée

Le guide utilisateur est `help/<langue>.html` (repli sur `help/fr.html`). `ui_help.open_help(parent, anchor=None)` l'affiche dans une fenêtre **non modale** (`HelpDialog`, un `QTextBrowser`), une par fenêtre parente et gardée d'une ouverture à l'autre : bouton « Ouvrir le guide utilisateur » et F1 dans la fenêtre principale ; F1 dans la fenêtre de synchronisation ouvre la section `id="synchronisation"`, l'aide étant alors l'enfant de cette fenêtre modale, donc utilisable. Les liens vers le web s'ouvrent dans le navigateur, les liens internes (`#…`) dans la fenêtre. Recherche reprise de Varians : `help_search.py` (sans Qt ; accents, casse et signes typographiques ignorés ; tous les mots dans une même section ; expression entre guillemets), liste des sections avec extrait, occurrences surlignées, ◀ ▶, F3/Maj+F3, Ctrl+F. Le guide doit garder un titre (`<h2>`/`<h3>`) par section : la recherche découpe l'aide sur ses titres, et ignore le sommaire (fait de liens).

**Écrire le guide.** Chaque libellé d'interface cité est balisé : `<b class="ui" data-tr="clé">…</b>` (clé du catalogue de Varians-Synchro, ou texte littéral du code) ou `<b class="varians" data-varians="clé">…</b>` (catalogue de Varians, `VARIANS_SOURCE` ou `../Varians`). `python tools/help_labels.py` remplit ces balises d'après les catalogues de la langue du guide (sans deux-points final) ; `--check` liste les écarts. Les champs du format JSON sont balisés `<code class="field">` dans la section `format-json` : `tests/test_help_guides.py` vérifie qu'ils sont exactement ceux que l'export écrit, que les sept guides ont les mêmes sections (`id`) et que les liens internes mènent quelque part. Un libellé ou un champ qui change dans le code fait donc échouer ce test, jusqu'à la mise à jour du guide. Tests : `tests/test_help_search.py`, `tests/test_help_window_qt.py`.
## Étape 3 : liste des paires

Sous le bouton « Aligner les témoins », `GuidedWindow.align_status` (`_PairList`) liste une ligne par session de `pair_sessions` (`ui.alignment.pair_status`), avec l'identifiant de la session en `Qt.ItemDataRole.UserRole` ; une ligne d'erreur ou « aucune synchronisation » n'en a pas et reste inerte. Un double-clic ou Entrée (traitée par la liste elle-même : sous macOS, Entrée n'active pas un élément) ouvrent la paire par le même chemin que le bouton (`_open_pair` → `create_pair_session`, qui rend la session existante, dans son sens) ; un simple clic (`currentItemChanged`) met la paire dans les deux menus. `_list_pairs` reconstruit la liste à chaque `refresh`, signaux bloqués : la ligne choisie est gardée et les menus ne bougent pas. Test : `tests/test_alignment_list_qt.py`.

## Icône de l'application

`gui.main` passe `app_icon.application_icon` à `qt_lifecycle.launch`, qui l'appelle une fois l'application Qt créée : l'icône devient celle de l'application (toutes ses fenêtres, boîtes sans parent comprises) quand Varians-Synchro possède l'application, et seulement celle de sa fenêtre principale dans la console Qt d'un autre programme. Sous Windows, `app_icon.use_own_taskbar_entry` donne au processus l'identité `Varians.VariansSynchro` (`SetCurrentProcessExplicitAppUserModelID`) avant la première fenêtre ; sans elle, la barre des tâches range la fenêtre sous `python.exe` et montre l'icône de Python. Elle n'est prise que si l'application Qt n'existe pas encore.

Les PNG de `icons/` (16 à 256 px) et `icons/varians_synchro.ico` sont produits par `python tools/generate_icons.py` (Pillow requis, seulement pour ce script) à partir du logo `logo/*.psd` : le logo est centré sur une pastille blanche aux coins arrondis, lisible sur une barre des tâches sombre. Après une modification du logo, relancer le script et livrer les fichiers produits. Tests : `tests/test_app_icon.py`, `test_app_icon_qt.py`, `test_qt_lifecycle.py`.

## Catalogues XML

Sept catalogues : `i18n/fr.xml`, `en.xml`, `de.xml`, `cs.xml`, `it.xml`, `ru.xml`, `ja.xml`. Dans v0.8.5.5 et v0.8.5.6 : **653 clés remplies par langue**, paramètres de format conservés. `i18n.py` contrôle balise racine, unicité/présence des clés, égalité des ensembles de clés et ensembles de paramètres `{variable}` ; `tr(key,**values)` ne modifie jamais les entrées métier inconnues. `translate_template` délègue à `tr`. Les valeurs françaises historiques peuvent servir d'alias pour les appels anciens.

Les messages des exceptions levées par le moteur (`raise ValueError('…')` en français, par exemple dans `physical_alignment.py`) sont traduits à l'affichage : leur texte français est la valeur d'une clé du catalogue (`alignment.error.*`), donc un alias que `tr` reconnaît, et les boîtes de message de `ui_widgets` passent leur texte par `tr`. `tests/test_alignment_errors_i18n.py` vérifie que chaque message de `physical_alignment.py` est au catalogue : un nouveau message doit y être ajouté, dans les sept langues, avec exactement le même texte français.

En cas d'ajout d'une chaîne : créer une clé stable, ajouter sept valeurs, conserver exactement les mêmes paramètres de format et faire passer `tests/test_i18n.py`, `test_i18n_xml_catalogs.py` et `test_i18n_full_0855.py`. Ne pas localiser JSON persisté, identifiants, sigles, chemins ni noms de balises/attributs XML.

## À ne pas confondre

- 653/653 **entrées présentes** n'implique pas 653 traductions **validées par locuteur natif**.
- Les traductions japonaises ecdotiques, les distinctions « absence / omission » et les pluriels tchèques/russes méritent une validation humaine ciblée. Voir `docs/I18N_NATIVE_REVIEW_V0855.md`.
- Le moteur vérifie la conformité **syntaxique des catalogues** et des placeholders, pas la clarté de l'interface lorsque des étiquettes sont longues ou coupées. Tester sous toutes les langues avec Qt.

## Précautions Spyder

`run.py` teste `spyder_launch.in_spyder_kernel` puis peut lancer l'application dans un autre processus pour éviter le conflit entre bindings Qt/plugins de Spyder. Conserver l'interpréteur choisi et filtrer soigneusement les variables d'environnement Qt ; ne pas « corriger » un crash natif en faisant passer artificiellement les tests. Si PySide6 est absent : installer dans le **même** environnement Python que celui qui lance réellement l'application.

**Tests clés** : `tests/test_qt_lifecycle.py`, `test_spyder_launch.py`, `test_project_open_creation_regression_0812.py`, `test_unsaved_changes.py`, `test_selection_gui_qt_0842.py`, `test_i18n_full_0855.py`.
