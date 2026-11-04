## Dossier de maintenance et de passation — V0.8.5.6 (19/10/2026)

La reprise du projet par un développeur humain commence dans **[MAINTENANCE_PASSATION_V0856/00_LIRE_EN_PREMIER.md](MAINTENANCE_PASSATION_V0856/00_LIRE_EN_PREMIER.md)** : architecture, modèles de données, décisions techniques, conventions, tests, procédures d’exploitation et risques connus. Ce dossier est autonome et distinct des guides utilisateur. Les fonctionnalités scientifiques restent celles de v0.8.5.5. Voir [CHANGELOG_V0856.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0856.md) et [TESTS_V0856.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0856.md).

# Varians-Synchro V0.8.5.5 — localisation complète des catalogues

**Nouveauté v0.8.5.5 :** les 244 replis anglais identifiés dans chacune des cinq langues supplémentaires (de, cs, it, ru, ja) ont été remplacés par des traductions, soit **1 220 entrées**. Les sept catalogues disposent des mêmes 653 clés et des mêmes paramètres de substitution. Les valeurs techniques et les textes des manuscrits ne sont jamais traduits. Les traductions restent à faire relire par des spécialistes natifs : voir `docs/I18N_NATIVE_REVIEW_V0855.md`. Aucune modification du moteur de synchronisation, du format `.vsynch` ou des exports JSON n'est prévue dans cette version.

**Vérifications :** `python -m pytest -q` (sans PySide6, tests Qt ignorés), `python -m compileall -q varians_synchro`, contrôle exhaustif des catalogues ; rapport dans [`TESTS_V0855.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0855.md).


# Varians-Synchro V0.8.5.3 — Copies HD IIIF réutilisables

**Après téléchargement ou rattachement d’un lot HD, enregistrer le projet `.vsynch`.** La création d’un dossier Varians inclut les copies locales **seulement si tous les Canvas liés à une segmentation ALTO/PAGE disposent d’une copie intègre**. Voir [`GUIDE_COPIES_HD_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_COPIES_HD_V0853.md), [`CHANGELOG_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0853.md) et [`TESTS_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0853.md). Le parcours HTR externe est désormais expliqué dans la fenêtre de gestion des images.

# Varians-Synchro V0.8.5.2 — Correctif de notification IIIF HD

**Cette version corrige le faux message « Téléchargement annulé » affiché après un téléchargement HD réussi.** La progression à 100 % et la fermeture de sa fenêtre ne sont plus traitées comme une annulation. Voir [`CHANGELOG_V0852.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0852.md) et [`TESTS_V0852.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0852.md).

Aucune modification du moteur d’alignement V0.7.4, du format `.vsynch` ni des exports vers Varians. La V0.8.5.2 reprend l’intégralité des fonctions V0.8.5.1.

# Varians-Synchro V0.8.5.1 — Ergonomie et finalisation

