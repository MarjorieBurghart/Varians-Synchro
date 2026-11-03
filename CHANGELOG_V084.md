# Varians-Synchro V0.8.4 — Contrôle visuel de la liaison TEI

Base : **V0.8.3**, moteur V0.7.4 et export Varians inchangés.

- Nouvelle fenêtre de liaison TEI : liste complète des lignes TEI à gauche ; **aperçus automatiques de la première et de la dernière ligne** à droite ; **sondage intermédiaire facultatif** depuis une ligne sélectionnée et recherche locale dans la liste.
- Recadrages de manuscrits avec surlignage du contour polygonal exact de la ligne (PAGE/ALTO) ou rectangle de secours ; chargement asynchrone.
- Préférence pour les requêtes **IIIF Image API v2/v3 sur la région concernée**, en tenant compte des résolutions différentes Canvas/XML ; chargement local et URL directe également prévus.
- Ouverture de la ligne sélectionnée dans le visualiseur graphique existant, avec zoom et contour.
- Validation toujours explicite, avec avertissement supplémentaire lorsque l'un des aperçus de contrôle n'a pas été chargé.
- Pour un témoin lié à une TEI **à jour**, la vue textuelle et le panneau de texte facultatif utilisent la TEI plutôt que la HTR. Recherche dans la TEI depuis la fenêtre de synchronisation : saut vers la ligne physique de la page concernée, sans créer de lien.
- Nouvelles traductions FR/EN et tests purs sur les extrémités, les transformations géométriques, les requêtes IIIF v2/v3, les sources périmées et la sauvegarde/réouverture.
- `tei_visual.py` isole la logique de prévisualisation **sans dépendance Qt** ; `linked_tei_texts` offre une lecture sûre de la transcription déjà validée.

Le format `.vsynch` **n'est pas modifié** ; aucune migration n'est requise.

**Recette de cette livraison :** voir `TESTS_V084.md`. Les tests graphiques Qt sont présents pour être lancés sur un poste disposant de PySide6 ; ils n'ont pas été exécutés ici.
