## Non publié (depuis V0.8.5.6)

- Dépôt GitHub : CI Linux et Windows, empreintes SHA remplacées par l’historique Git.
- Export du projet pour Varians vérifié en l’ouvrant avec le vrai code de Varians 0.9.4.0 ; ordre de lecture corrigé et lignes hors périmètre respectés.
- Projet Varians pré-renseigné sans édition TEI du pivot : plus de refus ; le projet reçoit la TEI vide que Varians crée pour une nouvelle transcription, et les messages indiquent comment y préparer les `<pb/>` et `<lb/>` du pivot dans Varians (« Paramètres du projet »).
- Correspondances périmées après une nouvelle segmentation : avertissement avant de changer le XML d’une page, marque dans la liste, exclusion des calculs, revalidation.
- Retrait d'une ressource enregistrée (dossier d'images, Manifest IIIF, fichier ALTO/PAGE, édition TEI) dans la fiche du témoin, et du témoin lui-même (« Retirer le témoin… ») : le logiciel dit d'abord ce que le retrait entraîne ; les groupes qui touchaient des lignes retirées sont gardés, marqués périmés ; le témoin pivot ne peut pas être retiré ; aucun fichier n'est supprimé du disque.
- Interface : barre de progression du téléchargement HD, fenêtres libérées après fermeture, export HTR hors du fil de l’interface avec annulation, erreurs imprévues affichées, « Annuler » de la liaison TEI sans effet sur le projet, appels différés (vignettes, ordre des pages, visionneuse) abandonnés avec leur fenêtre, fenêtre « Propositions HTR–HTR » : bouton « Enregistrer la sélection » (au lieu de « Conserver la sélection », trompeur sans présélection), boutons « Tout / Rien », sélection vide refusée, espaces rétablies dans les traductions ; étape « 3 · Aligner les témoins » : les paires déjà alignées forment une liste (textes traduits) où un double-clic ou Entrée rouvre la synchronisation d’une paire et un simple clic la choisit dans les deux menus.
- Code : `guided_ui.py` (3 300 lignes) découpé en modules `ui_*`, une fenêtre par module, sans changement du code des classes ; `make_guided_window()` sans paramètre ; les quatre fenêtres de propositions de la synchronisation passent par une fenêtre commune (`ui_proposals.py`), désormais testée, sans changement de comportement.
- Aide : le guide utilisateur, réécrit (présentation, premier essai, parcours « nouveau projet Varians » et « ajouter un témoin à un projet Varians existant », notions, étapes, format des fichiers de synchronisation JSON, dépannage), s'affiche dans une fenêtre du logiciel (bouton ou F1 ; dans la fenêtre de synchronisation, F1 ouvre sa section), avec la recherche de Varians ; sept langues (`help/<langue>.html`), libellés cités vérifiés d'après les catalogues ; l'ancien guide `docs/user/*.md` est retiré.
- Projet d'exemple (`demo_local_ALTO/`) : A y est déjà le témoin pivot ; le « Premier essai » de l'aide le fait constater et dit comment changer de pivot, au lieu de le faire définir.
- Terminologie alignée sur celle de Varians : en japonais ピボット伝本 (pivot) et シグラム (sigle), en allemand « Textzeuge » (interface et guide).
- Messages d'erreur de l'alignement (`physical_alignment.py`) traduits dans les sept langues : « Associez des pages ALTO aux deux témoins avant de synchroniser », notamment, s'affichait en français partout ; la ligne d'erreur de la liste des paires (étape 3) aussi.
- Messages d'erreur et avertissements de tous les moteurs (162 messages : import des ressources, copies HD, ordre de lecture, liaison TEI, révision, exports…) traduits dans les sept langues ; ceux qui citent un sigle ou un fichier gardent ces valeurs. La révision rapide n'écrit plus ses erreurs en anglais.
- Icône : le logo de Varians-Synchro (sur une pastille blanche, lisible sur fond sombre) est l'icône des fenêtres, de la barre des tâches et du Dock ; sous Windows, la fenêtre a sa propre entrée dans la barre des tâches au lieu de celle de Python. `icons/varians_synchro.ico` pour un raccourci ; icônes produites à partir de `logo/` par `tools/generate_icons.py`.
- Projet : un chemin de fichier relatif est lu par rapport au dossier du `.vsynch` ; l'exemple livré (`demo_local_ALTO/`) n'a plus que des chemins relatifs et s'ouvre tel quel (il pointait vers des chemins de l'environnement où il avait été créé). À l'enregistrement, un fichier situé dans le dossier du `.vsynch` ou en dessous est désormais écrit en chemin relatif (il était réécrit en chemin complet) : un projet rangé avec ses fichiers peut être déplacé ou copié ; un fichier ailleurs garde son chemin complet.
- Documentation du dépôt : les 57 anciennes notes de la racine (journaux de version détaillés, recettes, anciens guides) sont retirées ; elles restent dans l'historique Git, recensées avec un lien dans `docs/HISTORIQUE.md`. Les références techniques encore valables (architecture, format `.vsynch`, export vers Varians, internationalisation, portabilité) sont mises à jour dans `docs/developer/`, et le README est réduit à l'essentiel.
- Textes encore affichés en français ou en code brut, désormais traduits : état et type des groupes dans la liste de la synchronisation (« [validé] … · correspondance » au lieu de « [validated] … · correspondence »), propositions HTR–HTR, repères périmés et avertissements de repères du contrôle de cohérence, message du dossier non vide des copies HD (il parlait des JSON de Varians), résumé des témoins, choix des pages et des fichiers XML, barre d'état de la visionneuse, filtres « Projet » et « Images » des boîtes de fichiers. Un test refuse désormais toute phrase en dur dans les fenêtres et tout code d'avertissement sans message.
- Manifest IIIF qui n'a pas répondu à l'ajout du témoin : il est signalé « indisponible » dans la fiche du témoin, et « Réessayer » l'interroge de nouveau (ressaisir son adresse aussi) ; le logiciel dit s'il a répondu et combien de pages il contient. Auparavant, l'adresse déjà connue était ignorée et le Manifest restait indisponible pour de bon.

