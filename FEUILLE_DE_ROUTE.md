## V0.6.15 — Export direct vers Varians 0.8.5.2

- Bouton et CLI produisant les fichiers `tei-manuscript-alignment` pour chaque témoin, en distinguant validés / incertains.
- Prochain chantier prioritaire : relier les lignes physiques du témoin de base choisi aux `<lb/>` d'une **vraie** édition TEI, puis réécrire/valider les `base_keys` pour synchroniser texte et images dans Varians.
- Compatibilité à maintenir avec les scripts de lecture Varians 0.8.5.2 ou ultérieurs.

## V0.6.9 — Correctif du recalcul sur projets déjà synchronisés

Le moteur peut désormais recalculer les suggestions automatiques incertaines à l’intérieur d’une colonne déjà partiellement alignée, sans détruire les ancrages manuels ni les liens validés. Prévisualisation et confirmation avant application atomique.

---

## V0.6.6 — Implémenté

- Navigation réciproque instantanée par clic sur les cadres ALTO liés.
- Mise en évidence temporaire non destructive des correspondances, y compris 1↔n / n↔m, et passage automatique au folio concerné.
- Surlignage compatible avec les filtres de la V0.6.5, français/anglais.
- Tests métier complétés ; validation graphique native Windows/Spyder à effectuer.

> **V0.6.5 livrée :** filtres visuels des cadres ALTO (tous / non synchronisés / automatiques à vérifier) et rectification du statut visuel des interpolations géométriques. La suite de la feuille de route reste inchangée.

# Feuille de route — Varians-Synchro

## Invariants scientifiques et techniques

- Zéro obligation de TEI ni de texte TXT ; l'alignement ALTO–ALTO est un workflow autonome.
- Plusieurs témoins (sans plafond codé), images locales et/ou Manifests IIIF, ALTO géométriques avec HTR facultative.
- Pivot **technique**, éventuellement provisoire, distinct du témoin de base **éditorial**.
- Granularité des correspondances : **lignes physiques**, avec associations 1:n, n:1, n:m, absences et passages déplacés à terme.
- Correspondances proposées, incertaines et validées distinctes ; aucun calcul automatique ne modifie une validation scientifique.
- Sources originales inchangées ; sauvegarde du projet de travail distincte de l'exportation des JSON de Varians.

## Jalons

| Version | Livrable | Statut |
|---|---|---|
| V0.1–0.3 | Modèle projet, imports, images IIIF/locales, alignement manuel TEI | Hérité |
| V0.4–0.5 | Moteur TEI–HTR et modes de contrôle rapide/rigoureux | Hérité, perfectible |
| **V0.6** | **Accueil guidé, projet sans TEI, alignements ALTO–ALTO persistants, premier HTR–HTR, vérification pages/ALTO** | **Développé : tests noyau OK ; GUI Windows à vérifier** |
| V0.6.1 | Amélioration ergonomique approfondie : vraies vues côte à côte, association automatique contrôlable, réouverture de fichiers déplacés, projets portables | À développer |
| V0.6.2 | Texte pivot ancien TXT/MD/DOCX réellement exploité : segmentation et alignement pivot–HTR, sans statut éditorial imposé | À développer |
| V0.7 | HTR–HTR robuste sur gros corpus, traitement de nombreux témoins, pivot interchangeable, zones/ancrages, progression et annulation | À développer |
| V0.7.1 | Alignement visuel assisté sans HTR ; interpolation explicitement hypothétique ; navigation multitémoin | À développer |
| V0.8 | Omissions, additions, transpositions, transferts des alignements préparatoires vers TEI sans perte silencieuse | À développer |
| V0.9 | Tests sur corpus réels, contrôle des JSON dans Varians, résilience réseau/IIIF, performances et migration de projets | À développer |
| V1.0 | Version stable diffusée, installateur Windows, aide et documentation complète | À développer |

## Passerelle IIIF sans ALTO — retenue depuis V0.2

L'utilisateur peut sélectionner les pages pertinentes d'un Manifest IIIF, les exporter dans un ZIP avec `pages.json`, les traiter dans un service HTR externe tel que PERO et réimporter les ALTO. **Varians-Synchro ne devient pas un moteur de segmentation ou de HTR.**