Voir [`GUIDE_FINALISATION_V0851.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_FINALISATION_V0851.md) pour les quatre nouvelles étapes, le téléchargement HD d’images IIIF sélectionnées, l’audit lisible et l’export de projet Varians pré-renseigné. **Compatibilité à tester avec votre version installée de Varians.**

# Varians-Synchro V0.8.5 — Consolidation de la branche V0.8

**Version candidate stable** (validation GUI Windows et import dans le Varians le plus récent encore à réaliser). Cette version reprend la V0.8.4.2, **sans modification du moteur V0.7.4 ni de la projection JSON**.

- Sauvegardes atomiques avec copie récupérable `.vsynch.bak` au réenregistrement.
- Recette hors Qt : `python recette_v085.py mon_projet.vsynch --base Mu --output rapport.json`.
- Tests : **294 réussis, 11 Qt non exécutés** dans l'environnement de construction.
- Traductions FR/EN contrôlées ; retrait de l'API obsolète de nouveaux imports TXT/MD. Les anciens projets restent lisibles.
- Voir [CHANGELOG_V085.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V085.md), [RAPPORT_RECETTE_V085.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/RAPPORT_RECETTE_V085.md), [GUIDE_SAUVEGARDE_V085.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_SAUVEGARDE_V085.md) et [PASSATION_DEV_V085.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/PASSATION_DEV_V085.md).

---

# Varians-Synchro V0.8.4.2 — Sélection des lignes et repères visuels

**Correctif V0.8.4.2 :** « Repères discrets » décoché par défaut ; clic simple pour remplacer toute la sélection du témoin, Ctrl+clic pour ajouter/retirer une ligne, Maj+clic pour sélectionner une plage (y compris entre folios). Les correspondances prévisualisées dans l'autre témoin suivent exactement la sélection courante. Voir [CHANGELOG_V0842.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0842.md) et [TESTS_V0842.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0842.md).

Le moteur d'alignement V0.7.4 et le format d'export JSON vers Varians sont inchangés.

---

# Varians-Synchro V0.8.4.1 — Aperçu TEI unique

**Dernière version : V0.8.4.1.** La fenêtre « Liaison TEI ↔ lignes physiques » montre **un seul recadrage à la fois** : celui de la première ligne à l’ouverture, puis celui de la ligne sélectionnée. Les boutons « Début » / « Fin » et la recherche TEI sont conservés. Aucune modification du moteur d’alignement ni du format `.vsynch`.

Voir [CHANGELOG_V0841.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0841.md) et [GUIDE_CONTROLE_VISUEL_TEI_V084.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CONTROLE_VISUEL_TEI_V084.md).

---

# Varians-Synchro V0.8.4 — Contrôle visuel TEI et recherche

**Dernière version : V0.8.4.** Affichage automatique des images et textes TEI des **deux extrémités** avant validation, contrôle facultatif d’une ligne intermédiaire et recherche dans la TEI liée depuis la synchronisation visuelle. Le moteur V0.7.4 demeure inchangé.

Lire [GUIDE_CONTROLE_VISUEL_TEI_V084.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CONTROLE_VISUEL_TEI_V084.md), [CHANGELOG_V084.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V084.md) et [TESTS_V084.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V084.md).

---

# Varians-Synchro V0.8.3 — Intégration TEI (V0.8.2 + V0.8.3)

**Dernière version : V0.8.3.** Voir [`GUIDE_LIAISON_TEI_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_LIAISON_TEI_V083.md) et [`CHANGELOG_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V083.md) pour les nouveautés, les limites et la procédure de rattachement TEI.

# Varians-Synchro V0.8.1.2 — Correctif urgent de l’ouverture des projets

**Cette version corrige une erreur d’indentation dans `GuidedWindow.open` et `GuidedWindow.new`.** Dans la V0.8.1/0.8.1.1, le chemin du `.vsynch` changeait sans remplacer les données du projet affiché. Une sauvegarde pouvait alors écraser un fichier existant avec le contenu d’un autre projet.

Les deux parcours réaffectent maintenant `self.project` uniquement après un chargement ou une création réussis et une confirmation de sauvegarde le cas échéant. Le suivi des modifications est réinitialisé sur le bon document. Les données et l’algorithme de synchronisation, les associations IIIF/ALTO-PAGE et les exports JSON sont inchangés.

**Précaution :** faites une copie de vos `.vsynch` existants avant la reprise et n’enregistrez pas depuis une fenêtre restée vide après un chargement dans les versions antérieures. Voir [CORRECTIF_OUVERTURE_PROJET_V0812.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_OUVERTURE_PROJET_V0812.md).

---

# Varians-Synchro V0.8.1.1 — Correctif des associations ALTO/PAGE en double

**Lire [CORRECTIF_DOUBLONS_IIIF_V0811.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_DOUBLONS_IIIF_V0811.md).** Correction ciblée de la fenêtre d'association d'un sous-ensemble de Canvas IIIF avec des XML ; moteur d'alignement et export Varians inchangés.

---

# Varians-Synchro V0.8.1 — Ressources par témoin et associations groupées

Cette livraison réunit **V0.8.0 et V0.8.1** sur la base stable du moteur de synchronisation V0.7.4. Elle améliore **la préparation des témoins** et ne change pas le calcul entre repères ni le format des JSON destinés à Varians.

**Commencer par [GUIDE_RESSOURCES_V081.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_RESSOURCES_V081.md).**

## Démarrer

- Installer `PySide6` dans l'environnement Python utilisé, puis lancer `python run.py` ; sous Spyder, le démarrage reste isolé dans un processus séparé.
- L'application a pour icône le logo de Varians-Synchro (fenêtres, barre des tâches, Dock). Pour un raccourci Windows vers `start_windows.bat` : Propriétés → Changer d'icône → `icons/varians_synchro.ico`.
- Créer le projet, choisir tout de suite son fichier `.vsynch`, puis ouvrir **Projet et témoins → Ajouter un témoin…**.
- Renseigner le sigle, les images et les fichiers ALTO/PAGE, éventuellement un Manifest IIIF ou une édition TEI.
- Utiliser **Associer automatiquement les images et les ALTO/PAGE** dans la fiche du témoin ou l'étape Pages, contrôler les propositions, puis les appliquer.
- Vérifier les images et les contours, synchroniser comme en V0.7.4, puis exporter `validated/` ou `working/` pour Varians.

**Limite annoncée :** une TEI ajoutée dans la fiche n'est qu'une ressource référencée. Le comptage et le rattachement des `<lb edRef>` à la segmentation physique sont prévus pour V0.8.2–V0.8.3 ; aucune liaison n'est inventée à ce stade.

## Documentation principale

- [CHANGELOG_V081.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V081.md) : changements du lot V0.8.0–V0.8.1.
- [FEUILLE_DE_ROUTE_V08.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/FEUILLE_DE_ROUTE_V08.md) : étapes restant à développer.
- [GUIDE_RESSOURCES_V081.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_RESSOURCES_V081.md) : procédure d'utilisation et garanties.
- [TESTS_V081.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V081.md) : couverture automatique et essais graphiques à réaliser.
- [GUIDE_PROGRESSION_TEXTUELLE.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PROGRESSION_TEXTUELLE.md) : moteur de synchronisation conservé.
- [EXPORT_VARIANS.md](docs/developer/EXPORT_VARIANS.md) : export JSON et choix de statut.
- [GUIDE_STABILITE_SPYDER.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_STABILITE_SPYDER.md) : démarrage isolé.

Les anciens documents techniques et historiques restent fournis pour faciliter la maintenance. Leur contenu peut mentionner d'anciens boutons supprimés dans la V0.8.1.

---

# Varians-Synchro V0.7.4

**Branche de stabilisation de la refonte V0.7** : le moteur de progression textuelle et le parcours visuel sont conservés. Un contrôle global en lecture seule et un export transactionnel sécurisent le transfert des JSON vers Varians. Pour lancer : `python run.py` (PySide6 requis). Pour auditer sans Qt : `python audit_vsynch.py projet.vsynch --base Mu`.

Commencer par [`AUDIT_INTEGRITE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/AUDIT_INTEGRITE_V074.md) et [`RAPPORT_RECETTE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/RAPPORT_RECETTE_V074.md). La recette automatisée passe ; les essais graphiques Qt et IIIF à distance restent à confirmer sur un poste utilisateur.

---

# Varians-Synchro V0.7.3 — Exceptions éditoriales

Sélectionner une ou plusieurs lignes **dans un seul témoin** puis choisir **Autres opérations → Confirmer l’absence des lignes sélectionnées** (`Ctrl+Maj+A`). Les propositions automatiques incertaines peuvent être ajustées après confirmation ; aucune association manuelle ou validée n’est écrasée. Le filtre **Absences** permet de revoir et retirer une décision explicite. Les JSON de Varians conservent toutes les correspondances existantes, et les absences restent dans `.vsynch` et les diagnostics d’export.

Lire [GUIDE_EXCEPTIONS_EDITORIALES.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_EXCEPTIONS_EDITORIALES.md).

## V0.7.2.3 : contrôle de l’export JSON pour Varians

L’export signale désormais les témoins secondaires sans `base_keys` et distingue le nombre de lignes reliées dans `validated/` et `working/`. Voir [`DIAGNOSTIC_BASE_KEYS.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/DIAGNOSTIC_BASE_KEYS.md).