## V0.8.5.6 — dossier autonome de maintenance et passation (19/10/2026)

- Création de `MAINTENANCE_PASSATION_V0856/` : architecture, flux, inventaire de modules, contrats persistants, moteurs, TEI, IIIF, exports, GUI/i18n, tests, conventions, limites et ADR.
- Ajout de `tools/generate_module_inventory.py` (inventaire AST reproductible), `tools/check_maintenance.py` (intégrité du dossier et des empreintes) et `tests/test_maintenance_0856.py`.
- Mise à jour des points d’entrée documentaires, version applicative `core.VERSION` ; format `.vsynch` 1 et algorithmes inchangés.
- Voir [`CHANGELOG_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0856.md) et [`TESTS_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0856.md).

## V0.8.5.5 — Traductions intégrales des catalogues (18/10/2026)

- 244 messages précédemment en anglais traduits dans chacun des catalogues allemand, tchèque, italien, russe et japonais ; 1 220 entrées au total.
- 653 clés conservées dans chacun des sept catalogues ; paramètres techniques et séquences XML inchangés.
- Documentation sur la validation linguistique native à effectuer ; listes historiques des replis supprimées et couverture mise à jour.
- Moteur d’alignement, fichiers `.vsynch` et exports Varians inchangés.
- Voir [`CHANGELOG_V0855.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0855.md) et [`TESTS_V0855.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0855.md).

# V0.8.5.3 — Copies HD réutilisables et séparation des actions HTR

Voir [`CHANGELOG_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0853.md).

# V0.8.5.2 — Correction du message de fin de téléchargement IIIF HD

Voir [`CHANGELOG_V0852.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0852.md) : fin de téléchargement explicitement distinguée d'une annulation, sans changer le téléchargement lui-même.

# V0.8.5.1 — Interface, IIIF HD et finalisation

