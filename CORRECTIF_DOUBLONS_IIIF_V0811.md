# Varians-Synchro V0.8.1.1 — Détection des associations ALTO/PAGE en double

## Situation corrigée

Avec un Manifest IIIF de plusieurs centaines de Canvas et seulement quelques ALTO/PAGE à associer, l'interface montrait un avertissement générique si un même fichier XML était sélectionné pour deux pages (parfois très éloignées à l'écran). Une liste déroulante pouvait également changer de valeur lors d'un défilement involontaire à la molette.

## Nouveau comportement

- **Bilan en direct** du nombre de pages avec une association choisie et des éventuels doublons.
- **Repérage des doublons** par fichier XML, folio et page du Manifest, y compris lorsque les lignes concernées sont hors écran.
- **Surlignage rouge clair** des lignes en conflit et déplacement de la liste vers le premier conflit lors d'une tentative de validation.
- **Filtre facultatif** « Afficher uniquement les associations sélectionnées », utile pour travailler sur cinq folios dans un Manifest de 469 Canvas.
- **Libellé « Manuelle »** après une association sélectionnée manuellement, à la place de l'ancien et trompeur « Non résolue ».
- **Protection contre la molette** lorsqu'une liste déroulante n'est pas ouverte : la molette sert à parcourir les lignes plutôt qu'à modifier silencieusement le XML choisi.
- **Validation atomique maintenue** : en cas de conflit, aucune association n'est enregistrée.

## Utilisation

1. Ouvrir la fiche du témoin et « Associer automatiquement les images et les ALTO/PAGE ».
2. Associer manuellement les seuls Canvas utiles ; les autres restent « Ne pas associer ».
3. Activer le filtre des associations sélectionnées pour revoir rapidement le lot.
4. S'il existe un doublon, le corriger sur l'une des lignes mises en évidence avant de cliquer sur « Appliquer les associations ».
5. Enregistrer le témoin, puis le projet `.vsynch`.

**Remarque :** les propositions par rang restent désactivées sur les grands Manifests IIIF, car cinq XML ne doivent pas être arbitrairement associés à cinq Canvas parmi plusieurs centaines.

## Portée et sécurité

Aucun changement du moteur V0.7.4, des IDs des lignes, du modèle du projet, des JSON pour Varians, ni du comportement des imports PAGE/ALTO. Les fichiers sources restent intacts.

## Vérifications

250 tests automatisés réussis, 8 tests graphiques ignorés faute de PySide6 dans l'environnement de construction. Test spécifique d'un Manifest simulé de 469 Canvas : un XML sélectionné pour deux folios éloignés est signalé et le projet reste strictement inchangé après le refus.

Le rendu et la gestion de la molette doivent encore être confirmés sur Windows/PySide6.
