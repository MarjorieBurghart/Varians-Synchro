# Guide — Varians-Synchro V0.8.5.1

## 1. Ajout des témoins

Dans « 1 · Ajout des témoins », cliquer sur « Ajouter un témoin… » puis renseigner son sigle et sa description. Les ressources peuvent être ajoutées plus tard. Le bouton « Supprimer » retire de la **liste d’attente** la ressource ajoutée qui est sélectionnée ; il ne détruit pas un fichier ni une association ancienne.

## 2. Associer les ressources

Les quatre opérations sont désormais placées sous le titre, **au-dessus du tableau de synthèse** :

1. Gérer les images et les associations ALTO/PAGE : aperçu, tri des folios, appariement individuel ou groupé.
2. Proposer des associations : vérification nominative, puis par ordre naturel dans les seuls cas cohérents.
3. Définir les lignes ignorées : délimitation du passage éditorial dans le manuscrit.
4. Lier la TEI aux lignes : comparaison des `<lb edRef="#SIGLE"/>` et des lignes physiques actives, contrôle visuel avant confirmation.

### Télécharger une sélection d’images IIIF en HD

Dans « Gérer les images… », sélectionner les Canvas voulus (Ctrl ou Maj autorisés), puis cliquer sur **« Télécharger les images IIIF sélectionnées en HD… »**.

- Choisir un **dossier vide**. Seuls les Canvas sélectionnés sont demandés aux services IIIF Image API ; aucune commande de téléchargement intégral du Manifest n’est déclenchée.
- L’outil utilise la taille native demandée par IIIF v2 (`full/full`) et v3 (`full/max`) ; il ne fabrique pas une version HD à partir d’une vignette.
- Chaque fichier JPEG est accompagné d’une entrée dans `images.json` identifiant le Canvas et l’URL de téléchargement.
- Un téléchargement interrompu ou en erreur ne publie **aucun dossier partiel**.
- La disponibilité et les restrictions de téléchargement restent fixées par le serveur IIIF ; un refus du serveur, une image trop grande ou l’absence de service Image API sont signalés. Le logiciel ne contourne pas ces restrictions.

## 3. Aligner les témoins

Le pivot relie les témoins secondaires : une comparaison indirecte F ↔ A devient possible par Mu lorsque F et A sont alignés chacun sur Mu. Cela ne constitue pas automatiquement une nouvelle session de correspondances directes F ↔ A : aucune liaison n’est inventée.

## 4. Finaliser

### Actualiser le bilan

Le tableau montre le nombre d’images et de lignes actives par témoin ainsi que les **sessions d’alignement entre témoins**. Les anciennes sessions TEI sont signalées uniquement lorsqu’elles existent et sont conservées pour compatibilité.

### Contrôler la cohérence du projet…

Il s’agit d’une **vérification sans modification**. Elle examine le projet, notamment les identifiants de lignes physiques, les lignes ignorées, les associations obsolètes, les groupes d’alignement contradictoires, les liaisons TEI périmées, les fichiers externes locaux et les références du pivot utilisables dans l’export. Les avertissements exigent une vérification humaine ; aucun recalcul ni nettoyage automatique n’est effectué.

### Exporter les JSON pour Varians

Cette commande produit deux ensembles :

- `validated/` : seules les correspondances explicitement validées.
- `working/` : mêmes correspondances plus les propositions automatiques encore incertaines.

Ces fichiers ne créent **pas** un projet complet.

### Créer un projet Varians pré-renseigné…

Cette commande prépare un dossier de projet contenant :

```
project.xml
xml/edition.xml
alignments/Mu.json
alignments/F.json
...
rendering/tei.css
rendering/custom-elements.xml
RAPPORT_EXPORT_VARIANS.txt
```

Il faut impérativement avoir associé une **unique édition TEI au témoin pivot**, et lui avoir lié une segmentation physique exploitable. L’assistant vous demande un dossier vide et une confirmation. Les correspondances exportées sont **validées uniquement** par défaut.

**Attention aux chemins :** les images locales et fichiers ALTO/PAGE restent à leur emplacement d’origine ; leur déplacement rendra les chemins inscrits dans `project.xml` invalides. Les images IIIF restent référencées par leur Manifest. Les fichiers XML TEI du pivot sont copiés à l’identique.

La structure a été vérifiée contre le parseur du projet de Varians V0.8.5.6 disponible dans l’environnement de test. La **version actuelle** de Varians peut faire évoluer ce contrat ; tester l’ouverture de `project.xml` et la concordance effective des lignes TEI avant toute exploitation scientifique. Cet export ne remplace pas les validations philologiques et ne crée pas de liaisons transversales fictives.

## Vérifications Windows à réaliser

Ouvrir d’abord une copie du projet `.vsynch`. Tester : changement de langue, accès aux quatre étapes, infobulles, sélection de 2 ou 3 Canvas IIIF et téléchargement HD, annulation d’un téléchargement, audit « Finaliser », export JSON puis création/ouverture de `project.xml` dans Varians. Les tests Qt et la disponibilité des serveurs IIIF n’ont pas pu être validés dans l’environnement Python de compilation.


## Correctif V0.8.5.2 : message final du téléchargement HD

Après un téléchargement effectivement réussi, le message indique désormais « Téléchargement terminé » et le nombre d’images enregistrées. Une annulation est annoncée uniquement si le moteur interrompt réellement le téléchargement. Voir `CHANGELOG_V0852.md`.