Détails : [`CHANGELOG_V0851.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0851.md).

# Version V0.8.5 — consolidation

Voir [CHANGELOG_V085.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V085.md) pour les modifications, garanties et limites de validation.

## V0.8.4.2 — Sélection visuelle et repères

- Clic simple de sélection exclusif sur tout le témoin, y compris les folios non affichés.
- Ctrl+clic / Maj+clic pour ajouts ponctuels / plages de lignes en ordre documentaire.
- Aperçu rose des correspondances recalculé depuis toute la sélection effective, effacé avec les sélections.
- Repères discrets désactivés par défaut ; changement manuel conservé.
- Aucun changement du moteur V0.7.4, de la TEI liée ou du JSON d’export.

## V0.8.4.1 — Aperçu TEI unique (correctif ergonomique)

- Un seul aperçu TEI/manuscrit à la fois dans la fenêtre de liaison ; première ligne sélectionnée par défaut.
- Toute sélection de ligne remplace le même recadrage, y compris « Fin » et les résultats de recherche.
- Aucune requête IIIF automatique pour la dernière ligne avant qu’elle ne soit sélectionnée.
- Confirmation spécifique si les extrémités n’ont pas été affichées pour vérification.
- Modèle des données, algorithmes V0.7.4 et exports Varians inchangés.

## V0.8.4 — Contrôle visuel des liaisons TEI

- Aperçus automatiques du début et de la fin avec texte TEI et image manuscrite surlignée.
- Contrôle intermédiaire facultatif, recherche de lignes TEI et ouverture dans le visualiseur.
- Recherche TEI dans la synchronisation intertémoins, sans modifier les alignements.
- Recadrage local/IIIF régional v2/v3, chargement asynchrone et avertissement si image absente.
- Voir [`CHANGELOG_V084.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V084.md).

## V0.8.1.2 — Urgent : ouverture et création de projets

- Corrige deux affectations `self.project` inaccessibles dans `guided_ui.py`.
- Ouvrir un `.vsynch` chargé avec succès restitue immédiatement les témoins, les pages, les ressources, le pivot et les sessions en mémoire et à l’écran.
- Nouveau projet remplace le document courant uniquement après création enregistrée avec succès.
- Annulation ou fichier invalide : le document courant et son chemin restent inchangés.
- Tests de régression spécifiques qui exécutent les vraies méthodes GUI sans Qt, et tests d’intégration Qt optionnels.
- Aucun changement des formats `.vsynch`, des lignes ALTO/PAGE, des correspondances, du moteur d’alignement ou des exports Varians.

---

# Varians-Synchro V0.7.4 — Recette et stabilisation

- **Export atomique** : `validated/`, `working/` et `rapport_export.json` sont préparés, relus, puis publiés ensemble ; refus des dossiers déjà remplis et nettoyage des sorties temporaires en cas d'échec.
- **Contrat Varians vérifié** : `verify_export_payloads` contrôle les pages, les identifiants physiques, les `base_keys` et leur existence dans le témoin pivot. Les JSON de correspondance eux-mêmes restent inchangés.
- **Contrôle global** en lecture seule (`validation.py`) pour tous les témoins/paires et les absences ; bouton dans « 4 · Progression » et CLI `audit_vsynch.py` sans Qt.
- **Repères croisés isolés** : les intervalles adjacents à une paire de repères contradictoire ne sont plus traités comme sûrs par le moteur cumulatif.
- **Recette sur Mu–F–A** et tests de charge, de réouverture, d'intégrité, de reprise d'anciens projets, de traduction et d'export.
- Catalogues XML FR/EN complétés ; aucun changement des sources ALTO/PAGE, des images ou des sessions existantes.
- Voir [`AUDIT_INTEGRITE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/AUDIT_INTEGRITE_V074.md) et [`RAPPORT_RECETTE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/RAPPORT_RECETTE_V074.md).

---

## V0.7.3 — Exceptions éditoriales et absences confirmées