## Nouveauté V0.7.2.2 : remettre les pages dans l’ordre

Dans **2 · Pages et ALTO/PAGE**, ouvre la gestion des pages pour voir les
miniatures et réorganiser les folios par glisser-déposer, **Monter/Descendre**
ou **Inverser l’ordre**. Le déplacement n’altère jamais l’association
image–ALTO/PAGE ni les synchronisations existantes. **Enregistre ensuite le
`.vsynch`.** Détails : [GUIDE_ORDRE_VISUEL_PAGES.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_ORDRE_VISUEL_PAGES.md).

# Varians-Synchro V0.7.2.1 — Révision rapide des correspondances

Nouveau parcours de révision ordonné : F8, Maj+F8, Alt+V, validation explicite des sélections et recalcul local entre deux repères. Moteur de progression V0.7.1 et lancement Spyder isolé V0.7.1.1 conservés.

Lire [`GUIDE_REVISION_RAPIDE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_REVISION_RAPIDE.md).

---

# Varians-Synchro V0.7.1.1 — lancement indépendant sous Spyder

La V0.7.1.1 reprend le moteur de progression textuelle de la V0.7.1 sans modification de l’alignement. **Le lancement de `run.py` depuis Spyder utilise maintenant un processus Python indépendant**, afin d’éviter des conflits de Qt avec le noyau Spyder. Journaux de démarrage activés. Lire [GUIDE_STABILITE_SPYDER.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_STABILITE_SPYDER.md).

# Varians-Synchro V0.7.1 — synchronisation par quantité de texte entre repères

**Nouveau moteur par défaut** : synchronisation des deux flux de lignes entre repères validés, y compris au-delà des changements de colonne et de folio. HTR utilisée comme quantité de signes, repli sur la longueur graphique et les poids uniformes. Propositions incertaines, repères et choix manuels protégés. Le bouton principal est désormais « Synchroniser entre repères (texte) ». Les outils géométriques précédents restent sous « Autres opérations » pour comparaison.

**Lire en priorité [`GUIDE_PROGRESSION_TEXTUELLE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PROGRESSION_TEXTUELLE.md).** Les anciens projets et les exports Varians demeurent compatibles.

