# Varians-Synchro V0.8.1 — V0.8.0 + V0.8.1 livrées ensemble

- Création d'un projet avec chemin `.vsynch` choisi et fichier créé immédiatement ; protection des modifications non enregistrées conservée.
- Première étape centrée sur un témoin : une seule entrée « Ajouter un témoin », fiche complète et rééditable, choix du pivot.
- Fiche transactionnelle : l'annulation n'importe aucun fichier et ne touche pas aux associations existantes.
- Images locales triées naturellement dès l'import ; conservation de l'ordre manuel.
- Import groupé ALTO/PAGE, support IIIF conservé, TEI enregistrée comme référence en attente d'alignement éditorial.
- Appariement image ↔ ALTO/PAGE : noms uniques puis rang naturel contrôlé, aperçu éditable, contrôle de duplications et des changements entre prévisualisation et commit.
- Suppression des commandes et du code graphique historique V0.5/TXT de l'interface principale ; lancement GUI simplifié. Conservation des données historiques dans les projets chargés.
- Réutilisation **sans modification** du moteur de progression textuelle, de la révision rapide et de l'export JSON V0.7.4.
- Localisation FR/EN ; tests métier et documentation ajoutés.

Le rattachement effectif `<lb edRef>` ↔ lignes PAGE/ALTO est planifié pour V0.8.2–V0.8.3 et **n'est pas implémenté ici**.
