# Recette V0.8.4.2 — Sélection visuelle entre témoins

## Commande automatisée

```bash
python -m pytest -q
```

Résultat dans l'environnement de construction : **283 tests réussis, 11 modules/test suites Qt ignorés faute de PySide6**. Ces tests Qt sont livrés dans le dossier `tests/` pour exécution locale sous Windows/Spyder.

## Scénario prioritaire (à exécuter sur le vrai projet)

1. Ouvrir « Synchronisation visuelle entre témoins » avec Mu et F.
2. Vérifier que « Repères discrets » est **décoché sur les deux panneaux** et que les contours complets apparaissent.
3. Sur Mu, sélectionner la ligne 2, puis cliquer simplement la ligne 5 : **seule** la ligne 5 doit rester sélectionnée.
4. Sur Mu, Ctrl+cliquer ligne 7 : 5 et 7 sont sélectionnées. Ctrl+cliquer à nouveau 5 : seule 7 reste.
5. Cliquer sans modificateur ligne 3, puis Maj+cliquer ligne 6 : toutes les lignes de 3 à 6 doivent être sélectionnées, inclusivement. Tester de nouveau à rebours.
6. Sélectionner une ligne sur le folio précédent, passer au folio suivant et cliquer sans modificateur une nouvelle ligne : **l'ancienne sélection doit disparaître partout**, même si elle était hors écran.
7. Dans les mêmes circonstances, utiliser Maj : la plage doit respecter l'ordre de lecture entre les folios.
8. Sur une ligne Mu avec une correspondance enregistrée dans F, vérifier le contour rose dans F. Cliquer une ligne Mu différente : **le contour rose précédent disparaît** et la nouvelle correspondance (s'il en existe une) apparaît.
9. Ctrl+sélectionner deux lignes Mu ayant chacune des liens : les correspondances des deux doivent apparaître dans F, sans créer de sélection orange dans F.
10. Activer volontairement « Repères discrets » puis le désactiver ; les choix doivent demeurer stables lors d'un changement de folio.
11. Montrer le panneau « Texte HTR/TEI » et répéter clic, Ctrl, Maj dans sa liste ; les sélections doivent correspondre à celles de l'image.
12. Enregistrer et rouvrir le `.vsynch` : les groupes et `base_keys` exportées doivent être identiques à ceux de la version précédente.

Les choix de sélection dans le panneau visuel sont temporaires et ne sont pas des modifications éditoriales enregistrées.