- Confirmation explicite, propre à chaque paire, d’une absence de correspondance pour une sélection de lignes d’un seul témoin (Ctrl+Maj+A).
- Passage possible entre folios et groupes d’absence distincts pour une sélection disjointe.
- Conversion transactionnelle des seules propositions automatiques incertaines ; les restes demeurent révisables et non validés.
- Protection stricte des décisions humaines/validées, du périmètre ignoré et des références ALTO/PAGE modifiées.
- Suppression explicite des absences depuis la file de révision ; libellés indiquant le témoin où le passage manque.
- Compteurs d’absences par paire et rapport d’export enrichi ; **aucune fausse `base_keys` produite**.
- Nouveaux libellés FR/EN, guide dédié et tests de non-régression.
- Algorithme V0.7.1, ordre des pages, garde de sauvegarde et lancement isolé Spyder inchangés.

## V0.7.2.3 — Contrôle des base_keys avant export Varians

- Audit non destructif des JSON secondaires, en deux variantes : validés et travail.
- Avertissement avant l’export en cas de `base_keys` absents dans un témoin secondaire, ou de propositions non encore validées.
- Diagnostic des principales causes (pas de session directe, liens absents, références périmées, absences seules).
- `rapport_export.json` enrichi de `audit`; ligne de commande et message de succès détaillent les comptes.
- Catalogues français et anglais et documentation actualisés. Moteur d’alignement inchangé.

## V0.7.2.2 — Réorganisation visuelle des pages

- Dans « Pages et ALTO/PAGE » : glisser-déposer, Monter, Descendre, Inverser l’ordre.
- Miniatures des images locales et des Canvas IIIF disposant d’un service d’image,
  chargées à la demande dans la liste (pas de téléchargement massif du Manifest).
- Présentation explicite des deux notions distinctes : ordre de lecture et liaison image ↔ XML.
- Ordre enregistré via les champs `reading_order` : associations, IDs et alignements inchangés.
- Intégration à la sauvegarde sécurisée V0.7.2.1.
- Nouveaux textes traduits en français et en anglais dans les catalogues XML.
- Nouveau module `page_management.py` avec tests de non-régression.

## V0.7.2.1 — Sécurité des sauvegardes
- Avertissement à la fermeture du logiciel si le projet `.vsynch` contient des changements non enregistrés : Enregistrer / Ne pas enregistrer / Annuler (Annuler par défaut).
- Même protection lors de Nouveau projet et Ouvrir projet ; sans dialogue inutile si le projet n’a pas été modifié.
- Comparaison déterministe de l’ensemble du projet en mémoire avec le dernier état sauvegardé, y compris les modifications depuis les panneaux secondaires.
- Sauvegarde annulée ou échouée : la fermeture ou le remplacement du projet est interdit, sans perte des modifications.
- Marque visuelle des modifications non enregistrées ; le changement de langue conserve cet état sans déclencher d’alerte.
- Catalogues FR/EN mis à jour, documentation et tests dédiés.

## V0.7.2 — Révision rapide (J3)
- File des correspondances ordonnée selon le flux de lecture, filtres À vérifier / Validés / Absences / Tous.
- Navigation et contrôle simultané des images ; raccourcis F8, Maj+F8 et Alt+V.
- Validation d’un groupe puis suivant ; validation explicite par lots avec contrôle atomique des empreintes.
- Recalcul local entre le groupe validé sélectionné et le prochain repère compatible.
- Ni changements des identifiants physiques, ni modification du moteur V0.7.1 ni de l’export Varians.
- Traductions françaises et anglaises à jour.