# Varians-Synchro V0.7.0 — flux continu entre repères (premier jalon)

**Lire d’abord [REFONTE_V0.7.0.md](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/REFONTE_V0.7.0.md).** Cette version introduit la reconstruction et la correction de l’ordre de lecture, ainsi qu’un diagnostic d’intervalles entre repères validés, sans encore remplacer l’ancien moteur de synchronisation (remplacement prévu en V0.7.1).

# Varians-Synchro V0.6.16 — correctif export Varians

Voir [`CORRECTIF_EXPORT_VARIANS.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_EXPORT_VARIANS.md) pour les conditions d’export des lignes ignorées et les précautions relatives à la TEI incomplète.

# Varians-Synchro V0.6.15 — export JSON pour Varians 0.8.5.2

Consultez `EXPORT_VARIANS.md` et [`CHANGELOG_V0.6.15.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0.6.15.md). Un bouton d’exportation est disponible dans l’étape 3 ; il produit un JSON par témoin. L’export est fondé sur les lignes physiques et ne constitue pas à lui seul une correspondance établie avec les `<lb/>` d’une TEI.

# Varians-Synchro V0.6.14 — Complément des lignes résiduelles et libellés ALTO/PAGE

Cette version est une évolution de la V0.6.13. Elle **conserve** l'importation mixte ALTO/PAGE-XML, les polygones PAGE, les filtres, les exclusions de périmètre et les projets `.vsynch` existants.

## Correction visible

Dans **Synchronisation visuelle**, la case à cocher « Cadres ALTO » est maintenant **« Cadres lignes »** (anglais : **« Line outlines »**). Les traductions sont enregistrées dans `i18n/fr.xml` et `i18n/en.xml`, sous la même clé stable `viewer.alto.toggle`.

## Second passage : lignes restantes

Après avoir utilisé **« Compléter entre ancrages (géométrie) »** puis enregistré les propositions, utiliser **« Compléter les lignes restantes… »**, soit à côté du filtre « Cadres visibles », soit dans **Autres opérations**.

Ce second passage recherche les lignes encore libres situées à proximité d'un groupe de correspondance déjà créé. Il peut proposer d'**étendre un groupe automatique incertain** lorsqu'aucune ligne libre plausible ne subsiste au voisinage approprié dans l'autre témoin. L'HTR n'est pas indispensable.

