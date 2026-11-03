# Conventions de développement, stratégie d'évolution et livraison

## Conventions existantes à conserver

- Python 3.10+ et standard library pour le cœur documentaire autant que possible ; PySide6 confiné aux modules GUI. L'ajout d'une dépendance doit être explicite et accompagné de tests multiplateformes.
- Préférer des fonctions métier pures ou à mutation documentée ; distinguer par le nom `preview`/`inspect`/`audit` (lecture seule), `apply`/`save`/`export` (écritures). Si la fonction existante contredit cette convention, le documenter avant changement.
- Préserver les dictionnaires JSON pour compatibilité avec les projets existants. Ne pas ajouter de champs éphémères non sérialisables (QObjects, `Path`, ensembles) dans les structures persistées.
- UTF-8, JSON `ensure_ascii=False`, identifiants XML/TEI non traduits ; séparer données scientifiques et messages d'interface.
- Échecs explicites (`ValueError` ou diagnostics) plutôt que succès partiel silencieux lorsqu'il s'agit de liens, migration ou export.
- Conserver les commentaires portant sur les « raisons » et invariants historiques, pas seulement le « comment ».
- Respecter les formats de chemins Windows et Unix ; stages atomiques dans le même volume que leur destination.

## Workflow recommandé pour une modification

1. Définir le contrat touché, l'invariant de non-régression et **un test qui échoue avant modification**.
2. Rechercher tous les utilisateurs du champ/fonction (`rg`, recherche AST, IDE), dont exporteurs et GUI.
3. Sur des projets copiés : établir le comportement initial, ajouter/adapter les tests, appliquer le changement le plus réduit possible.
4. Rejouer suite complète et contrôles croisés `.vsynch` + JSON Varians + audit + UI lorsqu'applicable.
5. Mettre à jour dans la **même livraison** ce dossier, les manuels concernés, `CHANGELOG`, tests et empreintes.
6. Exposer clairement ce qui a été testé et ce qui attend un contrôle sur machine réelle ; n'appeler « validé » que ce qui a été vérifié.

## Réorganisations à risque

- **`guided_ui.py`** : module monolithique, découpage possible mais seulement avec tests de cycle de vie, signaux Qt, état courant et dialogues de confirmation.
- **UID de lignes** : un calcul plus « élégant » briserait les liens historiques ; écrire une conversion à table de correspondance, pas un remplacement immédiat.
- **Sessions physiques ↔ TEI** : fusionner les modèles rendrait possible des déductions éditoriales abusives ; conserver des transactions séparées et une provenance vérifiable.
- **`alto_binding`** : nom historique utilisé pour ALTO **et** PAGE ; ne pas le renommer sans migration complète.
- **Manifests IIIF** : le JSON de présentation d'origine peut contenir des cas réels que le cache simplifié ne représente pas ; conserver le repli à l'URL originale.
- **Localisation** : une entrée manquante ou une variable `{...}` divergent peut bloquer le chargement ; toute révision linguistique doit être testée comme du code.

## Politique de versionnement

- Version applicative : `core.VERSION`; en v0.8.5.6, elle est seule modifiée dans les modules applicatifs.
- Version du format : `core.SCHEMA` + projet `version:1`, inchangés ; toute nouvelle version du format nécessite une matrice de migration.
- Historique : `CHANGELOG.md`, `CHANGELOG_V0856.md`, `TESTS_V0856.md`; ne jamais réécrire rétroactivement des rapports anciens comme s'ils appartenaient à la version présente.
- Intégrité des fichiers : l'historique Git du dépôt (les anciennes listes `MANIFEST_SHA256.json` et `SHA256SUMS.txt` ont été retirées).
- Distribution : fournir l'archive source **et** le dossier autonome ; l'archive ZIP n'est pas un installateur signé ni un exécutable autonome.

## Règles d'acceptation

Rejeter une PR qui réduit la couverture de tests, introduit une écriture implicite de sources, supprime des liens sans consentement, falsifie des statuts, produit des `base_keys` irrésolus, mélange les états `working`/`validated`, ou annonce un import Varians réel sans avoir exécuté cet import. Les questions de terminologie médiévale doivent être arbitrées par un éditeur/locuteur compétent, non par l'algorithme.
