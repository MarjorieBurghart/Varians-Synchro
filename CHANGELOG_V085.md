# Varians-Synchro V0.8.5 — Consolidation et recette

La V0.8.5 part **exclusivement de V0.8.4.2**. Le moteur d'alignement V0.7.4, le rattachement TEI et la projection JSON Varians n'ont pas été modifiés.

## 1. Sauvegarde et récupération

- Écriture dans un fichier temporaire unique dans le même dossier, synchronisation sur disque puis remplacement atomique.
- À chaque **réenregistrement** d'un `.vsynch` déjà existant, conservation d'une copie des octets de la version précédente dans `<projet>.vsynch.bak`.
- Aucune `.bak` à la création initiale ; elle apparaît au premier réenregistrement.
- Les échecs simulés d'écriture, de copie de sauvegarde et de remplacement final ne détruisent pas le document précédent. Les fichiers temporaires sont nettoyés.
- Vérification du projet avant toute ouverture de fichier en écriture ; conservation des droits du fichier sur POSIX et refus de remplacer directement un lien symbolique.
- La récupération depuis la `.bak` est **manuelle** : l'application ne remplace jamais un projet corrompu sans demande explicite.

## 2. Nettoyage prudent

- Suppression de l'API obsolète `import_plain_text` qui servait aux nouveaux imports TXT/MD historiques ; aucune commande de l'interface V0.8 ne l'utilise.
- Les anciennes ressources TXT/PIVOT et les anciennes sessions présentes **dans les projets déjà créés** sont conservées, pas supprimées lors de l'ouverture.
- Les anciens algorithmes de géométrie encore accessibles comme opérations de révision ont été conservés ; les supprimer casserait des fonctions toujours présentes.

## 3. Traductions FR/EN

- Vérification structurelle des deux catalogues XML, des clés et des paramètres de traduction.
- Ajout d'un test statique couvrant **tous les appels explicites** à `tr('clé ou phrase')` dans les fichiers Python.
- Traduction du libellé oublié pour les groupes estimés et de deux bilans d'export / réimport HTR ; correction des alertes explicites de la gestion des pages.
- Les symboles de navigation ◀ et ▶ restent des symboles, sans entrée de traduction.
- Une vérification humaine du rendu graphique complet demeure nécessaire : les textes produits dynamiquement ne sont pas tous contrôlables par cette analyse statique.

## 4. Diagnostic de livraison en lecture seule

`recette_v085.py` prend en charge un `.vsynch` et produit un rapport JSON de cohérence, des liaisons TEI et, avec `--base`, des empreintes des deux exports `validated` et `working`.

```bash
python recette_v085.py mon_projet.vsynch --base Mu --output rapport.json
```

Ne modifie jamais le `.vsynch`, les images, la TEI ou les XML ALTO/PAGE. Refuse d'écraser un `.vsynch` ou sa `.bak` avec un rapport.

## 5. Recette constatée

- `python -m pytest -q` : **294 tests réussis ; 11 tests Qt ignorés** (PySide6 absent).
- `compileall` : succès.
- `test081.vsynch` : 2 témoins (Mu, F), 0 erreur bloquante, 1 avertissement (F sans correspondance exportable).
- `projetTest.vsynch` : 3 témoins (Mu, F, A), 0 erreur bloquante, 2 avertissements de repères contradictoires (Mu–F et Mu–A).
- Pour ces deux projets, les six familles de sorties témoin/mode concernées ont les **mêmes empreintes de JSON canonique** que la V0.8.4.2. Aucune donnée personnelle de ces projets n'est incluse dans la distribution.
- Le format a été rapproché de `ALIGNMENT_FORMAT.md` de la version Varians 0.8.5.6 disponible dans l'environnement ; l'essai réel dans la dernière version de Varians demeure à faire.

**Non réalisé ici** : essais PySide6 sur Windows/macOS/Linux ; affichage et téléchargements IIIF en situation réelle ; essai de bout en bout dans la version actuelle de Varians.
