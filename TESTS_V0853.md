# Recette V0.8.5.3

Commande :

```bash
python -m pytest -q
```

- Les suites héritées de V0.8.5.2 sont conservées.
- Cas nouveaux : plusieurs lots HD couvrant le périmètre éditorial, refus d'un lot incomplet, altération d'un JPEG, altération d'URL IIIF, récupération d'un téléchargement préexistant, absence de segmentation, image supplémentaire indisponible, validation de la structure du registre `.vsynch`.
- Pas de trafic réseau nécessaire aux tests automatisés (réponses JPEG simulées).
- Comparaison manuelle en Python contre le lecteur de cache de référence Varians 0.8.5.6 : les JPEG locaux sont retrouvés par Canvas et URL, tandis que les Canvas non copiés restent distants.
- Essais à réaliser sur le poste utilisateur : téléchargement réel, sauvegarde/réouverture du registre, inclusion des copies, lecture locale dans sa version installée de Varians et manipulation de l'interface Qt.

**Bilan dans cet environnement : 314 tests réussis, 13 tests Qt ignorés**, tests graphiques Windows restant à réaliser. Les quatre exports validés/de travail des projets réels `projetTest.vsynch` et `test081.vsynch` sont identiques (empreintes SHA-256 du JSON canonique) à ceux de la V0.8.5.2. Les tests Qt éventuellement ignorés ne doivent pas être présentés comme des validations graphiques réalisées.
