# Architecture de Varians-Synchro

Ce document décrit, thème par thème, les modules du logiciel et les choix qui les gouvernent. Il a été écrit au fil des versions : la version qui a introduit chaque mécanisme est indiquée entre parenthèses. La carte complète du code est au chapitre [03 du dossier de passation](../../MAINTENANCE_PASSATION_V0856/03_CARTE_DU_CODE.md), les flux de données au [chapitre 02](../../MAINTENANCE_PASSATION_V0856/02_ARCHITECTURE_ET_FLUX.md) ; le format des fichiers est dans [`FORMAT_PROJET.md`](FORMAT_PROJET.md) et l'export dans [`EXPORT_VARIANS.md`](EXPORT_VARIANS.md).

## Principes

- Les modules `core`, `imaging`, `physical_alignment`, `alignment`, `automatic` et `review` n'importent pas Qt ; ils sont testables sans interface graphique.
- Les fenêtres (modules `ui_*`, une par module) orchestrent les cas d'usage et appellent les services, sans écrire de TEI ou d'ALTO.
- `gui.py` lance l'application ; `guided_ui.make_guided_window` fournit la fenêtre principale (`ui_main_window.GuidedWindow`) et ne charge PySide6 qu'à son appel.
- `qt_lifecycle.py` protège le singleton QApplication lorsque l'application est lancée dans Spyder.
- `ui_help.py` affiche le guide utilisateur (`help/<langue>.html`, repli sur le français ; libellés cités vérifiés par `tools/help_labels.py` et `tests/test_help_guides.py`) dans une fenêtre non modale du logiciel (F1), avec la recherche de Varians (`help_search.py`, sans Qt).
- `app_icon.py` fournit l'icône de l'application (PNG de `icons/`, produits à partir de `logo/*.psd` par `tools/generate_icons.py`) et, sous Windows, l'identité propre du processus dans la barre des tâches.

Ne jamais modifier `physical_alignment.py`, `reading_stream.py`, `textual_progress.py`, `varians_export.py` sans tests spécifiques de non-régression : les identifiants déjà utilisés dans Varians doivent rester stables.

## Deux familles de sessions

### `pair_sessions` (V0.6)

Session autonome `physical-pair` avec `reference_witness_id` et `target_witness_id`. Ces noms expriment uniquement les rôles de comparaison. Chaque lien contient `reference_ids[]`, `target_ids[]`, statut, origine et empreintes documentaires. Ce sont elles que l'export convertit en fichiers de synchronisation pour Varians, avec des clés de lignes physiques du pivot.

Une ligne physique reçoit un ID déterministe calculé depuis `witness_id`, `page_id` et son ordinal dans l'ALTO associé. Le modèle conserve également `alto_id` et une empreinte SHA-256 du contenu/rectangle pour **détecter** une modification : une détection n'implique ni renumérotation ni destruction du lien.

### `alignment_sessions` (héritage V0.3–V0.5)

Session construite autour d'un `base_resource_id` TEI et d'un `target_witness_id` ; ses `base_keys` alimentent les JSON compatibles Varians. Les conventions ne sont pas modifiées.

## Sources ALTO / PAGE (V0.6.13)

`core.inspect_line_source` détecte la racine XML et choisit `core.inspect_alto` ou `page_xml.inspect_page_xml`. Une source contient `kind="alto"` ou `kind="page"` et le modèle commun `pages[].lines[]` (`alto_id` identifiant historique générique, `text`, `bbox`, `polygon`). Les points PAGE proviennent de `TextLine/Coords` et restent dans le système de coordonnées source, sans recalage artificiel. `core.add_line_source` est la nouvelle API, `add_alto_source` demeure alias compatible.

`imaging.mapped_line_page`, `bind_line_source`, `suggest_line_bindings` sont des alias génériques des anciennes fonctions `mapped_alto_page`, `bind_alto`, `suggest_alto_bindings`. Les champs JSON `alto_sources` et `alto_binding` ne sont pas renommés : cela préserverait les identifiants, caches et projets existants. La source active de chaque page est un choix, et non une fusion automatique de deux segmentations.

`page_xml.py` interprète les namespaces PAGE par nom local, extrait les alternatives de HTR directement sur les `TextLine`, lit les régions dans l'ordre PAGE `ReadingOrder` puis les lignes de chaque région dans l'ordre du document. Les lignes sans `Coords` sont explicitement comptabilisées comme non exploitables.

Le moteur physique reste indépendant du format de transcription et n'exige aucun texte de référence. La sauvegarde ne modifie jamais le PAGE ni l'ALTO.

## Géométrie des lignes (V0.6.12)

