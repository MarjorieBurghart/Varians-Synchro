# Rapport de recette — Varians-Synchro V0.8.5

## Environnement

- Python 3.13.5 sur Linux (environnement de construction).
- `pytest` et `lxml` disponibles ; **PySide6 absent**.
- Base source : V0.8.4.2, ZIP intégral repris sans reconstitution de code.

## Tests reproductibles

```bash
python -m compileall -q varians_synchro
python -m pytest -q
python recette_v085.py chemin/du/projet.vsynch --base Mu --output rapport.json
```

Bilan : **294 passed, 11 skipped**. Les 11 tests ignorés sont des contrôles Qt non exécutés, et non des succès simulés.

### Contrôles d'interface à reprendre sur Windows

1. Créer un projet et sauvegarder une première puis une deuxième fois ; vérifier la présence de la `.bak` et la possibilité d'ouvrir sa copie.
2. Ouvrir `test081.vsynch` et vérifier que Mu/F, les 469 Canvas de F, les ressources ALTO, les exclusions et les sessions s'affichent.
3. Créer des associations ALTO/PAGE sur un sous-ensemble de Canvas IIIF et vérifier la protection contre les doublons.
4. Rattacher une TEI aux lignes physiques d'un témoin après délimitation du périmètre.
5. Dans le contrôle TEI, afficher la première image, cliquer sur une autre ligne et utiliser « Fin » ; une seule image doit apparaître à la fois.
6. Dans la synchronisation visuelle, vérifier « Repères discrets » désactivé initialement et les sélections clic/Ctrl/Maj y compris sur plusieurs folios.
7. Enregistrer, fermer, rouvrir ; vérifier que groupes manuels/validés, absences et liaisons TEI persistent.
8. Produire `validated/` et `working/`, puis les charger dans la **version courante** de Varians ; vérifier les positions, les `base_keys`, les images locales et IIIF.
9. Vérifier les deux langues FR/EN dans les boîtes d'alerte, exports HTR et visualiseur.
10. Tester interruption de téléchargement IIIF et ressources locales manquantes sans perte de projet.

## Projets réels : audits **sans écriture**

| Projet | Témoins | Erreurs | Avertissements | Explication |
|---|---|---:|---:|---|
| `test081.vsynch` | Mu, F | 0 | 1 | F sans liens exportables vers Mu |
| `projetTest.vsynch` | Mu, F, A | 0 | 2 | Repères contradictoires Mu–F et Mu–A |

Les exports validés et de travail pour les deux projets donnent les mêmes empreintes JSON canoniques que ceux de la V0.8.4.2. Les avertissements ne sont ni supprimés ni corrigés automatiquement.

## Limites de certification

- L'absence de PySide6 **interdit de déclarer l'interface graphiquement validée**.
- Les ressources réseau IIIF ne sont pas testées en conditions réelles.
- La compatibilité avec le format documenté de Varians est contrôlée ; **l'import dans la version la plus récente de Varians n'a pas été exécuté** ici.
- La V0.8.5 peut servir de **candidate de référence stable**, sous réserve de cette dernière recette sur le poste utilisateur.