1. Ouvrir la prévisualisation : le calcul ne modifie rien.
2. Examiner les lignes à ajouter et leurs groupes destinataires. Toutes les suggestions demeurent **incertaines**.
3. Désélectionner les propositions douteuses.
4. Confirmer explicitement l'enregistrement. Les liens modifiés gardent leurs identifiants et conservent une trace des extensions dans `evidence.residual_extensions`.
5. Vérifier sur les images, puis valider manuellement les groupes corrects. Enregistrer le projet `.vsynch`.

### Garanties et limites

- **Jamais de modification automatique** d'un groupe manuel, corrigé manuellement ou validé. Si une ligne doit rejoindre un tel groupe, cliquer sur les lignes dans les deux témoins puis utiliser « Associer les lignes ».
- Les lignes **ignorées** sont exclues ; aucun lien d'absence n'est inféré.
- Les candidats dont l'ordre des lignes, le folio ou la colonne ne permet pas une hypothèse prudente sont laissés de côté, avec compteur de diagnostic.
- Les suggestions ajoutées sont toujours `uncertain` et d'origine `interpolated-residual` ; elles ne constituent pas une preuve de concordance textuelle.
- Une prévisualisation périmée, une segmentation changée, des lignes déjà associées ou des propositions contradictoires bloquent **l'opération entière**, sans modification partielle.
- Cette méthode conserve une borne de proximité géométrique et un nombre limité de lignes ajoutées par groupe : elle ne résout pas encore toutes les lacunes et transpositions.

## Démarrage

- Windows : `python run.py` (ou `start_windows.bat`, facultatif).
- macOS / Linux : `python3 run.py` (ou `start_unix.sh`).
- Dépendance graphique : PySide6 (voir `requirements.txt`). Le logiciel ne dépend ni de Spyder ni d'un système particulier.
- Pour les tests (depuis le dossier contenant `run.py`) : `python -m pytest -q` ou `PYTHONPATH=. pytest -q` selon le mode d'installation.

Lire aussi [`GUIDE_LIGNES_RESIDUELLES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_LIGNES_RESIDUELLES.md), [`GUIDE_PAGE_XML.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PAGE_XML.md), `INTERNATIONALISATION.md`, `FORMAT_PROJET.md` et le reste de la documentation livrée dans l'archive.

# Historique : V0.6.13 — Importation native ALTO et PAGE-XML

**ALTO et PAGE-XML sont désormais deux formats d'entrée de même niveau.** On peut importer un fichier PAGE-XML directement, avec ses contours de lignes (`TextLine/Coords`), son texte HTR (`TextEquiv/Unicode`) lorsqu'il existe et son ordre de lecture par régions. Aucune conversion en ALTO ni fichier TEI/TXT n'est obligatoire.

- Dans **1 · Projet et témoins**, utiliser **Importer ALTO ou PAGE** ; le format XML est détecté automatiquement.
- Dans **2 · Pages et ALTO**, associer le fichier à une image locale ou à un Canvas IIIF ; les suggestions tiennent compte de `Page@imageFilename` pour PAGE.
- Dans **3 · Synchronisation**, aligner les lignes PAGE exactement comme celles d'ALTO : sélections, groupes n↔m, ancrages, interpolation, lignes ignorées, surlignage et conservation des statuts.
- Sur une page PAGE-XML, les vrais contours `Coords` sont dessinés comme **polygones** : le visualiseur n'est pas obligé de se rabattre sur les rectangles ALTO.
- **Projets V0.6.12 et antérieurs compatibles** : les champs `alto_sources` et `alto_binding` sont conservés dans `.vsynch` pour ne pas déplacer les identifiants et les associations déjà enregistrés.
- Fichiers français/anglais dans `i18n/fr.xml` et `i18n/en.xml` ; Windows, macOS et Linux sont des cibles, sans dépendances système propres à Windows.

