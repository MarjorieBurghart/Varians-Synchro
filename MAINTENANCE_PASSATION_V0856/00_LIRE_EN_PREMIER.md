# Varians-Synchro — Dossier autonome de maintenance et de passation

**État du dossier : 19 octobre 2026 — application v0.8.5.6.**

Ce répertoire est le **point d'entrée unique pour une reprise du code par une autre équipe**. Il ne remplace ni le guide utilisateur (`help/<langue>.html`, affiché dans le logiciel par F1), ni les manuels développeur traduits (`docs/developer/`) : il décrit les contrats à préserver et la manière de travailler sur le logiciel. Les notes de livraison des versions 0.6 à 0.8.5.6 (journaux, recettes, anciens guides) ont été retirées du dépôt ; elles restent dans l'historique Git, recensées dans [`docs/HISTORIQUE.md`](../docs/HISTORIQUE.md). Elles témoignent des choix antérieurs et ne doivent pas être prises pour une spécification plus récente que le code.

## Consulter dans cet ordre

1. `01_PREMIERE_REPRISE.md` — installation, première exploration et vérifications sans rien modifier.
2. `02_ARCHITECTURE_ET_FLUX.md` — modèle mental et parcours de données.
3. `03_CARTE_DU_CODE.md` — cartographie effective des modules et points d'entrée.
4. `04_FORMATS_ET_PERSISTANCE.md` — contrat `.vsynch`, identifiants, rétrocompatibilité et sauvegarde.
5. `05_MOTEURS_ET_INVARIANTS.md` — groupes, algorithmes, niveaux de preuve et intégrité.
6. `06_TEI_ET_EDITIONS.md` — extraction TEI, liaisons et limites philologiques.
7. `07_IMAGES_IIIF_ALTO_PAGE.md` — ingestion et gestion des copies HD.
8. `08_EXPORT_VERS_VARIANS.md` — contrat des deux exports et compatibilité à vérifier.
9. `09_INTERFACE_ET_I18N.md` — Qt, Spyder, cycle de vie, sept catalogues.
10. `10_TESTS_ET_RECETTE.md` — commandes reproductibles et matrice d'essais.
11. `11_CONVENTIONS_ET_EVOLUTIONS.md` — politique de modifications, versions et migrations.
12. `12_RISQUES_ET_LIMITES.md` — dette, limites et contrôles humains nécessaires.
13. `13_REGISTRE_DECISIONS.md` — décisions motivées et distinction projetée/réalisée.
14. `14_CHECKLIST_PASSATION.md` — checklist contradictoire de réception.
15. `annexes/INVENTAIRE_MODULES_AUTOGENERE.md` — référence AST générée depuis le code livré.
16. `annexes/TRACABILITE_CODE_TESTS.md` — fonctions, tests et anciens documents pertinents.

## Limites de ce dossier

- **Vérifié par lecture du code et tests locaux** : structures, fonctions, flux, invariants explicites ; voir `10_TESTS_ET_RECETTE.md`.
- **Connu des échanges et de la documentation historique** : motivations éditoriales ; voir `13_REGISTRE_DECISIONS.md`.
- **Non vérifié ici** : exécution interactive sous Windows avec PySide6, comportement des serveurs IIIF réels, import dans la version *actuelle* de Varians, appréciation linguistique par locuteurs natifs.
- Les exemples JSON sont **schématiques** et ne constituent pas des fichiers de projet valides à eux seuls.

## Identification du livrable

Version applicative dans `varians_synchro/core.py` : `VERSION = '0.8.5.6'` ; format persistant distinct : `format = "varians-synchro-project"`, `version = 1` — ce dernier **ne change pas**. Version v0.8.5.6 **documentaire**, sans modification de l'algorithme ni des catalogues de traduction. Les captures d'environnement et compteurs de tests de cette livraison se trouvent dans [`TESTS_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0856.md) et la liste de ses modifications dans [`CHANGELOG_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/CHANGELOG_V0856.md) (historique Git) ; les changements suivants sont dans `CHANGELOG.md`.

**Règle d'or** : ne jamais transformer une suggestion algorithmique, une ligne physiquement correspondante, ou un JSON structurellement compatible en attestation éditoriale vérifiée sans contrôle humain explicite.
