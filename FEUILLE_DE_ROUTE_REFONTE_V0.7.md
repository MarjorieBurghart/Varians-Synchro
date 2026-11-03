> **État au jalon V0.7.4 :** J1–J4 mis en œuvre dans la branche V0.7 ; J5 (contrats JSON, contrôle `base_keys`, publication transactionnelle) vérifié automatiquement. J6 (recette utilisateur chronométrée, essais Qt Windows/macOS/Linux et IIIF en conditions réelles) reste à valider. L’ancien moteur géométrique est conservé comme outil secondaire, pas comme moteur principal.

# Avancement : J1 (V0.7.0) et J2 (V0.7.1) implémentés

Voir `GUIDE_PROGRESSION_TEXTUELLE.md` pour les critères et limites du second jalon. L’ergonomie de révision (V0.7.2) et les exceptions de correspondance (V0.7.3) sont intégrées. La campagne de recette sur corpus et la stabilisation finale (V0.7.4) restent à réaliser.

# Varians-Synchro — Feuille de route de refonte du moteur d'alignement

**Document de cadrage — 11 octobre 2026**  
**Point de départ : Varians-Synchro V0.6.16**  
**Cible : branche V0.7.x, moteur unifié d'alignement entre repères**

## 1. Objectif et critères de succès

L'outil doit permettre d'aligner rapidement les **lignes physiques** de deux manuscrits, puis d'exporter des JSON directement exploitables dans Varians. La vérification humaine doit porter sur les problèmes philologiques réels, non sur des refus arbitraires du logiciel.

**Objectif d'usage à éprouver sur corpus :** réaliser un passage ordinaire de **quatre pages de travail pour une paire de témoins en 10 à 15 minutes**, du projet prêt à l'emploi à l'export, en incluant un contrôle visuel. Cet objectif est une **cible de recette**, pas une performance déjà démontrée ; les cas comportant des omissions ou transpositions complexes pourront demander davantage de temps.

**Invariants :**
- Un alignement est délimité par **deux repères homologues choisis par l'utilisateur** ; entre eux, le programme présume qu'il s'agit du même passage, sans tenter de démontrer cette identité.
- Les **pages, colonnes et sauts de folio ne sont pas des frontières d'alignement**. Chaque témoin fournit une suite continue de lignes en ordre de lecture.
- L'ordre de lecture est une donnée critique : il doit être inspectable et corrigeable, sans réécrire les ALTO/PAGE originaux.
- La HTR est **facultative** ; la quantité de texte estimée peut aider même si les mots reconnus sont erronés. Aucun pourcentage de progression n'est assimilé à une preuve de concordance textuelle.
- Les associations manuelles et les liens validés restent intangibles sans action explicite ; toutes les nouvelles associations automatiques sont **incertaines**.
- **Ignorée / hors périmètre** (statut global au témoin), **sans correspondance** (absence attestée, propre à une paire) et **non encore alignée** sont trois états distincts.
- Les projets `.vsynch` existants doivent être ouverts et migrés sans perdre les liens, l'historique ni les identifiants physiques ; les JSON restent compatibles avec le format réellement lu par Varians.
- Fonctionnement multiplateforme Python/PySide6, images locales ou IIIF, ALTO ou PAGE, HTR non obligatoire, i18n XML par langue.

## 2. Décision d'architecture : un seul moteur

**Supprimer à terme le tandem `interpolation.py` (interpolation par colonnes et positions verticales) + `residual_alignment.py` (extensions résiduelles).** Les conserver temporairement dans la branche de transition pour comparaison et retour arrière, puis retirer leurs commandes de l'interface ordinaire.

Nouveau trajet de calcul :

`Repères homologues → suites de lignes ordonnées → filtrage du périmètre → poids par ligne → progression cumulée normalisée → regroupements monotones proposés → contrôle/validation → JSON Varians`

La géométrie conserve deux rôles : **identifier et afficher** une ligne sur l'image ; **estimer la quantité de texte** si nécessaire. Elle ne sert plus à assimiler directement la hauteur d'une ligne de Mu à celle d'une ligne de F.

## 3. Jalons de développement

### J0 — Référence et non-régression (préparation)

- Geler une copie reproductible de la V0.6.16 et du projet `projetTest.vsynch` (Mu, F, A) ; ne jamais modifier les originaux de l'utilisateur.
- Conserver les résultats attendus des exports Mu–F, y compris les lignes ignorées, les folios et les sources IIIF.
- Construire un jeu de tests « oracle » avec correspondances humaines validées, couvrant une ligne isolée, deux colonnes, et un passage coupé entre deux folios.
- Documenter les points d'entrée actuels : `physical_alignment.py`, `page_order.py`, `interpolation.py`, `residual_alignment.py`, `varians_export.py`, `guided_ui.py`.

**Sortie du jalon :** corpus de tests de référence, sauvegarde et bilan des défauts connus.

### J1 — Flux physique continu et ordre de lecture (V0.7.0)

