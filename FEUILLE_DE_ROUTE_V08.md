> **V0.8.5.1 : ergonomie et export de projet Varians de référence ajoutés.** Recette graphique et compatibilité avec le Varians actuel à confirmer. Voir `TESTS_V0851.md`.

> **V0.8.5 : stabilisation technique réalisée, validation graphique finale en attente.**

> **V0.8.4.2 livrée :** ajustement ergonomique des sélections et des repères dans la synchronisation visuelle. Moteur V0.7.4 préservé.

# Feuille de route — Varians-Synchro V0.8

**V0.8.0 + V0.8.1 : développées ensemble et livrées en V0.8.1.** Gestion centralisée des témoins, choix du fichier à la création, association groupée des ressources image/PAGE/ALTO. Le moteur V0.7.4 n'a pas été modifié.

**V0.8.2 : développée.** Extraction TEI robuste des `<lb edRef>` et résolution correcte des apparats critiques par témoin, sans contamination des lectures.

**V0.8.3 : développée.** Définition du périmètre physique, correspondances TEI ↔ lignes PAGE/ALTO, contrôle des effectifs, prévisualisation/validation et sauvegarde des liaisons éditoriales.

**V0.8.4 et V0.8.4.1 : développées.** Recadrage local/IIIF polygonal, contrôle TEI par sélection avec **un seul aperçu** (première ligne à l’ouverture, choix de la fin ou d’une ligne intermédiaire), texte TEI lié à la place de la HTR dans la synchronisation entre témoins, recherche et navigation vers les lignes physiques.

**V0.8.5 : candidate livrée pour recette finale.** Sauvegarde récupérable, tests de migrations, nettoyage de l’API TXT désuète, audit automatique des catalogues, 294 tests non graphiques, deux projets réels et JSON vérifiés sans régression. **Restent ouverts** : essais graphiques Qt sur Windows/macOS/Linux et essai dans la toute dernière version de Varians. Voir `RAPPORT_RECETTE_V085.md`.

Ne pas confondre le **pivot physique de correspondance** et une **édition TEI**. Les deux sont facultativement associés, mais une édition TEI seule ne constitue pas une segmentation PAGE/ALTO exploitable.
