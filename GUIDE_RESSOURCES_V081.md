# Varians-Synchro V0.8.1 — Projet, témoins et associations par lots

## Nouveautés V0.8.0 + V0.8.1

**La base du moteur reste la V0.7.4.** La synchronisation entre deux repères (flux continu de lignes, poids de HTR/longueur graphique, validations humaines), les projets `.vsynch` et l'export `validated/` / `working/` vers Varians ne sont pas recalculés.

### Créer le projet

1. Choisir **Nouveau projet** et saisir un titre.
2. Choisir immédiatement **le chemin du fichier `.vsynch`**. Le fichier est effectivement créé et sauvegardé à cet emplacement.
3. Annuler l'une des deux fenêtres laisse le projet courant intact. Des modifications non enregistrées déclenchent toujours l'avertissement Enregistrer / Ne pas enregistrer / Annuler.

### Ajouter ou modifier un témoin

Dans **1 · Projet et témoins**, choisir **Ajouter un témoin…** et remplir le sigle (obligatoire), éventuellement le nom, et cocher « Définir comme pivot » si souhaité. Le premier témoin devient pivot par défaut ; celui-ci peut être changé dans une fiche de témoin ultérieure. Vous pouvez alors, dans la même fiche :

- sélectionner un groupe d'**images locales** (tri initial selon leur nom naturel : 2 avant 10) ;
- saisir l'adresse d'un **Manifest IIIF** ; si le serveur est momentanément inaccessible, la référence est conservée avec le statut « unavailable » ;
- sélectionner un lot de **fichiers ALTO ou PAGE-XML**, détectés par leur contenu ;
- référencer une ou plusieurs **éditions TEI XML**.

Une TEI peut être associée à un témoin **en attente de rattachement**. Cette version ne prétend pas avoir aligné ses `<lb/>` avec les lignes physiques : ce chantier est réservé aux V0.8.2–V0.8.3. Pour le réaliser, il faudra également disposer d'ALTO/PAGE et sélectionner le périmètre éditorial sur les images. Les anciens extraits TEI déjà enregistrés dans un `.vsynch` ne sont pas supprimés.

Cliquer sur le nom d'un témoin **ou l'une de ses ressources** dans l'inventaire rouvre la même fiche. Par sécurité, le sigle d'un témoin déjà enregistré est en lecture seule et ses ressources déjà associées ne peuvent pas être retirées de cette fenêtre (leurs identifiants sont éventuellement utilisés par les sessions). On peut toutefois compléter ses ressources et son libellé. La fiche construit un brouillon indépendant : **Annuler n'applique aucune modification**, même si des ressources ont été examinées ou des associations prévisualisées.

### Associer les images aux ALTO/PAGE par lots

Depuis la fiche de témoin ou **2 · Pages et ALTO/PAGE**, choisir **Associer automatiquement les images et les ALTO/PAGE**.

1. Le premier passage exploite les correspondances **uniques** de nom d'image, `Page@imageFilename` ou identifiant de page documentaire. Les sources comportant plusieurs pages sont traitées page par page.
2. Pour les fichiers encore sans lien, si toutes les pages sont locales, que le lot est homogène et que **le nombre d'images restantes égale le nombre de pages XML restantes**, un second passage propose une association par **rang naturel**. Cette méthode ne prouve pas que les pages sont les bonnes : les propositions sont mises en garde et demandent une confirmation explicite.
3. La fenêtre présente image (avec miniature locale lorsqu'elle est visible), page XML, méthode de rapprochement et remarque. Chaque ligne possède un menu permettant de **changer la page XML proposée** ou de **ne rien associer**.
4. Un même XML ne peut être associé deux fois. Les liens existants sont verrouillés. Un conflit, une double utilisation ou une modification de ressources après la prévisualisation fait refuser **l'ensemble de l'opération**, sans enregistrer de résultat partiel.
5. Après application, les associations conservent `verified: false` : les noms et l'ordre ne constituent pas une validation éditoriale. Vérifier sur les images, notamment lorsque les noms sont aléatoires ou que des pages sont manquantes.

**IIIF :** aucun raccourci par rang ne rattache un sous-ensemble au début d'un grand Manifest. Les correspondances sont proposées à partir d'informations identifiables ; les Canvas restent indépendants des fichiers locaux. Les miniatures et l'ordre peuvent toujours être contrôlés dans la fenêtre générale de gestion des pages.

### Ordre des pages et identité documentaire

L'ordre naturel initial **ne remplace pas** un ordre manuel déjà fixé. Le glisser-déposer, « Monter / Descendre » et « Inverser l'ordre » existent toujours. Les identifiants de page, les liens image ↔ XML, les UID physiques et les sessions de synchronisation ne changent pas lorsqu'on réordonne.

### Export vers Varians

Dans l'étape 3, choisir le pivot de référence (par défaut celui enregistré dans le projet) et exporter. Les contrôles `base_keys`, `validated/` et `working/`, les absences confirmées et le rapport de diagnostic de la V0.7.4 sont conservés. **La simple présence d'une TEI importée ne crée pas de `base_keys` TEI.**

## Compatibilité et limites

- Les anciens projets V0.7.x s'ouvrent sans migration destructive ; `pivot_witness_id` est un champ facultatif ajouté au même schéma `.vsynch`.
- L'ancienne interface **« Outils historiques V0.5 »**, les commandes TXT et la fenêtre spéciale d'alignement TEI ancien format ont été supprimées des chemins graphiques. Le code de lancement historique (ancienne fenêtre V0.5) a été remplacé par un lanceur Qt minimal. Des modules de lecture historique restent conservés pour éviter de perdre les données des anciens projets.
- La suppression d'une ressource déjà référencée, le renommage transactionnel d'un sigle et l'alignement effectif `<lb edRef>` ↔ PAGE/ALTO **ne sont pas développés dans cette livraison**.
- Les tests de logique métier et d'import/export sont automatisés ; les interactions graphiques Qt nécessitent une vérification sur un poste muni de PySide6.
