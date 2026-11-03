# Varians-Synchro V0.7.2.1 — Avertissement de projet non enregistré

Le logiciel refuse maintenant la fermeture de la fenêtre principale, la création
et l'ouverture d'un autre projet lorsque des changements sont présents, sauf
validation explicite de l'utilisateur. Options : **Enregistrer**, **Ne pas
enregistrer**, **Annuler**. L'annulation de la boîte de dialogue « Enregistrer
sous » ou une erreur d'écriture n'autorise jamais la fermeture. **Annuler**
est le choix par défaut.

Le détecteur travaille sur l'intégralité du dictionnaire projet sérialisé en
JSON : il repère aussi les changements dans les boîtes de dialogue d'alignement,
les associations PAGE et l'ordre des pages, sans modifier les sources externes.
La création d'un nouveau projet marque celui-ci comme non enregistré, même
si aucune ligne n'a été créée. En revanche, un projet initial vide, jamais
modifié, peut être fermé sans alerte. L'ouverture d'un projet existant ne le
marque pas modifié ; la migration en mémoire du format reste enregistrée seulement
sur demande. Le changement de langue recrée la fenêtre sans alerte et conserve
l'état des modifications.

Le bouton Enregistrer et la boîte de dialogue utilisent la même méthode et
rapportent le succès/échec ; aucun échec d'E/S n'est traité comme une sauvegarde
réussie.

## Recette manuelle PySide6 sous Windows

1. Lancer et fermer un projet initial vide : pas d'alerte.
2. Ajouter un témoin sans sauvegarder, fermer : trois options.
3. Choisir Annuler : fenêtre ouverte, données intactes.
4. Choisir Enregistrer et annuler le dialogue de fichier : fenêtre ouverte.
5. Choisir Enregistrer avec un chemin valide : fermeture et fichier créé.
6. Rouvrir un projet, modifier une association depuis le visualiseur, fermer : alerte.
7. Tester Nouveau et Ouvrir avec une modification en cours.
8. Changer de langue sur un projet modifié : aucune alerte ni perte de l'état « modifié ».
9. Vérifier qu'un échec d'enregistrement laisse la fenêtre ouverte.

Tests de logique indépendants de Qt : `tests/test_unsaved_changes.py`.