**Guide étape par étape :** [`GUIDE_PAGE_XML.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PAGE_XML.md). À noter : une page image reçoit **une source de lignes active à la fois**, ALTO ou PAGE ; si les deux sont importées, on choisit laquelle associer à la page. Le logiciel ne fusionne pas automatiquement les deux jeux de segmentation, car les identifiants et découpages peuvent différer. La substitution d'une source sur une page déjà alignée nécessite une vérification des correspondances existantes.

**Validation technique :** tests automatiques sur PAGE avec HTR, polygones inclinés, import croisé PAGE–ALTO et sauvegarde `.vsynch`. Les tests graphiques PySide6 nécessitent encore un essai sur une machine équipée de Qt.

---

# Varians-Synchro V0.6.12 — Contours réels des lignes ALTO

Cette version corrige les cadres trop grands ou superposés sur certains manuscrits, en particulier avec des lignes inclinées provenant de PERO OCR. Un rectangle `TextLine` ALTO est une **enveloppe horizontale**, parfois nettement plus large/haute que le contour de l'écriture. Lorsque le fichier ALTO contient `<Shape><Polygon POINTS="…"/></Shape>`, Varians-Synchro affiche et utilise **ce polygone**, comme le fait PERO, plutôt que l'enveloppe.

- **Affichage fidèle :** contours polygonaux inclinés quand ils sont disponibles ; repli sur les rectangles si l'ALTO ne contient pas de polygone.
- **Sélection précise :** clic à l'intérieur d'un polygone plutôt que dans un rectangle englobant qui chevauche une ligne voisine.
- **Projets V0.6.x compatibles :** si les anciens projets n'ont pas enregistré les polygones, lecture à la demande de l'ALTO original sans modifier le projet ou ses identifiants de ligne.
- **État de la page :** la barre de statut indique le nombre de contours polygonaux effectivement disponibles. Sans polygones, des repères compacts restent proposés.
- **« Marqueurs compacts »** reste un choix manuel, utile si les polygones sont absents ou pour alléger l'affichage.
- **Données préservées :** aucun changement aux ALTO, aux images ou aux associations existantes. Le moteur d'alignement géométrique continue de fonctionner avec les coordonnées sources inchangées.

**Pour tester :** ouvre directement ton `.vsynch` existant ; sélectionne le folio qui chevauchait les cadres ; vérifie que le statut annonce des polygones ALTO et que le contour épouse la pente du texte. En l'absence de polygones, le mode compact s'active par défaut. Un exemple de l'ALTO concerné sera alors nécessaire pour examiner les données exportées par PERO.

**Vérification :** tests du noyau et tests de parsing des polygones exécutés. Tests Qt ajoutés mais dépendants de l'installation de PySide6.

---

# Varians-Synchro V0.6.11 — Périmètre documentaire et palette contrastée

Ce correctif conserve les fonctions de **V0.6.10** (corrections manuelles des groupes, interpolation de colonnes, visualiseur IIIF/local, navigation réciproque, filtres, i18n XML FR/EN et lancement multiplateforme) et ajoute :

- **Périmètre ▾ → Ignorer / Réintégrer** les lignes ALTO sélectionnées sur les images, **au niveau du témoin**, pas d'une paire particulière ; marquage persistant et réversible dans `.vsynch`.
- **Protection des associations** : confirmation explicite si des groupes sont touchés, dissociation partielle si possible, sans créer de fausses lacunes ; aucune modification avant confirmation.
- **Alignement géométrique et HTR–HTR** excluant les lignes ignorées ; statistiques distinguant les lignes ignorées des lignes restant réellement à synchroniser.
- **Palette révisée** : violet contrasté pour les lignes non synchronisées, vert pour le manuel, bleu pour l'automatique, gris pointillé pour les lignes ignorées, orange pour la sélection et rose pour une correspondance consultée.
- **Traductions XML** dans `i18n/fr.xml` et `i18n/en.xml`, sans changement des sources ALTO/IIIF.

**Guide d'utilisation et précautions :** [`GUIDE_PERIMETRE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PERIMETRE.md). Les fonctions de la version précédente sont détaillées dans [`GUIDE_CORRECTIONS_MANUELLES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CORRECTIONS_MANUELLES.md) et [`GUIDE_INTERPOLATION_COLONNES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_INTERPOLATION_COLONNES.md).

## Essai conseillé

Extraire le ZIP dans un **nouveau dossier**, relancer `run.py`, et ouvrir de préférence une **copie de sauvegarde** du projet `.vsynch` courant. Dans la synchronisation visuelle, sélectionner au Ctrl/Maj les lignes étrangères au texte étudié, ouvrir **Périmètre**, les ignorer puis vérifier leur couleur grise et les statistiques. Relancer ensuite « Compléter entre ancrages » et contrôler que ces lignes ne sont pas proposées. Réintégrer une ligne pour tester le retour arrière ; enregistrer et rouvrir le projet.