## Critères immédiats de recette sur Windows

1. Ouvrir un ancien projet `.vsynch` V0.5.2 et retrouver tous ses témoins, ses Manifests, ses ALTO et ses sessions TEI.
2. Sans TEI, ouvrir deux témoins avec ALTO (local ou IIIF), associer des lignes, fermer et rouvrir le projet : les liens persistent.
3. Sans TEI, avec deux HTR exploitables, produire des propositions HTR–HTR et vérifier qu'elles restent proposées ou incertaines, jamais validées automatiquement.
4. Sans HTR, sélectionner deux lignes via ALTO et vérifier qu'une correspondance manuelle est possible.
5. Ajouter ultérieurement une TEI ou un pivot TXT sans perdre les liens physiques validés.
6. Après changement d'une ligne ALTO, obtenir une alerte de correspondance à vérifier, sans suppression de l'historique.


## V0.6.1 — Retours du premier essai réel (réalisé)

- Deux images côte à côte pour l'alignement manuel, rectangles ALTO interactifs, zoom et navigation à haute résolution.
- HTR facultative ; vue textuelle secondaire.
- Tri documentaire des pages locales (folio r/v), ordre de Canvas IIIF conservé, anciens projets pris en charge.
- Sélection multi-lignes persistante d'une page à l'autre.

## Priorités suivantes

1. **V0.6.2** — Validation visuelle de l'interface sur Windows/Spyder et perfectionnement ergonomique à partir des retours ; possibilités d'enregistrer automatiquement les modifications, raccourcis et traitement des transformations géométriques ALTO complexes.
2. **V0.7** — Alignement HTR–HTR renforcé par segments et ancrages ; diagnostic par témoin, traitement par lots.
3. **V0.7.1** — Alignement visuel assisté sans HTR : ancrages et interpolation explicitement incertaine.
4. **V0.8** — Texte pivot TXT réellement exploitable, transfert ultérieur vers TEI et transpositions complexes.

## Mise à jour V0.6.2 (10 octobre 2026)

**Réalisé dans le noyau** : interpolation géométrique conservatrice entre les premières/dernières lignes de chaque colonne identifiées par des ancrages validés, sans dépendance au contenu HTR ; prévisualisation des propositions incertaines ; protection des alignements manuels. **Interface** : boutons principaux déplacés en haut ; taille ajustée à l'écran ; menu pour les actions secondaires ; première internationalisation française/anglaise et choix de langue persistant.

**Reste à faire** : validation native de l'interface graphique sur Windows et de différentes résolutions ; raffinement du modèle de lecture multi-colonnes ; traitement des passages déplacés et des cas de discontinuité ; améliorations ergonomiques, intégration complète du texte pivot TXT et traduction exhaustive des messages historiques. L'alignement géométrique n'est pas une preuve de correspondance textuelle : revue éditoriale obligatoire.

## Mise à jour V0.6.3 — visibilité du panneau HTR

La visibilité de la liste HTR est désormais réellement facultative dans le visualiseur d’alignement. Lorsqu’elle est masquée, l’image dispose de la hauteur libérée ; lorsqu’elle est affichée, la hauteur devient réglable par séparateur. Ce correctif ergonomique conserve l’interface FR/EN et les fichiers de projet.


## Correctif livré V0.6.11

Marquage persistant et réversible des lignes ALTO hors périmètre au niveau du témoin, exclusions prises en compte par les propositions et les statistiques, nouvelle palette contrastée FR/EN. Pour une version future : outils d'exclusion par plages de folios/colonnes avec ordre de lecture explicitement vérifié, et coordination approfondie des sessions TEI héritées.

## Ajout livré en V0.6.13

- [x] Importation native de PAGE-XML, avec contours polygonaux, HTR de ligne et ordre régional quand déclaré.
- [x] Coexistence PAGE/ALTO dans un projet et entre deux témoins d'une même session.
- [x] Sélection de la source active par page et rapprochement du PAGE par `imageFilename`.
- [ ] Fusion contrôlée PAGE + ALTO d'une même page lorsque les lignes diffèrent ; non requise pour le parcours PAGE autonome.
