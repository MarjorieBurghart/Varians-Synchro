## V0.6.15

Ajout des clés bilingues `export.varians.*` dans `i18n/fr.xml` et `i18n/en.xml` : dialogue de choix de la référence, avertissement sur la TEI et confirmation du dossier de sortie.

## V0.6.7 — Diagnostics des colonnes

Les nouveaux messages d'échec (colonnes trop différentes, liens existants incompatibles, ancrages non exploitables) ainsi que le compteur des lignes proposées disposent de traductions FR/EN dans `varians_synchro/i18n.py`.

---

## V0.6.6 — Navigation réciproque

Textes français/anglais ajoutés : instruction de clic sur les cadres liés, légende incluant le rose, message de correspondance affichée, absence confirmée et ligne sans correspondant. Les libellés des images et les HTR ne sont jamais traduits.

## V0.6.5 — Nouveaux libellés bilingues

Le sélecteur **Cadres visibles / Visible frames** propose **Toutes les lignes / All lines**, **Lignes non synchronisées / Unlinked lines** et **Synchronisations automatiques à vérifier / Automatic links to review**. Ces libellés sont traduits dans `varians_synchro/i18n.py`, sans toucher aux données sources.

# Internationalisation — architecture et principes

Le module `varians_synchro/i18n.py` expose :

- `get_language()` / `set_language('fr'|'en')` ;
- `tr(texte_source)` avec repli sur le français en cas de message non traduit ;
- `translate_template(...)` pour les messages paramétrés.

Les libellés français existants sont utilisés comme clés de la première version du catalogue anglais (`EN`). La sélection de langue est mémorisée par `QSettings('Varians','Varians-Synchro')`, et la fenêtre principale est reconstruite sans recréer de `QApplication`. La référence du projet en mémoire est conservée : aucun enregistrement ou modification des données sources n'est impliqué.

Les principales commandes de la nouvelle interface sont localisées via des composants PySide6 minces (boutons, labels, sélecteurs, en-têtes, titres de fenêtres et boîtes de dialogue). Les chaînes purement documentaires — transcriptions TEI/HTR, identifiants, labels de folio, chemins, URL et texte manuscrit — ne doivent **jamais** être traduites.

**État de traduction V0.6.2 :** les nouvelles pages guidées et les commandes d'alignement visuel ont un premier catalogue français/anglais. Des messages d'erreur issus du noyau et la fenêtre TEI historique héritée restent en français ; la couverture complète, la révision terminologique et des tests Qt natifs restent à réaliser dans les versions suivantes. Avant l'ajout d'autres langues, il faudra migrer les identifiants de messages vers des clés symboliques stables et vérifier les pluriels et la localisation des nombres.

**V0.6.3 :** le nouvel accès « Effacer sélection » et son aide contextuelle sont traduits (EN : « Clear selection »). Le libellé « Texte HTR » conserve sa traduction « HTR text » ; les données reconnues ne sont pas traduites.


## V0.6.4

Le code couleur des overlays de synchronisation visuelle dispose désormais d'une légende bilingue dans l'interface.


## V0.6.9

Les messages de confirmation de recalcul des propositions automatiques sont localisés par clés stables `alignment.recalculate.*` dans `i18n/fr.xml` et `i18n/en.xml`. Aucune chaîne traduite n’est intégrée au moteur d’interpolation.


## V0.6.11 — périmètre des lignes et nouvelle palette

Les entrées `scope.*` décrivent les actions d'exclusion/réintégration et la légende de l'overlay. Elles sont présentes dans les deux catalogues XML, au même format que Varians. Un statut de ligne dans les données `.vsynch` est toujours un identifiant métier invariant, pas une traduction.


## V0.6.12

Clés XML ajoutées dans `i18n/fr.xml` et `i18n/en.xml` : `viewer.polygon_count` et `viewer.no_polygon`. Le diagnostic est traduit ; les libellés des témoins et manuscrits ne sont jamais traduits.

## V0.6.13

Les libellés ALTO/PAGE des gestionnaires de projet, d'association de pages et du visualiseur ont été ajoutés dans les catalogues XML `i18n/fr.xml` et `i18n/en.xml`, avec des clés stables `ui.xml.*`. Les appellations scientifiques (PAGE-XML, ALTO, `Coords`, `TextEquiv`) restent identiques dans les deux langues.


### V0.6.14 — Libellés du viewer et des nouvelles opérations

Les deux catalogues `i18n/fr.xml` et `i18n/en.xml` contiennent la même clé `viewer.alto.toggle`, dont la nouvelle traduction est « Cadres lignes » / « Line outlines ». Les messages de prévisualisation et de diagnostic du second passage ont des clés explicites `alignment.residual.*` dans les deux langues. Les changements d'interface doivent être répercutés dans **tous** les catalogues livrés.


## V0.8.5.5 — Couverture des sept catalogues

Les 244 replis anglais identifiés dans chacun des catalogues de/cs/it/ru/ja ont été traduits : 653/653 entrées remplies dans chaque langue ; clés et paramètres de substitution contrôlés. Cela ne signifie pas que les traductions aient reçu une validation par des locuteurs natifs. Une vérification du vocabulaire critique, des pluriels et du rendu Qt reste nécessaire, voir `docs/I18N_NATIVE_REVIEW_V0855.md`. La liste historique des clés concernées est conservée dans `docs/i18n_completed_v0855.txt`.
