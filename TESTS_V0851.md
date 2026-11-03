# Recette Varians-Synchro V0.8.5.1

Exécution : `PYTHONPATH=. pytest -q` depuis le dossier de la distribution.

**305 tests réussis, 11 ignorés (dépendants de PySide6 non présent dans cet environnement).**

### Nouvelles vérifications

- Catalogue FR/EN synchronisé et nouveaux libellés/infobulles présents.
- Commandes de « Associer les ressources » placées avant le panneau de statut.
- Sorties JSON et projet Varians disponibles dans « Finaliser ».
- IIIF native-size v2 / v3, sélection explicite de Canvas, contrôle JPEG, dossiers vides, non-écrasement, interruption et refus des doublons.
- Export Varians : TEI copiée à l’octet près, images locales ou Manifest IIIF, liens ALTO/PAGE, sortie transactionnelle et compatibilité du XML avec le parseur de référence de Varians V0.8.5.6.
- `projetTest.vsynch` et `test081.vsynch` : sorties JSON *validées et de travail* strictement identiques à la V0.8.5.

### Réserves

1. Aucune suite Qt ni téléchargement IIIF en ligne réelle exécutés ici.
2. Compatibilité du projet exporté à contrôler dans la dernière version installée de Varians : le parseur de référence vérifié correspond à V0.8.5.6.
3. L’export n’est pas une garantie philologique d’alignement de chaque `<lb/>` TEI ; la correspondance physique est explicitement décrite comme telle dans les métadonnées JSON.
