# Varians-Synchro V0.7.4 — Contrôle global de cohérence

## Objectif

Le contrôle global est **en lecture seule** : il ne modifie ni `.vsynch`, ni ALTO/PAGE, ni les images, ni les liens. Il aide à préparer l’export des JSON vers Varians, notamment lorsqu’un projet contient trois témoins ou davantage.

Dans **4 · Progression → Contrôler la cohérence du projet…**, le rapport est affiché dans la zone « Progression », avec un décompte des erreurs et avertissements. Les libellés de la nouvelle commande et les messages sont disponibles dans les catalogues XML français et anglais.

### Contrôles réalisés

- Validité structurelle du projet et unicité des identifiants de témoins.
- Inventaire des lignes physiques, actives et ignorées, avec nombre de pages réellement associées à des XML ALTO/PAGE.
- Validité des réglages d'ordre de lecture et des séquences entre folios/colonnes.
- Doublons de sessions de paires, de liens, de références à une même ligne ; liens périmés ou touchant une ligne ignorée.
- Cohérence des groupes de correspondance et des absences confirmées (exactement un côté de la paire).
- Signalement des repères contradictoires **sans correction automatique**.
- Évaluation des `base_keys` produites par les deux politiques d’exportation, à partir d’un pivot choisi.
- Optionnel : disponibilité des fichiers XML et images locaux sur le poste courant (les absences sont des avertissements, pas une raison de détruire les snapshots conservés dans le projet).

**Important :** une absence confirmée dans Mu–F ne supprime aucune correspondance de Mu–A. Aucun alignement Mu–A n’est déduit transitivement de Mu–F et F–A.

### Signification des résultats

- **Erreur** : contradiction structurelle nécessitant un contrôle avant de considérer les liens comme fiables (référence physique introuvable, doublon, groupe invalide…).
- **Avertissement** : élément à examiner ; les exportations sûres peuvent rester possibles (repères croisés, fichiers externes momentanément introuvables, témoin secondaire ne possédant que des propositions incertaines).
- **0 erreur** n’est **pas une certification philologique** : le contrôle ne sait pas juger si les deux repères contiennent vraiment le même passage.

## Diagnostic sans interface Qt

Depuis le dossier contenant `run.py` :

```bash
python audit_vsynch.py /chemin/projet.vsynch --base Mu --output rapport_recette.json
```

Windows, par exemple :

```powershell
python audit_vsynch.py "C:\Travail\Projet\edition.vsynch" --base Mu --output "C:\Travail\Projet\audit.json"
```

Options : `--check-paths` pour la présence des sources locales ; `--strict` pour retourner un code d’échec en présence d’avertissements (utile pour une recette automatisée). Le rapport JSON contient les codes et comptages, **pas le texte manuscrit**. Le projet original n'est jamais réécrit.

## Exports transactionnels

Les deux dossiers `validated/` et `working/` sont générés dans une arborescence temporaire à côté de la destination, puis les `base_keys` sont contrôlées contre les numéros physiques présents dans le JSON pivot. L’opération ne publie les fichiers que si tout est réussi ; un dossier de destination déjà non vide est refusé.

Le fichier `rapport_export.json` contient maintenant la section `integrity` pour les deux politiques, en plus des compteurs des `base_keys` et des avertissements existants. Les schémas JSON **de Mu/F/A** restent inchangés par rapport à la V0.7.3.

## Limites

- Le logiciel ne remplace pas une validation éditoriale des correspondances.
- Un projet historique peut comporter des repères croisés : ils sont signalés et isolés, jamais déplacés sans intervention humaine.
- Les tests Qt et le parcours réel de chargement IIIF nécessitent une installation avec PySide6 et un accès réseau. Le contrôle n’interroge aucun serveur distant.