`varians_synchro/alto_geometry.py` décode les `Shape/Polygon` des `TextLine` et fournit les contours au visualiseur. Le stockage de `polygon` est facultatif, compatible avec les anciens `.vsynch`. Pour ceux-ci, une lecture à la demande dans l'ALTO source récupère les polygones si le fichier est inchangé, après contrôle des indices, identifiants et bbox, sans altérer le modèle enregistré. Le visualiseur représente les polygones en coordonnées de l'image téléchargée via `sx/sy` et utilise les mêmes polygones pour la zone cliquable ; le moteur d'alignement continuera à exploiter les rectangles sources. Aucun recalage inventé. Les tests pure-Python valident les calculs ; les tests Qt sont optionnels.

## Ordre des pages et visualisation (V0.6.1)

- `page_order.py` centralise l'ordre documentaire (`ordered_pages`) sans réécrire les identifiants ni les liens sauvegardés. Ordre de Canvas IIIF prioritaire ; tri par folios ou noms naturels pour les images locales ; un `reading_order` explicite sera respecté s'il est renseigné pour toutes les pages.
- `physical_alignment.physical_lines()` réutilise cet ordre, ce qui corrige aussi la vue textuelle des projets V0.6.0.
- `viewer.LineImagePanel` est un composant réutilisable par témoin : page, zoom, dessin/interaction des rectangles, sélection persistante des identifiants de lignes. `PageViewer` reste une enveloppe compatible avec l'aperçu d'une page.
- `ui_pair.PairDialog` utilise deux `LineImagePanel` en parallèle comme mode principal et réserve les listes HTR à un onglet secondaire.
- L'image est chargée dans un QThread ; les `QPixmap` et objets graphiques sont créés uniquement dans le fil de l'interface. Une réponse IIIF tardive ne remplace pas l'image d'une autre page (compteur de requête).
- Pour une image IIIF, la demande initiale est limitée à une largeur de 4 200 pixels, avec replis en cas de refus explicite de taille ; pas de téléchargement de l'intégralité du Manifest.
- Les rectangles ALTO sont projetés par des coefficients de redimensionnement `largeur image / largeur ALTO`, `hauteur image / hauteur ALTO`. Ce calcul n'est pas suffisant pour les documents recadrés/tournés ; ces cas requièrent une calibration future.

## Flux de lecture (V0.7)

