# Recette Varians-Synchro V0.8.5.2

Exécuter depuis le dossier du logiciel :

```bash
python -m pytest -q
```

Résultat dans l’environnement de construction : **306 tests réussis, 13 ignorés (PySide6 absent)**.

## Recette manuelle sur Windows avec PySide6

1. Ouvrir un projet `.vsynch` avec un témoin IIIF.
2. Dans « Associer les ressources », ouvrir la gestion des images ; sélectionner 1 ou 2 Canvas compatibles Image API.
3. Choisir « Télécharger les images IIIF sélectionnées en HD… » et un dossier vide.
4. Attendre 100 % : le message doit indiquer **« Téléchargement terminé »**, le nombre d’images et le dossier, jamais « annulé ».
5. Vérifier les fichiers `.jpg` et `images.json` dans le dossier.
6. Répéter en cliquant explicitement sur « Annuler » pendant un téléchargement long : le message doit indiquer l’annulation et le dossier choisi doit rester vide.
7. Simuler un téléchargement erroné (réponse non JPEG ou indisponibilité du service) : un avertissement doit présenter l’erreur, sans la qualifier d’annulation.

Le test Qt ciblé peut être exécuté ainsi :

```bash
python -m pytest -q tests/test_hd_completion_0852.py
```

Les deux tests Qt de ce fichier requièrent PySide6 ; le test de structure s’exécute également sans Qt. Les tests de réseau réel restent à confirmer depuis un poste disposant de l’accès au serveur IIIF.
