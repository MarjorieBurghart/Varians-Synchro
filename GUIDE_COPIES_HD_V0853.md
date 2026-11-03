# Varians-Synchro V0.8.5.3 — Copies HD IIIF et traitement HTR externe

## 1. Conservation des téléchargements HD

Dans **2 · Associer les ressources → Gérer les images, leur ordre et les associations ALTO/PAGE…**, sélectionner les Canvas du Manifest et cliquer sur **« Télécharger les images IIIF sélectionnées en HD… »**. Choisir un dossier **vide**. Lorsque l’opération réussit, ce dossier contient des JPEG originaux et un `images.json` qui relie chaque nom de fichier au Canvas et à la requête IIIF. La V0.8.5.3 enregistre aussi ce dossier et les correspondances **dans le témoin du projet `.vsynch`**, avec des empreintes SHA-256 des fichiers. **Enregistrer le `.vsynch` après la fin du téléchargement**, sinon la nouvelle association de copie n’est pas conservée dans le projet.

**Téléchargements réalisés en V0.8.5.1/0.8.5.2** : cliquer sur **« Rattacher un lot HD déjà téléchargé… »** et choisir le `images.json` original dans le dossier contenant les JPEG. Cette opération n’entraîne **aucun nouveau téléchargement**. Elle refuse les fichiers manquants, les références de Canvas incompatibles et les sources IIIF modifiées. Plusieurs lots dans des dossiers distincts peuvent être enregistrés pour un même témoin. Après rattachement, enregistrer le `.vsynch`.

Si l’on déplace ultérieurement les images HD, il faut **rattacher de nouveau le dossier déplacé** à l’aide de son `images.json` : le chemin d’origine, enregistré en valeur absolue, ne sera plus résolu automatiquement.

## 2. Export d’un projet Varians avec copies locales

Dans **4 · Finaliser → Créer un projet Varians pré-renseigné…**, la V0.8.5.3 effectue une vérification **indépendante pour chaque témoin IIIF** :

1. Identifier exactement les Canvas dont `pages[].alto_binding` est renseigné (association explicite avec une segmentation ALTO ou PAGE). Aucun lien n’est deviné.
2. Chercher leurs copies dans l’ensemble des téléchargements HD enregistrés pour ce témoin.
3. Vérifier à nouveau l’existence et l’intégrité des JPEG, leur appartenance au Canvas et la conformité de l’URL IIIF originale.
4. **Seulement si toutes les pages segmentées sont couvertes**, activer `localCopy="true"` et `downloadScope="ocr"` sur ce témoin dans le `project.xml` produit, copier les JPEG vérifiés sous `iiif/local/<sigle>/`, créer `index.json` au format `varians-iiif-local-1`, et enregistrer un cache local du Manifest à partir des métadonnées déjà disponibles.

La correspondance est faite par **URI Canvas et URL du service d’image**. Ni l’ordre alphabétique, ni le numéro de ligne, ni l’ordre de téléchargement ne sont considérés comme une preuve.

Lorsque **une seule image segmentée manque**, le témoin **reste en mode IIIF habituel**, sans copies locales exportées pour ce témoin. Une autre image téléchargée mais non segmentée ne compense pas le manque. Les Canvas manquants figurent dans le rapport `RAPPORT_EXPORT_VARIANS.txt`, dans le projet livré. Cela ne bloque pas l’export des correspondances JSON ni les copies complètes des *autres* témoins.

Les fichiers sources ALTO/PAGE restent référencés à leur emplacement d’origine (comme dans les versions précédentes) ; le présent changement ne les intègre pas au dossier. Les copies HD ne transforment pas l’image du Canvas en une deuxième page. Les URL IIIF et identifiants Canvas restent inchangés, assurant les associations déjà établies.

**Compatibilité** : le mécanisme local (`index.json`, `localCopy`) a été vérifié avec le code de lecture IIIF de référence **Varians V0.8.5.6**. Vérifier l’ouverture graphique dans la version plus récente effectivement utilisée.

## 3. Les deux boutons HTR

Ils figurent désormais dans une rubrique distincte **« Traitement HTR externe (facultatif) »**.

- **Exporter pour HTR** crée un ZIP des Canvas sélectionnés et un fichier `pages.json`. On peut donner ce ZIP à un logiciel externe de HTR pour produire des fichiers XML ALTO ou PAGE.
- **Réimporter HTR** demande ce `pages.json` et le dossier contenant les XML produits par l’outil externe. Varians-Synchro tente de les réassocier aux Canvas par les noms des fichiers de l’export. Les situations sans correspondance, ambiguës ou déjà associées sont signalées ou ignorées ; aucun lien existant n’est écrasé.

Ces actions **ne servent pas** à créer des copies HD locales du manuscrit pour Varians. Lorsque les fichiers ALTO/PAGE existent déjà, cette étape HTR n’est pas nécessaire. Le ZIP HTR et son `pages.json` ne doivent pas être confondus avec le dossier de téléchargement HD et son **`images.json`**.

## 4. Sécurité et limites

- L’association HD est facultative et rétrocompatible avec les anciens projets `.vsynch`.
- Les originaux téléchargés ne sont ni modifiés ni déplacés au moment de l’export.
- L’export Varians demeure préparé dans un dossier temporaire puis publié en une opération, seulement vers un répertoire vide.
- Une copie HD corrompue ou ayant changé de source n’est pas utilisée. Une image supplémentaire non segmentée et devenue indisponible n’empêche pas l’utilisation des images segmentées intègres.
- Le téléchargement reste soumis à la disponibilité du service IIIF, aux limites de taille et aux conditions d’utilisation de l’institution source.
- Il n’existe **aucune conversion automatique d’édition TEI**, aucune transformation des alignements intertémoins, ni écrasement des fichiers ALTO/PAGE.

## 5. Tests suggérés sur Windows

1. Télécharger deux ou trois Canvas segmentés depuis la fenêtre de pages, puis enregistrer le `.vsynch` ; fermer et rouvrir le projet pour confirmer que ces images sont répertoriées.
2. Ouvrir un autre lot HD antérieur au moyen de `images.json` sans téléchargement réseau ; enregistrer puis rouvrir le `.vsynch`.
3. Effectuer un export Varians lorsque **toutes** les pages associées à des ALTO/PAGE ont une copie HD enregistrée ; ouvrir `project.xml` dans Varians et vérifier l’usage de la copie locale.
4. Retirer temporairement l’un des JPEG requis, puis refaire l’export vers un nouveau dossier vide : il doit rester en mode IIIF distant pour ce témoin, et le rapport doit identifier le Canvas manquant.
5. Vérifier la fenêtre « Traitement HTR externe » et ses infobulles.