## V0.7.1.1 — isolation du lancement Spyder
- Démarrage séparé avec même Python pour ne pas mélanger les runtimes Qt natifs.
- Journal horodaté de démarrage et `faulthandler` ; lancement explicite alternatif.
- Aucune modification des correspondances, des exports ni des projets.
- Voir [`GUIDE_STABILITE_SPYDER.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_STABILITE_SPYDER.md).

# V0.7.1 — Progression textuelle entre repères (J2)

- Nouveau moteur `textual_progress.py` : flux de lecture multi-folios, estimation HTR **quantitative** (nombre de signes, sans comparaison des mots), puis repli sur géométrie des lignes de base PAGE ou largeur des boîtes, enfin poids uniforme.
- Appariement monotone et déterministe, sans limite sur le ratio de lignes ou sur les groupes automatiques 1↔n/n↔1 ; les groupes n↔m validés servent de repères et restent pris en charge pour la correction manuelle.
- Les groupes manuels, validés et les absences confirmées sont protégés. Les anciennes propositions automatiques incertaines peuvent être remplacées après prévisualisation et accord, de manière atomique. Aucun changement des identifiants ni du format `.vsynch`.
- Interface : nouveau bouton principal « Synchroniser entre repères (texte) », anciennes fonctions géométriques sous « Autres opérations ». Diagnostics des repères contradictoires, lacunes unilatérales et lignes restant après les repères ; traductions FR/EN actualisées.
- Export JSON pour Varians inchangé ; comparaison effectuée sur le projet réel Mu–F : export validé strictement identique après recalcul.
- Tests supplémentaires sur les folios successifs, les repères n↔m, omissions, exclusions, remplacement sûr, différents rapports de ligne et performances. Documentation dans [`GUIDE_PROGRESSION_TEXTUELLE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PROGRESSION_TEXTUELLE.md).

---

# V0.7.0 — Début de la refonte (J1)

- Nouveau module `reading_stream.py` : flux continu de lignes ALTO/PAGE, folios et colonnes successifs, lignes ignorées exclues du calcul.
- Intervalles multi-folios entre repères validés 1↔1, 1↔n, n↔m ; diagnostics de repères périmés, discontinus ou inversés.
- Correction manuelle réversible de l’ordre des pages, régions et lignes dans le projet, sans changement des identifiants physiques.
- Identifiants de `TextBlock` ALTO et de `TextRegion` PAGE capturés à l’import, lignes de base PAGE conservées.
- Nouvel inspecteur accessible dans les autres opérations de l’alignement visuel ; traductions FR/EN.
- Commande autonome `diagnostic_flux_lecture.py` (lecture seule).
- Préservation des préférences d’ordre même après actualisation de l’inventaire d’images.
- Ancien moteur conservé provisoirement ; export Varians inchangé et vérifié sur Mu–F.

## V0.6.16
- Exclusion réelle des lignes ignorées de l’export JSON Varians, sans renumérotation des lignes physiques.
- Identifiant IIIF Canvas conservé dans les métadonnées d’image de chaque page.
- Tests de comptage des lignes TEI attendues et de conservation de `base_keys`.

# V0.6.14 — Propositions pour lignes résiduelles et interface ALTO/PAGE

- Nouveau second passage conservateur `residual_alignment.py` : détecte des lignes encore non alignées pouvant rejoindre des **groupes automatiques non validés** existants, d'après la géométrie et le voisinage.
- Prévisualisation avec choix des propositions, confirmation explicite, contrôle des conflits et écriture atomique. Aucun changement des liens validés, manuels ou corrigés manuellement.
- Détection des situations risquées : lignes libres des deux côtés, voisin ambigu, groupes protégés, données manquantes, sources modifiées.
- Conservation des identifiants des groupes ; provenance des extensions ajoutée aux `evidence`.
- Nouveau bouton secondaire **« Compléter les lignes restantes… »** dans la zone de filtres visuels et commande équivalente dans « Autres opérations ».
- Renommage de la case **« Cadres ALTO »** en **« Cadres lignes »** / **« Line outlines »**, dans les catalogues XML français et anglais.
- Tests de sécurité supplémentaires sur la compatibilité, les filtres d'exclusion, l'intégrité des liens et les cas ambigus.

---

# V0.6.13 — Entrée native PAGE-XML (parallèlement à ALTO)