- Construire un inventaire commun `PhysicalLine` à partir des ALTO ou PAGE : témoin, folio, région/colonne, numéro d'ordre global, UID stable, texte HTR, rectangle, polygone, ligne de base si disponible.
- Mettre toutes les pages sélectionnées dans **un seul flux par témoin**, traversant folios et colonnes sans réinitialiser l'ordre ni les compteurs.
- Respecter les informations `ReadingOrder` lorsqu'elles sont fiables ; sinon proposer un ordre géométrique initial, affiché et révisable. Ne jamais confondre ordre documentaire des pages et ordre des colonnes.
- Ajouter une commande simple pour corriger l'ordre des pages/régions/lignes lorsqu'il est faux, en conservant la segmentation et les fichiers source.
- Écarter du flux actif les lignes globalement « ignorées », mais conserver leurs identifiants et leur visualisation grisée.
- Reconnaître les repères validés de type **1↔1, 1↔n et n↔m**, y compris quand leurs membres traversent un folio.

**Recette :** un intervalle allant de Mu 2v à Mu 3r et de F 14v à F 15r est extrait intégralement, dans le bon ordre, sans perte de ligne. Aucun besoin d'ancrages sur une même page.

### J2 — Moteur unique de progression textuelle (V0.7.1)

- Estimer un **poids** par ligne : (a) longueur HTR normalisée si exploitable ; (b) longueur de tracé/ligne de base ou largeur du polygone/rectangle, **calibrée par région** ; (c) poids uniforme comme repli.
- Détecter les indices d'HTR manifestement défaillante : texte absent, chaîne répétitive, longueurs aberrantes, couverture insuffisante. Une mauvaise HTR ne doit jamais bloquer le calcul.
- Convertir les poids en progression **cumulée de 0 à 1 dans chaque intervalle entre repères** ; chaque témoin est normalisé indépendamment. La quantité de lignes n'est pas une contrainte d'égalité.
- Associer les séquences par une méthode **monotone, déterministe et explicable** fondée sur la proximité des frontières cumulées. Proposer des groupes 1↔1, 1↔n et n↔m. Ne pas fusionner transitivement tous les intervalles qui se chevauchent : éviter les groupes géants.
- **Ne plus refuser** l'intervalle parce qu'il traverse une page, parce que le rapport de nombres de lignes dépasse 3, ou parce qu'un groupe contient plus de trois lignes d'un côté.
- Ne **jamais déduire automatiquement une absence** lorsqu'un côté devient vide ; présenter « passage à examiner » ou demander une confirmation explicite « sans correspondance ».
- Traiter chaque intervalle délimité par des groupes humains comme un bloc indépendant ; préserver les liens validés et les corrections manuelles même non validées.
- Autoriser le **recalcul complet des seules propositions automatiques incertaines** de l'intervalle, avec prévisualisation, remplacement transactionnel et annulation.

**Recette :** couverture par des propositions de toutes les lignes actives d'un passage ordinaire dont les deux côtés contiennent du texte, **ou diagnostic explicite pour chacune des lignes laissées libres** ; aucun blocage silencieux. Résultat identique à données et options identiques.

### J3 — Ergonomie : la synchronisation comme tâche rapide (V0.7.2)

- Flux guidé en trois actions : **poser deux repères → calculer → contrôler**.
- Dans le double visualiseur, naviguer sans perdre la sélection lorsque la correspondance franchit un folio ; précharger le folio suivant et garder le zoom utile.
- Une liste compacte montre les propositions de l'intervalle, avec raccourcis clavier pour **valider**, **corriger/fusionner**, **dissocier**, **marquer sans correspondance**, **poser un nouveau repère**, **suivante à vérifier** et **annuler**.
- Clic sur une proposition : mettre immédiatement en évidence toutes ses lignes, sur les deux témoins, même lorsque les pages affichées diffèrent.
- Afficher pour chaque intervalle : lignes Mu/F, méthode d'estimation, part couverte, nombre de validations, nombre d'exceptions ; détail des motifs de non-traitement.
- Mettre la HTR au second plan : utile pour la quantité de texte, jamais obligatoire pour travailler.
- Conserver le terme **« Cadres lignes »** et traduire **toutes** les nouvelles chaînes des catalogues `i18n/*.xml` présents.

**Recette :** aucun aller-retour obligatoire vers un autre onglet pour corriger une association ; l'utilisateur peut parcourir uniquement les lignes douteuses, sans contrôler individuellement celles qu'il a déjà validées.

### J4 — Gestion des exceptions et stabilité éditoriale (V0.7.3)

- Absence propre à une paire (`Mu ↔ F`), sans effet automatique sur `Mu ↔ A` ; possibilité de désigner une plage complète, pas seulement une ligne.
- Traiter les omissions, additions et décalages locaux par des **repères intermédiaires** et des segments séparés. Les transpositions complexes pourront être marquées « à traiter manuellement » sans fausser les correspondances ordinaires.
- Repérer les contradictions d'ordre entre deux groupes validés et **isoler seulement l'intervalle concerné**, plutôt que bloquer la synchronisation de toutes les pages.
- Garder la traçabilité : origine manuelle/automatique, méthode de pondération, repères, paramètres, révisions ; statut « incertain » par défaut des nouvelles propositions.
- Reprise transparente des projets ayant changé de source ALTO à PAGE, avec vérification stricte des identifiants/empreintes et aucune réassociation hasardeuse.
- Versionner le `.vsynch` si le schéma évolue, avec migration sur copie, sauvegarde pré-migration et rapport d'incompatibilités ; vérifier la réouverture sans perte.

