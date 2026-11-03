# Rapport de recette — Varians-Synchro V0.7.4

## Résultats exécutés ici

- `python -m pytest -q` : **228 tests réussis, 7 ignorés** faute de PySide6. Les deux suites de l'ancien moteur géométrique ont été **exécutées** cette fois (5 et 6 réussites, respectivement).
- Tests V0.7.4 : gestion de trois témoins, groupes 1↔n et n↔m, omissions confirmées par paire, préservation du périmètre, doublons, références périmées, repères croisés, contrôle de l’intégrité des `base_keys`, export transactionnel et test de performance local 500×500.
- Lecture d’un vrai `projetTest.vsynch` (Mu, F, A) : **0 erreur**, **2 avertissements d’ordre de repères**, sans aucune modification du projet.
- Statistiques du projet : Mu 211 lignes actives / 332 physiques ; F 241 / 282 ; A 97 / 116. Sessions directes Mu–F : 198 groupes, dont 60 validés ; Mu–A : 48 groupes, dont 38 validés. Il existe aussi une session F–A.
- Non-régression des JSON de Varians sur ce projet : **empreintes de sérialisation identiques** à celles de V0.7.3 pour les deux politiques `validated/` et `working/` (hors rapport auxiliaire).
- Politique validée : F 70 lignes avec `base_keys`, A 39. Politique de travail : F 224, A 49. Pivot Mu 211 clés physiques actives, non renumérotées.
- Tous les `base_keys` générés dans les deux politiques sont présents dans le JSON de Mu, y compris les groupes traversant les folios.

## Non validé dans cet environnement

- Les **7 tests Qt** sont ignorés parce que PySide6 n'est pas disponible.
- Les gestes de glisser-déposer de pages, l'affichage des miniatures et le nouveau bouton de contrôle doivent être testés sous Windows/Spyder.
- Compatibilité macOS/Linux de l’interface et téléchargements IIIF en conditions réseau réelles non testés ici.
- Le temps **10–15 minutes pour quatre pages** est une cible d’utilisation à mesurer sur des manuscrits réels ; aucun temps d’édition humaine n’a été mesuré par la suite de tests.
- Les deux repères contradictoires déjà détectés nécessitent une décision philologique, pas une correction automatisée.

## Plan de recette pour l'utilisateur

1. Extraire dans un **nouveau répertoire**, puis ouvrir une **copie** du `.vsynch` de travail.
2. Lancer **4 · Progression → Contrôler la cohérence du projet…** ; inspecter les erreurs/avertissements et le nombre de lignes actives.
3. Vérifier les deux repères contradictoires dans les paires signalées ; ne pas les modifier automatiquement.
4. Tester la navigation/révision et une absence confirmée, puis vérifier que la modification n’affecte pas une autre paire.
5. Exporter en choisissant Mu comme pivot. Charger, depuis **un seul et même dossier**, `validated/Mu.json` + `validated/F.json`, ou `working/Mu.json` + `working/F.json`.
6. Dans Varians, vérifier les folios de F au moyen du Manifest IIIF et la navigation TEI ↔ Mu ↔ F ; examiner les cas où une ligne recouvre plusieurs lignes du témoin opposé.
7. Fermer un projet modifié sans l’enregistrer pour contrôler le dialogue de sauvegarde (conservé de V0.7.2.1).
8. Si nécessaire, envoyer le rapport `audit_vsynch.py` et le `rapport_export.json`, sans les images ni les transcriptions complètes.
