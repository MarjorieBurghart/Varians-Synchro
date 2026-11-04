# Documents historiques retirés

Jusqu’à la version 0.8.5.6, chaque livraison de Varians-Synchro ajoutait à la racine du dépôt ses notes : journal de version, rapport de recette, guide de la nouveauté. Ces 57 fichiers ont été retirés en novembre 2026 : le guide utilisateur est désormais l’aide intégrée (`help/`), le journal des versions est `CHANGELOG.md`, et l’historique Git garde chaque fichier, à son dernier état comme à chacun des précédents.

Ils sont tous consultables au commit `f09a9b7` (le dernier qui les contient) : un lien ci-dessous, ou, dans un clone du dépôt, `git show f09a9b7:<nom du fichier>`.

Les documents de référence encore valables ont été mis à jour et rangés dans `docs/developer/` : [`ARCHITECTURE.md`](developer/ARCHITECTURE.md), [`FORMAT_PROJET.md`](developer/FORMAT_PROJET.md), [`EXPORT_VARIANS.md`](developer/EXPORT_VARIANS.md), [`INTERNATIONALISATION.md`](developer/INTERNATIONALISATION.md), [`PORTABILITE.md`](developer/PORTABILITE.md).

## Anciens guides utilisateur

Remplacés par l’aide intégrée (`help/<langue>.html`, F1 dans le logiciel). Plusieurs décrivent une interface qui a changé depuis (noms d’étapes, boutons, TEI obligatoire…) : ne pas s’y fier.

| Fichier | Sujet |
|---|---|
| [`GUIDE_ALIGNEMENT_VISUEL.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_ALIGNEMENT_VISUEL.md) | V0.6.6 — Consulter la ligne correspondante dans l’autre manuscrit |
| [`GUIDE_CONTROLE_VISUEL_TEI_V084.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CONTROLE_VISUEL_TEI_V084.md) | Varians-Synchro V0.8.4 — Contrôle visuel TEI et recherche textuelle |
| [`GUIDE_COPIES_HD_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_COPIES_HD_V0853.md) | Varians-Synchro V0.8.5.3 — Copies HD IIIF et traitement HTR externe |
| [`GUIDE_CORRECTIONS_MANUELLES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_CORRECTIONS_MANUELLES.md) | Corriger une correspondance entre les témoins — V0.6.10 |
| [`GUIDE_DEPANNAGE_SPYDER.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_DEPANNAGE_SPYDER.md) | Démarrage de Varians-Synchro sous Spyder |
| [`GUIDE_EXCEPTIONS_EDITORIALES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_EXCEPTIONS_EDITORIALES.md) | Varians-Synchro V0.7.3 — Exceptions éditoriales et absences confirmées |
| [`GUIDE_FINALISATION_V0851.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_FINALISATION_V0851.md) | Guide — Varians-Synchro V0.8.5.1 |
| [`GUIDE_INTERPOLATION_COLONNES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_INTERPOLATION_COLONNES.md) | Synchroniser les colonnes avec deux ancrages — V0.6.7 |
| [`GUIDE_LIAISON_TEI_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_LIAISON_TEI_V083.md) | Varians-Synchro — V0.8.2 + V0.8.3 — Intégration TEI et rattachement physique |
| [`GUIDE_LIGNES_RESIDUELLES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_LIGNES_RESIDUELLES.md) | Contrôle et complétion des lignes résiduelles (V0.6.14) |
| [`GUIDE_ORDRE_VISUEL_PAGES.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_ORDRE_VISUEL_PAGES.md) | Varians-Synchro V0.7.2.2 — Réordonnancement visuel des pages |
| [`GUIDE_PAGE_XML.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PAGE_XML.md) | Importer et synchroniser avec PAGE-XML ou ALTO |
| [`GUIDE_PERIMETRE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PERIMETRE.md) | Varians-Synchro V0.6.11 — Lignes hors périmètre |
| [`GUIDE_PROGRESSION_TEXTUELLE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_PROGRESSION_TEXTUELLE.md) | Varians-Synchro 0.7.1 — Synchroniser par progression du passage |
| [`GUIDE_RESSOURCES_V081.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_RESSOURCES_V081.md) | Varians-Synchro V0.8.1 — Projet, témoins et associations par lots |
| [`GUIDE_REVISION_RAPIDE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_REVISION_RAPIDE.md) | Guide V0.7.2 — Vérifier rapidement les alignements |
| [`GUIDE_SAUVEGARDE_V085.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_SAUVEGARDE_V085.md) | Sauvegardes `.vsynch` — V0.8.5 |
| [`GUIDE_STABILITE_SPYDER.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_STABILITE_SPYDER.md) | Varians-Synchro V0.7.1.1 — stabilité sous Spyder |

## Journaux de version détaillés

Le résumé de chaque version est dans `CHANGELOG.md` ; le détail de chaque changement est dans l’historique Git.

