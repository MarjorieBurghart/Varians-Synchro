# Varians-Synchro V0.8.4.1 — Fenêtre de liaison TEI allégée

## Changement demandé

La V0.8.4 montrait simultanément trois blocs, dont deux extrémités chargées automatiquement. La V0.8.4.1 présente **une seule ligne TEI et son recadrage manuscrit** à la fois.

1. À l'ouverture, la **première ligne TEI** est sélectionnée et son image se charge.
2. Un clic sur n'importe quelle ligne TEI remplace le texte et l'image du même panneau.
3. Les boutons **Début** et **Fin** déplacent directement la sélection.
4. La recherche filtre la liste sans déclencher de téléchargements d'images pour chaque frappe ; cliquer sur un résultat charge son aperçu.
5. Une réponse IIIF ancienne arrivée après un changement de sélection ne peut pas écraser l'aperçu courant (compteur de requêtes conservé).
6. Si les deux extrémités ne sont pas chargées pour vérification, une confirmation supplémentaire est demandée, sans empêcher l'utilisateur de poursuivre volontairement.

## Invariants

Aucune modification de la logique de lecture des TEI, du périmètre, des objets `tei_binding`, du fichier `.vsynch`, des correspondances intertémoins, du moteur d'alignement V0.7.4 ni de l'export JSON vers Varians.

## Recette

Voir `TESTS_V084.md` et `tests/test_tei_visual_gui_qt_084.py` (test graphique mis à jour). Le contrôle graphique sur une installation PySide6 est distinct des tests sans Qt.