**Recette :** suppression, ajout et modification d'un repère, puis recalcul local, ne changent jamais une autre association validée.

### J5 — Export JSON et validation réelle avec Varians (en continu ; finalisation V0.7.4)

- Tester **à chaque jalon**, et non uniquement à la fin, l'export `tei-manuscript-alignment` attendu par Varians.
- Respecter les lignes **hors périmètre** (aucun `<lb/>` fantôme) tout en préservant les numéros physiques et les `base_keys` ; maintenir les références exactes des Canvas et images locales/IIIF.
- Conserver deux politiques d'export distinctes : **validées uniquement** et **travail avec incertaines** ; indiquer la différence clairement.
- Vérifier, sur le projet test réel Mu–F, la synchronisation TEI↔Mu↔F et les changements de folio ; conserver F depuis son Manifest IIIF sans exiger des images locales.
- Contrôler l'intégrité : toutes les `base_keys` doivent pointer vers des lignes existantes et actives ; aucun lien validé ne disparaît.

**Recette :** les JSON se chargent dans Varians et les images synchronisées suivent les lignes TEI, sans intervention manuelle pour reconstruire les Canvas.

### J6 — Campagne pilote, performance et livraison (V0.7.x stable)

- Exécuter tests purs Python, tests Qt, tests de sauvegarde/migration, d'internationalisation et de cohérence d'export sur Windows, macOS et Linux dans la mesure des environnements disponibles.
- Tester : sans HTR ; HTR très bruitée ; PAGE à polygones ; ALTO à rectangles ; témoins avec deux colonnes ; rapports 1:1 et 1:5 ; passage sur trois folios ; intervalle de grande taille ; liens manuels 2↔1 ; absence confirmée ; changements de segmentation.
- Instrumenter les temps : ouverture/préparation, placement des repères, calcul, corrections, validation, export. Séparer la latence réseau IIIF du temps de calcul.
- Cibles initiales à mesurer : **calcul local ≤ 2 s pour un intervalle de 500 lignes par témoin** sur un poste usuel ; réponse aux commandes usuelles sans gel perceptible ; **10–15 min pour quatre pages ordinaires** avec contrôle visuel et export. Ces chiffres sont des objectifs à confirmer, non des résultats acquis.
- Livrer sources ZIP complètes, changelog, aide utilisateur, documentation de maintenance, tests et une note de migration précisant les anciens algorithmes retirés.

## 4. Ordre de priorité et règles de livraison

| Priorité | Livrable | Pourquoi |
|---|---|---|
| **P0** | Flux continu, ordre de lecture, repères multi-lignes et multi-pages (J1) | Sans cela, le calcul manque des lignes et reste prisonnier des folios. |
| **P0** | Un seul moteur cumulatif, sans blocage géométrique arbitraire (J2) | Résout le problème central de couverture. |
| **P0** | Aucun lien validé perdu ; export Varians vérifié (J0/J5) | Empêche une régression scientifique ou éditoriale. |
| **P1** | Contrôles clavier, navigation fluide et recalcul local (J3) | Condition d'adoption au quotidien. |
| **P1** | Absences et diagnostics par ligne (J4) | Permet de traiter les cas réels sans contorsion. |
| **P2** | Calibrage avancé des poids HTR/géométrie (affinage J2/J6) | Améliore la précision sans compromettre le socle simple. |
| **Hors de ce chantier** | Nouvelle HTR, transcription TEI automatique, transpositions générales, reconnaissance d'écriture | Risque de complexifier inutilement cette refonte. |

## 5. Porte de validation avant remplacement de l'ancien moteur

La refonte ne remplacera le moteur de production que lorsque ces conditions seront satisfaites :

1. **Zéro perte** de liens validés et d'exclusions éditoriales lors de la migration.
2. **Zéro omission silencieuse** d'une ligne active entre deux repères : chaque ligne est liée, explicitement laissée à examiner, ou qualifiée sans correspondance par décision humaine.
3. Des passages sur plusieurs pages et sur plusieurs colonnes sont synchronisés sans repère artificiel en limite de page.
4. Les propositions 1↔n et n↔m restent contrôlables, avec les incertitudes visibles.
5. L'export JSON reste lisible par Varians et conserve Mu/F, leurs folios et leurs sources d'images.
6. Un **essai chronométré avec l'utilisateur** démontre un gain de temps réel sur quatre pages représentatives.

**Principe directeur :** Varians-Synchro doit utiliser l'ordinateur pour organiser et répartir les lignes, et réserver le jugement philologique à l'éditeur. La complexité doit être dans la gestion fiable des sources et des exceptions, pas dans des heuristiques qui empêchent de travailler.