Le module `varians_synchro/reading_stream.py` convertit l’inventaire physique en un flux ordonné indépendamment des limites de page. Les fonctions publiques `reading_stream`, `anchor_intervals`, `set_page_order`, `set_region_order`, `set_line_order` ne modifient pas les identifiants `line_uid` et ne réécrivent pas les sources XML. Elles préparent le futur moteur cumulatif (V0.7.1) ; l’interpolation géométrique historique reste séparée en V0.7.0. Voir [`REFONTE_V0.7.0.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/REFONTE_V0.7.0.md).

## Ressources et association par lots (V0.8.0–V0.8.1)

`resource_workflow.py` fournit l'import documentaire groupé **atomique au niveau du projet** : les sources sont inspectées dans une copie complète, puis seules les nouvelles données confirmées sont publiées ; le changement d'un sigle existant est interdit pour ne pas casser les liens enregistrés. `pivot_witness_id` est un nouveau champ facultatif de projet, sans migration de `format` / `version`.

`bulk_binding.py` fournit le noyau d'appariement image ↔ source ALTO/PAGE. Il prépare une structure de prévisualisation et son empreinte (IDs pages, ordre, associations courantes, empreintes sources). Après choix explicite de l'utilisateur, le commit refuse les duplications et ressources modifiées et ne réécrit aucun identifiant ni ordre. Le repli par ordre naturel est limité aux lots locaux de même cardinalité et déclenche une confirmation particulière. L'affichage des miniatures est différé aux rangées visibles.

`ui_resources.py` contient une fiche de témoin transactionnelle (`WitnessResourceDialog`) et `ui_batch_binding.py` un tableau éditable d'associations (`BatchBindingDialog`). `gui.py` est maintenant un lanceur minimal sans l'ancienne fenêtre V0.5. Le parseur TEI ancien est conservé **uniquement pour la lecture des données historiques et leurs tests**, pas pour générer de nouvelles liaisons éditoriales : `store_tei_reference` crée une entrée `tei_unaligned` ; la liaison des `<lb/>` aux lignes physiques est faite par `tei_binding.py` (V0.8.2–V0.8.3).

`resource_removal.py` retire une ressource enregistrée ou un témoin : `removal_impact` dit, sans rien changer, ce que le retrait entraîne (pages retirées ou libérées, lignes perdues, groupes touchés, synchronisations) ; `remove_resource` et `remove_witness` l'appliquent d'un bloc sur une copie. Les groupes qui touchent des lignes disparues ne sont pas effacés : ils deviennent périmés (`link_is_stale`). Le témoin pivot ne peut pas être retiré ; aucun fichier n'est supprimé du disque. Dans la fiche du témoin, les retraits demandés s'appliquent au brouillon, donc à « Enregistrer le témoin ».

## Périmètre des lignes (V0.6.11)

`varians_synchro/line_scope.py` est le modèle de gestion des lignes « ignorées » au niveau de chaque témoin. Il conserve leur état dans `ignored_line_ids`, vérifie les références ALTO, contrôle les conflits avec toutes les sessions physiques, prépare les ajustements par copie limitée des sessions, puis effectue le commit final (source ALTO jamais éditée). Les anciennes sessions TEI directement concernées sont protégées par refus explicite.

`physical_alignment.py` exclut ces identifiants des nouvelles associations, des statistiques actives et des propositions HTR. `alignment.target_lines()` filtre également le flux HTR secondaire sans renuméroter les lignes. `interpolation.py` les exclut avant l'extraction et le classement géométriques. Le visualiseur `viewer.py` les colore via un style sémantique `ignored` ; les filtres demeurent indépendants du stockage.

## Moteur principal : progression textuelle (V0.7.1)

`reading_stream.py` forme les lignes physiques continues. `textual_progress.py` estime une progression textuelle normalisée (HTR quantitative → longueur de ligne → poids uniforme) et propose des groupes entre repères validés, en respectant toutes les associations protégées. `ui_pair.py` propose une prévisualisation avec sélection et n’enregistre rien sans confirmation. `physical_alignment.replace_revisable_pair_proposals()` applique atomiquement des changements limités aux propositions automatiques encore incertaines. `varians_export.py` exporte les JSON toujours conformes aux clés physiques `page_id::ordinal` pour Varians.

**Les couches de sources ALTO/PAGE, les images IIIF/locales, la TEI et les identifiants des lignes demeurent inchangés.** Les anciens modules `interpolation.py` et `residual_alignment.py` sont seulement conservés sous le menu de compatibilité ; ils ne sont plus le chemin principal. La V0.7.1 n’invente pas d’absence et ne vérifie pas le contenu philologique des deux textes. La production automatisée de n↔m plus fins et l’ergonomie de vérification seront perfectionnées après les tests utilisateurs.

---

## Proposition automatique HTR–HTR

`suggest_htr_pair_alignment()` construit **en mémoire uniquement** une représentation textuelle des lignes ALTO du pivot et appelle le comparateur de séquences déjà présent dans `automatic.py`. Les liens existants servent d'ancrages protégés. Les résultats sont traduits immédiatement vers les identifiants physiques avant sauvegarde : aucune fausse TEI n'est ajoutée au projet.

Le moteur reste heuristique : il peut échouer sur les passages répétés, les variantes importantes ou les transpositions. La confiance est une estimation algorithmique, pas une validation philologique.

## Interpolation géométrique de colonnes (V0.6.7)

Le module `varians_synchro/interpolation.py` isole désormais les lignes de l'intervalle par leurs rectangles et identifiants physiques, et non par une tranche de l'ordre de lecture ALTO. `_column_interval()` vérifie la page, la cohérence horizontale de la colonne et les bornes verticales, puis trie les lignes par centre géométrique. `_partition()` calcule ensuite une association monotone par programmation dynamique ; la HTR n'intervient que comme éventuel petit terme de préférence. `_unlinked_segments()` découpe les espaces libres autour des groupes déjà liés sans toucher aux groupes existants. Les propositions restent `uncertain`, avec la provenance `interpolated-geometry`.

Le calcul ne déduit aucune absence, aucune identité textuelle certifiée ni aucune transposition à partir des seules coordonnées.

---

## Recalcul sans perte des ancrages humains (V0.6.9)

Dans `interpolation.suggest_between_anchors(..., regenerate_automatic=True)`, les liens provisoires `origin=interpolated-*` ou `origin=automatic-*` sont exclus des barrières d’extraction. Ils restent intacts pendant la prévisualisation. Les liens manuels (même incertains), validés et les absences confirmées demeurent des contraintes fortes.

Dans `physical_alignment.replace_revisable_pair_proposals`, le remplacement est effectué sur une copie de la session. Une ancienne proposition automatique incertaine n’est éliminée que si l’ensemble de ses lignes, côté référence **et** côté cible, est couvert par les nouvelles propositions sélectionnées. Les recouvrements partiels non sûrs sont ignorés. Le commit n’intervient que si toutes les insertions retenues ont réussi.

L’interface `PairDialog.interpolate()` active explicitement le mode de recalcul, affiche la prévisualisation et requiert une confirmation avant remplacement. L’API métier conserve le paramètre `regenerate_automatic=False` par défaut afin de ne pas surprendre les clients historiques.

## Second passage résiduel (V0.6.14)

`varians_synchro/residual_alignment.py` exploite les `physical_lines` normalisées : ALTO ou PAGE ne change pas l'algorithme, et les polygones PAGE restent destinés au rendu visuel.

`*suggest_residual_extensions(project, pair_session)*` (fonction réelle : `suggest_residual_extensions`) calcule sans effet secondaire les lignes résiduelles, évalue un voisin de même colonne et de même folio et refuse un voisin si une ligne libre correspondante est susceptible d'exister sur l'autre témoin. Les propositions sont limitées en distance et en effectif.

`apply_residual_extensions` est transactionnel : il vérifie d'abord l'origine et le statut des groupes, les empreintes et les identifiants des membres, les lignes candidates et l'absence de conflit. Il met à jour une copie du tableau des liens et ne remplace l'état courant qu'en cas de réussite intégrale.

Aucune proposition n'est automatiquement validée. Les corrections humaines sont protégées par `is_revisable_automatic`, distinct de la présence ou non de HTR. Le format projet `physical-pair` ne change pas.

## Édition des groupes (V0.6.10)

`varians_synchro.physical_alignment.extend_pair_link(project, session, reference_ids, target_ids)` détecte une et une seule association préexistante parmi les lignes sélectionnées, puis fusionne les lignes restées libres dans cette association, sans modifier son identifiant ni d’autres groupes. Les sélections touchant plusieurs liens distincts sont rejetées : aucune fusion silencieuse de preuves philologiques. Le lien est marqué `origin=manual-correction`, et la correction datée est ajoutée à `evidence.manual_corrections`. Il conserve son statut antérieur (notamment `uncertain`). `is_revisable_automatic()` le protège dès lors du recalcul.

`detach_pair_lines(project, session, reference_ids, target_ids)` travaille sur une copie des liens et enlève **les seules lignes sélectionnées**, sur l’un ou les deux témoins. Si une correspondance conserve des membres des deux côtés, elle est mise à jour ; si un côté devient vide, le groupe est supprimé. L’absence textuelle n’est jamais induite de cette suppression. `remove_pair_link()` reste réservé à la suppression intégrale d’un groupe identifié explicitement.

La fenêtre `PairDialog` offre désormais trois parcours non ambigus : **Associer** (créer ou étendre), **Dissocier** (retirer les lignes sur les images) et **Autres opérations → Supprimer les groupes sélectionnés** (effacer les groupes de la liste après confirmation). Une consultation réciproque en rose ne crée pas de sélection de travail.

## Navigation entre témoins (V0.6.6) et sélection (V0.8.4.2)

`varians_synchro/correspondence_navigation.py` indexe les groupes `pair_sessions[*].links` dans les deux sens, sans aucune opération sur les sources ni sur les sélections. `LineImagePanel.line_clicked` est émis uniquement après un clic intentionnel sur un cadre ALTO ; `PairDialog` s’appuie sur ces index pour demander au panneau opposé `show_counterparts()`. Les identifiants correspondants sont conservés exclusivement dans `_counterpart_ids`, distinct de `_selected`. La priorité graphique est : sélection orange > consultation rose > état des liens > lignes non associées. Les filtres ne masquent jamais la consultation ou la sélection. Le changement de folio reste asynchrone (contrôle `_request_serial` existant), et le centrage sur la nouvelle image a lieu après que les rectangles ALTO ont été créés. Aucun changement du schéma .vsynch.

`varians_synchro/selection_policy.py` est une politique de sélection pure, à identifiants physiques stables, indépendante de Qt et des formats d'enregistrement. Le widget `WitnessLineList` détourne seulement les clics de souris explicites vers la même politique que les contours de l'image. `LineImagePanel` conserve le jeu de sélection à l'échelle du témoin et l'ancre en UID entre les folios ; aucune sélection ne modifie les sessions enregistrées. `combined_counterparts` génère la réunion en lecture seule des prévisualisations roses selon la sélection courante. Les contours ALTO/PAGE complets sont le défaut, l'option de repères discrets reste manuelle.

## Export vers Varians et audit (V0.6.15, V0.7.4)

`varians_synchro.varians_export` fabrique les fichiers de synchronisation que lit Varians (page, bbox, polygones, source image, `base_keys` ; contrat vérifié avec Varians 0.9.4.0), sans dépendance Qt ni réseau. Le témoin de base est **technique/physique**, et une TEI ne peut pas être présumée. Les `fingerprints` historiques peuvent être confrontés aux données ALTO conservées pour démontrer une migration PERO `line_UUID` → PAGE `id_UUID`. Les équivalences non prouvées sont exclues. Voir [`EXPORT_VARIANS.md`](EXPORT_VARIANS.md).

- `varians_synchro/validation.py` : diagnostic des ordres de lecture et des paires sans modification du projet ; l'absence est locale à une paire.
- `varians_synchro/varians_export.py` : `verify_export_payloads` valide les clés actives du pivot ; `export_varians_alignments` prépare les deux politiques dans un dossier temporaire avant publication.
- `audit_vsynch.py` : audit hors interface Qt, lecture seule, options `--base`, `--check-paths`, `--strict`.
- Le moteur V0.7.1 reste le seul moteur principal ; les outils géométriques antérieurs sont conservés dans « Autres opérations ».

## TEI

Les sessions physiques ne supposent aucune TEI. Une TEI du pivot peut être liée à ses lignes physiques (`tei_binding.py`), mais l'export n'en a pas besoin : Varians fait correspondre les lignes du pivot, dans l'ordre du fichier de synchronisation, à ses `<lb edRef="#PIVOT"/>`, et prépare lui-même les `<pb/>` et `<lb/>` d'une TEI vide. Aucune fausse TEI n'est fabriquée à partir de la HTR.

## Garde-fous de l'interface et des données reçues

Issus de la red team (voir [`../RED_TEAM.md`](../RED_TEAM.md)) ; chaque règle a son test.

- **Texte reçu affiché tel quel.** `ui_widgets.QLabel` est en texte brut, sauf pour un titre du catalogue (`i18n.is_catalog_text`) ou un balisage écrit par le programme (`rich=True`, texte échappé) ; les boîtes de message sont construites en texte brut (`ui_widgets.message_box`, y compris l'erreur imprévue d'`error_report`) ; une infobulle qui cite une donnée passe par `plain_tip`. Sinon Qt lit comme du HTML un sigle, un texte HTR ou TEI, ou la réponse d'un serveur.
- **Questions et clavier.** Les questions ont « Non » par défaut. `ui_widgets.QDialog` : Entrée n'active pas de bouton par défaut ; F1 ouvre l'aide (section `help_anchor`) ; une fenêtre qui définit `has_unsaved_draft()` (fiche du témoin, périmètre) demande avant d'abandonner un brouillon modifié (Échap, croix, « Annuler »). `fit_to_screen` borne une fenêtre à l'écran ; la fenêtre de synchronisation tient sous 1 280 px dans les sept langues.
- **Fils.** `ui_widgets.start_detached` démarre un fil sans parent, l'annule quand sa fenêtre disparaît et le libère à sa fin ; les fonctions de fin vérifient que la fenêtre existe encore. Le Manifest IIIF de la fiche du témoin est chargé ainsi (`_ManifestFetcher`), avec une attente annulable.
- **Images.** Seuls JPEG, PNG, TIFF, WebP et JPEG 2000 sont décodés comme images de page (`decode_page_image`, `page_image_reader_ok`) : un SVG pouvait charger des fichiers locaux ou réseau. Les miniatures IIIF ne sont demandées qu'en http/https et abandonnées au-delà de 2 Mo.
- **Réseau.** Les téléchargements (`imaging._http_bytes`) refusent une redirection hors http/https, plafonnent la taille et ont une échéance totale (120 s ; 600 s pour une copie HD), lue par blocs.
- **Sigles.** `witness_ids.py` reprend la règle de Varians (`witness_id_for_siglum`) et nomme fichiers et entrées d'archive (« Exporter pour HTR ») ; un sigle ne sert jamais tel quel de nom de fichier.
- **Moteurs.** Enregistrer des propositions se fait en temps linéaire (`physical_alignment._link_context`, calculé une fois par lot) ; la proposition HTR–HTR suit l'ordre de lecture corrigé (`reading_stream`) ; la réimportation HTR est tout ou rien.

## Limites connues

Le logiciel ne réconcilie pas automatiquement une page dont le Canvas IIIF a changé d'identité. Les propositions automatiques sont calculées dans le fil de l'interface, sans progression asynchrone : sur de très grandes HTR, le calcul peut être long. La projection des rectangles ALTO/PAGE sur l'image suppose une image ni recadrée ni tournée par rapport au fichier ALTO/PAGE.