**Limites :** les trois tests Qt graphiques préexistants et le nouveau test facultatif Qt ne s'exécutent pas dans notre environnement sans PySide6. Les traitements du noyau sont vérifiés automatiquement, mais le comportement graphique reste à confirmer sur le poste utilisateur. Les anciens alignements TEI dont une ligne serait concernée restent protégés : leur dissociation doit être réalisée dans l'outil TEI avant de pouvoir ignorer cette ligne.

# Varians-Synchro V0.6.10 — Correction manuelle des groupes de lignes

Cette mise à jour conserve toutes les fonctions de V0.6.9 : alignement sans TEI, images locales ou IIIF, visualiseur zoomable, surlignage réciproque, filtres d'overlay, interpolation géométrique avec ancrages, catalogues XML français/anglais et compatibilité Windows/macOS/Linux.

## Modifications principales

- **Associer les lignes** peut désormais **étendre une association existante**, par exemple de 1↔1 à 1↔2, en sélectionnant la ligne déjà associée d'un côté et la ligne oubliée de l'autre.
- **Dissocier**, désormais accessible dans la barre supérieure du visualiseur, agit sur les **lignes sélectionnées sur les images**. Une dissociation partielle conserve les autres membres du groupe ; elle n'efface pas le groupe entier par surprise.
- L'effacement de **groupes complets** est une opération distincte du menu **Autres opérations**, avec confirmation.
- Les corrections manuelles sont tracées dans les métadonnées et **protégées contre le recalcul automatique**. L'état « incertain » d'un lien automatique n'est jamais validé implicitement.
- Messages et commandes nouvellement introduits dans `i18n/fr.xml` et `i18n/en.xml`.

**Mode d'emploi détaillé :** [`GUIDE_CORRECTIONS_MANUELLES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CORRECTIONS_MANUELLES.md).

## Installation et test

Extraire l'archive dans un répertoire neuf. Depuis ce répertoire, lancer `python run.py` (ou `run.py` dans Spyder avec le bon répertoire de travail). Sous macOS/Linux, le script `start_unix.sh` est également fourni. Prérequis : Python et PySide6, voir `requirements.txt`.

Ouvrir une **copie** d'un projet `.vsynch` V0.6.9, puis « 3 · Synchronisation → Ouvrir l'alignement des lignes ALTO ». Pour corriger une ligne oubliée, cliquer sur une ligne déjà liée du manuscrit A et sur la ligne oubliée du manuscrit B, puis choisir **Associer les lignes**. Pour retirer uniquement une ligne, cliquer sur celle-ci, puis sur **Dissocier**.

Les exemples sont fondés sur des lignes ALTO physiques ; il n'est pas nécessaire d'importer une TEI, un TXT ou une HTR. Les transcriptions sources et images ne sont jamais modifiées.

## Tests et limites

Le noyau est vérifié automatiquement ; les interactions graphiques Qt restent à valider sur une machine équipée de PySide6. Le moteur géométrique peut encore laisser quelques intervalles non alignés si l'information spatiale ne permet pas de choisir une correspondance fiable. Ces lacunes peuvent maintenant être corrigées facilement en étendant manuellement le groupe voisin, sans forcer des équivalences arbitraires.

Pour la documentation technique, consulter `ARCHITECTURE.md`, `INTERNATIONALISATION.md`, `PORTABILITE.md`, et `FORMAT_PROJET.md`.


### Protection contre la perte des modifications (V0.7.2.1)

Lorsque le projet a changé depuis sa dernière sauvegarde, la fermeture de
Varians-Synchro, l'ouverture d'un autre projet et la création d'un nouveau
projet demandent : **Enregistrer / Ne pas enregistrer / Annuler**.
Une sauvegarde annulée ou échouée empêche la fermeture. Les modifications
effectuées dans les panneaux secondaires sont suivies automatiquement.
Le changement de langue n'est pas une fermeture de projet et conserve l'état
de sauvegarde. Les libellés sont traduits en français et anglais.