- Nouvelle importation PAGE-XML (`PcGts`) : `Page`, `TextRegion`, `TextLine/Coords`, `TextEquiv/Unicode`, ordre des régions lorsque disponible.
- Détection automatique ALTO/PAGE au chargement, indépendamment du nom du fichier.
- Modèle interne de lignes compatible avec la synchronisation visuelle, HTR–HTR et l'interpolation géométrique ; contours PAGE polygonaux exacts.
- Association aux images locales ou IIIF, propositions grâce à `Page@imageFilename`, et réimportation des sorties HTR au format PAGE.
- Mêmes sauvegarde `.vsynch` et identifiants que les versions ALTO, champ historique `alto_sources` conservé pour les anciens projets.
- Interface et traductions XML mises à jour en français/anglais ; prise en charge multiplateforme préservée.
- Nouveaux tests de compatibilité PAGE/ALTO et documentation [`GUIDE_PAGE_XML.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PAGE_XML.md).

---

## V0.6.12 — Polygones ALTO et sélection sur les contours

- Chargement du contour `<TextLine><Shape><Polygon POINTS="…"/></Shape></TextLine>` à l'importation des ALTO (namespace 3/4 accepté).
- Lecture non destructive à la demande des polygones dans les ALTO d'origine pour les projets déjà importés (contrôle des identifiants et rectangles avant application).
- Dessin des polygones inclinés au lieu des rectangles englobants lorsque disponibles ; repli sur les rectangles en leur absence.
- Sélection directement sur les zones polygonales, sans confusion avec les rectangles englobants qui se chevauchent.
- Mode compact basculé automatiquement selon la disponibilité des polygones, sauf si l'utilisateur a modifié ce choix explicitement.
- Diagnostic de la présence de polygones visible dans le panneau ; traduction FR/EN ajoutée aux catalogues XML.
- Aucun changement aux identifiants persistants de ligne, associations ou fichiers source.
- Tests de régression sur les polygones inclinés et anciens projets.

# Historique des versions

## V0.6.11 — 10 octobre 2026

- Ajout du périmètre documentaire des lignes ALTO à l'échelle de chaque témoin (`ignored_line_ids`).
- Commandes de marquage **Ignorer** et **Réintégrer** dans le visualiseur, disponibles pour des sélections multiples sur les deux témoins.
- Confirmation préalable si des groupes déjà synchronisés doivent être ajustés, puis modification atomique de toutes les paires concernées.
- Interdiction d'associer une ligne encore marquée ignorée.
- Exclusion des lignes ignorées du moteur d'interpolation géométrique (y compris ses calculs de géométrie), du HTR–HTR et des statistiques de progression.
- Palette d'overlay plus contrastée : violet pour les lignes non synchronisées, gris pointillé pour les lignes ignorées, vert manuel, bleu automatique, orange actif, rose inspection.
- Libellés FR/EN ajoutés aux catalogues XML.
- Tests de non-régression pour l'atomicité des changements, les groupes n:m, l'ouverture des anciens projets, les statistiques, les moteurs HTR et géométriques, les traductions et les styles.

# Historique des modifications

## V0.6.10 — Extension et dissociation partielle des groupes

- Correction du bouton **Dissocier** : action accessible dans la barre supérieure et compatible avec les lignes sélectionnées sur les images et dans la vue textuelle.
- Ajout de la dissociation **partielle** : seuls les membres sélectionnés sont retirés ; le groupe est conservé lorsqu'il reste des lignes des deux côtés.
- Séparation explicite de la **suppression d'un groupe entier**, effectuée depuis la liste des groupes et soumise à confirmation.
- **Associer les lignes** étend automatiquement un groupe existant si une seule des lignes sélectionnées appartient déjà à une correspondance, sans obligation de dissocier au préalable.
- Refus atomique des tentatives d'assembler plusieurs groupes distincts ou de contredire une absence déjà confirmée.
- Les corrections sont enregistrées sous `evidence.manual_corrections` et la validation antérieure est respectée.
- Internationalisation des nouvelles commandes et erreurs dans les XML FR/EN.
- Le calcul automatique géométrique de V0.6.9 n'a pas été modifié : ses résidus peuvent être traités avec les nouvelles corrections manuelles.

## V0.6.9

Voir [`GUIDE_INTERPOLATION_COLONNES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_INTERPOLATION_COLONNES.md) pour le recalcul automatique de colonnes et la protection des corrections manuelles.
