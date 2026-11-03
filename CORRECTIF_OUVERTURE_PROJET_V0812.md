# Correctif V0.8.1.2 — Projet vide à la réouverture

## Cause technique

Dans `varians_synchro/guided_ui.py`, `GuidedWindow.open` contenait :

```python
if not self._confirm_save_or_discard():
    return
    self.project = incoming  # inatteignable
self.path = path
```

`new` comportait la même erreur : `self.project = new_data` était placé après un `return` dans le bloc d'exception de `save_project`.

L'interface continuait d'afficher le projet précédent, souvent vide, malgré un chemin et un état « enregistré » correspondant au fichier choisi. Une sauvegarde ultérieure pouvait écraser le fichier du projet chargé avec le contenu d'un autre projet.

## Correction

- Affecter `self.project = incoming` après le chargement réussi et l'accord de remplacement, **avant** de mettre à jour le chemin et de réinitialiser `ProjectChangeTracker`.
- Affecter `self.project = new_data` après la création du fichier, hors du bloc `except`.
- En cas d'annulation ou d'exception, ne pas modifier le document courant ni son chemin.

## Précaution et récupération

**Ne pas enregistrer un projet qui semble vide dans V0.8.1/0.8.1.1 après « Ouvrir ».** Fermer en choisissant « Ne pas enregistrer » si nécessaire, après avoir fait une copie du fichier d'origine, puis utiliser V0.8.1.2.

Un `.vsynch` JSON qui contient encore des témoins n'a pas besoin d'être réparé ni converti. Le chargement corrigé l'utilise tel quel. Si le fichier a déjà été écrasé, il faut récupérer une sauvegarde extérieure : le correctif ne peut pas recréer des données effacées.

## Vérifications

- Six tests non graphiques spécifiques exécutent le code réel des méthodes `open` et `new` sans nécessiter PySide6.
- Deux tests Qt optionnels vérifient le tableau de témoins visible après ouverture / création sur une machine avec PySide6.
- Contrôles de non-régression : formats `.vsynch`, export JSON et synchronisation inchangés.
