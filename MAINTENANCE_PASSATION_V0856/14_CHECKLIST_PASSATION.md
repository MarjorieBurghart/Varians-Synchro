# Procès-verbal de passation : checklist à remplir par le repreneur

**Livraison** : Varians-Synchro v0.8.5.6 — 19/10/2026  
**Preneur** : __________________________  
**Date / système / Python / Qt** : __________________________

## Inventaire et vérification

- [ ] Archive reçue ; intégrité ZIP et SHA-256 vérifiées.
- [ ] `VERSION` et `SCHEMA` relevés ; absence de migration des fichiers `.vsynch` confirmée.
- [ ] 37 fichiers de package inventoriés (36 modules fonctionnels et `__init__.py`), entrypoints identifiés.
- [ ] Dossier `MAINTENANCE_PASSATION_V0856/` parcouru, notes de versions anciennes différenciées.
- [ ] Environnement Python créé, dépendances et tests de base installés.
- [ ] `python -m pytest -q` réussi, sorties et skips joints ; GUI Qt testée **ou** limite formellement déclarée.

## Compréhension du métier

- [ ] Capacité à expliquer différence **correspondance**, **absence**, **hors périmètre**, **périmé** et **incertain**.
- [ ] Capacité à reconstituer une ligne physique et son identifiant stable.
- [ ] Capacité à contrôler un `tei_binding` depuis l'édition source, et à expliquer pourquoi l'ordre égal ne démontre pas la justesse éditoriale.
- [ ] Capacité à auditer un `base_key` secondaire et retrouver sa ligne dans le JSON pivot.
- [ ] Capacité à expliquer `validated/`, `working/`, le rôle du rapport d'export et les limites de l'export projet.

## Fiabilité et évolution

- [ ] Copies de `.vsynch` et sources préparées pour essais ; origine scientifique jamais écrasée.
- [ ] Scénarios de sauvegarde `.bak` et d'annulation ouverture/création exécutés.
- [ ] Deux Manifests IIIF d'exemple, ALTO et PAGE avec polygones disponibles pour la recette.
- [ ] Compatibilité contrôlée dans **la version réellement utilisée de Varians** — ou marquée non vérifiée.
- [ ] Cinq catalogues traduits contrôlés par des natifs — ou contrôle restant expressément listé.
- [ ] Procédure de release et regeneration des SHA-256 comprise.
- [ ] Toute limite non couverte par l'automatisation a un responsable/une procédure, sans statut fictif « validé ».

## Remise au nouveau développeur

Le lot remis doit contenir : code source, tests, documentation technique autonome, document de version, exemples non sensibles, inventaire des dépendances et empreintes. Une première correction doit commencer par **un test de non-régression**, non par une refonte généralisée.

**Acceptation** : ________________________  **Réserves** : ________________________
