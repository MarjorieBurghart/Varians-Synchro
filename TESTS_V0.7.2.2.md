# Tests — V0.7.2.2

Exécution dans l’environnement de préparation, sans PySide6 :

`python -m pytest -q`

**201 tests réussis ; 7 tests ignorés** (dont un nouveau test d’interface et six anciens tests graphiques nécessitant Qt).

Les nouveaux tests vérifient :

- Inversion de l’ordre de pages dont les noms sont arbitraires ;
- Constance de l’association image ↔ PAGE-XML et des UID de lignes ;
- Rejet atomique de listes de pages incomplètes ou dupliquées ;
- Déplacement d’une page par identifiant stable, sans se fier au tri alphabétique ;
- Conservation d’un ordre manuel après ajout ultérieur de nouvelles pages ;
- Sérialisation et réouverture `.vsynch` ;
- Détection des changements non sauvegardés ;
- Cohérence des libellés et paramètres dans les catalogues FR/EN.

Un test facultatif `tests/test_page_manager_qt.py` contrôle réellement les widgets,
les miniatures locales et un déplacement au sein de la liste. Il est ignoré en
l’absence de PySide6 et doit être exécuté sur un poste équipé de cette bibliothèque :

`python -m pytest -q tests/test_page_manager_qt.py`

**Limite** : le glisser-déposer natif et les miniatures IIIF n’ont pas été testés
sur un poste Windows dans cet environnement.