| Fichier | Sujet |
|---|---|
| [`CHANGELOG_V0.6.15.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0.6.15.md) | Varians-Synchro V0.6.15 |
| [`CHANGELOG_V081.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V081.md) | Varians-Synchro V0.8.1 — V0.8.0 + V0.8.1 livrées ensemble |
| [`CHANGELOG_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V083.md) | Varians-Synchro V0.8.2 + V0.8.3 |
| [`CHANGELOG_V084.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V084.md) | Varians-Synchro V0.8.4 — Contrôle visuel de la liaison TEI |
| [`CHANGELOG_V0841.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0841.md) | Varians-Synchro V0.8.4.1 — Fenêtre de liaison TEI allégée |
| [`CHANGELOG_V0842.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0842.md) | Varians-Synchro V0.8.4.2 — Sélection visuelle prévisible |
| [`CHANGELOG_V085.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V085.md) | Varians-Synchro V0.8.5 — Consolidation et recette |
| [`CHANGELOG_V0851.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0851.md) | Varians-Synchro V0.8.5.1 — ergonomie et finalisation |
| [`CHANGELOG_V0852.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0852.md) | Varians-Synchro V0.8.5.2 — Correction du message de fin des téléchargements IIIF HD |
| [`CHANGELOG_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0853.md) | Varians-Synchro V0.8.5.3 — Registre des images IIIF HD |
| [`CHANGELOG_V0854.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0854.md) | V0.8.5.4 |
| [`CHANGELOG_V0855.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0855.md) | Varians-Synchro V0.8.5.5 — Refonte des traductions |
| [`CHANGELOG_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0856.md) | Varians-Synchro v0.8.5.6 — dossier complet de maintenance et passation |

## Rapports de tests et de recette

Les résultats valaient pour la version de leur titre ; la CI (Linux, Windows) les remplace pour les versions suivantes.

| Fichier | Sujet |
|---|---|
| [`AUDIT_INTEGRITE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/AUDIT_INTEGRITE_V074.md) | Varians-Synchro V0.7.4 — Contrôle global de cohérence |
| [`RAPPORT_RECETTE_V074.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/RAPPORT_RECETTE_V074.md) | Rapport de recette — Varians-Synchro V0.7.4 |
| [`RAPPORT_RECETTE_V085.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/RAPPORT_RECETTE_V085.md) | Rapport de recette — Varians-Synchro V0.8.5 |
| [`TESTS_V0.7.2.2.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0.7.2.2.md) | Tests — V0.7.2.2 |
| [`TESTS_V0.7.3.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0.7.3.md) | Validation V0.7.3 |
| [`TESTS_V081.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V081.md) | Recette V0.8.0–V0.8.1 |
| [`TESTS_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V083.md) | Recette V0.8.2 + V0.8.3 |
| [`TESTS_V084.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V084.md) | Addendum V0.8.4.1 — Aperçu unique |
| [`TESTS_V0842.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0842.md) | Recette V0.8.4.2 — Sélection visuelle entre témoins |
| [`TESTS_V0851.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0851.md) | Recette Varians-Synchro V0.8.5.1 |
| [`TESTS_V0852.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0852.md) | Recette Varians-Synchro V0.8.5.2 |
| [`TESTS_V0853.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0853.md) | Recette V0.8.5.3 |
| [`TESTS_V0855.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0855.md) | Recette de Varians-Synchro V0.8.5.5 |
| [`TESTS_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0856.md) | Procès-verbal de vérifications — Varians-Synchro v0.8.5.6 |

## Notes de livraison, correctifs et feuilles de route

Livraisons de l’époque où le code circulait en archives, sans Git.

| Fichier | Sujet |
|---|---|
| [`CORRECTIF_DOUBLONS_IIIF_V0811.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_DOUBLONS_IIIF_V0811.md) | Varians-Synchro V0.8.1.1 — Détection des associations ALTO/PAGE en double |
| [`CORRECTIF_EXPORT_VARIANS.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_EXPORT_VARIANS.md) | Correctif V0.6.16 : export vers Varians pour TEI à périmètre partiel |
| [`CORRECTIF_OUVERTURE_PROJET_V0812.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_OUVERTURE_PROJET_V0812.md) | Correctif V0.8.1.2 — Projet vide à la réouverture |
| [`CORRECTIF_SAUVEGARDE_V0.7.2.1.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CORRECTIF_SAUVEGARDE_V0.7.2.1.md) | Varians-Synchro V0.7.2.1 — Avertissement de projet non enregistré |
| [`DIAGNOSTIC_BASE_KEYS.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/DIAGNOSTIC_BASE_KEYS.md) | Vérifier les `base_keys` dans l’export Varians |
| [`FEUILLE_DE_ROUTE.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/FEUILLE_DE_ROUTE.md) | V0.6.15 — Export direct vers Varians 0.8.5.2 |
| [`FEUILLE_DE_ROUTE_REFONTE_V0.7.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/FEUILLE_DE_ROUTE_REFONTE_V0.7.md) | Avancement : J1 (V0.7.0) et J2 (V0.7.1) implémentés |
| [`FEUILLE_DE_ROUTE_V08.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/FEUILLE_DE_ROUTE_V08.md) | Feuille de route — Varians-Synchro V0.8 |
| [`LIVRAISON_V083.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/LIVRAISON_V083.md) | Livraison — Varians-Synchro V0.8.3 |
| [`LIVRAISON_V084.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/LIVRAISON_V084.md) | Varians-Synchro V0.8.4 — Note de livraison |
| [`PASSATION_DEV_V085.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/PASSATION_DEV_V085.md) | Note de passation technique — Varians-Synchro V0.8.5 |
| [`REFONTE_V0.7.0.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/REFONTE_V0.7.0.md) | Varians-Synchro V0.7.0 — J1 : flux de lecture continu |
