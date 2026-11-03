# Varians-Synchro V0.7.0 — J1 : flux de lecture continu

**Statut : première étape fonctionnelle de la refonte V0.7 ; le nouveau moteur de répartition cumulative est prévu pour la V0.7.1.**

## Pourquoi ce jalon ?

Les anciens modules `interpolation.py` et `residual_alignment.py` s'appuient sur la géométrie et limitent les intervalles à certaines paires de pages. Ils restent disponibles dans V0.7.0 pour ne pas rompre les travaux en cours, mais **ne sont pas encore remplacés**.

Le nouveau module `varians_synchro/reading_stream.py` pose le socle du remplacement :

1. Il parcourt les pages du témoin **dans l'ordre de lecture** et y concatène les lignes des régions/colonnes successives. Les limites de page ne réinitialisent jamais les indices globaux.
2. Les lignes marquées « ignorées » sont absentes du **flux actif**, mais leurs identifiants restent présents dans l'inventaire physique et dans la vue de contrôle.
3. Chaque ligne du flux conserve : témoin, folio, rang physique original, UID stable, texte HTR s'il existe, rectangle et éventuellement polygone, ligne de base PAGE, région et position dans le flux.
4. `anchor_intervals()` reconnaît les **groupes validés** 1↔1, 1↔n ou n↔m et extrait toutes les lignes entre deux repères, même sur plusieurs pages ou colonnes. Il affiche les conflits d'ordre ; il ne crée aucune nouvelle association.
5. La HTR et la géométrie ne décident pas encore des correspondances : la pondération par quantité de texte relève du jalon **V0.7.1**.

## Interface : contrôler et corriger l'ordre de lecture

Ouvrir un projet puis :

**3 · Synchronisation → Synchronisation visuelle entre témoins → Autres opérations → Ordre de lecture et intervalles…**

Dans cette nouvelle fenêtre :

- choisir Mu, F ou l'un des deux témoins de la session ;
- vérifier les **pages avec transcription XML**, **régions/colonnes** et **lignes** ;
- utiliser « Monter » et « Descendre » pour corriger leur ordre ;
- cliquer « Voir les intervalles entre repères » pour inspecter les groupes validés et les lignes situées entre eux ;
- fermer, puis **enregistrer le projet `.vsynch`** comme à l'habitude.

Une correction d'ordre **ne change ni le numéro physique, ni l'identifiant UID d'une ligne, ni les liens existants**. Les régions absentes des anciens instantanés ALTO/PAGE apparaissent comme une seule région `__unclassified__` : dans ce cas les lignes restent modifiables individuellement. Les nouvelles importations XML conservent l'identifiant de `TextBlock` (ALTO) ou de `TextRegion` (PAGE) ; PAGE conserve aussi `ReadingOrder` et les lignes de base.

Le réglage d'ordre des pages s'applique au témoin entier ; la liste de contrôle masque simplement les Canvas sans transcription, qui peuvent être très nombreux. Les modifications des régions et des lignes sont enregistrées dans les données de page, jamais dans les XML externes.

**Important :** si un ordre de lignes personnalisé devient périmé après un changement de segmentation, le logiciel doit le signaler ; aucun reclassement approximatif n'est appliqué automatiquement.

## Diagnostic sans interface graphique

Le script fourni n'exige pas PySide6 :

```bash
python diagnostic_flux_lecture.py "chemin/vers/projet.vsynch" --pair Mu F --json diagnostic.json
```

Il lit seulement le `.vsynch` et produit le nombre de lignes actives, les repères validés, les intervalles et les contradictions localisées. Aucun HTR complet n'est copié dans le rapport et le fichier source n'est pas modifié.

## Résultat observé sur le projet test réel Mu–F

- **Mu : 211** lignes actives ; **F : 241** ; **A : 97**.
- **Mu–F : 60** groupes validés utilisables comme repères ; **58** intervalles non contradictoires entre repères voisins ; **une contradiction d'ordre**.
- Contradiction localisée : **Mu 4r:25 ↔ F 16r:32**, puis **Mu 4r:26 ↔ F 16r:31**. Ces associations doivent être examinées philologiquement ; elles ne sont pas automatiquement modifiées.
- Les deux variantes d'export Varians (`validated` et `working`) ont donné des résultats **strictement identiques** aux exports produits par V0.6.16 sur le même `.vsynch` (comparaison de l'empreinte SHA-256 des représentations JSON normalisées).

**Aucune conclusion philologique ne doit être tirée d'une simple contradiction de numéros ; elle peut correspondre à une transposition réelle, à une erreur d'ordre local ou à une erreur d'association.**

## Sécurité et compatibilité

- Schéma `.vsynch` **version 1 inchangée** ; seules trois clés optionnelles de page sont ajoutées : `reading_order`, `reading_region_order`, `reading_line_order`.
- Ne pas remplacer silencieusement les liens validés, ignorer une anomalie de repères ou reconstituer artificiellement une absence.
- Images IIIF/locales et transferts JSON vers Varians inchangés ; aucun téléchargement réseau nécessaire pour les tests de lecture.
- Anciennes commandes d'interpolation temporairement conservées pour comparaison ; elles ne savent **toujours pas** synchroniser un passage complet multi-folios. Utiliser la nouvelle fenêtre pour vérifier le flux en attendant V0.7.1.
- Internationalisation : toutes les chaînes de cette fenêtre sont définies dans `i18n/fr.xml` et `i18n/en.xml`.

## Prochain jalon V0.7.1

Un seul moteur de propositions : longueurs HTR si exploitables, longueur graphique calibrée par région sinon, puis repli ordinal. Progressions cumulées normalisées par intervalle de repères, propositions monotones 1↔n, vérifiables et jamais validées automatiquement. Les tests multi-folios de V0.7.0 serviront de conditions d'entrée.

## Vérification automatisée

Commande : `python -m pytest -q tests`.

Les tests Qt ne sont pas exécutés dans l'environnement de fabrication, faute de PySide6. L'interface doit être vérifiée sur Windows/macOS/Linux dans un environnement PySide6 installé.
