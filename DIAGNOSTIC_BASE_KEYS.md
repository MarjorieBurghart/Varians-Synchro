# Vérifier les `base_keys` dans l’export Varians

Le témoin pivot (par exemple `Mu.json` avec `--base Mu`) ne comporte **jamais** de `base_keys` : ses clés sont dérivées de ses identifiants de page et des numéros physiques de ligne.

Les témoins secondaires doivent en revanche posséder des `base_keys` sur les lignes effectivement liées au pivot. **Ce champ ne doit pas être inventé** pour une ligne sans correspondance.

L’export écrit deux dossiers :

- `validated/` : seulement les groupes validés manuellement ;
- `working/` : groupes validés et propositions automatiques incertaines.

Si vous venez de lancer le moteur d’alignement sans valider individuellement les résultats, un témoin secondaire peut avoir **0** ligne liée dans `validated/` alors qu’il en a beaucoup dans `working/`. Le nouveau diagnostic de la V0.7.2.3 le signale avant de choisir le dossier de destination.

Le rapport `rapport_export.json` inclut `audit`, puis pour chaque témoin secondaire `validated_linked_lines`, `working_linked_lines` et `reason` lorsqu’un contrôle s’impose. Si les deux nombres valent 0, vérifier successivement le bon pivot, l’existence d’une session directe, les liens enregistrés et les éventuelles références périmées ou lignes ignorées.

Ne mélangez pas les JSON de deux exports ou de deux pivots différents. Dans Varians, importer le JSON de Mu pour Mu et celui de F pour F depuis **le même dossier** (`working` ou `validated`). Si le doute persiste, transmettre le nouveau `.vsynch`, le JSON du témoin secondaire et `rapport_export.json` pour un diagnostic des références exactes.

Le moteur et les données ne sont pas modifiés par ce contrôle : il vise uniquement à empêcher qu’un export sans correspondance passe inaperçu.

Contrôle facultatif sans PySide6 : `python verifier_base_keys_json.py chemin/vers/F.json`. Le script n’écrit rien et affiche notamment le rôle du JSON et le nombre de lignes munies de `base_keys`.
